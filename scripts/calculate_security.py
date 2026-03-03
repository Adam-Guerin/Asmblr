#!/usr/bin/env python3
"""
Calculate Security Score from Security Scan Results
Aggregates bandit, safety, and trufflehog results into a single score
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

def load_json_file(filepath: str) -> Dict:
    """Load JSON file safely"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def calculate_bandit_score(bandit_results: Dict) -> float:
    """Calculate score from bandit results"""
    if not bandit_results or 'results' not in bandit_results:
        return 100.0  # Perfect score if no issues
    
    issues = bandit_results.get('results', [])
    if not issues:
        return 100.0
    
    # Weight issues by severity
    severity_weights = {
        'HIGH': 20,
        'MEDIUM': 10,
        'LOW': 5
    }
    
    total_score = 100
    for issue in issues:
        severity = issue.get('issue_severity', 'LOW')
        weight = severity_weights.get(severity, 5)
        total_score -= weight
    
    return max(0, total_score)

def calculate_safety_score(safety_results: Dict) -> float:
    """Calculate score from safety results"""
    if not safety_results or 'vulnerabilities' not in safety_results:
        return 100.0
    
    vulns = safety_results.get('vulnerabilities', [])
    if not vulns:
        return 100.0
    
    # Deduct points for each vulnerability
    total_score = 100 - (len(vulns) * 15)
    return max(0, total_score)

def calculate_secrets_score(secrets_results: Dict) -> float:
    """Calculate score from secrets detection results"""
    if not secrets_results:
        return 100.0
    
    # If secrets_results is a list (trufflehog output format)
    if isinstance(secrets_results, list):
        issues = len(secrets_results)
    else:
        issues = len(secrets_results.get('results', []))
    
    # Heavy penalty for secrets
    total_score = 100 - (issues * 25)
    return max(0, total_score)

def main():
    if len(sys.argv) < 4:
        print("Usage: python calculate_security.py <bandit.json> <safety.json> <secrets.json>")
        return 1
    
    bandit_file = sys.argv[1]
    safety_file = sys.argv[2]
    secrets_file = sys.argv[3]
    
    # Load results
    bandit_results = load_json_file(bandit_file)
    safety_results = load_json_file(safety_file)
    secrets_results = load_json_file(secrets_file)
    
    # Calculate individual scores
    bandit_score = calculate_bandit_score(bandit_results)
    safety_score = calculate_safety_score(safety_results)
    secrets_score = calculate_secrets_score(secrets_results)
    
    # Calculate weighted average
    # Give more weight to secrets and bandit
    weights = {
        'bandit': 0.4,
        'safety': 0.3,
        'secrets': 0.3
    }
    
    total_score = (
        bandit_score * weights['bandit'] +
        safety_score * weights['safety'] +
        secrets_score * weights['secrets']
    )
    
    # Round to nearest integer
    final_score = round(total_score)
    
    print(final_score)
    
    # Generate detailed report
    report = {
        "overall_score": final_score,
        "breakdown": {
            "bandit": round(bandit_score),
            "safety": round(safety_score),
            "secrets": round(secrets_score)
        },
        "weights": weights,
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    with open("security_score_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
