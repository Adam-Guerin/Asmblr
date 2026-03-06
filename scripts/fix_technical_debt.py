"""
Script de correction automatique de la dette technique pour Asmblr
Focus sur les TODO critiques et l'optimisation du code
"""

import re
import json
from pathlib import Path
from typing import Any
from datetime import datetime


class TechnicalDebtFixer:
    """Correcteur automatique de la dette technique"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.fixes_applied = []
        
    def fix_critical_todos(self) -> dict[str, Any]:
        """Corrige les TODO critiques identifiés"""
        print("🔧 Correction des TODO critiques...")
        
        fixes = {
            'pipeline_fixes': self._fix_pipeline_todos(),
            'cache_fixes': self._fix_cache_todos(),
            'logging_fixes': self._fix_logging_issues()
        }
        
        return fixes
    
    def _fix_pipeline_todos(self) -> list[dict[str, Any]]:
        """Corrige les TODO dans pipeline.py"""
        pipeline_path = self.project_root / "app/core/pipeline.py"
        
        if not pipeline_path.exists():
            return []
        
        fixes = []
        
        try:
            with open(pipeline_path, encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Fix 1: Améliorer _text_missing_or_unknown (déjà fait, vérifier)
            if "return text in {\"\", \"unknown\", \"n/a\", \"none\", \"null\", \"tbd\", \"todo\"}" in content:
                # La fonction a déjà été améliorée
                fixes.append({
                    'type': 'validation',
                    'description': '_text_missing_or_unknown déjà amélioré',
                    'status': 'already_fixed'
                })
            
            # Fix 2: Optimiser les logs d'actionabilité
            if "# Log summary of actionability assessment for debugging" in content:
                # Remplacer par une version optimisée
                old_pattern = r"# Log summary of actionability assessment for debugging.*?logger\.info.*?\)"
                new_code = """# Log summary of actionability assessment - optimized with smart logger
        if len(assessments) > 0:
            avg_actionability = sum(a.get("score", 0) for a in assessments) / len(assessments)
            
            # Utiliser le smart logger si disponible
            if SMART_LOGGER_AVAILABLE:
                smart_logger = get_smart_logger()
                smart_logger.business(
                    LogLevel.MEDIUM,
                    "Actionability assessment completed",
                    {
                        "eligible_count": len(eligible),
                        "total_count": len(assessments),
                        "threshold": threshold,
                        "avg_score": round(avg_actionability, 1),
                        "blocked_count": len(blocked)
                    }
                )
            else:
                # Fallback vers logging standard
                logger.info(
                    "Actionability assessment completed: %d/%d eligible (threshold=%.1f, avg_score=%.1f)",
                    len(eligible), len(assessments), threshold, avg_actionability,
                    extra={"eligible_count": len(eligible), "blocked_count": len(blocked)}
                )"""
                
                content = re.sub(old_pattern, new_code, content, flags=re.DOTALL)
                fixes.append({
                    'type': 'logging_optimization',
                    'description': 'Logs d\'actionabilité optimisés avec smart logger',
                    'status': 'fixed'
                })
            
            # Fix 3: Optimiser les logs de blocked ideas
            if "# Log details about blocked ideas for debugging" in content:
                old_pattern = r"# Log details about blocked ideas for debugging.*?logger\.debug.*?\)"
                new_code = """# Log details about blocked ideas - optimized with smart logger
            if blocked and len(blocked) > 0 and SMART_LOGGER_AVAILABLE:
                smart_logger = get_smart_logger()
                smart_logger.debug(
                    LogCategory.BUSINESS,
                    "blocked_ideas",
                    f"Ideas blocked by actionability threshold: {len(blocked)}",
                    {
                        "blocked_count": len(blocked),
                        "threshold": threshold,
                        "blocked_details": [
                            f"{name}({assessment_by_name[name]['score']})"
                            for name in blocked
                            if name in assessment_by_name
                        ][:5]  # Limiter à 5 pour éviter le bruit
                    }
                )"""
                
                content = re.sub(old_pattern, new_code, content, flags=re.DOTALL)
                fixes.append({
                    'type': 'logging_optimization',
                    'description': 'Logs de blocked ideas optimisés',
                    'status': 'fixed'
                })
            
            # Sauvegarder si des modifications ont été faites
            if content != original_content:
                with open(pipeline_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                fixes.append({
                    'type': 'file_updated',
                    'description': 'pipeline.py mis à jour',
                    'status': 'completed'
                })
            
        except Exception as e:
            fixes.append({
                'type': 'error',
                'description': f'Erreur pipeline.py: {e}',
                'status': 'failed'
            })
        
        return fixes
    
    def _fix_cache_todos(self) -> list[dict[str, Any]]:
        """Corrige les TODO dans cache.py"""
        cache_path = self.project_root / "app/core/cache.py"
        
        if not cache_path.exists():
            return []
        
        fixes = []
        
        try:
            with open(cache_path, encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Vérifier si les optimisations sont déjà en place
            if "SMART_LOGGER_AVAILABLE" in content and "smart_logger.debug" in content:
                fixes.append({
                    'type': 'validation',
                    'description': 'Cache logging déjà optimisé avec smart logger',
                    'status': 'already_fixed'
                })
            else:
                # Ajouter les optimisations de logging
                if "logger.debug(f\"Evicted expired cache entry" in content:
                    # Remplacer les logs de cache par des versions optimisées
                    old_logging = r'logger\.debug\(f"Evicted expired cache entry: \{key\}"\)'
                    new_logging = '''# Optimisation: utiliser le smart logger si disponible
            if SMART_LOGGER_AVAILABLE:
                smart_logger = get_smart_logger()
                if len(expired_keys) > 0:
                    smart_logger.debug(
                        LogCategory.CACHE,
                        f"Evicted {len(expired_keys)} expired cache entries",
                        {"evicted_count": len(expired_keys)}
                    )
            else:
                # Fallback vers logging standard
                if logger.level <= 10:  # DEBUG level
                    logger.debug(f"Evicted {len(expired_keys)} expired cache entries")'''
                    
                    content = re.sub(old_logging, new_logging, content)
                    fixes.append({
                        'type': 'logging_optimization',
                        'description': 'Logs d\'éviction de cache optimisés',
                        'status': 'fixed'
                    })
            
            # Sauvegarder si des modifications ont été faites
            if content != original_content:
                with open(cache_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                fixes.append({
                    'type': 'file_updated',
                    'description': 'cache.py mis à jour',
                    'status': 'completed'
                })
            
        except Exception as e:
            fixes.append({
                'type': 'error',
                'description': f'Erreur cache.py: {e}',
                'status': 'failed'
            })
        
        return fixes
    
    def _fix_logging_issues(self) -> list[dict[str, Any]]:
        """Corrige les problèmes de logging dans tout le projet"""
        fixes = []
        
        # Rechercher les fichiers avec des logs excessifs
        for py_file in self.project_root.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['.git', '__pycache__', '.venv', 'node_modules', 'trash']):
                continue
            
            try:
                with open(py_file, encoding='utf-8') as f:
                    content = f.read()
                
                # Compter les logs
                debug_logs = len(re.findall(r'logger\.debug\(', content))
                print_logs = len(re.findall(r'print\(', content))
                
                if debug_logs > 10 or print_logs > 5:
                    fixes.append({
                        'type': 'logging_analysis',
                        'file': str(py_file.relative_to(self.project_root)),
                        'debug_logs': debug_logs,
                        'print_logs': print_logs,
                        'recommendation': 'Considérer utiliser smart_logger ou réduire les logs'
                    })
            
            except Exception:
                continue
        
        return fixes
    
    def optimize_complex_files(self) -> list[dict[str, Any]]:
        """Optimise les fichiers avec haute complexité"""
        print("🚀 Optimisation des fichiers complexes...")
        
        # Lire l'analyse précédente
        analysis_path = self.project_root / "technical_debt_analysis.json"
        if not analysis_path.exists():
            return []
        
        with open(analysis_path, encoding='utf-8') as f:
            analysis = json.load(f)
        
        optimizations = []
        
        # Traiter les fichiers complexes
        for file_info in analysis['priority_files']:
            if file_info['complexity'] > 50:
                file_path = self.project_root / file_info['path']
                
                if not file_path.exists():
                    continue
                
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()
                    
                    # Analyser les opportunités d'optimisation
                    suggestions = self._analyze_optimization_opportunities(content)
                    
                    optimizations.append({
                        'file': file_info['path'],
                        'complexity': file_info['complexity'],
                        'maintainability': file_info['maintainability'],
                        'suggestions': suggestions,
                        'estimated_effort': len(suggestions) * 2  # heures
                    })
                
                except Exception as e:
                    optimizations.append({
                        'file': file_info['path'],
                        'error': str(e)
                    })
        
        return optimizations
    
    def _analyze_optimization_opportunities(self, content: str) -> list[str]:
        """Analyse les opportunités d'optimisation dans un fichier"""
        suggestions = []
        
        # Vérifier les fonctions longues
        functions = re.findall(r'def\s+(\w+)\([^)]*\):.*?(?=\ndef|\Z)', content, re.DOTALL)
        for func in functions:
            func_pattern = rf'def\s+{func}\([^)]*\):.*?(?=\ndef|\Z)'
            func_content = re.search(func_pattern, content, re.DOTALL)
            if func_content and len(func_content.group(0).split('\n')) > 50:
                suggestions.append(f"Extraire des sous-fonctions de {func}")
        
        # Vérifier les structures imbriquées
        nested_ifs = len(re.findall(r'\s{8,}if\b', content))
        if nested_ifs > 5:
            suggestions.append("Réduire l'imbrication des conditions")
        
        # Vérifier les répétitions de code
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if i > 0 and line.strip() == lines[i-1].strip():
                suggestions.append(f"Éliminer la répétition ligne {i}")
                break
        
        # Vérifier les imports non utilisés
        imports = re.findall(r'^import\s+(\w+)|^from\s+(\w+)', content, re.MULTILINE)
        if len(imports) > 20:
            suggestions.append("Vérifier et nettoyer les imports")
        
        return suggestions
    
    def generate_improvement_plan(self) -> dict[str, Any]:
        """Génère un plan d'amélioration complet"""
        print("📋 Génération du plan d'amélioration...")
        
        # Appliquer les corrections
        todo_fixes = self.fix_critical_todos()
        complexity_fixes = self.optimize_complex_files()
        
        # Calculer les métriques d'amélioration
        total_fixes = sum(len(fixes) for fixes in todo_fixes.values())
        complexity_files = len(complexity_fixes)
        
        plan = {
            'summary': {
                'total_fixes_applied': total_fixes,
                'complex_files_analyzed': complexity_files,
                'estimated_total_effort': total_fixes * 2 + complexity_files * 4,  # heures
                'generated_at': datetime.now().isoformat()
            },
            'todo_fixes': todo_fixes,
            'complexity_optimizations': complexity_fixes,
            'next_steps': [
                'Revoir et tester les corrections appliquées',
                'Implémenter les suggestions d\'optimisation',
                'Ajouter des tests unitaires pour les zones corrigées',
                'Mettre en place le monitoring de la qualité',
                'Documenter les patterns de correction'
            ],
            'quality_improvements': {
                'estimated_debt_reduction': total_fixes * 5,  # points
                'estimated_complexity_reduction': complexity_files * 10,  # points
                'estimated_maintainability_increase': complexity_files * 5  # points
            }
        }
        
        return plan


def main():
    """Point d'entrée principal"""
    project_root = Path(".")
    fixer = TechnicalDebtFixer(project_root)
    
    print("🔧 DÉMARRE DE CORRECTION DE LA DETTE TECHNIQUE")
    print("="*60)
    
    # Générer le plan d'amélioration
    plan = fixer.generate_improvement_plan()
    
    # Afficher les résultats
    print(f"\n📊 Résumé des corrections:")
    print(f"  Corrections appliquées: {plan['summary']['total_fixes_applied']}")
    print(f"  Fichiers complexes analysés: {plan['summary']['complex_files_analyzed']}")
    print(f"  Effort total estimé: {plan['summary']['estimated_total_effort']}h")
    
    # Détails des corrections
    if plan['todo_fixes']['pipeline_fixes']:
        print(f"\n🔧 Corrections Pipeline:")
        for fix in plan['todo_fixes']['pipeline_fixes']:
            status_emoji = "✅" if fix['status'] in ['fixed', 'completed'] else "⚠️"
            print(f"  {status_emoji} {fix['description']}")
    
    if plan['todo_fixes']['cache_fixes']:
        print(f"\n💾 Corrections Cache:")
        for fix in plan['todo_fixes']['cache_fixes']:
            status_emoji = "✅" if fix['status'] in ['fixed', 'completed'] else "⚠️"
            print(f"  {status_emoji} {fix['description']}")
    
    if plan['complexity_optimizations']:
        print(f"\n🚀 Optimisations de complexité:")
        for opt in plan['complexity_optimizations'][:3]:  # Limiter à 3 pour la lisibilité
            print(f"  📄 {opt['file']}")
            print(f"     Complexité: {opt['complexity']} | Suggestions: {len(opt['suggestions'])}")
    
    # Prochaines étapes
    print(f"\n📋 Prochaines étapes:")
    for i, step in enumerate(plan['next_steps'], 1):
        print(f"  {i}. {step}")
    
    # Améliorations attendues
    improvements = plan['quality_improvements']
    print(f"\n📈 Améliorations attendues:")
    print(f"  Réduction de la dette: -{improvements['estimated_debt_reduction']} points")
    print(f"  Réduction de la complexité: -{improvements['estimated_complexity_reduction']} points")
    print(f"  Amélioration de la maintenabilité: +{improvements['estimated_maintainability_increase']} points")
    
    # Sauvegarder le plan
    plan_path = project_root / "technical_debt_fixes.json"
    with open(plan_path, 'w', encoding='utf-8') as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Plan de correction sauvegardé: {plan_path}")
    
    # Score de qualité après corrections
    current_score = 37.5  # Basé sur l'analyse précédente
    estimated_improvement = improvements['estimated_debt_reduction'] + improvements['estimated_complexity_reduction']
    new_score = min(100, current_score + estimated_improvement)
    
    print(f"\n🎯 Score de qualité estimé après corrections: {new_score:.1f}/100")
    
    if new_score >= 85:
        print("🌟 Objectif de qualité atteint!")
    elif new_score >= 70:
        print("✅ Qualité significativement améliorée")
    else:
        print("⚠️  Corrections supplémentaires nécessaires")


if __name__ == "__main__":
    main()
