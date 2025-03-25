import re
from typing import Dict, List, Optional, Any
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.console import Console
import questionary

from .base import CommitFormat, CommitFormatResult

# Dictionary of commit type descriptions
COMMIT_TYPE_DESCRIPTIONS = {
    "feat": "A new feature",
    "fix": "A bug fix",
    "docs": "Documentation only changes",
    "style": "Changes that do not affect the meaning of the code",
    "refactor": "A code change that neither fixes a bug nor adds a feature",
    "perf": "A code change that improves performance",
    "test": "Adding missing tests or correcting existing tests",
    "build": "Changes that affect the build system or external dependencies",
    "ci": "Changes to CI configuration files and scripts",
    "chore": "Other changes that don't modify src or test files",
    "revert": "Reverts a previous commit",
}

console = Console()


class ConventionalCommitResult(CommitFormatResult):
    """Results specific to Conventional Commits validation"""

    type: Optional[str] = None
    scope: Optional[str] = None
    breaking: bool = False
    description: Optional[str] = None
    body: Optional[str] = None
    footer: Optional[str] = None


class ConventionalCommitFormat(CommitFormat):
    """Implementation of Conventional Commits format"""

    @classmethod
    def get_format_name(cls) -> str:
        return "conventional"

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # Create regex pattern for conventional commits - fixed to properly separate description
        self.commit_pattern = re.compile(
            r"^(?P<type>\w+)"
            r"(?:\((?P<scope>[\w-]+)\))?"
            r"(?P<breaking>!)?"
            r": (?P<description>[^\n]+)"  # Changed from .+ to [^\n]+ to stop at first newline
            r"(?:\n\n(?P<body>[\s\S]*?))?"  # Made non-greedy with *?
            r"(?:\n\n(?P<footer>[\s\S]*))?$",
            re.DOTALL,
        )

    def validate(self, commit_message: str) -> ConventionalCommitResult:
        """Validate a commit message according to Conventional Commits format"""
        errors = []

        # Match against pattern
        match = self.commit_pattern.match(commit_message)
        if not match:
            return ConventionalCommitResult(
                valid=False, errors=["Commit message does not follow Conventional Commits format"]
            )

        # Extract components
        type_name = match.group("type")
        scope = match.group("scope")
        breaking = bool(match.group("breaking"))
        description = match.group("description")
        body = match.group("body")
        footer = match.group("footer")

        # Validate type
        valid_types = self.config.get("types", [])
        if valid_types and type_name not in valid_types:
            errors.append(f"Invalid type: {type_name}. Must be one of: {', '.join(valid_types)}")

        # Validate scope if required
        scope_required = self.config.get("scope_required", False)
        if scope_required and not scope:
            errors.append("Scope is required")

        # Validate allowed scopes if specified
        allowed_scopes = self.config.get("allowed_scopes")
        if allowed_scopes and scope and scope not in allowed_scopes:
            errors.append(f"Invalid scope: {scope}. Must be one of: {', '.join(allowed_scopes)}")

        # Validate breaking changes
        allowed_breaking = self.config.get("allowed_breaking_changes", [])
        if breaking and type_name not in allowed_breaking:
            errors.append(f"Breaking changes not allowed for type: {type_name}")

        # Validate subject length
        max_subject_length = self.config.get("max_subject_length", 100)
        subject_line = f"{type_name}"
        if scope:  # Only add parentheses if scope exists
            subject_line += f"({scope})"
        if breaking:
            subject_line += "!"
        subject_line += f": {description}"

        if len(subject_line) > max_subject_length:
            errors.append(f"Subject line too long ({len(subject_line)} > {max_subject_length})")

        # Validate subject case
        subject_case = self.config.get("subject_case", "lower")
        if subject_case == "lower" and not description[0].islower():
            errors.append("Subject description must start with lowercase")
        elif subject_case == "upper" and not description[0].isupper():
            errors.append("Subject description must start with uppercase")

        # Validate no period at end
        no_period_end = self.config.get("no_period_end", True)
        if no_period_end and description.strip().endswith("."):
            errors.append("Subject description should not end with period")

        # Validate body if required
        body_required = self.config.get("body_required", False)
        if body_required and not body:
            errors.append("Body is required")

        # Validate footer if required
        footer_required = self.config.get("footer_required", False)
        if footer_required and not footer:
            errors.append("Footer is required")

        return ConventionalCommitResult(
            valid=len(errors) == 0,
            errors=errors,
            type=type_name,
            scope=scope,
            breaking=breaking,
            description=description,
            body=body,
            footer=footer,
        )

    def prompt_for_message(self, config: Dict[str, Any]) -> str:
        """Interactive prompt to create a Conventional Commits message"""
        console.print(Panel("Create a Conventional Commit message", title="Commit Message"))

        # Get type
        valid_types = config.get("types", [])
        type_choices = []
        for t in valid_types:
            description = COMMIT_TYPE_DESCRIPTIONS.get(t, "")
            type_choices.append({"name": f"{t}: {description}" if description else t, "value": t})

        type_idx = questionary.select("Commit type:", choices=type_choices).ask()

        # Get scope
        scope = ""
        scope_required = config.get("scope_required", False)
        allowed_scopes = config.get("allowed_scopes")

        if allowed_scopes:
            scope_choices = [{"name": s, "value": s} for s in allowed_scopes]
            if not scope_required:
                # Add option for no scope
                scope_choices.insert(0, {"name": "No scope", "value": ""})

            scope = questionary.select("Scope:", choices=scope_choices).ask()
        else:
            scope_prompt = "Scope (optional):" if not scope_required else "Scope:"
            scope = questionary.text(scope_prompt).ask() or ""
            while scope_required and not scope:
                console.print("[red]Scope is required[/red]")
                scope = questionary.text(scope_prompt).ask() or ""

        # Breaking change
        allowed_breaking = config.get("allowed_breaking_changes", [])
        breaking = False
        breaking_description = ""
        if type_idx in allowed_breaking:
            breaking = questionary.confirm("Is this a breaking change?", default=False).ask()
            if breaking:
                # Get description of the breaking change for the footer
                breaking_description = (
                    questionary.text(
                        "Describe the breaking change (this will be added to the footer):",
                        instruction="BREAKING CHANGE:",
                    ).ask()
                    or "Breaking changes"
                )

        # Description
        description = questionary.text("Description:").ask()

        # Body
        body_required = config.get("body_required", False)
        body = ""
        if body_required or questionary.confirm("Add body?", default=False).ask():
            console.print("Enter body (press Esc + Enter when done):")
            body = questionary.text("", multiline=True).ask() or ""

        # Footer
        footer_required = config.get("footer_required", False)
        footer = ""

        # If breaking change, set up footer with BREAKING CHANGE prefix
        if breaking:
            footer = f"BREAKING CHANGE: {breaking_description}"

        # If additional footer content is needed beyond breaking changes
        if footer_required or (not breaking and questionary.confirm("Add footer?", default=False).ask()):
            instruction = "Enter additional footer information" if breaking else "Enter footer"
            console.print(f"{instruction} (press Esc + Enter when done):")
            additional_footer = questionary.text("", multiline=True).ask() or ""

            # Add additional footer content
            if additional_footer:
                if footer:  # We already have breaking change content
                    footer += f"\n\n{additional_footer}"
                else:
                    footer = additional_footer

        # Assemble message
        message = f"{type_idx}"
        if scope:
            message += f"({scope})"
        if breaking:
            message += "!"
        message += f": {description}"

        if body:
            message += f"\n\n{body}"
        if footer:
            message += f"\n\n{footer}"

        return message
