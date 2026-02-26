"""
Tests simples et fonctionnels pour Asmblr
Focus sur les tests de smoke et les composants critiques existants
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch


class TestSmokeTests:
    """Tests de smoke pour vérifier le fonctionnement de base"""

    def test_import_core_modules(self):
        """Test que les modules core importent correctement"""
        try:
            from app.core.config import Settings
            from app.core.pipeline import VenturePipeline
            from app.core.llm import LLMClient
            assert True
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_settings_creation(self):
        """Test la création basique des Settings"""
        from app.core.config import Settings
        
        settings = Settings()
        assert hasattr(settings, 'ollama_base_url')
        assert hasattr(settings, 'general_model')
        assert hasattr(settings, 'default_n_ideas')

    def test_mvp_builder_import(self):
        """Test l'import du MVP Builder"""
        try:
            from app.mvp.builder import MVPBuilder
            assert True
        except ImportError as e:
            pytest.fail(f"MVP Builder import failed: {e}")

    def test_run_manager_import(self):
        """Test l'import du Run Manager"""
        try:
            from app.core.run_manager import RunManager
            assert True
        except ImportError as e:
            pytest.fail(f"Run Manager import failed: {e}")


class TestExistingFunctionality:
    """Tests pour la fonctionnalité existante"""

    def test_build_mvp_smoke(self, tmp_path):
        """Test le smoke de build MVP existant"""
        from tests.test_build_mvp import test_smoke_build_mvp_repo
        
        # Utiliser le test existant qui fonctionne
        try:
            test_smoke_build_mvp_repo(tmp_path, Mock())
            assert True
        except Exception as e:
            pytest.fail(f"Build MVP smoke test failed: {e}")

    def test_crewai_pipeline_smoke(self, tmp_path):
        """Test le smoke de la pipeline CrewAI"""
        from tests.test_crewai_pipeline import test_crewai_pipeline_smoke
        
        try:
            test_crewai_pipeline_smoke(tmp_path, Mock())
            assert True
        except Exception as e:
            pytest.fail(f"CrewAI pipeline smoke test failed: {e}")


class TestConfigBasic:
    """Tests basiques pour la configuration"""

    def test_config_has_required_fields(self):
        """Test que la config a les champs requis"""
        from app.core.config import Settings
        
        settings = Settings()
        
        required_fields = [
            'ollama_base_url',
            'general_model', 
            'default_n_ideas',
            'max_sources'
        ]
        
        for field in required_fields:
            assert hasattr(settings, field), f"Missing required field: {field}"

    def test_config_values_are_reasonable(self):
        """Test que les valeurs de config sont raisonnables"""
        from app.core.config import Settings
        
        settings = Settings()
        
        assert settings.ollama_base_url.startswith('http')
        assert len(settings.general_model) > 0
        assert settings.default_n_ideas > 0
        assert settings.max_sources > 0


class TestFileStructure:
    """Tests pour la structure des fichiers"""

    def test_required_files_exist(self):
        """Test que les fichiers requis existent"""
        base_dir = Path(__file__).parent.parent
        
        required_files = [
            'app/core/config.py',
            'app/core/pipeline.py',
            'app/core/llm.py',
            'requirements.txt',
            'README.md',
            'docker-compose.yml'
        ]
        
        for file_path in required_files:
            full_path = base_dir / file_path
            assert full_path.exists(), f"Required file missing: {file_path}"

    def test_directories_exist(self):
        """Test que les répertoires requis existent"""
        base_dir = Path(__file__).parent.parent
        
        required_dirs = [
            'app',
            'app/core',
            'app/mvp',
            'tests',
            'configs'
        ]
        
        for dir_path in required_dirs:
            full_path = base_dir / dir_path
            assert full_path.exists(), f"Required directory missing: {dir_path}"
            assert full_path.is_dir(), f"Path is not a directory: {dir_path}"


class TestBasicFunctionality:
    """Tests de fonctionnalité de base"""

    def test_doctor_import(self):
        """Test que le module doctor peut être importé"""
        try:
            from app.core.doctor import doctor
            assert True
        except ImportError as e:
            pytest.fail(f"Doctor import failed: {e}")

    def test_main_import(self):
        """Test que le module main peut être importé"""
        try:
            from app.main import app
            assert True
        except ImportError as e:
            pytest.fail(f"Main import failed: {e}")

    def test_ui_import(self):
        """Test que le module UI peut être importé"""
        try:
            import app.ui
            assert True
        except ImportError as e:
            pytest.fail(f"UI import failed: {e}")


class TestErrorHandling:
    """Tests de gestion d'erreurs"""

    def test_missing_env_handling(self):
        """Test la gestion des variables d'environnement manquantes"""
        from app.core.config import Settings
        
        # Devrait fonctionner même sans variables d'environnement spéciales
        settings = Settings()
        assert settings.ollama_base_url is not None
        assert settings.general_model is not None

    def test_invalid_config_handling(self):
        """Test la gestion de configuration invalide"""
        # Test avec des valeurs qui pourraient être problématiques
        from app.core.config import Settings
        
        settings = Settings()
        
        # Les valeurs devraient toujours être valides
        assert isinstance(settings.ollama_base_url, str)
        assert isinstance(settings.general_model, str)
        assert isinstance(settings.default_n_ideas, int)


class TestPerformance:
    """Tests de performance basiques"""

    def test_settings_creation_performance(self):
        """Test la performance de création des Settings"""
        import time
        from app.core.config import Settings
        
        start_time = time.time()
        
        # Créer plusieurs instances pour tester la performance
        for _ in range(100):
            settings = Settings()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Devrait être rapide (< 1 seconde pour 100 créations)
        assert duration < 1.0, f"Settings creation too slow: {duration}s"

    def test_import_performance(self):
        """Test la performance des imports"""
        import time
        import importlib
        
        start_time = time.time()
        
        # Importer plusieurs modules critiques
        modules = [
            'app.core.config',
            'app.core.pipeline', 
            'app.core.llm',
            'app.mvp.builder'
        ]
        
        for module in modules:
            importlib.import_module(module)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Les imports devraient être raisonnables
        assert duration < 5.0, f"Module imports too slow: {duration}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
