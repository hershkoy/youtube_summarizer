## Learned User Preferences
- CLI flags use underscore names (`--youtube_video`, `--text_files_dir`, `--transcribe_only`); hyphen forms are accepted as aliases.
- Hebrew summary `.docx` files should be right-to-left, including a way to convert a file that already exists.

## Learned Workspace Facts
- `python main.py --youtube_video` (also `--youtube-video`) takes one YouTube URL or 11-character id. `--transcribe_only` / `--transcripts-only` saves the transcript and skips the summary; without that flag the run also writes a summary `.docx` (default `YouTube_Summaries.docx`). A transcript already saved under `transcripts/` is reused unless `--no-skip-existing`.
- `--rtl` on `main.py` writes `.docx` output right-to-left. Existing files are converted with `rtl_docx.py` (python-docx `w:bidi` on paragraphs and `w:rtl` on runs; alignment is stored as left because Word mirrors it).
- `--text-files-dir` / `--text_files_dir` summarizes only top-level `*.txt` files, in natural numeric order and in each file's language. Files longer than 80,000 characters are summarized in parts and merged. It needs a summary key only, saves the `.docx` after each file (default `text_summaries.docx`), and cannot be combined with `--channels` or `--transcribe_only`.
- Summaries default to Gemini (`gemini-2.5-flash`, `GEMINI_API_KEY` in `.env`). `--provider kimi` uses Moonshot (`MOONSHOT_API_KEY`, model `kimi-k3.1-pro`). YouTube fetch modes also need `YOUTUBE_API_KEY`.
- MCP stdio server: `python mcp_server.py` or `python main.py --mcp`. Tools are `list_channel_videos`, `get_video_transcript`, `summarize_video`, `summarize_channel`, and `list_saved_transcripts`. Sample config is `mcp.json.example` (server name `youtube-summarizer`). Cookies can be passed with `--cookies-from-browser`.
- The project venv is `.venv` in this folder. It was created before the move under `_Tools`; a stale activate script pointed `python` at the old location and missed installed packages.
