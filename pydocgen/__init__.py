"""PyDocGen Hook - Automatic Python Docstring Generator.

This package provides a pre-commit hook that automatically detects changes in Python files
and intelligently adds missing docstrings to modules, classes, and methods by analyzing their code.
"""

__version__ = "0.1.0"

from .cli import main