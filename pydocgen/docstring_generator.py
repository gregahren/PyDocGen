"""Docstring generator for PyDocGen."""
from pathlib import Path

import astroid
from jinja2 import Environment, FileSystemLoader, select_autoescape

from pydocgen.config import Config


class DocstringGenerator:
    """Generator for Python docstrings based on code analysis."""

    def __init__(self, config: Config):
        """Initialize the docstring generator.
        
        Args:
            config (Config): Configuration for the docstring generator.
        """
        self.config = config
        self.template_dir = Path("./pydocgen/templates")
        self.template_env = self._setup_templates()
        
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
    
    
    def process_file(self, file_path: Path) -> bool:
        """Process a Python file to add missing docstrings.
        
        Args:
            file_path (Path): Path to the Python file.
            
        Returns:
            bool: True if the file was modified, False otherwise.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Parse the file with astroid for better analysis
            module = astroid.parse(content, path=str(file_path))
            
            # Check if module needs a docstring
            modified = False
            
            # Add module docstring if missing
            if not module.doc_node and self._should_add_docstring(module):
                module_docstring = self._generate_module_docstring(module)
                module.doc_node = astroid.Const(module_docstring)
                modified = True
                
            # Process classes and functions
            for node in module.body:
                if isinstance(node, (astroid.ClassDef, astroid.FunctionDef)) and self._should_add_docstring(node):
                    if not node.doc_node:
                        docstring = self._generate_docstring(node)
                        node.doc_node = astroid.Const(docstring)
                        modified = True
                        
                # Process methods within classes
                if isinstance(node, astroid.ClassDef):
                    for method in node.methods():
                        if not method.doc_node and self._should_add_docstring(method):
                            docstring = self._generate_docstring(method, is_method=True, class_name=node.name)
                            method.doc_node = astroid.Const(docstring)
                            modified = True
            
            # Write changes back to file if modified
            if modified:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(module.as_string())
                    
            return modified
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            return False
    
    def _should_add_docstring(self, node) -> bool:
        """Determine if a docstring should be added to the node.
        
        Args:
            node: The AST node to check.
            
        Returns:
            bool: True if a docstring should be added, False otherwise.
        """
        # Skip private methods if not configured to include them
        if isinstance(node, astroid.FunctionDef) and node.name.startswith("_") and not self.config.include_private:
            return False
            
        return True
    
    def _generate_module_docstring(self, module) -> str:
        """Generate a docstring for a module.
        
        Args:
            module: The module AST node.
            
        Returns:
            str: The generated docstring.
        """
        # Extract module name from the file path
        module_name = Path(module.file).stem
        
        # Generate a summary based on the module name
        summary = f"{module_name.replace('_', ' ').title()} module."
        
        # Generate a description based on the module contents
        description = "This module provides functionality for "
        
        # Look at the classes and functions in the module
        classes = [n for n in module.body if isinstance(n, astroid.ClassDef)]
        functions = [n for n in module.body if isinstance(n, astroid.FunctionDef)]
        
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
            col_offset=0, # No indentation for module docstring
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
        if isinstance(node, astroid.ClassDef):
            return self._generate_class_docstring(node)
        elif isinstance(node, astroid.FunctionDef):
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
            base_names = [b.as_string() for b in node.bases]
            description = f"This class inherits from {', '.join(base_names)}."
        
        # Render the template
        template = self.template_env.get_template(f"{self.config.style}.jinja2")
        docstring = template.render(
            summary=summary,
            description=description,
            col_offset=node.col_offset + 4,  # Indent for class docstring
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
        for annotation, arg in zip(node.args.annotations, node.args.args):
            if arg.name == "self" and is_method:
                continue
                
            arg_type = "Any"
            if annotation:
                arg_type = annotation.as_string()
            
            # Try to infer default value
            default = None
            if hasattr(node.args, "defaults") and arg.name in node.args.defaults:
                default_node = node.args.defaults_dict[arg.name]
                if hasattr(default_node, "value"):
                    default = repr(default_node.value)
                else:
                    default = default_node.as_string()
            
            # Generate description based on argument name and function context
            description = f"The {arg.name.replace('_', ' ')}."
            
            args.append({
                "name": arg.name,
                "type": arg_type,
                "description": description,
                "default": default,
            })
        
        # Extract return type and description
        returns = None
        if node.returns:
            return_type = node.returns.as_string()
            
            # Generate return description based on function name and return type
            return_description = f"The {'result' if not func_name.startswith('get') else func_name[4:]}."
            
            returns = {
                "type": return_type,
                "description": return_description,
            }
        
        # Extract potential exceptions
        raises = []
        for raise_ in self._recursive_nodes_of_type(node, astroid.Raise):
            exception_type = "Exception"
            if hasattr(raise_.exc, "func"):
                exception_type = raise_.exc.func.name
            elif hasattr(raise_.exc, "as_string"):
                exception_type = raise_.exc.as_string()
            
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
            col_offset=node.col_offset + 4, # Indent for function docstring
        )
        
        return docstring
    
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
        for child in node.get_children():
            nodes.extend(self._recursive_nodes_of_type(child, node_type))
            
        return nodes
