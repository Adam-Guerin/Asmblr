"""
Script d'analyse et de correction de la dette technique pour Asmblr
Focus sur les TODO critiques et l'optimisation du code
"""

import re
import json
from pathlib import Path
from typing import Any
from dataclasses import dataclass


@dataclass
class TechnicalDebtItem:
    """Représente un item de dette technique"""
    file_path: str
    line_number: int
    debt_type: str  # TODO, FIXME, BUG, HACK
    severity: str  # low, medium, high, critical
    description: str
    context: str
    suggested_fix: str = ""


@dataclass
class FileMetrics:
    """Métriques pour un fichier"""
    path: str
    lines: int
    complexity: float
    maintainability: float
    debt_items: list[TechnicalDebtItem]
    debt_score: float


class TechnicalDebtAnalyzer:
    """Analyseur de dette technique"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.debt_patterns = {
            'TODO': r'#\s*TODO\s*[:\-]?\s*(.+)',
            'FIXME': r'#\s*FIXME\s*[:\-]?\s*(.+)',
            'BUG': r'#\s*BUG\s*[:\-]?\s*(.+)',
            'HACK': r'#\s*HACK\s*[:\-]?\s*(.+)'
        }
        self.severity_keywords = {
            'critical': ['critical', 'urgent', 'security', 'blocker'],
            'high': ['important', 'priority', 'fix', 'broken'],
            'medium': ['improve', 'optimize', 'refactor'],
            'low': ['cleanup', 'minor', 'cosmetic']
        }
    
    def analyze_file(self, file_path: Path) -> FileMetrics:
        """Analyse un fichier pour détecter la dette technique"""
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            print(f"Erreur lecture {file_path}: {e}")
            return FileMetrics(str(file_path), 0, 0, 0, [], 0)
        
        debt_items = []
        
        # Analyser chaque ligne
        for line_num, line in enumerate(lines, 1):
            for debt_type, pattern in self.debt_patterns.items():
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    description = match.group(1).strip()
                    severity = self._determine_severity(description, line)
                    
                    debt_item = TechnicalDebtItem(
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=line_num,
                        debt_type=debt_type,
                        severity=severity,
                        description=description,
                        context=line.strip()
                    )
                    debt_items.append(debt_item)
        
        # Calculer les métriques
        debt_score = self._calculate_debt_score(debt_items)
        complexity = self._estimate_complexity(content)
        maintainability = self._estimate_maintainability(content, len(debt_items))
        
        return FileMetrics(
            path=str(file_path.relative_to(self.project_root)),
            lines=len(lines),
            complexity=complexity,
            maintainability=maintainability,
            debt_items=debt_items,
            debt_score=debt_score
        )
    
    def _determine_severity(self, description: str, context: str) -> str:
        """Détermine la sévérité basée sur la description et le contexte"""
        text = (description + " " + context).lower()
        
        for severity, keywords in self.severity_keywords.items():
            if any(keyword in text for keyword in keywords):
                return severity
        
        # Par défaut, les TODO sont medium
        return 'medium'
    
    def _calculate_debt_score(self, debt_items: list[TechnicalDebtItem]) -> float:
        """Calcule un score de dette (0-100, plus élevé = plus de dette)"""
        severity_weights = {
            'critical': 10,
            'high': 5,
            'medium': 2,
            'low': 1
        }
        
        score = sum(severity_weights.get(item.severity, 1) for item in debt_items)
        return min(score, 100)
    
    def _estimate_complexity(self, content: str) -> float:
        """Estime la complexité cyclomatique"""
        # Simplification: compter les structures de contrôle
        control_structures = [
            r'\bif\b', r'\belif\b', r'\belse\b', r'\bfor\b', 
            r'\bwhile\b', r'\btry\b', r'\bexcept\b', r'\bfinally\b',
            r'\bwith\b', r'\band\b', r'\bor\b', r'\blambda\b'
        ]
        
        complexity = 1  # Base complexity
        for pattern in control_structures:
            complexity += len(re.findall(pattern, content))
        
        return float(complexity)
    
    def _estimate_maintainability(self, content: str, debt_count: int) -> float:
        """Estime la maintenabilité (0-100, plus élevé = plus maintenable)"""
        lines = len(content.split('\n'))
        
        # Facteurs négatifs
        complexity_penalty = min(self._estimate_complexity(content) / 10, 30)
        debt_penalty = min(debt_count * 2, 20)
        length_penalty = min(lines / 100, 10)
        
        # Score de base
        base_score = 100
        
        maintainability = base_score - complexity_penalty - debt_penalty - length_penalty
        return max(maintainability, 0)
    
    def analyze_project(self) -> dict[str, Any]:
        """Analyse tout le projet"""
        print("🔍 Analyse de la dette technique d'Asmblr...")
        
        python_files = list(self.project_root.rglob("*.py"))
        file_metrics = []
        
        for file_path in python_files:
            # Ignorer certains répertoires
            if any(skip in str(file_path) for skip in ['.git', '__pycache__', '.venv', 'node_modules']):
                continue
            
            metrics = self.analyze_file(file_path)
            file_metrics.append(metrics)
        
        # Agréger les résultats
        total_debt_items = sum(len(m.debt_items) for m in file_metrics)
        avg_complexity = sum(m.complexity for m in file_metrics) / len(file_metrics)
        avg_maintainability = sum(m.maintainability for m in file_metrics) / len(file_metrics)
        
        # Trier par dette score
        priority_files = sorted(file_metrics, key=lambda m: m.debt_score, reverse=True)[:10]
        
        # Grouper par type
        debt_by_type = {}
        debt_by_severity = {}
        
        for metrics in file_metrics:
            for item in metrics.debt_items:
                debt_by_type[item.debt_type] = debt_by_type.get(item.debt_type, 0) + 1
                debt_by_severity[item.severity] = debt_by_severity.get(item.severity, 0) + 1
        
        return {
            'summary': {
                'total_files': len(file_metrics),
                'total_debt_items': total_debt_items,
                'avg_complexity': avg_complexity,
                'avg_maintainability': avg_maintainability,
                'files_with_debt': len([m for m in file_metrics if m.debt_items])
            },
            'debt_by_type': debt_by_type,
            'debt_by_severity': debt_by_severity,
            'priority_files': [
                {
                    'path': m.path,
                    'debt_score': m.debt_score,
                    'debt_count': len(m.debt_items),
                    'complexity': m.complexity,
                    'maintainability': m.maintainability
                }
                for m in priority_files
            ],
            'critical_items': [
                {
                    'file': item.file_path,
                    'line': item.line_number,
                    'type': item.debt_type,
                    'description': item.description,
                    'context': item.context
                }
                for m in file_metrics
                for item in m.debt_items
                if item.severity == 'critical'
            ]
        }
    
    def generate_fixes(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Génère des suggestions de correction"""
        fixes = []
        
        # Corrections pour les TODO critiques
        critical_items = analysis['critical_items']
        if critical_items:
            fixes.append({
                'priority': 'high',
                'category': 'critical_todos',
                'description': f'Corriger {len(critical_items)} TODO critiques',
                'files': [item['file'] for item in critical_items],
                'estimated_effort': len(critical_items) * 2,  # heures
                'actions': [
                    'Analyser chaque TODO critique',
                    'Implémenter les corrections nécessaires',
                    'Ajouter des tests unitaires',
                    'Documenter les changements'
                ]
            })
        
        # Optimisation des fichiers complexes
        complex_files = [f for f in analysis['priority_files'] if f['complexity'] > 50]
        if complex_files:
            fixes.append({
                'priority': 'medium',
                'category': 'complexity_reduction',
                'description': f'Réduire la complexité de {len(complex_files)} fichiers',
                'files': [f['path'] for f in complex_files],
                'estimated_effort': len(complex_files) * 4,  # heures
                'actions': [
                    'Extraire des fonctions plus petites',
                    'Réduire les structures de contrôle imbriquées',
                    'Appliquer les design patterns appropriés',
                    'Ajouter de la documentation'
                ]
            })
        
        # Amélioration de la maintenabilité
        low_maintainability = [f for f in analysis['priority_files'] if f['maintainability'] < 50]
        if low_maintainability:
            fixes.append({
                'priority': 'medium',
                'category': 'maintainability_improvement',
                'description': f'Améliorer la maintenabilité de {len(low_maintainability)} fichiers',
                'files': [f['path'] for f in low_maintainability],
                'estimated_effort': len(low_maintainability) * 3,  # heures
                'actions': [
                    'Réorganiser le code',
                    'Ajouter des commentaires',
                    'Standardiser le formatage',
                    'Créer des tests'
                ]
            })
        
        return fixes


def main():
    """Point d'entrée principal"""
    project_root = Path(".")
    analyzer = TechnicalDebtAnalyzer(project_root)
    
    # Analyse
    analysis = analyzer.analyze_project()
    
    # Affichage des résultats
    print("\n" + "="*60)
    print("📊 RAPPORT DE DETTE TECHNIQUE")
    print("="*60)
    
    summary = analysis['summary']
    print(f"\n📈 Résumé:")
    print(f"  Fichiers analysés: {summary['total_files']}")
    print(f"  Items de dette: {summary['total_debt_items']}")
    print(f"  Complexité moyenne: {summary['avg_complexity']:.1f}")
    print(f"  Maintenabilité moyenne: {summary['avg_maintainability']:.1f}")
    print(f"  Fichiers avec dette: {summary['files_with_debt']}")
    
    print(f"\n📝 Dette par type:")
    for debt_type, count in analysis['debt_by_type'].items():
        print(f"  {debt_type}: {count}")
    
    print(f"\n🚨 Dette par sévérité:")
    for severity, count in analysis['debt_by_severity'].items():
        print(f"  {severity}: {count}")
    
    print(f"\n🔥 Fichiers prioritaires:")
    for i, file_info in enumerate(analysis['priority_files'][:5], 1):
        print(f"  {i}. {file_info['path']}")
        print(f"     Score: {file_info['debt_score']:.1f} | "
              f"Complexité: {file_info['complexity']:.1f} | "
              f"Maintenabilité: {file_info['maintainability']:.1f}")
    
    if analysis['critical_items']:
        print(f"\n⚠️  Items critiques:")
        for item in analysis['critical_items'][:5]:
            print(f"  {item['file']}:{item['line']} - {item['description']}")
    
    # Générer les corrections
    fixes = analyzer.generate_fixes(analysis)
    
    if fixes:
        print(f"\n🔧 Plan de correction:")
        for i, fix in enumerate(fixes, 1):
            print(f"  {i}. [{fix['priority'].upper()}] {fix['description']}")
            print(f"     Effort estimé: {fix['estimated_effort']}h")
            print(f"     Fichiers concernés: {len(fix['files'])}")
    
    # Sauvegarder le rapport
    report_path = project_root / "technical_debt_analysis.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Rapport détaillé sauvegardé: {report_path}")
    
    # Score de qualité global
    quality_score = max(0, 100 - summary['total_debt_items'] * 2 - summary['avg_complexity'])
    print(f"\n🎯 Score de qualité global: {quality_score:.1f}/100")
    
    if quality_score < 70:
        print("⚠️  Action requise - Qualité insuffisante")
    elif quality_score < 85:
        print("✅ Qualité acceptable - Améliorations possibles")
    else:
        print("🌟 Excellente qualité - Maintenir le niveau")


if __name__ == "__main__":
    main()
