#!/usr/bin/env python3
"""
Final Validation Script for Asmblr v2.0 Optimizations
Validates that all optimizations are properly integrated and functional
"""

import asyncio
import sys
import time
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import requests
    import redis.asyncio as redis
    from loguru import logger
    import pytest
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please install: pip install requests redis loguru pytest")
    sys.exit(1)


class OptimizationValidator:
    """Validates all Asmblr v2.0 optimizations"""
    
    def __init__(self):
        self.validation_results = {}
        self.start_time = time.time()
        self.base_url = "http://localhost:8000"
        self.ui_url = "http://localhost:8501"
        
    def validate_file_structure(self) -> Dict[str, Any]:
        """Validate that all optimization files exist"""
        logger.info("Validating file structure...")
        
        required_files = {
            "core_cache": "app/core/llm_cache.py",
            "core_async": "app/core/async_tasks.py", 
            "metrics": "app/monitoring/business_metrics.py",
            "backup": "scripts/backup-service.py",
            "docker_optimized": "docker-compose.optimized.yml",
            "dockerfile_optimized": "Dockerfile.optimized",
            "dockerfile_secure": "Dockerfile.secure",
            "test_runner": "run_optimized_tests.py",
            "quick_start": "QUICK_START.md",
            "deployment_guide": "DEPLOYMENT_GUIDE.md",
            "security_notes": "SECURITY_NOTES.md",
            "optimization_summary": "OPTIMIZATION_SUMMARY.md",
            "env_minimal": ".env.minimal",
            "requirements_core": "requirements.core.txt",
            "requirements_ml": "requirements.ml.txt"
        }
        
        results = {"missing_files": [], "existing_files": []}
        
        for name, file_path in required_files.items():
            full_path = project_root / file_path
            if full_path.exists():
                results["existing_files"].append(name)
                logger.success(f"✅ {name}: {file_path}")
            else:
                results["missing_files"].append(name)
                logger.error(f"❌ {name}: {file_path} (missing)")
        
        results["success"] = len(results["missing_files"]) == 0
        results["total_files"] = len(required_files)
        results["found_files"] = len(results["existing_files"])
        
        return results
    
    def validate_docker_configuration(self) -> Dict[str, Any]:
        """Validate Docker configuration"""
        logger.info("Validating Docker configuration...")
        
        results = {
            "docker_compose": False,
            "dockerfile_optimized": False,
            "dockerfile_secure": False,
            "resource_limits": False,
            "health_checks": False
        }
        
        # Check docker-compose.optimized.yml
        compose_file = project_root / "docker-compose.optimized.yml"
        if compose_file.exists():
            content = compose_file.read_text()
            
            results["docker_compose"] = True
            logger.success("✅ docker-compose.optimized.yml exists")
            
            # Check for resource limits
            if "mem_limit:" in content and "cpus:" in content:
                results["resource_limits"] = True
                logger.success("✅ Resource limits configured")
            
            # Check for health checks
            if "healthcheck:" in content:
                results["health_checks"] = True
                logger.success("✅ Health checks configured")
        
        # Check Dockerfile.optimized
        dockerfile_opt = project_root / "Dockerfile.optimized"
        if dockerfile_opt.exists():
            content = dockerfile_opt.read_text()
            
            if "FROM python:" in content and "as base" in content:
                results["dockerfile_optimized"] = True
                logger.success("✅ Dockerfile.optimized (multi-stage)")
        
        # Check Dockerfile.secure
        dockerfile_secure = project_root / "Dockerfile.secure"
        if dockerfile_secure.exists():
            content = dockerfile_secure.read_text()
            
            if "alpine" in content.lower():
                results["dockerfile_secure"] = True
                logger.success("✅ Dockerfile.secure (Alpine Linux)")
        
        results["success"] = all([
            results["docker_compose"],
            results["dockerfile_optimized"],
            results["resource_limits"],
            results["health_checks"]
        ])
        
        return results
    
    async def validate_services_health(self) -> Dict[str, Any]:
        """Validate that services are running and healthy"""
        logger.info("Validating services health...")
        
        results = {
            "api_health": False,
            "api_detailed": False,
            "api_ready": False,
            "ui_health": False,
            "redis_connection": False,
            "ollama_connection": False
        }
        
        try:
            # Test API basic health
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                results["api_health"] = True
                logger.success("✅ API basic health check passed")
            
            # Test API detailed health
            response = requests.get(f"{self.base_url}/health/detailed", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                results["api_detailed"] = True
                logger.success("✅ API detailed health check passed")
                
                # Check critical components
                if health_data.get("status") == "healthy":
                    results["api_ready"] = True
                    logger.success("✅ API ready check passed")
            
            # Test UI health
            response = requests.get(f"{self.ui_url}/_stcore/health", timeout=10)
            if response.status_code == 200:
                results["ui_health"] = True
                logger.success("✅ UI health check passed")
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Service health check failed: {e}")
        
        # Test Redis connection
        try:
            redis_client = redis.from_url("redis://localhost:6379/0")
            await redis_client.ping()
            results["redis_connection"] = True
            logger.success("✅ Redis connection successful")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
        
        # Test Ollama connection
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=10)
            if response.status_code == 200:
                results["ollama_connection"] = True
                logger.success("✅ Ollama connection successful")
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Ollama connection failed: {e}")
        
        results["success"] = all([
            results["api_health"],
            results["api_ready"]
        ])
        
        return results
    
    def validate_optimization_features(self) -> Dict[str, Any]:
        """Validate optimization-specific features"""
        logger.info("Validating optimization features...")
        
        results = {
            "cache_module": False,
            "async_tasks_module": False,
            "metrics_module": False,
            "backup_service": False,
            "test_files": False
        }
        
        # Check core modules
        core_files = {
            "cache_module": "app/core/llm_cache.py",
            "async_tasks_module": "app/core/async_tasks.py",
            "metrics_module": "app/monitoring/business_metrics.py",
            "backup_service": "scripts/backup-service.py"
        }
        
        for feature, file_path in core_files.items():
            full_path = project_root / file_path
            if full_path.exists():
                content = full_path.read_text()
                
                # Check for key classes/functions
                if feature == "cache_module" and "LLMCacheManager" in content:
                    results[feature] = True
                    logger.success(f"✅ {feature} implemented")
                elif feature == "async_tasks_module" and "AsyncTaskManager" in content:
                    results[feature] = True
                    logger.success(f"✅ {feature} implemented")
                elif feature == "metrics_module" and "BusinessMetricsCollector" in content:
                    results[feature] = True
                    logger.success(f"✅ {feature} implemented")
                elif feature == "backup_service" and "BackupService" in content:
                    results[feature] = True
                    logger.success(f"✅ {feature} implemented")
        
        # Check test files
        test_files = [
            "tests/test_llm_cache.py",
            "tests/test_async_tasks.py", 
            "tests/test_business_metrics.py",
            "tests/test_backup_service.py",
            "tests/test_docker_optimized.py"
        ]
        
        test_files_exist = all((project_root / f).exists() for f in test_files)
        if test_files_exist:
            results["test_files"] = True
            logger.success("✅ All optimization test files exist")
        
        results["success"] = all([
            results["cache_module"],
            results["async_tasks_module"],
            results["metrics_module"],
            results["backup_service"],
            results["test_files"]
        ])
        
        return results
    
    def run_optimization_tests(self) -> Dict[str, Any]:
        """Run optimization-specific tests"""
        logger.info("Running optimization tests...")
        
        test_runner = project_root / "run_optimized_tests.py"
        
        if not test_runner.exists():
            return {
                "success": False,
                "error": "Test runner not found",
                "output": "run_optimized_tests.py not found"
            }
        
        try:
            # Run tests with timeout
            result = subprocess.run(
                [sys.executable, str(test_runner), "--timeout", "300"],
                capture_output=True,
                text=True,
                timeout=360  # 6 minutes total timeout
            )
            
            success = result.returncode == 0
            
            if success:
                logger.success("✅ All optimization tests passed")
            else:
                logger.error("❌ Some optimization tests failed")
            
            return {
                "success": success,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Tests timed out",
                "output": "Test execution timed out after 6 minutes"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": f"Test execution failed: {e}"
            }
    
    def validate_configuration_files(self) -> Dict[str, Any]:
        """Validate configuration files"""
        logger.info("Validating configuration files...")
        
        results = {
            "env_minimal": False,
            "requirements_core": False,
            "requirements_ml": False,
            "quick_start": False
        }
        
        # Check .env.minimal
        env_minimal = project_root / ".env.minimal"
        if env_minimal.exists():
            content = env_minimal.read_text()
            
            # Check for essential variables
            essential_vars = [
                "OLLAMA_BASE_URL",
                "GENERAL_MODEL", 
                "CODE_MODEL",
                "SECRET_KEY"
            ]
            
            if all(var in content for var in essential_vars):
                results["env_minimal"] = True
                logger.success("✅ .env.minimal has essential variables")
        
        # Check requirements files
        req_files = {
            "requirements_core": "requirements.core.txt",
            "requirements_ml": "requirements.ml.txt"
        }
        
        for req_name, req_file in req_files.items():
            full_path = project_root / req_file
            if full_path.exists():
                content = full_path.read_text()
                
                # Check for key packages
                if req_name == "requirements_core":
                    if "fastapi" in content and "crewai" in content:
                        results[req_name] = True
                        logger.success(f"✅ {req_file} has core dependencies")
                elif req_name == "requirements_ml":
                    if "torch" in content and "transformers" in content:
                        results[req_name] = True
                        logger.success(f"✅ {req_file} has ML dependencies")
        
        # Check QUICK_START.md
        quick_start = project_root / "QUICK_START.md"
        if quick_start.exists():
            content = quick_start.read_text()
            
            if "5 minutes" in content and "docker-compose" in content:
                results["quick_start"] = True
                logger.success("✅ QUICK_START.md has quick setup instructions")
        
        results["success"] = all([
            results["env_minimal"],
            results["requirements_core"],
            results["quick_start"]
        ])
        
        return results
    
    def generate_validation_report(self, results: Dict[str, Any]) -> None:
        """Generate comprehensive validation report"""
        total_time = time.time() - self.start_time
        
        # Calculate overall success
        validation_categories = list(results.keys())
        successful_categories = sum(1 for r in results.values() if r.get("success", False))
        
        overall_success = successful_categories == len(validation_categories)
        
        # Generate report
        report = f"""
# 🔍 Asmblr v2.0 Optimization Validation Report

## 📊 Executive Summary
- **Validation Categories**: {len(validation_categories)}
- **Passed Categories**: {successful_categories}
- **Failed Categories**: {len(validation_categories) - successful_categories}
- **Overall Status**: {'✅ PASSED' if overall_success else '❌ FAILED'}
- **Validation Duration**: {total_time:.2f} seconds

## 📋 Detailed Results

"""
        
        for category, result in results.items():
            status = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
            report += f"""
### {category.replace('_', ' ').title()} {status}
"""
            
            if category == "file_structure":
                report += f"""
- Total Files: {result.get('total_files', 0)}
- Found Files: {result.get('found_files', 0)}
- Missing Files: {len(result.get('missing_files', []))}
"""
                if result.get("missing_files"):
                    report += f"- Missing: {', '.join(result['missing_files'])}\n"
            
            elif category == "services_health":
                report += f"""
- API Health: {'✅' if result.get('api_health') else '❌'}
- API Ready: {'✅' if result.get('api_ready') else '❌'}
- UI Health: {'✅' if result.get('ui_health') else '❌'}
- Redis: {'✅' if result.get('redis_connection') else '❌'}
- Ollama: {'✅' if result.get('ollama_connection') else '❌'}
"""
            
            elif category == "optimization_tests":
                if result.get("success"):
                    report += "- All optimization tests passed successfully\n"
                else:
                    report += f"- Exit Code: {result.get('exit_code', 'N/A')}\n"
                    if result.get("stderr"):
                        report += f"- Error: {result.get('stderr', 'N/A')}\n"
            
            elif category == "docker_configuration":
                report += f"""
- Docker Compose: {'✅' if result.get('docker_compose') else '❌'}
- Dockerfile Optimized: {'✅' if result.get('dockerfile_optimized') else '❌'}
- Dockerfile Secure: {'✅' if result.get('dockerfile_secure') else '❌'}
- Resource Limits: {'✅' if result.get('resource_limits') else '❌'}
- Health Checks: {'✅' if result.get('health_checks') else '❌'}
"""
            
            elif category == "optimization_features":
                report += f"""
- LLM Cache Module: {'✅' if result.get('cache_module') else '❌'}
- Async Tasks Module: {'✅' if result.get('async_tasks_module') else '❌'}
- Business Metrics Module: {'✅' if result.get('metrics_module') else '❌'}
- Backup Service: {'✅' if result.get('backup_service') else '❌'}
- Test Files: {'✅' if result.get('test_files') else '❌'}
"""
            
            elif category == "configuration_files":
                report += f"""
- .env.minimal: {'✅' if result.get('env_minimal') else '❌'}
- requirements.core.txt: {'✅' if result.get('requirements_core') else '❌'}
- requirements.ml.txt: {'✅' if result.get('requirements_ml') else '❌'}
- QUICK_START.md: {'✅' if result.get('quick_start') else '❌'}
"""
        
        # Add recommendations
        if not overall_success:
            report += """
## 🔧 Recommendations

### For Failed Validations:
1. Check the detailed results above
2. Ensure all required files are present
3. Start the required services before validation
4. Install missing dependencies if needed
5. Run individual tests for detailed debugging

### Quick Fix Commands:
```bash
# Start services
docker-compose -f docker-compose.optimized.yml up -d

# Install dependencies
pip install -r requirements.core.txt

# Run individual validation
python validate_optimization.py --category file_structure
```
"""
        
        else:
            report += """
## 🎉 All Validations Passed!

Your Asmblr v2.0 optimization is fully functional and ready for production!

### Next Steps:
1. Deploy to production: docker-compose -f docker-compose.optimized.yml --profile monitoring --profile backup up -d
2. Monitor performance: http://localhost:3001 (Grafana)
3. Check health: curl http://localhost:8000/health/detailed
4. Run tests: python run_optimized_tests.py

"""
        
        # Write report to file
        report_file = project_root / "validation_report.md"
        report_file.write_text(report)
        
        # Print to console
        print(report)
        
        logger.info(f"Validation report saved to: {report_file}")
    
    async def run_full_validation(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        logger.info("Starting comprehensive validation of Asmblr v2.0 optimizations...")
        
        validation_steps = [
            ("file_structure", self.validate_file_structure),
            ("docker_configuration", self.validate_docker_configuration),
            ("configuration_files", self.validate_configuration_files),
            ("optimization_features", self.validate_optimization_features),
            ("services_health", await self.validate_services_health()),
            ("optimization_tests", self.run_optimization_tests())
        ]
        
        results = {}
        for step_name, step_func in validation_steps:
            try:
                results[step_name] = step_func
            except Exception as e:
                logger.error(f"Validation step {step_name} failed: {e}")
                results[step_name] = {"success": False, "error": str(e)}
        
        return results


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Validate Asmblr v2.0 optimizations")
    parser.add_argument("--category", 
                       choices=["file_structure", "docker_configuration", "services_health", 
                                "optimization_features", "optimization_tests", "configuration_files"],
                       help="Run specific validation category")
    parser.add_argument("--timeout", type=int, default=300,
                       help="Timeout for validation in seconds")
    parser.add_argument("--report-only", action="store_true",
                       help="Generate report only (if validation data exists)")
    
    args = parser.parse_args()
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    validator = OptimizationValidator()
    
    if args.report_only:
        logger.info("Generating report from existing validation data...")
        # This would require loading saved validation data
        logger.warning("Report-only mode not implemented yet")
        return
    
    if args.category:
        # Run specific validation category
        validation_methods = {
            "file_structure": validator.validate_file_structure,
            "docker_configuration": validator.validate_docker_configuration,
            "services_health": validator.validate_services_health,
            "optimization_features": validator.validate_optimization_features,
            "optimization_tests": validator.run_optimization_tests,
            "configuration_files": validator.validate_configuration_files
        }
        
        if args.category in validation_methods:
            method = validation_methods[args.category]
            if args.category == "services_health":
                result = await method()
            else:
                result = method()
            
            results = {args.category: result}
        else:
            logger.error(f"Unknown category: {args.category}")
            sys.exit(1)
    else:
        # Run full validation
        results = await validator.run_full_validation()
    
    # Generate report
    validator.generate_validation_report(results)
    
    # Exit with appropriate code
    failed_count = sum(1 for r in results.values() if not r.get("success", False))
    sys.exit(1 if failed_count > 0 else 0)


if __name__ == "__main__":
    asyncio.run(main())
