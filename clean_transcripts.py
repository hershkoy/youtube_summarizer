#!/usr/bin/env python3
"""
Clean transcript text files in a folder in-place.

Usage:
  python clean_transcripts.py --dir transcripts
  python clean_transcripts.py --dir transcripts --glob "*.txt" --dry-run
"""

import argparse
import re
from pathlib import Path


def clean_caption_text(text: str) -> str:
    if not text:
        return text

    cleaned = text
    cleaned = re.sub(r"^\s*Kind:\s*captions\s+Language:\s*[A-Za-z0-9_-]+\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", " ", cleaned)
    cleaned = re.sub(r"</?c[^>]*>", " ", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace("&gt;&gt;", " ").replace("&gt;", " ").replace("&lt;", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean caption markup from transcript files.")
    parser.add_argument("--dir", type=str, default="transcripts", help="Target folder (default: transcripts).")
    parser.add_argument("--glob", type=str, default="*.txt", help="File glob inside folder (default: *.txt).")
    parser.add_argument("--dry-run", action="store_true", help="Show files that would change without writing.")
    args = parser.parse_args()

    target_dir = Path(args.dir)
    if not target_dir.exists() or not target_dir.is_dir():
        raise SystemExit(f"Directory not found: {target_dir}")

    changed = 0
    scanned = 0
    for path in sorted(target_dir.glob(args.glob)):
        if not path.is_file():
            continue
        scanned += 1
        original = path.read_text(encoding="utf-8", errors="replace")
        cleaned = clean_caption_text(original)
        if cleaned != original.strip():
            changed += 1
            if args.dry_run:
                print(f"[DRY-RUN] would clean: {path}")
            else:
                path.write_text(cleaned, encoding="utf-8")
                print(f"cleaned: {path}")

    print(f"Done. scanned={scanned}, changed={changed}, dry_run={args.dry_run}")


if __name__ == "__main__":
    main()
