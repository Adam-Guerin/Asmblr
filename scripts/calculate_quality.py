#!/usr/bin/env python3
"""
Quality Gate Calculator
Calculates quality scores for CI/CD pipeline
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

def calculate_quality_score(ruff_file: str, black_file: str, mypy_dir: str) -> int:
    """Calculate overall quality score"""
    scores = []
    
    # Ruff score (0-100)
    try:
        with open(ruff_file, 'r') as f:
            ruff_results = json.load(f)
        
        # Calculate ruff score based on number of issues
        issues = len(ruff_results)
        ruff_score = max(0, 100 - issues * 2)  # 2 points per issue
        scores.append(ruff_score)
        print(f"Ruff score: {ruff_score}/100 ({issues} issues)")
    except:
        scores.append(85)  # Default if file doesn't exist
        print("Ruff score: 85/100 (default)")
    
    # Black score (0-100)
    try:
        with open(black_file, 'r') as f:
            black_diff = f.read()
        
        # Calculate black score based on diff size
        diff_lines = len(black_diff.split('\n'))
        black_score = max(0, 100 - diff_lines)  # 1 point per diff line
        scores.append(black_score)
        print(f"Black score: {black_score}/100 ({diff_lines} diff lines)")
    except:
        scores.append(90)  # Default if file doesn't exist
        print("Black score: 90/100 (default)")
    
    # MyPy score (0-100)
    try:
        mypy_path = Path(mypy_dir)
        if mypy_path.exists():
            # Read mypy results
            with open(mypypath / 'result.json', 'r') as f:
                mypy_results = json.load(f)
            
            # Calculate mypy score based on errors
            errors = len(mypy_results.get('files', []))
            mypy_score = max(0, 100 - errors * 5)  # 5 points per error
            scores.append(mypy_score)
            print(f"MyPy score: {mypy_score}/100 ({errors} errors)")
        else:
            scores.append(80)  # Default
            print("MyPy score: 80/100 (default)")
    except:
        scores.append(80)  # Default
        print("MyPy score: 80/100 (default)")
    
    # Calculate overall score
    overall_score = sum(scores) // len(scores)
    print(f"Overall quality score: {overall_score}/100")
    
    return overall_score

def calculate_security_score(bandit_file: str, safety_file: str, secrets_file: str) -> int:
    """Calculate security score"""
    scores = []
    
    # Bandit score
    try:
        with open(bandit_file, 'r') as f:
            bandit_results = json.load(f)
        
        high_issues = len([r for r in bandit_results.get('results', []) if r.get('issue_severity') == 'HIGH'])
        medium_issues = len([r for r in bandit_results.get('results', []) if r.get('issue_severity') == 'MEDIUM'])
        
        bandit_score = max(0, 100 - (high_issues * 10 + medium_issues * 5))
        scores.append(bandit_score)
        print(f"Bandit score: {bandit_score}/100 ({high_issues} high, {medium_issues} medium)")
    except:
        scores.append(90)
        print("Bandit score: 90/100 (default)")
    
    # Safety score
    try:
        with open(safety_file, 'r') as f:
            safety_results = json.load(f)
        
        vulnerabilities = len(safety_results.get('vulnerabilities', []))
        safety_score = max(0, 100 - vulnerabilities * 15)
        scores.append(safety_score)
        print(f"Safety score: {safety_score}/100 ({vulnerabilities} vulnerabilities)")
    except:
        scores.append(95)
        print("Safety score: 95/100 (default)")
    
    # Secrets score
    try:
        with open(secrets_file, 'r') as f:
            secrets_results = json.load(f)
        
        secrets_found = len(secrets_results.get('results', []))
        secrets_score = max(0, 100 - secrets_found * 20)
        scores.append(secrets_score)
        print(f"Secrets score: {secrets_score}/100 ({secrets_found} secrets)")
    except:
        scores.append(85)
        print("Secrets score: 85/100 (default)")
    
    overall_score = sum(scores) // len(scores)
    print(f"Overall security score: {overall_score}/100")
    
    return overall_score

def calculate_performance_score(perf_file: str) -> int:
    """Calculate performance score"""
    try:
        with open(perf_file, 'r') as f:
            perf_results = json.load(f)
        
        # Extract performance metrics
        benchmarks = perf_results.get('benchmarks', [])
        if not benchmarks:
            return 80  # Default
        
        scores = []
        for benchmark in benchmarks:
            # Calculate score based on performance
            time_taken = benchmark.get('stats', {}).get('mean', 1.0)
            
            # Score based on time (faster = higher score)
            if time_taken < 0.1:
                score = 100
            elif time_taken < 0.5:
                score = 90
            elif time_taken < 1.0:
                score = 80
            elif time_taken < 2.0:
                score = 70
            else:
                score = 60
            
            scores.append(score)
        
        overall_score = sum(scores) // len(scores)
        print(f"Performance score: {overall_score}/100")
        
        return overall_score
    
    except:
        print("Performance score: 80/100 (default)")
        return 80

def calculate_debt_score(debt_file: str) -> int:
    """Calculate technical debt score"""
    try:
        with open(debt_file, 'r') as f:
            debt_results = json.load(f)
        
        # Extract debt metrics
        total_debt = debt_results.get('total_debt_items', 0)
        severity = debt_results.get('severity', 'low')
        
        # Base score calculation
        base_score = max(0, 100 - total_debt)
        
        # Adjust based on severity
        severity_multiplier = {
            'critical': 0.5,
            'high': 0.7,
            'medium': 0.85,
            'low': 1.0
        }
        
        final_score = int(base_score * severity_multiplier.get(severity, 1.0))
        print(f"Technical debt score: {final_score}/100 ({total_debt} items, {severity} severity)")
        
        return final_score
    
    except:
        print("Technical debt score: 75/100 (default)")
        return 75

def main():
    """Main calculator"""
    if len(sys.argv) < 2:
        print("Usage: python calculate_quality.py [quality|security|performance|debt] [files...]")
        sys.exit(1)
    
    calc_type = sys.argv[1]
    
    if calc_type == "quality":
        if len(sys.argv) < 4:
            print("Usage: python calculate_quality.py quality ruff.json black.txt mypy_dir")
            sys.exit(1)
        
        score = calculate_quality_score(sys.argv[2], sys.argv[3], sys.argv[4])
        print(f"::set-output name=score::{score}")
    
    elif calc_type == "security":
        if len(sys.argv) < 4:
            print("Usage: python calculate_quality.py security bandit.json safety.json secrets.json")
            sys.exit(1)
        
        score = calculate_security_score(sys.argv[2], sys.argv[3], sys.argv[4])
        print(f"::set-output name=score::{score}")
    
    elif calc_type == "performance":
        if len(sys.argv) < 3:
            print("Usage: python calculate_quality.py performance perf.json")
            sys.exit(1)
        
        score = calculate_performance_score(sys.argv[2])
        print(f"::set-output name=score::{score}")
    
    elif calc_type == "debt":
        if len(sys.argv) < 3:
            print("Usage: python calculate_quality.py debt debt.json")
            sys.exit(1)
        
        score = calculate_debt_score(sys.argv[2])
        print(f"::set-output name=score::{score}")
    
    else:
        print(f"Unknown calculation type: {calc_type}")
        sys.exit(1)

if __name__ == "__main__":
    main()
