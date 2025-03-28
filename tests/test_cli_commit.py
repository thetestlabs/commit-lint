from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from commit_lint.cli import app


@pytest.fixture
def runner():
    return CliRunner()


def test_commit_successful(runner):
    """Test successful commit creation and submission."""
    mock_format = MagicMock()
    mock_format.prompt_for_message.return_value = "feat: test commit"

    mock_result = MagicMock()
    mock_result.valid = True
    mock_format.validate.return_value = mock_result

    with (
        patch("commit_lint.cli.load_config") as mock_load_config,
        patch("commit_lint.cli.get_commit_format") as mock_get_format,
        patch("commit_lint.cli.subprocess.run") as mock_run,
        patch("tempfile.NamedTemporaryFile"),
    ):
        # Mock staged changes check
        mock_diff = MagicMock()
        mock_diff.stdout = "file1.py\nfile2.py"
        mock_diff.returncode = 0

        # Mock successful commit
        mock_commit = MagicMock()
        mock_commit.stdout = "Created commit abc123"
        mock_commit.returncode = 0

        # Set up run side effects for different commands
        mock_run.side_effect = [mock_diff, mock_commit]

        mock_load_config.return_value = {"format_type": "conventional"}
        mock_get_format.return_value = mock_format

        result = runner.invoke(app, ["commit"])

        assert result.exit_code == 0
        assert "committed successfully" in result.stdout.lower()

        # Verify git command
        assert any("git commit" in " ".join(call_args[0][0]) for call_args in mock_run.call_args_list)


def test_commit_no_staged_changes(runner):
    """Test handling when there are no staged changes."""
    mock_format = MagicMock()
    mock_format.prompt_for_message.return_value = "feat: test with no changes"

    mock_result = MagicMock()
    mock_result.valid = True
    mock_format.validate.return_value = mock_result

    with (
        patch("commit_lint.cli.load_config") as mock_load_config,
        patch("commit_lint.cli.get_commit_format") as mock_get_format,
        patch("commit_lint.cli.subprocess.run") as mock_run,
        patch("typer.confirm") as mock_confirm,
    ):
        # Mock empty staged changes
        mock_diff = MagicMock()
        mock_diff.stdout = ""
        mock_diff.returncode = 0

        # Mock successful add and commit
        mock_add = MagicMock()
        mock_add.returncode = 0

        mock_commit = MagicMock()
        mock_commit.stdout = "Created commit abc123"
        mock_commit.returncode = 0

        # Set up run side effects for different commands
        mock_run.side_effect = [mock_diff, mock_add, mock_commit]

        # User confirms adding all changes
        mock_confirm.return_value = True

        mock_load_config.return_value = {"format_type": "conventional"}
        mock_get_format.return_value = mock_format

        result = runner.invoke(app, ["commit"])

        assert result.exit_code == 0
        assert "No staged changes" in result.stdout
        assert "All changes staged" in result.stdout

        # Verify git add command was called
        assert any("git add" in " ".join(call_args[0][0]) for call_args in mock_run.call_args_list)


def test_commit_with_no_verify(runner):
    """Test commit with --no-verify flag."""
    mock_format = MagicMock()
    mock_format.prompt_for_message.return_value = "feat: skip hooks"

    mock_result = MagicMock()
    mock_result.valid = True
    mock_format.validate.return_value = mock_result

    with (
        patch("commit_lint.cli.load_config") as mock_load_config,
        patch("commit_lint.cli.get_commit_format") as mock_get_format,
        patch("commit_lint.cli.subprocess.run") as mock_run,
    ):
        # Mock staged changes check
        mock_diff = MagicMock()
        mock_diff.stdout = "file1.py"
        mock_diff.returncode = 0

        # Mock successful commit
        mock_commit = MagicMock()
        mock_commit.stdout = "Created commit abc123"
        mock_commit.returncode = 0

        # Set up run side effects for different commands
        mock_run.side_effect = [mock_diff, mock_commit]

        mock_load_config.return_value = {"format_type": "conventional"}
        mock_get_format.return_value = mock_format

        result = runner.invoke(app, ["commit", "--no-verify"])

        assert result.exit_code == 0
        assert "Skipping pre-commit hooks" in result.stdout

        # Verify --no-verify was passed to git command
        git_cmd_args = None
        for call in mock_run.call_args_list:
            if "git commit" in " ".join(call[0][0]):
                git_cmd_args = call[0][0]
                break

        assert "--no-verify" in git_cmd_args
