import tempfile
import subprocess
from typing import List, Optional, Dict, Any
from pathlib import Path
from importlib.metadata import version as get_version
from importlib.metadata import PackageNotFoundError

import typer
import tomli
from rich.panel import Panel
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown

from .config import load_config
from .formats import FORMAT_REGISTRY
from .formats import get_commit_format

# Get version from package metadata
try:
    __version__ = get_version("commit-lint")
except (ImportError, PackageNotFoundError):
    # During development, fallback to a default version
    __version__ = "0.1.0.dev0"

app = typer.Typer(
    help="""A configurable linter for better commit messages.

Supports multiple commit message formats:
- conventional: Conventional Commits format (https://www.conventionalcommits.org)
- github: GitHub style commit messages
- jira: Jira-style commit messages with ticket IDs
- custom: Custom format defined by regex pattern
"""
)
console = Console()


# Add version callback
def version_callback(value: bool):
    if value:
        console.print(f"Commit Message Linter version: {__version__}")
        raise typer.Exit()


def show_rules_callback(value: bool):
    """Display validation rules for all supported commit message formats."""
    if value:
        console.print("\n[bold]Commit Message Validation Rules[/bold]\n")

        # Display rules for Conventional Commits
        console.print(Markdown("## Conventional Commits Format"))
        conventional_table = Table(show_header=True, header_style="bold")
        conventional_table.add_column("Rule", style="dim")
        conventional_table.add_column("Description")
        conventional_table.add_column("Config Option", style="dim")

        conventional_table.add_row("Format pattern", "Must follow `type(scope)?: description` format", "-")
        conventional_table.add_row(
            "Type validation", "Type must be one of the predefined types", 'types = ["feat", "fix", ...]'
        )
        conventional_table.add_row(
            "Scope requirement", "Scope can be required or optional", "scope_required = true/false"
        )
        conventional_table.add_row(
            "Allowed scopes", "Scope must be in allowed list (if specified)", 'allowed_scopes = ["api", "ui", ...]'
        )
        conventional_table.add_row(
            "Breaking changes", "Only allowed for specific types", 'allowed_breaking_changes = ["feat", "fix"]'
        )
        conventional_table.add_row(
            "Subject length", "Subject line must not exceed maximum length", "max_subject_length = 100"
        )
        conventional_table.add_row(
            "Subject case", "Subject must start with specified case", 'subject_case = "lower"/"upper"'
        )
        conventional_table.add_row("No period", "Subject should not end with period", "no_period_end = true/false")
        console.print(conventional_table)

        # Display rules for GitHub style
        console.print(Markdown("## GitHub Style Format"))
        github_table = Table(show_header=True, header_style="bold")
        github_table.add_column("Rule", style="dim")
        github_table.add_column("Description")
        github_table.add_column("Config Option", style="dim")

        github_table.add_row(
            "Subject length", "Brief, concise subject line (usually 50-72 chars)", "max_subject_length = 72"
        )
        github_table.add_row(
            "Imperative mood", 'Use imperative verbs like "Add" not "Added"', "imperative_mood = true/false"
        )
        github_table.add_row(
            "Issue references", 'Refs with keywords: "Fixes #123"', 'keywords = ["Fixes", "Closes", ...]'
        )
        github_table.add_row(
            "Required reference", "Issue reference can be required", "issue_reference_required = false/true"
        )
        console.print(github_table)

        # Display rules for Jira style
        console.print(Markdown("## Jira Style Format"))
        jira_table = Table(show_header=True, header_style="bold")
        jira_table.add_column("Rule", style="dim")
        jira_table.add_column("Description")
        jira_table.add_column("Config Option", style="dim")

        jira_table.add_row(
            "Issue ID", "Must start with Jira issue ID (e.g., PROJ-123)", "require_issue_id = true/false"
        )
        jira_table.add_row(
            "Project keys", "Issue ID must match project keys (if specified)", 'jira_project_keys = ["PROJ", "TEST"]'
        )
        jira_table.add_row("Message length", "Message part must not exceed max length", "max_message_length = 72")
        console.print(jira_table)

        # Display rules for Custom format
        console.print(Markdown("## Custom Format"))
        custom_table = Table(show_header=True, header_style="bold")
        custom_table.add_column("Rule", style="dim")
        custom_table.add_column("Description")
        custom_table.add_column("Config Option", style="dim")

        custom_table.add_row(
            "Pattern matching",
            "Commit message must match the provided regex pattern",
            'custom_pattern = "^\\\\[\\\\w+\\\\] .+$"',
        )
        console.print(custom_table)

        # Example config in pyproject.toml
        console.print(Markdown("## Example Configuration"))
        console.print(
            Markdown(
                '```toml\n[tool.commit_lint]\n# Common configuration\nformat_type = "conventional"  # or "github", "jira", "custom"\n\n# Format-specific settings\ntypes = ["feat", "fix", "docs"]\nmax_subject_length = 100\nscope_required = false\n```'
            )
        )

        raise typer.Exit()


# Add version option to all commands
@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show the application version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
    show_rules: bool = typer.Option(
        False,
        "--show-rules",
        "-r",
        help="Show validation rules for all formats.",
        callback=show_rules_callback,
        is_eager=True,
    ),
):
    """
    A tool to lint and help craft conventional commit messages.
    """
    pass


def get_staged_files() -> List[str]:
    """Get a list of files staged for commit."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [file for file in result.stdout.splitlines() if file.strip()]


# Helper functions for CLI commands
def _load_config_and_format(config_file: Optional[str], format_type: Optional[str]):
    """Load configuration and create appropriate format validator."""

    # Convert string to Path if provided
    config_path = Path(config_file) if config_file else None

    try:
        config = load_config(config_path)

        # Override format type if specified
        if format_type:
            if format_type not in FORMAT_REGISTRY:
                valid_formats = ", ".join(FORMAT_REGISTRY.keys())
                console.print(f"[bold red]Invalid format type: {format_type}[/bold red]")
                console.print(f"Valid formats: {valid_formats}")
                raise typer.Exit(code=1)

            # Override the format type in the config
            config["format_type"] = format_type
            console.print(f"[blue]Using format type: {format_type}[/blue]")

        commit_format = get_commit_format(config)
        return config, commit_format
    except Exception as e:
        console.print(f"[bold red]Error loading config:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


def _get_message_from_sources(message: Optional[str], file: Optional[Path]):
    """Get commit message from available sources (CLI arg, file, or stdin)."""

    if message:
        # Message provided via command line option
        return message
    elif file:
        if str(file) == "-":
            # Read from stdin when file is "-"
            return typer.get_text_stream("stdin").read().strip()
        elif file.exists():
            # Read from file
            return file.read_text().strip()
        else:
            console.print(f"[red]Error:[/red] File not found: {file}")
            raise typer.Exit(code=1)
    elif not typer.get_text_stream("stdin").isatty():
        # No message or file specified, but stdin has content
        return typer.get_text_stream("stdin").read().strip()
    else:
        # No message provided
        console.print("[red]Error:[/red] No message provided")
        raise typer.Exit(code=1)


def _check_staged_changes():
    """Check if there are staged changes and offer to stage all if needed."""
    try:
        diff_result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, check=True
        )
        if not diff_result.stdout.strip():
            console.print("[bold yellow]Warning: No staged changes to commit.[/bold yellow]")
            if not typer.confirm("Stage all changes?", default=False):
                console.print("Use 'git add' to stage changes and try again.")
                raise typer.Exit(code=1)

            # Stage all changes
            subprocess.run(["git", "add", "-A"], check=True)
            console.print("[blue]All changes staged for commit.[/blue]")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Failed to check staged changes:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


def _run_git_commit(commit_message: str, skip_hooks: bool):
    """Execute git commit with the provided message."""
    # Save message to temp file for git commit
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
        temp_path = Path(temp.name)
        temp.write(commit_message)

    try:
        # Prepare git commit command
        git_cmd = ["git", "commit", "-F", str(temp_path)]

        # Add --no-verify flag if requested to skip hooks
        if skip_hooks:
            git_cmd.append("--no-verify")
            console.print("[yellow]Skipping pre-commit hooks[/yellow]")
        else:
            console.print("[blue]Running pre-commit hooks...[/blue]")

        # Execute git commit with the message file
        commit_process = subprocess.run(git_cmd, capture_output=True, text=True)

        return commit_process, temp_path
    except Exception as e:
        # Clean up temp file in case of exception
        temp_path.unlink(missing_ok=True)
        raise e


def _handle_commit_failure(commit_process, commit_message: str, output_file: Optional[Path]):
    """Handle git commit failure and potentially save the message."""
    if "hook" in commit_process.stderr.lower():
        console.print("[bold red]Pre-commit hooks failed:[/bold red]")
    else:
        console.print("[bold red]Git commit failed:[/bold red]")

    console.print(commit_process.stderr)
    console.print("\nYou can run with --no-verify to skip hooks.")

    # Save the commit message if requested for later use
    if output_file or typer.confirm("Save commit message for later use?", default=True):
        output_path = output_file or Path(".git/COMMIT_EDITMSG")
        with open(output_path, "w") as f:
            f.write(commit_message)
        console.print(f"[green]Commit message saved to {output_path}[/green]")

    return 1  # Non-zero return code


def _validate_and_display_message(commit_message: str, commit_format):
    """Validate a commit message and display results."""
    result = commit_format.validate(commit_message)

    if not result.valid:
        console.print("\n[bold yellow]⚠️  Warning: The generated commit message has validation issues:[/bold yellow]")
        for error in result.errors:
            console.print(f"  • {error}")
        console.print("\nYou may want to adjust the message before using it.")
    else:
        console.print("\n[bold green]✓ Commit message is valid![/bold green]")

    return result


def _save_or_display_message(commit_message: str, output_file: Optional[Path]):
    """Save the commit message to file or display it."""
    if output_file:
        with open(output_file, "w") as f:
            f.write(commit_message)
        console.print(f"[bold green]Commit message saved to {output_file}[/bold green]")
    else:
        # Just print the message
        console.print(Panel(commit_message, title="Generated Commit Message"))


def _get_format_specific_defaults(format_type: str) -> Dict[str, str]:
    """Get default configuration values for a specific format type."""
    if format_type == "conventional":
        return {
            "types": ",".join(
                ["feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"]
            ),
            "max_subject_length": "100",
            "subject_case": "lower",
            "scope_required": "False",
            "allowed_breaking_changes": ",".join(["feat", "fix"]),
            "no_period_end": "True",
        }
    elif format_type == "github":
        return {
            "max_subject_length": "72",
            "imperative_mood": "True",
            "issue_reference_required": "False",
            "keywords": ",".join(["Fixes", "Closes", "Resolves"]),
        }
    elif format_type == "jira":
        return {"jira_project_keys": ",".join(["PROJ"]), "require_issue_id": "True", "max_message_length": "72"}
    elif format_type == "custom":
        return {
            "custom_pattern": "^\\[(?P<category>\\w+)\\] (?P<message>.+)$",
            "message_template": "[{category}] {message}",
            "category_prompt": "Category (e.g. FEATURE, BUGFIX)",
            "message_prompt": "Commit message",
        }
    return {}


def _write_config_to_file(output_file: Path, config: Dict[str, Any]):
    """Write configuration to the appropriate file format."""
    import tomli_w

    try:
        if output_file.name == "pyproject.toml":
            _write_to_pyproject(output_file, config)
        else:
            # Write standalone TOML file
            with open(output_file, "wb") as f:
                tomli_w.dump(config, f)

        console.print(f"[bold green]Configuration created at {output_file}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Failed to write configuration:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


def _write_to_pyproject(pyproject_path: Path, config: Dict[str, Any]):
    """Write configuration to a pyproject.toml file."""
    import tomli
    import tomli_w

    # Check if file exists and read it first
    if pyproject_path.exists():
        with open(pyproject_path, "rb") as f:
            try:
                existing_config = tomli.load(f)
            except Exception as e:
                console.print(f"[bold red]Error reading existing pyproject.toml: {e}[/bold red]")
                raise typer.Exit(code=1)

        # Update with tool.commit_lint section
        if "tool" not in existing_config:
            existing_config["tool"] = {}
        existing_config["tool"]["commit_lint"] = config

        # Write back
        with open(pyproject_path, "wb") as f:
            tomli_w.dump(existing_config, f)
    else:
        # Create new file
        with open(pyproject_path, "wb") as f:
            tomli_w.dump({"tool": {"commit_lint": config}}, f)


@app.command()
def create(
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Path to config file"),
    format_type: Optional[str] = typer.Option(
        None, "--format-type", "-f", help="Override format type (conventional, github, jira, custom)"
    ),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="File to write commit message to"),
):
    """Interactively create a commit message according to configured format."""
    # Load config and create format validator
    config, commit_format = _load_config_and_format(config_file, format_type)

    # Use format-specific prompt_for_message
    commit_message = commit_format.prompt_for_message(config)

    # Validate the message we just created
    result = _validate_and_display_message(commit_message, commit_format)

    # Save message to file or display it
    _save_or_display_message(commit_message, output_file)

    # For non-interactive usage, we want to return a non-zero exit code if validation failed
    if not result.valid:
        raise typer.Exit(code=1)

    return 0


@app.command("lint")
def lint(
    message: Optional[str] = typer.Option(None, "-m", "--message", help="Message to lint"),
    file: Optional[Path] = typer.Argument(None, help="Path to commit message file or '-' for stdin"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Path to config file"),
    format_type: Optional[str] = typer.Option(
        None, "--format-type", "-f", help="Override format type (conventional, github, jira, custom)"
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Enable/disable interactive mode on failure",
    ),
):
    """
    Lint a commit message according to configured format.
    """
    import sys

    # Auto-disable interactive mode if not in a TTY
    if not sys.stdout.isatty():
        interactive = False

    # Load config and create format validator
    config, commit_format = _load_config_and_format(config_file, format_type)

    # Get the message to lint from available sources
    message_text = _get_message_from_sources(message, file)

    # Validate the message
    result = commit_format.validate(message_text)

    if result.valid:
        console.print("[bold green]Commit message is valid![/bold green]")
        return 0

    # Show errors for invalid messages
    _display_validation_errors(result)

    # Handle interactive mode
    if interactive:
        return _handle_interactive_fix(commit_format, config, file, message_text)
    else:
        # Non-interactive mode - just fail
        raise typer.Exit(code=1)


def _display_validation_errors(result):
    """Display validation errors from a result object."""
    console.print("[bold red]Commit message validation failed:[/bold red]")
    for error in result.errors:
        console.print(f"  • {error}")


def _handle_interactive_fix(commit_format, config, file, original_message):
    """Handle interactive fixing of invalid commit messages."""
    console.print("\n[bold]Let's fix your commit message...[/bold]")
    # Use the format-specific prompt_for_message method
    new_message = commit_format.prompt_for_message(config)

    # If this was called from a Git hook, write the new message back to the file
    if file:
        with open(file, "w") as f:
            f.write(new_message)
        console.print("[bold green]New commit message saved to file.[/bold green]")
    else:
        # For CLI usage, just print the message
        console.print(Panel(new_message, title="Use this commit message"))

    return 0


@app.command()
def commit(
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Path to config file"),
    format_type: Optional[str] = typer.Option(
        None, "--format-type", "-f", help="Override format type (conventional, github, jira, custom)"
    ),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="File to write commit message to"),
    skip_hooks: bool = typer.Option(False, "--no-verify", help="Skip pre-commit hooks"),
):
    """Create a commit message and commit changes."""
    # Load config and create format validator
    config, commit_format = _load_config_and_format(config_file, format_type)

    # Generate commit message interactively
    commit_message = commit_format.prompt_for_message(config)

    # Validate the message
    result = commit_format.validate(commit_message)
    if not result.valid:
        console.print("\n[bold yellow]⚠️ Warning: The commit message has validation issues:[/bold yellow]")
        for error in result.errors:
            console.print(f"  • {error}")

        if not typer.confirm("Continue with invalid commit message?", default=False):
            raise typer.Exit(code=1)

    # Check if there are staged changes
    _check_staged_changes()

    # Execute git commit
    commit_process, temp_path = _run_git_commit(commit_message, skip_hooks)

    try:
        if commit_process.returncode == 0:
            console.print("[bold green]Changes committed successfully![/bold green]")
            # Show the commit output
            console.print(commit_process.stdout)
            return 0
        else:
            # Handle commit failure
            return _handle_commit_failure(commit_process, commit_message, output_file)
    finally:
        # Clean up temp file
        temp_path.unlink(missing_ok=True)


@app.command()
def install():
    """
    Install Git hooks in the current repository.
    """
    git_dir = Path(".git")
    if not git_dir.exists():
        console.print("[bold red]Not a Git repository (or .git directory not found)[/bold red]")
        raise typer.Exit(code=1)

    hook_dir = git_dir / "hooks"
    hook_dir.mkdir(exist_ok=True)

    # Check if pre-commit framework is installed
    pre_commit_installed = False
    try:
        # Run pre-commit --version to check if installed
        result = subprocess.run(["pre-commit", "--version"], capture_output=True, text=True, check=False)
        pre_commit_installed = result.returncode == 0
    except Exception:
        pre_commit_installed = False

    if pre_commit_installed:
        console.print("[yellow]pre-commit framework detected[/yellow]")
        console.print("Installing pre-commit hooks...")
        try:
            # Install pre-commit hooks
            subprocess.run(["pre-commit", "install", "--install-hooks"], check=True)
            # Backup the original pre-commit hook
            pre_commit_path = hook_dir / "pre-commit"
            if pre_commit_path.exists():
                backup_path = hook_dir / ".pre-commit-hook"
                with open(pre_commit_path, "r") as src, open(backup_path, "w") as dst:
                    dst.write(src.read())
                backup_path.chmod(0o755)
                console.print(f"[green]Backed up pre-commit framework hook to {backup_path}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to install pre-commit framework hooks: {e}[/red]")

    # Install pre-commit hook
    pre_commit_path = hook_dir / "pre-commit"
    with open(pre_commit_path, "w") as f:
        f.write(
            """#!/bin/sh
# pre-commit hook for creating conventional commits

# Debug log file
DEBUG_LOG="/tmp/commit-lint-debug.log"

# Start debug logging
echo "====== $(date) ======" >> "$DEBUG_LOG"
echo "Running pre-commit hook" >> "$DEBUG_LOG"

# Location of the pre-commit framework's hook
FRAMEWORK_HOOK=".git/hooks/.pre-commit-hook"

# Better detection of -m flag
# Check command line args from git
git_orig_cmd=$(ps -ocommand= -p $PPID)
echo "Git command: $git_orig_cmd" >> "$DEBUG_LOG"

# Run the pre-commit framework hooks first regardless of -m flag
if [ -x "$FRAMEWORK_HOOK" ]; then
    echo "Running pre-commit framework hooks" >> "$DEBUG_LOG"
    "$FRAMEWORK_HOOK"
    HOOK_STATUS=$?

    if [ $HOOK_STATUS -ne 0 ]; then
        echo "Pre-commit framework hooks failed with code $HOOK_STATUS" >> "$DEBUG_LOG"
        exit $HOOK_STATUS
    else
        echo "Pre-commit framework hooks succeeded" >> "$DEBUG_LOG"
    fi
else
    echo "No pre-commit framework hook found at $FRAMEWORK_HOOK" >> "$DEBUG_LOG"
fi

# Check if -m is in the command
if echo "$git_orig_cmd" | grep -q -- " -m "; then
    echo "Detected -m flag in command, letting Git continue to commit-msg hook" >> "$DEBUG_LOG"
    # We'll let the commit-msg hook handle the linting
    exit 0
fi

# Check if this is a commit being created by our own tool to avoid recursion
if [ -n "$CONVENTIONAL_COMMIT_IN_PROGRESS" ]; then
    echo "Detected recursive call, exiting" >> "$DEBUG_LOG"
    exit 0
fi

# Prevent the normal commit from proceeding
export CONVENTIONAL_COMMIT_IN_PROGRESS=1

# Run our commit tool instead
echo "Running commit-lint commit" >> "$DEBUG_LOG"
commit-lint commit
EXIT_CODE=$?

# The exit code of the commit tool determines if the commit proceeds
exit $EXIT_CODE
"""
        )

    # Install commit-msg hook
    commit_msg_path = hook_dir / "commit-msg"
    with open(commit_msg_path, "w") as f:
        f.write(
            """#!/bin/sh
# commit-msg hook for linting commit messages

DEBUG_LOG="/tmp/commit-lint-debug.log"
echo "====== $(date) ======" >> "$DEBUG_LOG"
echo "Running commit-msg hook" >> "$DEBUG_LOG"
echo "Commit message file: $1" >> "$DEBUG_LOG"

# Skip if we're handling this ourselves via the pre-commit hook
if [ -n "$CONVENTIONAL_COMMIT_IN_PROGRESS" ]; then
    echo "CONVENTIONAL_COMMIT_IN_PROGRESS is set, skipping commit-msg hook" >> "$DEBUG_LOG"
    exit 0
fi

# Run the linting tool in non-interactive mode
echo "Running commit-lint lint" >> "$DEBUG_LOG"
commit-lint lint "$1" --no-interactive
EXIT_CODE=$?

exit $EXIT_CODE
"""
        )

    # Make both hooks executable
    pre_commit_path.chmod(0o755)
    commit_msg_path.chmod(0o755)

    console.print("[bold green]Git hooks installed successfully![/bold green]")
    console.print(f"pre-commit hook: {pre_commit_path}")
    console.print(f"commit-msg hook: {commit_msg_path}")


@app.command()
def init(
    output_file: Path = typer.Option("pyproject.toml", help="Output config file path"),
    format_type: str = typer.Option(
        "conventional", "--format-type", "-f", help="Commit format type (conventional, github, jira, custom)"
    ),
):
    """Create a new configuration file with default settings."""
    # Check if the selected format is valid
    if format_type not in FORMAT_REGISTRY:
        valid_formats = ", ".join(FORMAT_REGISTRY.keys())
        console.print(f"[bold red]Invalid format type: {format_type}[/bold red]")
        console.print(f"Valid formats: {valid_formats}")
        raise typer.Exit(code=1)

    # Build config dictionary with format type and format-specific defaults
    config = {"format_type": format_type}
    config.update(_get_format_specific_defaults(format_type))

    # Write config to the specified file
    _write_config_to_file(output_file, config)


if __name__ == "__main__":
    app()
