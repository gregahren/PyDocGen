"""Tests for the configuration module."""

import os
import tempfile
import unittest
from pathlib import Path

from pydocgen.config import Config


class TestConfig(unittest.TestCase):
    """Test cases for the Config class."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = Config()
        self.assertEqual(config.style, "google")
        self.assertEqual(config.exclude, [])
        self.assertFalse(config.include_private)
    
    def test_custom_values(self):
        """Test that custom values are set correctly."""
        config = Config(
            style="numpy",
            exclude=["tests/*", "setup.py"],
            include_private=True,
        )
        self.assertEqual(config.style, "numpy")
        self.assertEqual(config.exclude, ["tests/*", "setup.py"])
        self.assertTrue(config.include_private)
    
    def test_post_init(self):
        """Test that __post_init__ initializes default values correctly."""
        # Test with exclude=None
        config = Config(exclude=None)
        self.assertEqual(config.exclude, [])
        
        # Test with exclude already set
        config = Config(exclude=["tests/*"])
        self.assertEqual(config.exclude, ["tests/*"])


if __name__ == "__main__":
    unittest.main()