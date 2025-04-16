#!/usr/bin/env python3
"""Command-line interface for PyDocGen."""

import os
import sys
from pathlib import Path
from typing import Optional

import click
import yaml

from .config import Config
from .docstring_generator import DocstringGenerator
from .git_utils import get_modified_python_files

PASS = 0
FAIL = 1


def load_config(config_path: Optional[str] = None) -> dict:
    """Load configuration from file.
    
    Args:
        config_path (Optional[str], optional): Path to configuration file. Defaults to None.
        
    Returns:
        dict: Configuration dictionary.
    """
    if config_path and os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
            
    # Look for .pydocgen.yaml in the current directory
    default_paths = [".pydocgen.yaml", ".pydocgen.yml"]
    for path in default_paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                return yaml.safe_load(f)
                
    return {}


@click.command()
@click.option(
    "--style",
    type=click.Choice(["google", "numpy", "rst"]),
    default="google",
    help="Docstring style (default: google)",
)
@click.option(
    "--verbosity",
    type=click.IntRange(1, 3),
    default=2,
    help="Level of detail in docstrings (1-3, default: 2)",
)
@click.option(
    "--config",
    type=click.Path(exists=False),
    help="Path to configuration file",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Patterns to exclude from processing (can be used multiple times)",
)
@click.option(
    "--include-private",
    is_flag=True,
    help="Include private methods (prefixed with _)",
)
@click.argument(
    "filenames",
    nargs=-1,
    type=click.Path(exists=True),
)
def main(style, verbosity, config, exclude, include_private, filenames) -> int:
    """PyDocGen - Automatic Python Docstring Generator.
    
    Process Python files to add or update docstrings based on code analysis.
    If FILENAMES are not provided, will use git to find modified files.
    """
    # Load configuration
    config_dict = load_config(config)
    
    # Create config object, prioritizing command-line arguments over config file
    config_obj = Config(
        style=style or config_dict.get("style", "google"),
        verbosity=verbosity or config_dict.get("verbosity", 2),
        exclude=list(exclude) or config_dict.get("exclude", []),
        include_private=include_private or config_dict.get("include_private", False),
    )
    
    # Get files to process
    if filenames:
        files_to_process = [Path(f) for f in filenames if str(f).endswith(".py")]
    else:
        files_to_process = get_modified_python_files()
    
    if not files_to_process:
        click.echo("No Python files to process.")
        return PASS
    
    # Process files
    generator = DocstringGenerator(config_obj)
    modified_files = 0
    
    with click.progressbar(
        files_to_process,
        label="Processing files",
        item_show_func=lambda f: str(f) if f else "",
    ) as bar:
        for file_path in bar:
            if generator.process_file(file_path):
                modified_files += 1
    
    if modified_files > 0:
        click.echo(click.style(f"Added or updated docstrings in {modified_files} file(s).", fg="green"))
    else:
        click.echo("No docstrings needed to be added or updated.")
    
    return PASS


if __name__ == "__main__":
    sys.exit(main())