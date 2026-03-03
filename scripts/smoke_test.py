#!/usr/bin/env python3
"""
Smoke Tests for Asmblr Deployment
Basic functionality tests after deployment
"""

import argparse
import json
import sys
import time
from datetime import datetime

def test_api_health() -> bool:
    """Test API health endpoint"""
    print("Testing API health...")
    try:
        import subprocess
        result = subprocess.run([
            "curl", "-f", "-s", "http://localhost:8000/health"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ API health check passed")
            return True
        else:
            print("❌ API health check failed")
            return False
    except Exception as e:
        print(f"❌ API health check error: {e}")
        return False

def test_ui_health() -> bool:
    """Test Streamlit UI health"""
    print("Testing UI health...")
    try:
        import subprocess
        result = subprocess.run([
            "curl", "-f", "-s", "http://localhost:8501/_stcore/health"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ UI health check passed")
            return True
        else:
            print("❌ UI health check failed")
            return False
    except Exception as e:
        print(f"❌ UI health check error: {e}")
        return False

def test_redis_connection() -> bool:
    """Test Redis connection"""
    print("Testing Redis connection...")
    try:
        import subprocess
        result = subprocess.run([
            "redis-cli", "ping"
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and "PONG" in result.stdout:
            print("✅ Redis connection passed")
            return True
        else:
            print("❌ Redis connection failed")
            return False
    except Exception as e:
        print(f"❌ Redis connection error: {e}")
        return False

def test_basic_functionality() -> bool:
    """Test basic application functionality"""
    print("Testing basic functionality...")
    try:
        import subprocess
        # Test a simple API endpoint
        result = subprocess.run([
            "curl", "-f", "-s", "http://localhost:8000/readyz"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Basic functionality test passed")
            return True
        else:
            print("❌ Basic functionality test failed")
            return False
    except Exception as e:
        print(f"❌ Basic functionality test error: {e}")
        return False

def run_smoke_tests(env: str) -> int:
    """Run all smoke tests"""
    print(f"Running smoke tests for {env} environment...")
    
    tests = [
        ("API Health", test_api_health),
        ("UI Health", test_ui_health),
        ("Redis Connection", test_redis_connection),
        ("Basic Functionality", test_basic_functionality)
    ]
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "environment": env,
        "tests": {},
        "summary": {}
    }
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        success = test_func()
        results["tests"][test_name] = {
            "status": "pass" if success else "fail",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if success:
            passed += 1
        
        # Small delay between tests
        time.sleep(1)
    
    # Calculate summary
    results["summary"] = {
        "total_tests": total,
        "passed_tests": passed,
        "failed_tests": total - passed,
        "success_rate": round((passed / total) * 100, 1),
        "overall_status": "pass" if passed == total else "fail"
    }
    
    # Save results
    with open(f"smoke_test_results_{env}.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nSmoke Test Summary:")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {results['summary']['success_rate']}%")
    print(f"Overall Status: {results['summary']['overall_status']}")
    
    return 0 if passed == total else 1

def main():
    parser = argparse.ArgumentParser(description="Smoke Tests")
    parser.add_argument("--env", required=True, choices=["staging", "production"])
    
    args = parser.parse_args()
    
    return run_smoke_tests(args.env)

if __name__ == "__main__":
    sys.exit(main())
