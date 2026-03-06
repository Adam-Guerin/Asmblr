#!/usr/bin/env python3
"""
Simple compatibility test for scaled dataset.
"""

import json
from pathlib import Path

def test_dataset_structure():
    """Test that the scaled dataset has the correct structure."""
    print("Testing dataset structure...")
    
    dataset_path = Path("dataset_10k")
    
    # Check dataset exists
    if not dataset_path.exists():
        print("❌ Dataset directory not found")
        return False
    
    # Check metadata file
    metadata_file = dataset_path / "dataset_metadata.json"
    if not metadata_file.exists():
        print("❌ Dataset metadata not found")
        return False
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    print(f"✅ Dataset metadata: {metadata['total_contexts']} contexts")
    
    # Check context files
    context_files = list(dataset_path.glob("context_*.json"))
    print(f"✅ Found {len(context_files)} context files")
    
    if len(context_files) < 9000:  # Allow some tolerance
        print(f"❌ Dataset too small: {len(context_files)} < 9000")
        return False
    
    # Check sample context structure
    sample_file = context_files[0]
    with open(sample_file, 'r') as f:
        context = json.load(f)
    
    required_fields = ['id', 'raw_text', 'industry_tag', 'geographic_cluster', 'estimated_stage']
    missing_fields = [field for field in required_fields if field not in context]
    
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return False
    
    print("✅ Context structure is valid")
    
    # Check evaluation modes
    modes = ['full', 'large', 'stress']
    for mode in modes:
        mode_path = dataset_path / "evaluation_modes" / mode
        if not mode_path.exists():
            print(f"❌ Evaluation mode {mode} not found")
            return False
        
        mode_files = list(mode_path.glob("context_*.json"))
        expected_counts = {'full': 1000, 'large': 9000, 'stress': 1000}
        
        if len(mode_files) < expected_counts[mode] * 0.8:  # Allow 20% tolerance
            print(f"❌ Mode {mode} too small: {len(mode_files)}")
            return False
        
        print(f"✅ {mode} mode: {len(mode_files)} contexts")
    
    return True

def test_uncertainty_distribution():
    """Test uncertainty distribution meets targets."""
    print("\nTesting uncertainty distribution...")
    
    # Load validation report
    validation_file = Path("dataset_10k/dataset_validation_report.json")
    if not validation_file.exists():
        print("❌ Validation report not found")
        return False
    
    with open(validation_file, 'r') as f:
        report = json.load(f)
    
    uncertainty = report['uncertainty_breakdown']
    total = sum(uncertainty.values())
    
    low_pct = uncertainty['low'] / total * 100
    medium_pct = uncertainty['medium'] / total * 100
    high_pct = uncertainty['high'] / total * 100
    
    print(f"Uncertainty distribution:")
    print(f"  Low: {uncertainty['low']} ({low_pct:.1f}%)")
    print(f"  Medium: {uncertainty['medium']} ({medium_pct:.1f}%)")
    print(f"  High: {uncertainty['high']} ({high_pct:.1f}%)")
    
    # Check targets
    targets_met = (
        55 <= low_pct <= 65 and
        25 <= medium_pct <= 35 and
        8 <= high_pct <= 15
    )
    
    if targets_met:
        print("✅ Uncertainty distribution meets targets")
        return True
    else:
        print("❌ Uncertainty distribution doesn't meet targets")
        return False

def test_artifacts():
    """Test that all required artifacts are present."""
    print("\nTesting output artifacts...")
    
    dataset_path = Path("dataset_10k")
    required_files = [
        "dataset_metadata.json",
        "dataset_generation_manifest.json", 
        "dataset_validation_report.json",
        "dataset_summary_10k.csv",
        "uncertainty_distribution_10k.csv",
        "industry_distribution_10k.csv"
    ]
    
    missing_files = []
    for file_name in required_files:
        file_path = dataset_path / file_name
        if not file_path.exists():
            missing_files.append(file_name)
    
    if missing_files:
        print(f"❌ Missing artifacts: {missing_files}")
        return False
    
    print("✅ All required artifacts present")
    return True

def main():
    """Run all compatibility tests."""
    print("=" * 60)
    print("SCALED DATASET COMPATIBILITY TESTS")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    if test_dataset_structure():
        tests_passed += 1
    
    if test_uncertainty_distribution():
        tests_passed += 1
    
    if test_artifacts():
        tests_passed += 1
    
    print("\n" + "=" * 60)
    print(f"COMPATIBILITY TESTS: {tests_passed}/{total_tests} PASSED")
    print("=" * 60)
    
    if tests_passed == total_tests:
        print("✅ Scaled dataset is ready for evaluation pipeline")
        return True
    else:
        print("❌ Some issues need to be addressed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
