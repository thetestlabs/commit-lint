"""
Custom regex-based commit format implementation.

This module provides a flexible way to define custom commit message formats
using regular expressions. It allows projects to implement their own commit
message conventions beyond the standard formats like Conventional Commits.

Example configuration:
    custom_pattern = "^\\[(?P<category>\\w+)\\] (?P<message>.+)$"
    message_template = "[{category}] {message}"
    prompts = {
        "category": "Category (e.g. FEATURE, BUGFIX)",
        "message": "Commit message"
    }
"""

import re
from typing import Any
from typing import Dict
from typing import List

from rich.panel import Panel
from rich.prompt import Prompt
from rich.console import Console

from .base import CommitFormat
from .base import CommitFormatResult

console = Console()


class InvalidPatternError(Exception):
    """Exception raised when an invalid regex pattern is provided."""


class CustomCommitResult(CommitFormatResult):
    """
    Results specific to Custom format validation.

    This class extends the base CommitFormatResult with fields specific
    to custom regex-based validation, including the original message and
    any captured regex groups.

    Attributes:
        message: The original commit message that was validated
        matches: Dictionary of named capture groups from the regex pattern
    """

    message: str = ""
    matches: Dict[str, str] = {}


class CustomCommitFormat(CommitFormat):
    """
    Implementation of custom regex-based commit format.

    This class provides a flexible way to validate commit messages against
    a custom regex pattern defined in configuration. It also supports interactive
    prompting based on the named capture groups in the regex pattern.
    """

    @classmethod
    def get_format_name(cls) -> str:
        """
        Return the canonical name of this commit format.

        Returns:
            str: The string 'custom' which identifies this format.
        """
        return "custom"

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the custom commit format with configuration.

        Args:
            config: Dictionary containing custom format configuration including:
                  - custom_pattern: Regular expression pattern to match against
                  - message_template: Template for generating messages
                  - prompts: Dictionary of prompts for each named group

        Raises:
            InvalidPatternError: If the provided pattern is not a valid regex
        """
        super().__init__()

        pattern = config.get("custom_pattern", "")
        if not pattern:
            raise InvalidPatternError("No custom_pattern provided in configuration")

        try:
            self.pattern = re.compile(pattern, re.DOTALL)
        except re.error as e:
            raise InvalidPatternError(f"Invalid regular expression in custom_pattern: {e}") from e

        # Get named groups in the pattern for prompting
        self.named_groups = self._get_named_groups(pattern)

        # Get prompts for each group
        self.prompts = config.get("prompts", {})

    def _get_named_groups(self, pattern: str) -> List[str]:
        """
        Extract named capture groups from a regex pattern.

        This helper method parses the regex pattern to find all named capture
        groups (in the format ?P<name>) for use in interactive prompting.

        Args:
            pattern: Regular expression pattern to parse

        Returns:
            List[str]: List of named capture group identifiers found in the pattern
        """
        try:
            # Create a regex to find named groups in the pattern
            group_finder = re.compile(r"\(\?P<([^>]+)>")
            return group_finder.findall(pattern)
        except re.error:
            return []

    def validate(self, commit_message: str) -> CustomCommitResult:
        """
        Validate a commit message against the custom pattern.

        Examples:
            >>> format = CustomCommitFormat({"custom_pattern": r"^\[(?P<category>\w+)\] (?P<message>.+)$"})
            >>> result = format.validate("[FEATURE] Add new capability")
            >>> result.valid
            True
            >>> result.category
            'FEATURE'
        """
        # Match against pattern
        match = self.pattern.match(commit_message)
        if not match:
            return CustomCommitResult(
                valid=False,
                errors=["Commit message does not match the custom pattern"],
                message=commit_message,
                matches={},
            )

        # Extract matches as a dictionary
        matches = match.groupdict()

        # Additional validation rules can be added here based on config

        return CustomCommitResult(valid=True, errors=[], message=commit_message, matches=matches)

    def prompt_for_message(self, config: Dict[str, Any]) -> str:
        """
        Interactive prompt to create a custom format commit message.

        This method guides the user through creating a commit message according to
        the custom format defined in configuration. It uses the 'prompts' configuration
        to dynamically ask for each named capture group in the custom pattern.

        The method will then format the message according to the provided message template,
        substituting the user's input for each named component.

        Args:
            config: Configuration dictionary containing:
                   - custom_pattern: Regex pattern with named capture groups
                   - message_template: String template for formatting the message
                   - prompts: Dict mapping capture groups to prompt text

        Returns:
            str: A commit message formatted according to the custom template.

        Raises:
            ValueError: If the custom pattern, template, or prompts are not properly configured.
        """
        console.print(Panel("Create a custom format commit message", title="Commit Message"))

        # Collect values for each named group in the pattern
        values = {}
        for group in self.named_groups:
            prompt_text = self.prompts.get(group, f"Enter {group}")
            values[group] = Prompt.ask(prompt_text)

        # Use template if provided, otherwise try to reconstruct from pattern
        template = config.get("message_template", "")
        if template:
            # Replace {group_name} placeholders with values
            message = template
            for group, value in values.items():
                message = message.replace(f"{{{group}}}", value)
        else:
            # This is a simplistic approach - might not work for complex patterns
            # Better to use explicit template in config
            console.print("[yellow]Warning: No message_template provided, attempting to construct message[/yellow]")
            message = ""
            for group, value in values.items():
                if message:
                    message += " "
                message += value

        return message
