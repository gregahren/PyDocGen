

import os
from typing import List, Dict, Union


class ExampleClass:
    def __init__(self, name, value=None):
        self.name = name
        self.value = value or {}
        
    def process_data(self, data, transform:bool=False) -> Dict:
        result = {}
        for key, value in data.items():
            if transform:
                result[key] = self._transform_value(value)
            else:
                result[key] = value
        return result
        
    def _transform_value(self, value) -> Union[str, int, float, List]:
        if isinstance(value, str):
            return value.upper()
        elif isinstance(value, (int, float)):
            return value * 2
        elif isinstance(value, list):
            return [self._transform_value(v) for v in value]
        else:
            return value


def calculate_total(items, tax_rate=0.1):
    total = sum(items)
    return total * (1 + tax_rate)


def process_file(file_path: str, output_dir=None, overwrite=False) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir or os.path.dirname(file_path), 
                              f"processed_{os.path.basename(file_path)}")
                              
    if os.path.exists(output_path) and not overwrite:
        raise ValueError(f"Output file already exists: {output_path}")
        
    with open(file_path, 'r') as f:
        content = f.read()
        
    # Process the content
    processed_content = content.replace('\n', ' ').strip()
    
    with open(output_path, 'w') as f:
        f.write(processed_content)
        
    return output_path


def filter_data(data, criteria:str=None, sort_by=None, limit=None) -> List[Dict]:
    
    result = data.copy()
    
    if criteria:
        result = [item for item in result if all(item.get(k) == v for k, v in criteria.items())]
        
    if sort_by:
        reverse = False
        if sort_by.startswith('-'):
            sort_by = sort_by[1:]
            reverse = True
        result.sort(key=lambda x: x.get(sort_by), reverse=reverse)
        
    if limit:
        result = result[:limit]
        
    return result


if __name__ == "__main__":
    # Example usage
    example = ExampleClass("test")
    data = {
        "a": 1,
        "b": "hello",
        "c": [1, 2, 3]
    }
    result = example.process_data(data, transform=True)
    print(result)
    
    items = [10, 20, 30, 40]
    total = calculate_total(items, tax_rate=0.15)
    print(f"Total: {total}")