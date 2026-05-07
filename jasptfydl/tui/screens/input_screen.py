"""CSV picker screen — lists all CSVs in music_csv/ for the user to select."""

import os
from typing import List, Optional, Tuple

from textual import on
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, ListItem, ListView, Static

from core.csv_loader import load_csv

_MUSIC_CSV_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "music_csv",
)


def _scan_csvs() -> List[Tuple[str, str, int]]:
    """Return list of (display_name, full_path, track_count) sorted by filename."""
    if not os.path.isdir(_MUSIC_CSV_DIR):
        return []
    entries = []
    for fname in sorted(os.listdir(_MUSIC_CSV_DIR)):
        if not fname.lower().endswith(".csv"):
            continue
        path = os.path.join(_MUSIC_CSV_DIR, fname)
        try:
            tracks = load_csv(path)
            count = len(tracks)
        except Exception:
            count = 0
        name = os.path.splitext(fname)[0]
        entries.append((name, path, count))
    return entries


class InputScreen(Screen):
    """Lists CSVs from music_csv/ and returns (playlist_name, tracks) on selection."""

    CSS_PATH = "../../jasptfydl.tcss"
    BINDINGS = [
        ("ctrl+q", "app.quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Static(
            " Just Another Spotify DownLoader",
            id="header",
        )
        with Static(id="input-container"):
            with Static(id="input-card"):
                yield Label("Select a Playlist to Download", id="input-title")
                yield Label(
                    f"  Put your Exportify CSVs in:\n  {_MUSIC_CSV_DIR}\n\n"
                    "  R  →  Refresh\n"
                    "  Enter  →  Download\n"
                    "  Ctrl+Q  →  Quit",
                    id="input-subtitle",
                )
                yield ListView(id="csv-list")
                yield Label("", id="input-error")

    def on_mount(self) -> None:
        self._populate()

    def _populate(self) -> None:
        lv = self.query_one("#csv-list", ListView)
        lv.clear()
        error = self.query_one("#input-error", Label)

        self._entries = _scan_csvs()

        if not self._entries:
            error.update(
                f"⚠  No CSV files found in music_csv/.\n"
                "   Go to exportify.net, export a playlist, and drop the CSV there."
            )
            error.add_class("visible")
            return

        error.remove_class("visible")
        for name, path, count in self._entries:
            track_str = f"{count} track{'s' if count != 1 else ''}"
            lv.append(ListItem(Label(f"  {name:<45}  {track_str:>10}")))

        lv.focus()

    def action_refresh(self) -> None:
        self._populate()

    @on(ListView.Selected, "#csv-list")
    def on_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is None or idx >= len(self._entries):
            return
        name, path, _ = self._entries[idx]
        error = self.query_one("#input-error", Label)
        try:
            tracks = load_csv(path)
        except Exception as e:
            error.update(f"⚠  Failed to read {name}.csv: {e}")
            error.add_class("visible")
            return
        if not tracks:
            error.update(f"⚠  No valid tracks found in {name}.csv")
            error.add_class("visible")
            return
        self.dismiss((name, tracks))
