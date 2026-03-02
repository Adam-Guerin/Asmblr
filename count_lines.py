#!/usr/bin/env python3
"""Script to count lines of code in Asmblr project"""

from pathlib import Path

def count_lines():
    """Count lines in all Python files"""
    project_root = Path(".")
    total_lines = 0
    file_count = 0
    
    # Find all Python files
    for py_file in project_root.rglob("*.py"):
        try:
            with open(py_file, encoding='utf-8') as f:
                lines = len(f.readlines())
                total_lines += lines
                file_count += 1
                print(f"{py_file.relative_to(project_root)}: {lines} lines")
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    print(f"\n{'='*50}")
    print(f"Total Python files: {file_count}")
    print(f"Total lines of code: {total_lines:,}")
    print(f"Average lines per file: {total_lines / file_count:.1f}")
    print(f"{'='*50}")

if __name__ == "__main__":
    count_lines()
