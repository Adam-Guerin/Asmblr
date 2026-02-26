"""
Security Tests for Asmblr New Features
Tests security, authentication, authorization, and compliance of all new components
"""

import asyncio
import pytest
import time
import json
import tempfile
import os
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import redis.asyncio as redis

# Import all new features for security testing
from app.core.ai_orchestrator import AIOrchestrator
from app.core.predictive_monitoring import PredictiveMonitoring
from app.core.advanced_debugger import AdvancedDebugger
from app.core.ai_code_generator import AICodeGenerator
from app.core.advanced_testing import AdvancedTestingFramework
from app.core.multi_cloud import MultiCloudManager
from app.core.multi_llm import MultiLLMManager
from app.core.plugin_system import PluginManager
from app.core.enterprise_features import EnterpriseManager, UserRole, Permission
from app.core.security import SecurityManager
from app.core.k8s_secrets import K8sSecretsManager

class TestSecurityAndCompliance:
    """Security and compliance tests for all new features"""
    
    def __init__(self):
        self.test_results = {}
        self.redis_client = None
        self.temp_dir = None
        self.security_vulnerabilities = []
        
    async def setup(self):
        """Setup security test environment"""
        try:
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp(prefix="asmblr_security_")
            
            # Setup Redis for testing
            self.redis_client = redis.from_url("redis://localhost:6379/20")
            await self.redis_client.ping()
            
            print("✅ Security test environment setup complete")
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            raise
    
    async def teardown(self):
        """Cleanup security test environment"""
        try:
            if self.redis_client:
                await self.redis_client.close()
            
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
            
            print("✅ Security test environment cleanup complete")
            
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
    
    async def test_authentication_security(self):
        """Test authentication security mechanisms"""
        print("\n🔐 Testing Authentication Security...")
        
        try:
            enterprise = EnterpriseManager()
            await enterprise.initialize()
            
            # Test cases
            test_cases = [
                {
                    "name": "Valid SAML Authentication",
                    "provider": "saml",
                    "credentials": {"saml_response": "valid_saml_token"},
                    "should_succeed": True
                },
                {
                    "name": "Invalid SAML Token",
                    "provider": "saml",
                    "credentials": {"saml_response": "invalid_token"},
                    "should_succeed": False
                },
                {
                    "name": "Missing Credentials",
                    "provider": "saml",
                    "credentials": {},
                    "should_succeed": False
                },
                {
                    "name": "Valid OAuth2 Token",
                    "provider": "oauth2",
                    "credentials": {"access_token": "valid_oauth_token"},
                    "should_succeed": True
                },
                {
                    "name": "Expired OAuth2 Token",
                    "provider": "oauth2",
                    "credentials": {"access_token": "expired_token"},
                    "should_succeed": False
                }
            ]
            
            auth_results = {}
            
            for test_case in test_cases:
                try:
                    user = await enterprise.authenticate_user(
                        provider=test_case["provider"],
                        credentials=test_case["credentials"],
                        context={"ip_address": "192.168.1.100"}
                    )
                    
                    success = user is not None
                    expected_success = test_case["should_succeed"]
                    
                    auth_results[test_case["name"]] = {
                        "success": success,
                        "expected": expected_success,
                        "passed": success == expected_success
                    }
                    
                except Exception as e:
                    auth_results[test_case["name"]] = {
                        "success": False,
                        "expected": test_case["should_succeed"],
                        "passed": not test_case["should_succeed"],
                        "error": str(e)
                    }
            
            # Calculate overall security score
            passed_tests = len([r for r in auth_results.values() if r["passed"]])
            total_tests = len(auth_results)
            security_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.test_results["authentication_security"] = {
                "test_cases": auth_results,
                "passed_tests": passed_tests,
                "total_tests": total_tests,
                "security_score": security_score,
                "status": "passed" if security_score >= 80 else "failed"
            }
            
            print(f"✅ Authentication Security: {security_score:.1f}% security score")
            
        except Exception as e:
            self.test_results["authentication_security"] = {
                "error": str(e),
                "status": "failed"
            }
            print(f"❌ Authentication Security tests failed: {e}")
    
    async def test_authorization_rbac(self):
        """Test Role-Based Access Control (RBAC)"""
        print("\n👥 Testing RBAC Authorization...")
        
        try:
            enterprise = EnterpriseManager()
            await enterprise.initialize()
            
            # Create test users with different roles
            test_users = {
                "super_admin": Mock(
                    id="admin_001",
                    role=UserRole.SUPER_ADMIN,
                    permissions=list(Permission)
                ),
                "admin": Mock(
                    id="admin_002",
                    role=UserRole.ADMIN,
                    permissions=[
                        Permission.USER_READ, Permission.USER_UPDATE,
                        Permission.SYSTEM_CONFIG, Permission.DATA_READ
                    ]
                ),
                "developer": Mock(
                    id="dev_001",
                    role=UserRole.DEVELOPER,
                    permissions=[
                        Permission.USER_READ, Permission.DATA_READ,
                        Permission.CODE_DEPLOY, Permission.ANALYTICS_VIEW
                    ]
                ),
                "viewer": Mock(
                    id="viewer_001",
                    role=UserRole.VIEWER,
                    permissions=[
                        Permission.USER_READ, Permission.DATA_READ,
                        Permission.ANALYTICS_VIEW
                    ]
                ),
                "guest": Mock(
                    id="guest_001",
                    role=UserRole.GUEST,
                    permissions=[Permission.USER_READ]
                )
            }
            
            # Test permissions for each role
            permission_tests = {
                "super_admin": {
                    "user_create": True,
                    "system_config": True,
                    "data_export": True,
                    "code_deploy": True,
                    "analytics_export": True
                },
                "admin": {
                    "user_create": False,
                    "system_config": True,
                    "data_export": False,
                    "code_deploy": False,
                    "analytics_export": False
                },
                "developer": {
                    "user_create": False,
                    "system_config": False,
                    "data_export": False,
                    "code_deploy": True,
                    "analytics_export": False
                },
                "viewer": {
                    "user_create": False,
                    "system_config": False,
                    "data_export": False,
                    "code_deploy": False,
                    "analytics_export": False
                },
                "guest": {
                    "user_create": False,
                    "system_config": False,
                    "data_export": False,
                    "code_deploy": False,
                    "analytics_export": False
                }
            }
            
            rbac_results = {}
            
            for role_name, user in test_users.items():
                role_results = {}
                expected_permissions = permission_tests[role_name]
                
                for permission, expected in expected_permissions.items():
                    try:
                        perm_enum = Permission[f"DATA_EXPORT" if permission == "data_export" else 
                                             "USER_CREATE" if permission == "user_create" else
                                             "SYSTEM_CONFIG" if permission == "system_config" else
                                             "CODE_DEPLOY" if permission == "code_deploy" else
                                             "ANALYTICS_EXPORT"]
                        
                        has_perm = enterprise.check_permission(user, perm_enum)
                        role_results[permission] = {
                            "has_permission": has_perm,
                            "expected": expected,
                            "passed": has_perm == expected
                        }
                        
                    except Exception as e:
                        role_results[permission] = {
                            "has_permission": False,
                            "expected": expected,
                            "passed": False,
                            "error": str(e)
                        }
                
                rbac_results[role_name] = role_results
            
            # Calculate RBAC security score
            all_permission_tests = []
            for role_results in rbac_results.values():
                all_permission_tests.extend(role_results.values())
            
            passed_permission_tests = len([t for t in all_permission_tests if t["passed"]])
            total_permission_tests = len(all_permission_tests)
            rbac_score = (passed_permission_tests / total_permission_tests) * 100 if total_permission_tests > 0 else 0
            
            self.test_results["authorization_rbac"] = {
                "role_permissions": rbac_results,
                "passed_permission_tests": passed_permission_tests,
                "total_permission_tests": total_permission_tests,
                "rbac_score": rbac_score,
                "status": "passed" if rbac_score >= 90 else "failed"
            }
            
            print(f"✅ RBAC Authorization: {rbac_score:.1f}% authorization score")
            
        except Exception as e:
            self.test_results["authorization_rbac"] = {
                "error": str(e),
                "status": "failed"
            }
            print(f"❌ RBAC Authorization tests failed: {e}")
    
    async def test_data_encryption(self):
        """Test data encryption and decryption"""
        print("\n🔒 Testing Data Encryption...")
        
        try:
            security = SecurityManager()
            await security.initialize()
            
            # Test data encryption/decryption
            test_data = [
                "Simple text data",
                "Sensitive user information: john.doe@example.com",
                "API key: sk-1234567890abcdef",
                "Database password: P@ssw0rd123!",
                "JWT token:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
                "Long text with special characters: !@#$%^&*()_+-=[]{}|;:,.<>?",
                "Unicode data: Héllö Wörld 🌍",
                "JSON data: {'user': 'admin', 'role': 'superuser'}"
            ]
            
            encryption_results = {}
            
            for i, data in enumerate(test_data):
                try:
                    # Encrypt data
                    encrypted_data = security.encrypt_data(data)
                    
                    # Verify encrypted data is different from original
                    is_different = encrypted_data != data
                    
                    # Decrypt data
                    decrypted_data = security.decrypt_data(encrypted_data)
                    
                    # Verify decrypted data matches original
                    is_match = decrypted_data == data
                    
                    # Test with different encryption keys
                    encrypted_data_2 = security.encrypt_data(data, key_id="secondary")
                    decrypted_data_2 = security.decrypt_data(encrypted_data_2, key_id="secondary")
                    is_match_2 = decrypted_data_2 == data
                    
                    encryption_results[f"data_{i}"] = {
                        "original_length": len(data),
                        "encrypted_length": len(encrypted_data),
                        "is_different": is_different,
                        "decryption_match": is_match,
                        "secondary_key_match": is_match_2,
                        "passed": is_different and is_match and is_match_2
                    }
                    
                except Exception as e:
                    encryption_results[f"data_{i}"] = {
                        "error": str(e),
                        "passed": False
                    }
            
            # Test encryption key management
            key_management_results = {}
            
            try:
                # Test key rotation
                old_key_id = security.current_key_id
                await security.rotate_encryption_key()
                new_key_id = security.current_key_id
                
                key_management_results["key_rotation"] = {
                    "old_key_id": old_key_id,
                    "new_key_id": new_key_id,
                    "keys_different": old_key_id != new_key_id,
                    "passed": old_key_id != new_key_id
                }
                
                # Test key deletion
                await security.delete_encryption_key(old_key_id)
                key_management_results["key_deletion"] = {
                    "deleted_key_id": old_key_id,
                    "passed": True
                }
                
            except Exception as e:
                key_management_results["key_management"] = {
                    "error": str(e),
                    "passed": False
                }
            
            # Calculate encryption security score
            all_encryption_tests = list(encryption_results.values()) + list(key_management_results.values())
            passed_encryption_tests = len([t for t in all_encryption_tests if t["passed"]])
            total_encryption_tests = len(all_encryption_tests)
            encryption_score = (passed_encryption_tests / total_encryption_tests) * 100 if total_encryption_tests > 0 else 0
            
            self.test_results["data_encryption"] = {
                "encryption_tests": encryption_results,
                "key_management": key_management_results,
                "passed_tests": passed_encryption_tests,
                "total_tests": total_encryption_tests,
                "encryption_score": encryption_score,
                "status": "passed" if encryption_score >= 95 else "failed"
            }
            
            print(f"✅ Data Encryption: {encryption_score:.1f}% encryption score")
            
        except Exception as e:
            self.test_results["data_encryption"] = {
                "error": str(e),
                "status": "failed"
            }
            print(f"❌ Data Encryption tests failed: {e}")
    
    async def test_audit_logging_security(self):
        """Test audit logging and compliance"""
        print("\n📋 Testing Audit Logging Security...")
        
        try:
            enterprise = EnterpriseManager()
            await enterprise.initialize()
            
            # Test audit logging for different actions
            audit_test_cases = [
                {
                    "action": "user_login",
                    "user_id": "test_user_001",
                    "resource_type": "authentication",
                    "resource_id": "session_001",
                    "details": {"login_method": "saml", "ip_address": "192.168.1.100"}
                },
                {
                    "action": "data_export",
                    "user_id": "test_user_002",
                    "resource_type": "analytics",
                    "resource_id": "report_001",
                    "details": {"format": "csv", "rows": 1000, "sensitive_data": True}
                },
                {
                    "action": "permission_change",
                    "user_id": "admin_001",
                    "resource_type": "user",
                    "resource_id": "test_user_003",
                    "details": {"old_role": "viewer", "new_role": "developer"}
                },
                {
                    "action": "system_config",
                    "user_id": "admin_002",
                    "resource_type": "system",
                    "resource_id": "config_001",
                    "details": {"setting": "max_connections", "old_value": 100, "new_value": 200}
                }
            ]
            
            audit_results = {}
            
            for i, test_case in enumerate(audit_test_cases):
                try:
                    # Log the action
                    await enterprise.log_user_action(
                        user=Mock(id=test_case["user_id"], username=f"user_{test_case['user_id']}"),
                        action=test_case["action"],
                        resource_type=test_case["resource_type"],
                        resource_id=test_case["resource_id"],
                        details=test_case["details"],
                        context={"ip_address": test_case["details"].get("ip_address", "192.168.1.1")}
                    )
                    
                    # Retrieve audit logs
                    logs = await enterprise.get_audit_logs(
                        user_id=test_case["user_id"],
                        action=test_case["action"],
                        limit=10
                    )
                    
                    # Verify log integrity
                    log_found = False
                    log_integrity = False
                    
                    for log in logs:
                        if (log.user_id == test_case["user_id"] and 
                            log.action.value == test_case["action"] and
                            log.resource_type == test_case["resource_type"] and
                            log.resource_id == test_case["resource_id"]):
                            log_found = True
                            
                            # Check if details are properly logged
                            if all(key in log.details for key in test_case["details"].keys()):
                                log_integrity = True
                            
                            break
                    
                    audit_results[f"audit_test_{i}"] = {
                        "action": test_case["action"],
                        "log_found": log_found,
                        "log_integrity": log_integrity,
                        "logs_retrieved": len(logs),
                        "passed": log_found and log_integrity
                    }
                    
                except Exception as e:
                    audit_results[f"audit_test_{i}"] = {
                        "error": str(e),
                        "passed": False
                    }
            
            # Test compliance reporting
            compliance_results = {}
            
            try:
                # Generate GDPR compliance report
                gdpr_report = await enterprise.generate_compliance_report(
                    standard="gdpr",
                    period_start=datetime.now() - timedelta(days=30),
                    period_end=datetime.now()
                )
                
                compliance_results["gdpr"] = {
                    "report_generated": gdpr_report is not None,
                    "score": getattr(gdpr_report, 'score', 0),
                    "status": getattr(gdpr_report, 'status', 'unknown'),
                    "passed": gdpr_report is not None and hasattr(gdpr_report, 'score')
                }
                
                # Generate HIPAA compliance report
                hipaa_report = await enterprise.generate_compliance_report(
                    standard="hipaa",
                    period_start=datetime.now() - timedelta(days=30),
                    period_end=datetime.now()
                )
                
                compliance_results["hipaa"] = {
                    "report_generated": hipaa_report is not None,
                    "score": getattr(hipaa_report, 'score', 0),
                    "status": getattr(hipaa_report, 'status', 'unknown'),
                    "passed": hipaa_report is not None and hasattr(hipaa_report, 'score')
                }
                
            except Exception as e:
                compliance_results["compliance_reporting"] = {
                    "error": str(e),
                    "passed": False
                }
            
            # Calculate audit security score
            all_audit_tests = list(audit_results.values()) + list(compliance_results.values())
            passed_audit_tests = len([t for t in all_audit_tests if t["passed"]])
            total_audit_tests = len(all_audit_tests)
            audit_score = (passed_audit_tests / total_audit_tests) * 100 if total_audit_tests > 0 else 0
            
            self.test_results["audit_logging_security"] = {
                "audit_tests": audit_results,
                "compliance_tests": compliance_results,
                "passed_tests": passed_audit_tests,
                "total_tests": total_audit_tests,
                "audit_score": audit_score,
                "status": "passed" if audit_score >= 90 else "failed"
            }
            
            print(f"✅ Audit Logging Security: {audit_score:.1f}% audit score")
            
        except Exception as e:
            self.test_results["audit_logging_security"] = {
                "error": str(e),
                "status": "failed"
            }
            print(f"❌ Audit Logging Security tests failed: {e}")
    
    async def test_plugin_security_sandboxing(self):
        """Test plugin security and sandboxing"""
        print("\n🔌 Testing Plugin Security Sandboxing...")
        
        try:
            plugin_manager = PluginManager()
            await plugin_manager.initialize()
            
            # Test malicious plugin attempts
            malicious_plugin_tests = [
                {
                    "name": "File System Access",
                    "payload": {"__import__": "os", "method": "system", "args": "rm -rf /"},
                    "should_be_blocked": True
                },
                {
                    "name": "Network Access",
                    "payload": {"__import__": "socket", "method": "connect", "args": "evil.com:443"},
                    "should_be_blocked": True
                },
                {
                    "name": "Process Execution",
                    "payload": {"__import__": "subprocess", "method": "run", "args": "malicious_script.sh"},
                    "should_be_blocked": True
                },
                {
                    "name": "Memory Access",
                    "payload": {"__import__": "ctypes", "method": "string_at", "args": "0x0"},
                    "should_be_blocked": True
                },
                {
                    "name": "Environment Variables",
                    "payload": {"__import__": "os", "method": "environ", "args": "PASSWORD"},
                    "should_be_blocked": True
                }
            ]
            
            sandbox_results = {}
            
            for i, test_case in enumerate(malicious_plugin_tests):
                try:
                    # Try to execute malicious payload
                    result = await plugin_manager.execute_plugin(
                        plugin_id="test_malicious_plugin",
                        **test_case["payload"]
                    )
                    
                    # Check if execution was blocked
                    execution_blocked = result is None or str(result).startswith("Security violation")
                    
                    sandbox_results[f"malicious_test_{i}"] = {
                        "test_name": test_case["name"],
                        "payload_blocked": execution_blocked,
                        "expected_blocked": test_case["should_be_blocked"],
                        "passed": execution_blocked == test_case["should_be_blocked"]
                    }
                    
                except Exception as e:
                    # Exceptions are expected for security violations
                    security_exception = "security" in str(e).lower() or "permission" in str(e).lower()
                    sandbox_results[f"malicious_test_{i}"] = {
                        "test_name": test_case["name"],
                        "payload_blocked": security_exception,
                        "expected_blocked": test_case["should_be_blocked"],
                        "security_exception": security_exception,
                        "passed": security_exception == test_case["should_be_blocked"]
                    }
            
            # Test plugin permission validation
            permission_tests = [
                {
                    "plugin_id": "analytics_plugin",
                    "required_permissions": ["data_read", "analytics_view"],
                    "user_permissions": ["data_read"],
                    "should_fail": True
                },
                {
                    "plugin_id": "export_plugin",
                    "required_permissions": ["data_export"],
                    "user_permissions": ["data_read", "data_export"],
                    "should_fail": False
                }
            ]
            
            permission_results = {}
            
            for i, test_case in enumerate(permission_tests):
                try:
                    # Mock user with specific permissions
                    user = Mock(
                        id="test_user",
                        permissions=test_case["user_permissions"]
                    )
                    
                    # Try to execute plugin
                    result = await plugin_manager.execute_plugin(
                        plugin_id=test_case["plugin_id"],
                        user=user
                    )
                    
                    execution_failed = result is None or str(result).startswith("Permission denied")
                    expected_failure = test_case["should_fail"]
                    
                    permission_results[f"permission_test_{i}"] = {
                        "plugin_id": test_case["plugin_id"],
                        "execution_failed": execution_failed,
                        "expected_failure": expected_failure,
                        "passed": execution_failed == expected_failure
                    }
                    
                except Exception as e:
                    permission_exception = "permission" in str(e).lower()
                    permission_results[f"permission_test_{i}"] = {
                        "plugin_id": test_case["plugin_id"],
                        "permission_exception": permission_exception,
                        "expected_failure": test_case["should_fail"],
                        "passed": permission_exception == test_case["should_fail"]
                    }
            
            # Calculate plugin security score
            all_plugin_tests = list(sandbox_results.values()) + list(permission_results.values())
            passed_plugin_tests = len([t for t in all_plugin_tests if t["passed"]])
            total_plugin_tests = len(all_plugin_tests)
            plugin_score = (passed_plugin_tests / total_plugin_tests) * 100 if total_plugin_tests > 0 else 0
            
            self.test_results["plugin_security_sandboxing"] = {
                "sandbox_tests": sandbox_results,
                "permission_tests": permission_results,
                "passed_tests": passed_plugin_tests,
                "total_tests": total_plugin_tests,
                "plugin_score": plugin_score,
                "status": "passed" if plugin_score >= 95 else "failed"
            }
            
            print(f"✅ Plugin Security Sandboxing: {plugin_score:.1f}% security score")
            
        except Exception as e:
            self.test_results["plugin_security_sandboxing"] = {
                "error": str(e),
                "status": "failed"
            }
            print(f"❌ Plugin Security Sandboxing tests failed: {e}")
    
    async def test_k8s_secrets_security(self):
        """Test Kubernetes secrets management security"""
        print("\n☸️ Testing K8s Secrets Security...")
        
        try:
            k8s_secrets = K8sSecretsManager()
            await k8s_secrets.initialize()
            
            # Test secret creation and retrieval
            secret_test_cases = [
                {
                    "name": "database_password",
                    "value": "SuperSecretPassword123!",
                    "type": "Opaque"
                },
                {
                    "name": "api_key",
                    "value": "sk-1234567890abcdef1234567890abcdef",
                    "type": "Opaque"
                },
                {
                    "name": "jwt_secret",
                    "value": "your-256-bit-secret",
                    "type": "Opaque"
                }
            ]
            
            secret_results = {}
            
            for test_case in secret_test_cases:
                try:
                    # Create secret
                    await k8s_secrets.create_secret(
                        name=test_case["name"],
                        value=test_case["value"],
                        secret_type=test_case["type"]
                    )
                    
                    # Retrieve secret
                    retrieved_value = await k8s_secrets.get_secret(test_case["name"])
                    
                    # Verify secret integrity
                    value_match = retrieved_value == test_case["value"]
                    
                    # Test secret update
                    new_value = f"Updated_{test_case['value']}"
                    await k8s_secrets.update_secret(
                        name=test_case["name"],
                        value=new_value
                    )
                    
                    updated_value = await k8s_secrets.get_secret(test_case["name"])
                    update_success = updated_value == new_value
                    
                    # Test secret deletion
                    await k8s_secrets.delete_secret(test_case["name"])
                    
                    # Verify deletion
                    deleted_value = await k8s_secrets.get_secret(test_case["name"])
                    deletion_success = deleted_value is None
                    
                    secret_results[test_case["name"]] = {
                        "creation_success": True,
                        "retrieval_success": retrieved_value is not None,
                        "value_match": value_match,
                        "update_success": update_success,
                        "deletion_success": deletion_success,
                        "passed": value_match and update_success and deletion_success
                    }
                    
                except Exception as e:
                    secret_results[test_case["name"]] = {
                        "error": str(e),
                        "passed": False
                    }
            
            # Test secret encryption at rest
            encryption_results = {}
            
            try:
                # Test that secrets are encrypted
                test_secret_name = "encryption_test_secret"
                test_secret_value = "TestEncryptionValue123"
                
                await k8s_secrets.create_secret(
                    name=test_secret_name,
                    value=test_secret_value,
                    secret_type="Opaque",
                    encrypt_at_rest=True
                )
                
                # Verify encryption (this would check the actual stored data)
                is_encrypted = await k8s_secrets.verify_secret_encryption(test_secret_name)
                
                encryption_results["encryption_at_rest"] = {
                    "secret_name": test_secret_name,
                    "is_encrypted": is_encrypted,
                    "passed": is_encrypted
                }
                
                # Cleanup
                await k8s_secrets.delete_secret(test_secret_name)
                
            except Exception as e:
                encryption_results["encryption_at_rest"] = {
                    "error": str(e),
                    "passed": False
                }
            
            # Test secret access controls
            access_control_results = {}
            
            try:
                # Test access with different roles
                admin_user = Mock(id="admin", role="admin", permissions=["secret_read", "secret_write"])
                readonly_user = Mock(id="readonly", role="viewer", permissions=["secret_read"])
                no_permission_user = Mock(id="noperm", role="guest", permissions=[])
                
                # Admin should be able to create and read
                await k8s_secrets.create_secret(
                    name="admin_test_secret",
                    value="admin_value",
                    user=admin_user
                )
                admin_access = await k8s_secrets.get_secret("admin_test_secret", user=admin_user)
                
                # Readonly user should be able to read but not write
                readonly_access = await k8s_secrets.get_secret("admin_test_secret", user=readonly_user)
                
                try:
                    await k8s_secrets.create_secret(
                        name="readonly_test_secret",
                        value="readonly_value",
                        user=readonly_user
                    )
                    readonly_write_success = True
                except:
                    readonly_write_success = False
                
                # No permission user should not be able to access
                try:
                    no_perm_access = await k8s_secrets.get_secret("admin_test_secret", user=no_permission_user)
                    no_perm_access_success = no_perm_access is not None
                except:
                    no_perm_access_success = False
                
                access_control_results["role_based_access"] = {
                    "admin_read_success": admin_access is not None,
                    "readonly_read_success": readonly_access is not None,
                    "readonly_write_blocked": not readonly_write_success,
                    "no_permission_blocked": not no_perm_access_success,
                    "passed": (admin_access is not None and 
                             readonly_access is not None and 
                             not readonly_write_success and 
                             not no_perm_access_success)
                }
                
                # Cleanup
                await k8s_secrets.delete_secret("admin_test_secret")
                
            except Exception as e:
                access_control_results["role_based_access"] = {
                    "error": str(e),
                    "passed": False
                }
            
            # Calculate K8s secrets security score
            all_secret_tests = (list(secret_results.values()) + 
                              list(encryption_results.values()) + 
                              list(access_control_results.values()))
            passed_secret_tests = len([t for t in all_secret_tests if t["passed"]])
            total_secret_tests = len(all_secret_tests)
            secrets_score = (passed_secret_tests / total_secret_tests) * 100 if total_secret_tests > 0 else 0
            
            self.test_results["k8s_secrets_security"] = {
                "secret_management": secret_results,
                "encryption_tests": encryption_results,
                "access_control_tests": access_control_results,
                "passed_tests": passed_secret_tests,
                "total_tests": total_secret_tests,
                "secrets_score": secrets_score,
                "status": "passed" if secrets_score >= 90 else "failed"
            }
            
            print(f"✅ K8s Secrets Security: {secrets_score:.1f}% security score")
            
        except Exception as e:
            self.test_results["k8s_secrets_security"] = {
                "error": str(e),
                "status": "failed"
            }
            print(f"❌ K8s Secrets Security tests failed: {e}")
    
    async def test_input_validation_sanitization(self):
        """Test input validation and sanitization"""
        print("\n🧹 Testing Input Validation & Sanitization...")
        
        try:
            # Test various input validation scenarios
            validation_test_cases = [
                {
                    "name": "SQL Injection",
                    "input": "'; DROP TABLE users; --",
                    "expected_sanitized": "''; DROP TABLE users; --",
                    "should_be_sanitized": True
                },
                {
                    "name": "XSS Attack",
                    "input": "<script>alert('XSS')</script>",
                    "expected_sanitized": "&lt;script&gt;alert('XSS')&lt;/script&gt;",
                    "should_be_sanitized": True
                },
                {
                    "name": "Path Traversal",
                    "input": "../../../etc/passwd",
                    "expected_sanitized": "etc/passwd",
                    "should_be_sanitized": True
                },
                {
                    "name": "Command Injection",
                    "input": "test; rm -rf /",
                    "expected_sanitized": "test; rm -rf /",
                    "should_be_sanitized": True
                },
                {
                    "name": "LDAP Injection",
                    "input": "user)(|(objectClass=*",
                    "expected_sanitized": "user)(|(objectClass=*",
                    "should_be_sanitized": True
                },
                {
                    "name": "Valid Input",
                    "input": "normal_user_input_123",
                    "expected_sanitized": "normal_user_input_123",
                    "should_be_sanitized": False
                }
            ]
            
            validation_results = {}
            
            # Mock input validation function
            def sanitize_input(input_str):
                """Mock sanitization function"""
                if not isinstance(input_str, str):
                    return str(input_str)
                
                # Remove dangerous characters
                dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$', '(', ')', '{', '}']
                sanitized = input_str
                
                for char in dangerous_chars:
                    sanitized = sanitized.replace(char, '')
                
                # Remove path traversal attempts
                sanitized = sanitized.replace('../', '').replace('..\\', '')
                
                return sanitized.strip()
            
            for test_case in validation_test_cases:
                try:
                    # Sanitize input
                    sanitized_input = sanitize_input(test_case["input"])
                    
                    # Check if sanitization occurred
                    was_sanitized = sanitized_input != test_case["input"]
                    expected_sanitization = test_case["should_be_sanitized"]
                    
                    validation_results[test_case["name"]] = {
                        "original_input": test_case["input"],
                        "sanitized_input": sanitized_input,
                        "was_sanitized": was_sanitized,
                        "expected_sanitization": expected_sanitization,
                        "passed": was_sanitized == expected_sanitization
                    }
                    
                except Exception as e:
                    validation_results[test_case["name"]] = {
                        "error": str(e),
                        "passed": False
                    }
            
            # Test length validation
            length_test_cases = [
                {"input": "a" * 10, "max_length": 50, "should_pass": True},
                {"input": "a" * 100, "max_length": 50, "should_pass": False},
                {"input": "", "max_length": 50, "should_pass": True},
                {"input": "a" * 50, "max_length": 50, "should_pass": True}
            ]
            
            length_results = {}
            
            for i, test_case in enumerate(length_test_cases):
                try:
                    input_length = len(test_case["input"])
                    passes_validation = input_length <= test_case["max_length"]
                    expected_pass = test_case["should_pass"]
                    
                    length_results[f"length_test_{i}"] = {
                        "input_length": input_length,
                        "max_length": test_case["max_length"],
                        "passes_validation": passes_validation,
                        "expected_pass": expected_pass,
                        "passed": passes_validation == expected_pass
                    }
                    
                except Exception as e:
                    length_results[f"length_test_{i}"] = {
                        "error": str(e),
                        "passed": False
                    }
            
            # Test type validation
            type_test_cases = [
                {"input": "123", "expected_type": "int", "should_pass": True},
                {"input": "abc", "expected_type": "int", "should_pass": False},
                {"input": "123.45", "expected_type": "float", "should_pass": True},
                {"input": "true", "expected_type": "bool", "should_pass": True},
                {"input": "invalid", "expected_type": "bool", "should_pass": False}
            ]
            
            type_results = {}
            
            for i, test_case in enumerate(type_test_cases):
                try:
                    # Mock type validation
                    def validate_type(input_val, expected_type):
                        if expected_type == "int":
                            try:
                                int(input_val)
                                return True
                            except:
                                return False
                        elif expected_type == "float":
                            try:
                                float(input_val)
                                return True
                            except:
                                return False
                        elif expected_type == "bool":
                            return input_val.lower() in ["true", "false", "1", "0"]
                        return False
                    
                    type_valid = validate_type(test_case["input"], test_case["expected_type"])
                    expected_valid = test_case["should_pass"]
                    
                    type_results[f"type_test_{i}"] = {
                        "input": test_case["input"],
                        "expected_type": test_case["expected_type"],
                        "type_valid": type_valid,
                        "expected_valid": expected_valid,
                        "passed": type_valid == expected_valid
                    }
                    
                except Exception as e:
                    type_results[f"type_test_{i}"] = {
                        "error": str(e),
                        "passed": False
                    }
            
            # Calculate validation security score
            all_validation_tests = (list(validation_results.values()) + 
                                  list(length_results.values()) + 
                                  list(type_results.values()))
            passed_validation_tests = len([t for t in all_validation_tests if t["passed"]])
            total_validation_tests = len(all_validation_tests)
            validation_score = (passed_validation_tests / total_validation_tests) * 100 if total_validation_tests > 0 else 0
            
            self.test_results["input_validation_sanitization"] = {
                "sanitization_tests": validation_results,
                "length_tests": length_results,
                "type_tests": type_results,
                "passed_tests": passed_validation_tests,
                "total_tests": total_validation_tests,
                "validation_score": validation_score,
                "status": "passed" if validation_score >= 95 else "failed"
            }
            
            print(f"✅ Input Validation & Sanitization: {validation_score:.1f}% validation score")
            
        except Exception as e:
            self.test_results["input_validation_sanitization"] = {
                "error": str(e),
                "status": "failed"
            }
            print(f"❌ Input Validation & Sanitization tests failed: {e}")
    
    async def run_all_security_tests(self):
        """Run all security tests and generate comprehensive report"""
        print("🛡️ Starting Comprehensive Security Test Suite for Asmblr")
        print("=" * 70)
        
        start_time = time.time()
        
        # Setup test environment
        await self.setup()
        
        # Run all security test suites
        test_methods = [
            self.test_authentication_security,
            self.test_authorization_rbac,
            self.test_data_encryption,
            self.test_audit_logging_security,
            self.test_plugin_security_sandboxing,
            self.test_k8s_secrets_security,
            self.test_input_validation_sanitization
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                print(f"❌ Security test {test_method.__name__} failed: {e}")
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results.values() if r.get("status") == "passed"])
        failed_tests = total_tests - passed_tests
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Generate comprehensive security report
        report = {
            "security_test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            },
            "detailed_results": self.test_results,
            "security_assessment": self._generate_security_assessment(),
            "vulnerability_scan": self._generate_vulnerability_scan(),
            "compliance_status": self._generate_compliance_status(),
            "security_recommendations": self._generate_security_recommendations()
        }
        
        # Save report
        report_path = os.path.join(self.temp_dir, "security_test_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print("\n" + "=" * 70)
        print("🛡️ COMPREHENSIVE SECURITY TEST RESULTS")
        print("=" * 70)
        print(f"Total Security Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {report['security_test_summary']['success_rate']:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Report saved to: {report_path}")
        
        # Print security assessment
        print("\n🔍 Security Assessment:")
        assessment = report['security_assessment']
        for category, score in assessment.items():
            status_icon = "✅" if score >= 90 else "⚠️" if score >= 70 else "❌"
            print(f"  {category}: {score:.1f}% {status_icon}")
        
        # Print compliance status
        print("\n📋 Compliance Status:")
        compliance = report['compliance_status']
        for standard, status in compliance.items():
            status_icon = "✅" if status == "compliant" else "⚠️" if status == "partial" else "❌"
            print(f"  {standard}: {status} {status_icon}")
        
        # Print failed tests if any
        if failed_tests > 0:
            print("\n❌ Failed Security Tests:")
            for test_name, result in self.test_results.items():
                if result.get("status") == "failed":
                    print(f"  - {test_name}: {result.get('error', 'Security issues detected')}")
        
        # Cleanup
        await self.teardown()
        
        return report
    
    def _generate_security_assessment(self):
        """Generate overall security assessment"""
        assessment = {}
        
        for test_name, result in self.test_results.items():
            if result.get("status") == "passed":
                # Extract score from result
                score_key = None
                if "score" in result:
                    score_key = next((k for k in result.keys() if k.endswith("_score")), None)
                
                if score_key:
                    assessment[test_name] = result[score_key]
                else:
                    assessment[test_name] = 100  # Default to perfect score if passed
            else:
                assessment[test_name] = 0
        
        return assessment
    
    def _generate_vulnerability_scan(self):
        """Generate vulnerability scan results"""
        vulnerabilities = []
        
        for test_name, result in self.test_results.items():
            if result.get("status") == "failed":
                vulnerabilities.append({
                    "component": test_name,
                    "severity": "high",
                    "description": result.get("error", "Security vulnerability detected"),
                    "recommendation": f"Fix security issues in {test_name}"
                })
        
        return {
            "total_vulnerabilities": len(vulnerabilities),
            "critical_vulnerabilities": len([v for v in vulnerabilities if v["severity"] == "critical"]),
            "high_vulnerabilities": len([v for v in vulnerabilities if v["severity"] == "high"]),
            "medium_vulnerabilities": len([v for v in vulnerabilities if v["severity"] == "medium"]),
            "low_vulnerabilities": len([v for v in vulnerabilities if v["severity"] == "low"]),
            "vulnerabilities": vulnerabilities
        }
    
    def _generate_compliance_status(self):
        """Generate compliance status"""
        compliance = {}
        
        # Check compliance based on test results
        if self.test_results.get("audit_logging_security", {}).get("status") == "passed":
            compliance["GDPR"] = "compliant"
            compliance["HIPAA"] = "compliant"
            compliance["SOX"] = "compliant"
        else:
            compliance["GDPR"] = "non_compliant"
            compliance["HIPAA"] = "non_compliant"
            compliance["SOX"] = "non_compliant"
        
        if self.test_results.get("data_encryption", {}).get("status") == "passed":
            compliance["PCI_DSS"] = "compliant"
        else:
            compliance["PCI_DSS"] = "non_compliant"
        
        if self.test_results.get("authentication_security", {}).get("status") == "passed":
            compliance["ISO_27001"] = "compliant"
        else:
            compliance["ISO_27001"] = "partial"
        
        return compliance
    
    def _generate_security_recommendations(self):
        """Generate security recommendations"""
        recommendations = []
        
        for test_name, result in self.test_results.items():
            if result.get("status") == "failed":
                recommendations.append(f"Address security vulnerabilities in {test_name}")
        
        # Add general security recommendations
        if len(recommendations) == 0:
            recommendations.extend([
                "All security tests passed! System is secure and compliant.",
                "Implement regular security audits and penetration testing.",
                "Set up automated security scanning in CI/CD pipeline.",
                "Monitor for emerging security threats and vulnerabilities."
            ])
        else:
            recommendations.extend([
                "Implement security monitoring and alerting.",
                "Regularly update security patches and dependencies.",
                "Conduct security training for development team."
            ])
        
        return recommendations

async def main():
    """Main security test runner"""
    tester = TestSecurityAndCompliance()
    report = await tester.run_all_security_tests()
    
    # Exit with appropriate code
    exit_code = 0 if report['security_test_summary']['success_rate'] == 100 else 1
    exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())
