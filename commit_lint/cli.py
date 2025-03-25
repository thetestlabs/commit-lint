import tempfile
import subprocess
from typing import List, Optional
from pathlib import Path
from importlib.metadata import version as get_version

import typer
from rich.panel import Panel
from rich.console import Console

from .config import load_config
from .formats import get_commit_format

# Get version from package metadata
try:
    __version__ = get_version("commit-lint")
except ImportError:
    # During development, fallback to version in package's __init__.py
    try:
        from . import __version__
    except (ImportError, AttributeError):
        __version__ = "unknown"

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


@app.command()
def create(
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Path to config file"),
    format_type: Optional[str] = typer.Option(
        None, "--format-type", "-f", help="Override format type (conventional, github, jira, custom)"
    ),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="File to write commit message to"),
):
    """Interactively create a commit message according to configured format."""
    from .formats import FORMAT_REGISTRY

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
    except Exception as e:
        console.print(f"[bold red]Error loading config:[/bold red] {str(e)}")
        raise typer.Exit(code=1)

    # Use format-specific prompt_for_message
    commit_message = commit_format.prompt_for_message(config)

    # Validate the message we just created
    result = commit_format.validate(commit_message)

    if not result.valid:
        console.print("\n[bold yellow]⚠️  Warning: The generated commit message has validation issues:[/bold yellow]")
        for error in result.errors:
            console.print(f"  • {error}")
        console.print("\nYou may want to adjust the message before using it.")
    else:
        console.print("\n[bold green]✓ Commit message is valid![/bold green]")

    # Save message to file if requested
    if output_file:
        with open(output_file, "w") as f:
            f.write(commit_message)
        console.print(f"[bold green]Commit message saved to {output_file}[/bold green]")
    else:
        # Just print the message
        console.print(Panel(commit_message, title="Generated Commit Message"))

    # For non-interactive usage, we want to return a non-zero exit code if validation failed
    if not result.valid:
        raise typer.Exit(code=1)

    return 0


@app.command()
def lint(
    commit_msg_file: Optional[Path] = typer.Argument(None, help="Path to commit message file (used by Git hooks)"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Path to config file"),
    format_type: Optional[str] = typer.Option(
        None, "--format-type", "-f", help="Override format type (conventional, github, jira, custom)"
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Enable/disable interactive mode on failure",
    ),
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Commit message to lint (for CLI usage)"),
):
    """
    Lint a commit message according to configured format.
    """
    import sys
    from .formats import FORMAT_REGISTRY

    # Auto-disable interactive mode if not in a TTY
    if not sys.stdout.isatty():
        interactive = False

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
    except Exception as e:
        console.print(f"[bold red]Error loading config:[/bold red] {str(e)}")
        raise typer.Exit(code=1)

    # Get commit message from file or direct input
    commit_message = ""
    if message:
        commit_message = message
    elif commit_msg_file:
        try:
            with open(commit_msg_file, "r") as f:
                commit_message = f.read()
        except Exception as e:
            console.print(f"[bold red]Error reading commit message file:[/bold red] {str(e)}")
            raise typer.Exit(code=1)
    else:
        console.print("[bold yellow]No commit message provided.[/bold yellow]")
        console.print("Use --message/-m to provide a message or specify a commit message file.")
        raise typer.Exit(code=1)

    # Validate the message using the selected format
    result = commit_format.validate(commit_message)

    if result.valid:
        console.print("[bold green]Commit message is valid![/bold green]")
        return 0

    # If invalid, show errors
    console.print("[bold red]Commit message validation failed:[/bold red]")
    for error in result.errors:
        console.print(f"  • {error}")

    # If interactive mode is enabled and we're in a terminal, help fix the message
    if interactive:
        console.print("\n[bold]Let's fix your commit message...[/bold]")
        # Use the format-specific prompt_for_message method instead of the old function
        new_message = commit_format.prompt_for_message(config)

        # If this was called from a Git hook, write the new message back to the file
        if commit_msg_file:
            with open(commit_msg_file, "w") as f:
                f.write(new_message)
            console.print("[bold green]New commit message saved to file.[/bold green]")
        else:
            # For CLI usage, just print the message
            console.print(Panel(new_message, title="Use this commit message"))

        return 0
    else:
        # Non-interactive mode - just fail
        raise typer.Exit(code=1)


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
    from .formats import FORMAT_REGISTRY
    import tempfile
    import subprocess

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
    except Exception as e:
        console.print(f"[bold red]Error loading config:[/bold red] {str(e)}")
        raise typer.Exit(code=1)

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

        if commit_process.returncode == 0:
            console.print("[bold green]Changes committed successfully![/bold green]")
            # Show the commit output
            console.print(commit_process.stdout)
            return 0
        else:
            # If hooks or commit failed
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

            raise typer.Exit(code=1)
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
    from .formats import FORMAT_REGISTRY
    import yaml

    # Check if the selected format is valid
    if format_type not in FORMAT_REGISTRY:
        valid_formats = ", ".join(FORMAT_REGISTRY.keys())
        console.print(f"[bold red]Invalid format type: {format_type}[/bold red]")
        console.print(f"Valid formats: {valid_formats}")
        raise typer.Exit(code=1)

    # Default config based on format type
    config = {"format_type": format_type}

    # Add format-specific defaults
    if format_type == "conventional":
        config.update(
            {
                "types": ["feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"],
                "max_subject_length": 100,
                "subject_case": "lower",
                "scope_required": False,
                "allowed_breaking_changes": ["feat", "fix"],
                "no_period_end": True,
            }
        )
    elif format_type == "github":
        config.update(
            {
                "max_subject_length": 72,
                "imperative_mood": True,
                "issue_reference_required": False,
                "keywords": ["Fixes", "Closes", "Resolves"],
            }
        )
    elif format_type == "jira":
        config.update({"jira_project_keys": ["PROJ"], "require_issue_id": True, "max_message_length": 72})

    # Write to pyproject.toml or yaml file
    if output_file.name == "pyproject.toml":
        # Check if file exists and read it first
        if output_file.exists():
            with open(output_file, "rb") as f:
                try:
                    import tomli

                    existing_config = tomli.load(f)
                except Exception as e:
                    console.print(f"[bold red]Error reading existing pyproject.toml: {e}[/bold red]")
                    raise typer.Exit(code=1)

            # Update with tool.commit_lint section
            if "tool" not in existing_config:
                existing_config["tool"] = {}
            existing_config["tool"]["commit_lint"] = config

            # Write back
            import tomli_w

            with open(output_file, "wb") as f:
                tomli_w.dump(existing_config, f)
        else:
            # Create new file
            import tomli_w

            with open(output_file, "wb") as f:
                tomli_w.dump({"tool": {"commit_lint": config}}, f)
    else:
        # Handle YAML output for backwards compatibility
        with open(output_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

    console.print(f"[bold green]Configuration created at {output_file}[/bold green]")


if __name__ == "__main__":
    app()
