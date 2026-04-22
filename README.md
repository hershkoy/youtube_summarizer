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


## Run

> python main.py --channels channels.txt --out summaries.docx --per-channel 30

> python main.py ^
  --channels channels.txt ^
  --out summaries.docx ^
  --per-channel 250 ^
  --show-date ^
  --date-format "%Y-%m-%d"

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


