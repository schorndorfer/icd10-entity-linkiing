"""Tests for the view-json command."""

import json
import subprocess
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
from rich.console import Console

from elinker import cli


class TestViewJsonCommand:
    """Test the view_json command."""

    def test_view_json_command_exists(self):
        """Test that view_json command exists."""
        assert hasattr(cli, "view_json")
        assert callable(cli.view_json)

    def test_view_json_with_valid_file(self, tmp_path):
        """Test viewing a valid JSON file."""
        # Create a test JSON file
        test_data = {"name": "test", "value": 123, "items": ["a", "b", "c"]}
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps(test_data))

        # Capture output
        output = StringIO()
        test_console = Console(file=output)

        with patch.object(cli, "console", test_console):
            cli.view_json(json_file)

        result = output.getvalue()
        assert "test.json" in result
        assert "test" in result
        assert "123" in result

    def test_view_json_with_nested_structure(self, tmp_path):
        """Test viewing a nested JSON structure."""
        test_data = {
            "patient": {"id": "123", "name": "John", "age": 45},
            "diagnoses": [{"code": "E11.9", "desc": "Diabetes"}],
        }
        json_file = tmp_path / "nested.json"
        json_file.write_text(json.dumps(test_data))

        output = StringIO()
        test_console = Console(file=output)

        with patch.object(cli, "console", test_console):
            cli.view_json(json_file)

        result = output.getvalue()
        assert "patient" in result
        assert "diagnoses" in result
        assert "E11.9" in result

    def test_view_json_with_custom_indent(self, tmp_path):
        """Test viewing JSON with custom indentation."""
        test_data = {"key": "value"}
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps(test_data))

        output = StringIO()
        test_console = Console(file=output)

        with patch.object(cli, "console", test_console):
            cli.view_json(json_file, indent=4)

        result = output.getvalue()
        assert "key" in result
        assert "value" in result

    def test_view_json_file_not_found(self, tmp_path):
        """Test error handling when file doesn't exist."""
        non_existent = tmp_path / "does_not_exist.json"

        output = StringIO()
        test_console_err = Console(file=output)

        with patch.object(cli, "console_err", test_console_err):
            with pytest.raises(SystemExit) as exc_info:
                cli.view_json(non_existent)

            assert exc_info.value.code == 1

        result = output.getvalue()
        assert "File not found" in result or "not found" in result.lower()

    def test_view_json_invalid_json(self, tmp_path):
        """Test error handling with invalid JSON."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{invalid json}")

        output = StringIO()
        test_console_err = Console(file=output)

        with patch.object(cli, "console_err", test_console_err):
            with pytest.raises(SystemExit) as exc_info:
                cli.view_json(invalid_file)

            assert exc_info.value.code == 1

        result = output.getvalue()
        assert "Invalid JSON" in result or "JSON" in result

    def test_view_json_not_a_file(self, tmp_path):
        """Test error handling when path is a directory."""
        directory = tmp_path / "testdir"
        directory.mkdir()

        output = StringIO()
        test_console_err = Console(file=output)

        with patch.object(cli, "console_err", test_console_err):
            with pytest.raises(SystemExit) as exc_info:
                cli.view_json(directory)

            assert exc_info.value.code == 1

        result = output.getvalue()
        assert "Not a file" in result or "not a file" in result.lower()

    def test_view_json_shows_file_size(self, tmp_path):
        """Test that file size is displayed."""
        test_data = {"test": "data"}
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps(test_data))

        output = StringIO()
        test_console = Console(file=output)

        with patch.object(cli, "console", test_console):
            cli.view_json(json_file)

        result = output.getvalue()
        assert "Size:" in result
        assert "B" in result  # Bytes unit

    def test_view_json_unicode_content(self, tmp_path):
        """Test viewing JSON with Unicode characters."""
        test_data = {"message": "Hello 世界", "emoji": "🎉"}
        json_file = tmp_path / "unicode.json"
        json_file.write_text(json.dumps(test_data, ensure_ascii=False), encoding="utf-8")

        output = StringIO()
        test_console = Console(file=output)

        with patch.object(cli, "console", test_console):
            cli.view_json(json_file)

        result = output.getvalue()
        # Should handle unicode without errors
        assert "message" in result


class TestFormatSize:
    """Test the _format_size helper function."""

    def test_format_size_bytes(self):
        """Test formatting bytes."""
        result = cli._format_size(100)
        assert "100.00 B" == result

    def test_format_size_kilobytes(self):
        """Test formatting kilobytes."""
        result = cli._format_size(1024)
        assert "1.00 KB" == result

    def test_format_size_megabytes(self):
        """Test formatting megabytes."""
        result = cli._format_size(1024 * 1024)
        assert "1.00 MB" == result

    def test_format_size_gigabytes(self):
        """Test formatting gigabytes."""
        result = cli._format_size(1024 * 1024 * 1024)
        assert "1.00 GB" == result

    def test_format_size_decimal(self):
        """Test formatting with decimal values."""
        result = cli._format_size(1536)  # 1.5 KB
        assert "1.50 KB" == result


class TestViewJsonIntegration:
    """Integration tests for view-json command."""

    def test_view_json_via_cli(self, tmp_path):
        """Test running view-json via CLI."""
        test_data = {"test": "integration"}
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps(test_data))

        result = subprocess.run(
            [sys.executable, "-m", "elinker.cli", "view-json", str(json_file)],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "test" in result.stdout
        assert "integration" in result.stdout

    def test_view_json_help_via_cli(self):
        """Test view-json help via CLI."""
        result = subprocess.run(
            [sys.executable, "-m", "elinker.cli", "view-json", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "view-json" in result.stdout.lower() or "view_json" in result.stdout.lower()
        assert "JSON" in result.stdout

    def test_view_json_with_real_fixture(self):
        """Test with the actual fixture file."""
        fixture_path = Path(__file__).parent / "fixtures" / "sample.json"

        if fixture_path.exists():
            result = subprocess.run(
                [sys.executable, "-m", "elinker.cli", "view-json", str(fixture_path)],
                capture_output=True,
                text=True,
                timeout=5,
            )

            assert result.returncode == 0
            assert "patient" in result.stdout or "sample.json" in result.stdout
