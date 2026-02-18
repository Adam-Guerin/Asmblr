"""Tests pour le système de qualité de code"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock

from app.core.code_quality import (
    CodeQualityAnalyzer, CodeQualityFixer, QualityIssue,
    analyze_code_quality, auto_fix_quality_issues
)


class TestCodeQualityAnalyzer:
    """Tests pour l'analyseur de qualité de code"""
    
    def test_analyze_file_with_todos(self):
        """Test détection des TODO/FIXME/BUG"""
        analyzer = CodeQualityAnalyzer()
        
        # Créer un fichier temporaire avec des TODOs
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
# TODO: Implémenter cette fonction
def incomplete_function():
    # FIXME: Corriger la logique ici
    pass

# BUG: Cette fonction a un problème
def buggy_function():
    # HACK: Solution temporaire
    return None
""")
            temp_path = Path(f.name)
        
        try:
            issues, lines = analyzer.analyze_file(temp_path)
            
            # Vérifier que les TODOs sont détectés
            todo_issues = [i for i in issues if i.issue_type == "TODO/FIXME/BUG"]
            assert len(todo_issues) >= 3  # TODO, FIXME, BUG
            
            # Vérifier les détails
            issue_messages = [i.description for i in todo_issues]
            assert any("Implémenter" in msg for msg in issue_messages)  # TODO
            assert any("Corriger" in msg for msg in issue_messages)  # FIXME
            assert any("problème" in msg for msg in issue_messages)  # BUG
            
        finally:
            temp_path.unlink()
    
    def test_analyze_file_with_exception_issues(self):
        """Test détection des problèmes d'exceptions"""
        analyzer = CodeQualityAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def bad_function():
    try:
        risky_operation()
    except:  # Exception trop large
        pass
    
    try:
        another_operation()
    except Exception:  # Exception ignorée
        pass
    
    raise Exception("Erreur générique")  # Exception générique
""")
            temp_path = Path(f.name)
        
        try:
            issues, lines = analyzer.analyze_file(temp_path)
            
            # Vérifier les problèmes d'exceptions
            exception_issues = [i for i in issues if i.issue_type in ["Exception trop large", "Exception ignorée", "Exception générique"]]
            assert len(exception_issues) >= 3
            
            # Vérifier la sévérité
            high_severity_issues = [i for i in exception_issues if i.severity == "high"]
            assert len(high_severity_issues) >= 2
            
        finally:
            temp_path.unlink()
    
    def test_analyze_file_with_logging_issues(self):
        """Test détection des problèmes de logging"""
        analyzer = CodeQualityAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import logging

logger = logging.getLogger(__name__)

def function_with_bad_logging():
    print("Debug message")  # Print statement
    
    logger.info("Simple message")  # Logging sans contexte
    
    logger.debug(f"Processing {item}")  # Variable non définie mais pattern ok
""")
            temp_path = Path(f.name)
        
        try:
            issues, lines = analyzer.analyze_file(temp_path)
            
            # Vérifier les problèmes de logging
            logging_issues = [i for i in issues if i.issue_type == "Print statement"]
            assert len(logging_issues) >= 1
            
            # Vérifier les suggestions
            print_issue = next(i for i in logging_issues if i.issue_type == "Print statement")
            assert "logger" in print_issue.suggestion.lower()
            
        finally:
            temp_path.unlink()
    
    def test_analyze_file_with_code_smells(self):
        """Test détection des code smells"""
        analyzer = CodeQualityAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def function_with_smells(items):
    if len(items) == 0:  # Code smell
        return []
    
    if len(items) > 0:  # Code smell
        return items
    
    if True:  # Code smell
        return items
    
    for i in range(len(items)):  # Code smell
        pass
    
    return items
""")
            temp_path = Path(f.name)
        
        try:
            issues, lines = analyzer.analyze_file(temp_path)
            
            # Vérifier les code smells
            smell_issues = [i for i in issues if i.issue_type == "Code smell"]
            assert len(smell_issues) >= 4
            
        finally:
            temp_path.unlink()
    
    def test_analyze_file_with_security_issues(self):
        """Test détection des problèmes de sécurité"""
        analyzer = CodeQualityAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import subprocess

def insecure_function(user_input):
    password = "hardcoded_password"  # Mot de passe en dur
    api_key = "secret_key_123"  # Clé API en dur
    
    eval(user_input)  # eval() dangereux
    
    exec(user_input)  # exec() dangereux
    
    subprocess.run(command, shell=True)  # shell=True dangereux
    
    return password
""")
            temp_path = Path(f.name)
        
        try:
            issues, lines = analyzer.analyze_file(temp_path)
            
            # Vérifier les problèmes de sécurité
            security_issues = [i for i in issues if i.issue_type == "Sécurité"]
            assert len(security_issues) >= 5
            
            # Vérifier que tous sont critiques
            critical_issues = [i for i in security_issues if i.severity == "critical"]
            assert len(critical_issues) >= 5
            
        finally:
            temp_path.unlink()
    
    def test_calculate_metrics(self):
        """Test calcul des métriques de qualité"""
        analyzer = CodeQualityAnalyzer()
        
        # Simuler des problèmes
        analyzer.issues = [
            QualityIssue("file1.py", 1, "TODO/FIXME/BUG", "medium", "TODO found", "Fix it", "code"),
            QualityIssue("file1.py", 2, "Exception", "high", "Bad exception", "Fix it", "code"),
            QualityIssue("file2.py", 1, "Sécurité", "critical", "Security issue", "Fix it", "code")
        ]
        
        metrics = analyzer._calculate_metrics([Path("file1.py"), Path("file2.py")], 100)
        
        assert metrics.total_files == 2
        assert metrics.total_lines == 100
        assert metrics.issues_found == 3
        assert metrics.issues_by_severity["critical"] == 1
        assert metrics.issues_by_severity["high"] == 1
        assert metrics.issues_by_severity["medium"] == 1
        assert 0 <= metrics.quality_score <= 100
    
    def test_export_report_json(self):
        """Test export du rapport en JSON"""
        analyzer = CodeQualityAnalyzer()
        analyzer.issues = [
            QualityIssue("test.py", 1, "Test", "low", "Test issue", "Fix it", "code")
        ]
        analyzer.metrics = analyzer._calculate_metrics([Path("test.py")], 10)
        
        report_json = analyzer.export_report("json")
        report_data = json.loads(report_json)
        
        assert "metrics" in report_data
        assert "issues" in report_data
        assert "summary" in report_data
        assert len(report_data["issues"]) == 1
    
    def test_export_report_markdown(self):
        """Test export du rapport en Markdown"""
        analyzer = CodeQualityAnalyzer()
        analyzer.issues = [
            QualityIssue("test.py", 1, "Test", "low", "Test issue", "Fix it", "code")
        ]
        analyzer.metrics = analyzer._calculate_metrics([Path("test.py")], 10)
        
        report_md = analyzer.export_report("markdown")
        
        assert "# Rapport de Qualité de Code Asmblr" in report_md
        assert "## 📊 Métriques Générales" in report_md
        assert "## 🚨 Problèmes par Sévérité" in report_md


class TestCodeQualityFixer:
    """Tests pour le correcteur automatique"""
    
    def test_fix_print_statement(self):
        """Test correction des print statements"""
        fixer = CodeQualityFixer()
        
        issue = QualityIssue(
            "test.py", 1, "Print statement", "medium",
            "Print statement found", "Use logger", 'print("debug")'
        )
        
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('print("debug message")\n')
            temp_path = Path(f.name)
        
        try:
            # Test en mode dry run
            correction = fixer._fix_print_statement(issue, file_path=temp_path, dry_run=True)
            assert correction is not None
            assert "corrigé" in correction.lower()
            
            # Vérifier que le fichier n'est pas modifié en dry run
            with open(temp_path, 'r') as f:
                content = f.read()
            assert 'print("debug message")' in content
            
        finally:
            temp_path.unlink()
    
    def test_fix_broad_exception(self):
        """Test correction des exceptions larges"""
        fixer = CodeQualityFixer()
        
        issue = QualityIssue(
            "test.py", 1, "Exception trop large", "high",
            "Broad exception", "Specify type", 'except:'
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('try:\n    risky()\nexcept:\n    pass\n')
            temp_path = Path(f.name)
        
        try:
            correction = fixer._fix_broad_exception(issue, file_path=temp_path, dry_run=True)
            assert correction is not None
            assert "corrigée" in correction.lower()
            
        finally:
            temp_path.unlink()
    
    def test_auto_fix_issues(self):
        """Test correction automatique des problèmes"""
        fixer = CodeQualityFixer()
        
        # Create temporary files for testing
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Create test files
            file1 = tmp_path / "test1.py"
            file2 = tmp_path / "test2.py"
            
            with open(file1, 'w') as f:
                f.write('print("test")\n')
            with open(file2, 'w') as f:
                f.write('try:\n    risky()\nexcept:\n    pass\n')
            
            issues = [
                QualityIssue(str(file1), 1, "Print statement", "medium", "Print", "Use logger", 'print("test")'),
                QualityIssue(str(file2), 2, "Exception trop large", "high", "Broad except", "Specify type", 'except:')
            ]
            
            corrections = fixer.auto_fix_issues(issues, dry_run=True)
            
            assert len(corrections) == 2
            assert all("corrigé" in c.lower() for c in corrections)
            assert fixer.fixes_applied == 2


class TestIntegration:
    """Tests d'intégration pour le système de qualité"""
    
    def test_analyze_code_quality_function(self):
        """Test fonction d'analyse de qualité"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Créer des fichiers de test
            test_file = tmp_path / "test.py"
            test_file.write_text("""
# TODO: Fix this
def bad_function():
    print("debug")
    try:
        pass
    except:
        pass
""")
            
            metrics = analyze_code_quality(tmp_path)
            
            assert metrics.total_files == 1
            assert metrics.total_lines > 0
            assert metrics.issues_found > 0
            assert 0 <= metrics.quality_score <= 100
    
    def test_auto_fix_quality_issues_function(self):
        """Test fonction de correction automatique"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Créer un fichier avec des problèmes corrigeables
            test_file = tmp_path / "test.py"
            test_file.write_text("""
def test_function():
    print("debug message")
    try:
        pass
    except:
        pass
""")
            
            # Analyser et corriger
            corrections = auto_fix_quality_issues(dry_run=True)
            
            assert isinstance(corrections, list)
            # Les corrections dépendent de l'analyse du répertoire courant
            # donc on vérifie juste que la fonction s'exécute sans erreur


class TestQualityIssue:
    """Tests pour la classe QualityIssue"""
    
    def test_quality_issue_creation(self):
        """Test création d'une issue de qualité"""
        issue = QualityIssue(
            file_path="test.py",
            line_number=10,
            issue_type="Test",
            severity="medium",
            description="Test description",
            suggestion="Test suggestion",
            code_snippet="test code"
        )
        
        assert issue.file_path == "test.py"
        assert issue.line_number == 10
        assert issue.issue_type == "Test"
        assert issue.severity == "medium"
        assert issue.description == "Test description"
        assert issue.suggestion == "Test suggestion"
        assert issue.code_snippet == "test code"
    
    def test_quality_issue_serialization(self):
        """Test sérialisation d'une issue de qualité"""
        from dataclasses import asdict
        
        issue = QualityIssue(
            "test.py", 1, "Test", "low", "Desc", "Sugg", "code"
        )
        
        issue_dict = asdict(issue)
        
        assert issue_dict["file_path"] == "test.py"
        assert issue_dict["line_number"] == 1
        assert issue_dict["issue_type"] == "Test"


class TestQualityMetrics:
    """Tests pour la classe QualityMetrics"""
    
    def test_quality_metrics_creation(self):
        """Test création des métriques de qualité"""
        from app.core.code_quality import QualityMetrics
        
        metrics = QualityMetrics(
            total_files=5,
            total_lines=1000,
            issues_found=10,
            issues_by_type={"TODO": 5, "Exception": 3, "Security": 2},
            issues_by_severity={"low": 5, "medium": 3, "high": 2},
            quality_score=85.5
        )
        
        assert metrics.total_files == 5
        assert metrics.total_lines == 1000
        assert metrics.issues_found == 10
        assert metrics.issues_by_type["TODO"] == 5
        assert metrics.issues_by_severity["high"] == 2
        assert metrics.quality_score == 85.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
