"""
Jira-style commit format implementation.

This module implements validation and generation of Jira-style commit messages,
which typically reference Jira issue IDs in the format "PROJ-123: Message".
It supports configurable project keys and message formatting rules.
"""

import re
from typing import Dict, Optional, Any
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.console import Console

from .base import CommitFormat, CommitFormatResult

console = Console()


class JiraCommitResult(CommitFormatResult):
    """
    Results specific to Jira style commit validation.

    This class extends the base CommitFormatResult with fields specific
    to the Jira commit format, including the issue ID and message components.

    Attributes:
        issue_id: The Jira issue identifier (e.g., "PROJ-123")
        message: The commit message content after the issue ID
        body: Optional detailed description following the summary
    """

    issue_id: Optional[str] = None
    message: Optional[str] = None
    body: Optional[str] = None


class JiraCommitFormat(CommitFormat):
    """
    Implementation of Jira style commit format.

    This class validates and generates commit messages that follow the Jira
    style, typically with a reference to a Jira issue ID at the beginning
    of the message.
    """

    @classmethod
    def get_format_name(cls) -> str:
        """
        Return the canonical name of this commit format.

        Returns:
            str: The string 'jira' which identifies this format.
        """
        return "jira"

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Jira format validator with configuration settings.

        Args:
            config: Configuration dictionary with settings such as jira_project_keys,
                  require_issue_id, and max_message_length.
        """
        self.config = config

        # Get Jira project keys from config
        self.jira_project_keys = config.get("jira_project_keys", [])

        # Create regex pattern for Jira-style commits
        # Format: PROJ-123: Message
        project_keys_pattern = "|".join(self.jira_project_keys) if self.jira_project_keys else r"\w+"

        self.commit_pattern = re.compile(
            rf"^(?P<issue_id>(?:{project_keys_pattern})-\d+):\s+(?P<message>.+?)(?:\n\n(?P<body>[\s\S]*))?$", re.DOTALL
        )

    def validate(self, commit_message: str) -> JiraCommitResult:
        """
        Validate a commit message according to Jira format standards.
        """
        errors = []
        issue_id = None
        message_text = commit_message
        body = None

        # Check if there's a body (separated by blank line)
        parts = commit_message.split("\n\n", 1)

        # Extract just the first line for subject validation
        first_line = parts[0].strip()

        # If there's a body, set it
        if len(parts) > 1:
            body = parts[1].strip()

        # Check if issue ID is required and properly formatted
        require_issue_id = self.config.get("require_issue_id", True)
        project_keys = self.config.get("jira_project_keys", [])

        # Debug the input to see what we're dealing with
        # print(f"DEBUG - first_line: '{first_line}'")

        # Modified regex to be more tolerant of whitespace
        issue_id_match = re.match(r"^\s*([A-Z][A-Z0-9_]+-\d+)\s*:\s*(.*?)\s*$", first_line)

        if issue_id_match:
            issue_id = issue_id_match.group(1)
            message_text = issue_id_match.group(2).strip()  # Extract just the message part

            # Validate project key if specific keys are configured
            if project_keys and issue_id.split("-")[0] not in project_keys:
                errors.append(
                    f"Commit message must start with a Jira issue ID from one of the allowed projects: {', '.join(project_keys)}"
                )
        elif require_issue_id:
            errors.append("Commit message must start with a Jira issue ID (e.g., PROJECT-123: message)")
        else:
            # No issue ID but it's optional, so message_text is the whole first line
            message_text = first_line

        # Validate message length (only checking the message part, not the issue ID)
        max_length = self.config.get("max_message_length", 72)
        if len(message_text) > max_length:
            errors.append(f"Commit message is too long ({len(message_text)} > {max_length} characters)")

        # Return result object with all components
        return JiraCommitResult(
            valid=len(errors) == 0,
            errors=errors,
            issue_id=issue_id,
            message=message_text,  # This should now be just the subject line
            body=body,
        )

    def prompt_for_message(self, config: Dict[str, Any]) -> str:
        """
        Interactive prompt to create a Jira-style commit message.

        This method guides the user through creating a commit message that references
        a Jira issue ID in the format "PROJ-123: Message". It prompts for the
        Jira project key, issue number, and commit message details.

        The method will validate that the project key is among the configured
        allowed project keys if they are specified in the configuration.

        Args:
            config: Configuration dictionary with Jira format settings such as
                   project keys and message length limits.

        Returns:
            str: A properly formatted Jira-style commit message.
        """
        console.print(Panel("Create a Jira-style commit message", title="Commit Message"))

        # Rest of the implementation...

        # Get Jira issue ID
        require_issue_id = config.get("require_issue_id", True)
        jira_project_keys = config.get("jira_project_keys", [])

        issue_id = ""
        if require_issue_id or Confirm.ask("Include Jira issue ID?", default=True):
            if jira_project_keys:
                project_key = Prompt.ask("Jira project key", choices=jira_project_keys, default=jira_project_keys[0])
            else:
                project_key = Prompt.ask("Jira project key")

            issue_number = Prompt.ask("Issue number")
            issue_id = f"{project_key}-{issue_number}"

        # Get commit message
        message = Prompt.ask("Commit message")

        # Get optional body
        body = ""
        if Confirm.ask("Add detailed description?", default=False):
            console.print("Enter detailed description (empty line to finish):")
            body_lines = []
            while True:
                line = input()
                if not line:
                    break
                body_lines.append(line)
            if body_lines:
                body = "\n".join(body_lines)

        # Assemble message
        if issue_id:
            formatted_message = f"{issue_id}: {message}"
        else:
            formatted_message = message

        if body:
            formatted_message += f"\n\n{body}"

        return formatted_message
