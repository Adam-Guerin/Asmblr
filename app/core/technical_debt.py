"""
Technical debt tracker and refactoring utilities for Asmblr
Automated TODO/FIXME resolution and large file management
"""

import ast
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from loguru import logger


@dataclass
class TechnicalDebtItem:
    """Represents a technical debt item"""
    file_path: str
    line_number: int
    debt_type: str  # TODO, FIXME, BUG, HACK, XXX
    description: str
    severity: str  # low, medium, high, critical
    estimated_effort: str  # hours, days, weeks
    assignee: Optional[str] = None
    created_at: datetime = None
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None


@dataclass
class FileMetrics:
    """Metrics for file analysis"""
    file_path: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    complexity_score: float
    technical_debt_count: int
    maintainability_index: float


class TechnicalDebtManager:
    """Manages and resolves technical debt"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.debt_items: List[TechnicalDebtItem] = []
        self.file_metrics: Dict[str, FileMetrics] = {}
        
        # Patterns for detecting technical debt
        self.debt_patterns = {
            'TODO': re.compile(r'#\s*TODO\s*:?\s*(.+)'),
            'FIXME': re.compile(r'#\s*FIXME\s*:?\s*(.+)'),
            'BUG': re.compile(r'#\s*BUG\s*:?\s*(.+)'),
            'HACK': re.compile(r'#\s*HACK\s*:?\s*(.+)'),
            'XXX': re.compile(r'#\s*XXX\s*:?\s*(.+)'),
        }
        
        # Severity classification based on keywords
        self.severity_keywords = {
            'critical': ['critical', 'security', 'urgent', 'blocker', 'production'],
            'high': ['important', 'priority', 'major', 'breaking', 'performance'],
            'medium': ['refactor', 'improve', 'optimize', 'cleanup'],
            'low': ['minor', 'nice-to-have', 'suggestion', 'consider']
        }
    
    def scan_repository(self) -> Dict[str, Any]:
        """Scan entire repository for technical debt"""
        logger.info("Starting technical debt scan...")
        
        python_files = list(self.base_dir.rglob("*.py"))
        
        for file_path in python_files:
            try:
                self._analyze_file(file_path)
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
        
        return self._generate_report()
    
    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single file for technical debt and metrics"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            logger.error(f"Could not read file {file_path}: {e}")
            return
        
        # Calculate basic metrics
        total_lines = len(lines)
        code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        blank_lines = sum(1 for line in lines if not line.strip())
        
        # Calculate complexity (simplified)
        complexity_score = self._calculate_complexity(content)
        
        # Find technical debt items
        debt_items = []
        for line_num, line in enumerate(lines, 1):
            for debt_type, pattern in self.debt_patterns.items():
                match = pattern.search(line)
                if match:
                    description = match.group(1).strip()
                    severity = self._classify_severity(description)
                    effort = self._estimate_effort(description)
                    
                    debt_item = TechnicalDebtItem(
                        file_path=str(file_path),
                        line_number=line_num,
                        debt_type=debt_type,
                        description=description,
                        severity=severity,
                        estimated_effort=effort,
                        created_at=datetime.now()
                    )
                    debt_items.append(debt_item)
        
        # Calculate maintainability index (simplified)
        maintainability_index = self._calculate_maintainability_index(
            total_lines, code_lines, comment_lines, complexity_score, len(debt_items)
        )
        
        # Store metrics
        metrics = FileMetrics(
            file_path=str(file_path),
            total_lines=total_lines,
            code_lines=code_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            complexity_score=complexity_score,
            technical_debt_count=len(debt_items),
            maintainability_index=maintainability_index
        )
        
        self.file_metrics[str(file_path)] = metrics
        self.debt_items.extend(debt_items)
    
    def _calculate_complexity(self, content: str) -> float:
        """Calculate cyclomatic complexity (simplified)"""
        try:
            tree = ast.parse(content)
            complexity = 1  # Base complexity
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                    complexity += 1
                elif isinstance(node, (ast.ExceptHandler, ast.With, ast.AsyncWith)):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
                elif isinstance(node, ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp):
                    complexity += 1
            
            return float(complexity)
        except:
            # Fallback for files that can't be parsed
            return float(content.count('if') + content.count('while') + content.count('for') + 1)
    
    def _classify_severity(self, description: str) -> str:
        """Classify severity based on description keywords"""
        description_lower = description.lower()
        
        for severity, keywords in self.severity_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return severity
        
        return 'medium'  # Default severity
    
    def _estimate_effort(self, description: str) -> str:
        """Estimate effort based on description"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['quick', 'simple', 'easy', 'minor']):
            return 'hours'
        elif any(word in description_lower for word in ['refactor', 'rewrite', 'major']):
            return 'weeks'
        elif any(word in description_lower for word in ['complex', 'difficult', 'hard']):
            return 'days'
        else:
            return 'hours'
    
    def _calculate_maintainability_index(self, total_lines: int, code_lines: int, 
                                       comment_lines: int, complexity: float, debt_count: int) -> float:
        """Calculate maintainability index (simplified)"""
        if total_lines == 0:
            return 100.0
        
        # Simplified maintainability index
        comment_ratio = comment_lines / total_lines
        complexity_penalty = min(complexity / 10, 1.0)
        debt_penalty = min(debt_count / 20, 1.0)
        
        maintainability = (comment_ratio * 40) + (40 - complexity_penalty * 20) + (20 - debt_penalty * 20)
        return max(0, min(100, maintainability))
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive technical debt report"""
        # Aggregate statistics
        total_debt = len(self.debt_items)
        debt_by_type = {}
        debt_by_severity = {}
        debt_by_file = {}
        
        for item in self.debt_items:
            # By type
            debt_by_type[item.debt_type] = debt_by_type.get(item.debt_type, 0) + 1
            
            # By severity
            debt_by_severity[item.severity] = debt_by_severity.get(item.severity, 0) + 1
            
            # By file
            file_path = item.file_path
            debt_by_file[file_path] = debt_by_file.get(file_path, 0) + 1
        
        # File statistics
        files_analyzed = len(self.file_metrics)
        avg_complexity = sum(m.complexity_score for m in self.file_metrics.values()) / files_analyzed if files_analyzed > 0 else 0
        avg_maintainability = sum(m.maintainability_index for m in self.file_metrics.values()) / files_analyzed if files_analyzed > 0 else 0
        
        # Large files (over 500 lines)
        large_files = [m for m in self.file_metrics.values() if m.total_lines > 500]
        
        # High complexity files
        high_complexity_files = [m for m in self.file_metrics.values() if m.complexity_score > 20]
        
        # Low maintainability files
        low_maintainability_files = [m for m in self.file_metrics.values() if m.maintainability_index < 50]
        
        return {
            'summary': {
                'total_debt_items': total_debt,
                'files_analyzed': files_analyzed,
                'avg_complexity': round(avg_complexity, 2),
                'avg_maintainability': round(avg_maintainability, 2),
                'large_files_count': len(large_files),
                'high_complexity_files_count': len(high_complexity_files),
                'low_maintainability_files_count': len(low_maintainability_files)
            },
            'debt_by_type': debt_by_type,
            'debt_by_severity': debt_by_severity,
            'priority_files': {
                'large_files': [{'path': m.file_path, 'lines': m.total_lines} for m in large_files[:10]],
                'high_complexity': [{'path': m.file_path, 'complexity': m.complexity_score} for m in high_complexity_files[:10]],
                'low_maintainability': [{'path': m.file_path, 'index': m.maintainability_index} for m in low_maintainability_files[:10]],
                'most_debt': [{'path': path, 'count': count} for path, count in sorted(debt_by_file.items(), key=lambda x: x[1], reverse=True)[:10]]
            },
            'detailed_items': [
                {
                    'file_path': item.file_path,
                    'line_number': item.line_number,
                    'type': item.debt_type,
                    'description': item.description,
                    'severity': item.severity,
                    'effort': item.estimated_effort
                }
                for item in sorted(self.debt_items, key=lambda x: self._severity_priority(x.severity), reverse=True)[:50]
            ]
        }
    
    def _severity_priority(self, severity: str) -> int:
        """Get numeric priority for severity"""
        priorities = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        return priorities.get(severity, 0)
    
    def suggest_refactoring_plan(self) -> Dict[str, Any]:
        """Suggest refactoring plan based on analysis"""
        report = self._generate_report()
        
        # Identify files that need immediate attention
        critical_files = []
        for file_path, metrics in self.file_metrics.items():
            if (metrics.total_lines > 1000 or 
                metrics.complexity_score > 30 or 
                metrics.maintainability_index < 30 or
                metrics.technical_debt_count > 10):
                critical_files.append({
                    'path': file_path,
                    'issues': [],
                    'recommendations': []
                })
                
                if metrics.total_lines > 1000:
                    critical_files[-1]['issues'].append(f"Very large file ({metrics.total_lines} lines)")
                    critical_files[-1]['recommendations'].append("Split into multiple modules")
                
                if metrics.complexity_score > 30:
                    critical_files[-1]['issues'].append(f"High complexity ({metrics.complexity_score})")
                    critical_files[-1]['recommendations'].append("Extract functions/classes")
                
                if metrics.maintainability_index < 30:
                    critical_files[-1]['issues'].append(f"Low maintainability ({metrics.maintainability_index:.1f})")
                    critical_files[-1]['recommendations'].append("Refactor and add documentation")
                
                if metrics.technical_debt_count > 10:
                    critical_files[-1]['issues'].append(f"High technical debt ({metrics.technical_debt_count} items)")
                    critical_files[-1]['recommendations'].append("Address TODO/FIXME items")
        
        return {
            'immediate_actions': critical_files[:5],
            'medium_term_goals': [
                "Reduce average file size to under 500 lines",
                "Improve maintainability index above 70",
                "Resolve critical and high severity debt items",
                "Implement automated code quality gates"
            ],
            'long_term_improvements': [
                "Establish coding standards and review process",
                "Implement continuous refactoring sprints",
                "Add comprehensive test coverage",
                "Document architectural decisions"
            ]
        }
    
    def export_report(self, output_path: Path) -> None:
        """Export technical debt report to JSON"""
        report = self._generate_report()
        refactoring_plan = self.suggest_refactoring_plan()
        
        full_report = {
            'generated_at': datetime.now().isoformat(),
            'analysis': report,
            'refactoring_plan': refactoring_plan
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(full_report, f, indent=2, default=str)
        
        logger.info(f"Technical debt report exported to {output_path}")


def run_technical_debt_analysis(base_dir: Path) -> Dict[str, Any]:
    """Run complete technical debt analysis"""
    manager = TechnicalDebtManager(base_dir)
    report = manager.scan_repository()
    
    # Export report
    output_path = base_dir / "technical_debt_report.json"
    manager.export_report(output_path)
    
    return report
