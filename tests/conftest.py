"""
Configuration pour pytest avec les fixtures et paramètres globaux
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Ajout du répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture(scope="session")
def temp_dir():
    """Fixture temporaire pour la session de tests"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="session")
def test_env_vars():
    """Variables d'environnement pour les tests"""
    original_env = os.environ.copy()
    
    # Configuration de test
    test_env = {
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "GENERAL_MODEL": "llama3.1:8b",
        "CODE_MODEL": "qwen2.5-coder:7b",
        "DEFAULT_N_IDEAS": "3",
        "FAST_MODE": "true",
        "MAX_SOURCES": "5",
        "REQUEST_TIMEOUT": "10",
        "SIGNAL_SOURCES_TARGET": "3",
        "SIGNAL_PAINS_TARGET": "5",
        "MARKET_SIGNAL_THRESHOLD": "30",
        "SIGNAL_QUALITY_THRESHOLD": "40",
        "LOG_LEVEL": "DEBUG",
        "TEST_MODE": "true"
    }
    
    os.environ.update(test_env)
    yield test_env
    
    # Restauration de l'environnement original
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_ollama():
    """Mock pour Ollama"""
    from unittest.mock import Mock
    
    mock = Mock()
    mock.available.return_value = True
    mock.generate.return_value = "Mock response"
    mock.list_models.return_value = [
        {"name": "llama3.1:8b", "size": 8000000000},
        {"name": "qwen2.5-coder:7b", "size": 7000000000}
    ]
    
    return mock


@pytest.fixture
def sample_run_data():
    """Données d'exécution de test"""
    return {
        "topic": "AI compliance for SMBs",
        "n_ideas": 5,
        "fast_mode": True,
        "status": "created",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_ideas():
    """Idées de test"""
    return [
        {
            "name": "AI Compliance Checker",
            "one_liner": "Automated compliance monitoring for SMBs",
            "target_user": "Compliance officers",
            "problem": "Manual compliance tracking is error-prone",
            "solution": "AI-powered automated monitoring",
            "key_features": ["Real-time monitoring", "Report generation", "Alert system"]
        },
        {
            "name": "Compliance Chatbot",
            "one_liner": "AI assistant for compliance questions",
            "target_user": "Business owners",
            "problem": "Complex compliance regulations",
            "solution": "Simplified AI guidance",
            "key_features": ["Natural language queries", "Regulation database", "Action recommendations"]
        }
    ]


@pytest.fixture
def sample_market_data():
    """Données de marché de test"""
    return {
        "pain_statements": [
            "Teams struggle with GDPR compliance",
            "SMBs lack resources for compliance monitoring",
            "Manual compliance tracking is time-consuming"
        ],
        "sources": [
            {"name": "TechCrunch", "url": "https://techcrunch.com/compliance", "text": "Compliance challenges"},
            {"name": "Forbes", "url": "https://forbes.com/smb-compliance", "text": "SMB compliance issues"}
        ],
        "competitors": [
            {"product_name": "ComplianceAI", "pricing": "$100/month"},
            {"product_name": "RegTech", "pricing": "$75/month"}
        ]
    }


@pytest.fixture
def sample_artifacts():
    """Artefacts de test"""
    return {
        "prd.md": "# Product Requirements Document\n\n## Overview\n...",
        "tech_spec.md": "# Technical Specification\n\n## Architecture\n...",
        "market_report.md": "# Market Report\n\n## Executive Summary\n...",
        "landing_page/index.html": "<html><head><title>Product</title></head><body>...</body></html>",
        "content_pack/posts.md": "# Blog Posts\n\n## Post 1\n..."
    }


# Configuration pytest
def pytest_configure(config):
    """Configuration globale de pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modification des tests collectés"""
    # Ajout automatique de marqueurs basés sur le nom du fichier
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        else:
            item.add_marker(pytest.mark.unit)  # Par défaut


# Configuration pour les tests lents
def pytest_runtest_setup(item):
    """Setup avant chaque test"""
    # Marquer les tests lents
    if "slow" in item.keywords:
        if item.config.getoption("-m") == "not slow":
            pytest.skip("slow test skipped")
