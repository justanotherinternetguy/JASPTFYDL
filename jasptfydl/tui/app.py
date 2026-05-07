"""Main Textual application."""

import os
from typing import Optional

from textual.app import App

from tui.screens.input_screen import InputScreen
from tui.screens.download_screen import DownloadScreen

_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "music",
)


class JasptfydlApp(App):
    CSS_PATH = "../jasptfydl.tcss"

    def __init__(self, output_dir: Optional[str] = None):
        super().__init__()
        self._output_dir = output_dir or _OUTPUT_DIR

    def on_mount(self) -> None:
        self.run_worker(self._flow(), exclusive=True)

    async def _flow(self) -> None:
        result = await self.push_screen_wait(InputScreen())
        if not result:
            self.exit()
            return

        playlist_name, tracks = result
        safe_name = playlist_name.replace("/", "-").strip()
        output_dir = os.path.join(self._output_dir, safe_name)

        await self.push_screen(
            DownloadScreen(
                playlist_name=playlist_name,
                tracks=tracks,
                output_dir=output_dir,
            )
        )
