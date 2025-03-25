import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

# Import callbacks directly from the CLI module
from commit_lint.cli import version_callback, show_rules_callback, app


def test_version_callback():
    """Test version callback displays version and exits."""
    with patch("commit_lint.cli.__version__", "1.0.0"):
        with patch("typer.Exit") as mock_exit:
            # Mock console to capture output
            with patch("commit_lint.cli.console") as mock_console:
                # Call the callback function directly
                mock_exit.side_effect = SystemExit(0)  # Prevent actual exit

                with pytest.raises(SystemExit):
                    version_callback(True)

                # Check that version was printed
                mock_console.print.assert_called_once()


def test_show_rules_callback():
    """Test show_rules callback displays rules and exits."""
    with patch("typer.Exit") as mock_exit:
        # Mock console to capture output
        with patch("commit_lint.cli.console") as mock_console:
            mock_exit.side_effect = SystemExit(0)  # Prevent actual exit

            with pytest.raises(SystemExit):
                show_rules_callback(True)

            # Check that rules were printed (multiple calls to console.print)
            assert mock_console.print.call_count > 1


def test_cli_help(runner):
    """Test that the CLI help output works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    # Check for something that should definitely be in the help text
    assert "version" in result.stdout.lower()
    assert "show-rules" in result.stdout.lower()
    assert "create" in result.stdout.lower()
    assert "lint" in result.stdout.lower()
    assert "commit" in result.stdout.lower()
    assert "install" in result.stdout.lower()
    assert "init" in result.stdout.lower()
    # The app name might be different in test mode vs. real mode
    # so we don't check for "commit-lint" specifically


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()
