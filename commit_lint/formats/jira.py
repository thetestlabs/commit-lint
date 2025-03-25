import re
from typing import Dict, List, Optional, Any
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.console import Console

from .base import CommitFormat, CommitFormatResult

console = Console()


class JiraCommitResult(CommitFormatResult):
    """Results specific to Jira style commit validation"""

    issue_id: Optional[str] = None
    message: Optional[str] = None
    body: Optional[str] = None


class JiraCommitFormat(CommitFormat):
    """Implementation of Jira style commit format"""

    @classmethod
    def get_format_name(cls) -> str:
        return "jira"

    def __init__(self, config: Dict[str, Any]):
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
        """Validate a commit message according to Jira style"""
        errors = []

        # Match against pattern
        match = self.commit_pattern.match(commit_message)
        if not match:
            if self.config.get("require_issue_id", True):
                return JiraCommitResult(
                    valid=False, errors=["Commit message must start with a Jira issue ID (e.g., 'PROJ-123: Message')"]
                )
            else:
                # If issue ID not required, try to match just the message
                simple_match = re.match(r"^(?P<message>.+?)(?:\n\n(?P<body>[\s\S]*))?$", commit_message, re.DOTALL)
                if simple_match:
                    return JiraCommitResult(
                        valid=True,
                        errors=[],
                        issue_id=None,
                        message=simple_match.group("message"),
                        body=simple_match.group("body"),
                    )
                else:
                    return JiraCommitResult(valid=False, errors=["Invalid commit message format"])

        # Extract components
        issue_id = match.group("issue_id")
        message = match.group("message")
        body = match.group("body")

        # Check if project key is valid (if project keys are specified)
        if self.jira_project_keys:
            project_key = issue_id.split("-")[0]
            if project_key not in self.jira_project_keys:
                errors.append(
                    f"Invalid Jira project key: {project_key}. Must be one of: {', '.join(self.jira_project_keys)}"
                )

        # Validate message length
        max_message_length = self.config.get("max_message_length", 72)
        if len(message) > max_message_length:
            errors.append(f"Message too long ({len(message)} > {max_message_length})")

        return JiraCommitResult(valid=len(errors) == 0, errors=errors, issue_id=issue_id, message=message, body=body)

    def prompt_for_message(self, config: Dict[str, Any]) -> str:
        """Interactive prompt to create a Jira style commit message"""
        console.print(Panel("Create a Jira style commit message", title="Commit Message"))

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
