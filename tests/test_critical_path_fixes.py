"""
Tests to verify critical path reference bugs after cleanup
"""
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestCriticalPathFixes:
    """Test critical path references after cleanup"""
    
    def test_env_example_path_references(self):
        """Test that .env.example references point to correct location"""
        # Check doctor.py specifically
        doctor_file = project_root / "app" / "core" / "doctor.py"
        assert doctor_file.exists(), "doctor.py should exist"
        
        content = doctor_file.read_text(encoding='utf-8')
        
        # Should reference config/.env.example (check for the pattern with Path operations)
        assert '"config" / ".env.example"' in content, "Should reference config/.env.example"
        
        # Should not reference root .env.example directly
        lines = content.split('\n')
        root_env_refs = []
        for line in lines:
            if '.env.example' in line and '"config"' not in line:
                root_env_refs.append(line.strip())
        
        assert len(root_env_refs) == 0, f"Found root .env.example references: {root_env_refs}"
    
    def test_env_file_exists_in_config(self):
        """Test that .env.example exists in config directory"""
        env_example = project_root / "config" / ".env.example"
        assert env_example.exists(), ".env.example should exist in config directory"
        
        # Should not exist in root
        root_env = project_root / ".env.example"
        assert not root_env.exists(), ".env.example should not exist in root directory"
    
    def test_requirements_txt_path_references(self):
        """Test that requirements.txt references point to correct location"""
        # Check for old path references in scripts and setup files
        py_files = list(project_root.rglob("*.py"))
        
        old_path_refs = []
        new_path_refs = []
        
        for py_file in py_files:
            # Skip test files and files that are legitimately generating requirements.txt for MVPs
            if ("test_" in str(py_file) or 
                any(skip in str(py_file) for skip in ["mvp_", "repo_generator", "project_build"]) or
                "enhanced_builder.py" in str(py_file)):  # Skip MVP builders
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Check for old pip install commands (these are definitely wrong)
                if 'pip install -r requirements.txt' in content and 'requirements/requirements.txt' not in content:
                    old_path_refs.append(str(py_file.relative_to(project_root)))
                
                # Check for old file existence checks that should use new path
                if "'requirements.txt'" in content or '"requirements.txt"' in content:
                    lines = content.split('\n')
                    for line in lines:
                        if ('requirements.txt' in line and 
                            'requirements/requirements.txt' not in line and
                            'pip install' not in line and
                            'write_text' not in line and
                            'COPY' not in line):  # Skip legitimate file creation
                            old_path_refs.append(f"{py_file.relative_to(project_root)}: {line.strip()}")
                
                # Check for new path references
                if 'requirements/requirements.txt' in content:
                    new_path_refs.append(str(py_file.relative_to(project_root)))
                    
            except Exception as e:
                # Skip files that can't be read
                continue
        
        # Should have no old path references
        assert len(old_path_refs) == 0, f"Found old requirements.txt references: {old_path_refs}"
        
        # Should have some new path references
        assert len(new_path_refs) > 0, "Should have some requirements/requirements.txt references"
    
    def test_requirements_files_exist(self):
        """Test that requirements files exist in requirements directory"""
        requirements_dir = project_root / "requirements"
        assert requirements_dir.exists(), "requirements directory should exist"
        
        main_requirements = requirements_dir / "requirements.txt"
        assert main_requirements.exists(), "requirements.txt should exist in requirements directory"
        
        # Should not exist in root
        root_requirements = project_root / "requirements.txt"
        assert not root_requirements.exists(), "requirements.txt should not exist in root directory"
    
    def test_script_imports(self):
        """Test that script imports are correctly updated"""
        # Check for common script imports
        py_files = list(project_root.rglob("*.py"))
        
        broken_imports = []
        
        for py_file in py_files:
            # Skip test files and scripts directory (they're the source)
            if "test_" in str(py_file) or "scripts/" in str(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Check for direct imports of moved scripts
                if 'from asmblr_cli import' in content:
                    broken_imports.append(f"{py_file}: imports asmblr_cli directly")
                
                if 'from ui import' in content and 'app/ui' not in content:
                    broken_imports.append(f"{py_file}: imports ui directly")
                    
            except Exception:
                continue
        
        # Should have no broken script imports
        assert len(broken_imports) == 0, f"Found broken script imports: {broken_imports}"
    
    def test_dockerfile_references(self):
        """Test that Dockerfiles reference correct paths"""
        docker_files = list(project_root.rglob("Dockerfile*"))
        
        broken_docker_refs = []
        
        for docker_file in docker_files:
            try:
                content = docker_file.read_text(encoding='utf-8')
                
                # Check for old requirements path
                if 'COPY requirements.txt' in content:
                    broken_docker_refs.append(f"{docker_file}: references requirements.txt in root")
                
                # Check for old env path
                if '.env.example' in content and 'config/.env.example' not in content:
                    broken_docker_refs.append(f"{docker_file}: references .env.example in root")
                    
            except Exception:
                continue
        
        # Should have no broken Docker references
        assert len(broken_docker_refs) == 0, f"Found broken Docker references: {broken_docker_refs}"
    
    def test_application_startup(self):
        """Test that application can start up without import errors"""
        # Test basic config import
        try:
            from app.core.config import get_settings
            settings = get_settings()
            assert settings is not None, "Should be able to get settings"
        except ImportError as e:
            pytest.fail(f"Failed to import config: {e}")
    
    def test_cli_import(self):
        """Test that CLI can be imported"""
        try:
            from scripts.asmblr_cli import AsmblrCLI
            assert AsmblrCLI is not None, "Should be able to import CLI"
        except ImportError as e:
            pytest.fail(f"Failed to import CLI: {e}")
    
    def test_ui_import(self):
        """Test that UI can be imported"""
        try:
            # Import the UI module
            sys.path.insert(0, str(project_root / "scripts"))
            import ui
            assert ui is not None, "Should be able to import UI"
        except ImportError as e:
            pytest.fail(f"Failed to import UI: {e}")
    
    def test_doctor_functionality(self):
        """Test that doctor functionality works with new paths"""
        try:
            from app.core.doctor import run_doctor, DoctorResult
            from app.core.config import get_settings
            
            settings = get_settings()
            result = run_doctor(settings)
            
            assert isinstance(result, DoctorResult), "Should return DoctorResult"
            assert result.report is not None, "Should have a report"
            
        except Exception as e:
            pytest.fail(f"Doctor functionality failed: {e}")


class TestSubprocessCommands:
    """Test subprocess commands with updated paths"""
    
    def test_pip_install_command(self):
        """Test that pip install commands use correct paths"""
        # Check scripts that use pip install
        script_files = list((project_root / "scripts").rglob("*.py"))
        
        broken_commands = []
        
        for script_file in script_files:
            try:
                content = script_file.read_text(encoding='utf-8')
                
                # Check for old pip install commands
                if 'pip install -r requirements.txt' in content:
                    broken_commands.append(f"{script_file}: uses old requirements.txt path")
                    
            except Exception:
                continue
        
        # Should have no broken pip commands
        assert len(broken_commands) == 0, f"Found broken pip commands: {broken_commands}"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
