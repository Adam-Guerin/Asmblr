#!/usr/bin/env python3
"""
Security Policy Checker for Asmblr
Validates security configurations and policies
"""

import os
import json
from pathlib import Path
from typing import Any
from loguru import logger

class SecurityPolicyChecker:
    """Validates security policies and configurations"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passes = []
        
        # Security policies
        self.policies = {
            'password_strength': {
                'min_length': 16,
                'require_uppercase': True,
                'require_lowercase': True,
                'require_digits': True,
                'require_special': True
            },
            'api_security': {
                'require_auth': True,
                'rate_limiting': True,
                'cors_enabled': True,
                'https_only': True,
                'secure_headers': True
            },
            'data_protection': {
                'encryption_at_rest': True,
                'data_redaction': True,
                'audit_logging': True,
                'retention_policy': True
            },
            'infrastructure': {
                'network_isolation': True,
                'resource_limits': True,
                'health_checks': True,
                'monitoring_enabled': True
            }
        }
    
    def check_all_policies(self) -> dict[str, Any]:
        """Run all security policy checks"""
        logger.info("🔒 Running comprehensive security policy checks")
        
        # Check password policies
        self._check_password_policies()
        
        # Check API security
        self._check_api_security()
        
        # Check data protection
        self._check_data_protection()
        
        # Check infrastructure security
        self._check_infrastructure_security()
        
        # Check Docker security
        self._check_docker_security()
        
        # Check environment variables
        self._check_environment_variables()
        
        # Generate report
        report = self._generate_report()
        
        return report
    
    def _check_password_policies(self):
        """Check password-related security policies"""
        try:
            # Check for default passwords
            default_passwords = [
                'password', 'admin', 'root', 'user', 'test', 'demo',
                '123456', 'password123', 'admin123', 'changeme'
            ]
            
            # Check .env file for default passwords
            env_file = Path('.env')
            if env_file.exists():
                with open(env_file) as f:
                    content = f.read().lower()
                    for pwd in default_passwords:
                        if pwd in content:
                            self.issues.append(f"Default password found: {pwd}")
            
            # Check password requirements in configuration
            min_length = self.policies['password_strength']['min_length']
            if os.getenv('UI_PASSWORD', '').strip() and len(os.getenv('UI_PASSWORD')) < min_length:
                self.warnings.append(f"UI password shorter than {min_length} characters")
            
            logger.info("✅ Password policies checked")
            
        except Exception as e:
            logger.error(f"Error checking password policies: {e}")
    
    def _check_api_security(self):
        """Check API security configurations"""
        try:
            # Check authentication requirements
            if not os.getenv("API_KEY") and not os.getenv("AUTH_ENABLED", "false").lower() == "true":
                self.issues.append("API authentication not enabled")
            
            # Check HTTPS requirements
            if not os.getenv("HTTPS_ENABLED", "false").lower() == "true":
                self.issues.append("HTTPS not enabled")
            
            # Check rate limiting
            if not os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true":
                self.warnings.append("Rate limiting not enabled")
            
            # Check CORS configuration
            if not os.getenv("CORS_ORIGINS"):
                self.warnings.append("CORS origins not configured")
            
            # Check secure headers
            secure_headers = [
                "SECURE_COOKIES",
                "HSTS_ENABLED",
                "CSP_ENABLED"
            ]
            for header in secure_headers:
                if not os.getenv(header, "false").lower() == "true":
                    self.warnings.append(f"Security header not enabled: {header}")
            
            logger.info("✅ API security checked")
            
        except Exception as e:
            logger.error(f"Error checking API security: {e}")
    
    def _check_data_protection(self):
        """Check data protection measures"""
        try:
            # Check encryption at rest
            if not os.getenv("ENCRYPTION_KEY"):
                self.issues.append("Encryption key not configured")
            
            # Check data redaction
            if not os.getenv("ENABLE_DATA_REDACTION", "true").lower() == "true":
                self.warnings.append("Data redaction not enabled")
            
            # Check audit logging
            if not os.getenv("AUDIT_LOG_ENABLED", "true").lower() == "true":
                self.warnings.append("Audit logging not enabled")
            
            # Check retention policies
            if not os.getenv("DATA_RETENTION_ENABLED", "true").lower() == "true":
                self.warnings.append("Data retention not enabled")
            
            logger.info("✅ Data protection checked")
            
        except Exception as e:
            logger.error(f"Error checking data protection: {e}")
    
    def _check_infrastructure_security(self):
        """Check infrastructure security"""
        try:
            # Check network isolation
            if not os.getenv("NETWORK_ISOLATION", "true").lower() == "true":
                self.warnings.append("Network isolation not enabled")
            
            # Check resource limits
            if not os.getenv("RESOURCE_LIMITS_ENABLED", "true").lower() == "true":
                self.warnings.append("Resource limits not enabled")
            
            # Check health checks
            health_checks = [
                "HEALTH_CHECK_ENABLED",
                "API_HEALTH_CHECK",
                "UI_HEALTH_CHECK",
                "WORKER_HEALTH_CHECK"
            ]
            for check in health_checks:
                if not os.getenv(check, "true").lower() == "true":
                    self.warnings.append(f"Health check not enabled: {check}")
            
            # Check monitoring
            if not os.getenv("MONITORING_ENABLED", "true").lower() == "true":
                self.warnings.append("Monitoring not enabled")
            
            logger.info("✅ Infrastructure security checked")
            
        except Exception as e:
            logger.error(f"Error checking infrastructure security: {e}")
    
    def _check_docker_security(self):
        """Check Docker security configurations"""
        try:
            # Check if Docker files exist
            docker_files = [
                'Dockerfile',
                'docker-compose.yml',
                'docker-compose.secure.yml'
            ]
            
            for docker_file in docker_files:
                if not Path(docker_file).exists():
                    self.warnings.append(f"Docker file not found: {docker_file}")
            
            # Check Docker security best practices
            dockerfile_path = Path('Dockerfile')
            if dockerfile_path.exists():
                with open(dockerfile_path) as f:
                    content = f.read().lower()
                    
                    # Check for root user
                    if 'from root' in content:
                        self.issues.append("Dockerfile uses root user")
                    
                    # Check for sudo usage
                    if 'sudo ' in content:
                        self.warnings.append("Dockerfile uses sudo")
                    
                    # Check for sensitive data in Dockerfile
                    sensitive_patterns = ['password', 'key', 'secret', 'token']
                    for pattern in sensitive_patterns:
                        if pattern in content:
                            self.issues.append(f"Sensitive data in Dockerfile: {pattern}")
            
            # Check docker-compose security
            compose_files = [
                'docker-compose.yml',
                'docker-compose.secure.yml'
            ]
            
            for compose_file in compose_files:
                if Path(compose_file).exists():
                    with open(compose_file) as f:
                        content = f.read().lower()
                    
                    # Check for exposed ports
                    if 'ports:' in content and '127.0.0.1:' not in content:
                        self.warnings.append("Docker compose exposes ports to all interfaces")
                    
                    # Check for environment variables with secrets
                    if 'password=' in content or 'secret=' in content or 'key=' in content:
                        self.issues.append("Docker compose contains sensitive data")
            
            logger.info("✅ Docker security checked")
            
        except Exception as e:
            logger.error(f"Error checking Docker security: {e}")
    
    def _check_environment_variables(self):
        """Check environment variables for security issues"""
        try:
            # Check for sensitive data in environment files
            env_files = ['.env', '.env.example', '.env.production']
            
            sensitive_patterns = [
                'password', 'secret', 'key', 'token', 'api_key',
                'private_key', 'access_token', 'auth_token'
            ]
            
            for env_file in env_files:
                if Path(env_file).exists():
                    with open(env_file) as f:
                        content = f.read().lower()
                        
                        for pattern in sensitive_patterns:
                            if pattern in content:
                                self.warnings.append(f"Sensitive pattern '{pattern}' found in {env_file}")
            
            # Check for hardcoded secrets in code
            code_patterns = [
                'password = "', 'secret = "', 'key = "',
                'token = "', 'api_key = "',
                'private_key = "', 'access_token = "'
            ]
            
            python_files = list(Path('.').rglob('**/*.py'))
            for py_file in python_files:
                try:
                    with open(py_file) as f:
                        content = f.read()
                        for pattern in code_patterns:
                            if pattern in content:
                                self.issues.append(f"Hardcoded secret found in {py_file}")
                except Exception:
                    continue
            
            logger.info("✅ Environment variables checked")
            
        except Exception as e:
            logger.error(f"Error checking environment variables: {e}")
    
    def _generate_report(self) -> dict[str, Any]:
        """Generate comprehensive security report"""
        try:
            report = {
                'scan_timestamp': time.time(),
                'total_issues': len(self.issues),
                'total_warnings': len(self.warnings),
                'total_passes': len(self.passes),
                'policies': self.policies,
                'issues': self.issues,
                'warnings': self.warnings,
                'passes': self.passes,
                'score': self._calculate_security_score(),
                'recommendations': self._get_recommendations()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate security report: {e}")
            return {}
    
    def _calculate_security_score(self) -> int:
        """Calculate overall security score (0-100)"""
        try:
            base_score = 100
            
            # Deduct points for issues
            issue_penalty = 10
            warning_penalty = 5
            
            score = base_score - (len(self.issues) * issue_penalty) - (len(self.warnings) * warning_penalty)
            
            # Ensure score doesn't go below 0
            return max(0, score)
            
        except Exception:
            return 0
    
    def _get_recommendations(self) -> list[str]:
        """Get security improvement recommendations"""
        recommendations = []
        
        if len(self.issues) > 0:
            recommendations.append("🚨 Fix critical security issues immediately")
        
        if len(self.warnings) > 0:
            recommendations.append("⚠️ Address security warnings")
        
        if len(self.issues) == 0 and len(self.warnings) == 0:
            recommendations.append("✅ Security configuration is excellent")
        
        return recommendations

# Global security policy checker
security_policy_checker = SecurityPolicyChecker()

if __name__ == "__main__":
    print("🔒 Running Security Policy Check")
    print("=" * 50)
    
    # Run all security checks
    report = security_policy_checker.check_all_policies()
    
    print(f"\n📊 Security Score: {report['score']}/100")
    print(f"🚨 Issues: {report['total_issues']}")
    print(f"⚠️ Warnings: {report['total_warnings']}")
    print(f"✅ Passes: {report['total_passes']}")
    
    if report['issues']:
        print("\n🚨 Critical Issues:")
        for issue in report['issues'][:5]:
            print(f"  - {issue}")
    
    if report['warnings']:
        print("\n⚠️ Warnings:")
        for warning in report['warnings'][:5]:
            print(f"  - {warning}")
    
    print("\n💡 Recommendations:")
    for rec in report['recommendations']:
        print(f"  - {rec}")
    
    # Save report
    try:
        with open('security-policy-report.json', 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Report saved to security-policy-report.json")
    except Exception as e:
        print(f"\n❌ Failed to save report: {e}")
    
    # Exit with appropriate code
    exit(0 if report['score'] >= 80 else 1)
