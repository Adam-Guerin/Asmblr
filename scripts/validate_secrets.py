#!/usr/bin/env python
"""
Security secrets validation script for Asmblr
Validates and reports on security configuration and secrets
"""

import os
import json
import logging
from typing import Any
from pathlib import Path

logger = logging.getLogger(__name__)

def validate_secrets(settings: dict[str, Any]) -> dict[str, Any]:
    """Validate security secrets and configuration"""
    
    report = {
        "ok": True,
        "issues": [],
        "recommendations": [],
        "validated_secrets": [],
        "missing_secrets": []
    }
    
    # Critical security secrets
    critical_secrets = {
        "POSTGRES_PASSWORD": {
            "description": "PostgreSQL database password",
            "required": True,
            "validation": lambda x: len(x) >= 12 and x != "change_me_in_production"
        },
        "AWS_SECRET_ACCESS_KEY": {
            "description": "AWS secret access key",
            "required": False,
            "validation": lambda x: len(x) >= 20 and x.startswith("A")  # Basic AWS key format
        },
        "OAUTH2_CLIENT_SECRET": {
            "description": "OAuth2 client secret",
            "required": False,
            "validation": lambda x: len(x) >= 16
        },
        "RDS_MASTER_PASSWORD": {
            "description": "RDS master password",
            "required": False,
            "validation": lambda x: len(x) >= 12 and x != "change_me_in_production"
        },
        "COMMUNICATION_PASSWORD": {
            "description": "Secure communication password",
            "required": False,
            "validation": lambda x: len(x) >= 16
        }
    }
    
    # Validate each secret
    for secret_name, config in critical_secrets.items():
        secret_value = os.getenv(secret_name)
        
        if secret_value:
            try:
                if config["validation"](secret_value):
                    report["validated_secrets"].append({
                        "name": secret_name,
                        "status": "valid",
                        "description": config["description"]
                    })
                else:
                    report["issues"].append({
                        "name": secret_name,
                        "issue": "Invalid format or weak value",
                        "description": config["description"]
                    })
                    report["ok"] = False
            except Exception as e:
                report["issues"].append({
                    "name": secret_name,
                    "issue": f"Validation error: {str(e)}",
                    "description": config["description"]
                })
                report["ok"] = False
        elif config["required"]:
            report["missing_secrets"].append({
                "name": secret_name,
                "description": config["description"]
            })
            report["ok"] = False
        else:
            report["recommendations"].append({
                "name": secret_name,
                "message": f"Consider setting {secret_name} for enhanced security",
                "description": config["description"]
            })
    
    # Check for hardcoded secrets in common files
    hardcoded_secrets = check_hardcoded_secrets()
    if hardcoded_secrets:
        report["issues"].extend(hardcoded_secrets)
        report["ok"] = False
    
    # Security best practices check
    security_checks = check_security_best_practices()
    report["recommendations"].extend(security_checks)
    
    return report

def check_hardcoded_secrets() -> list[dict[str, Any]]:
    """Check for hardcoded secrets in source code"""
    
    hardcoded_patterns = [
        "asmblr_secure_password",
        "secure_password",
        "client_secret':",
        "aws_secret_access_key=",
        "MasterUserPassword='",
        "COMMUNICATION_PASSWORD\""
    ]
    
    issues = []
    
    # Check common source files
    source_files = [
        "deploy_microservices_fixed.py",
        "app/core/enterprise_features.py",
        "app/core/multi_cloud.py",
        "app/core/secure_communication.py"
    ]
    
    for file_path in source_files:
        if Path(file_path).exists():
            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()
                    line_num = 1
                    
                    for line in content.split('\n'):
                        for pattern in hardcoded_patterns:
                            if pattern in line and not line.strip().startswith('#'):
                                issues.append({
                                    "name": "hardcoded_secret",
                                    "issue": f"Hardcoded secret pattern found in {file_path}:{line_num}",
                                    "pattern": pattern,
                                    "line": line.strip()
                                })
                        line_num += 1
            except Exception as e:
                logger.warning(f"Could not check {file_path}: {e}")
    
    return issues

def check_security_best_practices() -> list[dict[str, Any]]:
    """Check security best practices"""
    
    recommendations = []
    
    # Check if .env is in .gitignore
    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        with open(gitignore_path) as f:
            gitignore_content = f.read()
            if ".env" not in gitignore_content:
                recommendations.append({
                    "name": "gitignore_env",
                    "message": "Add .env to .gitignore to prevent committing secrets",
                    "priority": "high"
                })
    else:
        recommendations.append({
            "name": "gitignore_missing",
            "message": "Create .gitignore file and add .env to prevent committing secrets",
            "priority": "high"
        })
    
    # Check for environment variables file
    env_file = Path(".env")
    if env_file.exists():
        recommendations.append({
            "name": "env_file_exists",
            "message": ".env file exists - ensure it's not committed to version control",
            "priority": "medium"
        })
    
    # Check for secrets management
    vault_env = os.getenv("VAULT_ADDR")
    aws_secrets = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    if not vault_env and not aws_secrets:
        recommendations.append({
            "name": "secrets_management",
            "message": "Consider implementing a secrets management system (HashiCorp Vault or AWS Secrets Manager)",
            "priority": "medium"
        })
    
    return recommendations

if __name__ == "__main__":
    # Test the validation
    settings = {}
    report = validate_secrets(settings)
    print(json.dumps(report, indent=2))
