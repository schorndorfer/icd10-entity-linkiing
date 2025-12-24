"""Pytest configuration and shared fixtures."""

from io import StringIO

import pytest
from rich.console import Console


@pytest.fixture
def mock_console():
    """Create a mock console for testing output."""
    output = StringIO()
    console = Console(file=output, force_terminal=True)
    return console, output


@pytest.fixture
def plain_console():
    """Create a plain console without formatting for testing."""
    output = StringIO()
    console = Console(file=output, force_terminal=False, legacy_windows=False)
    return console, output
