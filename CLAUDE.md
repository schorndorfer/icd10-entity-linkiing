# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an ICD-10 entity linking and extraction tool for clinical text. The project works with the MDACE (Medical Data Annotation for Clinical Entities) dataset and provides tools to view, analyze, and process ICD-10 code annotations in clinical notes.

## Key Commands

### Package Management (using uv)
```bash
# Install package in editable mode with dependencies
uv pip install -e .

# Install with development dependencies
uv pip install -e ".[dev]"
```

### Running the Application
```bash
# Run the CLI tool
uv run elinker

# View ICD-10 annotated clinical notes (interactive TUI)
uv run elinker view <path-to-json-file>

# View JSON files with rich formatting
uv run elinker view-json <path-to-json-file>

# Alternative: use python module directly
python -m elinker.cli
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=elinker --cov-report=html

# Run specific test file
pytest tests/test_cli.py

# Run single test
pytest tests/test_cli.py::TestCLIApp::test_cli_app_exists
```

### Code Quality
```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type check (note: currently configured with loose settings)
mypy elinker/
```

### Streamlit Viewer
```bash
# Run the Streamlit-based ICD-10 viewer (from root directory)
streamlit run icd10_viewer.py
```

## Architecture

### Package Structure
- **src/elinker/**: Main package source code
  - **cli.py**: CLI implementation using cyclopts. Entry point for the `elinker` command with subcommands for viewing JSON and ICD-10 annotations
  - **viewer.py**: Interactive TUI (Textual) for viewing ICD-10 annotated clinical notes with clickable code highlighting
  - **__init__.py**: Package initialization with version info

- **tests/**: Test suite using pytest
  - **conftest.py**: Shared pytest fixtures (mock consoles)
  - **test_cli.py**: Unit tests for CLI app structure
  - **test_integration.py**: Integration tests running CLI as subprocess
  - **test_package.py**: Package metadata tests
  - **test_view_json.py**: Tests for view-json command
  - **fixtures/**: Test data files (sample.json, invalid.json)

- **notebooks/**: Jupyter notebooks for exploration and experimentation
- **experiments/**: Experimental code and results
- **data/**: Data files (gitignored, not in version control)
  - **icd10cm/**: ICD-10-CM code tables and indexes (2026 version)
  - **MDACE/**: Clinical notes dataset with ICD-10 annotations

### CLI Architecture

The CLI is built with **cyclopts** and uses **Rich** for terminal formatting:

1. **Main command** (`elinker`): Displays "Hello World" by default
2. **view-json subcommand**: Displays any JSON file with rich formatting and syntax highlighting
3. **view subcommand**: Launches interactive TUI viewer for ICD-10 annotated files

### Interactive Viewer Architecture

The `ICD10Viewer` (viewer.py) is a **Textual** app with three main components:

1. **Data Processing Layer**:
   - `AnnotationGroup`: Groups annotations by ICD-10 code across all notes
   - `NoteData`: Represents individual clinical notes with character offset tracking
   - Processes JSON data on initialization to create annotation groups and note list

2. **UI Components**:
   - File info panel: Shows metadata (HADM ID, note count, unique code count)
   - Annotations panel (40% height): Scrollable list of ICD-10 codes with checkboxes
   - Text panel (55% height): Scrollable display of all clinical notes
   - Each `AnnotationItem` is a clickable checkbox showing code, system, description, and instance count

3. **Interaction Flow**:
   - User checks/unchecks ICD-10 codes in the annotations panel
   - Viewer highlights matching text spans in all clinical notes using Rich Text markup
   - Reactive properties trigger UI updates when selection changes

### Data Format

The MDACE annotation files follow this structure:
```json
{
  "hadm_id": 100197,
  "notes": [
    {
      "note_id": 25762,
      "category": "Discharge summary",
      "description": "Report",
      "text": "...",
      "annotations": [
        {
          "begin": 374,
          "end": 377,
          "code": "I61.8",
          "code_system": "ICD-10-CM",
          "description": "Other nontraumatic intracerebral hemorrhage",
          "type": "Human",
          "covered_text": "IPH"
        }
      ]
    }
  ]
}
```

Key fields:
- `hadm_id`: Hospital admission ID
- `notes`: Array of clinical notes (discharge summaries, progress notes, etc.)
- `annotations`: Character-offset spans with ICD-10 code, system (ICD-10-CM/PCS), and description

## Dependencies

Key dependencies:
- **anthropic**: Claude API client
- **cyclopts**: Modern CLI framework
- **rich**: Terminal formatting and pretty-printing
- **textual**: TUI framework for interactive viewer
- **streamlit**: Web-based viewer (icd10_viewer.py)
- **dspy**: LLM programming framework
- **litellm**: Multi-provider LLM API
- **mlflow**: Experiment tracking
- **polars**: High-performance dataframes
- **datasets**: HuggingFace datasets library

## Project-Specific Notes

### ICD-10 Code Systems
- **ICD-10-CM**: Clinical Modification codes for diagnoses
- **ICD-10-PCS**: Procedure Coding System for procedures

### Data Sources
- ICD-10-CM 2026 official tables and indexes are in `data/icd10cm/`
- The `diagnoses_recursive.json` file contains hierarchical ICD-10 code structure
- MDACE dataset contains real clinical notes with expert annotations

### Tool Configuration
- **ruff**: Line length 100, Python 3.11+ target, notebooks and data excluded
- **pytest**: Auto-discovery of test_*.py files, coverage reports to htmlcov/
- **mypy**: Loose configuration (no strict type checking yet)

### Environment
- Python 3.11+ required
- Uses uv for fast package management
- Virtual environment in .venv/
