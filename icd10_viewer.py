"""
ICD-10 Clinical Entity Viewer - Streamlit App
Displays clinical notes with interactive ICD-10 code annotations.
"""

import streamlit as st
import json
import os
from pathlib import Path
from typing import Dict, List, Any
import html

# Page configuration
st.set_page_config(
    page_title="ICD-10 Clinical Entity Viewer",
    page_icon="🏥",
    layout="wide"
)

# Constants
DATA_DIR = Path("/Users/williamthompson/Code/projects/clinical-entity-extraction/projects/icd10-entity-linking/data/MDACE/with_text/gold/Inpatient")


def load_json_files(directory: Path) -> Dict[str, Path]:
    """Load all JSON file paths from the directory recursively."""
    json_files = {}
    for json_path in directory.rglob("*.json"):
        # Create a display name from the path
        relative_path = json_path.relative_to(directory)
        display_name = str(relative_path)
        json_files[display_name] = json_path
    return dict(sorted(json_files.items()))


def load_json_content(file_path: Path) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def get_annotation_color(code_system: str) -> tuple:
    """Return color based on code system."""
    if code_system == "ICD-10-CM":
        return "#FFB6C1", "#8B0000"  # Light pink bg, dark red text (Diagnosis)
    elif code_system == "ICD-10-PCS":
        return "#90EE90", "#006400"  # Light green bg, dark green text (Procedure)
    else:
        return "#E0E0E0", "#333333"  # Gray


def create_highlighted_text(text: str, annotations: List[Dict], selected_annotation_idx: int = None) -> str:
    """Create HTML with highlighted annotations."""
    if not annotations:
        return f"<pre style='white-space: pre-wrap; font-family: monospace; color: #333333;'>{html.escape(text)}</pre>"

    # Sort annotations by begin position (reverse for processing from end)
    sorted_annotations = sorted(enumerate(annotations), key=lambda x: x[1]['begin'])

    # Build the highlighted text
    result_parts = []
    last_end = 0

    for orig_idx, ann in sorted_annotations:
        begin = ann['begin']
        end = ann['end']

        # Add text before this annotation
        if begin > last_end:
            result_parts.append(html.escape(text[last_end:begin]))

        # Get colors
        bg_color, text_color = get_annotation_color(ann.get('code_system', ''))

        # Check if this is the selected annotation
        is_selected = selected_annotation_idx is not None and orig_idx == selected_annotation_idx

        # Create the highlighted span
        border_style = "border: 3px solid #FF0000; box-shadow: 0 0 10px #FF0000;" if is_selected else ""
        span_id = f"annotation-{orig_idx}"

        highlighted_text = html.escape(text[begin:end])
        result_parts.append(
            f'<span id="{span_id}" style="background-color: {bg_color}; color: {text_color}; '
            f'padding: 2px 4px; border-radius: 3px; {border_style}">'
            f'{highlighted_text}</span>'
        )

        last_end = end

    # Add remaining text
    if last_end < len(text):
        result_parts.append(html.escape(text[last_end:]))

    final_html = ''.join(result_parts)
    return f"<pre style='white-space: pre-wrap; font-family: monospace; line-height: 1.6; color: #333333;'>{final_html}</pre>"


def main():
    st.title("ICD-10 Clinical Entity Viewer")

    # Custom CSS
    st.markdown("""
    <style>
    .diagnosis-badge {
        background-color: #FFB6C1;
        color: #8B0000;
        padding: 8px 12px;
        border-radius: 5px;
        margin: 4px;
        display: inline-block;
        cursor: pointer;
        border: 2px solid transparent;
        transition: all 0.2s;
    }
    .diagnosis-badge:hover {
        border-color: #8B0000;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .procedure-badge {
        background-color: #90EE90;
        color: #006400;
        padding: 8px 12px;
        border-radius: 5px;
        margin: 4px;
        display: inline-block;
        cursor: pointer;
        border: 2px solid transparent;
        transition: all 0.2s;
    }
    .procedure-badge:hover {
        border-color: #006400;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .note-container {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        background-color: #fafafa;
        color: #333333;
        max-height: 600px;
        overflow-y: auto;
    }
    .stButton > button {
        width: 100%;
        text-align: left;
        padding: 10px;
        margin: 2px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Load available JSON files
    json_files = load_json_files(DATA_DIR)

    if not json_files:
        st.error(f"No JSON files found in {DATA_DIR}")
        return

    # Sidebar for file selection
    st.sidebar.header("Select File")
    selected_file = st.sidebar.selectbox(
        "Choose a clinical record:",
        options=list(json_files.keys()),
        format_func=lambda x: x.split('/')[-1]  # Show just filename
    )

    if selected_file:
        # Load the selected file
        data = load_json_content(json_files[selected_file])

        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**Hospital Admission ID:** {data.get('hadm_id', 'N/A')}")

        # Get all notes
        notes = data.get('notes', [])

        if not notes:
            st.warning("No notes found in this file.")
            return

        # Note selector
        st.sidebar.header("Select Note")
        note_options = [f"{n['category']} - {n['description']}" for n in notes]
        selected_note_idx = st.sidebar.selectbox(
            "Choose a note:",
            range(len(notes)),
            format_func=lambda i: note_options[i]
        )

        selected_note = notes[selected_note_idx]
        annotations = selected_note.get('annotations', [])

        # Initialize session state for selected annotation
        if 'selected_annotation' not in st.session_state:
            st.session_state.selected_annotation = None

        # Main content area with two columns
        col1, col2 = st.columns([2, 1])

        with col2:
            st.subheader("ICD-10 Codes")

            # Separate diagnoses and procedures
            diagnoses = [a for a in annotations if a.get('code_system') == 'ICD-10-CM']
            procedures = [a for a in annotations if a.get('code_system') == 'ICD-10-PCS']

            # Legend
            st.markdown("""
            <div style="margin-bottom: 15px;">
                <span style="background-color: #FFB6C1; padding: 4px 8px; border-radius: 3px; margin-right: 10px;">Diagnosis (CM)</span>
                <span style="background-color: #90EE90; padding: 4px 8px; border-radius: 3px;">Procedure (PCS)</span>
            </div>
            """, unsafe_allow_html=True)

            if diagnoses:
                st.markdown("**Diagnoses (ICD-10-CM)**")
                for i, ann in enumerate(annotations):
                    if ann.get('code_system') == 'ICD-10-CM':
                        original_idx = annotations.index(ann)
                        btn_label = f"{ann['code']}: {ann['description'][:50]}..."
                        if len(ann['description']) <= 50:
                            btn_label = f"{ann['code']}: {ann['description']}"

                        if st.button(
                            btn_label,
                            key=f"diag_{original_idx}",
                            help=f"Click to highlight: '{ann['covered_text']}'"
                        ):
                            st.session_state.selected_annotation = original_idx
                            st.rerun()

            if procedures:
                st.markdown("**Procedures (ICD-10-PCS)**")
                for i, ann in enumerate(annotations):
                    if ann.get('code_system') == 'ICD-10-PCS':
                        original_idx = annotations.index(ann)
                        btn_label = f"{ann['code']}: {ann['description'][:50]}..."
                        if len(ann['description']) <= 50:
                            btn_label = f"{ann['code']}: {ann['description']}"

                        if st.button(
                            btn_label,
                            key=f"proc_{original_idx}",
                            help=f"Click to highlight: '{ann['covered_text']}'"
                        ):
                            st.session_state.selected_annotation = original_idx
                            st.rerun()

            if not annotations:
                st.info("No ICD-10 codes annotated in this note.")

            # Clear selection button
            if st.session_state.selected_annotation is not None:
                st.markdown("---")
                if st.button("Clear Selection", key="clear"):
                    st.session_state.selected_annotation = None
                    st.rerun()

                # Show selected annotation details
                sel_ann = annotations[st.session_state.selected_annotation]
                st.markdown("**Selected Code Details:**")
                st.markdown(f"- **Code:** {sel_ann['code']}")
                st.markdown(f"- **System:** {sel_ann['code_system']}")
                st.markdown(f"- **Description:** {sel_ann['description']}")
                st.markdown(f"- **Covered Text:** \"{sel_ann['covered_text']}\"")
                st.markdown(f"- **Position:** {sel_ann['begin']}-{sel_ann['end']}")

        with col1:
            st.subheader(f"Clinical Note: {selected_note['category']}")
            st.caption(f"Note ID: {selected_note['note_id']} | Description: {selected_note['description']}")

            # Create highlighted text
            note_text = selected_note.get('text', '')
            highlighted_html = create_highlighted_text(
                note_text,
                annotations,
                st.session_state.selected_annotation
            )

            # JavaScript to scroll to selected annotation
            scroll_script = ""
            if st.session_state.selected_annotation is not None:
                scroll_script = f"""
                <script>
                    setTimeout(function() {{
                        var element = document.getElementById('annotation-{st.session_state.selected_annotation}');
                        if (element) {{
                            element.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        }}
                    }}, 100);
                </script>
                """

            # Display the note with highlighting
            st.markdown(
                f'<div class="note-container">{highlighted_html}</div>{scroll_script}',
                unsafe_allow_html=True
            )

            # Statistics
            st.markdown("---")
            stats_col1, stats_col2, stats_col3 = st.columns(3)
            with stats_col1:
                st.metric("Total Annotations", len(annotations))
            with stats_col2:
                st.metric("Diagnoses", len(diagnoses))
            with stats_col3:
                st.metric("Procedures", len(procedures))


if __name__ == "__main__":
    main()
