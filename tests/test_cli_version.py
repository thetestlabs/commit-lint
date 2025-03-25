import pytest
from unittest.mock import patch, MagicMock
import sys
import importlib


def test_version_import_from_metadata():
    """Test version is correctly imported from package metadata."""
    # Save original module if it exists
    original_module = sys.modules.get("commit_lint.cli", None)

    try:
        # Remove the module if it's already loaded
        if "commit_lint.cli" in sys.modules:
            del sys.modules["commit_lint.cli"]

        # Mock the version function before importing
        with patch("importlib.metadata.version") as mock_get_version:
            mock_get_version.return_value = "1.0.0"

            # Now import the module
            import commit_lint.cli

            # Check that version is correctly set
            assert commit_lint.cli.__version__ == "1.0.0"
            mock_get_version.assert_called_once_with("commit-lint")

    finally:
        # Restore original state
        if original_module is not None:
            sys.modules["commit_lint.cli"] = original_module
        elif "commit_lint.cli" in sys.modules:
            del sys.modules["commit_lint.cli"]


def test_version_fallback_to_default():
    """Test version fallback when metadata import fails."""
    # Save original module if it exists
    original_module = sys.modules.get("commit_lint.cli", None)

    try:
        # Remove the module if it's already loaded
        if "commit_lint.cli" in sys.modules:
            del sys.modules["commit_lint.cli"]

        # Mock the version function to raise an exception
        with patch("importlib.metadata.version") as mock_get_version:
            mock_get_version.side_effect = ImportError("No metadata found")

            # Now import the module
            import commit_lint.cli

            # Check that the fallback version is used
            assert commit_lint.cli.__version__ == "0.1.0.dev0"

    finally:
        # Restore original state
        if original_module is not None:
            sys.modules["commit_lint.cli"] = original_module
        elif "commit_lint.cli" in sys.modules:
            del sys.modules["commit_lint.cli"]
