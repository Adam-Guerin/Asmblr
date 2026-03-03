#!/usr/bin/env python3
"""
Calculate Technical Debt Score from Analysis Results
Aggregates technical debt metrics into a single score
"""

import json
import sys
from pathlib import Path
from typing import Dict

def load_json_file(filepath: str) -> Dict:
    """Load JSON file safely"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def calculate_debt_score(debt_report: Dict) -> float:
    """Calculate technical debt score from report"""
    if not debt_report:
        return 75.0  # Default score
    
    # Extract debt metrics
    total_issues = debt_report.get('total_issues', 0)
    high_priority_issues = debt_report.get('high_priority', 0)
    medium_priority_issues = debt_report.get('medium_priority', 0)
    low_priority_issues = debt_report.get('low_priority', 0)
    code_duplication = debt_report.get('code_duplication_percent', 0)
    test_coverage = debt_report.get('test_coverage_percent', 80)
    
    # Calculate base score
    base_score = 100.0
    
    # Deduct points for issues (weighted by priority)
    base_score -= (high_priority_issues * 10)  # High priority: -10 points each
    base_score -= (medium_priority_issues * 5)   # Medium priority: -5 points each
    base_score -= (low_priority_issues * 2)     # Low priority: -2 points each
    
    # Deduct points for code duplication
    base_score -= (code_duplication * 0.5)  # 0.5 points per percent
    
    # Bonus points for good test coverage
    if test_coverage > 80:
        base_score += 10  # Bonus for >80% coverage
    elif test_coverage > 60:
        base_score += 5   # Small bonus for >60% coverage
    
    # Ensure score is within bounds
    final_score = max(0, min(100, base_score))
    
    return final_score

def main():
    if len(sys.argv) < 2:
        print("Usage: python calculate_debt_score.py <debt_report.json>")
        return 1
    
    debt_file = sys.argv[1]
    
    # Load debt report
    debt_report = load_json_file(debt_file)
    
    # Calculate score
    score = calculate_debt_score(debt_report)
    
    # Round to nearest integer
    final_score = round(score)
    
    print(final_score)
    
    # Generate detailed report
    report = {
        "debt_score": final_score,
        "input_file": debt_file,
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    with open("debt_score_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
