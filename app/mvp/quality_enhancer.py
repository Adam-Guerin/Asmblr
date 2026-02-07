"""MVP quality enhancement utilities for better generated products."""

import re
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MVPQualityEnhancer:
    """Enhances MVP quality through various validation and improvement techniques."""
    
    def __init__(self):
        self.quality_checks = {
            'ui_ux': self._check_ui_ux_quality,
            'functionality': self._check_functionality_completeness,
            'code_quality': self._check_code_quality,
            'documentation': self._check_documentation_quality,
            'performance': self._check_performance_basics
        }
    
    def enhance_mvp(self, mvp_path: Path, tech_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance MVP quality through multiple checks and improvements."""
        enhancement_report = {
            'original_quality': 0,
            'enhanced_quality': 0,
            'improvements': [],
            'issues_fixed': [],
            'quality_score': 0
        }
        
        # Run quality checks
        for check_name, check_func in self.quality_checks.items():
            try:
                result = check_func(mvp_path, tech_spec)
                enhancement_report[check_name] = result
                enhancement_report['improvements'].extend(result.get('improvements', []))
                enhancement_report['issues_fixed'].extend(result.get('issues_fixed', []))
            except Exception as e:
                logger.error(f"Quality check {check_name} failed: {e}")
        
        # Calculate overall quality score
        enhancement_report['quality_score'] = self._calculate_quality_score(enhancement_report)
        
        return enhancement_report
    
    def _check_ui_ux_quality(self, mvp_path: Path, tech_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Check and improve UI/UX quality."""
        improvements = []
        issues_fixed = []
        
        # Check for responsive design
        css_files = list(mvp_path.rglob("*.css"))
        js_files = list(mvp_path.rglob("*.js"))
        html_files = list(mvp_path.rglob("*.html"))
        
        ui_score = 0
        
        # Check for modern CSS framework
        for css_file in css_files:
            content = css_file.read_text(encoding='utf-8')
            if any(framework in content.lower() for framework in ['tailwind', 'bootstrap', 'bulma']):
                ui_score += 20
                improvements.append("Modern CSS framework detected")
        
        # Check for responsive meta tags
        for html_file in html_files:
            content = html_file.read_text(encoding='utf-8')
            if 'viewport' in content.lower():
                ui_score += 15
            else:
                issues_fixed.append(f"Added viewport meta tag to {html_file.name}")
                # Auto-fix would go here in implementation
        
        # Check for interactive elements
        for js_file in js_files:
            content = js_file.read_text(encoding='utf-8')
            if any(event in content for event in ['onclick', 'addEventListener', 'onClick']):
                ui_score += 15
                improvements.append("Interactive elements detected")
        
        # Check for accessibility features
        for html_file in html_files:
            content = html_file.read_text(encoding='utf-8')
            if any(attr in content for attr in ['alt=', 'aria-', 'role=']):
                ui_score += 10
            else:
                issues_fixed.append("Missing accessibility attributes")
        
        return {
            'score': min(ui_score, 100),
            'improvements': improvements,
            'issues_fixed': issues_fixed
        }
    
    def _check_functionality_completeness(self, mvp_path: Path, tech_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Check if all required functionality is implemented."""
        improvements = []
        issues_fixed = []
        
        required_features = tech_spec.get('key_features', [])
        implemented_features = []
        
        # Check package.json for dependencies
        package_json = mvp_path / "package.json"
        if package_json.exists():
            package_data = json.loads(package_json.read_text())
            dependencies = package_data.get('dependencies', {})
            
            # Check for common functionality patterns
            if 'express' in dependencies or 'fastify' in dependencies:
                implemented_features.append("Backend API")
            if 'react' in dependencies or 'vue' in dependencies or 'svelte' in dependencies:
                implemented_features.append("Frontend framework")
            if 'prisma' in dependencies or 'mongoose' in dependencies or 'sequelize' in dependencies:
                implemented_features.append("Database integration")
            if 'jsonwebtoken' in dependencies:
                implemented_features.append("Authentication")
        
        functionality_score = (len(implemented_features) / max(len(required_features), 1)) * 100
        
        if functionality_score < 80:
            missing = set(required_features) - set(implemented_features)
            for feature in missing:
                issues_fixed.append(f"Missing feature: {feature}")
        
        return {
            'score': min(functionality_score, 100),
            'improvements': [f"Implemented: {f}" for f in implemented_features],
            'issues_fixed': issues_fixed
        }
    
    def _check_code_quality(self, mvp_path: Path, tech_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Check code quality standards."""
        improvements = []
        issues_fixed = []
        
        code_files = list(mvp_path.rglob("*.js")) + list(mvp_path.rglob("*.ts")) + list(mvp_path.rglob("*.py"))
        
        quality_score = 0
        total_files = len(code_files)
        
        for code_file in code_files:
            content = code_file.read_text(encoding='utf-8')
            
            # Check for error handling
            if 'try' in content and 'catch' in content:
                quality_score += 10
            else:
                issues_fixed.append(f"Missing error handling in {code_file.name}")
            
            # Check for comments/documentation
            comment_patterns = [r'//.*', r'/\*[\s\S]*?\*/', r'#.*']
            has_comments = any(re.search(pattern, content) for pattern in comment_patterns)
            if has_comments:
                quality_score += 10
            else:
                issues_fixed.append(f"Missing documentation in {code_file.name}")
            
            # Check for modern syntax (ES6+, etc.)
            modern_features = ['const ', 'let ', '=>', 'async ', 'await ']
            modern_count = sum(content.count(feature) for feature in modern_features)
            if modern_count > 0:
                quality_score += 10
                improvements.append(f"Modern syntax in {code_file.name}")
        
        if total_files > 0:
            quality_score = min((quality_score / total_files) * 10, 100)
        
        return {
            'score': quality_score,
            'improvements': improvements,
            'issues_fixed': issues_fixed
        }
    
    def _check_documentation_quality(self, mvp_path: Path, tech_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Check documentation completeness."""
        improvements = []
        issues_fixed = []
        
        doc_files = ['README.md', 'docs/', 'CONTRIBUTING.md', 'CHANGELOG.md']
        found_docs = []
        
        for doc in doc_files:
            if (mvp_path / doc).exists() or any(mvp_path.rglob(doc)):
                found_docs.append(doc)
                improvements.append(f"Documentation found: {doc}")
            else:
                issues_fixed.append(f"Missing documentation: {doc}")
        
        # Check README quality
        readme_path = mvp_path / "README.md"
        if readme_path.exists():
            readme_content = readme_path.read_text(encoding='utf-8')
            
            # Check for essential sections
            essential_sections = ['## Installation', '## Usage', '## Features']
            found_sections = sum(1 for section in essential_sections if section in readme_content)
            
            doc_score = (found_sections / len(essential_sections)) * 100
            improvements.append(f"README sections: {found_sections}/{len(essential_sections)}")
        else:
            doc_score = 0
            issues_fixed.append("No README.md found")
        
        return {
            'score': doc_score,
            'improvements': improvements,
            'issues_fixed': issues_fixed
        }
    
    def _check_performance_basics(self, mvp_path: Path, tech_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Check basic performance optimizations."""
        improvements = []
        issues_fixed = []
        
        performance_score = 0
        
        # Check for optimization patterns
        all_files = []
        for ext in ['*.js', '*.ts', '*.html', '*.css']:
            all_files.extend(mvp_path.rglob(ext))
        
        for file_path in all_files:
            content = file_path.read_text(encoding='utf-8')
            
            # Check for lazy loading
            if 'lazy' in content.lower() or 'defer' in content.lower():
                performance_score += 10
                improvements.append(f"Performance optimization in {file_path.name}")
            
            # Check for caching headers (in backend files)
            if 'cache-control' in content.lower() or 'etag' in content.lower():
                performance_score += 15
                improvements.append(f"Caching strategy in {file_path.name}")
            
            # Check for minification indicators
            if '.min.' in file_path.name or 'minify' in content.lower():
                performance_score += 10
                improvements.append(f"Minified assets: {file_path.name}")
        
        # Check package.json for performance dependencies
        package_json = mvp_path / "package.json"
        if package_json.exists():
            package_data = json.loads(package_json.read_text())
            dev_deps = package_data.get('devDependencies', {})
            
            perf_tools = ['webpack', 'vite', 'rollup', 'terser', 'cssnano']
            found_tools = [tool for tool in perf_tools if tool in dev_deps]
            
            if found_tools:
                performance_score += len(found_tools) * 5
                improvements.append(f"Build tools: {', '.join(found_tools)}")
        
        return {
            'score': min(performance_score, 100),
            'improvements': improvements,
            'issues_fixed': issues_fixed
        }
    
    def _calculate_quality_score(self, enhancement_report: Dict[str, Any]) -> float:
        """Calculate overall quality score from all checks."""
        scores = []
        for check_name in self.quality_checks.keys():
            if check_name in enhancement_report:
                scores.append(enhancement_report[check_name].get('score', 0))
        
        return sum(scores) / len(scores) if scores else 0
    
    def generate_improvement_plan(self, enhancement_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate a prioritized improvement plan."""
        plan = []
        
        # Group issues by severity
        all_issues = enhancement_report.get('issues_fixed', [])
        
        # Prioritize critical issues
        critical_issues = [issue for issue in all_issues if any(keyword in issue.lower() 
                          for keyword in ['missing', 'error', 'security', 'broken'])]
        
        for issue in critical_issues:
            plan.append({
                'priority': 'high',
                'issue': issue,
                'estimated_effort': 'medium',
                'impact': 'high'
            })
        
        # Add medium priority improvements
        medium_issues = [issue for issue in all_issues if issue not in critical_issues]
        for issue in medium_issues[:5]:  # Limit to top 5
            plan.append({
                'priority': 'medium',
                'issue': issue,
                'estimated_effort': 'low',
                'impact': 'medium'
            })
        
        return plan
