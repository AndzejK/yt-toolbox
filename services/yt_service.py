from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import yt_dlp


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _ensure_output_dir(output_path: str) -> Path:
    path = Path(output_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _base_ydl_opts(output_path: Path) -> dict:
    return {
        "outtmpl": str(output_path / "%(title)s.%(ext)s"),
        "user_agent": USER_AGENT,
        "remote_components": ["ejs:github"],
        "noplaylist": True,
    }


def _format_timestamp(seconds: float) -> str:
    total_seconds = int(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _format_transcript(result: dict) -> str:
    segments = result.get("segments") or []
    if segments:
        lines = []
        for segment in segments:
            text = str(segment.get("text", "")).strip()
            if not text:
                continue
            start = _format_timestamp(float(segment.get("start", 0.0)))
            end = _format_timestamp(float(segment.get("end", 0.0)))
            lines.append(f"[{start} -> {end}] {text}")
        if lines:
            return "\n".join(lines).strip()
    return str(result.get("text", "")).strip()


def download_video(url, output_path="downloads", quality="best", format="mp4"):
    output_dir = _ensure_output_dir(output_path)

    if format == "mp3":
        ydl_opts = _base_ydl_opts(output_dir)
        ydl_opts.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
        )
    else:
        format_string = "bestvideo+bestaudio/best" if quality == "best" else "worst"
        ydl_opts = _base_ydl_opts(output_dir)
        ydl_opts.update(
            {
                "format": format_string,
                "merge_output_format": format,
            }
        )

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return info.get("title", "Unknown Title")


def download_transcript(url, output_path="downloads", model_name="base"):
    output_dir = _ensure_output_dir(output_path)

    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg is required for transcript generation. Install it and make sure it is on PATH."
        )

    try:
        import whisper
    except ImportError as exc:
        raise RuntimeError(
            "Transcript mode requires the openai-whisper package. Install dependencies with pip install -r requirements.txt."
        ) from exc

    with tempfile.TemporaryDirectory(dir=output_dir) as temp_dir:
        ydl_opts = _base_ydl_opts(Path(temp_dir))
        ydl_opts.update({"format": "bestaudio/best"})

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_path = Path(ydl.prepare_filename(info))

        if not audio_path.exists():
            raise RuntimeError("Audio download failed before transcription could start.")

        model = whisper.load_model(model_name)
        result = model.transcribe(str(audio_path))
        transcript = _format_transcript(result)
        title = info.get("title", "Unknown Title")

        if not transcript:
            transcript = ""

        transcript_path = output_dir / f"{audio_path.stem}.transcript.txt"
        transcript_path.write_text(transcript + "\n", encoding="utf-8")

        return {
            "title": title,
            "transcript": transcript,
            "transcript_path": str(transcript_path),
        }
