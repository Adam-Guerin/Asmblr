#!/usr/bin/env python3
"""
Tests de charge et performance pour Asmblr - Phase 3
Validation des performances en conditions de production
"""

import asyncio
import aiohttp
import time
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
import argparse

# Configuration
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_CONCURRENT_USERS = 50
DEFAULT_DURATION_SECONDS = 60
DEFAULT_RAMP_UP_SECONDS = 10

class LoadTestResult:
    """Résultat d'un test de charge"""
    
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []
        self.status_codes = {}
        self.errors = []
        self.start_time = None
        self.end_time = None
    
    def add_request(self, success: bool, response_time: float, status_code: int = None, error: str = None):
        """Ajoute une requête aux résultats"""
        self.total_requests += 1
        
        if success:
            self.successful_requests += 1
            self.response_times.append(response_time)
            if status_code:
                self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1
        else:
            self.failed_requests += 1
            if error:
                self.errors.append(error)
    
    def get_stats(self) -> Dict[str, Any]:
        """Calcule les statistiques"""
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0
        
        stats = {
            "duration_seconds": duration,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
            "requests_per_second": self.total_requests / duration if duration > 0 else 0,
            "status_codes": self.status_codes,
            "errors": self.errors[:10]  # Limiter à 10 erreurs
        }
        
        if self.response_times:
            stats.update({
                "avg_response_time": statistics.mean(self.response_times),
                "min_response_time": min(self.response_times),
                "max_response_time": max(self.response_times),
                "median_response_time": statistics.median(self.response_times),
                "p95_response_time": self._percentile(self.response_times, 95),
                "p99_response_time": self._percentile(self.response_times, 99)
            })
        
        return stats
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calcule un percentile"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))


class LoadTester:
    """Testeur de charge pour Asmblr"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
        self.result = LoadTestResult()
    
    async def __aenter__(self):
        """Initialise le testeur"""
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=100,
            ttl_dns_cache=300,
            ttl_dns_cache_per_host=300,
            use_dns_cache=True,
            keepalive_timeout=60,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "User-Agent": "Asmblr-LoadTester/1.0",
                "Accept": "application/json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Nettoie le testeur"""
        if self.session:
            await self.session.close()
    
    async def test_health_endpoint(self) -> bool:
        """Test le endpoint de santé"""
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/health") as response:
                response_time = time.time() - start_time
                success = response.status == 200
                self.result.add_request(success, response_time, response.status)
                return success
        except Exception as e:
            self.result.add_request(False, 0, error=str(e))
            return False
    
    async def test_create_pipeline(self, topic: str = None) -> bool:
        """Test la création de pipeline"""
        try:
            topic = topic or f"Load test pipeline {int(time.time())}"
            payload = {
                "topic": topic,
                "mode": "quick",
                "config": {"test": True}
            }
            
            start_time = time.time()
            async with self.session.post(
                f"{self.base_url}/api/v1/pipelines",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                success = response.status in [200, 201]
                self.result.add_request(success, response_time, response.status)
                return success
        except Exception as e:
            self.result.add_request(False, 0, error=str(e))
            return False
    
    async def test_list_pipelines(self) -> bool:
        """Test le listing des pipelines"""
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/api/v1/pipelines") as response:
                response_time = time.time() - start_time
                success = response.status == 200
                self.result.add_request(success, response_time, response.status)
                return success
        except Exception as e:
            self.result.add_request(False, 0, error=str(e))
            return False
    
    async def test_agent_task(self) -> bool:
        """Test l'exécution d'une tâche d'agent"""
        try:
            payload = {
                "task_type": "idea_generation",
                "input_data": {"topic": f"Load test topic {int(time.time())}"},
                "config": {"max_ideas": 5}
            }
            
            start_time = time.time()
            async with self.session.post(
                f"{self.base_url}/api/v1/agents/execute",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                success = response.status == 200
                self.result.add_request(success, response_time, response.status)
                return success
        except Exception as e:
            self.result.add_request(False, 0, error=str(e))
            return False
    
    async def test_media_upload(self) -> bool:
        """Test l'upload de média (simulation)"""
        try:
            # Simuler un upload avec un petit payload
            payload = {
                "media_type": "document",
                "prompt": f"Load test document {int(time.time())}",
                "config": {"test": True}
            }
            
            start_time = time.time()
            async with self.session.post(
                f"{self.base_url}/api/v1/media/generate",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                success = response.status == 200
                self.result.add_request(success, response_time, response.status)
                return success
        except Exception as e:
            self.result.add_request(False, 0, error=str(e))
            return False
    
    async def run_user_simulation(self, user_id: int, duration_seconds: int, test_types: List[str]) -> None:
        """Simule l'activité d'un utilisateur"""
        end_time = time.time() + duration_seconds
        
        while time.time() < end_time:
            # Choisir un type de test aléatoirement
            test_type = test_types[user_id % len(test_types)]
            
            if test_type == "health":
                await self.test_health_endpoint()
            elif test_type == "pipeline":
                await self.test_create_pipeline()
            elif test_type == "list":
                await self.test_list_pipelines()
            elif test_type == "agent":
                await self.test_agent_task()
            elif test_type == "media":
                await self.test_media_upload()
            
            # Pause entre les requêtes
            await asyncio.sleep(0.1 + (user_id % 5) * 0.05)
    
    async def run_load_test(self, concurrent_users: int, duration_seconds: int, 
                          ramp_up_seconds: int = 10) -> LoadTestResult:
        """Exécute un test de charge"""
        print(f"🚀 Démarrage du test de charge...")
        print(f"   URL: {self.base_url}")
        print(f"   Utilisateurs concurrents: {concurrent_users}")
        print(f"   Durée: {duration_seconds} secondes")
        print(f"   Montée en charge: {ramp_up_seconds} secondes")
        
        self.result.start_time = datetime.utcnow()
        
        # Types de tests à exécuter
        test_types = ["health", "pipeline", "list", "agent", "media"]
        
        # Créer les tâches utilisateur avec montée en charge progressive
        tasks = []
        users_per_second = concurrent_users / ramp_up_seconds
        
        for i in range(concurrent_users):
            delay = i / users_per_second
            task = asyncio.create_task(
                self._delayed_user_simulation(i, duration_seconds, delay, test_types)
            )
            tasks.append(task)
        
        # Exécuter toutes les tâches
        await asyncio.gather(*tasks, return_exceptions=True)
        
        self.result.end_time = datetime.utcnow()
        
        return self.result
    
    async def _delayed_user_simulation(self, user_id: int, duration_seconds: int, 
                                   delay: float, test_types: List[str]) -> None:
        """Simulation utilisateur avec délai"""
        if delay > 0:
            await asyncio.sleep(delay)
        
        await self.run_user_simulation(user_id, duration_seconds, test_types)


class PerformanceTestSuite:
    """Suite de tests de performance"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    async def run_stress_test(self, max_users: int = 200) -> Dict[str, Any]:
        """Test de stress progressif"""
        print("\n🔥 TEST DE STRESS PROGRESSIF")
        print("=" * 50)
        
        results = {}
        user_levels = [10, 25, 50, 100, 150, 200]
        
        for users in user_levels:
            if users > max_users:
                break
            
            print(f"\n📊 Test avec {users} utilisateurs...")
            
            async with LoadTester(self.base_url) as tester:
                result = await tester.run_load_test(
                    concurrent_users=users,
                    duration_seconds=30,
                    ramp_up_seconds=5
                )
                
                stats = result.get_stats()
                results[f"users_{users}"] = stats
                
                print(f"   ✅ Requêtes: {stats['total_requests']}")
                print(f"   ⚡ Taux de succès: {stats['success_rate']:.1f}%")
                print(f"   ⏱️  Temps de réponse moyen: {stats.get('avg_response_time', 0):.3f}s")
                print(f"   📈 RPS: {stats['requests_per_second']:.1f}")
                
                # Arrêter si le taux de succès est trop bas
                if stats['success_rate'] < 80:
                    print(f"   ⚠️  Arrêt du test: taux de succès trop bas")
                    break
        
        return results
    
    async def run_endurance_test(self, duration_minutes: int = 10) -> Dict[str, Any]:
        """Test d'endurance"""
        print(f"\n⏰ TEST D'ENDURANCE ({duration_minutes} minutes)")
        print("=" * 50)
        
        async with LoadTester(self.base_url) as tester:
            result = await tester.run_load_test(
                concurrent_users=20,
                duration_seconds=duration_minutes * 60,
                ramp_up_seconds=30
            )
            
            stats = result.get_stats()
            
            print(f"   ✅ Requêtes totales: {stats['total_requests']}")
            print(f"   ⚡ Taux de succès: {stats['success_rate']:.1f}%")
            print(f"   ⏱️  Temps de réponse moyen: {stats.get('avg_response_time', 0):.3f}s")
            print(f"   📈 RPS moyen: {stats['requests_per_second']:.1f}")
            print(f"   📊 P95: {stats.get('p95_response_time', 0):.3f}s")
            print(f"   📊 P99: {stats.get('p99_response_time', 0):.3f}s")
            
            return stats
    
    async def run_spike_test(self) -> Dict[str, Any]:
        """Test de pic (spike)"""
        print("\n📈 TEST DE PIC (SPIKE)")
        print("=" * 50)
        
        results = {}
        
        # Phase 1: Charge normale
        print("📊 Phase 1: Charge normale (20 utilisateurs)")
        async with LoadTester(self.base_url) as tester:
            result1 = await tester.run_load_test(
                concurrent_users=20,
                duration_seconds=60,
                ramp_up_seconds=10
            )
            stats1 = result1.get_stats()
            results["normal_load"] = stats1
            
            print(f"   ✅ RPS: {stats1['requests_per_second']:.1f}")
            print(f"   ⏱️  Temps de réponse: {stats1.get('avg_response_time', 0):.3f}s")
        
        # Pause
        await asyncio.sleep(10)
        
        # Phase 2: Pic de charge
        print("📊 Phase 2: Pic de charge (100 utilisateurs)")
        async with LoadTester(self.base_url) as tester:
            result2 = await tester.run_load_test(
                concurrent_users=100,
                duration_seconds=30,
                ramp_up_seconds=5
            )
            stats2 = result2.get_stats()
            results["spike_load"] = stats2
            
            print(f"   ✅ RPS: {stats2['requests_per_second']:.1f}")
            print(f"   ⏱️  Temps de réponse: {stats2.get('avg_response_time', 0):.3f}s")
        
        # Pause
        await asyncio.sleep(10)
        
        # Phase 3: Retour à la normale
        print("📊 Phase 3: Retour à la normale (20 utilisateurs)")
        async with LoadTester(self.base_url) as tester:
            result3 = await tester.run_load_test(
                concurrent_users=20,
                duration_seconds=60,
                ramp_up_seconds=10
            )
            stats3 = result3.get_stats()
            results["recovery"] = stats3
            
            print(f"   ✅ RPS: {stats3['requests_per_second']:.1f}")
            print(f"   ⏱️  Temps de réponse: {stats3.get('avg_response_time', 0):.3f}s")
        
        return results
    
    async def run_all_tests(self, max_users: int = 200, endurance_minutes: int = 5) -> Dict[str, Any]:
        """Exécute tous les tests de performance"""
        print("🧪 SUITE COMPLÈTE DE TESTS DE PERFORMANCE")
        print("=" * 60)
        print(f"URL cible: {self.base_url}")
        print(f"Utilisateurs max: {max_users}")
        print(f"Durée endurance: {endurance_minutes} minutes")
        
        start_time = datetime.utcnow()
        
        all_results = {
            "test_suite": "asmblr_performance_tests",
            "start_time": start_time.isoformat(),
            "base_url": self.base_url,
            "configuration": {
                "max_users": max_users,
                "endurance_minutes": endurance_minutes
            }
        }
        
        try:
            # Test de stress
            all_results["stress_test"] = await self.run_stress_test(max_users)
            
            # Test d'endurance
            all_results["endurance_test"] = await self.run_endurance_test(endurance_minutes)
            
            # Test de pic
            all_results["spike_test"] = await self.run_spike_test()
            
        except Exception as e:
            print(f"❌ Erreur lors des tests: {e}")
            all_results["error"] = str(e)
        
        finally:
            end_time = datetime.utcnow()
            all_results["end_time"] = end_time.isoformat()
            all_results["total_duration"] = (end_time - start_time).total_seconds()
        
        # Sauvegarder les résultats
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_test_results_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\n💾 Résultats sauvegardés dans: {filename}")
        
        # Résumé
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS DE PERFORMANCE")
        print("=" * 60)
        
        if "stress_test" in all_results:
            max_stress_users = max([int(k.split("_")[1]) for k in all_results["stress_test"].keys()])
            stress_result = all_results["stress_test"][f"users_{max_stress_users}"]
            print(f"🔥 Stress test max: {max_stress_users} utilisateurs")
            print(f"   RPS max: {stress_result['requests_per_second']:.1f}")
            print(f"   Succès: {stress_result['success_rate']:.1f}%")
        
        if "endurance_test" in all_results:
            endurance = all_results["endurance_test"]
            print(f"⏰ Endurance test: {endurance['duration_seconds']:.0f}s")
            print(f"   Requêtes totales: {endurance['total_requests']}")
            print(f"   RPS moyen: {endurance['requests_per_second']:.1f}")
        
        if "spike_test" in all_results:
            spike = all_results["spike_test"]
            if "spike_load" in spike:
                spike_load = spike["spike_load"]
                print(f"📈 Spike test: {spike_load['requests_per_second']:.1f} RPS")
                print(f"   Temps de réponse: {spike_load.get('avg_response_time', 0):.3f}s")
        
        return all_results


async def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Tests de charge et performance pour Asmblr")
    parser.add_argument("--url", default=DEFAULT_BASE_URL, help="URL de base à tester")
    parser.add_argument("--users", type=int, default=DEFAULT_CONCURRENT_USERS, help="Nombre d'utilisateurs concurrents")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION_SECONDS, help="Durée du test en secondes")
    parser.add_argument("--ramp-up", type=int, default=DEFAULT_RAMP_UP_SECONDS, help="Temps de montée en charge")
    parser.add_argument("--max-users", type=int, default=200, help="Utilisateurs max pour le test de stress")
    parser.add_argument("--endurance", type=int, default=5, help="Durée du test d'endurance en minutes")
    parser.add_argument("--test", choices=["load", "stress", "endurance", "spike", "all"], default="all", help="Type de test à exécuter")
    
    args = parser.parse_args()
    
    test_suite = PerformanceTestSuite(args.url)
    
    try:
        if args.test == "load":
            async with LoadTester(args.url) as tester:
                result = await tester.run_load_test(args.users, args.duration, args.ramp_up)
                print(json.dumps(result.get_stats(), indent=2))
        
        elif args.test == "stress":
            await test_suite.run_stress_test(args.max_users)
        
        elif args.test == "endurance":
            await test_suite.run_endurance_test(args.endurance)
        
        elif args.test == "spike":
            await test_suite.run_spike_test()
        
        elif args.test == "all":
            await test_suite.run_all_tests(args.max_users, args.endurance)
    
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrompus par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")


if __name__ == "__main__":
    asyncio.run(main())
