"""Interactive viewer for ICD-10 annotated clinical notes."""

from pathlib import Path
from typing import Any

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Checkbox, Footer, Header, Static


class AnnotationGroup:
    """Group of annotations sharing the same ICD-10 code."""

    def __init__(self, code: str, code_system: str, description: str):
        self.code = code
        self.code_system = code_system
        self.description = description
        self.instances = []  # List of (note_idx, annotation_dict)

    def add_instance(self, note_idx: int, annotation: dict):
        """Add an annotation instance to this group."""
        self.instances.append((note_idx, annotation))

    @property
    def count(self) -> int:
        """Total number of instances of this code."""
        return len(self.instances)

    def __repr__(self):
        return f"<AnnotationGroup {self.code}: {self.count} instances>"


class NoteData:
    """Processed note with character offset tracking."""

    def __init__(
        self,
        note_id: int,
        category: str,
        description: str,
        text: str,
        annotations: list,
        start_offset: int,
    ):
        self.note_id = note_id
        self.category = category
        self.description = description
        self.text = text
        self.annotations = annotations
        self.start_offset = start_offset  # Character offset in combined text
        self.end_offset = start_offset + len(text)


class AnnotationItem(Horizontal):
    """A clickable annotation item with checkbox showing ICD code."""

    def __init__(self, group: AnnotationGroup, group_id: int):
        super().__init__(classes="annotation-item", id=f"annotation-item-{group_id}")
        self.group = group
        self.group_id = group_id

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        # Format label: "S02.0XXB (ICD-10-CM): Fracture of vault of skull... (x3)"
        label = (
            f"[bold cyan]{self.group.code}[/bold cyan] "
            f"({self.group.code_system}): "
            f"{self.group.description[:50]}{'...' if len(self.group.description) > 50 else ''} "
            f"[dim]({self.group.count})[/dim]"
        )

        yield Checkbox(label, id=f"checkbox-{self.group_id}")

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox state changes."""
        app = self.app
        if isinstance(app, ICD10Viewer):
            if event.value:
                app.add_selected_group(self.group_id)
            else:
                app.remove_selected_group(self.group_id)


class ICD10Viewer(App):
    """Interactive viewer for ICD-10 annotated clinical notes."""

    CSS = """
    Screen {
        background: $surface;
    }

    #file-info {
        height: auto;
        padding: 0 1;
        background: $panel;
        border: solid $primary;
        margin: 1 2;
    }

    #annotations-panel {
        height: 40%;
        padding: 1;
        background: $panel;
        border: solid $primary;
        margin: 1 2;
    }

    #text-panel {
        height: 55%;
        padding: 1;
        background: $panel;
        border: solid $primary;
        margin: 1 2;
    }

    .annotation-item {
        height: auto;
        padding: 0;
        margin: 0 0 0 0;
    }

    .annotation-item:hover {
        background: $primary 10%;
    }

    .note-header {
        height: auto;
        padding: 1;
        margin: 1 0;
        background: $boost;
        border: solid $primary;
    }

    .note-text {
        height: auto;
        padding: 1;
    }

    .info-text {
        padding: 0 1;
    }
    """

    # Reactive properties
    selected_groups: reactive[set] = reactive(set())

    def __init__(self, data: dict, file_path: Path):
        super().__init__()
        self.data = data
        self.file_path = file_path

        # Process data
        self.hadm_id = data.get("hadm_id", "Unknown")
        self.annotation_groups = {}  # code -> AnnotationGroup
        self.notes = []  # List of NoteData

        self._process_data()

    def _process_data(self):
        """Transform JSON data into viewer-friendly structure."""
        # Build annotation groups and note data
        current_offset = 0

        for note_idx, note_dict in enumerate(self.data.get("notes", [])):
            # Create note data
            note_data = NoteData(
                note_id=note_dict.get("note_id", note_idx),
                category=note_dict.get("category", "Unknown"),
                description=note_dict.get("description", ""),
                text=note_dict.get("text", ""),
                annotations=note_dict.get("annotations", []),
                start_offset=current_offset,
            )
            self.notes.append(note_data)
            current_offset = note_data.end_offset

            # Group annotations by code
            for annotation in note_dict.get("annotations", []):
                code = annotation.get("code", "")

                if code not in self.annotation_groups:
                    self.annotation_groups[code] = AnnotationGroup(
                        code=code,
                        code_system=annotation.get("code_system", ""),
                        description=annotation.get("description", ""),
                    )

                self.annotation_groups[code].add_instance(note_idx, annotation)

        # Sort groups by code
        self.sorted_groups = sorted(self.annotation_groups.values(), key=lambda g: g.code)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        yield self._create_file_info()
        yield self._create_annotations_panel()
        yield self._create_text_panel()
        yield Footer()

    def _create_file_info(self) -> Container:
        """Create file information header."""
        info_text = (
            f"[bold]File:[/bold] {self.file_path.name}  |  "
            f"[bold]HADM ID:[/bold] {self.hadm_id}  |  "
            f"[bold]Notes:[/bold] {len(self.notes)}  |  "
            f"[bold]Unique Codes:[/bold] {len(self.annotation_groups)}"
        )

        container = Vertical(Static(info_text, classes="info-text"), id="file-info")
        container.border_title = "Document Information"
        return container

    def _create_annotations_panel(self) -> Container:
        """Create panel showing grouped annotations."""
        widgets = []

        if not self.sorted_groups:
            widgets.append(Static("No annotations found", classes="annotation-item"))
        else:
            for idx, group in enumerate(self.sorted_groups):
                widgets.append(AnnotationItem(group, idx))

        container = VerticalScroll(*widgets, id="annotations-panel")
        container.border_title = f"Annotations by ICD-10 Code ({len(self.sorted_groups)} codes)"
        return container

    def _create_text_panel(self) -> Container:
        """Create panel showing all notes with text."""
        widgets = []

        for note in self.notes:
            # Note header
            header_text = (
                f"[bold cyan]Note {note.note_id}[/bold cyan] - "
                f"[yellow]{note.category}[/yellow]: {note.description}"
            )
            widgets.append(Static(header_text, classes="note-header"))

            # Note text (will be updated with highlighting)
            text_widget = Static(
                note.text, classes="note-text", id=f"note-text-{note.note_id}"
            )
            widgets.append(text_widget)

        container = VerticalScroll(*widgets, id="text-panel")
        container.border_title = "Clinical Notes"
        return container

    def add_selected_group(self, group_id: int):
        """Add a group to the selection."""
        new_selected = set(self.selected_groups)
        new_selected.add(group_id)
        self.selected_groups = new_selected

    def remove_selected_group(self, group_id: int):
        """Remove a group from the selection."""
        new_selected = set(self.selected_groups)
        new_selected.discard(group_id)
        self.selected_groups = new_selected

    def watch_selected_groups(self, new_value: set):
        """React to changes in selected annotation groups."""
        if not self.is_mounted:
            return

        # Update checkbox states
        for idx in range(len(self.sorted_groups)):
            try:
                checkbox = self.query_one(f"#checkbox-{idx}", Checkbox)
                checkbox.value = idx in new_value
            except Exception:
                pass

        # Update text highlighting
        self._update_text_highlighting()

    def _update_text_highlighting(self):
        """Update text highlighting based on selected groups."""
        # Get selected annotation groups
        selected_codes = set()
        for group_id in self.selected_groups:
            if group_id < len(self.sorted_groups):
                selected_codes.add(self.sorted_groups[group_id].code)

        # Update each note
        for note in self.notes:
            try:
                text_widget = self.query_one(f"#note-text-{note.note_id}", Static)

                if not selected_codes:
                    # No selection - show plain text
                    text_widget.update(note.text)
                else:
                    # Highlight matching annotations
                    highlighted = self._highlight_text(
                        note.text, note.annotations, selected_codes
                    )
                    text_widget.update(highlighted)
            except Exception:
                pass

    def _highlight_text(
        self, text: str, annotations: list, selected_codes: set
    ) -> Text:
        """Apply highlighting to text based on selected codes.

        Args:
            text: Original note text
            annotations: List of annotation dicts
            selected_codes: Set of ICD codes to highlight

        Returns:
            Rich Text object with markup
        """
        # Collect spans to highlight
        highlight_spans = []
        for annotation in annotations:
            if annotation.get("code") in selected_codes:
                begin = annotation.get("begin", 0)
                end = annotation.get("end", 0)

                # Validate positions
                if 0 <= begin < len(text) and begin < end <= len(text):
                    highlight_spans.append(
                        {"begin": begin, "end": end, "code": annotation.get("code")}
                    )

        # Sort by position
        highlight_spans.sort(key=lambda x: x["begin"])

        # Build Rich Text with highlighting
        rich_text = Text()
        last_pos = 0

        for span in highlight_spans:
            # Add text before highlight
            if span["begin"] > last_pos:
                rich_text.append(text[last_pos : span["begin"]])

            # Add highlighted text
            highlighted_segment = text[span["begin"] : span["end"]]
            rich_text.append(highlighted_segment, style="bold yellow on blue")

            last_pos = span["end"]

        # Add remaining text
        if last_pos < len(text):
            rich_text.append(text[last_pos:])

        return rich_text
