#!/usr/bin/env python
"""
Script d'analyse de qualité pour Asmblr
"""

from app.core.code_quality import analyze_code_quality
from pathlib import Path

def main():
    print("🔍 Analyse de qualité du code Asmblr...")
    print("=" * 50)
    
    try:
        metrics = analyze_code_quality(Path('app'))
        
        print(f"📊 Score qualité actuel: {metrics.quality_score}/100")
        print(f"🔍 Problèmes détectés: {metrics.issues_found}")
        print(f"📝 TODO/FIXME/BUG: {len([i for i in metrics.issues_by_type.get('TODO/FIXME/BUG', [])])}")
        
        print(f"🐛 Exceptions: {len([i for i in metrics.issues_by_type.get('Exception', [])])}")
        print(f"📝 Print statements: {len([i for i in metrics.issues_by_type.get('Print statement', [])])}")
        print(f"🔧 Code smells: {len([i for i in metrics.issues_by_type.get('Code smell', [])])}")
        
        print("\n📋 Top 10 des problèmes:")
        all_issues = []
        for issue_type, issue_list in metrics.issues_by_type.items():
            if isinstance(issue_list, list):
                all_issues.extend(issue_list)
        
        # Trier par sévérité
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        sorted_issues = sorted(
            all_issues,
            key=lambda x: severity_order.get(x.severity, 0),
            reverse=True
        )
        
        for i, issue in enumerate(sorted_issues[:10], 1):
            print(f"{i}. {issue.file_path}:{issue.line_number} - {issue.description}")
        
        print(f"\n📈 Répartition par type:")
        for issue_type, count in metrics.issues_by_type.items():
            if isinstance(count, list):
                print(f"  {issue_type}: {len(count)}")
            else:
                print(f"  {issue_type}: {count}")
        
        print(f"\n📁 Répartition par fichier:")
        file_counts = {}
        for issue_type, issue_list in metrics.issues_by_type.items():
            if isinstance(issue_list, list):
                for issue in issue_list:
                    file_counts[issue.file_path] = file_counts.get(issue.file_path, 0) + 1
        
        for file_path, count in sorted(file_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {file_path}: {count}")
        
        # Recommandations
        print(f"\n💡 Recommandations:")
        if metrics.quality_score < 70:
            print("  ⚠️  Score qualité faible - Corrections critiques nécessaires")
        if len(metrics.issues_by_type.get('TODO/FIXME/BUG', [])) > 5:
            print("  📝 Plusieurs TODO - Créer des issues et résoudre")
        if len(metrics.issues_by_type.get('Exception', [])) > 10:
            print("  🐛 Exceptions mal gérées - Utiliser ErrorHandlerV2")
        if len(metrics.issues_by_type.get('Print statement', [])) > 3:
            print("  📝 Print statements - Remplacer par SmartLogger")
        
        return metrics
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        return None

if __name__ == "__main__":
    main()
