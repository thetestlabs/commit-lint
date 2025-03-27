from pathlib import Path
from typer.testing import CliRunner

import pytest
import tomli

from commit_lint.cli import app


@pytest.fixture
def runner():
    return CliRunner()


def test_init_new_config(runner):
    """Test creating a new config file."""
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["init", "--output-file", "commit-lint.toml"])
        assert result.exit_code == 0
        assert "Configuration created" in result.stdout

        # Verify file was created
        config_file = Path("commit-lint.toml")
        assert config_file.exists()

        # Verify content with tomli
        with open(config_file, "rb") as f:
            config = tomli.load(f)
            assert "format_type" in config
            assert config["format_type"] == "conventional"


def test_init_with_format_type(runner):
    """Test creating a config with specific format type."""
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["init", "--format-type", "github"])
        assert result.exit_code == 0

        # Verify file was created with correct format
        config_file = Path("pyproject.toml")
        with open(config_file, "rb") as f:
            config = tomli.load(f)
            assert config["tool"]["commit_lint"]["format_type"] == "github"
            assert "imperative_mood" in config["tool"]["commit_lint"]


def test_init_invalid_format_type(runner):
    """Test error handling with invalid format type."""
    result = runner.invoke(app, ["init", "--format-type", "nonexistent"])
    assert result.exit_code != 0
    assert "Invalid format type" in result.stdout


def test_init_update_existing_config(runner):
    """Test updating an existing pyproject.toml file."""
    with runner.isolated_filesystem():
        # Create existing pyproject.toml with some content
        with open("pyproject.toml", "w") as f:
            f.write("""
[tool.poetry]
name = "commit-lint"
version = "0.1.0"
description = "Commit message linter"
            """)

        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0

        # Verify config was merged with existing file
        with open("pyproject.toml", "rb") as f:
            config = tomli.load(f)
            assert "tool" in config
            assert "poetry" in config["tool"]
            assert "commit_lint" in config["tool"]
