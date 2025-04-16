"""Configuration module for PyDocGen."""

from dataclasses import dataclass
from typing import List


@dataclass
class Config:
    """Configuration for PyDocGen.
    
    Attributes:
        style (str): Docstring style (google, numpy, rst).
        verbosity (int): Level of detail in docstrings (1-3).
        exclude (List[str]): Patterns to exclude from processing.
        include_private (bool): Whether to include private methods (prefixed with _).
    """

    style: str = "google"
    verbosity: int = 2
    exclude: List[str] = None
    include_private: bool = False

    def __post_init__(self):
        """Initialize default values for optional fields."""
        if self.exclude is None:
            self.exclude = []