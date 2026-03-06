#!/usr/bin/env python3
"""Script to count lines of code in core Asmblr project (excluding runs, trash, backups)"""

from pathlib import Path

def count_core_lines():
    """Count lines in core Python files only"""
    project_root = Path(".")
    total_lines = 0
    file_count = 0
    
    # Directories to exclude
    exclude_dirs = {
        'runs', 'trash', 'backups', '__pycache__', '.git', 
        'node_modules', '.pytest_cache', 'venv', 'env'
    }
    
    # Find all Python files in core directories
    for py_file in project_root.rglob("*.py"):
        # Skip excluded directories
        if any(exclude_dir in py_file.parts for exclude_dir in exclude_dirs):
            continue
            
        try:
            with open(py_file, encoding='utf-8') as f:
                lines = len(f.readlines())
                total_lines += lines
                file_count += 1
                print(f"{py_file.relative_to(project_root)}: {lines} lines")
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    print(f"\n{'='*50}")
    print(f"Core Python files: {file_count}")
    print(f"Core lines of code: {total_lines:,}")
    print(f"Average lines per file: {total_lines / file_count:.1f}")
    print(f"{'='*50}")

if __name__ == "__main__":
    count_core_lines()
