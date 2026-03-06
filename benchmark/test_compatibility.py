#!/usr/bin/env python3
"""
Test compatibility of scaled dataset with existing evaluation pipeline.
"""

import sys
import json
from pathlib import Path

# Add benchmark to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import ExperimentConfig
from core.runner import BenchmarkRunner
from datasets import load_dataset

def test_dataset_compatibility():
    """Test that the scaled dataset works with existing pipeline."""
    print("Testing dataset compatibility...")
    
    # Test loading the dataset
    try:
        dataset = load_dataset("realistic_corpus", "dataset_10k")
        if dataset is None:
            # Try alternative loading
            dataset = load_dataset("scaled_dataset", "dataset_10k")
        
        if dataset is None:
            print("❌ Failed to load scaled dataset")
            return False
            
        print(f"✅ Successfully loaded {len(dataset)} contexts")
        
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return False
    
    # Test dataset structure
    sample_context = dataset[0] if dataset else {}
    required_fields = ['id', 'raw_text', 'industry_tag', 'geographic_cluster', 'estimated_stage']
    
    missing_fields = []
    for field in required_fields:
        if field not in sample_context:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return False
    
    print("✅ Dataset structure is compatible")
    
    # Test evaluation mode datasets
    modes = ['full', 'large', 'stress']
    for mode in modes:
        mode_path = Path(f"dataset_10k/evaluation_modes/{mode}")
        if not mode_path.exists():
            print(f"❌ Evaluation mode {mode} not found")
            return False
        
        mode_files = list(mode_path.glob("context_*.json"))
        print(f"✅ {mode} mode: {len(mode_files)} contexts")
    
    return True

def test_experiment_config():
    """Test experiment configuration with scaled dataset."""
    print("\nTesting experiment configuration...")
    
    try:
        # Create config for scaled dataset
        config = ExperimentConfig(
            experiment_id="test_scaled_dataset",
            dataset_name="scaled_dataset",
            dataset_path="dataset_10k",
            baselines=["random_baseline"],
            metrics=["pain_extraction", "idea_novelty"],
            output_dir="test_output",
            seed=42
        )
        
        print("✅ Experiment configuration created successfully")
        
        # Test runner initialization
        runner = BenchmarkRunner(config)
        print("✅ Benchmark runner initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error with experiment configuration: {e}")
        return False

def main():
    """Run compatibility tests."""
    print("=" * 60)
    print("SCALED DATASET COMPATIBILITY TESTS")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 2
    
    # Test dataset compatibility
    if test_dataset_compatibility():
        tests_passed += 1
    
    # Test experiment configuration
    if test_experiment_config():
        tests_passed += 1
    
    print("\n" + "=" * 60)
    print(f"COMPATIBILITY TESTS: {tests_passed}/{total_tests} PASSED")
    print("=" * 60)
    
    if tests_passed == total_tests:
        print("✅ Scaled dataset is fully compatible with evaluation pipeline")
        return True
    else:
        print("❌ Some compatibility issues found")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
