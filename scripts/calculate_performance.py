#!/usr/bin/env python3
"""
Calculate Performance Score from Test Results
Aggregates performance test results into a single score
"""

import json
import sys
from pathlib import Path

def load_json_file(filepath: str) -> Dict:
    """Load JSON file safely"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def calculate_performance_score(perf_results: Dict) -> float:
    """Calculate performance score from test results"""
    if not perf_results or 'tests' not in perf_results:
        return 80.0  # Default score if no results
    
    tests = perf_results.get('tests', {})
    if not tests:
        return 80.0
    
    # Calculate score based on test results
    total_score = 100.0
    
    # Response time scoring (weight: 30%)
    response_test = tests.get('response_time', {})
    if response_test.get('status') == 'fail':
        total_score -= 30
    elif response_test.get('average_ms', 0) > 200:
        total_score -= 15
    
    # Memory usage scoring (weight: 25%)
    memory_test = tests.get('memory_usage', {})
    if memory_test.get('status') == 'fail':
        total_score -= 25
    elif memory_test.get('peak_mb', 0) > 512:
        total_score -= 10
    
    # CPU usage scoring (weight: 25%)
    cpu_test = tests.get('cpu_usage', {})
    if cpu_test.get('status') == 'fail':
        total_score -= 25
    elif cpu_test.get('average_percent', 0) > 80:
        total_score -= 10
    
    # Throughput scoring (weight: 20%)
    throughput_test = tests.get('throughput', {})
    if throughput_test.get('status') == 'fail':
        total_score -= 20
    elif throughput_test.get('rps', 0) < 500:
        total_score -= 10
    
    return max(0, total_score)

def main():
    if len(sys.argv) < 2:
        print("Usage: python calculate_performance.py <performance_results.json>")
        return 1
    
    perf_file = sys.argv[1]
    
    # Load performance results
    perf_results = load_json_file(perf_file)
    
    # Calculate score
    score = calculate_performance_score(perf_results)
    
    # Round to nearest integer
    final_score = round(score)
    
    print(final_score)
    
    # Generate detailed report
    report = {
        "performance_score": final_score,
        "input_file": perf_file,
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    with open("performance_score_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
