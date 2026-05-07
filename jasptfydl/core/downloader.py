"""yt-dlp wrapper with progress callbacks — runs synchronously in a thread."""

import os
from typing import Any, Callable, Dict, Optional

import yt_dlp
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError


def sanitize_filename(name: str) -> str:
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, "-")
    return name.strip()


_sanitize = sanitize_filename  # internal alias


def download_track(
    track: Dict[str, Any],
    output_dir: str,
    audio_format: str = "mp3",
    on_progress: Optional[Callable[[float], None]] = None,
    on_status: Optional[Callable[[str], None]] = None,
) -> bool:
    """Download one track via yt-dlp YouTube search. Returns True on success."""
    artist = track.get("artist", "").strip()
    title = track.get("title", "").strip()
    query = f"{artist} - {title}"
    safe_name = _sanitize(f"{artist} - {title}")
    out_template = os.path.join(output_dir, f"{safe_name}.%(ext)s")

    def progress_hook(d: Dict[str, Any]) -> None:
        if on_progress is None:
            return
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                on_progress(downloaded / total * 100)
        elif status == "finished":
            on_progress(99.0)  # will jump to 100 after postprocess

    def postprocessor_hook(d: Dict[str, Any]) -> None:
        if d.get("status") == "finished" and on_progress:
            on_progress(100.0)

    ydl_opts: Dict[str, Any] = {
        "format": "bestaudio/best",
        "audio_quality": 0,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": "0",
            }
        ],
        "outtmpl": out_template,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "progress_hooks": [progress_hook],
        "postprocessor_hooks": [postprocessor_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{query}"])
    except Exception as e:
        if on_status:
            on_status(f"yt-dlp error: {e}")
        return False

    # Embed Spotify metadata into the downloaded file
    expected_path = os.path.join(output_dir, f"{safe_name}.{audio_format}")
    if os.path.exists(expected_path) and audio_format == "mp3":
        _embed_id3(expected_path, track)

    return True


def _embed_id3(path: str, track: Dict[str, Any]) -> None:
    try:
        try:
            audio = EasyID3(path)
        except ID3NoHeaderError:
            audio = EasyID3()
            audio.save(path)
            audio = EasyID3(path)

        if track.get("artist"):
            audio["artist"] = track["artist"]
        if track.get("title"):
            audio["title"] = track["title"]
        if track.get("album"):
            audio["album"] = track["album"]
        if track.get("release_date"):
            audio["date"] = str(track["release_date"])[:4]
        audio.save(path)
    except Exception:
        pass  # metadata embedding is best-effort
