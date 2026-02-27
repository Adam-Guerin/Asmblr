"""
Secure Communication Manager for Asmblr
Handles internal service communication with encryption and authentication
"""

import os
import ssl
import hashlib
import hmac
import secrets
import time
import json
from typing import Dict, Any, Optional, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from loguru import logger
from app.core.security import security_manager

class SecureCommunicationManager:
    """Manages secure internal communication between Asmblr services"""
    
    def __init__(self):
        self.communication_keys_dir = Path(__file__).parent.parent.parent / "secrets" / "communication"
        self.communication_keys_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate communication encryption key
        self.encryption_key = self._get_or_create_communication_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Service authentication tokens
        self.service_tokens = {}
        self.token_expiry = 3600  # 1 hour
        
        # Communication policies
        self.require_encryption = os.getenv("SECURE_COMMUNICATIONS", "true").lower() == "true"
        self.max_message_size = 10 * 1024 * 1024  # 10MB
        self.message_timeout = 30  # 30 seconds
        
        # Service registry
        self.registered_services = {}
        
    def _get_or_create_communication_key(self) -> bytes:
        """Generate or load communication encryption key"""
        key_file = self.communication_keys_dir / "comm_key.enc"
        
        if key_file.exists():
            try:
                with open(key_file, 'r') as f:
                    key_data = base64.b64decode(f.read())
                    return key_data
            except Exception as e:
                logger.error(f"Failed to load communication key: {e}")
        
        # Generate new key
        password = os.getenv("COMMUNICATION_PASSWORD", secrets.token_bytes(32).hex()).encode()
        if not password:
            password = secrets.token_bytes(32)
        
        salt = os.getenv("COMMUNICATION_SALT", "").encode()
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
            with open(key_file, 'w') as f:
                f.write(key.decode())
            logger.info("Communication encryption key generated and saved")
        except Exception as e:
            logger.error(f"Failed to save communication key: {e}")
        
        return base64.urlsafe_b64decode(key)
    
    def register_service(self, service_name: str, service_host: str, service_port: int) -> str:
        """Register a service for secure communication"""
        try:
            # Generate service token
            service_token = secrets.token_urlsafe(32)
            token_expiry = time.time() + self.token_expiry
            
            # Store service info
            self.service_tokens[service_name] = {
                'token': service_token,
                'host': service_host,
                'port': service_port,
                'created_at': time.time(),
                'expires_at': token_expiry,
                'last_seen': time.time()
            }
            
            # Encrypt and store token
            encrypted_token = self.cipher_suite.encrypt(json.dumps({
                'service_name': service_name,
                'token': service_token,
                'expires_at': token_expiry,
                'host': service_host,
                'port': service_port
            }).encode())
            
            self.registered_services[service_name] = {
                'encrypted_token': encrypted_token,
                'host': service_host,
                'port': service_port,
                'created_at': time.time()
            }
            
            logger.info(f"Service '{service_name}' registered for secure communication")
            return service_token
            
        except Exception as e:
            logger.error(f"Failed to register service '{service_name}': {e}")
            return ""
    
    def get_service_token(self, service_name: str) -> Optional[str]:
        """Get authentication token for a service"""
        try:
            if service_name not in self.registered_services:
                logger.warning(f"Service '{service_name}' not registered")
                return None
            
            service_data = self.registered_services[service_name]
            encrypted_token = service_data['encrypted_token']
            
            # Decrypt token
            token_data = json.loads(self.cipher_suite.decrypt(encrypted_token))
            
            # Check if token is expired
            if time.time() > token_data['expires_at']:
                logger.warning(f"Token for service '{service_name}' has expired")
                return None
            
            # Update last seen
            token_data['last_seen'] = time.time()
            self.registered_services[service_name]['last_seen'] = time.time()
            
            return token_data['token']
            
        except Exception as e:
            logger.error(f"Failed to get token for service '{service_name}': {e}")
            return None
    
    def encrypt_message(self, message: str, recipient_service: str) -> Optional[str]:
        """Encrypt a message for a specific service"""
        try:
            if not self.require_encryption:
                return message
            
            # Get recipient's token
            recipient_token = self.get_service_token(recipient_service)
            if not recipient_token:
                logger.error(f"No valid token found for service '{recipient_service}'")
                return None
            
            # Create message metadata
            metadata = {
                'timestamp': time.time(),
                'sender': 'secure_comm_manager',
                'recipient': recipient_service,
                'message_id': secrets.token_urlsafe(16),
                'size': len(message)
            }
            
            # Combine message and metadata
            full_message = json.dumps({
                'metadata': metadata,
                'message': message
            })
            
            # Encrypt message
            encrypted_message = self.cipher_suite.encrypt(full_message.encode())
            
            # Add authentication header
            auth_header = f"Bearer {recipient_token}"
            
            logger.debug(f"Message encrypted for service '{recipient_service}'")
            return encrypted_message.decode()
            
        except Exception as e:
            logger.error(f"Failed to encrypt message for '{recipient_service}': {e}")
            return None
    
    def decrypt_message(self, encrypted_message: str, sender_service: str, auth_header: str = None) -> Optional[str]:
        """Decrypt a message from a service"""
        try:
            if not self.require_encryption:
                return encrypted_message
            
            # Verify authentication
            if auth_header:
                token = auth_header.replace("Bearer ", "")
                service_name = self._get_service_by_token(token)
                if service_name != sender_service:
                    logger.error(f"Authentication failed for service '{sender_service}'")
                    return None
            
            # Decrypt message
            decrypted_data = json.loads(self.cipher_suite.decrypt(encrypted_message.encode()))
            
            # Validate message
            metadata = decrypted_data.get('metadata', {})
            
            # Check message size
            if metadata.get('size', 0) > self.max_message_size:
                logger.error(f"Message too large: {metadata.get('size', 0)} bytes")
                return None
            
            # Check message age
            message_age = time.time() - metadata.get('timestamp', 0)
            if message_age > self.message_timeout:
                logger.error(f"Message too old: {message_age}s")
                return None
            
            # Verify recipient
            if metadata.get('recipient') != sender_service:
                logger.error(f"Message intended for '{metadata.get('recipient')}' but received from '{sender_service}'")
                return None
            
            return decrypted_data.get('message', '')
            
        except Exception as e:
            logger.error(f"Failed to decrypt message: {e}")
            return None
    
    def _get_service_by_token(self, token: str) -> Optional[str]:
        """Get service name by authentication token"""
        try:
            for service_name, token_data in self.service_tokens.items():
                if token_data['token'] == token:
                    return service_name
            return None
        except Exception as e:
            logger.error(f"Failed to find service by token: {e}")
            return None
    
    def create_secure_channel(self, service1: str, service2: str) -> Dict[str, Any]:
        """Create a secure communication channel between two services"""
        try:
            # Get service tokens
            token1 = self.get_service_token(service1)
            token2 = self.get_service_token(service2)
            
            if not token1 or not token2:
                logger.error(f"Cannot create secure channel: missing tokens for services")
                return {}
            
            # Generate channel key
            channel_key = secrets.token_urlsafe(32)
            
            # Create channel metadata
            channel_info = {
                'channel_id': channel_key,
                'service1': service1,
                'service2': service2,
                'created_at': time.time(),
                'last_activity': time.time(),
                'message_count': 0
            }
            
            # Encrypt channel info
            encrypted_channel = self.cipher_suite.encrypt(json.dumps(channel_info).encode())
            
            logger.info(f"Secure channel created between '{service1}' and '{service2}'")
            
            return {
                'channel_id': channel_key,
                'encrypted_channel': encrypted_channel.decode(),
                'service1_token': token1,
                'service2_token': token2
            }
            
        except Exception as e:
            logger.error(f"Failed to create secure channel: {e}")
            return {}
    
    def send_message(self, channel: Dict[str, Any], message: str, sender: str) -> bool:
        """Send a message through a secure channel"""
        try:
            # Determine recipient
            recipient = channel['service2'] if channel['service1'] == sender else channel['service1']
            
            # Encrypt message
            encrypted_message = self.encrypt_message(message, recipient)
            if not encrypted_message:
                return False
            
            # In a real implementation, this would send the message
            # For now, we'll just log it
            logger.info(f"Secure message sent from '{sender}' to '{recipient}'")
            
            # Update channel activity
            channel['last_activity'] = time.time()
            channel['message_count'] = channel.get('message_count', 0) + 1
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def receive_message(self, channel: Dict[str, Any], sender: str) -> Optional[str]:
        """Receive a message from a secure channel"""
        try:
            # Determine sender
            recipient = channel['service2'] if channel['service1'] == sender else channel['service1']
            
            # In a real implementation, this would receive the message
            # For now, we'll just simulate it
            logger.info(f"Secure message received from '{sender}' by '{recipient}'")
            
            # Update channel activity
            channel['last_activity'] = time.time()
            channel['message_count'] = channel.get('message_count', 0) + 1
            
            # Return a sample message for demonstration
            return f"Secure message from {sender} to {recipient}"
            
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            return None
    
    def cleanup_expired_tokens(self) -> int:
        """Clean up expired service tokens"""
        try:
            current_time = time.time()
            expired_tokens = []
            
            for service_name, token_data in self.service_tokens.items():
                if current_time > token_data['expires_at']:
                    expired_tokens.append(service_name)
            
            for token_name in expired_tokens:
                del self.service_tokens[token_name]
                logger.info(f"Cleaned up expired token for service '{token_name}'")
            
            return len(expired_tokens)
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired tokens: {e}")
            return 0
    
    def get_communication_stats(self) -> Dict[str, Any]:
        """Get communication statistics"""
        try:
            current_time = time.time()
            
            stats = {
                'total_services': len(self.registered_services),
                'active_channels': 0,  # Would track active channels
                'total_messages': 0,     # Would track total messages
                'expired_tokens': 0,
                'services': []
            }
            
            for service_name, service_data in self.registered_services.items():
                service_age = current_time - service_data['created_at']
                stats['services'].append({
                    'name': service_name,
                    'age_seconds': service_age,
                    'last_seen': service_data.get('last_seen', 0),
                    'host': service_data['host'],
                    'port': service_data['port']
                })
            
            stats['expired_tokens'] = self.cleanup_expired_tokens()
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get communication stats: {e}")
            return {}

# Global secure communication manager instance
secure_comm_manager = SecureCommunicationManager()
