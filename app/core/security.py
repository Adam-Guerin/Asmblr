"""
Security Manager - Centralized security for Asmblr
Handles secrets management, encryption, and security policies
"""

import os
import secrets
import base64
from pathlib import Path
from typing import Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from loguru import logger
import json
import time

class SecurityManager:
    """Centralized security management for Asmblr"""
    
    def __init__(self):
        self.secrets_dir = Path(__file__).parent.parent.parent / "secrets"
        self.secrets_dir.mkdir(exist_ok=True)
        self.keys_file = self.secrets_dir / "security_keys.json"
        self.encrypted_secrets_file = self.secrets_dir / "encrypted_secrets.enc"
        
        # Security configuration
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Security policies
        self.min_password_length = 16
        self.session_timeout = 3600  # 1 hour
        self.max_failed_attempts = 5
        self.lockout_duration = 900  # 15 minutes
        
        # Initialize failed attempts tracking
        self.failed_attempts_file = self.secrets_dir / "failed_attempts.json"
        self.failed_attempts = self._load_failed_attempts()
        
    def _get_or_create_encryption_key(self) -> bytes:
        """Generate or load encryption key"""
        if self.keys_file.exists():
            try:
                with open(self.keys_file) as f:
                    data = json.load(f)
                    key_data = base64.b64decode(data['encryption_key'])
                    return key_data
            except Exception as e:
                logger.warning(f"Failed to load encryption key: {e}")
        
        # Generate new key
        password = os.getenv("MASTER_PASSWORD", "").encode()
        if not password:
            # Generate random password if not set
            password = secrets.token_bytes(32)
            logger.warning("MASTER_PASSWORD not set, using random key")
        
        salt = os.getenv("ENCRYPTION_SALT", "").encode()
        if not salt:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        # Save key
        try:
            with open(self.keys_file, 'w') as f:
                json.dump({
                    'encryption_key': key.decode(),
                    'created_at': time.time(),
                    'algorithm': 'PBKDF2HMAC-SHA256'
                }, f)
            logger.info("Encryption key generated and saved")
        except Exception as e:
            logger.error(f"Failed to save encryption key: {e}")
        
        return base64.urlsafe_b64decode(key)
    
    def encrypt_secret(self, secret: str) -> str:
        """Encrypt a secret value"""
        try:
            encrypted = self.cipher_suite.encrypt(secret.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt secret: {e}")
            raise
    
    def decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt a secret value"""
        try:
            encrypted = base64.b64decode(encrypted_secret.encode())
            decrypted = self.cipher_suite.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt secret: {e}")
            raise
    
    def store_secret(self, key: str, value: str, metadata: dict | None = None) -> bool:
        """Store an encrypted secret"""
        try:
            # Load existing secrets
            secrets = self.load_all_secrets()
            
            # Encrypt the value
            encrypted_value = self.encrypt_secret(value)
            
            # Store with metadata
            secrets[key] = {
                'encrypted_value': encrypted_value,
                'created_at': time.time(),
                'updated_at': time.time(),
                'access_count': 0,
                'metadata': metadata or {}
            }
            
            # Save to file
            with open(self.encrypted_secrets_file, 'w') as f:
                json.dump(secrets, f)
            
            logger.info(f"Secret '{key}' stored successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store secret '{key}': {e}")
            return False
    
    def get_secret(self, key: str) -> str | None:
        """Retrieve and decrypt a secret"""
        try:
            secrets = self.load_all_secrets()
            
            if key not in secrets:
                logger.warning(f"Secret '{key}' not found")
                return None
            
            secret_data = secrets[key]
            encrypted_value = secret_data['encrypted_value']
            
            # Decrypt
            decrypted_value = self.decrypt_secret(encrypted_value)
            
            # Update access count and timestamp
            secret_data['access_count'] += 1
            secret_data['last_accessed'] = time.time()
            secrets[key] = secret_data
            
            # Save updated access info
            with open(self.encrypted_secrets_file, 'w') as f:
                json.dump(secrets, f)
            
            logger.debug(f"Secret '{key}' accessed successfully")
            return decrypted_value
            
        except Exception as e:
            logger.error(f"Failed to retrieve secret '{key}': {e}")
            return None
    
    def load_all_secrets(self) -> dict[str, Any]:
        """Load all encrypted secrets"""
        try:
            if not self.encrypted_secrets_file.exists():
                return {}
            
            with open(self.encrypted_secrets_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load secrets: {e}")
            return {}
    
    def delete_secret(self, key: str) -> bool:
        """Delete a secret"""
        try:
            secrets = self.load_all_secrets()
            
            if key in secrets:
                del secrets[key]
                
                with open(self.encrypted_secrets_file, 'w') as f:
                    json.dump(secrets, f)
                
                logger.info(f"Secret '{key}' deleted successfully")
                return True
            else:
                logger.warning(f"Secret '{key}' not found for deletion")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete secret '{key}': {e}")
            return False
    
    def generate_secure_password(self, length: int = None) -> str:
        """Generate a secure random password"""
        length = length or self.min_password_length
        
        # Generate password with required complexity
        password = secrets.token_urlsafe(length)
        
        # Ensure it meets requirements
        while not self._validate_password_strength(password):
            password = secrets.token_urlsafe(length)
        
        return password
    
    def _validate_password_strength(self, password: str) -> bool:
        """Validate password strength requirements"""
        if len(password) < self.min_password_length:
            return False
        
        # Check for at least one of each character type
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    def rotate_secret(self, key: str) -> str | None:
        """Rotate a secret and return the new value"""
        try:
            current_value = self.get_secret(key)
            metadata = self.load_all_secrets().get(key, {}).get('metadata', {})
            
            # Generate new secret
            if 'password' in key.lower():
                new_value = self.generate_secure_password()
            elif 'token' in key.lower() or 'key' in key.lower():
                new_value = secrets.token_urlsafe(32)
            else:
                new_value = secrets.token_urlsafe(32)
            
            # Store new secret
            if self.store_secret(key, new_value, metadata):
                logger.info(f"Secret '{key}' rotated successfully")
                return new_value
            else:
                logger.error(f"Failed to rotate secret '{key}'")
                return None
                
        except Exception as e:
            logger.error(f"Error rotating secret '{key}': {e}")
            return None
    
    def check_rate_limit(self, identifier: str) -> bool:
        """Check if identifier is rate limited"""
        current_time = time.time()
        
        if identifier not in self.failed_attempts:
            return False
        
        attempts = self.failed_attempts[identifier]
        
        # Check if currently locked out
        if attempts.get('locked_until', 0) > current_time:
            return True
        
        # Check if too many failed attempts
        if attempts.get('count', 0) >= self.max_failed_attempts:
            # Lock out
            attempts['locked_until'] = current_time + self.lockout_duration
            attempts['count'] = 0
            self._save_failed_attempts()
            logger.warning(f"Identifier '{identifier}' locked out due to too many failed attempts")
            return True
        
        return False
    
    def record_failed_attempt(self, identifier: str):
        """Record a failed authentication attempt"""
        current_time = time.time()
        
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = {
                'count': 0,
                'first_attempt': current_time,
                'last_attempt': current_time,
                'locked_until': 0
            }
        
        self.failed_attempts[identifier]['count'] += 1
        self.failed_attempts[identifier]['last_attempt'] = current_time
        self._save_failed_attempts()
        
        logger.warning(f"Failed attempt recorded for '{identifier}' (count: {self.failed_attempts[identifier]['count']})")
    
    def clear_failed_attempts(self, identifier: str):
        """Clear failed attempts for identifier"""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]
            self._save_failed_attempts()
            logger.info(f"Failed attempts cleared for '{identifier}'")
    
    def _load_failed_attempts(self) -> dict[str, Any]:
        """Load failed attempts from file"""
        try:
            if self.failed_attempts_file.exists():
                with open(self.failed_attempts_file) as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load failed attempts: {e}")
        return {}
    
    def _save_failed_attempts(self):
        """Save failed attempts to file"""
        try:
            with open(self.failed_attempts_file, 'w') as f:
                json.dump(self.failed_attempts, f)
        except Exception as e:
            logger.error(f"Failed to save failed attempts: {e}")
    
    def audit_secrets(self) -> dict[str, Any]:
        """Generate audit report of all secrets"""
        try:
            secrets = self.load_all_secrets()
            
            audit_report = {
                'total_secrets': len(secrets),
                'secrets_by_age': {},
                'secrets_by_access': {},
                'old_secrets': [],
                'never_accessed': []
            }
            
            current_time = time.time()
            
            for key, data in secrets.items():
                age_days = (current_time - data['created_at']) / 86400
                access_count = data.get('access_count', 0)
                last_accessed = data.get('last_accessed', data['created_at'])
                
                # Categorize by age
                if age_days < 7:
                    audit_report['secrets_by_age']['< 7 days'] = audit_report['secrets_by_age'].get('< 7 days', 0) + 1
                elif age_days < 30:
                    audit_report['secrets_by_age']['7-30 days'] = audit_report['secrets_by_age'].get('7-30 days', 0) + 1
                elif age_days < 90:
                    audit_report['secrets_by_age']['30-90 days'] = audit_report['secrets_by_age'].get('30-90 days', 0) + 1
                else:
                    audit_report['secrets_by_age']['> 90 days'] = audit_report['secrets_by_age'].get('> 90 days', 0) + 1
                    audit_report['old_secrets'].append(key)
                
                # Categorize by access
                if access_count == 0:
                    audit_report['never_accessed'].append(key)
                elif access_count < 10:
                    audit_report['secrets_by_access']['< 10'] = audit_report['secrets_by_access'].get('< 10', 0) + 1
                elif access_count < 100:
                    audit_report['secrets_by_access']['10-100'] = audit_report['secrets_by_access'].get('10-100', 0) + 1
                else:
                    audit_report['secrets_by_access']['> 100'] = audit_report['secrets_by_access'].get('> 100', 0) + 1
            
            return audit_report
            
        except Exception as e:
            logger.error(f"Failed to generate audit report: {e}")
            return {}
    
    def cleanup_old_secrets(self, days_old: int = 90) -> int:
        """Clean up secrets older than specified days"""
        try:
            secrets = self.load_all_secrets()
            current_time = time.time()
            cutoff_time = current_time - (days_old * 86400)
            
            keys_to_delete = []
            for key, data in secrets.items():
                if data['created_at'] < cutoff_time:
                    keys_to_delete.append(key)
            
            deleted_count = 0
            for key in keys_to_delete:
                if self.delete_secret(key):
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} secrets older than {days_old} days")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old secrets: {e}")
            return 0

# Global security manager instance
security_manager = SecurityManager()
