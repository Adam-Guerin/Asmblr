"""Data sanitization utilities to prevent sensitive data exposure."""

import re
import json
from typing import Any, Dict, List, Union
from pathlib import Path


class DataSanitizer:
    """Utility class for sanitizing sensitive data from logs and artifacts."""
    
    # Patterns that might contain sensitive data
    SENSITIVE_PATTERNS = [
        # API keys and tokens - more comprehensive patterns
        r'(api[_-]?key|token|secret|password|pwd)\s*[:=]\s*["\']?([a-zA-Z0-9+/=_-]{8,})["\']?',
        r'Bearer\s+([a-zA-Z0-9+/=_-]{10,})',
        r'Basic\s+([a-zA-Z0-9+/=]{10,})',
        r'sk-[a-zA-Z0-9]{20,}',  # Stripe-like keys
        r'[a-zA-Z0-9+/=_-]{32,}',  # Generic long hex/base64 strings
        
        # Email addresses
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        
        # URLs with potential sensitive parameters
        r'https?://[^\s]*?(api[_-]?key|token|secret|password|pwd)=[^\s&]*',
        
        # IP addresses (internal/external)
        r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        
        # File paths that might contain sensitive info
        r'[A-Za-z]:\\[^\\]*\\(?:Users|home|etc)[^\\]*\\',
        r'/(?:home|etc|var)[^/]*/[^/]*',
        
        # Database connection strings
        r'(mysql|postgresql|mongodb)://[^\s]*:[^\s]*@[^\s]*',
        
        # Credit card numbers (basic pattern)
        r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        
        # Phone numbers
        r'\b\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
        
        # Names in file paths (Windows)
        r'\\Users\\[^\\]*\\',
        r'\\home\\[^\\]*\\',
    ]
    
    # Fields that commonly contain sensitive data
    SENSITIVE_FIELDS = {
        'api_key', 'apikey', 'api-key', 'secret', 'password', 'pwd', 'token',
        'authorization', 'auth', 'bearer', 'basic_auth', 'credentials',
        'private_key', 'privatekey', 'private-key', 'access_key', 'accesskey',
        'secret_key', 'secretkey', 'session_key', 'sessionkey', 'csrf_token',
        'auth_token', 'authtoken', 'bearer_token', 'bearertoken',
        'email', 'email_address', 'phone', 'phone_number', 'ssn', 'social_security',
        'credit_card', 'creditcard', 'cc_number', 'bank_account', 'bank_account_number',
        'routing_number', 'swift_code', 'iban', 'account_number', 'account_number',
        'user_password', 'user_pwd', 'passphrase', 'pass_key', 'master_key',
        'encryption_key', 'decryption_key', 'ssl_key', 'tls_key', 'cert_key',
        'database_url', 'db_url', 'connection_string', 'conn_string',
        'redis_url', 'mongo_url', 'postgres_url', 'mysql_url',
        'aws_access_key', 'aws_secret_key', 'azure_key', 'gcp_key',
        'slack_token', 'discord_token', 'github_token', 'gitlab_token',
        'jwt_token', 'jwt', 'oauth_token', 'oauth2_token',
        'cookie', 'session_id', 'sessionid', 'user_session',
        'private_ip', 'public_ip', 'server_ip', 'client_ip',
        'hostname', 'domain', 'subdomain', 'fqdn',
        'file_path', 'directory_path', 'system_path', 'config_path',
    }
    
    @classmethod
    def sanitize_text(cls, text: str, max_length: int = 1000) -> str:
        """
        Sanitize text by removing or redacting sensitive information.
        
        Args:
            text: Text to sanitize
            max_length: Maximum length of sanitized text
            
        Returns:
            Sanitized text
        """
        if not text:
            return text
            
        # Convert to string if needed
        if not isinstance(text, str):
            text = str(text)
        
        # Truncate to max length first
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        # Apply sensitive patterns
        for pattern in cls.SENSITIVE_PATTERNS:
            text = re.sub(pattern, '[REDACTED]', text, flags=re.IGNORECASE)
        
        return text
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any], max_depth: int = 10) -> Dict[str, Any]:
        """
        Recursively sanitize dictionary values.
        
        Args:
            data: Dictionary to sanitize
            max_depth: Maximum recursion depth
            
        Returns:
            Sanitized dictionary
        """
        if max_depth <= 0:
            return {'error': 'Max depth exceeded'}
        
        sanitized = {}
        for key, value in data.items():
            # Check if key name suggests sensitive data
            if cls._is_sensitive_field(key):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value, max_depth - 1)
            elif isinstance(value, list):
                sanitized[key] = cls.sanitize_list(value, max_depth - 1)
            elif isinstance(value, str):
                sanitized[key] = cls.sanitize_text(value)
            else:
                # For other types, convert to string and sanitize
                sanitized[key] = cls.sanitize_text(str(value))
        
        return sanitized
    
    @classmethod
    def sanitize_list(cls, data: List[Any], max_depth: int = 10) -> List[Any]:
        """
        Recursively sanitize list values.
        
        Args:
            data: List to sanitize
            max_depth: Maximum recursion depth
            
        Returns:
            Sanitized list
        """
        if max_depth <= 0:
            return ['[MAX_DEPTH_EXCEEDED]']
        
        sanitized = []
        for item in data:
            if isinstance(item, dict):
                sanitized.append(cls.sanitize_dict(item, max_depth - 1))
            elif isinstance(item, list):
                sanitized.append(cls.sanitize_list(item, max_depth - 1))
            elif isinstance(item, str):
                sanitized.append(cls.sanitize_text(item))
            else:
                sanitized.append(cls.sanitize_text(str(item)))
        
        return sanitized
    
    @classmethod
    def sanitize_for_logging(cls, data: Any, max_length: int = 500) -> str:
        """
        Sanitize data specifically for logging purposes.
        
        Args:
            data: Data to sanitize
            max_length: Maximum length for log output
            
        Returns:
            Sanitized string suitable for logging
        """
        if isinstance(data, str):
            return cls.sanitize_text(data, max_length)
        elif isinstance(data, (dict, list)):
            # Convert to JSON and sanitize
            try:
                json_str = json.dumps(data, default=str, ensure_ascii=False)
                return cls.sanitize_text(json_str, max_length)
            except Exception:
                return cls.sanitize_text(str(data), max_length)
        else:
            return cls.sanitize_text(str(data), max_length)
    
    @classmethod
    def sanitize_for_artifact(cls, data: Any, artifact_type: str = "json") -> Any:
        """
        Sanitize data for writing to artifact files.
        
        Args:
            data: Data to sanitize
            artifact_type: Type of artifact (json, text, etc.)
            
        Returns:
            Sanitized data suitable for artifact storage
        """
        if artifact_type == "json":
            if isinstance(data, dict):
                return cls.sanitize_dict(data)
            elif isinstance(data, list):
                return cls.sanitize_list(data)
            else:
                return cls.sanitize_text(str(data))
        else:
            return cls.sanitize_text(str(data))
    
    @classmethod
    def _is_sensitive_field(cls, field_name: str) -> bool:
        """
        Check if a field name suggests it contains sensitive data.
        
        Args:
            field_name: Field name to check
            
        Returns:
            True if field appears to contain sensitive data
        """
        field_lower = field_name.lower()
        return any(sensitive in field_lower for sensitive in cls.SENSITIVE_FIELDS)
    
    @classmethod
    def sanitize_error_message(cls, error: Exception, max_length: int = 200) -> str:
        """
        Sanitize error messages for logging.
        
        Args:
            error: Exception to sanitize
            max_length: Maximum length of error message
            
        Returns:
            Sanitized error message
        """
        error_str = str(error)
        # Remove potentially sensitive stack traces
        lines = error_str.split('\n')
        # Keep only the first few lines of the error
        relevant_lines = [line for line in lines[:3] if line.strip()]
        sanitized_error = '\n'.join(relevant_lines)
        return cls.sanitize_text(sanitized_error, max_length)
    
    @classmethod
    def sanitize_topic(cls, topic: str, max_length: int = 100) -> str:
        """
        Sanitize topic strings for logging.
        
        Args:
            topic: Topic string to sanitize
            max_length: Maximum length for topic
            
        Returns:
            Sanitized topic string
        """
        if not topic:
            return topic
            
        # Remove potential PII while preserving meaning
        sanitized = cls.sanitize_text(topic, max_length)
        
        # Additional topic-specific sanitization
        # Replace email addresses with [EMAIL] placeholder
        sanitized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', sanitized)
        # Replace phone numbers with [PHONE] placeholder
        sanitized = re.sub(r'\b\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b', '[PHONE]', sanitized)
        
        return sanitized
    
    @classmethod
    def sanitize_run_id(cls, run_id: str) -> str:
        """
        Sanitize run ID for logging (preserve structure but remove sensitive parts).
        
        Args:
            run_id: Run ID to sanitize
            
        Returns:
            Sanitized run ID
        """
        if not run_id:
            return run_id
            
        # Keep timestamp part but redact any potentially sensitive parts
        # Run IDs are typically timestamps, so we can keep them
        if re.match(r'^\d{8}_\d{6}_\d{6}$', run_id):
            return run_id  # Standard run ID format, keep as is
        else:
            # Non-standard format, truncate and sanitize
            return cls.sanitize_text(run_id[:50])[:50]  # Increased limit for longer IDs
