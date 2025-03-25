import re
from typing import Dict, Optional, Any
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.console import Console

from .base import CommitFormat, CommitFormatResult

console = Console()


class GitHubCommitResult(CommitFormatResult):
    """Results specific to GitHub style commit validation"""

    message: Optional[str] = None
    issue_reference: Optional[str] = None
    issue_keyword: Optional[str] = None


class GitHubCommitFormat(CommitFormat):
    """Implementation of GitHub style commit format"""

    @classmethod
    def get_format_name(cls) -> str:
        return "github"

    def __init__(self, config: Dict[str, Any]):
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
        """Validate a commit message according to GitHub style"""
        errors = []

        # Match against pattern
        match = self.commit_pattern.match(commit_message)
        if not match:
            return GitHubCommitResult(valid=False, errors=["Invalid commit message format"])

        # Extract components
        subject = match.group("subject")
        body = match.group("body")

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
            errors.append(f"Missing issue reference (e.g., '{self.issue_keywords[0]} #123')")

        return GitHubCommitResult(
            valid=len(errors) == 0,
            errors=errors,
            message=subject,
            issue_reference=issue_reference,
            issue_keyword=issue_keyword,
        )

    def prompt_for_message(self, config: Dict[str, Any]) -> str:
        """Interactive prompt to create a GitHub style commit message"""
        console.print(Panel("Create a GitHub style commit message", title="Commit Message"))

        # Brief, imperative subject line
        console.print("Enter a brief, imperative subject line (what the commit does, not what you did)")
        subject = Prompt.ask("Subject")

        # Body - optional detailed description
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

        # Issue reference if configured/requested
        issue_reference = ""
        issue_keywords = config.get("keywords", ["Fixes", "Closes", "Resolves"])
        issue_required = config.get("issue_reference_required", False)

        if issue_required or Confirm.ask("Add issue reference?", default=False):
            keyword = Prompt.ask("Reference keyword", choices=issue_keywords, default=issue_keywords[0])
            issue_number = Prompt.ask("Issue number")
            issue_reference = f"{keyword} #{issue_number}"

            # Add to subject or body based on length
            if not body:
                subject = f"{subject} ({issue_reference})"
            else:
                body += f"\n\n{issue_reference}"

        # Assemble message
        if body:
            message = f"{subject}\n\n{body}"
        else:
            message = subject

        return message
