# YouTube Downloader

A small Streamlit app for downloading YouTube videos, extracting audio as MP3, or generating transcripts from spoken audio.

## What It Does

- Paste a YouTube URL into the app
- Choose a quality option: `best` or `worst`
- Choose an output format: `mp4`, `mkv`, `webm`, or `mp3`
- Optionally enable `Transcript only`
- Click `Download`
- The file is saved into a local `downloads/` folder next to the app

## Requirements

- Python 3.10+ recommended
- `ffmpeg` installed and available on your `PATH` if you want MP3 downloads
- `ffmpeg` installed and available on your `PATH` for transcript generation
- `openai-whisper` for local speech-to-text transcript generation

## Install

### Windows

Open PowerShell in the project folder and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks script activation, run this once in the same terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

From the project directory:

```bash
streamlit run yt_downloader_app.py
```

Streamlit will open the app in your browser, usually at `http://localhost:8501`.

## How It Works

The app uses `yt-dlp` behind the scenes.

- For video formats, `best` tries to fetch the best available video + audio stream combination.
- `worst` requests the lowest-quality available format.
- For `mp3`, the app downloads the best audio stream and converts it to MP3 using `ffmpeg`.
- For `Transcript only`, the app downloads the best audio stream, then runs local speech-to-text with Whisper and saves a `.txt` transcript.

The download logic lives in [`services/yt_service.py`](./services/yt_service.py), and the UI lives in [`yt_downloader_app.py`](./yt_downloader_app.py).

## Notes

- No login or API key is required for the app itself.
- Some YouTube links may fail depending on the video, region, or site changes.
- If MP3 conversion fails, check that `ffmpeg` is installed and available from the command line.
- If transcript generation fails, check that `ffmpeg` is installed and that `openai-whisper` and its dependencies are installed correctly.
- Downloaded files are written to `downloads/`, which you can safely delete later if you want to clean up space.

## Project Files

- `yt_downloader_app.py` - Streamlit UI
- `services/yt_service.py` - download and conversion logic
- `requirements.txt` - Python dependencies
- `downloads/` - output folder created at runtime
