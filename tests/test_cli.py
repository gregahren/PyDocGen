"""Tests for the CLI module."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import click
from click.testing import CliRunner

from pydocgen.cli import load_config, main


class TestCLI(unittest.TestCase):
    """Test cases for the CLI module."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.runner = CliRunner()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()
    
    def test_load_config_from_path(self):
        """Test load_config with a specified path."""
        config_path = self.temp_path / "config.yaml"
        with open(config_path, "w") as f:
            f.write("""
style: numpy
exclude:
  - tests/*
  - setup.py
include_private: true
""")
        
        config = load_config(str(config_path))
        self.assertEqual(config["style"], "numpy")
        self.assertEqual(config["exclude"], ["tests/*", "setup.py"])
        self.assertTrue(config["include_private"])
    
    def test_load_config_default_path(self):
        """Test load_config with default path."""
        # Create a config file in the current directory
        old_cwd = os.getcwd()
        os.chdir(self.temp_path)
        
        try:
            with open(".pydocgen.yaml", "w") as f:
                f.write("""
style: rst
exclude:
  - tests/*
include_private: false
""")
            
            config = load_config()
            self.assertEqual(config["style"], "rst")
            self.assertEqual(config["exclude"], ["tests/*"])
            self.assertFalse(config["include_private"])
        finally:
            os.chdir(old_cwd)
    
    def test_load_config_no_file(self):
        """Test load_config with no config file."""
        config = load_config("nonexistent.yaml")
        self.assertEqual(config, {})
    
    @patch('pydocgen.cli.get_modified_python_files')
    @patch('pydocgen.cli.DocstringGenerator')
    def test_cli_no_files(self, mock_generator_class, mock_get_files):
        """Test CLI with no files to process."""
        mock_get_files.return_value = []
        mock_generator = mock_generator_class.return_value
        
        result = self.runner.invoke(main)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("No Python files to process", result.output)
        mock_generator_class.assert_called_once()
        mock_get_files.assert_called_once()
    
    @patch('pydocgen.cli.get_modified_python_files')
    @patch('pydocgen.cli.DocstringGenerator')
    def test_cli_with_files(self, mock_generator_class, mock_get_files):
        """Test CLI with files to process."""
        mock_generator = mock_generator_class.return_value
        mock_generator.process_file.return_value = True
        
        mock_get_files.return_value = [Path("file1.py"), Path("file2.py")]
        
        result = self.runner.invoke(main)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Added or updated docstrings in 2 file(s)", result.output)
        mock_generator_class.assert_called_once()
        mock_get_files.assert_called_once()
        self.assertEqual(mock_generator.process_file.call_count, 2)
    
    def test_cli_with_options(self):
        """Test CLI with command line options."""
        with patch('pydocgen.cli.DocstringGenerator') as mock_generator_class:
            mock_generator = mock_generator_class.return_value
            mock_generator.process_file.return_value = True
            
            # Create a temporary Python file
            test_file = self.temp_path / "test_file.py"
            with open(test_file, "w") as f:
                f.write("def test_function():\n    pass\n")
            
            result = self.runner.invoke(main, [
                '--style', 'numpy',
                '--include-private',
                '--exclude', 'tests/*',
                str(test_file)
            ])
            
            self.assertEqual(result.exit_code, 0)
            mock_generator_class.assert_called_once()
            
            # Check that the Config object was created with the right parameters
            config = mock_generator_class.call_args[0][0]
            self.assertEqual(config.style, "numpy")
            self.assertEqual(config.exclude, ["tests/*"])
            self.assertTrue(config.include_private)


if __name__ == "__main__":
    unittest.main()