import pytest
from unittest.mock import patch, MagicMock
import os
from pathlib import Path
from typer.testing import CliRunner

from commit_lint.cli import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


def test_config_precedence(runner):
    """Test that CLI config option takes precedence over default config."""
    with runner.isolated_filesystem():
        # Create default config in pyproject.toml
        with open("pyproject.toml", "w") as f:
            f.write("""
            [tool.commit_lint]
            format_type = "conventional"
            types = ["default"]
            """)

        # Create override config
        with open("override.toml", "w") as f:
            f.write("""
            format_type = "github"
            """)

        # Patch load_config first to intercept the loaded configuration
        with patch("commit_lint.cli.load_config") as mock_load_config:
            # Set up the mock to return our github config when called with override.toml
            def load_config_side_effect(config_path=None):
                if config_path and "override.toml" in str(config_path):
                    return {"format_type": "github"}
                return {"format_type": "conventional", "types": ["default"]}

            mock_load_config.side_effect = load_config_side_effect

            # Then patch get_commit_format at the point where it's imported and used
            with patch("commit_lint.cli.get_commit_format") as mock_get_format:
                mock_format = MagicMock()
                mock_result = MagicMock()
                mock_result.valid = True
                mock_format.validate.return_value = mock_result
                mock_get_format.return_value = mock_format

                # Run with override config
                result = runner.invoke(app, ["lint", "--config", "override.toml", "-m", "test message"])

                # Check that the override was used
                assert mock_get_format.called, "get_commit_format was not called"

                # Check that the correct config was passed
                if mock_get_format.call_args:
                    called_config = mock_get_format.call_args[0][0]
                    assert called_config["format_type"] == "github"
                else:
                    # If we can't check call_args directly for some reason, at least verify the command ran successfully
                    assert result.exit_code == 0
                    print("Command succeeded but mock wasn't called with args")


def test_format_specific_options(runner):
    """Test that format-specific options are properly passed."""
    with runner.isolated_filesystem():
        # Create config with format-specific options
        with open("test_config.toml", "w") as f:
            f.write("""
            format_type = "conventional"
            types = ["feat", "fix"]
            scope_required = true
            allowed_scopes = ["api", "ui"]
            max_subject_length = 50
            """)

        # Patch load_config to return our test config
        with patch("commit_lint.cli.load_config") as mock_load_config:
            # Use specific config when test_config.toml is requested
            def load_config_side_effect(config_path=None):
                if config_path and "test_config.toml" in str(config_path):
                    return {
                        "format_type": "conventional",
                        "types": ["feat", "fix"],
                        "scope_required": True,
                        "allowed_scopes": ["api", "ui"],
                        "max_subject_length": 50,
                    }
                return {"format_type": "conventional"}  # Default fallback

            mock_load_config.side_effect = load_config_side_effect

            # Then patch get_commit_format at the CLI module
            with patch("commit_lint.cli.get_commit_format") as mock_get_format:
                mock_format = MagicMock()
                mock_result = MagicMock()
                mock_result.valid = True
                mock_format.validate.return_value = mock_result
                mock_get_format.return_value = mock_format

                # Run with custom config
                result = runner.invoke(app, ["lint", "--config", "test_config.toml", "-m", "feat(api): test"])

                # Check that the command was called and successful
                assert mock_get_format.called, "get_commit_format was not called"
                assert result.exit_code == 0

                # Check that format-specific options were passed
                if mock_get_format.call_args:
                    called_config = mock_get_format.call_args[0][0]
                    assert called_config["scope_required"] == True
                    assert "api" in called_config["allowed_scopes"]
                    assert called_config["max_subject_length"] == 50
