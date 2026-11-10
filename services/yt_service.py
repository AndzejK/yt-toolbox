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
YOUTUBE_PLAYER_CLIENTS = ["android", "mweb", "web"]
YOUTUBE_IMPERSONATE_TARGET = "chrome"
YOUTUBE_HTTP_CHUNK_SIZE = 10 * 1024 * 1024


def _ensure_output_dir(output_path: str) -> Path:
    path = Path(output_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _base_ydl_opts(output_path: Path, skip_sponsors: bool = False) -> dict:
    opts = {
        "outtmpl": str(output_path / "%(title)s.%(ext)s"),
        "user_agent": USER_AGENT,
        "http_headers": {"User-Agent": USER_AGENT},
        "remote_components": ["ejs:github"],
        "noplaylist": True,
        "http_chunk_size": YOUTUBE_HTTP_CHUNK_SIZE,
    }
    if skip_sponsors:
        # yt-dlp's SponsorBlock "default" behavior removes all supported
        # categories except filler. A single "sponsor" category is often too
        # narrow for videos that tag promotional reads as selfpromo, intro, or
        # interaction instead of sponsor.
        opts["sponsorblock_remove"] = ["all", "-filler"]
    return opts


def _youtube_compat_opts(player_clients: list[str] | None = None, impersonate: str | None = None) -> dict:
    opts: dict = {}
    if player_clients:
        opts["extractor_args"] = {"youtube": {"player_client": player_clients}}
    if impersonate:
        opts["impersonate"] = impersonate
    return opts


def _youtube_impersonation_target() -> str | None:
    try:
        import curl_cffi  # noqa: F401
    except ImportError:
        return None
    return YOUTUBE_IMPERSONATE_TARGET


def _youtube_download_attempts(base_opts: dict) -> list[tuple[str, dict]]:
    attempts: list[tuple[str, dict]] = []

    primary = dict(base_opts)
    primary.update(_youtube_compat_opts(YOUTUBE_PLAYER_CLIENTS, _youtube_impersonation_target()))
    attempts.append(("android/mweb/web + impersonation", primary))

    fallback = dict(base_opts)
    fallback.update(_youtube_compat_opts(["web", "android", "mweb"]))
    attempts.append(("web/android/mweb fallback", fallback))

    last_resort = dict(base_opts)
    attempts.append(("default yt-dlp settings", last_resort))

    return attempts


def _download_with_retries(url: str, attempts: list[tuple[str, dict]]) -> tuple[dict, Path]:
    errors: list[str] = []
    for label, ydl_opts in attempts:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return info, Path(ydl.prepare_filename(info))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{label}: {exc}")

    raise RuntimeError("Unable to download video data after trying multiple YouTube client settings.\n" + "\n".join(errors))


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


def download_video(url, output_path="downloads", quality="best", format="mp4", skip_sponsors: bool = False):
    output_dir = _ensure_output_dir(output_path)

    if format == "mp3":
        ydl_opts = _base_ydl_opts(output_dir, skip_sponsors=skip_sponsors)
        ydl_opts.update(
            {
                "format": "bestvideo+bestaudio/best" if skip_sponsors else "bestaudio/best",
                "merge_output_format": "mkv" if skip_sponsors else None,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
        )
        if ydl_opts["merge_output_format"] is None:
            ydl_opts.pop("merge_output_format")
    else:
        format_string = "bestvideo+bestaudio/best" if quality == "best" else "worst"
        ydl_opts = _base_ydl_opts(output_dir, skip_sponsors=skip_sponsors)
        ydl_opts.update(
            {
                "format": format_string,
                "merge_output_format": format,
            }
        )

    info, _ = _download_with_retries(url, _youtube_download_attempts(ydl_opts))
    return info.get("title", "Unknown Title")


def download_transcript(url, output_path="downloads", model_name="base", skip_sponsors: bool = False):
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
        ydl_opts = _base_ydl_opts(Path(temp_dir), skip_sponsors=skip_sponsors)
        ydl_opts.update({"format": "bestaudio/best"})

        info, audio_path = _download_with_retries(url, _youtube_download_attempts(ydl_opts))

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
