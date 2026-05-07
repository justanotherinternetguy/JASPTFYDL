"""Exportify CSV parser — adapted from harmoni/utils/loaders.py."""

import csv
import os
from typing import Dict, List


def _normalize_artists(raw: str) -> str:
    """Exportify uses semicolons for multi-artist; normalize to comma-separated."""
    raw = (raw or "").strip()
    if not raw:
        return ""
    delimiter = ";" if ";" in raw else ","
    parts = [p.strip() for p in raw.split(delimiter) if p.strip()]
    seen: set[str] = set()
    uniq = []
    for p in parts:
        if p.casefold() not in seen:
            seen.add(p.casefold())
            uniq.append(p)
    return ", ".join(uniq)


def load_csv(path: str) -> List[Dict[str, str]]:
    """
    Parse an Exportify CSV into a list of track dicts.
    Keys: artist, title, album, uri, release_date, genres, record_label,
          duration_ms, tempo, key, energy (all strings, empty-stripped).
    Raises ValueError if the file isn't a recognizable Exportify CSV.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    tracks: List[Dict[str, str]] = []

    # utf-8-sig strips the BOM that Exportify prepends
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or has no header row.")

        fields = [h.strip() for h in reader.fieldnames]
        if "Track Name" not in fields and "Artist Name(s)" not in fields:
            raise ValueError(
                "Doesn't look like an Exportify CSV.\n"
                "Expected columns: Track Name, Artist Name(s), Album Name, …"
            )

        for row in reader:
            artist = _normalize_artists(row.get("Artist Name(s)", "") or "")
            title = (row.get("Track Name", "") or "").strip()
            if not artist or not title:
                continue

            track: Dict[str, str] = {
                "artist": artist,
                "title": title,
                "album": (row.get("Album Name", "") or "").strip(),
                "uri": (row.get("Track URI", "") or "").strip(),
                "release_date": (row.get("Release Date", "") or "").strip(),
                "genres": (row.get("Genres", "") or "").strip(),
                "record_label": (row.get("Record Label", "") or "").strip(),
                "duration_ms": (row.get("Duration (ms)", "") or "").strip(),
                "tempo": (row.get("Tempo", "") or "").strip(),
                "energy": (row.get("Energy", "") or "").strip(),
                "key": (row.get("Key", "") or "").strip(),
            }
            tracks.append({k: v for k, v in track.items() if v})

    return tracks
