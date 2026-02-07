"""Tests pour le système de configuration intelligente"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

from app.core.smart_config import SmartConfig, get_smart_config, configure_for_topic
from app.core.agent_config import DynamicConfigManager, ConfigurationAgent
from app.agents.config_agent import ConfigCrewManager, ConfigAnalysisAgent


class TestConfigurationAgent:
    """Tests pour l'agent de configuration"""
    
    def test_analyze_context_basic(self):
        """Test analyse basique de contexte"""
        mock_llm = Mock()
        mock_llm.generate_json.return_value = {
            "configuration": {
                "execution_mode": "validation_sprint",
                "n_ideas": 1,
                "max_sources": 5,
                "market_signal_threshold": 40,
                "signal_quality_threshold": 45,
                "fast_mode": True,
                "reasoning": "Sujet simple, mode sprint"
            }
        }
        
        agent = ConfigurationAgent(mock_llm)
        result = agent.analyze_context("AI compliance for SMBs")
        
        assert result["execution_mode"] == "validation_sprint"
        assert result["n_ideas"] == 1
        assert result["max_sources"] == 5
        assert result["fast_mode"] is True
        assert len(agent.config_history) == 1
    
    def test_normalize_config_validation(self):
        """Test validation et normalisation de configuration"""
        mock_llm = Mock()
        agent = ConfigurationAgent(mock_llm)
        
        # Test valeurs invalides
        invalid_config = {
            "execution_mode": "invalid_mode",
            "n_ideas": 50,  # Trop élevé
            "max_sources": 100,  # Trop élevé
            "market_signal_threshold": 10  # Trop bas
        }
        
        normalized = agent._normalize_config(invalid_config)
        
        assert normalized["execution_mode"] == "standard"  # Valeur par défaut
        assert normalized["n_ideas"] <= 15  # Limité
        assert normalized["max_sources"] <= 20  # Limité
        assert normalized["market_signal_threshold"] >= 30  # Minimum
    
    def test_optimize_for_performance(self):
        """Test optimisation basée sur les performances"""
        mock_llm = Mock()
        mock_llm.generate_json.return_value = {
            "adjustments": {
                "max_sources": 6,
                "request_timeout": 30,
                "retry_max_attempts": 3
            },
            "reasoning": "Réduction pour améliorer la vitesse"
        }
        
        agent = ConfigurationAgent(mock_llm)
        current_config = {
            "max_sources": 12,
            "request_timeout": 60,
            "retry_max_attempts": 5
        }
        performance_metrics = {
            "execution_time_seconds": 300,
            "error_rate": 0.1
        }
        
        optimized = agent.optimize_for_performance(current_config, performance_metrics)
        
        assert optimized["max_sources"] == 6
        assert optimized["request_timeout"] == 30
        assert optimized["retry_max_attempts"] == 3


class TestDynamicConfigManager:
    """Tests pour le gestionnaire de configuration dynamique"""
    
    def test_get_config_for_topic(self):
        """Test génération configuration pour un sujet"""
        mock_llm = Mock()
        mock_llm.generate_json.return_value = {
            "configuration": {
                "execution_mode": "standard",
                "n_ideas": 8,
                "max_sources": 10
            }
        }
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = DynamicConfigManager(mock_llm, Path(tmp_dir))
            config = manager.get_config_for_topic("Test topic")
            
            assert config.n_ideas == 8
            assert config.max_sources == 10
            assert config.execution_mode == "standard"
    
    def test_get_env_vars(self):
        """Test génération variables d'environnement"""
        mock_llm = Mock()
        manager = DynamicConfigManager(mock_llm)
        
        env_vars = manager.get_env_vars()
        
        assert "DEFAULT_N_IDEAS" in env_vars
        assert "MAX_SOURCES" in env_vars
        assert "MARKET_SIGNAL_THRESHOLD" in env_vars
        assert env_vars["DEFAULT_N_IDEAS"] == "10"  # Valeur par défaut


class TestSmartConfig:
    """Tests pour la configuration intelligente"""
    
    def test_initialization(self):
        """Test initialisation configuration"""
        with patch.dict('os.environ', {
            'OLLAMA_BASE_URL': 'http://test:11434',
            'GENERAL_MODEL': 'test-model',
            'AGENT_AUTO_CONFIG': 'true'
        }):
            config = SmartConfig()
            
            assert config.current_config['OLLAMA_BASE_URL'] == 'http://test:11434'
            assert config.current_config['GENERAL_MODEL'] == 'test-model'
            assert 'DEFAULT_N_IDEAS' in config.current_config
    
    def test_configure_for_topic(self):
        """Test configuration pour un sujet"""
        mock_llm = Mock()
        mock_llm.generate_json.return_value = {
            "configuration": {
                "execution_mode": "validation_sprint",
                "n_ideas": 1,
                "fast_mode": True
            }
        }
        
        with patch.dict('os.environ', {'AGENT_AUTO_CONFIG': 'true'}):
            config = SmartConfig(mock_llm)
            result = config.configure_for_topic("Test topic")
            
            assert 'EXECUTION_MODE' in result
            assert 'DEFAULT_N_IDEAS' in result
    
    def test_disabled_auto_config(self):
        """Test désactivation configuration automatique"""
        with patch.dict('os.environ', {'AGENT_AUTO_CONFIG': 'false'}):
            config = SmartConfig()
            result = config.configure_for_topic("Test topic")
            
            # Devrait retourner la configuration par défaut
            assert result == config.current_config
    
    def test_export_config_env(self):
        """Test export configuration format ENV"""
        config = SmartConfig()
        config.current_config = {
            'TEST_VAR': 'test_value',
            'EMPTY_VAR': '',
            'BOOL_VAR': 'true'
        }
        
        exported = config.export_config('env')
        lines = exported.split('\n')
        
        assert 'TEST_VAR=test_value' in lines
        assert 'BOOL_VAR=true' in lines
        assert 'EMPTY_VAR=' not in exported  # Valeurs vides exclues
    
    def test_export_config_json(self):
        """Test export configuration format JSON"""
        config = SmartConfig()
        config.current_config = {'TEST_VAR': 'test_value'}
        
        exported = config.export_config('json')
        parsed = json.loads(exported)
        
        assert parsed['TEST_VAR'] == 'test_value'


class TestConfigAnalysisAgent:
    """Tests pour l'agent d'analyse de configuration"""
    
    def test_analyze_topic_complexity(self):
        """Test analyse complexité sujet"""
        mock_llm = Mock()
        mock_llm.generate_json.return_value = {
            "technical_complexity": 7,
            "market_specificity": 6,
            "data_availability": 4,
            "recommended_config": {
                "execution_mode": "standard",
                "n_ideas": 12,
                "max_sources": 10,
                "market_signal_threshold": 50
            },
            "reasoning": "Sujet modérément complexe"
        }
        
        agent = ConfigAnalysisAgent(mock_llm)
        result = agent.analyze_topic_complexity("Blockchain for supply chain")
        
        assert result["technical_complexity"] == 7
        assert result["recommended_config"]["execution_mode"] == "standard"
        assert result["recommended_config"]["n_ideas"] == 12
    
    def test_validate_complexity_analysis(self):
        """Test validation analyse complexité"""
        agent = ConfigAnalysisAgent(Mock())
        
        invalid_analysis = {
            "technical_complexity": 15,  # Trop élevé
            "market_specificity": -5,   # Trop bas
            "recommended_config": {
                "execution_mode": "invalid",
                "n_ideas": 100,  # Trop élevé
                "market_signal_threshold": 10  # Trop bas
            }
        }
        
        validated = agent._validate_complexity_analysis(invalid_analysis)
        
        assert validated["technical_complexity"] == 10  # Limité à 10
        assert validated["market_specificity"] == 1    # Limité à 1
        assert validated["recommended_config"]["execution_mode"] == "standard"  # Par défaut
        assert validated["recommended_config"]["n_ideas"] <= 30  # Limité
        assert validated["recommended_config"]["market_signal_threshold"] >= 30  # Minimum


class TestConfigCrewManager:
    """Tests pour le gestionnaire d'équipage de configuration"""
    
    def test_generate_optimal_config(self):
        """Test génération configuration optimale"""
        mock_llm = Mock()
        
        # Mock des réponses pour les différents agents
        mock_llm.generate_json.side_effect = [
            # Réponse analyse complexité
            {
                "technical_complexity": 6,
                "recommended_config": {
                    "execution_mode": "standard",
                    "n_ideas": 10
                }
            },
            # Réponse adaptation profil
            {
                "execution_mode": "validation_sprint",
                "fast_mode": True,
                "n_ideas": 1
            },
            # Réponse optimisation performance
            {
                "optimizations": []
            }
        ]
        
        manager = ConfigCrewManager(mock_llm)
        result = manager.generate_optimal_config(
            topic="Test topic",
            user_profile={"experience_level": "beginner"}
        )
        
        assert "final_config" in result
        assert "complexity_analysis" in result
        assert "user_adaptation" in result
        assert result["topic"] == "Test topic"
    
    def test_merge_configurations(self):
        """Test fusion configurations"""
        manager = ConfigCrewManager(Mock())
        
        base_config = {"n_ideas": 10, "max_sources": 8}
        user_config = {"n_ideas": 5, "fast_mode": True}
        optimizations = []  # Pas d'optimisations
        
        merged = manager._merge_configurations(base_config, user_config, optimizations)
        
        # La configuration utilisateur doit primer
        assert merged["n_ideas"] == 5
        assert merged["max_sources"] == 8
        assert merged["fast_mode"] is True


class TestIntegration:
    """Tests d'intégration"""
    
    def test_configure_for_topic_utility(self):
        """Test fonction utilitaire configure_for_topic"""
        mock_llm = Mock()
        mock_llm.generate_json.return_value = {
            "configuration": {
                "execution_mode": "validation_sprint",
                "n_ideas": 1
            }
        }
        
        with patch.dict('os.environ', {'AGENT_AUTO_CONFIG': 'true'}):
            result = configure_for_topic("Test topic", mock_llm)
            
            assert isinstance(result, dict)
            assert 'EXECUTION_MODE' in result or 'DEFAULT_N_IDEAS' in result
    
    def test_get_smart_config_singleton(self):
        """Test singleton get_smart_config"""
        # Premier appel
        config1 = get_smart_config()
        # Deuxième appel
        config2 = get_smart_config()
        
        # Doit retourner la même instance
        assert config1 is config2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
