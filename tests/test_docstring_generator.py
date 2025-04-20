import os
import tempfile
import unittest
from pathlib import Path

from pydocgen.config import Config
from pydocgen.docstring_generator import DocstringGenerator


class TestDocstringGenerator(unittest.TestCase):
    def setUp(self):
        self.config = Config(
            style="google",
            exclude=[],
            include_private=False,
        )
        self.generator = DocstringGenerator(self.config)
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        
    def tearDown(self):
        self.temp_dir.cleanup()
        
    def test_process_file_with_missing_docstrings(self):
        # Create a test file with missing docstrings
        test_file_content = """
def add(a, b):
    return a + b

class TestClass:
    def __init__(self, name):
        self.name = name
        
    def get_name(self):
        return self.name
"""
        test_file_path = Path(self.temp_dir.name) / "test_file.py"
        with open(test_file_path, "w") as f:
            f.write(test_file_content)
            
        # Process the file
        result = self.generator.process_file(test_file_path)
        
        # Check that the file was modified
        self.assertTrue(result)
        
        # Read the modified file
        with open(test_file_path, "r") as f:
            modified_content = f.read()
            
        # Check that docstrings were added
        self.assertIn('"""Add.', modified_content)
        self.assertIn('"""TestClass class', modified_content)
        self.assertIn('"""Get name.', modified_content)
        
    def test_process_file_with_existing_docstrings(self):
        # Create a test file with existing docstrings
        test_file_content = '''
def add(a, b):
    """Add two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        The sum of a and b
    """
    return a + b

class TestClass:
    """A test class."""
    
    def __init__(self, name):
        """Initialize the test class.
        
        Args:
            name: The name
        """
        self.name = name
        
    def get_name(self):
        """Get the name.
        
        Returns:
            The name
        """
        return self.name
'''
        test_file_path = Path(self.temp_dir.name) / "test_file_with_docstrings.py"
        with open(test_file_path, "w") as f:
            f.write(test_file_content)
            
        # Process the file
        result = self.generator.process_file(test_file_path)
        
        # Check that the file was not modified
        self.assertFalse(result)
        
        # Read the file
        with open(test_file_path, "r") as f:
            content = f.read()
            
        # Check that the content is unchanged
        self.assertEqual(content, test_file_content)
        
    def test_different_docstring_styles(self, a:str, b:int, c:list[int]):
        # Create a test file
        test_file_content = """
def add(a: int, b: int) -> int:
    return a + b
"""
        test_file_path = Path(self.temp_dir.name) / "test_styles.py"
        with open(test_file_path, "w") as f:
            f.write(test_file_content)
            
        # Test Google style
        self.config.style = "google"
        self.generator = DocstringGenerator(self.config)
        self.generator.process_file(test_file_path)
        
        with open(test_file_path, "r") as f:
            google_content = f.read()
            
        self.assertIn("Args:", google_content)
        
        # Reset the file
        with open(test_file_path, "w") as f:
            f.write(test_file_content)
            
        # Test NumPy style
        self.config.style = "numpy"
        self.generator = DocstringGenerator(self.config)
        self.generator.process_file(test_file_path)
        
        with open(test_file_path, "r") as f:
            numpy_content = f.read()
            
        self.assertIn("Parameters", numpy_content)
        
        # Reset the file
        with open(test_file_path, "w") as f:
            f.write(test_file_content)
            
        # Test RST style
        self.config.style = "rst"
        self.generator = DocstringGenerator(self.config)
        self.generator.process_file(test_file_path)
        
        with open(test_file_path, "r") as f:
            rst_content = f.read()
            
        self.assertIn(":param", rst_content)


if __name__ == "__main__":
    unittest.main()