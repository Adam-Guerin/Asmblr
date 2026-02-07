"""Test data sanitization functionality."""

import pytest
from app.core.sanitizer import DataSanitizer


def test_sanitize_text_removes_api_keys():
    """Test that API keys are properly redacted."""
    text = "api_key=sk-1234567890abcdef and token=abc123def456"
    result = DataSanitizer.sanitize_text(text)
    assert "sk-1234567890abcdef" not in result
    assert "abc123def456" not in result
    assert "[REDACTED]" in result


def test_sanitize_text_removes_emails():
    """Test that email addresses are properly redacted."""
    text = "Contact us at support@example.com or admin@company.org"
    result = DataSanitizer.sanitize_text(text)
    assert "support@example.com" not in result
    assert "admin@company.org" not in result
    assert "[REDACTED]" in result


def test_sanitize_text_removes_phone_numbers():
    """Test that phone numbers are properly redacted."""
    text = "Call us at (555) 123-4567 or +1-800-555-0199"
    result = DataSanitizer.sanitize_text(text)
    assert "(555) 123-4567" not in result
    assert "+1-800-555-0199" not in result
    assert "[REDACTED]" in result


def test_sanitize_text_removes_ip_addresses():
    """Test that IP addresses are properly redacted."""
    text = "Server at 192.168.1.1 or 10.0.0.1"
    result = DataSanitizer.sanitize_text(text)
    assert "192.168.1.1" not in result
    assert "10.0.0.1" not in result
    assert "[REDACTED]" in result


def test_sanitize_text_removes_urls_with_sensitive_params():
    """Test that URLs with sensitive parameters are redacted."""
    text = "https://api.example.com/endpoint?api_key=secret123&token=abc456"
    result = DataSanitizer.sanitize_text(text)
    assert "api_key=secret123" not in result
    assert "token=abc456" not in result
    assert "[REDACTED]" in result


def test_sanitize_text_truncates_long_text():
    """Test that long text is properly truncated."""
    text = "x" * 2000
    result = DataSanitizer.sanitize_text(text, max_length=100)
    assert len(result) <= 103  # 100 + "..."
    assert result.endswith("...")


def test_sanitize_dict_redacts_sensitive_fields():
    """Test that dictionaries with sensitive field names are redacted."""
    data = {
        "username": "john_doe",
        "api_key": "secret123",
        "password": "mypassword",
        "email": "john@example.com",
        "normal_field": "some_value"
    }
    result = DataSanitizer.sanitize_dict(data)
    assert result["username"] == "john_doe"
    assert result["normal_field"] == "some_value"
    assert result["api_key"] == "[REDACTED]"
    assert result["password"] == "[REDACTED]"
    assert result["email"] == "[REDACTED]"


def test_sanitize_dict_recursive():
    """Test that nested dictionaries are properly sanitized."""
    data = {
        "level1": {
            "api_key": "secret123",
            "level2": {
                "password": "mypassword",
                "normal_field": "value"
            }
        },
        "top_level_secret": "abc123"
    }
    result = DataSanitizer.sanitize_dict(data)
    assert result["level1"]["api_key"] == "[REDACTED]"
    assert result["level1"]["level2"]["password"] == "[REDACTED]"
    assert result["level1"]["level2"]["normal_field"] == "value"
    assert result["top_level_secret"] == "[REDACTED]"


def test_sanitize_list():
    """Test that lists are properly sanitized."""
    data = [
        {"api_key": "secret123"},
        {"normal_field": "value"},
        "text with email@example.com",
        12345
    ]
    result = DataSanitizer.sanitize_list(data)
    assert result[0]["api_key"] == "[REDACTED]"
    assert result[1]["normal_field"] == "value"
    assert "email@example.com" not in result[2]
    assert "[REDACTED]" in result[2]


def test_sanitize_for_logging():
    """Test sanitization specifically for logging."""
    data = {
        "api_key": "secret123",
        "user_email": "john@example.com",
        "normal_field": "value"
    }
    result = DataSanitizer.sanitize_for_logging(data, max_length=200)
    assert "secret123" not in result
    assert "john@example.com" not in result
    assert "[REDACTED]" in result
    assert len(result) <= 203  # 200 + "..."


def test_sanitize_error_message():
    """Test error message sanitization."""
    try:
        # Simulate an error with sensitive info
        raise ValueError("API key sk-1234567890abcdef is invalid for user john@example.com")
    except Exception as e:
        result = DataSanitizer.sanitize_error_message(e)
        assert "sk-1234567890abcdef" not in result
        assert "john@example.com" not in result
        assert "[REDACTED]" in result
        assert len(result) <= 202  # 200 + "..."


def test_sanitize_topic():
    """Test topic sanitization."""
    topic = "Build app for john@example.com with API key sk-1234567890abcdef"
    result = DataSanitizer.sanitize_topic(topic, max_length=50)
    assert "john@example.com" not in result
    assert "sk-1234567890abcdef" not in result
    assert "[EMAIL]" in result
    assert len(result) <= 53  # 50 + "..."


def test_sanitize_run_id():
    """Test run ID sanitization."""
    # Standard format run ID should be preserved
    run_id = "20240131_123456_789012"
    result = DataSanitizer.sanitize_run_id(run_id)
    assert result == run_id
    
    # Non-standard format should be sanitized
    run_id = "user_session_api_key_secret123"
    result = DataSanitizer.sanitize_run_id(run_id)
    assert "secret123" not in result
    assert "[REDACTED]" in result
    assert len(result) <= 20


def test_is_sensitive_field():
    """Test sensitive field detection."""
    assert DataSanitizer._is_sensitive_field("api_key")
    assert DataSanitizer._is_sensitive_field("password")
    assert DataSanitizer._is_sensitive_field("user_email")
    assert DataSanitizer._is_sensitive_field("auth_token")
    assert not DataSanitizer._is_sensitive_field("username")
    assert not DataSanitizer._is_sensitive_field("normal_field")
    assert DataSanitizer._is_sensitive_field("API_KEY")  # Case insensitive
    assert DataSanitizer._is_sensitive_field("userPassword")  # Compound words


def test_sanitize_credit_card_numbers():
    """Test that credit card numbers are redacted."""
    text = "Pay with card 4111-1111-1111-1111 or 4111111111111111"
    result = DataSanitizer.sanitize_text(text)
    assert "4111-1111-1111-1111" not in result
    assert "4111111111111111" not in result
    assert "[REDACTED]" in result


def test_sanitize_database_urls():
    """Test that database connection strings are redacted."""
    text = "mysql://user:password@localhost:3306/dbname"
    result = DataSanitizer.sanitize_text(text)
    assert "user:password" not in result
    assert "[REDACTED]" in result


def test_sanitize_bearer_tokens():
    """Test that Bearer tokens are redacted."""
    text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    result = DataSanitizer.sanitize_text(text)
    assert "Bearer" in result
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result
    assert "[REDACTED]" in result


def test_sanitize_file_paths():
    """Test that sensitive file paths are redacted."""
    text = "Config at C:\\Users\\John\\AppData\\config.json"
    result = DataSanitizer.sanitize_text(text)
    assert "John" not in result
    assert "AppData" not in result
    assert "[REDACTED]" in result


def test_max_depth_protection():
    """Test that maximum recursion depth is respected."""
    # Create deeply nested structure
    data = {"level": 0}
    current = data
    for i in range(1, 20):
        current["level"] = {"level": i}
        current = current["level"]
    
    result = DataSanitizer.sanitize_dict(data, max_depth=5)
    # Should stop at max depth
    assert "error" in str(result) or "MAX_DEPTH_EXCEEDED" in str(result)
