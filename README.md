# PyDocGen Hook

A pre-commit hook that automatically detects changes in Python files and intelligently adds missing docstrings to modules, classes, and methods by analyzing their code.

## Features

- Automatically detects Python files changed in a commit
- Intelligently generates contextually relevant docstrings by analyzing code
- Supports multiple docstring styles (Google, NumPy, reStructuredText)
- Configurable verbosity levels and docstring format
- Handles edge cases gracefully
- Easy integration with any Python project's Git workflow

## Installation

### Prerequisites

- Python 3.8 or higher
- Git
- [pre-commit](https://pre-commit.com/) package

### Quick Install

1. Install the pre-commit package:

```bash
pip install pre-commit
```

2. Add PyDocGen to your project's `.pre-commit-config.yaml`:

```yaml
repos:
-   repo: https://github.com/yourusername/pydocgen
    rev: v0.1.0  # Use the latest version
    hooks:
    -   id: pydocgen
        args: [--style=google]  # Optional: specify docstring style
```

3. Install the pre-commit hook:

```bash
pre-commit install
```

## Configuration

PyDocGen can be configured using command-line arguments or a configuration file.

### Command-line Arguments

- `--style`: Docstring style (google, numpy, rst). Default: google
- `--verbosity`: Level of detail in docstrings (1-3). Default: 2
- `--config`: Path to configuration file
- `--exclude`: Patterns to exclude from processing
- `--include-private`: Include private methods (prefixed with _)

### Configuration File

Create a `.pydocgen.yaml` file in your project root:

```yaml
style: google
verbosity: 2
exclude:
  - tests/*
  - setup.py
include_private: false
```

## Examples

### Google Style Docstring

```python
def calculate_total(items, tax_rate=0.1):
    """Calculate the total cost of items including tax.
    
    Args:
        items (list): A list of prices as floats.
        tax_rate (float, optional): The tax rate to apply. Defaults to 0.1.
        
    Returns:
        float: The total cost including tax.
        
    Raises:
        TypeError: If items is not a list or tax_rate is not a number.
    """
    # Function implementation
```

### NumPy Style Docstring

```python
def calculate_total(items, tax_rate=0.1):
    """Calculate the total cost of items including tax.
    
    Parameters
    ----------
    items : list
        A list of prices as floats.
    tax_rate : float, optional
        The tax rate to apply. Default is 0.1.
        
    Returns
    -------
    float
        The total cost including tax.
        
    Raises
    ------
    TypeError
        If items is not a list or tax_rate is not a number.
    """
    # Function implementation
```

### reStructuredText Style Docstring

```python
def calculate_total(items, tax_rate=0.1):
    """Calculate the total cost of items including tax.
    
    :param items: A list of prices as floats.
    :type items: list
    :param tax_rate: The tax rate to apply, defaults to 0.1
    :type tax_rate: float, optional
    
    :return: The total cost including tax.
    :rtype: float
    
    :raises TypeError: If items is not a list or tax_rate is not a number.
    """
    # Function implementation
```

## License

MIT
