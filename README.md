# YouTube Summarizer (Gemini) -> Word

## Setup

1) Create and activate a virtualenv (recommended):
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

2) Install dependencies:
```bash
pip install -r requirements.txt
```

3) Configure environment variables:
- Copy `.env.example` to `.env` and put your keys.
- Get `YOUTUBE_API_KEY` from Google Cloud Console:
  - Create/select a project in [Google Cloud Console](https://console.cloud.google.com/)
  - Enable **YouTube Data API v3** for that project
  - Go to **APIs & Services -> Credentials -> Create credentials -> API key**
- Get `GEMINI_API_KEY` from Google AI Studio:
  - Open [Google AI Studio API keys](https://aistudio.google.com/app/apikey)
  - Click **Create API key**
- If you run with `--transcripts-only`, only `YOUTUBE_API_KEY` is required.
- If you run with `--text-files-dir`, only `GEMINI_API_KEY` is required.
- To summarize with Kimi instead, create a key at [platform.kimi.ai API Keys](https://platform.kimi.ai/console/api-keys), set `MOONSHOT_API_KEY` in `.env`, and pass `--provider kimi`. That uses the balance on the Kimi console, not the Gemini free tier. The default model is `kimi-k3.1-pro` with `KIMI_REASONING_EFFORT=low`.

4) Prepare your channel list file, e.g. `channels.txt`:
```
https://www.youtube.com/@GoogleAI
https://www.youtube.com/channel/UCILwQvG8d7yCw9x2Z8I2y0A
```

5) Run:
```bash
python main.py --channels channels.txt --out summaries.docx --per-channel 30
```

The script will create `summaries.docx` with per-channel headings and per-video summaries.

One video. This saves a transcript under `transcripts/` and writes a summary `.docx`. Add `--transcribe_only` to skip the summary (`--transcripts-only` is the same flag).

```bash
python main.py --youtube_video "https://www.youtube.com/watch?v=fg-kBYiChK4" --out video.docx
python main.py --youtube_video "https://www.youtube.com/watch?v=fg-kBYiChK4" --transcribe_only
```

An 11-character id works in place of the URL. Do not combine `--youtube_video` with `--channels` or `--text-files-dir`.

Hebrew summaries: add `--rtl` so the `.docx` is right-to-left. The same layout can be applied to a file that was already written:

```bash
python main.py --text-files-dir "D:\path\to\folder" --out summaries.docx --rtl
python rtl_docx.py price_action.docx
python rtl_docx.py price_action.docx --out price_action_rtl.docx
```

`rtl_docx.py` leaves the input file unchanged. With no `--out`, it writes `<name>_rtl.docx` next to the input.

Summarize existing `.txt` files only (no YouTube fetch). Other extensions in the folder are ignored. Files are read in natural order (`1_…` before `10_…`). The report is saved after each file, so a later failure keeps earlier summaries. Default output is `text_summaries.docx` in the current directory.

```bash
python main.py --text-files-dir "D:\path\to\folder" --out summaries.docx
```

Same folder, paid with the Kimi balance. Sections already saved in the output file are kept.

```bash
python main.py --text-files-dir "D:\path\to\folder" --out summaries.docx --provider kimi
```

`--text_files_dir` is the same flag. Do not combine it with `--channels` or `--transcripts-only`.


## Run

> python main.py --channels channels.txt --out summaries.docx --per-channel 30

> python main.py ^
  --channels channels.txt ^
  --out summaries.docx ^
  --per-channel 250 ^
  --show-date ^
  --date-format "%Y-%m-%d"

Local .txt files only (Gemini summaries, no YouTube):
> python main.py --text-files-dir "D:\path\to\folder" --out summaries.docx

Local .txt files with Kimi:
> python main.py --text-files-dir "D:\path\to\folder" --out summaries.docx --provider kimi

One video, transcript plus summary:
> python main.py --youtube_video "https://www.youtube.com/watch?v=fg-kBYiChK4" --out video.docx

Hebrew, right-to-left .docx:
> python main.py --youtube_video "https://www.youtube.com/watch?v=fg-kBYiChK4" --out video.docx --rtl

Convert an existing .docx to right-to-left (writes price_action_rtl.docx):
> python rtl_docx.py price_action.docx

Choose the output name:
> python rtl_docx.py price_action.docx --out hebrew.docx

One video, transcript only:
> python main.py --youtube_video "https://www.youtube.com/watch?v=fg-kBYiChK4" --transcribe_only

Transcripts only (skip Gemini + DOCX):
> python main.py --channels channels.txt --per-channel 30 --transcripts-only

Skip existing transcript files (default behavior):
> python main.py --channels channels.txt --per-channel 30 --transcripts-only --skip-existing

Force re-fetch even if transcript files already exist:
> python main.py --channels channels.txt --per-channel 30 --transcripts-only --no-skip-existing

Clean existing transcript files in a folder (in-place):
> python clean_transcripts.py --dir transcripts

Preview only:
> python clean_transcripts.py --dir transcripts --dry-run

debug:
> yt-dlp -v --print-traffic https://youtu.be/nLTSWy3tze4


## Use as an MCP server

The same pipeline can run as a Model Context Protocol (MCP) server so Cursor (or any MCP host) can list videos, fetch transcripts, and summarize with Gemini.

1. Install dependencies (includes the `mcp` package):
```bash
pip install -r requirements.txt
```

2. Keep your `.env` next to `mcp_server.py` (`YOUTUBE_API_KEY`; `GEMINI_API_KEY` for summarize tools).

3. Point the host at the server. For Cursor, copy `mcp.json.example` to `.cursor/mcp.json` in this project:
```json
{
  "mcpServers": {
    "youtube-summarizer": {
      "command": "python",
      "args": ["mcp_server.py"]
    }
  }
}
```
Use your venv interpreter if `python` is not the one with this project's packages, e.g. `.venv/Scripts/python.exe` on Windows. For a global Cursor MCP config, pass an absolute path to `mcp_server.py`.

4. Start it yourself (stdio; waits on stdin — that means it is running):
```bash
python mcp_server.py
python main.py --mcp
```

Cookie flags still work with the CLI entry: `python main.py --mcp --cookies-from-browser firefox`.

### Tools

| Tool | What it does |
| --- | --- |
| `list_channel_videos` | Latest videos for a channel URL / `@handle` / UC id |
| `get_video_transcript` | Fetch (and optionally save) one video transcript |
| `summarize_video` | Gemini summary for one video |
| `summarize_channel` | Gemini summaries for the latest N videos (default 5, max 20) |
| `list_saved_transcripts` | Files already in `transcripts/` |

`summarize_channel` can take several minutes. Transcripts are still written under `transcripts/`.

