"""
Tests unitaires pour le module core.config (version adaptée)
Tests basés sur la structure réelle de la classe Settings
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch

from app.core.config import Settings, BASE_DIR


class TestSettings:
    """Tests pour la classe Settings basés sur l'implémentation réelle"""

    def test_default_settings_initialization(self):
        """Test l'initialisation avec les valeurs par défaut"""
        settings = Settings()
        
        # Vérification des valeurs par défaut
        assert settings.ollama_base_url == "http://localhost:11434"
        assert settings.general_model == "llama3.1:8b"
        assert settings.code_model == "qwen2.5-coder:7b"
        assert settings.default_n_ideas == 10
        assert settings.fast_mode is False
        assert settings.max_sources == 8
        assert settings.market_signal_threshold == 40

    def test_custom_settings_initialization(self):
        """Test l'initialisation avec des valeurs personnalisées"""
        with patch.dict(os.environ, {
            "OLLAMA_BASE_URL": "http://custom:11434",
            "GENERAL_MODEL": "custom_model",
            "DEFAULT_N_IDEAS": "15",
            "FAST_MODE": "true"
        }):
            settings = Settings()
            
            assert settings.ollama_base_url == "http://custom:11434"
            assert settings.general_model == "custom_model"
            assert settings.default_n_ideas == 15
            assert settings.fast_mode is True

    def test_boolean_conversion(self):
        """Test la conversion des valeurs booléennes"""
        test_cases = [
            ("true", True),
            ("false", False),
            ("TRUE", True),
            ("FALSE", False),
            ("True", True),
            ("False", False),
            ("1", False),  # Non reconnu comme True
            ("0", False),  # Non reconnu comme True
        ]
        
        for env_value, expected in test_cases:
            with patch.dict(os.environ, {"FAST_MODE": env_value}):
                settings = Settings()
                assert settings.fast_mode == expected

    def test_integer_conversion(self):
        """Test la conversion des valeurs entières"""
        with patch.dict(os.environ, {
            "DEFAULT_N_IDEAS": "25",
            "MAX_SOURCES": "12",
            "REQUEST_TIMEOUT": "45"
        }):
            settings = Settings()
            
            assert settings.default_n_ideas == 25
            assert settings.max_sources == 12
            assert settings.request_timeout == 45

    def test_mvp_settings(self):
        """Test la configuration MVP"""
        with patch.dict(os.environ, {
            "MVP_BUILD_COMMAND": "npm run build",
            "MVP_TEST_COMMAND": "npm run test",
            "MVP_INSTALL_COMMAND": "npm install",
            "MVP_DEV_COMMAND": "npm run dev"
        }):
            settings = Settings()
            
            assert settings.mvp_build_command == "npm run build"
            assert settings.mvp_test_command == "npm run test"
            assert settings.mvp_install_command == "npm install"
            assert settings.mvp_dev_command == "npm run dev"

    def test_signal_processing_settings(self):
        """Test la configuration du traitement de signal"""
        with patch.dict(os.environ, {
            "SIGNAL_SOURCES_TARGET": "8",
            "SIGNAL_PAINS_TARGET": "12",
            "SIGNAL_DOMAIN_TARGET": "6",
            "SIGNAL_QUALITY_THRESHOLD": "55"
        }):
            settings = Settings()
            
            assert settings.signal_sources_target == 8
            assert settings.signal_pains_target == 12
            assert settings.signal_domain_target == 6

    def test_retry_settings(self):
        """Test la configuration des retry"""
        with patch.dict(os.environ, {
            "RETRY_MAX_ATTEMPTS": "5",
            "RETRY_MIN_WAIT": "2",
            "RETRY_MAX_WAIT": "10"
        }):
            settings = Settings()
            
            assert settings.retry_max_attempts == 5
            assert settings.retry_min_wait == 2
            assert settings.retry_max_wait == 10

    def test_base_dir_constant(self):
        """Test la constante BASE_DIR"""
        assert isinstance(BASE_DIR, Path)
        assert BASE_DIR.exists()
        assert (BASE_DIR / "app").exists()

    def test_settings_dataclass(self):
        """Test que Settings est bien un dataclass"""
        from dataclasses import is_dataclass
        
        assert is_dataclass(Settings)
        
        # Test des attributs du dataclass
        settings = Settings()
        assert hasattr(settings, '__dataclass_fields__')
        assert len(settings.__dataclass_fields__) > 0

    def test_env_var_priority(self):
        """Test la priorité des variables d'environnement"""
        # Valeur par défaut
        settings1 = Settings()
        default_value = settings1.ollama_base_url
        
        # Modification de l'environnement
        with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://override:11434"}):
            settings2 = Settings()
            assert settings2.ollama_base_url != default_value
            assert settings2.ollama_base_url == "http://override:11434"

    def test_invalid_integer_values(self):
        """Test la gestion de valeurs entières invalides"""
        with patch.dict(os.environ, {"DEFAULT_N_IDEAS": "invalid"}):
            with pytest.raises(ValueError):
                Settings()

    def test_missing_env_vars(self):
        """Test le comportement quand les variables d'environnement manquent"""
        # Suppression temporaire des variables
        original_env = os.environ.copy()
        try:
            # Supprimer quelques variables
            for key in ["OLLAMA_BASE_URL", "GENERAL_MODEL"]:
                os.environ.pop(key, None)
            
            # Settings devrait utiliser les valeurs par défaut
            settings = Settings()
            assert settings.ollama_base_url == "http://localhost:11434"
            assert settings.general_model == "llama3.1:8b"
            
        finally:
            # Restauration
            os.environ.clear()
            os.environ.update(original_env)

    def test_all_settings_attributes(self):
        """Test que tous les attributs attendus existent"""
        settings = Settings()
        
        expected_attributes = [
            'ollama_base_url', 'general_model', 'code_model',
            'default_n_ideas', 'fast_mode', 'max_sources',
            'market_signal_threshold', 'request_timeout',
            'retry_max_attempts', 'retry_min_wait', 'retry_max_wait',
            'mvp_build_command', 'mvp_test_command', 'mvp_install_command',
            'signal_sources_target', 'signal_pains_target', 'signal_domain_target'
        ]
        
        for attr in expected_attributes:
            assert hasattr(settings, attr), f"Attribute {attr} missing"

    def test_settings_immutability_of_fields(self):
        """Test que les champs sont bien définis"""
        settings = Settings()
        
        # Vérification des types
        assert isinstance(settings.ollama_base_url, str)
        assert isinstance(settings.general_model, str)
        assert isinstance(settings.default_n_ideas, int)
        assert isinstance(settings.fast_mode, bool)
        assert isinstance(settings.max_sources, int)

    def test_edge_case_values(self):
        """Test des cas limites pour les valeurs"""
        with patch.dict(os.environ, {
            "DEFAULT_N_IDEAS": "0",  # Valeur limite
            "MAX_SOURCES": "1",     # Valeur minimale
            "FAST_MODE": "unknown"  # Valeur non reconnue
        }):
            settings = Settings()
            
            assert settings.default_n_ideas == 0
            assert settings.max_sources == 1
            assert settings.fast_mode is False  # unknown -> False

    def test_comprehensive_env_loading(self):
        """Test du chargement complet de l'environnement"""
        env_vars = {
            "OLLAMA_BASE_URL": "http://test:11434",
            "GENERAL_MODEL": "test_model",
            "CODE_MODEL": "test_code_model",
            "DEFAULT_N_IDEAS": "20",
            "FAST_MODE": "true",
            "MAX_SOURCES": "15",
            "REQUEST_TIMEOUT": "60",
            "MARKET_SIGNAL_THRESHOLD": "50",
            "SIGNAL_SOURCES_TARGET": "10",
            "SIGNAL_PAINS_TARGET": "15"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            # Vérification que toutes les valeurs sont chargées
            assert settings.ollama_base_url == env_vars["OLLAMA_BASE_URL"]
            assert settings.general_model == env_vars["GENERAL_MODEL"]
            assert settings.code_model == env_vars["CODE_MODEL"]
            assert settings.default_n_ideas == int(env_vars["DEFAULT_N_IDEAS"])
            assert settings.fast_mode is True
            assert settings.max_sources == int(env_vars["MAX_SOURCES"])
            assert settings.request_timeout == int(env_vars["REQUEST_TIMEOUT"])
            assert settings.market_signal_threshold == int(env_vars["MARKET_SIGNAL_THRESHOLD"])
            assert settings.signal_sources_target == int(env_vars["SIGNAL_SOURCES_TARGET"])
            assert settings.signal_pains_target == int(env_vars["SIGNAL_PAINS_TARGET"])
