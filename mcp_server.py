#!/usr/bin/env python3
"""
MCP stdio server for the YouTube channel summarizer.

Run (from this project directory):
  python mcp_server.py
  python main.py --mcp

Cursor: copy mcp.json.example into .cursor/mcp.json (see README).
"""

from __future__ import annotations

import logging
import os
import re
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.chdir(PROJECT_ROOT)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    try:
        from mcp.server import MCPServer as FastMCP
    except ImportError as exc:
        raise SystemExit(
            "The 'mcp' package is required to run as an MCP server. "
            "Install with: pip install -r requirements.txt"
        ) from exc

from dotenv import load_dotenv

yt = None  # bound to the summarizer module in run()

mcp = FastMCP("youtube-summarizer")

_VIDEO_ID_RE = re.compile(
    r"(?:v=|/videos/|embed/|/shorts/|youtu\.be/)([0-9A-Za-z_-]{11})"
)


def _bind_yt(yt_module=None):
    global yt
    if yt_module is not None:
        yt = yt_module
    elif yt is None:
        import main as yt_mod
        yt = yt_mod
    return yt


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s [%(levelname)s] %(message)s",
        force=True,
    )


def _configure_ytdlp() -> None:
    fn = _bind_yt().fetch_transcript_with_ytdlp
    if getattr(fn, "_cookies_path", None) is None:
        fn._cookies_path = os.getenv("YT_COOKIES")
    if getattr(fn, "_cookies_browser", None) is None:
        fn._cookies_browser = os.getenv("YT_COOKIES_FROM_BROWSER")
    if getattr(fn, "_cookies_profile", None) is None:
        fn._cookies_profile = os.getenv("YT_COOKIES_PROFILE")
    if getattr(fn, "_rustypipe_bin", None) is None:
        fn._rustypipe_bin = os.getenv("RUSTYPIPE_BG_BIN")
    if getattr(fn, "_po_token", None) is None:
        fn._po_token = os.getenv("YT_PO_TOKEN")
    fn._verbose = False


def _ensure_env(*, require_gemini: bool) -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    _bind_yt().load_env(require_gemini=require_gemini)


def _youtube_client():
    _ensure_env(require_gemini=False)
    return yt.build_youtube_client()


@contextmanager
def _keep_stdout_clean():
    """yt-dlp may print to stdout, which would break MCP stdio JSON-RPC."""
    old_stdout = sys.stdout
    sys.stdout = sys.stderr
    try:
        yield
    finally:
        sys.stdout = old_stdout


def parse_video_id(video: str) -> str:
    """Accept a raw 11-char id or any common YouTube URL."""
    value = (video or "").strip()
    if re.fullmatch(r"[0-9A-Za-z_-]{11}", value):
        return value
    match = _VIDEO_ID_RE.search(value)
    if match:
        return match.group(1)
    raise ValueError(f"Could not parse a YouTube video id from: {video}")


def _video_payload(video_id: str, snippet: Optional[dict] = None) -> dict[str, Any]:
    snippet = snippet or {}
    return {
        "video_id": video_id,
        "url": f"https://youtu.be/{video_id}",
        "title": snippet.get("title") or "",
        "channel_title": snippet.get("channelTitle") or "",
        "published_at": snippet.get("publishedAt") or "",
        "description": snippet.get("description") or "",
    }


def _summarize_one(video_id: str, snippet: dict, *, url_fallback: bool) -> dict[str, Any]:
    payload = _video_payload(video_id, snippet)
    with _keep_stdout_clean():
        transcript = yt.fetch_transcript_text(video_id)
    if transcript:
        yt.save_transcript(
            transcript,
            video_id,
            snippet.get("title", ""),
            snippet.get("publishedAt"),
        )
        payload["transcript_saved"] = True
        payload["summary"] = yt.gemini_summarize(transcript)
        payload["source"] = "transcript"
        return payload

    payload["transcript_saved"] = False
    if url_fallback:
        summary = yt.gemini_summarize_url(payload["url"])
        if summary and len(summary.strip()) > 40:
            payload["summary"] = summary
            payload["source"] = "url"
            return payload

    payload["summary"] = yt.gemini_summarize_metadata(
        {
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "publishedAt": snippet.get("publishedAt", ""),
            "channelTitle": snippet.get("channelTitle", ""),
        }
    )
    payload["source"] = "metadata"
    return payload


@mcp.tool()
def list_channel_videos(channel_url: str, limit: int = 10) -> dict[str, Any]:
    """List the latest videos from a YouTube channel.

    Accepts a channel URL, @handle (e.g. @GoogleAI), or UC… channel ID.
    """
    limit = max(1, min(int(limit), 50))
    youtube = _youtube_client()
    channel_id = yt.resolve_channel_id(youtube, channel_url.strip())
    video_ids = yt.list_latest_video_ids(youtube, channel_id, limit)
    snippets = yt.get_video_snippets_batch(youtube, video_ids)
    return {
        "channel_url": channel_url.strip(),
        "channel_id": channel_id,
        "count": len(video_ids),
        "videos": [_video_payload(vid, snippets.get(vid, {})) for vid in video_ids],
    }


@mcp.tool()
def get_video_transcript(video: str, save: bool = True) -> dict[str, Any]:
    """Fetch the transcript for a YouTube video id or URL.

    Saves a cleaned .txt under transcripts/ unless save is false.
    """
    _ensure_env(require_gemini=False)
    video_id = parse_video_id(video)
    youtube = _youtube_client()
    snippet = yt.get_video_snippet(youtube, video_id)
    with _keep_stdout_clean():
        transcript = yt.fetch_transcript_text(video_id)
    result = _video_payload(video_id, snippet)
    if not transcript:
        result["transcript"] = None
        result["error"] = "No transcript available."
        return result
    if save:
        yt.save_transcript(
            transcript,
            video_id,
            snippet.get("title", ""),
            snippet.get("publishedAt"),
        )
    result["transcript"] = yt.clean_caption_text(transcript)
    result["saved"] = bool(save)
    return result


@mcp.tool()
def summarize_video(video: str, url_fallback: bool = True) -> dict[str, Any]:
    """Summarize one YouTube video with Gemini.

    Uses the transcript when available, then URL/metadata fallbacks.
    Requires GEMINI_API_KEY.
    """
    _ensure_env(require_gemini=True)
    video_id = parse_video_id(video)
    youtube = _youtube_client()
    snippet = yt.get_video_snippet(youtube, video_id)
    return _summarize_one(video_id, snippet, url_fallback=url_fallback)


@mcp.tool()
def summarize_channel(
    channel_url: str,
    per_channel: int = 5,
    skip_existing: bool = True,
    url_fallback: bool = True,
    sleep: float = 0.5,
) -> dict[str, Any]:
    """Summarize the latest videos from a YouTube channel with Gemini.

    Default is 5 videos (max 20). Existing local transcripts are skipped unless
    skip_existing is false. This can take several minutes.
    """
    _ensure_env(require_gemini=True)
    per_channel = max(1, min(int(per_channel), 20))
    youtube = _youtube_client()
    channel_id = yt.resolve_channel_id(youtube, channel_url.strip())
    video_ids = yt.list_latest_video_ids(youtube, channel_id, per_channel)
    snippets = yt.get_video_snippets_batch(youtube, video_ids)
    existing = yt.get_existing_transcript_video_ids() if skip_existing else set()

    results: list[dict[str, Any]] = []
    skipped: list[str] = []
    for vid in video_ids:
        if skip_existing and vid in existing:
            skipped.append(vid)
            continue
        snippet = snippets.get(vid, {})
        try:
            results.append(_summarize_one(vid, snippet, url_fallback=url_fallback))
        except Exception as exc:
            payload = _video_payload(vid, snippet)
            payload["error"] = str(exc)
            results.append(payload)
        time.sleep(max(0.0, float(sleep)))

    return {
        "channel_url": channel_url.strip(),
        "channel_id": channel_id,
        "summarized": results,
        "skipped_existing": skipped,
    }


@mcp.tool()
def list_saved_transcripts() -> dict[str, Any]:
    """List transcript files already saved in the local transcripts/ folder."""
    _bind_yt()
    transcripts_dir = PROJECT_ROOT / "transcripts"
    if not transcripts_dir.exists():
        return {"count": 0, "transcripts": []}
    items = []
    for path in sorted(transcripts_dir.glob("*.txt")):
        items.append(
            {
                "filename": path.name,
                "path": str(path),
                "video_id": yt.get_video_id_from_transcript_filename(path.name),
            }
        )
    return {"count": len(items), "transcripts": items}


def run(yt_module=None) -> None:
    _bind_yt(yt_module)
    _configure_logging()
    _configure_ytdlp()
    load_dotenv(PROJECT_ROOT / ".env")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run()
