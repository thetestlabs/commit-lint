"""
Configuration management for commit-lint.

This module handles loading and parsing configuration from various sources,
with support for both pyproject.toml and standalone commit-lint.toml files.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List

import tomli
from pydantic import Field, BaseModel


class CommitConfig(BaseModel):
    """
    Configuration model for commit message format.

    This Pydantic model defines the schema for commit-lint configuration,
    with type validation and default values.
    """

    types: List[str] = Field(..., description="Valid commit types")
    max_subject_length: int = Field(100, description="Maximum subject line length")
    subject_case: str = Field("lower", description="Case style for subject line")
    scope_required: bool = Field(False, description="Whether scope is required")
    allowed_scopes: Optional[List[str]] = Field(
        None, description="List of allowed scopes (if None, any scope is allowed)"
    )
    body_required: bool = Field(False, description="Whether body is required")
    footer_required: bool = Field(False, description="Whether footer is required")
    allowed_breaking_changes: List[str] = Field(["feat", "fix"], description="Types allowed for breaking changes")
    no_period_end: bool = Field(True, description="Whether subject line can end with period")
    custom_pattern: Optional[str] = Field(None, description="Optional regex pattern for custom validation")


def get_default_config_path() -> Path:
    """
    Get the default configuration file path.

    This function determines where to look for configuration files by default.
    It first checks for pyproject.toml, then commit-lint.toml in the current
    working directory.

    Returns:
        Path: The path to the default configuration file, even if it doesn't exist yet.
             Preference is given to pyproject.toml if it exists.
    """
    # Look for pyproject.toml first, then commit-lint.toml
    current_dir = Path.cwd()

    # Check for pyproject.toml in current directory
    pyproject_path = current_dir / "pyproject.toml"
    if pyproject_path.exists():
        return pyproject_path

    # Look for standalone commit-lint.toml
    commit_lint_path = current_dir / "commit-lint.toml"
    if commit_lint_path.exists():
        return commit_lint_path

    # Default to pyproject.toml even if it doesn't exist
    return pyproject_path


def get_config_paths() -> List[Path]:
    """
    Get all possible configuration file paths in priority order.

    This function returns a list of all potential configuration file paths,
    searching the current directory and all parent directories. Paths are
    ordered by priority, with pyproject.toml taking precedence in each directory.

    Returns:
        List[Path]: Ordered list of possible configuration file paths.
    """
    current_dir = Path.cwd()
    paths = []

    # Check for config files in current and parent directories
    dir_path = current_dir
    while dir_path != dir_path.parent:
        # First check pyproject.toml
        pyproject_path = dir_path / "pyproject.toml"
        paths.append(pyproject_path)

        # Then check standalone commit-lint.toml
        commit_lint_path = dir_path / "commit-lint.toml"
        paths.append(commit_lint_path)

        dir_path = dir_path.parent

    return paths


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from file or search for it.

    Args:
        config_path: Optional explicit path to a configuration file.
                   If None, configuration will be searched for automatically.

    Returns:
        Dict[str, Any]: The loaded configuration dictionary.
                      If no configuration is found, default values are returned.

    Raises:
        FileNotFoundError: If a specific config_path is provided but the file doesn't exist.
        ValueError: If there is an error parsing the configuration file.
    """
    # If specific path provided, only try that file
    if config_path:
        return _load_from_specific_path(config_path)
    else:
        # Search for config files in priority order
        return _search_and_load_config()


def _load_from_specific_path(config_path: Path) -> Dict[str, Any]:
    """Load configuration from a specific file path."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    return _parse_config_file(config_path)


def _search_and_load_config() -> Dict[str, Any]:
    """Search for and load configuration from standard locations."""
    # Search for config files in priority order
    for path in get_config_paths():
        if path.exists():
            try:
                config_data = _parse_config_file(path)
                if config_data:  # Only use if we got valid config data
                    return config_data
            except Exception:
                # Continue to next file on parsing error
                continue

    # If no config found, use defaults
    return get_default_config()


def _parse_config_file(file_path: Path) -> Dict[str, Any]:
    """
    Parse a configuration file.

    Args:
        file_path: Path to the configuration file

    Returns:
        Dict[str, Any]: Configuration data

    Raises:
        ValueError: If there is an error parsing the file
    """
    try:
        with open(file_path, "rb") as f:
            if file_path.name == "pyproject.toml":
                return _extract_from_pyproject(f)
            else:
                # Standalone TOML file - load directly
                return tomli.load(f)
    except Exception as e:
        raise ValueError(f"Error parsing {file_path}: {str(e)}")


def _extract_from_pyproject(file_obj) -> Dict[str, Any]:
    """
    Extract commit_lint configuration from a pyproject.toml file.

    Args:
        file_obj: Open file object for pyproject.toml

    Returns:
        Dict[str, Any]: Configuration data from [tool.commit_lint] section
    """
    pyproject = tomli.load(file_obj)
    return pyproject.get("tool", {}).get("commit_lint", {})


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration settings.

    This function returns the default configuration used when no configuration
    file is found. It provides sensible defaults for Conventional Commits format.

    Returns:
        Dict[str, Any]: Default configuration dictionary with conventional commit settings.
    """
    return {
        "format_type": "conventional",
        "types": ["feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"],
        "max_subject_length": 100,
        "subject_case": "lower",
        "scope_required": False,
        "allowed_breaking_changes": ["feat", "fix"],
        "no_period_end": True,
    }
