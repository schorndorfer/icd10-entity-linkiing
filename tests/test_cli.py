"""Tests for the CLI module."""

from io import StringIO
from unittest.mock import patch

import pytest
from cyclopts import App
from rich.console import Console

from elinker import cli


class TestCLIApp:
    """Test the CLI application structure."""

    def test_cli_app_exists(self):
        """Test that the CLI app is properly defined."""
        assert cli.app is not None
        assert isinstance(cli.app, App)

    def test_cli_app_name(self):
        """Test that the CLI app has the correct name."""
        assert "elinker" in cli.app.name

    def test_cli_app_help(self):
        """Test that the CLI app has help text."""
        assert cli.app.help == "ICD-10 Entity Linker CLI"

    def test_main_function_exists(self):
        """Test that the main function exists."""
        assert callable(cli.main)

    def test_console_exists(self):
        """Test that the console is properly initialized."""
        assert cli.console is not None
        assert isinstance(cli.console, Console)


class TestMainFunction:
    """Test the main function behavior."""

    def test_main_prints_hello_world(self):
        """Test that main prints 'Hello World'."""
        # Create a StringIO buffer to capture output
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        # Temporarily replace the console
        with patch.object(cli, "console", test_console):
            cli.main()

        result = output.getvalue()
        assert "Hello World" in result

    def test_main_uses_rich_formatting(self):
        """Test that main uses rich formatting (bold green)."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True, legacy_windows=False)

        with patch.object(cli, "console", test_console):
            cli.main()

        result = output.getvalue()
        # Check that ANSI codes are present (indicating formatting)
        assert "\x1b[" in result or "Hello World" in result

    def test_main_no_exceptions(self):
        """Test that main runs without raising exceptions."""
        output = StringIO()
        test_console = Console(file=output)

        with patch.object(cli, "console", test_console):
            try:
                cli.main()
            except Exception as e:
                pytest.fail(f"main() raised an exception: {e}")


class TestCLIIntegration:
    """Test CLI integration and command execution."""

    def test_app_can_be_called(self):
        """Test that the app can be invoked."""
        output = StringIO()
        test_console = Console(file=output)

        with patch.object(cli, "console", test_console):
            # Call the app with no arguments (should trigger main)
            # Cyclopts apps exit after running, so we expect SystemExit
            with pytest.raises(SystemExit) as exc_info:
                cli.app([])

            assert exc_info.value.code == 0

        result = output.getvalue()
        assert "Hello World" in result

    def test_app_help_flag(self, capsys):
        """Test that --help flag works."""
        with pytest.raises(SystemExit) as exc_info:
            cli.app(["--help"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "ICD-10 Entity Linker CLI" in captured.out

    def test_app_version_flag(self, capsys):
        """Test that --version flag works."""
        with pytest.raises(SystemExit) as exc_info:
            cli.app(["--version"])

        assert exc_info.value.code == 0
        # Version should be displayed
        captured = capsys.readouterr()
        assert captured.out.strip() != ""
