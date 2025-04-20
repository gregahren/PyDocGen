"""Configuration module for PyDocGen."""

from dataclasses import dataclass
from typing import List


@dataclass
class Config:
    """Configuration for PyDocGen.
    
    Attributes:
        style (str): Docstring style (google, numpy, rst).
        exclude (List[str]): Glob patterns to exclude from processing.
            Examples: ["tests/*.py", "pydocgen/cli.py", "*_test.py"]
        include_private (bool): Whether to include private methods (prefixed with _).
    """

    style: str = "google"
    exclude: List[str] = None
    include_private: bool = False

    def __post_init__(self):
        """Initialize default values for optional fields."""
        if self.exclude is None:
            self.exclude = []
        
        # Validate exclude patterns
        if not isinstance(self.exclude, list):
            raise ValueError("exclude must be a list of string patterns")
            
        # Ensure all patterns are strings
        self.exclude = [str(pattern) for pattern in self.exclude if pattern]