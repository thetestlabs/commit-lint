"""
GitHub-style commit format implementation.

This module implements validation and generation of GitHub-style commit messages,
which typically have a concise subject line and optional detailed body,
potentially with references to GitHub issues (e.g., "Fixes #123").
"""

import re
from typing import Dict, Optional, Any, Tuple
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.console import Console

from .base import CommitFormat, CommitFormatResult

console = Console()


class GitHubCommitResult(CommitFormatResult):
    """
    Results specific to GitHub style commit validation.

    This class extends the base CommitFormatResult with fields specific
    to the GitHub commit format, including issue references.

    Attributes:
        message: The commit message content (subject line)
        issue_reference: Referenced issue number, if any
        issue_keyword: Keyword used to reference the issue (e.g., "Fixes")
    """

    message: Optional[str] = None
    issue_reference: Optional[str] = None
    issue_keyword: Optional[str] = None


class GitHubCommitFormat(CommitFormat):
    """
    Implementation of GitHub style commit format.

    This class validates and generates commit messages that follow the GitHub
    style, with a concise subject line, optional body, and potential issue
    references using keywords like "Fixes #123".
    """

    @classmethod
    def get_format_name(cls) -> str:
        """
        Return the canonical name of this commit format.

        Returns:
            str: The string 'github' which identifies this format.
        """
        return "github"

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the GitHub format validator with configuration settings.

        Args:
            config: Configuration dictionary with settings such as max_subject_length,
                  imperative_mood, issue_reference_required, and keywords.
        """
        self.config = config

        # GitHub issue reference pattern (e.g., "Fixes #123")
        self.issue_keywords = config.get("keywords", ["Fixes", "Closes", "Resolves"])
        keyword_pattern = "|".join(self.issue_keywords)

        self.issue_pattern = re.compile(rf"(?:^|\s)(?P<keyword>{keyword_pattern}):?\s+#(?P<issue>\d+)", re.IGNORECASE)

        # Format for GitHub commit messages
        # Simple, concise first line <= 72 chars
        # Optional blank line followed by more detailed description
        self.commit_pattern = re.compile(r"^(?P<subject>.+?)(?:\n\n(?P<body>[\s\S]*))?$", re.DOTALL)

    def validate(self, commit_message: str) -> GitHubCommitResult:
        """
        Validate a commit message according to GitHub style.

        This method checks if the message follows GitHub best practices:
        - Concise subject line under the configured maximum length
        - Use of imperative mood (if configured)
        - Proper issue references (if required)

        Args:
            commit_message: The commit message string to validate.

        Returns:
            GitHubCommitResult: A result object containing validation status,
                              any errors, and parsed components of the message.
        """
        errors = []

        # Match against pattern
        match = self.commit_pattern.match(commit_message)
        if not match:
            return GitHubCommitResult(valid=False, errors=["Invalid commit message format"])

        # Extract components
        subject = match.group("subject")
        # body = match.group("body")  # Currently unused, commented out

        # Validate subject length (GitHub standard is 50 chars, flexible up to 72)
        max_subject_length = self.config.get("max_subject_length", 72)
        if len(subject) > max_subject_length:
            errors.append(f"Subject line too long ({len(subject)} > {max_subject_length})")

        # Check for imperative mood if configured
        imperative_mood = self.config.get("imperative_mood", True)
        if imperative_mood:
            # This is a very simple check for imperative mood (could be improved)
            non_imperative_starters = ["added", "fixes", "fixed", "adding", "updated", "changed"]
            subject_start = subject.split()[0].lower() if subject.split() else ""
            if subject_start in non_imperative_starters:
                errors.append("Use imperative mood in subject line (e.g., 'Add' not 'Added')")

        # Check for issue reference if required
        issue_required = self.config.get("issue_reference_required", False)
        issue_match = self.issue_pattern.search(commit_message)

        issue_reference = None
        issue_keyword = None

        if issue_match:
            issue_keyword = issue_match.group("keyword")
            issue_reference = issue_match.group("issue")
        elif issue_required:
            keyword_list = ", ".join(self.issue_keywords)
            errors.append(
                f"Missing issue reference (e.g., '{self.issue_keywords[0]} #123'). Use one of: {keyword_list}"
            )

        return GitHubCommitResult(
            valid=len(errors) == 0,
            errors=errors,
            message=subject,
            issue_reference=issue_reference,
            issue_keyword=issue_keyword,
        )

    def prompt_for_message(self, config: Dict[str, Any]) -> str:
        """
        Interactive prompt to create a GitHub style commit message.
        """
        console.print(Panel("Create a GitHub style commit message", title="Commit Message"))

        # Get message components using helper methods
        subject = self._prompt_for_subject()
        body = self._prompt_for_body()
        issue_reference, keyword = self._prompt_for_issue_reference(config)

        # Assemble the final message
        return self._assemble_message(subject, body, issue_reference)

    def _prompt_for_subject(self) -> str:
        """Get the commit subject line from user."""
        console.print("Enter a brief, imperative subject line (what the commit does, not what you did)")
        return Prompt.ask("Subject")

    def _prompt_for_body(self) -> str:
        """Get optional detailed commit description."""
        body = ""
        if Confirm.ask("Add detailed description?", default=False):
            console.print("Enter detailed description (empty line to finish):")
            body_lines = []
            while True:
                line = input()
                if not line and not body_lines:
                    continue  # Don't allow empty body
                if not line:
                    break
                body_lines.append(line)
            if body_lines:
                body = "\n".join(body_lines)
        return body

    def _prompt_for_issue_reference(self, config: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """Get optional or required issue reference."""
        issue_reference = ""
        keyword = None

        issue_keywords = config.get("keywords", ["Fixes", "Closes", "Resolves"])
        issue_required = config.get("issue_reference_required", False)

        if issue_required or Confirm.ask("Add issue reference?", default=False):
            keyword = Prompt.ask("Reference keyword", choices=issue_keywords, default=issue_keywords[0])
            issue_number = Prompt.ask("Issue number")
            issue_reference = f"{keyword} #{issue_number}"

        return issue_reference, keyword

    def _assemble_message(self, subject: str, body: str, issue_reference: str) -> str:
        """Assemble final commit message from components."""
        # If there's an issue reference but no body, add to subject line
        if issue_reference and not body:
            subject = f"{subject} ({issue_reference})"

        # Construct the message with or without body
        if body:
            message = f"{subject}\n\n{body}"
            # If there's an issue reference and a body, add to body
            if issue_reference and not subject.endswith(f"({issue_reference})"):
                message += f"\n\n{issue_reference}"
        else:
            message = subject

        return message
