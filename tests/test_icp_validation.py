"""Test ICP validation functionality."""

import pytest

from app.agents.crew import _validate_icp_settings


def test_validate_icp_settings_valid():
    """Test validation with valid ICP settings."""
    icp = "Founders B2B SaaS pre-seed"
    keywords = "founder,founders,b2b,saas,pre-seed,startup,startups,small team,operators"
    
    validated_icp, validated_keywords = _validate_icp_settings(icp, keywords)
    
    assert validated_icp == icp
    assert validated_keywords == keywords


def test_validate_icp_settings_empty():
    """Test validation with empty ICP settings."""
    with pytest.raises(ValueError, match="PRIMARY_ICP cannot be empty"):
        _validate_icp_settings("", "founder,b2b,saas")
    
    with pytest.raises(ValueError, match="PRIMARY_ICP_KEYWORDS cannot be empty"):
        _validate_icp_settings("Founders B2B SaaS pre-seed", "")


def test_validate_icp_settings_whitespace_only():
    """Test validation with whitespace-only ICP settings."""
    with pytest.raises(ValueError, match="PRIMARY_ICP cannot be empty"):
        _validate_icp_settings("   ", "founder,b2b,saas")
    
    with pytest.raises(ValueError, match="PRIMARY_ICP_KEYWORDS cannot be empty"):
        _validate_icp_settings("Founders B2B SaaS pre-seed", "   ")


def test_validate_icp_settings_too_short():
    """Test validation with too short ICP."""
    with pytest.raises(ValueError, match="PRIMARY_ICP is too short"):
        _validate_icp_settings("short", "founder,b2b,saas")


def test_validate_icp_settings_too_long():
    """Test validation with too long ICP."""
    long_icp = "x" * 201
    with pytest.raises(ValueError, match="PRIMARY_ICP is too long"):
        _validate_icp_settings(long_icp, "founder,b2b,saas")


def test_validate_icp_settings_invalid_patterns():
    """Test validation with invalid placeholder values."""
    invalid_patterns = ["test example", "example value", "dummy content", "placeholder text", "none specified", "unknown target"]
    
    for pattern in invalid_patterns:
        with pytest.raises(ValueError, match="invalid placeholder value"):
            _validate_icp_settings(pattern, "founder,b2b,saas")


def test_validate_icp_keywords_too_few():
    """Test validation with too few keywords."""
    with pytest.raises(ValueError, match="must contain at least 3 valid keywords"):
        _validate_icp_settings("Founders B2B SaaS pre-seed", "founder,b2b")


def test_validate_icp_keywords_too_many():
    """Test validation with too many keywords."""
    many_keywords = ",".join([f"keyword{i}" for i in range(21)])
    with pytest.raises(ValueError, match="too many keywords"):
        _validate_icp_settings("Founders B2B SaaS pre-seed", many_keywords)


def test_validate_icp_keywords_invalid_characters():
    """Test validation with invalid characters in keywords."""
    with pytest.raises(ValueError, match="invalid characters"):
        _validate_icp_settings("Founders B2B SaaS pre-seed", "founder,b2b,saas@invalid")


def test_validate_icp_keywords_too_short():
    """Test validation with too short keywords."""
    with pytest.raises(ValueError, match="is too short"):
        _validate_icp_settings("Founders B2B SaaS pre-seed", "founder,b2b,x")


def test_validate_icp_keywords_too_long():
    """Test validation with too long keywords."""
    long_keyword = "x" * 51
    with pytest.raises(ValueError, match="is too long"):
        _validate_icp_settings("Founders B2B SaaS pre-seed", f"founder,b2b,{long_keyword}")


def test_validate_icp_settings_normalizes_whitespace():
    """Test that validation normalizes whitespace in keywords."""
    icp = "  Founders B2B SaaS pre-seed  "
    keywords = "  founder  ,  b2b  ,  saas  ,  pre-seed  "
    
    validated_icp, validated_keywords = _validate_icp_settings(icp, keywords)
    
    assert validated_icp == "Founders B2B SaaS pre-seed"
    assert validated_keywords == "founder,b2b,saas,pre-seed"


def test_validate_icp_settings_hyphens_and_underscores():
    """Test that hyphens and underscores are allowed in keywords."""
    icp = "Developers and DevOps teams"
    keywords = "developer,dev-ops,team_lead,full-stack"
    
    validated_icp, validated_keywords = _validate_icp_settings(icp, keywords)
    
    assert validated_icp == icp
    assert validated_keywords == keywords
