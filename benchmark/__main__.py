"""
Main CLI entry point for the benchmark suite.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from .core import BenchmarkRunner, ExperimentConfig, set_seed, load_json, save_json
from .datasets import DatasetRegistry, load_dataset, create_sample_dataset
from .baselines import BaselineRegistry, run_baseline
from .metrics import MetricRegistry, compute_all_metrics
from .reporting import ReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.getLogger().setLevel(level)


def cmd_run(args):
    """Run benchmark experiment."""
    logger.info("Starting benchmark run")
    
    # Load configuration
    config = ExperimentConfig.from_yaml(args.config)
    
    # Validate configuration
    issues = config.validate()
    if issues:
        logger.error("Configuration validation failed:")
        for issue in issues:
            logger.error(f"  - {issue}")
        return 1
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Set seed for reproducibility
    if config.deterministic:
        set_seed(config.seed)
    
    try:
        # Initialize and run benchmark
        runner = BenchmarkRunner(config)
        results = runner.run_experiment()
        
        logger.info(f"Benchmark completed successfully")
        logger.info(f"Results saved to: {config.get_output_path()}")
        logger.info(f"Overall score: {results.get('aggregated', {}).get('metrics_summary', {}).get('overall', 'N/A')}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Benchmark run failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_evaluate_run(args):
    """Evaluate a single Asmblr run."""
    logger.info(f"Evaluating run: {args.run_dir}")
    
    # Load configuration
    config = ExperimentConfig.from_yaml(args.config)
    setup_logging(args.verbose)
    
    try:
        # Initialize runner
        runner = BenchmarkRunner(config)
        
        # Evaluate single run
        results = runner.evaluate_single_run(args.run_dir)
        
        logger.info(f"Evaluation completed")
        logger.info(f"Results saved to: {config.get_output_path()}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_compare(args):
    """Compare multiple runs."""
    logger.info(f"Comparing {len(args.run_dirs)} runs")
    
    # Load configuration
    config = ExperimentConfig.from_yaml(args.config)
    setup_logging(args.verbose)
    
    try:
        # Initialize runner
        runner = BenchmarkRunner(config)
        
        # Compare runs
        results = runner.compare_runs(args.run_dirs)
        
        logger.info(f"Comparison completed")
        logger.info(f"Results saved to: {config.get_output_path()}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_list_datasets(args):
    """List available datasets."""
    datasets = DatasetRegistry.list_datasets()
    
    print("Available datasets:")
    for dataset in datasets:
        info = DatasetRegistry.dataset_info(dataset)
        print(f"  - {dataset}: {info.get('description', 'No description')}")
    
    return 0


def cmd_list_baselines(args):
    """List available baselines."""
    baselines = BaselineRegistry.list_baselines()
    
    print("Available baselines:")
    for baseline in baselines:
        info = BaselineRegistry.baseline_info(baseline)
        print(f"  - {baseline}: {info.get('description', 'No description')}")
    
    return 0


def cmd_list_metrics(args):
    """List available metrics."""
    metrics = MetricRegistry.list_metrics()
    
    print("Available metrics:")
    for metric in metrics:
        info = MetricRegistry.metric_info(metric)
        print(f"  - {metric}: {info.get('description', 'No description')}")
    
    return 0


def cmd_create_sample(args):
    """Create sample dataset."""
    logger.info(f"Creating sample dataset with {args.size} items")
    
    try:
        create_sample_dataset(args.output, args.size)
        logger.info(f"Sample dataset created: {args.output}")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to create sample dataset: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Asmblr Scientific Benchmark Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full benchmark experiment
  python -m benchmark run --config benchmark/configs/default.yaml
  
  # Evaluate single Asmblr run
  python -m benchmark evaluate_run --config benchmark/configs/default.yaml --run_dir runs/exp_001
  
  # Compare multiple runs
  python -m benchmark compare --config benchmark/configs/default.yaml --run_dir runs/exp_001 runs/exp_002
  
  # List available resources
  python -m benchmark list-datasets
  python -m benchmark list-baselines
  python -m benchmark list-metrics
  
  # Create sample dataset
  python -m benchmark create-sample --output sample_dataset.json --size 10
        """
    )
    
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run full benchmark experiment')
    run_parser.add_argument('--config', '-c', required=True,
                          help='Configuration file path')
    run_parser.set_defaults(func=cmd_run)
    
    # Evaluate run command
    eval_parser = subparsers.add_parser('evaluate_run', help='Evaluate single Asmblr run')
    eval_parser.add_argument('--config', '-c', required=True,
                           help='Configuration file path')
    eval_parser.add_argument('--run_dir', '-r', required=True,
                           help='Asmblr run directory to evaluate')
    eval_parser.set_defaults(func=cmd_evaluate_run)
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare multiple runs')
    compare_parser.add_argument('--config', '-c', required=True,
                             help='Configuration file path')
    compare_parser.add_argument('--run_dirs', '-r', nargs='+', required=True,
                             help='Asmblr run directories to compare')
    compare_parser.set_defaults(func=cmd_compare)
    
    # List commands
    list_parser = subparsers.add_parser('list-datasets', help='List available datasets')
    list_parser.set_defaults(func=cmd_list_datasets)
    
    list_parser = subparsers.add_parser('list-baselines', help='List available baselines')
    list_parser.set_defaults(func=cmd_list_baselines)
    
    list_parser = subparsers.add_parser('list-metrics', help='List available metrics')
    list_parser.set_defaults(func=cmd_list_metrics)
    
    # Create sample command
    sample_parser = subparsers.add_parser('create-sample', help='Create sample dataset')
    sample_parser.add_argument('--output', '-o', required=True,
                            help='Output file path')
    sample_parser.add_argument('--size', '-s', type=int, default=10,
                            help='Number of items to generate (default: 10)')
    sample_parser.set_defaults(func=cmd_create_sample)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Command failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
