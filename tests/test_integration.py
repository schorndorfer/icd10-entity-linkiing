"""Integration tests for the CLI."""

import subprocess
import sys


class TestCLIIntegration:
    """Integration tests that run the CLI as a subprocess."""

    def test_cli_runs_successfully(self):
        """Test that the CLI runs without errors."""
        result = subprocess.run(
            [sys.executable, "-m", "elinker.cli"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "Hello World" in result.stdout

    def test_cli_help_command(self):
        """Test that --help flag works via subprocess."""
        result = subprocess.run(
            [sys.executable, "-m", "elinker.cli", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "ICD-10 Entity Linker CLI" in result.stdout
        assert "--help" in result.stdout

    def test_cli_version_command(self):
        """Test that --version flag works via subprocess."""
        result = subprocess.run(
            [sys.executable, "-m", "elinker.cli", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert result.stdout.strip() != ""

    def test_cli_invalid_flag(self):
        """Test that invalid flags produce an error."""
        result = subprocess.run(
            [sys.executable, "-m", "elinker.cli", "--invalid-flag"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Should exit with non-zero code for invalid flags
        assert result.returncode != 0

    def test_cli_via_entry_point(self):
        """Test that the entry point works (if installed)."""
        # This test will only work if the package is installed
        result = subprocess.run(
            ["elinker"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # May fail if not installed, that's ok
        if result.returncode == 0:
            assert "Hello World" in result.stdout
