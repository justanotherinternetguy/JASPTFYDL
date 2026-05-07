#!/usr/bin/env python3
"""Just Another Spotify DownLoader.

Put Exportify CSVs in  ../music_csv/  then run:
    venv/bin/python main.py
    venv/bin/python main.py -o /path/to/output   # custom output dir
"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="jasptfydl",
        description="Pick an Exportify CSV from music_csv/ and download via YouTube.",
    )
    parser.add_argument("--output", "-o", default=None, help="Output directory (default: ../music/)")
    args = parser.parse_args()

    from tui.app import JasptfydlApp
    JasptfydlApp(output_dir=args.output).run()


if __name__ == "__main__":
    main()
