#!/usr/bin/env python3
"""
Security Scanner and Fixer for Asmblr Phase 2
Identifies and helps secure hardcoded secrets, passwords, keys, and tokens
"""

import os
import re
import json
from pathlib import Path

class SecurityScanner:
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'authorization\s*=\s*["\'][^"\']+["\']',
            r'bearer\s+["\'][^"\']+["\']',
            r'["\'][A-Za-z0-9_\-\.=+/]{20,}["\']',  # Long base64-like strings
        ]
        
        self.file_extensions = ['.py', '.yml', '.yaml', '.json', '.env', '.env.example', '.md']
        self.exclude_dirs = ['.git', '__pycache__', 'node_modules', '.venv', 'venv']
        
    def scan_file(self, file_path: Path) -> list[dict]:
        """Scan a single file for security issues"""
        issues = []
        try:
            with open(file_path, encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for pattern in self.patterns:
                        matches = re.finditer(pattern, line, re.IGNORECASE)
                        for match in matches:
                            # Filter out false positives
                            if self._is_false_positive(match.group(), line):
                                continue
                                
                            issues.append({
                                'file': str(file_path.relative_to(self.root_path)),
                                'line': line_num,
                                'content': line.strip(),
                                'match': match.group(),
                                'severity': self._get_severity(match.group(), file_path)
                            })
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")
            
        return issues
    
    def _is_false_positive(self, match: str, line: str) -> bool:
        """Filter out obvious false positives"""
        false_positives = [
            'password_template', 'secret_template', 'key_template', 'token_template',
            'your_password', 'your_secret', 'your_api_key', 'your_token',
            'example_password', 'example_secret', 'example_key', 'example_token',
            'placeholder', 'dummy', 'test', 'mock', 'fake',
            'password_regex', 'secret_pattern', 'key_format', 'token_format',
            'password_length', 'secret_size', 'key_bits', 'token_chars',
            'README', 'CHANGELOG', 'TODO', 'FIXME'
        ]
        
        line_lower = line.lower()
        match_lower = match.lower()
        
        return any(fp in line_lower for fp in false_positives)
    
    def _get_severity(self, match: str, file_path: Path) -> str:
        """Determine severity of the match"""
        file_name = file_path.name.lower()
        
        # High severity files
        if any(x in file_name for x in ['.env', 'config', 'settings', 'secrets']):
            return 'HIGH'
        
        # Medium severity files
        if any(x in file_name for x in ['.py', '.yml', '.yaml', '.json']):
            if any(x in match.lower() for x in ['password', 'secret', 'api_key']):
                return 'MEDIUM'
            return 'LOW'
        
        return 'LOW'
    
    def scan_all(self) -> dict:
        """Scan all files and return comprehensive report"""
        all_issues = []
        file_count = 0
        
        print(f"🔍 Scanning {self.root_path} for security issues...")
        
        for file_path in self.root_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in self.file_extensions:
                # Skip excluded directories
                if any(exclude_dir in file_path.parts for exclude_dir in self.exclude_dirs):
                    continue
                    
                file_count += 1
                issues = self.scan_file(file_path)
                all_issues.extend(issues)
                
                if issues:
                    print(f"⚠️  Found {len(issues)} issues in {file_path.relative_to(self.root_path)}")
        
        # Generate summary
        severity_counts = {}
        for issue in all_issues:
            severity = issue['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'total_files_scanned': file_count,
            'total_issues': len(all_issues),
            'severity_breakdown': severity_counts,
            'issues': all_issues
        }
    
    def generate_fixes(self, issues: list[dict]) -> list[dict]:
        """Generate suggested fixes for security issues"""
        fixes = []
        
        for issue in issues:
            file_path = self.root_path / issue['file']
            
            if issue['severity'] == 'HIGH':
                fixes.append({
                    'type': 'REPLACE_WITH_ENV',
                    'file': issue['file'],
                    'line': issue['line'],
                    'original': issue['match'],
                    'suggested': f"os.getenv('{self._extract_key_name(issue['match'])}', '')",
                    'description': 'Replace hardcoded secret with environment variable'
                })
            elif issue['severity'] == 'MEDIUM':
                fixes.append({
                    'type': 'ADD_VALIDATION',
                    'file': issue['file'],
                    'line': issue['line'],
                    'description': 'Add input validation and sanitization'
                })
        
        return fixes
    
    def _extract_key_name(self, match: str) -> str:
        """Extract environment variable name from hardcoded value"""
        if 'password' in match.lower():
            return 'PASSWORD'
        elif 'secret' in match.lower():
            return 'SECRET'
        elif 'api_key' in match.lower():
            return 'API_KEY'
        elif 'token' in match.lower():
            return 'TOKEN'
        else:
            return 'SECRET_KEY'
    
    def create_security_report(self, report: dict) -> str:
        """Create a comprehensive security report"""
        output = []
        output.append("# 🔒 Asmblr Security Scan Report")
        output.append(f"**Generated**: {os.popen('date').read().strip()}")
        output.append("")
        
        # Summary
        output.append("## 📊 Summary")
        output.append(f"- **Files Scanned**: {report['total_files_scanned']}")
        output.append(f"- **Total Issues**: {report['total_issues']}")
        output.append("")
        
        # Severity breakdown
        output.append("## 🚨 Severity Breakdown")
        for severity, count in report['severity_breakdown'].items():
            emoji = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(severity, '⚪')
            output.append(f"- {emoji} **{severity}**: {count}")
        output.append("")
        
        # Top issues by severity
        high_issues = [i for i in report['issues'] if i['severity'] == 'HIGH']
        medium_issues = [i for i in report['issues'] if i['severity'] == 'MEDIUM']
        
        if high_issues:
            output.append("## 🔴 High Severity Issues")
            for issue in high_issues[:10]:  # Show top 10
                output.append(f"**{issue['file']}:{issue['line']}**")
                output.append(f"```")
                output.append(issue['content'])
                output.append("```")
                output.append("")
        
        if medium_issues:
            output.append("## 🟡 Medium Severity Issues (Top 10)")
            for issue in medium_issues[:10]:  # Show top 10
                output.append(f"**{issue['file']}:{issue['line']}**")
                output.append(f"```")
                output.append(issue['content'])
                output.append("```")
                output.append("")
        
        # Recommendations
        output.append("## 🛠️ Security Recommendations")
        output.append("1. **Immediate Actions**:")
        output.append("   - Replace all HIGH severity hardcoded secrets with environment variables")
        output.append("   - Add .env to .gitignore if not already present")
        output.append("   - Rotate any exposed secrets immediately")
        output.append("")
        output.append("2. **Medium Term**:")
        output.append("   - Implement secret management system (HashiCorp Vault, AWS Secrets Manager)")
        output.append("   - Add input validation and sanitization")
        output.append("   - Enable security scanning in CI/CD pipeline")
        output.append("")
        output.append("3. **Long Term**:")
        output.append("   - Regular security audits and penetration testing")
        output.append("   - Implement zero-trust architecture")
        output.append("   - Add comprehensive logging and monitoring")
        
        return "\n".join(output)

def main():
    """Main security scanning function"""
    root_path = Path(".")
    scanner = SecurityScanner(root_path)
    
    print("🔒 Starting Asmblr Security Scan...")
    
    # Perform scan
    report = scanner.scan_all()
    
    # Generate fixes
    fixes = scanner.generate_fixes(report['issues'])
    
    # Create report
    security_report = scanner.create_security_report(report)
    
    # Save report
    report_path = root_path / "SECURITY_SCAN_REPORT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(security_report)
    
    # Save fixes
    fixes_path = root_path / "security_fixes.json"
    with open(fixes_path, 'w', encoding='utf-8') as f:
        json.dump(fixes, f, indent=2)
    
    # Summary
    print(f"\n📊 Scan Complete!")
    print(f"   Files scanned: {report['total_files_scanned']}")
    print(f"   Total issues: {report['total_issues']}")
    print(f"   High severity: {report['severity_breakdown'].get('HIGH', 0)}")
    print(f"   Medium severity: {report['severity_breakdown'].get('MEDIUM', 0)}")
    print(f"   Low severity: {report['severity_breakdown'].get('LOW', 0)}")
    print(f"\n📄 Reports saved:")
    print(f"   - {report_path}")
    print(f"   - {fixes_path}")
    
    return report['total_issues']

if __name__ == "__main__":
    total_issues = main()
    exit(0 if total_issues == 0 else 1)
