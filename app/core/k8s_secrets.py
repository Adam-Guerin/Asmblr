"""
Kubernetes Secrets Manager for Asmblr
Handles Kubernetes secrets with proper encryption and rotation
"""

import os
import base64
from typing import Any
from kubernetes import client, config
from kubernetes.client import V1Secret
from loguru import logger
from app.core.security import security_manager

class KubernetesSecretsManager:
    """Manages Kubernetes secrets for Asmblr deployment"""
    
    def __init__(self):
        self.namespace = os.getenv("K8S_NAMESPACE", "asmblr")
        self.secrets_prefix = "asmblr-"
        
        # Initialize Kubernetes client
        try:
            config.load_kube_config()
            self.k8s_client = client.CoreV1Api()
            logger.info("Kubernetes client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Kubernetes client: {e}")
            self.k8s_client = None
    
    def create_secret(self, name: str, data: dict[str, str], secret_type: str = "Opaque") -> bool:
        """Create a Kubernetes secret"""
        if not self.k8s_client:
            logger.error("Kubernetes client not available")
            return False
        
        try:
            # Prepare secret data (base64 encoded)
            secret_data = {}
            for key, value in data.items():
                secret_data[key] = base64.b64encode(value.encode()).decode()
            
            # Create secret object
            secret = V1Secret(
                metadata={
                    "name": f"{self.secrets_prefix}{name}",
                    "namespace": self.namespace,
                    "labels": {
                        "app": "asmblr",
                        "managed-by": "asmblr-security",
                        "secret-type": secret_type
                    },
                    "annotations": {
                        "created-by": "asmblr-security-manager",
                        "rotation-policy": "automatic"
                    }
                },
                string_data=secret_data,
                type=secret_type
            )
            
            # Create the secret
            self.k8s_client.create_namespaced_secret(
                namespace=self.namespace,
                body=secret
            )
            
            logger.info(f"Kubernetes secret '{name}' created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Kubernetes secret '{name}': {e}")
            return False
    
    def get_secret(self, name: str) -> dict[str, str] | None:
        """Retrieve a Kubernetes secret"""
        if not self.k8s_client:
            logger.error("Kubernetes client not available")
            return None
        
        try:
            secret = self.k8s_client.read_namespaced_secret(
                name=f"{self.secrets_prefix}{name}",
                namespace=self.namespace
            )
            
            # Decode secret data
            decoded_data = {}
            if secret.data:
                for key, value in secret.data.items():
                    decoded_data[key] = base64.b64decode(value).decode()
            
            logger.debug(f"Kubernetes secret '{name}' retrieved successfully")
            return decoded_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve Kubernetes secret '{name}': {e}")
            return None
    
    def update_secret(self, name: str, data: dict[str, str]) -> bool:
        """Update an existing Kubernetes secret"""
        if not self.k8s_client:
            logger.error("Kubernetes client not available")
            return False
        
        try:
            # Get existing secret
            existing_secret = self.k8s_client.read_namespaced_secret(
                name=f"{self.secrets_prefix}{name}",
                namespace=self.namespace
            )
            
            # Update secret data
            secret_data = {}
            for key, value in data.items():
                secret_data[key] = base64.b64encode(value.encode()).decode()
            
            existing_secret.string_data = secret_data
            
            # Update the secret
            self.k8s_client.patch_namespaced_secret(
                name=f"{self.secrets_prefix}{name}",
                namespace=self.namespace,
                body=existing_secret
            )
            
            logger.info(f"Kubernetes secret '{name}' updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update Kubernetes secret '{name}': {e}")
            return False
    
    def delete_secret(self, name: str) -> bool:
        """Delete a Kubernetes secret"""
        if not self.k8s_client:
            logger.error("Kubernetes client not available")
            return False
        
        try:
            self.k8s_client.delete_namespaced_secret(
                name=f"{self.secrets_prefix}{name}",
                namespace=self.namespace
            )
            
            logger.info(f"Kubernetes secret '{name}' deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete Kubernetes secret '{name}': {e}")
            return False
    
    def list_secrets(self) -> list[str]:
        """List all Asmblr secrets"""
        if not self.k8s_client:
            logger.error("Kubernetes client not available")
            return []
        
        try:
            secrets = self.k8s_client.list_namespaced_secret(
                namespace=self.namespace,
                label_selector=f"app=asmblr"
            )
            
            secret_names = []
            for secret in secrets.items:
                # Remove prefix from name
                if secret.metadata.name.startswith(self.secrets_prefix):
                    secret_names.append(secret.metadata.name[len(self.secrets_prefix):])
            
            return secret_names
            
        except Exception as e:
            logger.error(f"Failed to list Kubernetes secrets: {e}")
            return []
    
    def rotate_secret(self, name: str) -> str | None:
        """Rotate a Kubernetes secret"""
        try:
            # Generate new secret value
            current_data = self.get_secret(name)
            if not current_data:
                logger.error(f"Secret '{name}' not found for rotation")
                return None
            
            # Generate new values
            new_data = {}
            for key, old_value in current_data.items():
                if 'password' in key.lower():
                    new_data[key] = security_manager.generate_secure_password()
                elif 'token' in key.lower() or 'key' in key.lower():
                    new_data[key] = security_manager.encrypt_secret(secrets.token_urlsafe(32))
                else:
                    new_data[key] = secrets.token_urlsafe(32)
            
            # Update the secret
            if self.update_secret(name, new_data):
                logger.info(f"Kubernetes secret '{name}' rotated successfully")
                return new_data.get(list(current_data.keys())[0])
            else:
                logger.error(f"Failed to rotate Kubernetes secret '{name}'")
                return None
                
        except Exception as e:
            logger.error(f"Error rotating Kubernetes secret '{name}': {e}")
            return None
    
    def sync_from_local(self, secret_names: list[str]) -> int:
        """Sync local secrets to Kubernetes"""
        synced_count = 0
        
        for secret_name in secret_names:
            try:
                # Get local secret
                local_value = security_manager.get_secret(secret_name)
                if local_value:
                    # Create or update Kubernetes secret
                    if secret_name in self.list_secrets():
                        # Update existing
                        if self.update_secret(secret_name, {secret_name: local_value}):
                            synced_count += 1
                    else:
                        # Create new
                        if self.create_secret(secret_name, {secret_name: local_value}):
                            synced_count += 1
                else:
                    logger.warning(f"Local secret '{secret_name}' not found")
                    
            except Exception as e:
                logger.error(f"Failed to sync secret '{secret_name}': {e}")
        
        logger.info(f"Synced {synced_count} secrets to Kubernetes")
        return synced_count
    
    def sync_to_local(self, secret_names: list[str]) -> int:
        """Sync Kubernetes secrets to local storage"""
        synced_count = 0
        
        for secret_name in secret_names:
            try:
                # Get Kubernetes secret
                k8s_data = self.get_secret(secret_name)
                if k8s_data:
                    # Store in local storage
                    for key, value in k8s_data.items():
                        if security_manager.store_secret(key, value):
                            synced_count += 1
                else:
                    logger.warning(f"Kubernetes secret '{secret_name}' not found")
                    
            except Exception as e:
                logger.error(f"Failed to sync secret '{secret_name}': {e}")
        
        logger.info(f"Synced {synced_count} secrets from Kubernetes")
        return synced_count
    
    def create_tls_secret(self, cert_path: str, key_path: str, name: str = "tls") -> bool:
        """Create a TLS secret for HTTPS"""
        try:
            # Read certificate and key files
            with open(cert_path) as f:
                cert_data = f.read()
            
            with open(key_path) as f:
                key_data = f.read()
            
            # Create TLS secret
            tls_data = {
                'tls.crt': cert_data,
                'tls.key': key_data
            }
            
            return self.create_secret(name, tls_data, "kubernetes.io/tls")
            
        except Exception as e:
            logger.error(f"Failed to create TLS secret: {e}")
            return False
    
    def audit_k8s_secrets(self) -> dict[str, Any]:
        """Generate audit report for Kubernetes secrets"""
        try:
            secrets = self.list_secrets()
            
            audit_report = {
                'total_secrets': len(secrets),
                'secrets_by_type': {},
                'namespace': self.namespace,
                'secrets_list': []
            }
            
            for secret_name in secrets:
                secret_data = self.get_secret(secret_name)
                secret_info = {
                    'name': secret_name,
                    'keys': list(secret_data.keys()) if secret_data else [],
                    'has_tls': 'tls.crt' in (secret_data or {}),
                    'has_password': any('password' in key.lower() for key in (secret_data or {})),
                    'has_token': any('token' in key.lower() for key in (secret_data or {}))
                }
                
                # Categorize by type
                if secret_info['has_tls']:
                    audit_report['secrets_by_type']['TLS'] = audit_report['secrets_by_type'].get('TLS', 0) + 1
                elif secret_info['has_password']:
                    audit_report['secrets_by_type']['Password'] = audit_report['secrets_by_type'].get('Password', 0) + 1
                elif secret_info['has_token']:
                    audit_report['secrets_by_type']['Token'] = audit_report['secrets_by_type'].get('Token', 0) + 1
                else:
                    audit_report['secrets_by_type']['Other'] = audit_report['secrets_by_type'].get('Other', 0) + 1
                
                audit_report['secrets_list'].append(secret_info)
            
            return audit_report
            
        except Exception as e:
            logger.error(f"Failed to generate Kubernetes audit report: {e}")
            return {}

# Global Kubernetes secrets manager instance
k8s_secrets_manager = KubernetesSecretsManager()
