import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from typer.testing import CliRunner

from commit_lint.cli import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


def test_lint_from_file(runner):
    """Test linting from a commit message file."""
    with patch("commit_lint.config.load_config") as mock_load_config:
        mock_load_config.return_value = {"format_type": "conventional", "types": ["feat", "fix"]}

        with patch("commit_lint.formats.get_commit_format") as mock_get_format:
            mock_format = MagicMock()
            mock_result = MagicMock()
            mock_result.valid = True
            mock_format.validate.return_value = mock_result
            mock_get_format.return_value = mock_format

            # Create a temporary file with a commit message
            with runner.isolated_filesystem():
                commit_file = Path("COMMIT_EDITMSG")
                commit_file.write_text("feat: valid message from file")

                result = runner.invoke(app, ["lint", str(commit_file)])

                assert result.exit_code == 0
                assert "valid" in result.stdout.lower()