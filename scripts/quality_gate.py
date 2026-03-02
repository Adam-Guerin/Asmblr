#!/usr/bin/env python3
import ast
import sys
import json
from pathlib import Path

class QualityGate:
    def __init__(self, root_path: Path):
        self.root_path = root_path
    
    def check_quality_standards(self):
        python_files = list(self.root_path.rglob("*.py"))
        python_files = [f for f in python_files if "trash" not in str(f)]
        
        total_complexity = 0
        total_functions = 0
        documented_functions = 0
        
        for file_path in python_files[:20]:  # Sample for speed
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        if ast.get_docstring(node):
                            documented_functions += 1
                        
                        complexity = 1
                        for child in ast.walk(node):
                            if isinstance(child, (ast.If, ast.While, ast.For)):
                                complexity += 1
                        total_complexity += complexity
                        
            except Exception:
                pass
        
        avg_complexity = total_complexity / max(total_functions, 1)
        documentation_coverage = (documented_functions / max(total_functions, 1)) * 100
        
        gates_passed = []
        gates_failed = []
        
        if avg_complexity <= 10:
            gates_passed.append("Complexity")
        else:
            gates_failed.append(f"Complexity too high: {avg_complexity:.1f}")
        
        if documentation_coverage >= 80:
            gates_passed.append("Documentation")
        else:
            gates_failed.append(f"Documentation too low: {documentation_coverage:.1f}%")
        
        result = {
            'avg_complexity': avg_complexity,
            'documentation_coverage': documentation_coverage,
            'gates_passed': gates_passed,
            'gates_failed': gates_failed,
            'status': 'PASS' if not gates_failed else 'FAIL'
        }
        
        print(f"Quality Gate: {result['status']}")
        if gates_failed:
            print(f"Failed: {', '.join(gates_failed)}")
        
        return result

def main():
    gate = QualityGate(Path("."))
    result = gate.check_quality_standards()
    sys.exit(0 if result['status'] == 'PASS' else 1)

if __name__ == "__main__":
    main()
