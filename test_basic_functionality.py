#!/usr/bin/env python3
"""
Basic functionality test for Asmblr Phase 1 Stabilization
Tests core imports and basic functionality without Ollama
"""

import sys
import traceback
from pathlib import Path

def test_import(module_name, description):
    """Test importing a module"""
    try:
        __import__(module_name)
        print(f"✅ {description}")
        return True
    except Exception as e:
        print(f"❌ {description}: {e}")
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic functionality"""
    print("🚀 Testing Asmblr Basic Functionality")
    print("=" * 50)
    
    results = []
    
    # Test core imports
    results.append(test_import("app.core.config", "Core Configuration"))
    results.append(test_import("app.core.models", "Core Models"))
    results.append(test_import("app.cli", "CLI Module"))
    results.append(test_import("app.ui", "UI Module"))
    
    # Test settings
    try:
        from app.core.config import get_settings
        settings = get_settings()
        print(f"✅ Settings loaded - lightweight mode: {settings.lightweight_mode}")
        results.append(True)
    except Exception as e:
        print(f"❌ Settings failed: {e}")
        results.append(False)
    
    # Test basic paths
    try:
        from app.core.config import get_settings
        settings = get_settings()
        runs_dir = settings.runs_dir
        data_dir = settings.data_dir
        print(f"✅ Paths valid - runs: {runs_dir}, data: {data_dir}")
        results.append(True)
    except Exception as e:
        print(f"❌ Paths failed: {e}")
        results.append(False)
    
    # Test CLI help (without Ollama)
    try:
        import subprocess
        result = subprocess.run([sys.executable, "-m", "app", "--help"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ CLI help command works")
            results.append(True)
        else:
            print(f"❌ CLI help failed: {result.stderr}")
            results.append(False)
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic functionality tests passed!")
        print("✅ Phase 1 Stabilization: CORE SYSTEM STABLE")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed - needs fixes")
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
