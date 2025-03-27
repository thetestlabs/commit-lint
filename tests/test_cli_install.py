import pytest
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from commit_lint.cli import app


@pytest.fixture
def runner():
    return CliRunner()


def test_install_hooks_success(runner):
    """Test successful installation of git hooks."""
    with runner.isolated_filesystem():
        # Create mock .git directory
        git_dir = Path(".git")
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        result = runner.invoke(app, ["install"])

        assert result.exit_code == 0
        assert "hooks installed successfully" in result.stdout.lower()

        # Verify files were created
        pre_commit_hook = hooks_dir / "pre-commit"
        commit_msg_hook = hooks_dir / "commit-msg"

        assert pre_commit_hook.exists()
        assert commit_msg_hook.exists()

        # Check file permissions
        assert pre_commit_hook.stat().st_mode & 0o111  # Check executable bit
        assert commit_msg_hook.stat().st_mode & 0o111  # Check executable bit


def test_install_hooks_no_git(runner):
    """Test install hooks command when not in a git repository."""
    with runner.isolated_filesystem():
        # No .git directory
        result = runner.invoke(app, ["install"])

        assert result.exit_code != 0
        assert "not a git repository" in result.stdout.lower()


def test_install_with_pre_commit_framework(runner):
    """Test installation when pre-commit framework is detected."""
    with runner.isolated_filesystem():
        # Create mock .git directory
        git_dir = Path(".git")
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        # Create existing pre-commit hook
        pre_commit_path = hooks_dir / "pre-commit"
        with open(pre_commit_path, "w") as f:
            f.write("#!/bin/sh\n# pre-commit framework hook\nexit 0")

        with patch("commit_lint.cli.subprocess.run") as mock_run:
            # Mock pre-commit check
            mock_version = MagicMock()
            mock_version.returncode = 0

            # Mock pre-commit install
            mock_install = MagicMock()
            mock_install.returncode = 0

            mock_run.side_effect = [mock_version, mock_install]

            result = runner.invoke(app, ["install"])

            assert result.exit_code == 0
            assert "pre-commit framework detected" in result.stdout.lower()
            assert "hooks installed successfully" in result.stdout.lower()

            # Verify backup file was created
            backup_path = hooks_dir / ".pre-commit-hook"
            assert backup_path.exists()
