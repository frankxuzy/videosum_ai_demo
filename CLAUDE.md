# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube Video Summarizer - A Python tool that downloads YouTube videos, transcribes audio using local Whisper, summarizes content with OpenAI GPT, and translates to Chinese.

## Architecture

The codebase follows a modular pipeline architecture in `src/`:

1. **downloader.py** - Downloads YouTube audio using yt-dlp, extracts video metadata
2. **transcriber.py** - Local Whisper transcription (model sizes: tiny/base/small/medium/large)
3. **summarizer.py** - OpenAI GPT API for content summarization with chunking for long transcripts
4. **translator.py** - OpenAI GPT API for translating summaries to Chinese
5. **markdown_writer.py** - Generates final Markdown output with metadata and transcripts
6. **transcript_fetcher.py** - NEW: Fetches YouTube subtitles directly via API (no download needed)

### Pipeline Flow

**Option 1: Direct Subtitle API (Fastest - Recommended)**
```
YouTube URL → transcript_fetcher → native language subtitle → [translator if not Chinese] → chinese text → saved to file
```
- Automatically detects video language
- Translates non-Chinese content to Chinese
- Saves money on Chinese videos (no translation API cost)

**Option 2: Full Pipeline with Download**
```
YouTube URL → downloader → audio file → transcriber → transcript → summarizer → english_summary → translator → chinese_summary → markdown_writer → .md file
```

## Entry Points

- **`blog_main.py`** - **NEW: Batch Processing** - Process multiple YouTube videos and save results in a single Markdown blog file. Supports JSON/YAML configuration and incremental updates.
- **`transcript_main.py`** - **Recommended** - Directly fetch YouTube subtitles via API, no video download needed. Fastest option if subtitles exist.
- **`main.py`** - Full automated pipeline (download → transcribe → summarize → translate → markdown). Requires `OPENAI_API_KEY`.
- **`extract.py`** - Legacy entry point, only downloads and transcribes, creates template markdown for manual filling
- **`update_summary.py`** - Utility to programmatically update markdown files with summaries

## Common Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your OPENAI_API_KEY
```

### Run Subtitle Fetcher (Recommended)

The subtitle fetcher now supports **any language**! It automatically detects the video's native language and:
- Translates non-Chinese videos to Chinese (requires API key)
- Saves Chinese videos directly without translation (saves API cost)

```bash
# Auto-detect language and translate to Chinese (if not Chinese)
python transcript_main.py "https://www.youtube.com/watch?v=xxxxx"

# Fetch subtitle only, no translation
python transcript_main.py "URL" --no-translate

# Force specific language (e.g., English)
python transcript_main.py "URL" --language en

# Force Japanese subtitle
python transcript_main.py "URL" --language ja

# Custom output directory
python transcript_main.py "URL" -o ./my_transcripts/

# Show preview of translated text
python transcript_main.py "URL" -v
```

### Run Full Pipeline (Download + Transcribe)
```bash
# Basic usage
python main.py "https://www.youtube.com/watch?v=xxxxx"

# Custom output directory
python main.py "URL" -o ./my_summaries/

# Exclude full transcript from output (smaller file)
python main.py "URL" --no-transcript

# Keep temporary audio files
python main.py "URL" --no-cleanup

# Download only (no API key required)
python main.py "URL" --download-only

# Verbose logging
python main.py "URL" -v
```

### Run Tests
```bash
python -m unittest tests/test_basic.py
```

### Run Single Test Class
```bash
python -m unittest tests.test_basic.TestYouTubeDownloader
```

## Configuration

Configuration is via environment variables (loaded from `.env`):

- `OPENAI_API_KEY` - Required for GPT summarization and translation
- `ANTHROPIC_API_KEY` - Optional, alternative LLM (not currently used)
- `SUMMARIZER_MODEL` - Model for summarization (default: gpt-4o)
- `TRANSLATOR_MODEL` - Model for translation (default: gpt-4o)
- `DEFAULT_OUTPUT_DIR` - Output directory (default: ./output)
- `TEMP_DIR` - Temporary audio files directory (default: ./temp)

## Dependencies

Key dependencies from `requirements.txt`:
- `youtube-transcript-api` - **NEW**: Directly fetch YouTube subtitles (faster than download + Whisper)
- `yt-dlp>=2023.12.30` - YouTube downloading (requires FFmpeg for audio extraction)
- `openai-whisper` - Local transcription (fallback if no subtitles)
- `openai` - GPT API client for translation
- `python-dotenv` - Environment management
- `tqdm` - Progress bars

## Important Notes

- **Recommended workflow**: Use `transcript_main.py` first - it fetches subtitles directly (seconds vs minutes) in any language.
- **Multi-language support**: Automatically detects video language and translates non-Chinese content to Chinese
- **Cost savings**: Chinese videos skip translation (no API cost), other languages are translated using GPT-4o
- **Python 3.9 compatibility**: Use `Optional[str]` instead of `str | None` for type hints
- **FFmpeg required**: Only needed for downloader.py. Not needed if using transcript_main.py
- **API costs**: Translation uses OpenAI API (GPT-4o). Transcript fetching is free.
- **Subtitle availability**: Not all YouTube videos have subtitles. If `transcript_main.py` fails, the video has no captions.
- **Whisper models**: First run downloads the model (base ~72MB, large ~3GB). Models cached in ~/.cache/whisper/
- **YouTube 403 errors**: If Python downloader fails with 403, use command line: `yt-dlp -f "bestaudio[ext=m4a]" "URL" -o "temp/%(id)s.%(ext)s"`
