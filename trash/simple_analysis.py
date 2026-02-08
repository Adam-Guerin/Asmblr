#!/usr/bin/env python
"""
Analyse simple de qualité pour Asmblr
"""

import os
import re
from pathlib import Path

def count_issues_in_file(file_path):
    """Compte les problèmes dans un fichier"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        issues = {
            'todos': 0,
            'exceptions': 0,
            'prints': 0,
            'code_smells': 0
        }
        
        for line_num, line in enumerate(lines, 1):
            # TODO/FIXME/BUG
            if re.search(r'#\s*(TODO|FIXME|BUG|HACK|XXX)', line, re.IGNORECASE):
                issues['todos'] += 1
            
            # Exceptions mal gérées
            if re.search(r'except\s*:\s*$', line):
                issues['exceptions'] += 1
            if re.search(r'except\s*Exception\s*:\s*pass\s*$', line):
                issues['exceptions'] += 1
            
            # Print statements
            if re.search(r'print\s*\(', line):
                issues['prints'] += 1
            
            # Code smells
            if re.search(r'if\s+True\s*:', line):
                issues['code_smells'] += 1
            if re.search(r'if\s+False\s*:', line):
                issues['code_smells'] += 1
        
        return issues, len(lines)
        
    except Exception as e:
        print(f"Erreur lecture {file_path}: {e}")
        return {'todos': 0, 'exceptions': 0, 'prints': 0, 'code_smells': 0}, 0

def main():
    print("🔍 Analyse simple de qualité d'Asmblr...")
    print("=" * 50)
    
    app_dir = Path('app')
    if not app_dir.exists():
        print("❌ Répertoire 'app' non trouvé")
        return
    
    total_issues = {
        'todos': 0,
        'exceptions': 0,
        'prints': 0,
        'code_smells': 0
    }
    total_lines = 0
    file_count = 0
    problem_files = {}
    
    # Analyser tous les fichiers Python
    for py_file in app_dir.rglob('*.py'):
        file_issues, lines = count_issues_in_file(py_file)
        
        for issue_type, count in file_issues.items():
            total_issues[issue_type] += count
        
        total_lines += lines
        file_count += 1
        
        # Compter les problèmes par fichier
        total_file_issues = sum(file_issues.values())
        if total_file_issues > 0:
            problem_files[str(py_file)] = total_file_issues
    
    # Calculer le score de qualité
    severity_weights = {
        'todos': 3,
        'exceptions': 2,
        'prints': 1,
        'code_smells': 1
    }
    
    weighted_issues = sum(
        total_issues[issue_type] * weight
        for issue_type, weight in severity_weights.items()
    )
    
    quality_score = max(0, 100 - (weighted_issues * 100 / max(total_lines, 1)))
    
    # Afficher les résultats
    print(f"📊 Score qualité: {quality_score:.1f}/100")
    print(f"📁 Fichiers analysés: {file_count}")
    print(f"📝 Lignes de code: {total_lines}")
    print()
    
    print("🔍 Problèmes détectés:")
    print(f"  📝 TODO/FIXME/BUG: {total_issues['todos']}")
    print(f"  🐛 Exceptions mal gérées: {total_issues['exceptions']}")
    print(f"  🖨️ Print statements: {total_issues['prints']}")
    print(f"  🔧 Code smells: {total_issues['code_smells']}")
    print(f"  📊 Total: {sum(total_issues.values())}")
    print()
    
    # Top 10 des fichiers avec le plus de problèmes
    print("📋 Top 10 des fichiers problématiques:")
    sorted_files = sorted(problem_files.items(), key=lambda x: x[1], reverse=True)
    for i, (file_path, count) in enumerate(sorted_files[:10], 1):
        print(f"  {i}. {file_path}: {count} problèmes")
    print()
    
    # Recommandations
    print("💡 Recommandations:")
    if quality_score < 80:
        print("  ⚠️  Score qualité faible - Corrections nécessaires")
    if total_issues['todos'] > 5:
        print("  📝 Plusieurs TODO - Créer des issues GitHub")
    if total_issues['exceptions'] > 10:
        print("  🐛 Exceptions mal gérées - Utiliser ErrorHandlerV2")
    if total_issues['prints'] > 5:
        print("  🖨️ Print statements - Remplacer par SmartLogger")
    if total_issues['code_smells'] > 10:
        print("  🔧 Code smells - Refactoring nécessaire")
    
    print()
    print("🚀 Actions immédiates recommandées:")
    print("  1. Appliquer les corrections automatiques:")
    print("     python -c \"from app.core.code_quality import auto_fix_quality_issues; auto_fix_quality_issues()\"")
    print("  2. Déployer les micro-services:")
    print("     docker-compose -f docker-compose.microservices.yml up -d")
    print("  3. Activer le monitoring:")
    print("     http://localhost:9090  # Prometheus")
    print("     http://localhost:3001  # Grafana")

if __name__ == "__main__":
    main()
