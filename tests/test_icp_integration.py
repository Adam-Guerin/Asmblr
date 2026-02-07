"""Test ICP integration in the pipeline."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from app.agents.crew import _validate_icp_settings


def test_icp_validation_integration():
    """Test ICP validation with realistic values."""
    # Test with the default values from .env.example
    icp = "Founders B2B SaaS pre-seed"
    keywords = "founder,founders,b2b,saas,pre-seed,startup,startups,small team,operators"
    
    validated_icp, validated_keywords = _validate_icp_settings(icp, keywords)
    
    assert validated_icp == icp
    assert validated_keywords == keywords
    
    # Test with spaces in keywords
    icp2 = "Developers and DevOps Teams"
    keywords2 = "developer,dev-ops,team lead,full-stack,small team"
    
    validated_icp2, validated_keywords2 = _validate_icp_settings(icp2, keywords2)
    
    assert validated_icp2 == icp2
    assert validated_keywords2 == keywords2


def test_icp_validation_edge_cases():
    """Test ICP validation edge cases."""
    # Test minimum valid length
    icp = "A" * 10  # Exactly 10 characters
    keywords = "dev,ops,team"
    
    validated_icp, validated_keywords = _validate_icp_settings(icp, keywords)
    assert validated_icp == icp
    assert validated_keywords == keywords
    
    # Test maximum valid length
    icp = "A" * 200  # Exactly 200 characters
    validated_icp, validated_keywords = _validate_icp_settings(icp, keywords)
    assert validated_icp == icp
    
    # Test minimum number of keywords (each at least 2 characters)
    keywords = "ab,cd,ef"  # Exactly 3 keywords, each 2 chars
    validated_icp, validated_keywords = _validate_icp_settings(icp, keywords)
    assert validated_keywords == keywords
    
    # Test maximum number of keywords
    keywords = ",".join([f"keyword{i}" for i in range(20)])  # Exactly 20 keywords
    validated_icp, validated_keywords = _validate_icp_settings(icp, keywords)
    assert len(validated_keywords.split(",")) == 20
