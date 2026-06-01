# pyclean 🧹

**Tidy up cluttered directories by file type** — with dry-run previews, one-command undo, and gorgeous terminal output.

![Python Version](https://img.shields.io/badge/python-≥3.10-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

```bash
# See what would happen (safe)
pyclean ~/Downloads -n

# Actually clean it
pyclean ~/Downloads

# Oops — put everything back
pyclean ~/Downloads --undo
```

## Features

- **Smart categorization** — images, documents, audio, video, archives, code, and a catch-all `Other`.
- **Dry-run mode** (`-n`) — preview every move without touching a file.
- **Undo** (`--undo`) — reverts the last clean by reading a manifest stored in `.pyclean/`.
- **Interactive mode** (`-i`) — confirm each file one-by-one.
- **Recursive scan** (`-r`) — reach into subdirectories.
- **Rich output** — color-coded tables, tree views, and progress via the `rich` library.
- **Minimal deps** — only needs `rich`.

## Installation

```bash
pip install pyclean
```

Or from source:

```bash
git clone https://github.com/farhan-codez/pyclean.git
cd pyclean
pip install -e .
```

## Usage

```
usage: pyclean [-h] [-n] [-r] [-i] [--min-size MIN_SIZE] [--undo] [--version] [directory]

Tidy up cluttered directories by file type.

positional arguments:
  directory           Directory to clean (default: current)

options:
  -h, --help          Show this help message and exit
  -n, --dry-run       Preview changes without moving anything
  -r, --recursive     Scan subdirectories recursively
  -i, --interactive   Confirm each file before moving
  --min-size BYTES    Skip files smaller than this many bytes
  --undo              Reverse the last clean operation
  --version           Show version and exit
```

### Examples

**Dry-run your Downloads folder:**

```bash
pyclean ~/Downloads -n
```

**Clean your Desktop with interactive confirmation:**

```bash
pyclean ~/Desktop -i
```

**Clean recursively, skipping tiny files:**

```bash
pyclean ~/projects -r --min-size 1024
```

**Undo the last clean:**

```bash
pyclean ~/Downloads --undo
```

## How it works

| Extension | Category |
|-----------|----------|
| `.jpg`, `.png`, `.gif`, ... | Images |
| `.pdf`, `.docx`, `.txt`, ... | Documents |
| `.mp3`, `.wav`, `.flac`, ... | Audio |
| `.mp4`, `.mkv`, `.mov`, ... | Video |
| `.zip`, `.tar`, `.gz`, ...  | Archives |
| `.py`, `.js`, `.ts`, ...    | Code |
| everything else             | Other |

Files are **moved** (not copied) into `Category/` subfolders. If a filename already exists, a numeric suffix is appended (`file_1.ext`, `file_2.ext`, …).

## Project structure

```
pyclean/
├── pyproject.toml
├── README.md
├── .gitignore
└── src/
    └── pyclean/
        ├── __init__.py
        ├── __main__.py
        ├── cli.py       # Argument parsing + entry point
        └── cleaner.py   # Scan, organize, undo logic
```

## License

MIT
