from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table
from rich.tree import Tree

from pyclean import __version__
from pyclean.cleaner import scan_directory, organize, undo

console = Console()


class Reporter:
    def preview(self, category: str, src: Path, dest: Path) -> None:
        tree = Tree(f"[bold]{category}[/bold]", guide_style="dim")
        tree.add(f"[dim]{src.name}[/dim]  →  {dest.parent.name}/[bold]{dest.name}[/bold]")
        console.print(tree)

    def moved(self, category: str, src: Path, dest: Path) -> None:
        console.print(
            f"  [green]✓[/green] {src.name}  →  [bold]{dest.parent.name}/{dest.name}[/bold]"
        )

    def confirm(self, src: Path, dest: Path) -> bool:
        return Confirm.ask(f"Move [bold]{src.name}[/bold] → [bold]{dest.parent.name}/{dest.name}[/bold]?")

    def restored(self, src: Path, dst: Path) -> None:
        console.print(f"  [yellow]↩[/yellow] {src.name}  →  {dst.parent.name}/")

    def error(self, msg: str) -> None:
        console.print(f"[red]✖[/red] {msg}")

    def success(self, msg: str) -> None:
        console.print(f"[green]✔[/green] {msg}")

    def info(self, msg: str) -> None:
        console.print(f"[dim]ℹ[/dim] {msg}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pyclean",
        description="Tidy up cluttered directories by file type.",
        epilog="Report issues at https://github.com/<your>/pyclean",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        type=Path,
        help="Directory to clean (default: current)",
    )
    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Preview changes without moving anything",
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Scan subdirectories recursively",
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Confirm each file before moving",
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=0,
        help="Skip files smaller than this many bytes",
    )
    parser.add_argument(
        "--undo",
        action="store_true",
        help="Reverse the last clean operation",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"pyclean v{__version__}",
    )
    return parser


def show_summary(grouped: dict[str, list[Path]]) -> None:
    table = Table(title="Files Found", title_style="bold cyan")
    table.add_column("Category", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Total Size", justify="right")

    total_files = 0
    total_size = 0
    for cat, files in sorted(grouped.items()):
        size = sum(f.stat().st_size for f in files)
        table.add_row(cat, str(len(files)), _fmt_size(size))
        total_files += len(files)
        total_size += size

    table.add_row("[bold]Total[/bold]", str(total_files), _fmt_size(total_size), style="bold")
    console.print(table)


def _fmt_size(bytes_: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if bytes_ < 1024:
            return f"{bytes_:.1f} {unit}"
        bytes_ /= 1024
    return f"{bytes_:.1f} TB"


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    directory = args.directory.expanduser().resolve()

    if not directory.is_dir():
        console.print(f"[red]✖[/red] Not a directory: {directory}")
        sys.exit(1)

    if args.undo:
        sys.exit(undo(directory, Reporter()))

    reporter = Reporter()

    with console.status("[bold green]Scanning...") as _:
        grouped = scan_directory(
            directory,
            recursive=args.recursive,
            min_size=args.min_size,
        )

    if not grouped:
        reporter.info("No organizable files found.")
        sys.exit(0)

    show_summary(grouped)

    if args.dry_run:
        console.print("\n[bold]Dry run — no files will be moved[/bold]\n")
    elif not Confirm.ask("\nProceed with organization?"):
        reporter.info("Cancelled.")
        sys.exit(0)

    manifest = organize(
        directory, grouped,
        dry_run=args.dry_run,
        interactive=args.interactive,
        reporter=reporter,
    )

    moved = [e for e in manifest if e["action"] == "moved"]
    if not args.dry_run and moved:
        reporter.success(f"Moved {len(moved)} file(s). Use [bold]pyclean --undo[/bold] to revert.")
    elif args.dry_run:
        reporter.info(f"Would move {len([e for e in manifest if e['action'] == 'would_move'])} file(s).")
