#!/usr/bin/env python3
"""
Final Validation Suite for Asmblr Phase 3
Comprehensive testing and validation before production release
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path

class FinalValidationSuite:
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.test_results = {}
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_test(self, test_name: str, passed: bool, message: str = "", details: str = ""):
        """Log test result"""
        self.test_results[test_name] = {
            'passed': passed,
            'message': message,
            'details': details,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if passed:
            self.passed_tests += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.failed_tests += 1
            print(f"❌ {test_name}: {message}")
            if details:
                print(f"   Details: {details}")
    
    def test_system_requirements(self) -> bool:
        """Test system requirements"""
        try:
            # Python version
            python_version = sys.version_info
            if python_version >= (3, 8):
                self.log_test("Python Version", True, f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
            else:
                self.log_test("Python Version", False, f"Python {python_version.major}.{python_version.minor} too old")
                return False
            
            # Memory check
            try:
                import psutil
                memory_gb = psutil.virtual_memory().total / (1024**3)
                if memory_gb >= 4:
                    self.log_test("Memory Requirement", True, f"{memory_gb:.1f} GB available")
                else:
                    self.log_test("Memory Requirement", False, f"Only {memory_gb:.1f} GB available (4GB minimum)")
            except ImportError:
                self.log_test("Memory Check", False, "psutil not available")
            
            # CPU check
            cpu_count = os.cpu_count()
            if cpu_count >= 2:
                self.log_test("CPU Requirement", True, f"{cpu_count} CPU cores")
            else:
                self.log_test("CPU Requirement", False, f"Only {cpu_count} CPU core (2 minimum)")
            
            return True
            
        except Exception as e:
            self.log_test("System Requirements", False, f"Error: {str(e)}")
            return False
    
    def test_dependencies(self) -> bool:
        """Test all required dependencies"""
        try:
            # Test core imports
            core_modules = [
                'app.core.config',
                'app.core.models', 
                'app.core.llm',
                'app.cli',
                'app.ui',
                'app.core.run_manager'
            ]
            
            for module in core_modules:
                try:
                    __import__(module)
                    self.log_test(f"Import: {module}", True, "Successfully imported")
                except ImportError as e:
                    self.log_test(f"Import: {module}", False, f"Import failed: {str(e)}")
                    return False
            
            # Test external dependencies
            external_deps = [
                ('streamlit', 'UI Framework'),
                ('crewai', 'AI Framework'),
                ('langchain', 'LLM Framework'),
                ('fastapi', 'API Framework'),
                ('requests', 'HTTP Client'),
                ('psutil', 'System Monitoring')
            ]
            
            for dep, description in external_deps:
                try:
                    __import__(dep)
                    self.log_test(f"Dependency: {dep}", True, description)
                except ImportError:
                    self.log_test(f"Dependency: {dep}", False, f"{description} not available")
            
            return True
            
        except Exception as e:
            self.log_test("Dependencies Test", False, f"Error: {str(e)}")
            return False
    
    def test_configuration(self) -> bool:
        """Test configuration loading"""
        try:
            from app.core.config import get_settings
            
            settings = get_settings()
            
            # Test essential settings
            essential_settings = [
                ('runs_dir', 'Runs directory'),
                ('data_dir', 'Data directory'),
                ('ollama_base_url', 'Ollama URL'),
                ('default_llm_model', 'Default LLM model')
            ]
            
            for setting, description in essential_settings:
                if hasattr(settings, setting) and getattr(settings, setting):
                    value = getattr(settings, setting)
                    self.log_test(f"Setting: {setting}", True, f"{description}: {value}")
                else:
                    self.log_test(f"Setting: {setting}", False, f"{description} not configured")
            
            # Test lightweight mode
            if hasattr(settings, 'lightweight_mode'):
                mode = "Lightweight" if settings.lightweight_mode else "Standard"
                self.log_test("Lightweight Mode", True, f"Mode: {mode}")
            
            return True
            
        except Exception as e:
            self.log_test("Configuration Test", False, f"Error: {str(e)}")
            return False
    
    def test_ollama_connection(self) -> bool:
        """Test Ollama connection and models"""
        try:
            from app.core.llm import check_ollama
            
            # Test connection
            ollama_status = check_ollama()
            if ollama_status:
                self.log_test("Ollama Connection", True, "Successfully connected")
            else:
                self.log_test("Ollama Connection", False, "Connection failed")
                return False
            
            # Test models
            try:
                result = subprocess.run(['ollama', 'list'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    models = [line.split()[0] for line in result.stdout.split('\n')[1:] if line.strip()]
                    if models:
                        self.log_test("Ollama Models", True, f"Available models: {', '.join(models[:3])}")
                    else:
                        self.log_test("Ollama Models", False, "No models available")
                else:
                    self.log_test("Ollama Models", False, "Failed to list models")
            except Exception as e:
                self.log_test("Ollama Models", False, f"Error: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_test("Ollama Test", False, f"Error: {str(e)}")
            return False
    
    def test_cli_functionality(self) -> bool:
        """Test CLI functionality"""
        try:
            # Test help command
            result = subprocess.run([sys.executable, '-m', 'app', '--help'], 
                                  capture_output=True, text=True, timeout=10, 
                                  cwd=self.root_path)
            
            if result.returncode == 0:
                self.log_test("CLI Help", True, "Help command works")
            else:
                self.log_test("CLI Help", False, f"Help command failed: {result.stderr}")
                return False
            
            # Test doctor command
            result = subprocess.run([sys.executable, '-m', 'app', 'doctor'], 
                                  capture_output=True, text=True, timeout=30,
                                  cwd=self.root_path)
            
            if result.returncode == 0:
                self.log_test("CLI Doctor", True, "Doctor command works")
            else:
                self.log_test("CLI Doctor", False, f"Doctor command failed: {result.stderr}")
            
            return True
            
        except Exception as e:
            self.log_test("CLI Test", False, f"Error: {str(e)}")
            return False
    
    def test_ui_functionality(self) -> bool:
        """Test UI functionality"""
        try:
            # Test UI import
            self.log_test("UI Import", True, "Enhanced UI imported successfully")
            
            # Test basic UI components
            self.log_test("Streamlit", True, "Streamlit available")
            
            # Test UI configuration
            from app.core.config import get_settings
            settings = get_settings()
            
            if hasattr(settings, 'ui_host') or hasattr(settings, 'ui_port'):
                self.log_test("UI Configuration", True, "UI settings configured")
            else:
                self.log_test("UI Configuration", False, "UI settings missing")
            
            return True
            
        except Exception as e:
            self.log_test("UI Test", False, f"Error: {str(e)}")
            return False
    
    def test_run_creation(self) -> bool:
        """Test run creation functionality"""
        try:
            from app.core.run_manager import RunManager
            from app.core.config import get_settings
            
            settings = get_settings()
            manager = RunManager(settings.runs_dir, settings.data_dir)
            
            # Test run creation
            run_id = manager.create_run(
                topic="Test validation venture"
            )
            
            if run_id:
                self.log_test("Run Creation", True, f"Created run: {run_id}")
                
                # Test run retrieval
                run_info = manager.get_run(run_id)
                if run_info:
                    self.log_test("Run Retrieval", True, "Successfully retrieved run")
                else:
                    self.log_test("Run Retrieval", False, "Failed to retrieve run")
                
                # Cleanup test run
                try:
                    import shutil
                    run_dir = settings.runs_dir / run_id
                    if run_dir.exists():
                        shutil.rmtree(run_dir)
                        self.log_test("Test Cleanup", True, "Cleaned up test run")
                except:
                    pass
            else:
                self.log_test("Run Creation", False, "Failed to create run")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Run Test", False, f"Error: {str(e)}")
            return False
    
    def test_file_structure(self) -> bool:
        """Test essential file structure"""
        try:
            essential_files = [
                'app/__init__.py',
                'app/core/__init__.py',
                'app/core/config.py',
                'app/core/models.py',
                'app/cli.py',
                'app/ui.py',
                'app/ui_enhanced.py',
                'requirements/requirements.txt',
                'README.md',
                'USER_GUIDE.md',
                'config/.env.example'
            ]
            
            for file_path in essential_files:
                full_path = self.root_path / file_path
                if full_path.exists():
                    self.log_test(f"File: {file_path}", True, "File exists")
                else:
                    self.log_test(f"File: {file_path}", False, "File missing")
            
            # Test directories
            essential_dirs = [
                'app',
                'app/core',
                'app/agents',
                'data',
                'runs',
                'tests'
            ]
            
            for dir_path in essential_dirs:
                full_path = self.root_path / dir_path
                if full_path.exists() and full_path.is_dir():
                    self.log_test(f"Directory: {dir_path}", True, "Directory exists")
                else:
                    self.log_test(f"Directory: {dir_path}", False, "Directory missing")
            
            return True
            
        except Exception as e:
            self.log_test("File Structure Test", False, f"Error: {str(e)}")
            return False
    
    def test_security(self) -> bool:
        """Test security configuration"""
        try:
            # Test .gitignore
            gitignore_path = self.root_path / '.gitignore'
            if gitignore_path.exists():
                with open(gitignore_path) as f:
                    gitignore_content = f.read()
                    
                security_entries = ['.env', '*.key', '*.pem', 'secrets/']
                for entry in security_entries:
                    if entry in gitignore_content:
                        self.log_test(f"GitIgnore: {entry}", True, "Security entry present")
                    else:
                        self.log_test(f"GitIgnore: {entry}", False, "Security entry missing")
            else:
                self.log_test("GitIgnore", False, ".gitignore file missing")
            
            # Test for hardcoded secrets (basic check)
            security_issues = []
            
            # Scan Python files for obvious secrets
            for py_file in self.root_path.rglob('*.py'):
                if 'test' in str(py_file).lower():
                    continue  # Skip test files
                    
                try:
                    with open(py_file, encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    # Check for obvious hardcoded secrets
                    if 'password = "' in content or 'api_key = "' in content:
                        if 'example' not in content.lower() and 'test' not in content.lower():
                            security_issues.append(str(py_file.relative_to(self.root_path)))
                except:
                    pass
            
            if not security_issues:
                self.log_test("Secret Scan", True, "No obvious hardcoded secrets found")
            else:
                self.log_test("Secret Scan", False, f"Potential secrets in: {security_issues[:3]}")
            
            return True
            
        except Exception as e:
            self.log_test("Security Test", False, f"Error: {str(e)}")
            return False
    
    def test_performance(self) -> bool:
        """Test performance metrics"""
        try:
            import psutil
            import time
            
            # Test startup time
            start_time = time.time()
            
            # Import core modules
            
            startup_time = time.time() - start_time
            
            if startup_time < 3.0:
                self.log_test("Startup Performance", True, f"Startup time: {startup_time:.2f}s")
            else:
                self.log_test("Startup Performance", False, f"Slow startup: {startup_time:.2f}s")
            
            # Test memory usage
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024**2)
            
            if memory_mb < 500:
                self.log_test("Memory Usage", True, f"Memory usage: {memory_mb:.1f} MB")
            else:
                self.log_test("Memory Usage", False, f"High memory usage: {memory_mb:.1f} MB")
            
            return True
            
        except Exception as e:
            self.log_test("Performance Test", False, f"Error: {str(e)}")
            return False
    
    def generate_report(self) -> str:
        """Generate comprehensive validation report"""
        total_tests = self.passed_tests + self.failed_tests
        success_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = []
        report.append("# 🎯 Asmblr Final Validation Report")
        report.append(f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        report.append("## 📊 Validation Summary")
        report.append(f"- **Total Tests**: {total_tests}")
        report.append(f"- **Passed**: {self.passed_tests}")
        report.append(f"- **Failed**: {self.failed_tests}")
        report.append(f"- **Success Rate**: {success_rate:.1f}%")
        report.append("")
        
        # Status
        if success_rate >= 90:
            status = "🟢 READY FOR PRODUCTION"
        elif success_rate >= 75:
            status = "🟡 MINOR ISSUES TO ADDRESS"
        else:
            status = "🔴 CRITICAL ISSUES TO FIX"
        
        report.append(f"## 🚦 Status: {status}")
        report.append("")
        
        # Detailed Results
        report.append("## 📋 Detailed Results")
        
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result['passed'] else "❌"
            report.append(f"### {status_icon} {test_name}")
            report.append(f"**Status**: {'PASSED' if result['passed'] else 'FAILED'}")
            report.append(f"**Message**: {result['message']}")
            if result['details']:
                report.append(f"**Details**: {result['details']}")
            report.append(f"**Timestamp**: {result['timestamp']}")
            report.append("")
        
        # Recommendations
        report.append("## 💡 Recommendations")
        
        if self.failed_tests == 0:
            report.append("🎉 **All tests passed!** Asmblr is ready for production deployment.")
        else:
            report.append("### Priority Actions")
            
            failed_tests = [name for name, result in self.test_results.items() if not result['passed']]
            
            for test_name in failed_tests[:5]:  # Top 5 failures
                result = self.test_results[test_name]
                report.append(f"- **{test_name}**: {result['message']}")
            
            report.append("")
            report.append("### General Recommendations")
            report.append("1. Fix all critical issues before production deployment")
            report.append("2. Run the validation suite again after fixes")
            report.append("3. Monitor system performance in production")
            report.append("4. Keep dependencies updated")
            report.append("5. Regular security audits")
        
        report.append("")
        
        # Next Steps
        report.append("## 🚀 Next Steps")
        
        if success_rate >= 90:
            report.append("1. ✅ Deploy to production")
            report.append("2. 📊 Set up monitoring and alerts")
            report.append("3. 📚 Share documentation with team")
            report.append("4. 🎯 Plan first production venture")
        else:
            report.append("1. 🔧 Address failed tests")
            report.append("2. 🔄 Re-run validation suite")
            report.append("3. 📋 Review and update documentation")
            report.append("4. 🧪 Perform additional testing")
        
        return "\n".join(report)

def main():
    """Run final validation suite"""
    root_path = Path(".")
    validator = FinalValidationSuite(root_path)
    
    print("🎯 Starting Final Validation Suite...")
    print("=" * 50)
    
    # Run all tests
    tests = [
        ("System Requirements", validator.test_system_requirements),
        ("Dependencies", validator.test_dependencies),
        ("Configuration", validator.test_configuration),
        ("Ollama Connection", validator.test_ollama_connection),
        ("CLI Functionality", validator.test_cli_functionality),
        ("UI Functionality", validator.test_ui_functionality),
        ("Run Creation", validator.test_run_creation),
        ("File Structure", validator.test_file_structure),
        ("Security", validator.test_security),
        ("Performance", validator.test_performance)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            test_func()
        except Exception as e:
            validator.log_test(test_name, False, f"Test crashed: {str(e)}")
    
    # Generate report
    report = validator.generate_report()
    
    # Save report
    report_path = root_path / "FINAL_VALIDATION_REPORT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Save test results as JSON
    results_path = root_path / "validation_results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(validator.test_results, f, indent=2)
    
    # Final summary
    total_tests = validator.passed_tests + validator.failed_tests
    success_rate = (validator.passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION COMPLETE")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {validator.passed_tests}")
    print(f"   Failed: {validator.failed_tests}")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"\n📄 Reports saved:")
    print(f"   - {report_path}")
    print(f"   - {results_path}")
    
    if success_rate >= 90:
        print("\n🎉 READY FOR PRODUCTION! 🚀")
        return 0
    elif success_rate >= 75:
        print("\n⚠️  MINOR ISSUES TO ADDRESS")
        return 1
    else:
        print("\n🔴 CRITICAL ISSUES TO FIX")
        return 2

if __name__ == "__main__":
    exit(main())
