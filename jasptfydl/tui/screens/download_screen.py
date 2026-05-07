"""Download progress screen."""

import asyncio
import os
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List, Optional

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Label, ProgressBar, Static

from core.downloader import download_track, sanitize_filename


class TrackState(Enum):
    PENDING = auto()
    DOWNLOADING = auto()
    DONE = auto()
    FAILED = auto()
    SKIPPED = auto()


@dataclass
class TrackJob:
    idx: int
    artist: str
    title: str
    data: Dict[str, Any]
    state: TrackState = TrackState.PENDING
    progress: float = 0.0
    row_key: Optional[str] = None


_SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
_ICON = {
    TrackState.PENDING: " ·",
    TrackState.DOWNLOADING: "⬇",
    TrackState.DONE: " ✓",
    TrackState.FAILED: " ✗",
    TrackState.SKIPPED: " ↩",
}


class DownloadScreen(Screen):
    CSS_PATH = "../../jasptfydl.tcss"
    BINDINGS = [
        ("ctrl+q", "app.quit", "Quit"),
        ("r", "retry_failed", "Retry failed"),
    ]

    def __init__(
        self,
        playlist_name: str,
        tracks: List[Dict[str, Any]],
        output_dir: str,
        max_concurrent: int = 3,
        audio_format: str = "mp3",
    ):
        super().__init__()
        self._playlist_name = playlist_name
        self._raw_tracks = tracks
        self._output_dir = output_dir
        self._max_concurrent = max_concurrent
        self._audio_format = audio_format
        self._jobs: List[TrackJob] = []
        self._spinner_frame = 0
        self._total = len(tracks)

    def compose(self) -> ComposeResult:
        yield Static(
            " Just Another Spotify DownLoader",
            id="header",
        )
        with Static(id="dl-header"):
            yield Label(
                f"  {self._playlist_name}  •  {self._total} tracks",
                id="dl-playlist-name",
            )
        yield DataTable(id="track-table", zebra_stripes=True, show_cursor=True)
        with Static(id="dl-footer"):
            yield ProgressBar(total=self._total, show_eta=False, id="progress-bar")
            yield Label("", id="dl-stats")
            yield Label(f"  Output → {self._output_dir}", id="dl-output")

    def on_mount(self) -> None:
        table = self.query_one("#track-table", DataTable)
        table.add_column("", key="status", width=2)
        table.add_column("Artist", key="artist")
        table.add_column("Title", key="title")
        table.add_column("Progress", key="progress", width=10)
        table.cursor_type = "row"

        for i, t in enumerate(self._raw_tracks):
            artist = t.get("artist", "")
            title = t.get("title", "")
            job = TrackJob(idx=i, artist=artist, title=title, data=t)
            job.row_key = str(i)
            table.add_row(" ·", artist[:34], title[:42], "", key=str(i))  # status, artist, title, progress
            self._jobs.append(job)

        os.makedirs(self._output_dir, exist_ok=True)
        self.set_interval(0.12, self._tick_spinner)
        self.run_worker(self._download_all(), exclusive=True)

    def _tick_spinner(self) -> None:
        self._spinner_frame = (self._spinner_frame + 1) % len(_SPINNER)
        table = self.query_one("#track-table", DataTable)
        spin = _SPINNER[self._spinner_frame]
        for job in self._jobs:
            if job.state == TrackState.DOWNLOADING:
                table.update_cell(job.row_key, "progress", f"{job.progress:5.1f}%")  # type: ignore[arg-type]
                table.update_cell(job.row_key, "status", spin)  # type: ignore[arg-type]

    def _update_row(self, job: TrackJob) -> None:
        table = self.query_one("#track-table", DataTable)
        pct = (
            "done" if job.state == TrackState.DONE
            else "failed" if job.state == TrackState.FAILED
            else "skipped" if job.state == TrackState.SKIPPED
            else ""
        )
        table.update_cell(job.row_key, "status", _ICON[job.state])  # type: ignore[arg-type]
        table.update_cell(job.row_key, "progress", pct)  # type: ignore[arg-type]

    def _update_stats(self) -> None:
        done = sum(1 for j in self._jobs if j.state == TrackState.DONE)
        fail = sum(1 for j in self._jobs if j.state == TrackState.FAILED)
        skip = sum(1 for j in self._jobs if j.state == TrackState.SKIPPED)
        active = sum(1 for j in self._jobs if j.state == TrackState.DOWNLOADING)
        pending = self._total - done - fail - skip - active
        self.query_one("#dl-stats", Label).update(
            f"  ✓ {done}  ✗ {fail}  ↩ {skip}  ⬇ {active}  · {pending} pending"
        )
        self.query_one("#progress-bar", ProgressBar).progress = done + fail + skip

    async def _download_all(self) -> None:
        sem = asyncio.Semaphore(self._max_concurrent)
        await asyncio.gather(*[self._download_one(job, sem) for job in self._jobs])
        done = sum(1 for j in self._jobs if j.state == TrackState.DONE)
        fail = sum(1 for j in self._jobs if j.state == TrackState.FAILED)
        skip = sum(1 for j in self._jobs if j.state == TrackState.SKIPPED)
        self.query_one("#dl-stats", Label).update(
            f"  Finished — ✓ {done} downloaded  ✗ {fail} failed  ↩ {skip} skipped  •  press Ctrl+Q to quit"
        )

    async def _download_one(self, job: TrackJob, sem: asyncio.Semaphore) -> None:
        safe_name = sanitize_filename(f"{job.artist} - {job.title}")
        expected_path = os.path.join(self._output_dir, f"{safe_name}.{self._audio_format}")
        if os.path.exists(expected_path):
            job.state = TrackState.SKIPPED
            job.progress = 100.0
            self._update_row(job)
            self._update_stats()
            return

        async with sem:
            job.state = TrackState.DOWNLOADING

            def on_progress(pct: float) -> None:
                job.progress = pct

            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None,
                lambda: download_track(
                    job.data,
                    self._output_dir,
                    self._audio_format,
                    on_progress=on_progress,
                ),
            )
            job.state = TrackState.DONE if success else TrackState.FAILED
            job.progress = 100.0 if success else 0.0
            self._update_row(job)
            self._update_stats()

    def action_retry_failed(self) -> None:
        failed = [j for j in self._jobs if j.state == TrackState.FAILED]
        if not failed:
            return
        for job in failed:
            job.state = TrackState.PENDING
            job.progress = 0.0
            self._update_row(job)

        async def _retry() -> None:
            sem = asyncio.Semaphore(self._max_concurrent)
            await asyncio.gather(*[self._download_one(j, sem) for j in failed])

        self.run_worker(_retry(), exclusive=False)
