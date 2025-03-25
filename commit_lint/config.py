import yaml
import tomli  # Import at the top level since we'll always need it now
from pathlib import Path
from typing import Dict, Any, Optional, List

from pydantic import Field, BaseModel


class CommitConfig(BaseModel):
    """Configuration model for commit message format."""

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
    """Get the default configuration file path."""
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
    """Get all possible configuration file paths in priority order."""
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
    """Load configuration from file or search for it."""
    config_data = {}

    # If specific path provided, only try that file
    if config_path:
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with open(config_path, "rb") as f:
                if config_path.name == "pyproject.toml":
                    # Extract from [tool.commit_lint] section
                    pyproject = tomli.load(f)
                    config_data = pyproject.get("tool", {}).get("commit_lint", {})
                else:
                    # Standalone TOML file - load directly
                    config_data = tomli.load(f)
        except Exception as e:
            raise ValueError(f"Error parsing {config_path}: {str(e)}")
    else:
        # Search for config files in priority order
        for path in get_config_paths():
            if path.exists():
                try:
                    with open(path, "rb") as f:
                        if path.name == "pyproject.toml":
                            # Extract from [tool.commit_lint] section
                            pyproject = tomli.load(f)
                            config_data = pyproject.get("tool", {}).get("commit_lint", {})
                            if config_data:  # Only use if section exists
                                break
                        else:
                            # Standalone TOML file - load directly
                            config_data = tomli.load(f)
                            break
                except Exception:
                    # Continue to next file on parsing error
                    continue

    # If no config found, use defaults
    if not config_data:
        config_data = get_default_config()

    return config_data


def get_default_config() -> Dict[str, Any]:
    """Get default configuration"""
    return {
        "format_type": "conventional",
        "types": ["feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"],
        "max_subject_length": 100,
        "subject_case": "lower",
        "scope_required": False,
        "allowed_breaking_changes": ["feat", "fix"],
        "no_period_end": True,
    }
