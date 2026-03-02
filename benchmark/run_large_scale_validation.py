#!/usr/bin/env python3
"""
Large-Scale Empirical Validation Runner
Executes the complete validation pipeline with proper error handling and progress tracking.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
import json
import time
from datetime import datetime

# Add benchmark to path
sys.path.insert(0, str(Path(__file__).parent))

from large_scale_validation import main, logger

def setup_directories():
    """Create necessary directories."""
    directories = [
        "dataset",
        "runs", 
        "results",
        "paper_ready_figures"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"Created directory: {directory}")

def validate_requirements():
    """Validate that all requirements are installed."""
    required_packages = {
        'aiohttp': 'aiohttp',
        'beautifulsoup4': 'bs4', 
        'requests': 'requests',
        'numpy': 'numpy',
        'torch': 'torch',
        'scipy': 'scipy',
        'pandas': 'pandas',
        'GitPython': 'git'
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        logger.error(f"Missing required packages: {missing_packages}")
        logger.error("Install with: pip install -r requirements_validation.txt")
        return False
    
    logger.info("All required packages are installed")
    return True

def check_dataset_size():
    """Check if dataset meets minimum size requirement."""
    dataset_dir = Path("dataset")
    if not dataset_dir.exists():
        logger.warning("Dataset directory does not exist")
        return 0
    
    context_files = list(dataset_dir.glob("context_*.json"))
    size = len(context_files)
    
    logger.info(f"Current dataset size: {size} contexts")
    
    if size < 1000:
        logger.warning(f"Dataset size {size} < 1,000. Will collect more data.")
    
    return size

async def run_validation():
    """Run the complete validation pipeline."""
    logger.info("=" * 80)
    logger.info("LARGE-SCALE EMPIRICAL VALIDATION OF ASMBLR")
    logger.info("=" * 80)
    
    start_time = time.time()
    
    try:
        # Setup
        logger.info("Setting up environment...")
        setup_directories()
        
        # Validate requirements
        if not validate_requirements():
            return 1
        
        # Check dataset
        current_size = check_dataset_size()
        
        # Run main validation
        logger.info("Starting validation pipeline...")
        await main()
        
        # Calculate runtime
        end_time = time.time()
        runtime = end_time - start_time
        
        logger.info("=" * 80)
        logger.info("VALIDATION COMPLETED SUCCESSFULLY")
        logger.info(f"Total runtime: {runtime:.2f} seconds ({runtime/60:.1f} minutes)")
        logger.info("=" * 80)
        
        # Generate summary report
        await generate_summary_report(runtime)
        
        return 0
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

async def generate_summary_report(runtime: float):
    """Generate a summary report of the validation."""
    report = {
        "validation_summary": {
            "timestamp": datetime.now().isoformat(),
            "runtime_seconds": runtime,
            "runtime_minutes": runtime / 60,
            "status": "completed"
        },
        "dataset_info": {},
        "results_info": {},
        "files_generated": []
    }
    
    # Dataset info
    dataset_dir = Path("dataset")
    if dataset_dir.exists():
        context_files = list(dataset_dir.glob("context_*.json"))
        report["dataset_info"] = {
            "total_contexts": len(context_files),
            "metadata_file": "dataset/dataset_metadata.json" if Path("dataset/dataset_metadata.json").exists() else None
        }
    
    # Results info
    results_dir = Path("results")
    if results_dir.exists():
        result_files = list(results_dir.glob("*.json"))
        report["results_info"] = {
            "total_files": len(result_files),
            "files": [f.name for f in result_files]
        }
    
    # Runs info
    runs_dir = Path("runs")
    if runs_dir.exists():
        run_dirs = [d for d in runs_dir.iterdir() if d.is_dir()]
        report["runs_info"] = {
            "total_run_directories": len(run_dirs),
            "run_ids": [d.name for d in run_dirs]
        }
    
    # Files generated
    report["files_generated"] = [
        "dataset/dataset_metadata.json",
        "results/summary_statistics.json", 
        "results/statistical_tests.json",
        "results/failure_taxonomy.json",
        "results/compute_tracking.json",
        "paper_ready_tables.csv"
    ]
    
    # Save report
    with open("validation_summary_report.json", 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info("Summary report saved to: validation_summary_report.json")
    
    # Print summary to console
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Dataset contexts: {report['dataset_info'].get('total_contexts', 0)}")
    print(f"Run directories: {report['runs_info'].get('total_run_directories', 0)}")
    print(f"Result files: {report['results_info'].get('total_files', 0)}")
    print(f"Runtime: {runtime:.1f} minutes")
    print("\nKey output files:")
    for file_path in report["files_generated"]:
        if Path(file_path).exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} (missing)")
    print("=" * 80)

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('validation.log'),
            logging.StreamHandler()
        ]
    )
    
    # Run validation
    exit_code = asyncio.run(run_validation())
    sys.exit(exit_code)
