"""Git utilities for PyDocGen."""

import subprocess
from pathlib import Path
from typing import List


def get_modified_python_files() -> List[Path]:
    """Get a list of Python files that have been modified in the current Git staging area.
    
    Returns:
        List[Path]: List of modified Python file paths.
    """
    try:
        # Get staged files
        staged_cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"]
        staged_output = subprocess.check_output(staged_cmd, universal_newlines=True)
        staged_files = staged_output.splitlines()
        
        # Get unstaged files
        unstaged_cmd = ["git", "diff", "--name-only", "--diff-filter=ACMR"]
        unstaged_output = subprocess.check_output(unstaged_cmd, universal_newlines=True)
        unstaged_files = unstaged_output.splitlines()
        
        # Combine and filter for Python files
        all_files = set(staged_files + unstaged_files)
        python_files = [Path(f) for f in all_files if f.endswith(".py")]
        
        return python_files
    except subprocess.CalledProcessError:
        # Not in a git repository or git command failed
        return []