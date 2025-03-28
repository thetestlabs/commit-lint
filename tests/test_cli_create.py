from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from commit_lint.cli import app


@pytest.fixture
def runner():
    return CliRunner()


def test_create_commit_message(runner):
    """Test creating a commit message interactively."""
    mock_format = MagicMock()
    mock_format.prompt_for_message.return_value = "feat: test message"

    mock_result = MagicMock()
    mock_result.valid = True
    mock_format.validate.return_value = mock_result

    with (
        patch("commit_lint.cli.load_config") as mock_load_config,
        patch("commit_lint.cli.get_commit_format") as mock_get_format,
    ):
        mock_load_config.return_value = {"format_type": "conventional"}
        mock_get_format.return_value = mock_format

        result = runner.invoke(app, ["create"])

        assert result.exit_code == 0
        assert "Generated Commit Message" in result.stdout
        assert mock_format.prompt_for_message.called


def test_create_with_output_file(runner):
    """Test creating a commit message and saving to file."""
    mock_format = MagicMock()
    mock_format.prompt_for_message.return_value = "feat: save to file test"

    mock_result = MagicMock()
    mock_result.valid = True
    mock_format.validate.return_value = mock_result

    with runner.isolated_filesystem():
        with (
            patch("commit_lint.cli.load_config") as mock_load_config,
            patch("commit_lint.cli.get_commit_format") as mock_get_format,
        ):
            mock_load_config.return_value = {"format_type": "conventional"}
            mock_get_format.return_value = mock_format

            result = runner.invoke(app, ["create", "--output", "commit-msg.txt"])

            assert result.exit_code == 0
            assert "saved to" in result.stdout

            # Verify file was created with correct content
            with open("commit-msg.txt", "r") as f:
                content = f.read()
                assert content == "feat: save to file test"


def test_create_with_format_override(runner):
    """Test overriding the format type when creating a message."""
    mock_format = MagicMock()
    mock_format.prompt_for_message.return_value = "TEST-123: Jira style message"

    mock_result = MagicMock()
    mock_result.valid = True
    mock_format.validate.return_value = mock_result

    with (
        patch("commit_lint.cli.load_config") as mock_load_config,
        patch("commit_lint.cli.get_commit_format") as mock_get_format,
    ):
        mock_load_config.return_value = {"format_type": "conventional"}  # Default config
        mock_get_format.return_value = mock_format

        result = runner.invoke(app, ["create", "--format-type", "jira"])

        assert result.exit_code == 0
        assert "Using format type: jira" in result.stdout
        # Verify the config was overridden
        assert mock_get_format.call_args[0][0]["format_type"] == "jira"


def test_create_with_invalid_result(runner):
    """Test handling when validation of created message fails."""
    mock_format = MagicMock()
    mock_format.prompt_for_message.return_value = "invalid message"

    mock_result = MagicMock()
    mock_result.valid = False
    mock_result.errors = ["Invalid format", "Missing type"]
    mock_format.validate.return_value = mock_result

    with (
        patch("commit_lint.cli.load_config") as mock_load_config,
        patch("commit_lint.cli.get_commit_format") as mock_get_format,
    ):
        mock_load_config.return_value = {"format_type": "conventional"}
        mock_get_format.return_value = mock_format

        result = runner.invoke(app, ["create"])

        assert result.exit_code == 1  # Should exit with error
        assert "Warning" in result.stdout
        assert "Invalid format" in result.stdout
