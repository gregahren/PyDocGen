"""Docstring generator for PyDocGen."""
from pathlib import Path
import os
import ast
import re

from jinja2 import Environment, FileSystemLoader, select_autoescape

from pydocgen.config import Config


# Template content definitions
GOOGLE_TEMPLATE = """{{ summary }}{% if description or args or returns or raises %}{% if description %}


{{ description }}{% endif %}{% if args %}


Args:
{% for arg in args %}    {{ arg.name }} ({{ arg.type }}{% if arg.default %}, optional{% endif %}): {{ arg.description }}{% if arg.default %} Defaults to {{ arg.default }}.{% endif %}
{% endfor %}{% endif %}{% if returns %}


Returns:
    {{ returns.type }}: {{ returns.description }}
{% endif %}{% if raises %}


Raises:
{% for exception in raises %}    {{ exception.type }}: {{ exception.description }}
{% endfor %}{% endif %}{% endif %}"""

NUMPY_TEMPLATE = """{{ summary }}

{% if description %}{{ description }}

{% endif %}{% if args %}Parameters
----------
{% for arg in args %}{{ arg.name }} : {{ arg.type }}
    {{ arg.description }}{% if arg.default %} Default is {{ arg.default }}.{% endif %}
{% endfor %}
{% endif %}{% if returns %}Returns
-------
{{ returns.type }}
    {{ returns.description }}
{% endif %}{% if raises %}Raises
------
{% for exception in raises %}{{ exception.type }}
    {{ exception.description }}
{% endfor %}{% endif %}"""

RST_TEMPLATE = """{{ summary }}

{% if description %}{{ description }}

{% endif %}{% if args %}{% for arg in args %}:param {{ arg.name }}: {{ arg.description }}
:type {{ arg.name }}: {{ arg.type }}{% if arg.default %}, optional{% endif %}
{% endfor %}
{% endif %}{% if returns %}:return: {{ returns.description }}
:rtype: {{ returns.type }}
{% endif %}{% if raises %}{% for exception in raises %}:raises {{ exception.type }}: {{ exception.description }}
{% endfor %}{% endif %}"""

INIT_TEMPLATE = """\"\"\"Templates package for PyDoGen.\"\"\""""

# Template mapping
TEMPLATES = {
    "google.jinja2": GOOGLE_TEMPLATE,
    "numpy.jinja2": NUMPY_TEMPLATE,
    "rst.jinja2": RST_TEMPLATE,
    "__init__.py": INIT_TEMPLATE
}


class DocstringGenerator:
    """Generator for Python docstrings based on code analysis."""

    def __init__(self, config: Config):
        """Initialize the docstring generator.
        
        Args:
            config (Config): Configuration for the docstring generator.
        """
        self.config = config
        self.template_dir = Path(__file__).parent / "templates"
        self._ensure_templates_exist()
        self.template_env = self._setup_templates()
        self._compile_exclude_patterns()
        
    def _ensure_templates_exist(self):
        """Ensure that template directory and files exist.
        
        Creates the template directory and files if they don't exist.
        This ensures the templates are available in production environments.
        """
        # Create template directory if it doesn't exist
        os.makedirs(self.template_dir, exist_ok=True)
        
        # Create template files if they don't exist
        for filename, content in TEMPLATES.items():
            file_path = self.template_dir / filename
            if not file_path.exists():
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
    
    def _setup_templates(self) -> Environment:
        """Set up Jinja2 templates for docstring generation.
        
        Returns:
            Environment: Configured Jinja2 environment.
        """
        env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        return env
    
    def _compile_exclude_patterns(self):
        """Compile exclude patterns for file matching.
        
        Converts the exclude patterns from the config into a format that can be
        used for efficient file path matching.
        
        Raises:
            ValueError: If an exclude pattern is invalid.
        """
        import fnmatch
        import re
        
        self.exclude_patterns = []
        
        if not self.config.exclude:
            return
            
        for pattern in self.config.exclude:
            if not pattern or not isinstance(pattern, str):
                print(f"Warning: Ignoring invalid exclude pattern: {pattern}")
                continue
                
            try:
                # Convert glob pattern to regex pattern
                regex_pattern = fnmatch.translate(pattern)
                # Compile the regex for faster matching
                compiled_pattern = re.compile(regex_pattern)
                self.exclude_patterns.append(compiled_pattern)
            except Exception as e:
                print(f"Warning: Failed to compile exclude pattern '{pattern}': {e}")
    
    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if a file should be excluded from processing.
        
        Args:
            file_path (Path): Path to the file to check.
            
        Returns:
            bool: True if the file should be excluded, False otherwise.
            
        Raises:
            ValueError: If the file path is invalid.
        """
        if file_path is None:
            raise ValueError("File path cannot be None")
            
        # Convert to string for pattern matching
        try:
            file_path_str = str(file_path)
        except Exception as e:
            raise ValueError(f"Invalid file path: {e}")
        
        # Check against each exclude pattern
        for pattern in self.exclude_patterns:
            try:
                if pattern.match(file_path_str):
                    return True
            except Exception as e:
                # Log the error but continue with other patterns
                print(f"Error matching pattern {pattern.pattern}: {e}")
                
        return False
    
    def process_file(self, file_path: Path) -> bool:
        """Process a Python file to add missing docstrings.
        
        Args:
            file_path (Path): Path to the Python file.
            
        Returns:
            bool: True if the file was modified, False otherwise.
        """
        # Skip excluded files
        if self.should_exclude_file(file_path):
            return False
            
        try:
            # Read the file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Parse the file with ast to identify nodes
            tree = ast.parse(content)
            
            # Add parent references to all nodes
            self._add_parent_references(tree)
            
            # Collect nodes that need docstrings
            docstring_insertions = []
            
            # Check if module needs a docstring
            module_docstring = None
            if not ast.get_docstring(tree) and self._should_add_docstring(tree):
                module_docstring = self._generate_module_docstring(tree, str(file_path))
                docstring_insertions.append({
                    'node': tree,
                    'docstring': module_docstring,
                    'type': 'module'
                })
            
            # Process classes and functions
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and self._should_add_docstring(node):
                    if not ast.get_docstring(node):
                        # Determine if this is a method (function inside a class)
                        is_method = False
                        class_name = None
                        
                        if isinstance(node, ast.FunctionDef) and hasattr(node, 'parent'):
                            is_method = isinstance(node.parent, ast.ClassDef)
                            if is_method and hasattr(node.parent, 'name'):
                                class_name = node.parent.name
                        
                        docstring = self._generate_docstring(node, is_method=is_method, class_name=class_name)
                        docstring_insertions.append({
                            'node': node,
                            'docstring': docstring,
                            'type': 'class' if isinstance(node, ast.ClassDef) else 'function'
                        })
            
            # If no docstrings need to be added, return False
            if not docstring_insertions:
                return False
                
            # Insert docstrings while preserving original formatting
            modified_content = self._insert_docstrings(content, docstring_insertions)
            
            # Write changes back to file if modified
            if modified_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(modified_content)
                return True
                
            return False
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            return False
            
    def _insert_docstrings(self, content, insertions):
        """Insert docstrings into the content while preserving formatting.
        
        Args:
            content (str): Original file content
            insertions (list): List of docstring insertion points
            
        Returns:
            str: Modified content with docstrings inserted
        """
        # Sort insertions by line number in reverse order to avoid offset issues
        # Module nodes don't have lineno, so use 0 for them
        def get_lineno(insertion):
            """Get lineno.

            Args:
                insertion (Any): The insertion.
            """
            node = insertion['node']
            if isinstance(node, ast.Module):
                return 0
            return node.lineno
            
        insertions.sort(key=get_lineno, reverse=True)
        
        # Convert content to lines for easier manipulation
        lines = content.splitlines(True)  # Keep line endings
        
        for insertion in insertions:
            node = insertion['node']
            docstring = insertion['docstring']
            node_type = insertion['type']
            
            # Determine insertion point and indentation
            if node_type == 'module':
                # For module docstrings, insert at the beginning of the file
                # after any comments, imports, or empty lines
                insert_line = 0
                indent = ''
            else:
                # For class and function docstrings, insert after the definition line
                insert_line = node.lineno
                
                # Find the actual line where the body starts (after the colon)
                while insert_line < len(lines) and ':' not in lines[insert_line-1]:
                    insert_line += 1
                
                # Determine indentation from the next line or the definition line
                if insert_line < len(lines):
                    # Get indentation of the body
                    body_indent_match = re.match(r'^(\s*)', lines[insert_line])
                    if body_indent_match:
                        indent = body_indent_match.group(1)
                    else:
                        # Fallback to definition line indentation + 4 spaces
                        def_indent_match = re.match(r'^(\s*)', lines[node.lineno-1])
                        indent = def_indent_match.group(1) + '    ' if def_indent_match else '    '
                else:
                    # Fallback if we're at the end of the file
                    def_indent_match = re.match(r'^(\s*)', lines[node.lineno-1])
                    indent = def_indent_match.group(1) + '    ' if def_indent_match else '    '
            
            # Format the docstring with proper indentation
            docstring_lines = docstring.splitlines()
            if len(docstring_lines) == 1:
                # Single line docstring
                formatted_docstring = f'{indent}"""{docstring}"""\n'
            else:
                # Multi-line docstring
                formatted_docstring = f'{indent}"""{docstring_lines[0]}\n'
                for line in docstring_lines[1:]:
                    if line.strip():
                        formatted_docstring += f'{indent}{line}\n'
                    else:
                        formatted_docstring += '\n'
                formatted_docstring += f'{indent}"""\n'
            
            # Insert the formatted docstring
            lines.insert(insert_line, formatted_docstring)
        
        return ''.join(lines)
    
    def _should_add_docstring(self, node) -> bool:
        """Determine if a docstring should be added to the node.
        
        Args:
            node: The AST node to check.
            
        Returns:
            bool: True if a docstring should be added, False otherwise.
        """
        # Skip private methods if not configured to include them
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_") and not self.config.include_private:
            return False
            
        return True
    
    def _generate_module_docstring(self, module, file_path) -> str:
        """Generate a docstring for a module.
        
        Args:
            module: The module AST node.
            file_path: The path to the module file.
            
        Returns:
            str: The generated docstring.
        """
        # Extract module name from the file path
        module_name = Path(file_path).stem
        
        # Generate a summary based on the module name
        summary = f"{module_name.replace('_', ' ').title()} module."
        
        # Generate a description based on the module contents
        description = "This module provides functionality for "
        
        # Look at the classes and functions in the module
        classes = [n for n in module.body if isinstance(n, ast.ClassDef)]
        functions = [n for n in module.body if isinstance(n, ast.FunctionDef)]
        
        if classes:
            description += f"working with {', '.join([c.name for c in classes[:3]])}."
        elif functions:
            description += f"performing operations like {', '.join([f.name.replace('_', ' ') for f in functions[:3]])}."
        else:
            description += "various operations."
        
        # Render the template
        template = self.template_env.get_template(f"{self.config.style}.jinja2")
        docstring = template.render(
            summary=summary,
            description=description,
        )
        
        return docstring
    
    def _generate_docstring(self, node, is_method=False, class_name=None) -> str:
        """Generate a docstring for a function or class.
        
        Args:
            node: The AST node to generate a docstring for.
            is_method (bool, optional): Whether the node is a method. Defaults to False.
            class_name (str, optional): The name of the class if the node is a method. Defaults to None.
            
        Returns:
            str: The generated docstring.
        """
        if isinstance(node, ast.ClassDef):
            return self._generate_class_docstring(node)
        elif isinstance(node, ast.FunctionDef):
            return self._generate_function_docstring(node, is_method, class_name)
        return ""
    
    def _generate_class_docstring(self, node) -> str:
        """Generate a docstring for a class.
        
        Args:
            node: The class AST node.
            
        Returns:
            str: The generated docstring.
        """
        # Generate a summary based on the class name
        summary = f"{node.name} class for {node.name.lower().replace('_', ' ')}."
        
        # Generate a description based on the class contents
        description = ""
        if node.bases:
            base_names = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    base_names.append(base.id)
                elif isinstance(base, ast.Attribute):
                    base_names.append(f"{base.value.id}.{base.attr}")
                else:
                    base_names.append("BaseClass")
            
            description = f"This class inherits from {', '.join(base_names)}."
        
        # Render the template
        template = self.template_env.get_template(f"{self.config.style}.jinja2")
        docstring = template.render(
            summary=summary,
            description=description,
        )
        
        return docstring
    
    def _generate_function_docstring(self, node, is_method=False, class_name=None) -> str:
        """Generate a docstring for a function or method.
        
        Args:
            node: The function AST node.
            is_method (bool, optional): Whether the node is a method. Defaults to False.
            class_name (str, optional): The name of the class if the node is a method. Defaults to None.
            
        Returns:
            str: The generated docstring.
        """
        # Generate a summary based on the function name
        func_name = node.name.replace("_", " ")
        if is_method and class_name:
            summary = f"{func_name.capitalize()} for {class_name}."
        else:
            summary = f"{func_name.capitalize()}."
        
        # Extract arguments
        args = []
        for i, arg in enumerate(node.args.args):
            if arg.arg == "self" and is_method:
                continue
                
            arg_type = "Any"
            # Check for type annotations
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    arg_type = arg.annotation.id
                elif isinstance(arg.annotation, ast.Attribute):
                    arg_type = f"{arg.annotation.value.id}.{arg.annotation.attr}"
                elif isinstance(arg.annotation, ast.Subscript):
                    if isinstance(arg.annotation.value, ast.Name):
                        arg_type = f"{arg.annotation.value.id}[...]"
                    else:
                        arg_type = "complex_type"
            
            # Try to infer default value
            default = None
            defaults_offset = len(node.args.args) - len(node.args.defaults)
            if i >= defaults_offset and node.args.defaults:
                default_node = node.args.defaults[i - defaults_offset]
                if isinstance(default_node, ast.Constant):
                    default = repr(default_node.value)
                elif isinstance(default_node, ast.Name):
                    default = default_node.id
                else:
                    default = "default_value"
            
            # Generate description based on argument name and function context
            description = f"The {arg.arg.replace('_', ' ')}."
            
            args.append({
                "name": arg.arg,
                "type": arg_type,
                "description": description,
                "default": default,
            })
        
        # Extract return type and description
        returns = None
        if node.returns:
            return_type = "Any"
            if isinstance(node.returns, ast.Name):
                return_type = node.returns.id
            elif isinstance(node.returns, ast.Attribute):
                return_type = f"{node.returns.value.id}.{node.returns.attr}"
            elif isinstance(node.returns, ast.Subscript):
                if isinstance(node.returns.value, ast.Name):
                    return_type = f"{node.returns.value.id}[...]"
                else:
                    return_type = "complex_type"
            
            # Generate return description based on function name and return type
            return_description = f"The {'result' if not func_name.startswith('get') else func_name[4:]}."
            
            returns = {
                "type": return_type,
                "description": return_description,
            }
        
        # Extract potential exceptions
        raises = []
        for raise_node in self._recursive_nodes_of_type(node, ast.Raise):
            exception_type = "Exception"
            if isinstance(raise_node.exc, ast.Name):
                exception_type = raise_node.exc.id
            elif isinstance(raise_node.exc, ast.Call) and isinstance(raise_node.exc.func, ast.Name):
                exception_type = raise_node.exc.func.id
            
            # Generate exception description
            description = f"If an error occurs during {func_name}."
            
            raises.append({
                "type": exception_type,
                "description": description,
            })
        
        # Render the template
        template = self.template_env.get_template(f"{self.config.style}.jinja2")
        docstring = template.render(
            summary=summary,
            args=args,
            returns=returns,
            raises=raises,
        )
        
        return docstring
    
    def _add_parent_references(self, node, parent=None):
        """Add parent references to all nodes in the AST.
        
        Args:
            node: The AST node to process.
            parent: The parent node, if any.
        """
        # Set parent reference
        node.parent = parent
        
        # Process all child nodes
        for child in ast.iter_child_nodes(node):
            self._add_parent_references(child, node)
    
    def _recursive_nodes_of_type(self, node, node_type):
        """Recursively find all nodes of a specific type in the AST.
        
        Args:
            node: The AST node to search.
            node_type: The type of nodes to find.
            
        Returns:
            list: List of nodes of the specified type.
        """
        if isinstance(node, node_type):
            return [node]
        
        nodes = []
        for child_node in ast.iter_child_nodes(node):
            nodes.extend(self._recursive_nodes_of_type(child_node, node_type))
            
        return nodes
