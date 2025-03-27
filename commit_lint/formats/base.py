"""
Base classes for commit message format handlers.

This module defines the contract that all format handlers must implement,
providing a consistent interface for validation and interactive prompting
regardless of the specific commit message format being used.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pydantic import BaseModel


class CommitFormatResult(BaseModel):
    """
    Base validation result for all commit formats.

    This Pydantic model defines the common structure for validation results
    across different commit message formats.

    Attributes:
        valid: Whether the commit message is valid according to the format rules.
        errors: List of error messages if validation failed.
    """

    valid: bool
    errors: List[str]
    # Common fields across formats


class CommitFormat(ABC):
    """
    Base class for commit format validators.

    This abstract class defines the interface that all commit format validators
    must implement. It provides methods for validating commit messages and
    interactively prompting for new messages.
    """

    @abstractmethod
    def validate(self, commit_message: str) -> CommitFormatResult:
        """
        Validate a commit message according to this format.

        This method checks whether a commit message complies with the format's
        rules and returns a result object with validation status and any errors.

        Args:
            commit_message: The commit message string to validate.

        Returns:
            CommitFormatResult: An object containing validation results.
        """

    @abstractmethod
    @abstractmethod
    def prompt_for_message(self, config: Dict[str, Any]) -> str:
        """
        Interactive prompt to create a message in this format.

        This method guides the user through creating a valid commit message
        by asking for the necessary components according to the format.

        Args:
            config: Configuration dictionary with format-specific settings.

        Returns:
            str: The generated commit message.
        """

    @classmethod
    @abstractmethod
    def get_format_name(cls) -> str:
        """
        Return the name of this format.

        This class method provides the canonical name of the format for use
        in the format registry and configuration.

        Returns:
            str: The format name identifier (e.g., 'conventional', 'github').
        """
