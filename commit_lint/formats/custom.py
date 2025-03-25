import re
from typing import Dict, List, Optional, Any
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.console import Console

from .base import CommitFormat, CommitFormatResult

console = Console()


class CustomCommitResult(CommitFormatResult):
    """Results specific to Custom format validation"""

    message: str = ""
    matches: Dict[str, str] = {}


class CustomCommitFormat(CommitFormat):
    """Implementation of custom regex-based commit format"""

    @classmethod
    def get_format_name(cls) -> str:
        return "custom"

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # Get custom pattern from config
        pattern = config.get("custom_pattern", "")
        if not pattern:
            raise ValueError("Custom commit format requires 'custom_pattern' in config")

        # Compile custom pattern
        try:
            self.pattern = re.compile(pattern, re.DOTALL)
        except re.error as e:
            raise ValueError(f"Invalid regular expression in custom_pattern: {e}")

        # Get named groups in the pattern for prompting
        self.named_groups = self._get_named_groups(pattern)

        # Get prompts for each group
        self.prompts = config.get("prompts", {})

    def _get_named_groups(self, pattern: str) -> List[str]:
        """Extract named groups from regex pattern"""
        try:
            # Create a regex to find named groups in the pattern
            group_finder = re.compile(r"\(\?P<([^>]+)>")
            return group_finder.findall(pattern)
        except:
            return []

    def validate(self, commit_message: str) -> CustomCommitResult:
        """Validate a commit message according to custom pattern"""
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
        """Interactive prompt to create a custom format commit message"""
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
