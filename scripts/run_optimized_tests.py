#!/usr/bin/env python3
"""
Comprehensive Test Runner for Asmblr Optimized Features
Runs all tests for cache, async tasks, metrics, backup, and Docker
"""

import sys
import time
import subprocess
from pathlib import Path
from typing import Any
import argparse

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import pytest
    from loguru import logger
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please install: pip install pytest loguru")
    sys.exit(1)


class OptimizedTestRunner:
    """Test runner for optimized Asmblr features"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        
    def run_test_suite(self, suite_name: str, test_files: list[str], timeout: int = 300) -> dict[str, Any]:
        """Run a specific test suite"""
        logger.info(f"Running test suite: {suite_name}")
        
        suite_start = time.time()
        
        try:
            # Run pytest with specified test files
            cmd = [
                "python", "-m", "pytest",
                "-v",
                "--tb=short",
                "--timeout=" + str(timeout),
                "--json-report",
                "--json-report-file=test_results.json",
                *test_files
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 60  # Extra time for pytest overhead
            )
            
            suite_end = time.time()
            duration = suite_end - suite_start
            
            # Parse results
            try:
                with open("test_results.json") as f:
                    import json
                    json_results = json.load(f)
            except:
                json_results = {"summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0}}
            
            suite_results = {
                "suite": suite_name,
                "exit_code": result.returncode,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "summary": json_results.get("summary", {}),
                "success": result.returncode == 0
            }
            
            logger.info(f"Suite {suite_name} completed in {duration:.2f}s")
            return suite_results
            
        except subprocess.TimeoutExpired:
            logger.error(f"Test suite {suite_name} timed out")
            return {
                "suite": suite_name,
                "exit_code": -1,
                "duration": timeout,
                "error": "timeout",
                "success": False
            }
        except Exception as e:
            logger.error(f"Test suite {suite_name} failed: {e}")
            return {
                "suite": suite_name,
                "exit_code": -2,
                "error": str(e),
                "success": False
            }
    
    def run_all_tests(self) -> dict[str, Any]:
        """Run all optimized feature tests"""
        logger.info("Starting comprehensive test suite for Asmblr optimized features")
        
        # Define test suites
        test_suites = {
            "cache_llm": {
                "files": ["tests/test_llm_cache.py"],
                "description": "LLM Cache Tests",
                "timeout": 180
            },
            "async_tasks": {
                "files": ["tests/test_async_tasks.py"],
                "description": "Async Task Processing Tests",
                "timeout": 240
            },
            "business_metrics": {
                "files": ["tests/test_business_metrics.py"],
                "description": "Business Intelligence Metrics Tests",
                "timeout": 180
            },
            "backup_service": {
                "files": ["tests/test_backup_service.py"],
                "description": "Backup Service Tests",
                "timeout": 300
            },
            "docker_optimized": {
                "files": ["tests/test_docker_optimized.py"],
                "description": "Optimized Docker Configuration Tests",
                "timeout": 120
            }
        }
        
        results = {}
        
        for suite_name, config in test_suites.items():
            suite_result = self.run_test_suite(
                suite_name,
                config["files"],
                config["timeout"]
            )
            results[suite_name] = suite_result
            
            # Log intermediate results
            if suite_result["success"]:
                logger.success(f"✅ {config['description']}: PASSED")
            else:
                logger.error(f"❌ {config['description']}: FAILED")
        
        return results
    
    def generate_report(self, results: dict[str, Any]) -> None:
        """Generate comprehensive test report"""
        total_time = time.time() - self.start_time
        
        # Calculate summary
        total_suites = len(results)
        passed_suites = sum(1 for r in results.values() if r.get("success", False))
        failed_suites = total_suites - passed_suites
        
        # Calculate test counts
        total_tests = sum(r.get("summary", {}).get("total", 0) for r in results.values())
        passed_tests = sum(r.get("summary", {}).get("passed", 0) for r in results.values())
        failed_tests = sum(r.get("summary", {}).get("failed", 0) for r in results.values())
        skipped_tests = sum(r.get("summary", {}).get("skipped", 0) for r in results.values())
        
        success_rate = (passed_suites/total_suites*100) if total_suites > 0 else 0
        test_success_rate = (passed_tests/total_tests*100) if total_tests > 0 else 0
        
        # Generate report
        report = f"""
# 🧪 Asmblr Optimized Features Test Report

## 📊 Executive Summary
- **Total Test Suites**: {total_suites}
- **Passed Suites**: {passed_suites}
- **Failed Suites**: {failed_suites}
- **Success Rate**: {success_rate:.1f}%

## 📈 Test Results
- **Total Tests**: {total_tests}
- **Passed Tests**: {passed_tests}
- **Failed Tests**: {failed_tests}
- **Skipped Tests**: {skipped_tests}
- **Test Success Rate**: {test_success_rate:.1f}%

## ⏱️ Performance
- **Total Duration**: {total_time:.2f} seconds

## 📋 Detailed Results

"""
        
        for suite_name, result in results.items():
            status = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
            duration = result.get("duration", 0)
            summary = result.get("summary", {})
            
            report += f"""
### {result.get('suite', suite_name).replace('_', ' ').title()} {status}
- Duration: {duration:.2f}s
- Tests: {summary.get('total', 0)} total, {summary.get('passed', 0)} passed, {summary.get('failed', 0)} failed
"""
            
            if not result.get("success", False):
                error = result.get("error", result.get("stderr", "Unknown error"))
                report += f"- Error: {error}\n"
        
        # Add recommendations
        if failed_suites > 0:
            report += """
## 🔧 Recommendations

### For Failed Tests:
1. Check the error messages above
2. Verify all dependencies are installed
3. Ensure Docker is running for Docker tests
4. Check Redis connection for cache tests
5. Verify file permissions for backup tests

### General:
- Run individual test suites for detailed debugging
- Check logs in the test output above
- Ensure all test dependencies are available

"""
        
        # Add next steps
        if passed_suites == total_suites:
            report += """
## 🎉 All Tests Passed!

Your Asmblr optimized features are working correctly. You can now:

1. Deploy with: `docker-compose -f docker-compose.optimized.yml up -d`
2. Enable monitoring: `--profile monitoring`
3. Enable backup: `--profile backup`
4. Check health: `curl http://localhost:8000/health/detailed`

"""
        
        # Write report to file
        report_file = Path("test_report_optimized.md")
        report_file.write_text(report)
        
        # Print to console
        print(report)
        
        logger.info(f"Test report saved to: {report_file}")
    
    def run_integration_tests(self) -> dict[str, Any]:
        """Run integration tests for the complete optimized stack"""
        logger.info("Running integration tests for optimized stack")
        
        integration_tests = {
            "cache_integration": {
                "files": ["tests/test_llm_cache.py::TestCachePerformance::test_cache_performance"],
                "description": "Cache Performance Integration",
                "timeout": 120
            },
            "async_integration": {
                "files": ["tests/test_async_tasks.py::TestTaskManagerIntegration::test_concurrent_task_execution"],
                "description": "Async Task Integration",
                "timeout": 180
            },
            "metrics_integration": {
                "files": ["tests/test_business_metrics.py::TestMetricsIntegration::test_metrics_end_to_end_flow"],
                "description": "Metrics Integration",
                "timeout": 120
            }
        }
        
        results = {}
        for test_name, config in integration_tests.items():
            result = self.run_test_suite(test_name, config["files"], config["timeout"])
            results[test_name] = result
        
        return results


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run Asmblr optimized feature tests")
    parser.add_argument("--suite", choices=["cache", "async", "metrics", "backup", "docker", "integration"],
                       help="Run specific test suite")
    parser.add_argument("--timeout", type=int, default=300,
                       help="Timeout for tests in seconds")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--report-only", action="store_true",
                       help="Generate report only (if test results exist)")
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    runner = OptimizedTestRunner()
    
    if args.report_only:
        # Generate report from existing results
        try:
            with open("test_results.json") as f:
                import json
                results = {"cached": json.load(f)}
            runner.generate_report(results)
        except FileNotFoundError:
            logger.error("No test results found. Run tests first.")
            sys.exit(1)
        return
    
    if args.suite:
        # Run specific suite
        suite_configs = {
            "cache": ["tests/test_llm_cache.py"],
            "async": ["tests/test_async_tasks.py"],
            "metrics": ["tests/test_business_metrics.py"],
            "backup": ["tests/test_backup_service.py"],
            "docker": ["tests/test_docker_optimized.py"],
            "integration": None  # Special case
        }
        
        if args.suite == "integration":
            results = runner.run_integration_tests()
        else:
            test_files = suite_configs.get(args.suite, [])
            if test_files:
                results = {args.suite: runner.run_test_suite(args.suite, test_files, args.timeout)}
            else:
                logger.error(f"Unknown suite: {args.suite}")
                sys.exit(1)
        
        runner.generate_report(results)
        
        # Exit with appropriate code
        failed_count = sum(1 for r in results.values() if not r.get("success", False))
        sys.exit(1 if failed_count > 0 else 0)
    
    else:
        # Run all tests
        results = runner.run_all_tests()
        runner.generate_report(results)
        
        # Exit with appropriate code
        failed_count = sum(1 for r in results.values() if not r.get("success", False))
        sys.exit(1 if failed_count > 0 else 0)


if __name__ == "__main__":
    main()
