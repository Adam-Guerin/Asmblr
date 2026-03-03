#!/usr/bin/env python3
"""
Technical Debt Analyzer
Analyzes technical debt for CI/CD pipeline
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any

class TechnicalDebtAnalyzer:
    """Analyzes technical debt in the codebase"""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        
    def analyze_debt(self) -> Dict[str, Any]:
        """Analyze all technical debt"""
        print("Analyzing technical debt...")
        
        debt_items = []
        
        # Find TODO/FIXME/BUG/HACK items
        debt_items.extend(self._find_todo_items())
        
        # Find code smells
        debt_items.extend(self._find_code_smells())
        
        # Find complexity issues
        debt_items.extend(self._find_complexity_issues())
        
        # Find security issues
        debt_items.extend(self._find_security_issues())
        
        # Calculate severity
        severity = self._calculate_severity(debt_items)
        
        return {
            "total_debt_items": len(debt_items),
            "severity": severity,
            "items": debt_items,
            "categories": self._categorize_items(debt_items)
        }
    
    def _find_todo_items(self) -> List[Dict[str, Any]]:
        """Find TODO/FIXME/BUG/HACK items"""
        items = []
        patterns = [
            (r'#\s*TODO\s*:?\s*(.+)', 'TODO', 'medium'),
            (r'#\s*FIXME\s*:?\s*(.+)', 'FIXME', 'high'),
            (r'#\s*BUG\s*:?\s*(.+)', 'BUG', 'critical'),
            (r'#\s*HACK\s*:?\s*(.+)', 'HACK', 'medium'),
        ]
        
        python_files = list(self.root_path.rglob("*.py"))
        python_files = [f for f in python_files if "trash" not in str(f) and "__pycache__" not in str(f)]
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines, 1):
                    for pattern, item_type, default_severity in patterns:
                        match = re.search(pattern, line.strip())
                        if match:
                            description = match.group(1) if match.groups() else ""
                            
                            # Determine severity
                            severity = default_severity
                            if "security" in description.lower() or "urgent" in description.lower():
                                severity = "critical"
                            elif "performance" in description.lower():
                                severity = "high"
                            
                            items.append({
                                "type": item_type,
                                "file": str(file_path.relative_to(self.root_path)),
                                "line": i,
                                "description": description,
                                "severity": severity,
                                "code_snippet": line.strip()
                            })
            except Exception:
                continue
        
        return items
    
    def _find_code_smells(self) -> List[Dict[str, Any]]:
        """Find code smells"""
        items = []
        patterns = [
            (r'except\s*:', 'Bare except', 'high'),
            (r'print\s*\(', 'Print statement', 'medium'),
            (r'eval\s*\(', 'Use of eval', 'critical'),
            (r'exec\s*\(', 'Use of exec', 'critical'),
            (r'import\s+\*', 'Wildcard import', 'medium'),
            (r'len\([^)]+\)\s*==\s*0', 'Unnecessary len check', 'low'),
            (r'len\([^)]+\)\s*>\s*0', 'Unnecessary len check', 'low'),
        ]
        
        python_files = list(self.root_path.rglob("*.py"))
        python_files = [f for f in python_files if "trash" not in str(f) and "__pycache__" not in str(f)]
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines, 1):
                    for pattern, description, severity in patterns:
                        if re.search(pattern, line):
                            items.append({
                                "type": "Code Smell",
                                "file": str(file_path.relative_to(self.root_path)),
                                "line": i,
                                "description": description,
                                "severity": severity,
                                "code_snippet": line.strip()
                            })
            except Exception:
                continue
        
        return items
    
    def _find_complexity_issues(self) -> List[Dict[str, Any]]:
        """Find complexity issues"""
        items = []
        
        # Find large files
        python_files = list(self.root_path.rglob("*.py"))
        python_files = [f for f in python_files if "trash" not in str(f) and "__pycache__" not in str(f)]
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    line_count = len(lines)
                
                # Check for large files
                if line_count > 1000:
                    severity = "critical" if line_count > 5000 else "high"
                    items.append({
                        "type": "Complexity",
                        "file": str(file_path.relative_to(self.root_path)),
                        "line": 1,
                        "description": f"Large file ({line_count} lines)",
                        "severity": severity,
                        "code_snippet": f"File has {line_count} lines"
                    })
                
                # Check for long functions
                content = ''.join(lines)
                function_matches = re.finditer(r'def\s+(\w+)\s*\([^)]*\):', content)
                
                for match in function_matches:
                    func_start = match.start()
                    func_name = match.group(1)
                    
                    # Find function end (simplified)
                    func_lines = content[func_start:].split('\n')
                    func_length = 0
                    indent_level = None
                    
                    for line in func_lines[1:]:
                        if line.strip() == "":
                            continue
                        current_indent = len(line) - len(line.lstrip())
                        
                        if indent_level is None:
                            indent_level = current_indent
                        elif current_indent <= indent_level and line.strip():
                            break
                        
                        func_length += 1
                    
                    if func_length > 50:
                        severity = "critical" if func_length > 100 else "high"
                        items.append({
                            "type": "Complexity",
                            "file": str(file_path.relative_to(self.root_path)),
                            "line": content[:func_start].count('\n') + 1,
                            "description": f"Long function ({func_length} lines): {func_name}",
                            "severity": severity,
                            "code_snippet": f"def {func_name}(...): # {func_length} lines"
                        })
                
            except Exception:
                continue
        
        return items
    
    def _find_security_issues(self) -> List[Dict[str, Any]]:
        """Find security issues"""
        items = []
        patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password', 'critical'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key', 'critical'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret', 'critical'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'Hardcoded token', 'critical'),
            (r'shell=True', 'Shell injection risk', 'high'),
            (r'subprocess\.call\s*\(', 'Unsafe subprocess call', 'medium'),
            (r'pickle\.loads?\s*\(', 'Unsafe pickle usage', 'high'),
        ]
        
        python_files = list(self.root_path.rglob("*.py"))
        python_files = [f for f in python_files if "trash" not in str(f) and "__pycache__" not in str(f)]
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines, 1):
                    for pattern, description, severity in patterns:
                        if re.search(pattern, line):
                            items.append({
                                "type": "Security",
                                "file": str(file_path.relative_to(self.root_path)),
                                "line": i,
                                "description": description,
                                "severity": severity,
                                "code_snippet": line.strip()
                            })
            except Exception:
                continue
        
        return items
    
    def _calculate_severity(self, items: List[Dict[str, Any]]) -> str:
        """Calculate overall severity"""
        critical_count = len([i for i in items if i['severity'] == 'critical'])
        high_count = len([i for i in items if i['severity'] == 'high'])
        total_count = len(items)
        
        if critical_count > 5 or total_count > 100:
            return "critical"
        elif high_count > 20 or total_count > 50:
            return "high"
        elif total_count > 20:
            return "medium"
        else:
            return "low"
    
    def _categorize_items(self, items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize items by type"""
        categories = {}
        for item in items:
            category = item['type']
            categories[category] = categories.get(category, 0) + 1
        return categories

def main():
    """Main analyzer"""
    import sys
    from pathlib import Path
    
    if len(sys.argv) < 3:
        print("Usage: python technical_debt_analyzer.py --output <file>")
        sys.exit(1)
    
    root_path = Path(__file__).parent.parent
    analyzer = TechnicalDebtAnalyzer(root_path)
    
    # Analyze debt
    results = analyzer.analyze_debt()
    
    # Save results
    output_file = sys.argv[2]
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Technical debt analysis saved to {output_file}")
    print(f"Total items: {results['total_debt_items']}")
    print(f"Severity: {results['severity']}")

if __name__ == "__main__":
    main()
