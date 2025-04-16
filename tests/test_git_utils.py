"""Tests for the git utilities module."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from pydocgen.git_utils import get_modified_python_files


class TestGitUtils(unittest.TestCase):
    """Test cases for the git utilities module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for the test git repository
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = Path(self.temp_dir.name)
        
        # Initialize a git repository
        self.old_cwd = os.getcwd()
        os.chdir(self.repo_path)
        subprocess.run(["git", "init"], check=True, capture_output=True)
        
        # Configure git user
        subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True, capture_output=True)
        
        # Create some Python files
        self.py_file1 = self.repo_path / "file1.py"
        self.py_file2 = self.repo_path / "file2.py"
        self.txt_file = self.repo_path / "file.txt"
        
        with open(self.py_file1, "w") as f:
            f.write("# Python file 1")
        
        with open(self.py_file2, "w") as f:
            f.write("# Python file 2")
        
        with open(self.txt_file, "w") as f:
            f.write("Text file")
        
        # Add and commit the files
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True, capture_output=True)
    
    def tearDown(self):
        """Tear down test fixtures."""
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()
    
    def test_get_modified_python_files_no_changes(self):
        """Test get_modified_python_files with no changes."""
        files = get_modified_python_files()
        self.assertEqual(len(files), 0)
    
    def test_get_modified_python_files_with_staged_changes(self):
        """Test get_modified_python_files with staged changes."""
        # Modify a Python file and stage it
        with open(self.py_file1, "a") as f:
            f.write("\n# Modified")
        
        subprocess.run(["git", "add", str(self.py_file1)], check=True, capture_output=True)
        
        files = get_modified_python_files()
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "file1.py")
    
    def test_get_modified_python_files_with_unstaged_changes(self):
        """Test get_modified_python_files with unstaged changes."""
        # Modify a Python file but don't stage it
        with open(self.py_file2, "a") as f:
            f.write("\n# Modified")
        
        files = get_modified_python_files()
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "file2.py")
    
    def test_get_modified_python_files_ignores_non_python_files(self):
        """Test get_modified_python_files ignores non-Python files."""
        # Modify a non-Python file
        with open(self.txt_file, "a") as f:
            f.write("\nModified")
        
        subprocess.run(["git", "add", str(self.txt_file)], check=True, capture_output=True)
        
        files = get_modified_python_files()
        self.assertEqual(len(files), 0)


if __name__ == "__main__":
    unittest.main()