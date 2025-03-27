from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from commit_lint.cli import app


@pytest.fixture
def runner():
    return CliRunner()


def test_version_display(runner):
    """Test that version information is displayed correctly."""
    with patch("commit_lint.cli.__version__", "1.0.0-test"):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0-test" in result.stdout


def test_show_rules(runner):
    """Test the show-rules option displays format information."""
    result = runner.invoke(app, ["--show-rules"])
    assert result.exit_code == 0
    assert "Conventional Commits Format" in result.stdout
    assert "GitHub Style Format" in result.stdout
    assert "Jira Style Format" in result.stdout
    assert "Custom Format" in result.stdout


def test_help_display(runner):
    """Test that help information is displayed correctly."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "A configurable linter for better commit messages" in result.stdout

    # Check that all commands are listed
    assert "create" in result.stdout.lower()
    assert "lint" in result.stdout.lower()
    assert "commit" in result.stdout.lower()
    assert "install" in result.stdout.lower()
    assert "init" in result.stdout.lower()
