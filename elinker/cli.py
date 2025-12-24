"""CLI for ICD-10 Entity Linker."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel

app = App(name="elinker", help="ICD-10 Entity Linker CLI")
console = Console()
console_err = Console(stderr=True)


@app.default
def main():
    """Display Hello World."""
    console.print("[bold green]Hello World[/bold green]")


@app.command
def view_json(
    file_path: Annotated[Path, Parameter(help="Path to JSON file to display")],
    indent: Annotated[int, Parameter(help="Indentation level for JSON")] = 2,
    expand_all: Annotated[bool, Parameter(help="Expand all nested objects")] = True,
):
    """Load and display a JSON document with rich formatting.

    Args:
        file_path: Path to the JSON file
        indent: Indentation level for pretty printing
        expand_all: Whether to expand all nested objects
    """
    try:
        # Check if file exists
        if not file_path.exists():
            console_err.print(f"[red]Error:[/red] File not found: {file_path}")
            sys.exit(1)

        # Check if it's a file
        if not file_path.is_file():
            console_err.print(f"[red]Error:[/red] Not a file: {file_path}")
            sys.exit(1)

        # Read and parse JSON
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        # Display file info
        file_size = file_path.stat().st_size
        size_str = _format_size(file_size)
        console.print(f"\n[bold cyan]File:[/bold cyan] {file_path}")
        console.print(f"[bold cyan]Size:[/bold cyan] {size_str}\n")

        # Display JSON with rich formatting
        json_str = json.dumps(data, indent=indent, ensure_ascii=False)
        json_display = JSON(json_str, indent=indent, highlight=True)

        # Show in a panel for better visual separation
        panel = Panel(
            json_display,
            title=f"[bold]{file_path.name}[/bold]",
            border_style="cyan",
            expand=False,
        )
        console.print(panel)

    except json.JSONDecodeError as e:
        console_err.print(f"[red]Error:[/red] Invalid JSON in file: {e}")
        sys.exit(1)
    except PermissionError:
        console_err.print(f"[red]Error:[/red] Permission denied: {file_path}")
        sys.exit(1)
    except Exception as e:
        console_err.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@app.command
async def view(
    file_path: Annotated[Path, Parameter(help="Path to ICD-10 annotation JSON file")],
):
    """Launch interactive viewer for ICD-10 annotated clinical notes.

    Displays annotations grouped by ICD-10 code with clickable highlighting
    in the text. Shows all notes in a single scrollable view.

    Args:
        file_path: Path to the ICD-10 annotation JSON file
    """
    try:
        # Import viewer here to avoid loading textual unless needed
        from .viewer import ICD10Viewer

        # Validate file
        if not file_path.exists():
            console_err.print(f"[red]Error:[/red] File not found: {file_path}")
            sys.exit(1)

        if not file_path.is_file():
            console_err.print(f"[red]Error:[/red] Not a file: {file_path}")
            sys.exit(1)

        # Load JSON data
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        # Validate structure
        if "notes" not in data:
            console_err.print(f"[red]Error:[/red] Invalid format - missing 'notes' field")
            sys.exit(1)

        # Launch viewer
        viewer = ICD10Viewer(data, file_path)
        await viewer.run_async()

    except json.JSONDecodeError as e:
        console_err.print(f"[red]Error:[/red] Invalid JSON: {e}")
        sys.exit(1)
    except Exception as e:
        console_err.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


if __name__ == "__main__":
    asyncio.run(app())
