from __future__ import annotations

import json
import shutil
from pathlib import Path
from datetime import datetime

EXTENSION_MAP: dict[str, str] = {
    # Images
    ".jpg": "Images", ".jpeg": "Images", ".png": "Images",
    ".gif": "Images", ".bmp": "Images", ".svg": "Images",
    ".webp": "Images", ".ico": "Images",
    # Documents
    ".pdf": "Documents", ".doc": "Documents", ".docx": "Documents",
    ".xls": "Documents", ".xlsx": "Documents", ".ppt": "Documents",
    ".pptx": "Documents", ".odt": "Documents", ".csv": "Documents",
    ".txt": "Documents", ".md": "Documents", ".rtf": "Documents",
    # Audio
    ".mp3": "Audio", ".wav": "Audio", ".flac": "Audio",
    ".aac": "Audio", ".ogg": "Audio", ".wma": "Audio",
    # Video
    ".mp4": "Video", ".mkv": "Video", ".avi": "Video",
    ".mov": "Video", ".wmv": "Video", ".webm": "Video",
    # Archives
    ".zip": "Archives", ".rar": "Archives", ".7z": "Archives",
    ".tar": "Archives", ".gz": "Archives", ".bz2": "Archives",
    # Code
    ".py": "Code", ".js": "Code", ".ts": "Code", ".jsx": "Code",
    ".tsx": "Code", ".html": "Code", ".css": "Code", ".scss": "Code",
    ".json": "Code", ".xml": "Code", ".yaml": "Code", ".yml": "Code",
    ".toml": "Code", ".sql": "Code", ".sh": "Code", ".bat": "Code",
    ".ps1": "Code", ".cpp": "Code", ".c": "Code", ".h": "Code",
    ".rs": "Code", ".go": "Code", ".java": "Code", ".rb": "Code",
    ".php": "Code", ".swift": "Code", ".kt": "Code",
}

DEFAULT_CATEGORIES = sorted(set(EXTENSION_MAP.values()))


def scan_directory(
    directory: Path,
    recursive: bool = False,
    min_size: int = 0,
) -> dict[str, list[Path]]:
    grouped: dict[str, list[Path]] = {cat: [] for cat in DEFAULT_CATEGORIES}
    grouped["Other"] = []

    pattern = "**/*" if recursive else "*"
    for entry in sorted(directory.glob(pattern)):
        if not entry.is_file():
            continue
        if entry.name.startswith("."):
            continue
        if min_size and entry.stat().st_size < min_size:
            continue

        ext = entry.suffix.lower()
        category = EXTENSION_MAP.get(ext, "Other")
        grouped[category].append(entry)

    return {k: v for k, v in grouped.items() if v}


def organize(
    directory: Path,
    grouped: dict[str, list[Path]],
    reporter,
    dry_run: bool = False,
    interactive: bool = False,
) -> list[dict]:
    manifest = []
    timestamp = datetime.now().isoformat()

    for category, files in grouped.items():
        target_dir = directory / category
        if not dry_run:
            target_dir.mkdir(exist_ok=True)

        for file in files:
            dest = target_dir / file.name
            suffix = 1
            while dest.exists():
                stem = file.stem
                dest = target_dir / f"{stem}_{suffix}{file.suffix}"
                suffix += 1

            if interactive and not reporter.confirm(file, dest):
                manifest.append({
                    "source": str(file),
                    "destination": str(dest),
                    "action": "skipped",
                })
                continue

            if dry_run:
                reporter.preview(category, file, dest)
                manifest.append({
                    "source": str(file),
                    "destination": str(dest),
                    "action": "would_move",
                })
            else:
                shutil.move(str(file), str(dest))
                reporter.moved(category, file, dest)
                manifest.append({
                    "source": str(file),
                    "destination": str(dest),
                    "action": "moved",
                })

    if not dry_run and any(e["action"] == "moved" for e in manifest):
        _write_manifest(directory, timestamp, manifest)

    return manifest


def undo(directory: Path, reporter) -> int:
    manifest_dir = directory / ".pyclean"
    if not manifest_dir.exists():
        reporter.error("No undo history found.")
        return 1

    manifests = sorted(manifest_dir.glob("*.json"), reverse=True)
    if not manifests:
        reporter.error("No undo history found.")
        return 1

    latest = manifests[0]
    with open(latest, encoding="utf-8") as f:
        manifest = json.load(f)

    count = 0
    for entry in reversed(manifest["files"]):
        if entry["action"] != "moved":
            continue
        src = Path(entry["destination"])
        dst = Path(entry["source"])
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            reporter.restored(src, dst)
            count += 1

    latest.unlink()
    if count:
        reporter.success(f"Restored {count} file(s).")
    else:
        reporter.info("Nothing to undo.")
    return 0


def _write_manifest(directory: Path, timestamp: str, entries: list[dict]) -> None:
    manifest_dir = directory / ".pyclean"
    manifest_dir.mkdir(exist_ok=True)
    name = f"clean_{timestamp.replace(':', '-')}.json"
    path = manifest_dir / name
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"timestamp": timestamp, "files": entries}, f, indent=2)
