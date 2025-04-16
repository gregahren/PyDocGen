"""Tests for the package's __init__.py module."""

import unittest

import pydocgen


class TestInit(unittest.TestCase):
    """Test cases for the package's __init__.py module."""

    def test_version(self):
        """Test that the version is defined."""
        self.assertIsNotNone(pydocgen.__version__)
        self.assertIsInstance(pydocgen.__version__, str)
        # Check that it follows semantic versioning format (major.minor.patch)
        parts = pydocgen.__version__.split('.')
        self.assertEqual(len(parts), 3)
        for part in parts:
            self.assertTrue(part.isdigit())


if __name__ == "__main__":
    unittest.main()