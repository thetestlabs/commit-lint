from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from commit_lint.cli import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


def test_lint_command_valid_message(runner):
    """Test lint command with valid message."""
    with patch("commit_lint.config.load_config") as mock_load_config:
        mock_load_config.return_value = {"format_type": "conventional", "types": ["feat", "fix"]}

        # Add this patch first to intercept any direct creation of ConventionalCommitResult
        with patch("commit_lint.formats.conventional.ConventionalCommitResult") as mock_result_class:
            # Configure what happens when ConventionalCommitResult is instantiated
            mock_result_instance = MagicMock()
            mock_result_instance.valid = True
            mock_result_class.return_value = mock_result_instance

            # Then continue with your existing mocks
            with patch("commit_lint.formats.get_commit_format") as mock_get_format:
                mock_format = MagicMock()
                # This creates a basic mock with valid=True
                mock_result = MagicMock()
                mock_result.valid = True
                mock_format.validate.return_value = mock_result
                mock_get_format.return_value = mock_format

                result = runner.invoke(app, ["lint", "-m", "feat: valid message"])

                assert result.exit_code == 0
                assert "valid" in result.stdout.lower()


def test_lint_command_invalid_message(runner):
    """Test lint command with invalid message."""
    with patch("commit_lint.config.load_config") as mock_load_config:
        mock_load_config.return_value = {"format_type": "conventional", "types": ["feat", "fix"]}

        # Patch ConventionalCommitResult first
        with patch("commit_lint.formats.conventional.ConventionalCommitResult") as mock_result_class:
            mock_result_instance = MagicMock()
            mock_result_instance.valid = False
            mock_result_instance.errors = ["Commit message does not follow Conventional Commits format"]
            mock_result_class.return_value = mock_result_instance

            # Continue with existing mocks
            with patch("commit_lint.formats.get_commit_format") as mock_get_format:
                mock_format = MagicMock()
                mock_result = MagicMock()
                mock_result.valid = False
                mock_result.errors = ["Commit message does not follow Conventional Commits format"]
                mock_format.validate.return_value = mock_result
                mock_get_format.return_value = mock_format

                result = runner.invoke(app, ["lint", "-m", "invalid message", "--no-interactive"])

                assert result.exit_code == 1
                # Check for the actual message that appears in the output
                assert "failed" in result.stdout.lower()
                assert "conventional commits format" in result.stdout.lower()


def test_create_command_success(runner):
    """Test create command generates valid message."""
    with patch("commit_lint.config.load_config") as mock_load_config:
        mock_load_config.return_value = {"format_type": "conventional", "types": ["feat", "fix"]}

        # Add this patch to handle any attempts to create a ConventionalCommitResult
        with patch("commit_lint.formats.conventional.ConventionalCommitResult") as MockResult:
            # Configure the mock class
            mock_result_instance = MagicMock()
            mock_result_instance.valid = True
            MockResult.return_value = mock_result_instance

            # Continue with your existing mocks
            with (
                patch("questionary.select") as mock_select,
                patch("questionary.text") as mock_text,
                patch("questionary.confirm") as mock_confirm,
            ):
                # Set up questionary mocks to return specific values
                mock_select.return_value.ask.return_value = "feat"  # Type selection
                mock_text.return_value.ask.side_effect = ["", "test message", ""]  # Scope, description, body
                mock_confirm.return_value.ask.return_value = False  # For "breaking change" and other confirms

                # Run the command with output to a file
                with runner.isolated_filesystem():
                    result = runner.invoke(app, ["create", "-o", "message.txt"], catch_exceptions=False)

                    print(f"Exit code: {result.exit_code}")
                    print(f"Output: {result.stdout}")

                    # Check if the command succeeded and the file was created
                    assert result.exit_code == 0
                    assert Path("message.txt").exists()

                    # Verify content contains our mocked responses
                    with open("message.txt") as f:
                        content = f.read()
                        assert "feat: test message" in content


def test_init_command_creates_config(runner):
    """Test init command creates config file."""
    with runner.isolated_filesystem():
        with patch("tomli_w.dump") as mock_dump:
            # Mock the file writing to avoid dependency issues in testing
            mock_dump.return_value = None

            # Test creating pyproject.toml
            result = runner.invoke(app, ["init", "--format-type", "conventional"])

            assert result.exit_code == 0
            assert "created" in result.stdout.lower()
            assert mock_dump.called


def test_format_type_override(runner):
    """Test overriding format type via command line."""
    # Mock the entire CLI function chain
    with patch("commit_lint.cli.load_config") as mock_load_config:
        mock_load_config.return_value = {
            "format_type": "conventional",  # Default in config
        }

        # This is where our issue is - need to mock where it's actually imported
        with patch("commit_lint.cli.get_commit_format") as mock_get_format:
            mock_format = MagicMock()
            mock_result = MagicMock()
            mock_result.valid = True
            mock_format.validate.return_value = mock_result
            mock_get_format.return_value = mock_format

            # Debug to track if the mock is called
            mock_get_format.side_effect = lambda config: print(f"Mock called with: {config}") or mock_format

            # Override with github format
            result = runner.invoke(app, ["lint", "-m", "Test message", "--format-type", "github"])

            # Check that mock was called
            assert mock_get_format.called, "get_commit_format was not called"

            # Get the config that was passed to get_commit_format
            if mock_get_format.call_args:  # Safe check
                called_config = mock_get_format.call_args[0][0]
                assert called_config["format_type"] == "github"
            else:
                # Alternative approach: just check the command ran successfully
                assert result.exit_code == 0
                print(f"Mock wasn't called with args, but command succeeded: {result.stdout}")
