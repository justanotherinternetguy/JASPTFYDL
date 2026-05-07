# JASPTFYDL

**Just Another Spotify DownLoader**

A terminal UI for downloading your Spotify playlists as MP3s via YouTube. Export your playlists with [Exportify](https://exportify.net), drop the CSVs in a folder, and let the TUI handle the rest.

## Requirements

- Python 3.10+
- `ffmpeg` (must be on your `PATH` for audio conversion)

## Installation

```bash
git clone https://github.com/justanotherinternetguy/JASPTFYDL
cd JASPTFYDL/jasptfydl
python -m venv venv
venv/bin/pip install -r requirements.txt
```

## Usage

### 1. Export your Spotify playlists

Go to [exportify.net](https://exportify.net), log in, and export any playlists you want. Each export produces a `.csv` file.

### 2. Drop the CSVs into `music_csv/`

Place your exported CSV files in the `music_csv/` directory at the root of the repo (next to the `jasptfydl/` folder). Create it if it doesn't exist:

```
JASPTFYDL/
├── jasptfydl/
├── music_csv/       <-- put your CSVs here
│   ├── My Playlist.csv
│   └── Road Trip.csv
└── music/           <-- downloaded MP3s go here (created automatically)
```

### 3. Run

```bash
cd jasptfydl
venv/bin/python main.py
```

With a custom output directory:

```bash
venv/bin/python main.py -o /path/to/output
```

### 4. Select a playlist

The TUI will list all CSVs found in `music_csv/`. Use arrow keys to navigate and `Enter` to start downloading.

### Keybindings

| Key      | Action                      |
|----------|-----------------------------|
| `↑` / `↓` | Navigate playlist list     |
| `Enter`  | Start downloading selected playlist |
| `R`      | Refresh the playlist list   |
| `R` (download screen) | Retry failed tracks |
| `Ctrl+Q` | Quit                        |

## How it works

- Reads Exportify CSVs (handles UTF-8 BOM, multi-artist tracks, etc.)
- Searches YouTube for each track using `yt-dlp` (`"{artist} - {title}"`)
- Downloads up to 3 tracks concurrently
- Converts to MP3 at best available quality via `ffmpeg`
- Embeds ID3 tags (artist, title, album, year) from Spotify metadata
- Skips tracks that already exist in the output directory
- Organizes downloads into `music/<playlist-name>/`

## Output structure

```
music/
└── My Playlist/
    ├── Artist - Song Title.mp3
    └── ...
```

## Track states

| Icon | Meaning        |
|------|----------------|
| `·`  | Pending        |
| `⬇`  | Downloading    |
| `✓`  | Done           |
| `✗`  | Failed         |
| `↩`  | Skipped (already exists) |
