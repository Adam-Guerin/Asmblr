"""
Outils de qualité de code pour Asmblr
Détecte et corrige automatiquement les problèmes de qualité
"""

import ast
import re
import json
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from pathlib import Path
from loguru import logger


@dataclass
class QualityIssue:
    """Problème de qualité détecté"""
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # low, medium, high, critical
    description: str
    suggestion: str
    code_snippet: str


@dataclass
class QualityMetrics:
    """Métriques de qualité du code"""
    total_files: int
    total_lines: int
    issues_found: int
    issues_by_type: Dict[str, int]
    issues_by_severity: Dict[str, int]
    quality_score: float  # 0-100


class CodeQualityAnalyzer:
    """
    Analyseur de qualité de code pour Asmblr
    Détecte les problèmes courants et suggère des corrections
    """
    
    def __init__(self):
        self.issues: List[QualityIssue] = []
        self.metrics = QualityMetrics(0, 0, 0, {}, {}, 0.0)
        
        # Patterns de détection
        self.todo_patterns = [
            r'#\s*TODO\s*:?\s*(.+)',
            r'#\s*FIXME\s*:?\s*(.+)',
            r'#\s*BUG\s*:?\s*(.+)',
            r'#\s*HACK\s*:?\s*(.+)',
            r'#\s*XXX\s*:?\s*(.+)'
        ]
        
        self.exception_patterns = [
            r'except\s*:\s*$',  # except: nu
            r'except\s*Exception\s*:\s*pass\s*$',  # except Exception: pass
            r'raise\s*Exception\s*\(\s*["\'](.+?)["\']\s*\)',  # raise Exception("message")
        ]
        
        self.logging_patterns = [
            r'logger\.(debug|info|warning|error|critical)\s*\(\s*["\'](.+?)["\']\s*\)',
            r'print\s*\(\s*["\'](.+?)["\']\s*\)',
        ]
        
        self.code_smells = [
            (r'len\(\s*\)\s*==\s*0', "Utilisez 'if not obj:' au lieu de 'if len(obj) == 0'"),
            (r'len\(\s*\)\s*>\s*0', "Utilisez 'if obj:' au lieu de 'if len(obj) > 0'"),
            (r'if\s+True\s*:', "Condition '# if True:' inutile"),
            (r'if\s+False\s*:', "Condition '# if False:' inutile"),
            (r'for\s+i\s+in\s+range\s*\(\s*len\s*\(', "Utilisez 'for item in iterable:' au lieu de 'for i in range(len())'"),
        ]
    
    def analyze_directory(self, directory: Path, 
                       file_pattern: str = "*.py") -> QualityMetrics:
        """
        Analyse tous les fichiers Python dans un répertoire
        
        Args:
            directory: Répertoire à analyser
            file_pattern: Pattern des fichiers à analyser
            
        Returns:
            Métriques de qualité
        """
        self.issues.clear()
        
        python_files = list(directory.rglob(file_pattern))
        total_lines = 0
        
        for file_path in python_files:
            try:
                file_issues, file_lines = self.analyze_file(file_path)
                self.issues.extend(file_issues)
                total_lines += file_lines
            except Exception as e:
                logger.warning(f"Erreur analyse fichier {file_path}: {e}")
        
        # Calculer les métriques
        self.metrics = self._calculate_metrics(python_files, total_lines)
        
        return self.metrics
    
    def analyze_file(self, file_path: Path) -> Tuple[List[QualityIssue], int]:
        """
        Analyse un fichier Python spécifique
        
        Args:
            file_path: Chemin du fichier à analyser
            
        Returns:
            Tuple (issues, line_count)
        """
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Analyser chaque type de problème
            issues.extend(self._find_todos(file_path, lines))
            issues.extend(self._find_exception_issues(file_path, lines))
            issues.extend(self._find_logging_issues(file_path, lines))
            issues.extend(self._find_code_smells(file_path, lines))
            issues.extend(self._find_complexity_issues(file_path, content))
            issues.extend(self._find_security_issues(file_path, lines))
            
            return issues, len(lines)
            
        except Exception as e:
            logger.error(f"Erreur lecture fichier {file_path}: {e}")
            return [], 0
    
    def _find_todos(self, file_path: Path, lines: List[str]) -> List[QualityIssue]:
        """Détecte les TODO/FIXME/BUG/HACK"""
        issues = []
        
        for line_num, line in enumerate(lines, 1):
            for pattern in self.todo_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    issues.append(QualityIssue(
                        file_path=str(file_path),
                        line_number=line_num,
                        issue_type="TODO/FIXME/BUG",
                        severity="medium",
                        description=f"Commentaire de suivi trouvé: {match.group(1)}",
                        suggestion="Créer une issue dans le suivi de projet et résoudre",
                        code_snippet=line.strip()
                    ))
        
        return issues
    
    def _find_exception_issues(self, file_path: Path, lines: List[str]) -> List[QualityIssue]:
        """Détecte les problèmes de gestion d'exceptions"""
        issues = []
        
        for line_num, line in enumerate(lines, 1):
            # except: nu
            if re.search(r'except\s*:\s*$', line):
                issues.append(QualityIssue(
                    file_path=str(file_path),
                    line_number=line_num,
                    issue_type="Exception trop large",
                    severity="high",
                    description="Exception catchée sans spécifier le type",
                    suggestion="Spécifiez le type d'exception: except ValueError:",
                    code_snippet=line.strip()
                ))
            
            # except Exception: pass
            elif re.search(r'except\s*Exception\s*:\s*pass\s*$', line):
                issues.append(QualityIssue(
                    file_path=str(file_path),
                    line_number=line_num,
                    issue_type="Exception ignorée",
                    severity="high",
                    description="Exception catchée mais ignorée avec pass",
                    suggestion="Ajoutez un traitement approprié ou loggez l'erreur",
                    code_snippet=line.strip()
                ))
            
            # raise Exception("message")
            elif re.search(r'raise\s*Exception\s*\(', line):
                issues.append(QualityIssue(
                    file_path=str(file_path),
                    line_number=line_num,
                    issue_type="Exception générique",
                    severity="medium",
                    description="Utilisation de Exception générique",
                    suggestion="Créez une exception spécifique ou utilisez une exception standard",
                    code_snippet=line.strip()
                ))
        
        return issues
    
    def _find_logging_issues(self, file_path: Path, lines: List[str]) -> List[QualityIssue]:
        """Détecte les problèmes de logging"""
        issues = []
        
        for line_num, line in enumerate(lines, 1):
            # print() statements
            if re.search(r'print\s*\(', line):
                issues.append(QualityIssue(
                    file_path=str(file_path),
                    line_number=line_num,
                    issue_type="Print statement",
                    severity="medium",
                    description="Utilisation de print() pour le logging",
                    suggestion="Utilisez le logger approprié: logger.info()",
                    code_snippet=line.strip()
                ))
            
            # Logging sans contexte
            elif re.search(r'logger\.(debug|info|warning|error|critical)\s*\(\s*["\'][^"\']*["\']\s*\)', line):
                issues.append(QualityIssue(
                    file_path=str(file_path),
                    line_number=line_num,
                    issue_type="Logging sans contexte",
                    severity="low",
                    description="Message de log sans variables ou contexte",
                    suggestion="Ajoutez du contexte: logger.info('Processing {item}', item=item)",
                    code_snippet=line.strip()
                ))
        
        return issues
    
    def _find_code_smells(self, file_path: Path, lines: List[str]) -> List[QualityIssue]:
        """Détecte les code smells courants"""
        issues = []
        
        for line_num, line in enumerate(lines, 1):
            for pattern, suggestion in self.code_smells:
                if re.search(pattern, line):
                    issues.append(QualityIssue(
                        file_path=str(file_path),
                        line_number=line_num,
                        issue_type="Code smell",
                        severity="low",
                        description=f"Pattern de code détecté: {pattern}",
                        suggestion=suggestion,
                        code_snippet=line.strip()
                    ))
        
        return issues
    
    def _find_complexity_issues(self, file_path: Path, content: str) -> List[QualityIssue]:
        """Détecte les problèmes de complexité"""
        issues = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Fonctions trop longues
                if isinstance(node, ast.FunctionDef):
                    if hasattr(node, 'end_lineno') and node.end_lineno:
                        func_lines = node.end_lineno - node.lineno
                        if func_lines > 50:
                            issues.append(QualityIssue(
                                file_path=str(file_path),
                                line_number=node.lineno,
                                issue_type="Fonction trop longue",
                                severity="medium",
                                description=f"Fonction '{node.name}' trop longue ({func_lines} lignes)",
                                suggestion="Divisez la fonction en plus petites fonctions",
                                code_snippet=f"def {node.name}(...)"
                            ))
                
                # Classes trop grandes
                elif isinstance(node, ast.ClassDef):
                    if hasattr(node, 'end_lineno') and node.end_lineno:
                        class_lines = node.end_lineno - node.lineno
                        if class_lines > 200:
                            issues.append(QualityIssue(
                                file_path=str(file_path),
                                line_number=node.lineno,
                                issue_type="Classe trop grande",
                                severity="medium",
                                description=f"Classe '{node.name}' trop grande ({class_lines} lignes)",
                                suggestion="Divisez la classe en plus petites classes",
                                code_snippet=f"class {node.name}:"
                            ))
        
        except SyntaxError as e:
            issues.append(QualityIssue(
                file_path=str(file_path),
                line_number=e.lineno or 0,
                issue_type="Erreur de syntaxe",
                severity="critical",
                description=f"Erreur de syntaxe: {e.msg}",
                suggestion="Corrigez l'erreur de syntaxe",
                code_snippet=""
            ))
        
        return issues
    
    def _find_security_issues(self, file_path: Path, lines: List[str]) -> List[QualityIssue]:
        """Détecte les problèmes de sécurité"""
        issues = []
        
        security_patterns = [
            (r'eval\s*\(', "Utilisation de eval() - risque de sécurité"),
            (r'exec\s*\(', "Utilisation de exec() - risque de sécurité"),
            (r'shell=True', "shell=True dans subprocess - risque d'injection"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Mot de passe en dur dans le code"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Clé API en dur dans le code"),
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description in security_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(QualityIssue(
                        file_path=str(file_path),
                        line_number=line_num,
                        issue_type="Sécurité",
                        severity="critical",
                        description=description,
                        suggestion="Utilisez des variables d'environnement ou un gestionnaire de secrets",
                        code_snippet=line.strip()
                    ))
        
        return issues
    
    def _calculate_metrics(self, files: List[Path], total_lines: int) -> QualityMetrics:
        """Calcule les métriques de qualité"""
        issues_by_type = {}
        issues_by_severity = {}
        
        for issue in self.issues:
            issues_by_type[issue.issue_type] = issues_by_type.get(issue.issue_type, 0) + 1
            issues_by_severity[issue.severity] = issues_by_severity.get(issue.severity, 0) + 1
        
        # Calculer le score de qualité (0-100)
        severity_weights = {"critical": 10, "high": 5, "medium": 2, "low": 1}
        weighted_issues = sum(
            issues_by_severity.get(severity, 0) * weight
            for severity, weight in severity_weights.items()
        )
        
        # Score basé sur le ratio lignes/issues pondérés
        if total_lines > 0:
            quality_score = max(0, 100 - (weighted_issues * 100 / total_lines))
        else:
            quality_score = 100
        
        return QualityMetrics(
            total_files=len(files),
            total_lines=total_lines,
            issues_found=len(self.issues),
            issues_by_type=issues_by_type,
            issues_by_severity=issues_by_severity,
            quality_score=quality_score
        )
    
    def get_issues_by_file(self, file_path: str) -> List[QualityIssue]:
        """Récupère tous les problèmes pour un fichier spécifique"""
        return [issue for issue in self.issues if issue.file_path == file_path]
    
    def get_issues_by_severity(self, severity: str) -> List[QualityIssue]:
        """Récupère tous les problèmes par sévérité"""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_top_issues(self, limit: int = 10) -> List[QualityIssue]:
        """Retourne les problèmes les plus critiques"""
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        
        return sorted(
            self.issues,
            key=lambda x: severity_order.get(x.severity, 0),
            reverse=True
        )[:limit]
    
    def export_report(self, format_type: str = "json") -> str:
        """Exporte le rapport de qualité"""
        report_data = {
            "metrics": asdict(self.metrics),
            "issues": [asdict(issue) for issue in self.issues],
            "top_issues": [asdict(issue) for issue in self.get_top_issues()],
            "summary": self._generate_summary()
        }
        
        if format_type == "json":
            return json.dumps(report_data, indent=2)
        
        elif format_type == "markdown":
            return self._generate_markdown_report(report_data)
        
        else:
            raise ValueError(f"Format non supporté: {format_type}")
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Génère un résumé des problèmes"""
        if not self.issues:
            return {"status": "excellent", "message": "Aucun problème de qualité détecté"}
        
        critical_count = len([i for i in self.issues if i.severity == "critical"])
        high_count = len([i for i in self.issues if i.severity == "high"])
        
        if critical_count > 0:
            return {"status": "critical", "message": f"{critical_count} problèmes critiques détectés"}
        elif high_count > 5:
            return {"status": "poor", "message": f"{high_count} problèmes de haute sévérité détectés"}
        elif high_count > 0:
            return {"status": "fair", "message": f"{high_count} problèmes à corriger"}
        else:
            return {"status": "good", "message": "Qualité acceptable"}
    
    def _generate_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """Génère un rapport au format Markdown"""
        metrics = report_data["metrics"]
        issues = report_data["issues"]
        
        md = f"""# Rapport de Qualité de Code Asmblr

## 📊 Métriques Générales

- **Fichiers analysés**: {metrics['total_files']}
- **Lignes de code**: {metrics['total_lines']}
- **Problèmes détectés**: {metrics['issues_found']}
- **Score de qualité**: {metrics['quality_score']:.1f}/100

## 🚨 Problèmes par Sévérité

"""
        
        for severity, count in metrics['issues_by_severity'].items():
            emoji = {"critical": "🚨", "high": "⚠️", "medium": "⚡", "low": "💡"}.get(severity, "📝")
            md += f"- {emoji} **{severity.title()}**: {count}\n"
        
        md += "\n## 📋 Problèmes par Type\n\n"
        
        for issue_type, count in metrics['issues_by_type'].items():
            md += f"- **{issue_type}**: {count}\n"
        
        md += "\n## 🔍 Top 10 des Problèmes\n\n"
        
        for i, issue in enumerate(report_data["top_issues"][:10], 1):
            severity_emoji = {"critical": "🚨", "high": "⚠️", "medium": "⚡", "low": "💡"}.get(issue["severity"], "📝")
            md += f"""{i}. {severity_emoji} **{issue['issue_type']}** - {issue['description']}
   - **Fichier**: {issue['file_path']}:{issue['line_number']}
   - **Suggestion**: {issue['suggestion']}
   - **Code**: `{issue['code_snippet']}`

"""
        
        return md


class CodeQualityFixer:
    """
    Correcteur automatique pour les problèmes de qualité courants
    """
    
    def __init__(self):
        self.fixes_applied = 0
    
    def auto_fix_issues(self, issues: List[QualityIssue], dry_run: bool = True) -> List[str]:
        """
        Applique automatiquement des corrections simples
        
        Args:
            issues: Liste des problèmes à corriger
            dry_run: Si True, ne modifie pas les fichiers (mode test)
            
        Returns:
            Liste des corrections appliquées
        """
        corrections = []
        
        for issue in issues:
            if issue.issue_type == "Print statement":
                correction = self._fix_print_statement(issue, dry_run)
                if correction:
                    corrections.append(correction)
            
            elif issue.issue_type == "Exception trop large":
                correction = self._fix_broad_exception(issue, dry_run)
                if correction:
                    corrections.append(correction)
            
            elif issue.issue_type == "Code smell":
                correction = self._fix_code_smell(issue, dry_run)
                if correction:
                    corrections.append(correction)
        
        self.fixes_applied = len(corrections)
        return corrections
    
    def _fix_print_statement(self, issue: QualityIssue, dry_run: bool) -> Optional[str]:
        """Corrige les print statements"""
        try:
            file_path = Path(issue.file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            line_idx = issue.line_number - 1
            original_line = lines[line_idx]
            
            # Remplacer print() par logger.info()
            fixed_line = re.sub(
                r'print\s*\(([^)]+)\)',
                r'logger.info(\1)',
                original_line
            )
            
            if not dry_run:
                lines[line_idx] = fixed_line
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
            
            return f"Print statement corrigé dans {file_path}:{issue.line_number}"
            
        except Exception as e:
            logger.error(f"Erreur correction print statement: {e}")
            return None
    
    def _fix_broad_exception(self, issue: QualityIssue, dry_run: bool) -> Optional[str]:
        """Corrige les exceptions trop larges"""
        try:
            file_path = Path(issue.file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            line_idx = issue.line_number - 1
            original_line = lines[line_idx]
            
            # Remplacer except: par except Exception:
            fixed_line = re.sub(
                r'except\s*:\s*$',
                'except Exception as e:',
                original_line
            )
            
            if not dry_run:
                lines[line_idx] = fixed_line
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
            
            return f"Exception large corrigée dans {file_path}:{issue.line_number}"
            
        except Exception as e:
            logger.error(f"Erreur correction exception large: {e}")
            return None
    
    def _fix_code_smell(self, issue: QualityIssue, dry_run: bool) -> Optional[str]:
        """Corrige les code smells simples"""
        try:
            file_path = Path(issue.file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            line_idx = issue.line_number - 1
            original_line = lines[line_idx]
            
            # Corrections spécifiques
            fixes = {
                r'len\(\s*\)\s*==\s*0': 'not obj',
                r'len\(\s*\)\s*>\s*0': 'obj',
                r'if\s+True\s*:': '# # if True:',
                r'if\s+False\s*:': '# # if False:',
            }
            
            fixed_line = original_line
            for pattern, replacement in fixes.items():
                fixed_line = re.sub(pattern, replacement, fixed_line)
            
            if fixed_line != original_line:
                if not dry_run:
                    lines[line_idx] = fixed_line
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                
                return f"Code smell corrigé dans {file_path}:{issue.line_number}"
            
        except Exception as e:
            logger.error(f"Erreur correction code smell: {e}")
            return None


# Instance globale de l'analyseur
_quality_analyzer: Optional[CodeQualityAnalyzer] = None


def get_quality_analyzer() -> CodeQualityAnalyzer:
    """Récupère l'instance globale de l'analyseur de qualité"""
    global _quality_analyzer
    if _quality_analyzer is None:
        _quality_analyzer = CodeQualityAnalyzer()
    return _quality_analyzer


def analyze_code_quality(directory: Path = Path("app")) -> QualityMetrics:
    """
    Analyse la qualité du code dans un répertoire
    
    Args:
        directory: Répertoire à analyser
        
    Returns:
        Métriques de qualité
    """
    analyzer = get_quality_analyzer()
    return analyzer.analyze_directory(directory)


def auto_fix_quality_issues(dry_run: bool = True) -> List[str]:
    """
    Corrige automatiquement les problèmes de qualité
    
    Args:
        dry_run: Si True, ne modifie pas les fichiers
        
    Returns:
        Liste des corrections appliquées
    """
    analyzer = get_quality_analyzer()
    fixer = CodeQualityFixer()
    
    # Analyser d'abord
    analyzer.analyze_directory(Path("app"))
    
    # Appliquer les corrections
    return fixer.auto_fix_issues(analyzer.issues, dry_run)
