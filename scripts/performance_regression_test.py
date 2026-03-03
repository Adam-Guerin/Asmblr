#!/usr/bin/env python3
"""
Performance Regression Testing for Asmblr CI/CD
Compares current performance against baseline
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

def load_baseline_data(baseline_ref: str) -> dict:
    """Load baseline performance data"""
    # In a real implementation, this would fetch data from GitHub API
    # For now, return mock baseline data
    return {
        "baseline_ref": baseline_ref,
        "timestamp": "2024-01-01T00:00:00Z",
        "metrics": {
            "response_time_ms": 150,
            "memory_usage_mb": 200,
            "cpu_usage_percent": 40,
            "throughput_rps": 1000
        }
    }

def load_current_data(current_ref: str) -> dict:
    """Load current performance data"""
    # Load current performance data from recent tests
    current_file = Path("perf_results.json")
    if not current_file.exists():
        return {}
    
    try:
        with open(current_file, 'r') as f:
            data = json.load(f)
        
        # Extract key metrics
        tests = data.get('tests', {})
        return {
            "current_ref": current_ref,
            "timestamp": data.get('timestamp'),
            "metrics": {
                "response_time_ms": tests.get('response_time', {}).get('average_ms', 0),
                "memory_usage_mb": tests.get('memory_usage', {}).get('peak_mb', 0),
                "cpu_usage_percent": tests.get('cpu_usage', {}).get('average_percent', 0),
                "throughput_rps": tests.get('throughput', {}).get('rps', 0)
            }
        }
    except Exception:
        return {}

def calculate_regression(baseline: dict, current: dict) -> dict:
    """Calculate performance regression"""
    baseline_metrics = baseline.get('metrics', {})
    current_metrics = current.get('metrics', {})
    
    regression = {
        "baseline_ref": baseline.get('baseline_ref'),
        "current_ref": current.get('current_ref'),
        "timestamp": datetime.utcnow().isoformat(),
        "comparisons": {},
        "summary": {
            "has_regression": False,
            "regression_count": 0,
            "improvement_count": 0
        }
    }
    
    # Compare each metric
    for metric_name, baseline_value in baseline_metrics.items():
        current_value = current_metrics.get(metric_name, 0)
        
        # Calculate percentage change
        if baseline_value > 0:
            change_percent = ((current_value - baseline_value) / baseline_value) * 100
        else:
            change_percent = 0
        
        # Determine if regression (higher is worse for most metrics)
        thresholds = {
            'response_time_ms': 10,      # 10% increase is regression
            'memory_usage_mb': 15,     # 15% increase is regression
            'cpu_usage_percent': 20,     # 20% increase is regression
            'throughput_rps': -10       # 10% decrease is regression
        }
        
        threshold = thresholds.get(metric_name, 10)
        is_regression = (threshold > 0 and change_percent > threshold) or (threshold < 0 and change_percent < threshold)
        
        regression["comparisons"][metric_name] = {
            "baseline": baseline_value,
            "current": current_value,
            "change_percent": round(change_percent, 2),
            "threshold": threshold,
            "status": "regression" if is_regression else "stable" if abs(change_percent) < 5 else "improved",
            "is_regression": is_regression
        }
        
        # Update summary
        if is_regression:
            regression["summary"]["has_regression"] = True
            regression["summary"]["regression_count"] += 1
        elif change_percent < -5:
            regression["summary"]["improvement_count"] += 1
    
    return regression

def main():
    parser = argparse.ArgumentParser(description="Performance Regression Testing")
    parser.add_argument("--baseline", required=True, help="Baseline git ref")
    parser.add_argument("--current", required=True, help="Current git ref")
    
    args = parser.parse_args()
    
    # Load data
    baseline_data = load_baseline_data(args.baseline)
    current_data = load_current_data(args.current)
    
    if not current_data:
        print("Error: Could not load current performance data")
        return 1
    
    # Calculate regression
    regression_result = calculate_regression(baseline_data, current_data)
    
    # Save regression report
    with open("performance_regression_report.json", "w") as f:
        json.dump(regression_result, f, indent=2)
    
    # Print results
    print(f"Performance Regression Analysis:")
    print(f"Baseline: {regression_result['baseline_ref']}")
    print(f"Current: {regression_result['current_ref']}")
    print(f"Has Regression: {regression_result['summary']['has_regression']}")
    print(f"Regressions: {regression_result['summary']['regression_count']}")
    print(f"Improvements: {regression_result['summary']['improvement_count']}")
    
    print("\nMetric Comparisons:")
    for metric, comparison in regression_result["comparisons"].items():
        status_icon = "📉" if comparison["is_regression"] else "📈" if comparison["status"] == "improved" else "➡️"
        print(f"{status_icon} {metric}: {comparison['baseline']} → {comparison['current']} ({comparison['change_percent']}%)")
    
    return 1 if regression_result["summary"]["has_regression"] else 0

if __name__ == "__main__":
    sys.exit(main())
