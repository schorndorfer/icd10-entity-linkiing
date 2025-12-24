"""CLI for ICD-10 Entity Linker."""

from cyclopts import App
from rich.console import Console

app = App(name="elinker", help="ICD-10 Entity Linker CLI")
console = Console()


@app.default
def main():
    """Display Hello World."""
    console.print("[bold green]Hello World[/bold green]")


if __name__ == "__main__":
    app()
