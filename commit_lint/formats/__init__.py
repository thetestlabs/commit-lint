"""
Format validators for different commit message styles.

This module provides a plugin-based system for validating and generating
commit messages in various formats including Conventional Commits,
GitHub style, Jira style, and custom regex-based formats.
"""

from typing import Any
from typing import Dict

from .base import CommitFormat
from .jira import JiraCommitFormat
from .custom import CustomCommitFormat
from .github import GitHubCommitFormat
from .conventional import ConventionalCommitFormat

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

    This factory function examines the provided configuration to determine
    which commit format class to instantiate. It uses the 'format_type' key
    in the config dictionary to look up the appropriate implementation in
    the FORMAT_REGISTRY.

    Args:
        config: Configuration dictionary containing format_type and format-specific settings.
               The format_type key determines which validator to create.

    Returns:
        CommitFormat: An instance of the appropriate format validator configured with
                     the provided settings.

    Raises:
        ValueError: If the requested format_type is not in the registry or is invalid.

    Examples:
        >>> config = {"format_type": "conventional", "types": ["feat", "fix"]}
        >>> validator = get_commit_format(config)
        >>> isinstance(validator, ConventionalCommitFormat)
        True
    """
    format_type = config.get("format_type", "conventional")

    if format_type not in FORMAT_REGISTRY:
        valid_formats = ", ".join(FORMAT_REGISTRY.keys())
        raise ValueError(f"Unknown commit format type: {format_type}. Valid types: {valid_formats}")

    format_class = FORMAT_REGISTRY[format_type]
    return format_class(config)


# Convenience functions to get specific formats directly
def get_conventional_format(config: Dict[str, Any]) -> ConventionalCommitFormat:
    """
    Get a conventional commit format validator.

    This is a convenience function for directly creating a Conventional Commits
    validator without going through the format registry.

    Args:
        config: Configuration dictionary with Conventional Commits specific settings.

    Returns:
        ConventionalCommitFormat: A validator for Conventional Commits format.
    """
    return ConventionalCommitFormat(config)


def get_github_format(config: Dict[str, Any]) -> GitHubCommitFormat:
    """
    Get a GitHub style commit format validator.

    This is a convenience function for directly creating a GitHub style
    validator without going through the format registry.

    Args:
        config: Configuration dictionary with GitHub format specific settings.

    Returns:
        GitHubCommitFormat: A validator for GitHub style commit messages.
    """
    return GitHubCommitFormat(config)


def get_jira_format(config: Dict[str, Any]) -> JiraCommitFormat:
    """
    Get a Jira style commit format validator.

    This is a convenience function for directly creating a Jira style
    validator without going through the format registry.

    Args:
        config: Configuration dictionary with Jira format specific settings.

    Returns:
        JiraCommitFormat: A validator for Jira style commit messages.
    """
    return JiraCommitFormat(config)
