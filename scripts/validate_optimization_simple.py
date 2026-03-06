#!/usr/bin/env python3
"""
Simple Validation Script for Asmblr v2.0 Optimizations
Quick validation of key components without complex formatting
"""

import asyncio
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class SimpleValidator:
    """Simple validator for Asmblr v2.0 optimizations"""
    
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
    
    def check_files(self) -> Dict[str, Any]:
        """Check that all required files exist"""
        print("🔍 Checking required files...")
        
        required_files = [
            "app/core/llm_cache.py",
            "app/core/async_tasks.py", 
            "app/monitoring/business_metrics.py",
            "scripts/backup-service.py",
            "docker-compose.optimized.yml",
            "Dockerfile.optimized",
            "Dockerfile.secure",
            "run_optimized_tests.py",
            "QUICK_START.md",
            "DEPLOYMENT_GUIDE.md",
            ".env.minimal",
            "requirements.core.txt"
        ]
        
        results = {"missing": [], "found": []}
        
        for file_path in required_files:
            full_path = project_root / file_path
            if full_path.exists():
                results["found"].append(file_path)
                print(f"✅ {file_path}")
            else:
                results["missing"].append(file_path)
                print(f"❌ {file_path} (missing)")
        
        results["success"] = len(results["missing"]) == 0
        return results
    
    def check_docker(self) -> Dict[str, Any]:
        """Check Docker configuration"""
        print("\n🐳 Checking Docker configuration...")
        
        results = {
            "compose_file": False,
            "dockerfile_opt": False,
            "dockerfile_secure": False
        }
        
        # Check docker-compose
        compose_file = project_root / "docker-compose.optimized.yml"
        if compose_file.exists():
            results["compose_file"] = True
            print("✅ docker-compose.optimized.yml")
            
            # Quick content check
            content = compose_file.read_text()
            if "mem_limit:" in content:
                print("✅ Resource limits configured")
            if "healthcheck:" in content:
                print("✅ Health checks configured")
        
        # Check Dockerfiles
        dockerfile_opt = project_root / "Dockerfile.optimized"
        if dockerfile_opt.exists():
            results["dockerfile_opt"] = True
            print("✅ Dockerfile.optimized")
        
        dockerfile_secure = project_root / "Dockerfile.secure"
        if dockerfile_secure.exists():
            results["dockerfile_secure"] = True
            print("✅ Dockerfile.secure")
        
        results["success"] = all([
            results["compose_file"],
            results["dockerfile_optimized"]
        ])
        
        return results
    
    def check_tests(self) -> Dict[str, Any]:
        """Check test files"""
        print("\n🧪 Checking test files...")
        
        test_files = [
            "tests/test_llm_cache.py",
            "tests/test_async_tasks.py",
            "tests/test_business_metrics.py",
            "tests/test_backup_service.py",
            "tests/test_docker_optimized.py"
        ]
        
        results = {"missing": [], "found": []}
        
        for test_file in test_files:
            full_path = project_root / test_file
            if full_path.exists():
                results["found"].append(test_file)
                print(f"✅ {test_file}")
            else:
                results["missing"].append(test_file)
                print(f"❌ {test_file} (missing)")
        
        results["success"] = len(results["missing"]) == 0
        return results
    
    def run_quick_tests(self) -> Dict[str, Any]:
        """Run quick tests"""
        print("\n🚀 Running quick tests...")
        
        test_runner = project_root / "run_optimized_tests.py"
        
        if not test_runner.exists():
            return {
                "success": False,
                "error": "Test runner not found"
            }
        
        try:
            # Try to run a simple syntax check
            result = subprocess.run(
                [sys.executable, str(test_runner), "--help"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            
            if success:
                print("✅ Test runner is functional")
            else:
                print("⚠️ Test runner may have issues")
            
            return {
                "success": success,
                "exit_code": result.returncode
            }
            
        except Exception as e:
            print(f"❌ Test runner check failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_simple_report(self, results: Dict[str, Any]) -> None:
        """Generate simple validation report"""
        total_time = time.time() - self.start_time
        
        # Calculate overall success
        categories = list(results.keys())
        successful = sum(1 for r in results.values() if r.get("success", False))
        
        print(f"\n{'='*60}")
        print("🔍 ASMblr v2.0 Validation Report")
        print(f"{'='*60}")
        print(f"Time: {total_time:.2f}s")
        print(f"Categories: {successful}/{len(categories)} passed")
        
        if successful == len(categories):
            print("\n🎉 ALL VALIDATIONS PASSED!")
            print("\nYour Asmblr v2.0 optimization is ready!")
            print("\nNext steps:")
            print("1. Start services: docker-compose -f docker-compose.optimized.yml up -d")
            print("2. Check health: curl http://localhost:8000/health")
            print("3. Run tests: python run_optimized_tests.py")
        else:
            print(f"\n❌ {len(categories) - successful} validation(s) failed")
            print("\nPlease check the missing components above.")
        
        print(f"{'='*60}")
    
    def run_validation(self) -> bool:
        """Run complete validation"""
        print("🚀 Starting Asmblr v2.0 validation...")
        
        all_results = {}
        
        # Run all checks
        all_results["files"] = self.check_files()
        all_results["docker"] = self.check_docker()
        all_results["tests"] = self.check_tests()
        all_results["test_runner"] = self.run_quick_tests()
        
        # Generate report
        self.generate_simple_report(all_results)
        
        # Return overall success
        overall_success = all(r.get("success", False) for r in all_results.values())
        return overall_success


def main():
    """Main function"""
    validator = SimpleValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
