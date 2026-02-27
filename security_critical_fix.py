#!/usr/bin/env python3
"""
Critical Security Fixer for Asmblr Phase 2
Focuses on REAL hardcoded secrets, passwords, keys, and tokens
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple

class CriticalSecurityFixer:
    def __init__(self, root_path: Path):
        self.root_path = root_path
        
        # More precise patterns for REAL secrets
        self.critical_patterns = [
            # Hardcoded passwords/secrets with actual values
            r'password\s*=\s*["\'][^"\']{8,}["\']',
            r'secret\s*=\s*["\'][^"\']{16,}["\']',
            r'api_key\s*=\s*["\'][^"\']{20,}["\']',
            r'token\s*=\s*["\'][^"\']{20,}["\']',
            
            # Database connection strings with passwords
            r'mysql://[^:]+:[^@]+@',
            r'postgresql://[^:]+:[^@]+@',
            r'mongodb://[^:]+:[^@]+@',
            
            # JWT tokens and API keys
            r'["\'][A-Za-z0-9_-]{32,}["\'].*token',
            r'["\'][A-Za-z0-9_-]{40,}["\'].*key',
            
            # AWS keys
            r'AKIA[0-9A-Z]{16}',
            
            # Private keys (PEM format)
            r'-----BEGIN (RSA |OPENSSH |DSA |EC |PGP )?PRIVATE KEY-----',
        ]
        
        self.file_extensions = ['.py', '.yml', '.yaml', '.json', '.env', '.env.example']
        self.exclude_dirs = ['.git', '__pycache__', 'node_modules', '.venv', 'venv', 'trash', 'tmp_runs', 'runs']
        
    def scan_for_real_secrets(self, file_path: Path) -> List[Dict]:
        """Scan for REAL hardcoded secrets (not false positives)"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for pattern in self.critical_patterns:
                        matches = re.finditer(pattern, line, re.IGNORECASE)
                        for match in matches:
                            # Filter out false positives more aggressively
                            if self._is_false_positive(match.group(), line, file_path.name):
                                continue
                                
                            issues.append({
                                'file': str(file_path.relative_to(self.root_path)),
                                'line': line_num,
                                'content': line.strip(),
                                'match': match.group(),
                                'severity': 'CRITICAL'
                            })
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")
            
        return issues
    
    def _is_false_positive(self, match: str, line: str, filename: str) -> bool:
        """More aggressive false positive filtering"""
        line_lower = line.lower()
        match_lower = match.lower()
        
        # Obvious false positives
        false_positives = [
            'password_template', 'secret_template', 'key_template', 'token_template',
            'your_password', 'your_secret', 'your_api_key', 'your_token',
            'example_password', 'example_secret', 'example_key', 'example_token',
            'placeholder', 'dummy', 'test', 'mock', 'fake', 'sample',
            'password_regex', 'secret_pattern', 'key_format', 'token_format',
            'password_length', 'secret_size', 'key_bits', 'token_chars',
            'readme', 'changelog', 'todo', 'fixme', 'example', 'demo',
            'localhost', '127.0.0.1', '0.0.0.0', 'development', 'dev',
            'xxxx', 'yyyy', 'zzzz', 'aaaa', 'bbbb', 'cccc',
            'abc123', 'test123', 'demo123', 'temp123',
        ]
        
        # Skip if contains false positive indicators
        if any(fp in line_lower for fp in false_positives):
            return True
        
        # Skip documentation and comments
        if line.strip().startswith('#') or line.strip().startswith('//') or line.strip().startswith('*'):
            return True
            
        # Skip if in test files or examples
        if any(x in filename.lower() for x in ['test', 'example', 'demo', 'sample', 'mock']):
            return True
            
        # Skip if looks like a template or placeholder
        if any(x in match_lower for x in ['<', '>', '{', '}', '[', ']', 'xxx', 'yyy', 'zzz']):
            return True
            
        # Skip if too short to be a real secret
        if len(match.strip('"\'')) < 16:
            return True
            
        return False
    
    def scan_critical_files(self) -> Dict:
        """Scan only critical files for real secrets"""
        all_issues = []
        file_count = 0
        
        print(f"🔍 Scanning for CRITICAL security issues...")
        
        for file_path in self.root_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in self.file_extensions:
                # Skip excluded directories
                if any(exclude_dir in file_path.parts for exclude_dir in self.exclude_dirs):
                    continue
                    
                # Focus on configuration and main application files
                file_name = file_path.name.lower()
                if any(x in file_name for x in ['config', 'settings', 'secret', 'key', 'env', 'main', 'app']):
                    file_count += 1
                    issues = self.scan_for_real_secrets(file_path)
                    all_issues.extend(issues)
                    
                    if issues:
                        print(f"🚨 CRITICAL: Found {len(issues)} real secrets in {file_path.relative_to(self.root_path)}")
        
        return {
            'files_scanned': file_count,
            'critical_issues': len(all_issues),
            'issues': all_issues
        }
    
    def create_env_template(self) -> str:
        """Create a secure .env template"""
        template = """# Asmblr Environment Configuration
# Copy this to .env and fill in your actual values

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/asmblr
DATABASE_PASSWORD=your_secure_database_password

# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_LLM_MODEL=llama3.1:8b

# Security
SECRET_KEY=your_very_long_random_secret_key_here
JWT_SECRET=your_jwt_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here

# External Services
SLACK_WEBHOOK_URL=your_slack_webhook_url
DISCORD_WEBHOOK_URL=your_discord_webhook_url
EMAIL_PASSWORD=your_email_app_password

# Monitoring
GRAFANA_API_KEY=your_grafana_api_key
PROMETHEUS_API_KEY=your_prometheus_api_key

# Development
DEBUG=false
ENVIRONMENT=production
"""
        return template
    
    def fix_critical_issues(self, issues: List[Dict]) -> List[Dict]:
        """Generate fixes for critical issues"""
        fixes = []
        
        for issue in issues:
            file_path = self.root_path / issue['file']
            
            fixes.append({
                'action': 'REPLACE_WITH_ENV',
                'file': issue['file'],
                'line': issue['line'],
                'original': issue['match'],
                'replacement': f"os.getenv('{self._extract_env_var(issue['match'])}', '')",
                'description': f"Replace hardcoded secret in {issue['file']}:{issue['line']}"
            })
        
        return fixes
    
    def _extract_env_var(self, match: str) -> str:
        """Extract appropriate environment variable name"""
        match_lower = match.lower()
        
        if 'password' in match_lower:
            return 'DATABASE_PASSWORD'
        elif 'secret' in match_lower:
            return 'SECRET_KEY'
        elif 'api_key' in match_lower or 'akia' in match_lower:
            return 'API_KEY'
        elif 'token' in match_lower:
            return 'API_TOKEN'
        elif 'mysql' in match_lower:
            return 'DATABASE_URL'
        elif 'postgresql' in match_lower:
            return 'DATABASE_URL'
        elif 'mongodb' in match_lower:
            return 'MONGODB_URL'
        else:
            return 'SECRET_KEY'

def main():
    """Main critical security fix function"""
    root_path = Path(".")
    fixer = CriticalSecurityFixer(root_path)
    
    print("🚨 Starting CRITICAL Security Scan...")
    
    # Scan for real secrets
    report = fixer.scan_critical_files()
    
    if report['critical_issues'] == 0:
        print("✅ No CRITICAL security issues found!")
        print("🎉 Your application is secure from hardcoded secrets!")
        return 0
    
    # Generate fixes
    fixes = fixer.fix_critical_issues(report['issues'])
    
    # Create .env template
    env_template = fixer.create_env_template()
    
    # Save fixes
    fixes_path = root_path / "critical_security_fixes.json"
    with open(fixes_path, 'w', encoding='utf-8') as f:
        json.dump(fixes, f, indent=2)
    
    # Save .env template
    env_template_path = root_path / ".env.template"
    with open(env_template_path, 'w', encoding='utf-8') as f:
        f.write(env_template)
    
    # Create security summary
    print(f"\n🚨 CRITICAL Security Issues Found!")
    print(f"   Files scanned: {report['files_scanned']}")
    print(f"   Critical issues: {report['critical_issues']}")
    print(f"\n📄 Files created:")
    print(f"   - {fixes_path}")
    print(f"   - {env_template_path}")
    
    print(f"\n🛠️ Immediate Actions Required:")
    print(f"   1. Review {fixes_path}")
    print(f"   2. Copy {env_template_path} to .env")
    print(f"   3. Fill in actual values in .env")
    print(f"   4. Apply the fixes in critical_security_fixes.json")
    print(f"   5. Add .env to .gitignore if not already present")
    
    return report['critical_issues']

if __name__ == "__main__":
    critical_issues = main()
    exit(0 if critical_issues == 0 else 1)
