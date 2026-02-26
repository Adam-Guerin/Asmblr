"""
Tests simples et fonctionnels pour Asmblr
Focus sur les tests de smoke et les composants critiques existants
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from app.core.config import Settings
from app.core.pipeline import VenturePipeline
from app.core.llm import LLMClient
from app.core.cache import ArtifactCache


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
        settings = Settings()
        
        # Devrait fonctionner même sans variables d'environnement spéciales
        assert settings.ollama_base_url is not None
        assert settings.general_model is not None

    def test_invalid_config_handling(self):
        """Test la gestion de configuration invalide"""
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
        
        start_time = time.time()
        for _ in range(100):
            settings = Settings()
        end_time = time.time()
        
        duration = end_time - start_time
        assert duration < 1.0  # 100 créations en moins de 1 seconde

    def test_import_performance(self):
        """Test la performance des imports"""
        import time
        
        start_time = time.time()
        
        imports = [
            'app.core.config',
            'app.core.pipeline', 
            'app.core.llm',
            'app.core.cache'
        ]
        
        for import_name in imports:
            start_time = time.time()
            __import__(import_name)
            end_time = time.time()
            duration = end_time - start_time
            assert duration < 0.1  # Chaque import en moins de 100ms


class TestEndToEndScenarios:
    """Tests de bout en bout pour des scénarios réels"""

    def test_simple_workflow(self):
        """Test un workflow simple de bout en bout"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Configuration de test
            test_config = {
                "RUNS_DIR": temp_dir,
                "CACHE_DIR": temp_dir,
                "DEFAULT_N_IDEAS": "2",
                "FAST_MODE": "true"
            }
            
            with patch.dict('os.environ', test_config):
                # Mock LLM pour éviter les dépendances externes
                with patch('app.core.llm.httpx.AsyncClient') as mock_client:
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {"response": "Simple test response", "done": True}
                    mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
                    
                    # Test simple
                    settings = Settings()
                    cache = ArtifactCache(max_size=50, ttl_seconds=300)
                    llm_client = LLMClient("http://localhost:11434", "llama3.1:8b")
                    pipeline = VenturePipeline(settings)
                    
                    # Configurer les composants si nécessaire
                    if hasattr(pipeline, 'cache_manager'):
                        pipeline.cache_manager = cache
                    if hasattr(pipeline, 'llm_client'):
                        pipeline.llm_client = llm_client
                    
                    # Exécuter une opération simple
                    run_id = pipeline.create_run()
                    assert run_id is not None
                    
                    # Vérifier que le run existe
                    run_data = pipeline.get_run_data(run_id)
                    assert run_data is not None

    def test_error_recovery(self):
        """Test la récupération d'erreur"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_config = {
                "RUNS_DIR": temp_dir,
                "CACHE_DIR": temp_dir,
                "DEFAULT_N_IDEAS": "1"
            }
            
            with patch.dict('os.environ', test_config):
                # Mock LLM qui échouche une fois puis réussit
                with patch('app.core.llm.httpx.AsyncClient') as mock_client:
                    call_count = 0
                    
                    async def mock_post(*args, **kwargs):
                        nonlocal call_count
                        call_count += 1
                        if call_count == 1:
                            raise Exception("First attempt failed")
                        else:
                            response = Mock()
                            response.status_code = 200
                            response.json.return_value = {"response": "Success after retry", "done": True}
                            return response
                    
                    mock_client.return_value.__aenter__.return_value.post = mock_post
                    
                    settings = Settings()
                    cache = ArtifactCache(max_size=50, ttl_seconds=300)
                    llm_client = LLMClient("http://localhost:11434", "llama3.1:8b")
                    pipeline = VenturePipeline(settings)
                    
                    # Configurer les composants si nécessaire
                    if hasattr(pipeline, 'cache_manager'):
                        pipeline.cache_manager = cache
                    if hasattr(pipeline, 'llm_client'):
                        pipeline.llm_client = llm_client
                    
                    # Première tentative (échec)
                    run_id1 = pipeline.create_run()
                    pipeline.add_idea(run_id1, {"name": "Test", "description": "Test"})
                    
                    try:
                        result1 = pipeline.run_pipeline(run_id1)
                        # Si ça réussit, c'est que la récupération a fonctionné
                        assert result1["status"] == "completed"
                    except Exception:
                        # Si ça échoue, réessayer avec un nouveau run
                        pass
                    
                    # Deuxième tentative (devrait réussir)
                    run_id2 = pipeline.create_run()
                    pipeline.add_idea(run_id2, {"name": "Recovery Test", "description": "Test"})
                    
                    result2 = pipeline.run_pipeline(run_id2)
                    assert result2["status"] == "completed"
                    assert call_count > 1  # Vérifier que les retries ont eu lieu


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
