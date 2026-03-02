#!/usr/bin/env python3
import ast
import sys
from pathlib import Path

class CodeRefactorer:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.content = file_path.read_text(encoding='utf-8')
        self.lines = self.content.split('\n')
        self.tree = ast.parse(self.content)
    
    def analyze_quality(self):
        print(f"Analyzing {self.file_path}")
        
        # Check for long functions
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                start_line = node.lineno
                end_line = getattr(node, 'end_lineno', start_line)
                length = end_line - start_line + 1
                
                if length > 50:
                    print(f"Long function: {node.name} ({length} lines)")
        
        # Check for TODO comments
        todo_count = self.content.count('# TODO')
        if todo_count > 0:
            print(f"TODO comments found: {todo_count}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python refactor_tool.py <file.py>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    refactorer = CodeRefactorer(file_path)
    refactorer.analyze_quality()

if __name__ == "__main__":
    main()
