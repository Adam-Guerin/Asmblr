"""
Script d'exécution des tests complexes pour Asmblr
"""

import subprocess
import sys
import time
from pathlib import Path


def run_test_suite(test_type="all"):
    """
    Exécute une suite de tests complexes
    
    Args:
        test_type: Type de tests ('integration', 'performance', 'resilience', 'all')
    """
    
    test_suites = {
        "integration": {
            "path": "tests/integration/test_complex_integration.py",
            "description": "Tests d'intégration complexes"
        },
        "performance": {
            "path": "tests/performance/test_load_and_stress.py", 
            "description": "Tests de performance et de charge"
        },
        "resilience": {
            "path": "tests/resilience/test_failure_recovery.py",
            "description": "Tests de résilience et de récupération"
        }
    }
    
    if test_type == "all":
        suites_to_run = test_suites
    else:
        suites_to_run = {test_type: test_suites[test_type]}
    
    print(f"🚀 Exécution des tests complexes: {test_type}")
    print("=" * 60)
    
    results = {}
    
    for suite_name, suite_info in suites_to_run.items():
        print(f"\n📋 {suite_info['description']}")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            # Exécuter la suite de tests
            cmd = [
                sys.executable, "-m", "pytest", 
                suite_info["path"],
                "-v", "-s",  # Verbose avec sortie des prints
                "--tb=short",  # Traceback court
                "--no-cov"  # Pas de couverture pour les tests complexes
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Analyser les résultats
            output_lines = result.stdout.split('\n')
            
            passed = 0
            failed = 0
            errors = 0
            
            for line in output_lines:
                if "PASSED" in line:
                    passed += 1
                elif "FAILED" in line:
                    failed += 1
                elif "ERROR" in line:
                    errors += 1
                elif " passed in " in line:
                    # Extraire le nombre de tests passés
                    try:
                        passed_count = int(line.split(" passed in ")[0].split()[-1])
                        passed = max(passed, passed_count)
                    except:
                        pass
            
            total = passed + failed + errors
            success_rate = (passed / total * 100) if total > 0 else 0
            
            results[suite_name] = {
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "total": total,
                "duration": duration,
                "success_rate": success_rate,
                "output": result.stdout,
                "return_code": result.returncode
            }
            
            # Afficher les résultats
            status_emoji = "✅" if result.returncode == 0 else "❌"
            print(f"{status_emoji} {suite_name}: {passed}/{total} tests ({success_rate:.1f}%)")
            print(f"   Duration: {duration:.2f}s")
            print(f"   Return code: {result.returncode}")
            
            if result.returncode != 0:
                print(f"   Errors: {errors}")
                print(f"   Failed: {failed}")
                # Afficher les erreurs principales
                error_lines = [line for line in result.stdout.split('\n') if 'ERROR' in line or 'FAILED' in line]
                if error_lines:
                    print("   Sample errors:")
                    for line in error_lines[:3]:
                        print(f"     {line}")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'exécution de {suite_name}: {e}")
            results[suite_name] = {
                "passed": 0,
                "failed": 0,
                "errors": 1,
                "total": 0,
                "duration": 0,
                "success_rate": 0,
                "output": str(e),
                "return_code": 1
            }
    
    # Résumé final
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS COMPLEXES")
    print("=" * 60)
    
    total_passed = sum(r["passed"] for r in results.values())
    total_failed = sum(r["failed"] for r in results.values())
    total_errors = sum(r["errors"] for r in results.values())
    total_tests = total_passed + total_failed + total_errors
    total_duration = sum(r["duration"] for r in results.values())
    
    if total_tests > 0:
        overall_success_rate = (total_passed / total_tests) * 100
    else:
        overall_success_rate = 0
    
    print(f"📈 Tests totaux: {total_passed}/{total_tests} ({overall_success_rate:.1f}%)")
    print(f"⏱️  Durée totale: {total_duration:.2f}s")
    print(f"✅ Réussis: {total_passed}")
    print(f"❌ Échoués: {total_failed}")
    print(f"🚨 Erreurs: {total_errors}")
    
    # Détails par suite
    print(f"\n📋 Détails par suite:")
    for suite_name, result in results.items():
        status_emoji = "✅" if result["return_code"] == 0 else "❌"
        print(f"  {status_emoji} {suite_name}: {result['passed']}/{result['total']} ({result['success_rate']:.1f}%) - {result['duration']:.2f}s")
    
    # Recommandations
    print(f"\n💡 Recommandations:")
    
    if overall_success_rate < 80:
        print("  ⚠️  Taux de succès faible - Vérifier les tests échoués")
    elif overall_success_rate < 95:
        print("  ✅ Taux de succès acceptable - Quelques améliorations possibles")
    else:
        print("  🌟 Excellent taux de succès - Tests robustes")
    
    if total_duration > 300:  # 5 minutes
        print("  ⏱️  Tests longs - Considérer l'optimisation")
    
    if total_errors > 0:
        print("  🚨 Erreurs de test - Vérifier la configuration")
    
    # Sauvegarder les résultats
    results_file = Path("complex_test_results.json")
    import json
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Résultats détaillés sauvegardés: {results_file}")
    
    return overall_success_rate >= 80


def run_specific_test(test_path, test_name):
    """Exécute un test spécifique"""
    print(f"🎯 Exécution du test: {test_name}")
    print(f"📂 Chemin: {test_path}")
    print("-" * 40)
    
    start_time = time.time()
    
    try:
        cmd = [
            sys.executable, "-m", "pytest",
            test_path,
            "-v", "-s",
            "--tb=long",  # Traceback détaillé pour un test spécifique
            "--no-cov"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"\n⏱️  Durée: {duration:.2f}s")
        print(f"📋 Return code: {result.returncode}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
        return False


def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Exécuteur de tests complexes pour Asmblr")
    parser.add_argument(
        "--type",
        choices=["integration", "performance", "resilience", "all"],
        default="all",
        help="Type de tests à exécuter"
    )
    parser.add_argument(
        "--specific",
        help="Chemin vers un test spécifique à exécuter"
    )
    parser.add_argument(
        "--name",
        help="Nom du test spécifique"
    )
    
    args = parser.parse_args()
    
    if args.specific:
        # Exécuter un test spécifique
        success = run_specific_test(args.specific, args.name or "Test spécifique")
        sys.exit(0 if success else 1)
    else:
        # Exécuter une suite de tests
        success = run_test_suite(args.type)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
