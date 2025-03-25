from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from pydantic import BaseModel


class CommitFormatResult(BaseModel):
    """Base validation result for all commit formats"""

    valid: bool
    errors: List[str]
    # Common fields across formats


class CommitFormat(ABC):
    """Base class for commit format validators"""

    @abstractmethod
    def validate(self, commit_message: str) -> CommitFormatResult:
        """Validate a commit message according to this format"""
        pass

    @abstractmethod
    def prompt_for_message(self, config: Dict[str, Any]) -> str:
        """Interactive prompt to create a message in this format"""
        pass

    @classmethod
    @abstractmethod
    def get_format_name(cls) -> str:
        """Return the name of this format"""
        pass
