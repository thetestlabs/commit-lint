from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from commit_lint.cli import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


def test_config_file_not_found(runner):
    """Test handling of a non-existent config file."""
    result = runner.invoke(app, ["lint", "--config", "nonexistent.toml", "-m", "test"])

    assert result.exit_code != 0
    assert "not found" in result.stdout.lower() or "not found" in str(result.exception)


def test_invalid_format_type(runner):
    """Test handling of an invalid format type."""
    result = runner.invoke(app, ["lint", "--format-type", "invalid-format", "-m", "test"])

    assert result.exit_code != 0
    # Fix: Check for the actual error message text
    assert "invalid format type" in result.stdout.lower()
    # Also verify that the valid formats are listed
    assert "conventional" in result.stdout.lower()


def test_invalid_message_detection(runner):
    """Test that invalid messages are properly detected."""
    with patch("commit_lint.cli.load_config") as mock_load_config:
        mock_load_config.return_value = {"format_type": "conventional", "types": ["feat", "fix"]}

        with patch("commit_lint.cli.get_commit_format") as mock_get_format:
            mock_format = MagicMock()
            mock_result = MagicMock()
            mock_result.valid = False
            mock_result.errors = ["Invalid type"]
            mock_format.validate.return_value = mock_result
            mock_get_format.return_value = mock_format

            # Run with --no-interactive to ensure we don't hit interactive code paths
            result = runner.invoke(app, ["lint", "-m", "invalid message", "--no-interactive"])

            assert result.exit_code == 1
            assert "invalid" in result.stdout.lower() or "failed" in result.stdout.lower()


def test_create_valid_message(runner):
    """Test creating a valid message directly."""
    with patch("commit_lint.cli.load_config") as mock_load_config:
        mock_load_config.return_value = {"format_type": "conventional", "types": ["feat", "fix"]}

        with patch("commit_lint.cli.get_commit_format") as mock_get_format:
            mock_format = MagicMock()
            # Return a valid message when prompted
            mock_format.prompt_for_message.return_value = "feat: valid created message"

            # Make validation pass
            mock_result_valid = MagicMock()
            mock_result_valid.valid = True
            mock_format.validate.return_value = mock_result_valid

            mock_get_format.return_value = mock_format

            # Use isolated filesystem to create real output file
            with runner.isolated_filesystem():
                # Use create command which is designed for direct generation
                result = runner.invoke(app, ["create", "-o", "message.txt"])

                if result.exit_code != 0:
                    print(f"Output: {result.stdout}")
                    if hasattr(result, "exception"):
                        print(f"Exception: {result.exception}")

                # Check we can create a valid message
                assert result.exit_code == 0
                # Verify the message was written correctly
                with open("message.txt") as f:
                    content = f.read()
                    assert "feat: valid created message" in content
