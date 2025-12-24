"""Tests for the package structure and metadata."""

import re

import elinker


class TestPackageMetadata:
    """Test package metadata and structure."""

    def test_version_exists(self):
        """Test that the package has a version."""
        assert hasattr(elinker, "__version__")
        assert elinker.__version__ is not None

    def test_version_format(self):
        """Test that version follows semantic versioning."""
        version = elinker.__version__
        # Match semver pattern (e.g., 0.1.0, 1.2.3, etc.)
        pattern = r"^\d+\.\d+\.\d+$"
        assert re.match(pattern, version), f"Version {version} doesn't match semver format"

    def test_package_name(self):
        """Test that the package has the correct name."""
        assert elinker.__name__ == "elinker"

    def test_package_docstring(self):
        """Test that the package has a docstring."""
        assert elinker.__doc__ is not None
        assert "ICD-10" in elinker.__doc__
