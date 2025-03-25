"""Format validators for different commit message styles."""

from typing import Dict, Any
from .base import CommitFormat
from .conventional import ConventionalCommitFormat
from .github import GitHubCommitFormat
from .jira import JiraCommitFormat
from .custom import CustomCommitFormat

# Define public API
__all__ = ["get_commit_format", "CommitFormat", "FORMAT_REGISTRY"]

# Register all format implementations
FORMAT_REGISTRY = {
    format_class.get_format_name(): format_class
    for format_class in [ConventionalCommitFormat, GitHubCommitFormat, JiraCommitFormat, CustomCommitFormat]
}


def get_commit_format(config: Dict[str, Any]) -> CommitFormat:
    """
    Create appropriate format validator based on configuration.

    Args:
        config: Configuration dictionary containing format_type and format-specific settings

    Returns:
        CommitFormat: An instance of the appropriate format validator

    Raises:
        ValueError: If the requested format_type is not in the registry
    """
    format_type = config.get("format_type", "conventional")

    if format_type not in FORMAT_REGISTRY:
        valid_formats = ", ".join(FORMAT_REGISTRY.keys())
        raise ValueError(f"Unknown commit format type: {format_type}. Valid types: {valid_formats}")

    format_class = FORMAT_REGISTRY[format_type]
    return format_class(config)


# Convenience functions to get specific formats directly
def get_conventional_format(config: Dict[str, Any]) -> ConventionalCommitFormat:
    """Get a conventional commit format validator."""
    return ConventionalCommitFormat(config)


def get_github_format(config: Dict[str, Any]) -> GitHubCommitFormat:
    """Get a GitHub style commit format validator."""
    return GitHubCommitFormat(config)

def get_jira_format(config: Dict[str, Any]) -> JiraCommitFormat:
    """Get a Jira style commit format validator."""
    return JiraCommitFormat(config)