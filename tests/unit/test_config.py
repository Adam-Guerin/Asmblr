"""
Tests unitaires pour le module core.config
Couvre la configuration, la validation des paramètres et la gestion des environnements
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, mock_open
import os

from app.core.config import Settings


class TestSettings:
    """Tests complets pour la classe Settings"""

    def test_default_settings_initialization(self):
        """Test l'initialisation avec les valeurs par défaut"""
        settings = Settings()
        
        assert settings.runs_dir == Path("runs")
        assert settings.data_dir == Path("data")
        assert settings.config_dir == Path("configs")
        assert settings.knowledge_dir == Path("knowledge")
        assert isinstance(settings.env_vars, dict)

    def test_custom_settings_initialization(self):
        """Test l'initialisation avec des chemins personnalisés"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            runs_dir = Path(tmp_dir) / "runs"
            data_dir = Path(tmp_dir) / "data"
            
            settings = Settings(runs_dir=runs_dir, data_dir=data_dir)
            
            assert settings.runs_dir == runs_dir
            assert settings.data_dir == data_dir

    def test_load_env_file_existing(self):
        """Test le chargement d'un fichier .env existant"""
        env_content = """
TEST_VAR=test_value
ANOTHER_VAR=another_value
"""
        with patch("builtins.open", mock_open(read_data=env_content)):
            with patch.object(Path, "exists", return_value=True):
                settings = Settings()
                settings._load_env_file()
                
                assert settings.env_vars.get("TEST_VAR") == "test_value"
                assert settings.env_vars.get("ANOTHER_VAR") == "another_value"

    def test_load_env_file_missing(self):
        """Test le comportement quand le fichier .env n'existe pas"""
        with patch.object(Path, "exists", return_value=False):
            settings = Settings()
            settings._load_env_file()
            
            assert settings.env_vars == {}

    def test_get_env_var_existing(self):
        """Test la récupération d'une variable d'environnement existante"""
        settings = Settings()
        settings.env_vars = {"EXISTING_VAR": "existing_value"}
        
        assert settings.get_env_var("EXISTING_VAR") == "existing_value"
        assert settings.get_env_var("EXISTING_VAR", default="default") == "existing_value"

    def test_get_env_var_missing_with_default(self):
        """Test la récupération d'une variable manquante avec valeur par défaut"""
        settings = Settings()
        settings.env_vars = {}
        
        assert settings.get_env_var("MISSING_VAR", default="default_value") == "default_value"
        assert settings.get_env_var("MISSING_VAR") is None

    def test_get_env_var_type_conversion(self):
        """Test la conversion de type des variables d'environnement"""
        settings = Settings()
        settings.env_vars = {
            "STRING_VAR": "test",
            "INT_VAR": "42",
            "BOOL_VAR_TRUE": "true",
            "BOOL_VAR_FALSE": "false",
            "FLOAT_VAR": "3.14"
        }
        
        assert settings.get_env_var("STRING_VAR") == "test"
        assert settings.get_env_var("INT_VAR", var_type=int) == 42
        assert settings.get_env_var("BOOL_VAR_TRUE", var_type=bool) is True
        assert settings.get_env_var("BOOL_VAR_FALSE", var_type=bool) is False
        assert settings.get_env_var("FLOAT_VAR", var_type=float) == 3.14

    def test_ollama_settings(self):
        """Test la configuration Ollama"""
        settings = Settings()
        settings.env_vars = {
            "OLLAMA_BASE_URL": "http://localhost:11434",
            "GENERAL_MODEL": "llama3.1:8b",
            "CODE_MODEL": "qwen2.5-coder:7b"
        }
        
        assert settings.ollama_base_url == "http://localhost:11434"
        assert settings.general_model == "llama3.1:8b"
        assert settings.code_model == "qwen2.5-coder:7b"

    def test_pipeline_settings(self):
        """Test la configuration de la pipeline"""
        settings = Settings()
        settings.env_vars = {
            "DEFAULT_N_IDEAS": "10",
            "FAST_MODE": "true",
            "MAX_SOURCES": "12",
            "REQUEST_TIMEOUT": "45"
        }
        
        assert settings.default_n_ideas == 10
        assert settings.fast_mode is True
        assert settings.max_sources == 12
        assert settings.request_timeout == 45

    def test_mvp_settings(self):
        """Test la configuration MVP"""
        settings = Settings()
        settings.env_vars = {
            "MVP_BUILD_COMMAND": "npm run build",
            "MVP_TEST_COMMAND": "npm run test",
            "MVP_INSTALL_COMMAND": "npm install",
            "MVP_DEV_COMMAND": "npm run dev"
        }
        
        assert settings.mvp_build_command == "npm run build"
        assert settings.mvp_test_command == "npm run test"
        assert settings.mvp_install_command == "npm install"
        assert settings.mvp_dev_command == "npm run dev"

    def test_threshold_settings(self):
        """Test la configuration des seuils"""
        settings = Settings()
        settings.env_vars = {
            "SIGNAL_SOURCES_TARGET": "6",
            "SIGNAL_PAINS_TARGET": "8",
            "MARKET_SIGNAL_THRESHOLD": "45",
            "SIGNAL_QUALITY_THRESHOLD": "50"
        }
        
        assert settings.signal_sources_target == 6
        assert settings.signal_pains_target == 8
        assert settings.market_signal_threshold == 45
        assert settings.signal_quality_threshold == 50

    def test_create_directories(self, tmp_path):
        """Test la création des répertoires"""
        runs_dir = tmp_path / "runs"
        data_dir = tmp_path / "data"
        
        settings = Settings(runs_dir=runs_dir, data_dir=data_dir)
        settings.create_directories()
        
        assert runs_dir.exists()
        assert data_dir.exists()

    def test_validate_settings_valid(self):
        """Test la validation de configuration valide"""
        settings = Settings()
        settings.env_vars = {
            "OLLAMA_BASE_URL": "http://localhost:11434",
            "GENERAL_MODEL": "llama3.1:8b",
            "DEFAULT_N_IDEAS": "10",
            "MAX_SOURCES": "12"
        }
        
        # Ne devrait pas lever d'exception
        settings.validate_settings()

    def test_validate_settings_missing_required(self):
        """Test la validation avec des paramètres requis manquants"""
        settings = Settings()
        settings.env_vars = {}
        
        with pytest.raises(ValueError, match="OLLAMA_BASE_URL.*required"):
            settings.validate_settings()

    def test_validate_settings_invalid_values(self):
        """Test la validation avec des valeurs invalides"""
        settings = Settings()
        settings.env_vars = {
            "OLLAMA_BASE_URL": "http://localhost:11434",
            "GENERAL_MODEL": "llama3.1:8b",
            "DEFAULT_N_IDEAS": "-1",  # Invalide
            "MAX_SOURCES": "0"  # Invalide
        }
        
        with pytest.raises(ValueError, match="DEFAULT_N_IDEAS.*positive"):
            settings.validate_settings()

    def test_to_dict(self):
        """Test la conversion en dictionnaire"""
        settings = Settings()
        settings.env_vars = {"TEST_VAR": "test_value"}
        
        result = settings.to_dict()
        
        assert isinstance(result, dict)
        assert "env_vars" in result
        assert result["env_vars"]["TEST_VAR"] == "test_value"

    def test_from_dict(self):
        """Test la création depuis un dictionnaire"""
        data = {
            "runs_dir": "custom_runs",
            "data_dir": "custom_data",
            "env_vars": {"TEST_VAR": "test_value"}
        }
        
        settings = Settings.from_dict(data)
        
        assert settings.runs_dir == Path("custom_runs")
        assert settings.data_dir == Path("custom_data")
        assert settings.env_vars["TEST_VAR"] == "test_value"

    def test_environment_override(self):
        """Test la priorité des variables d'environnement système"""
        with patch.dict(os.environ, {"SYSTEM_VAR": "system_value"}):
            settings = Settings()
            settings.env_vars = {"SYSTEM_VAR": "local_value"}
            
            # La valeur système devrait avoir la priorité
            assert settings.get_env_var("SYSTEM_VAR") == "system_value"

    def test_nested_config_access(self):
        """Test l'accès à la configuration imbriquée"""
        settings = Settings()
        settings.env_vars = {
            "NESTED_CONFIG": json.dumps({"key1": "value1", "key2": {"subkey": "subvalue"}})
        }
        
        nested = settings.get_env_var("NESTED_CONFIG", var_type=dict)
        assert nested["key1"] == "value1"
        assert nested["key2"]["subkey"] == "subvalue"

    def test_config_file_loading(self, tmp_path):
        """Test le chargement depuis un fichier de configuration"""
        config_data = {
            "ollama_base_url": "http://custom:11434",
            "general_model": "custom_model",
            "default_n_ideas": 15
        }
        
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        settings = Settings()
        settings.load_from_file(config_file)
        
        assert settings.ollama_base_url == "http://custom:11434"
        assert settings.general_model == "custom_model"
        assert settings.default_n_ideas == 15
