"""
Tests de performance et de charge pour Asmblr
Tests de charge, stress, et limites du système
"""

import pytest
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import gc
import random

from app.core.pipeline import VenturePipeline
from app.core.cache import CacheManager
from app.core.llm import LLMClient


class TestPerformanceAndLoad:
    """Tests de performance et de charge"""
    
    @pytest.fixture
    def performance_config(self):
        """Configuration pour les tests de performance"""
        return {
            "DEFAULT_N_IDEAS": "10",
            "FAST_MODE": "true",
            "CACHE_TTL": "300",
            "MAX_CACHE_SIZE": "1000"
        }
    
    def test_pipeline_performance_benchmark(self, performance_config):
        """Benchmark de performance des pipelines"""
        results = []
        
        # Mock LLM pour performance
        with patch('app.core.llm.httpx.AsyncClient') as mock_client:
            mock_response = type('MockResponse', (), {
                'status_code': 200,
                'json': lambda: {"response": "Fast response", "done": True}
            })()
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Test avec différentes tailles de données
            test_sizes = [1, 5, 10, 25, 50]
            
            for size in test_sizes:
                # Mesurer la performance pour cette taille
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss
                
                # Créer et exécuter la pipeline
                cache = CacheManager(max_size=1000, ttl_seconds=300)
                llm_client = LLMClient()
                pipeline = VenturePipeline(cache_manager=cache, llm_client=llm_client)
                
                run_id = pipeline.create_run()
                
                # Ajouter les idées
                for i in range(size):
                    idea = {
                        "name": f"Test Idea {i}",
                        "description": f"Description for test idea {i} with some content"
                    }
                    pipeline.add_idea(run_id, idea)
                
                # Exécuter
                result = pipeline.run_pipeline(run_id)
                
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss
                
                # Calculer les métriques
                duration = end_time - start_time
                memory_used = end_memory - start_memory
                throughput = size / duration
                
                results.append({
                    "size": size,
                    "duration": duration,
                    "memory_used": memory_used,
                    "throughput": throughput,
                    "success": result["status"] == "completed"
                })
                
                # Nettoyer
                del cache, llm_client, pipeline
                gc.collect()
            
            # Analyser les résultats
            successful_results = [r for r in results if r["success"]]
            assert len(successful_results) == len(test_sizes)
            
            # Vérifier que la performance est acceptable
            for result in successful_results:
                assert result["duration"] < 10.0  # Moins de 10 secondes
                assert result["throughput"] > 0.5  # Au moins 0.5 opérations par seconde
                assert result["memory_used"] < 50 * 1024 * 1024  # Moins de 50MB par opération
            
            # Vérifier que la performance ne se dégrade pas trop
            throughputs = [r["throughput"] for r in successful_results]
            assert statistics.stdev(throughputs) < statistics.mean(throughputs) * 0.5  # Écart-type < 50% de la moyenne
    
    def test_concurrent_load_test(self, performance_config):
        """Test de charge concurrent"""
        concurrent_users = 20
        operations_per_user = 10
        
        # Mock LLM
        with patch('app.core.llm.httpx.AsyncClient') as mock_client:
            mock_response = type('MockResponse', (), {
                'status_code': 200,
                'json': lambda: {"response": "Concurrent response", "done": True}
            })()
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Mesurer les ressources avant le test
            initial_memory = psutil.Process().memory_info().rss
            initial_cpu = psutil.cpu_percent(interval=1)
            
            start_time = time.time()
            
            # Exécuter les opérations concurrentes
            def user_operations(user_id):
                user_results = []
                
                for op_id in range(operations_per_user):
                    # Créer des composants isolés
                    cache = CacheManager(max_size=100, ttl_seconds=300)
                    llm_client = LLMClient()
                    pipeline = VenturePipeline(cache_manager=cache, llm_client=llm_client)
                    
                    try:
                        run_id = pipeline.create_run()
                        idea = {
                            "name": f"User {user_id} Idea {op_id}",
                            "description": f"Description from user {user_id}, operation {op_id}"
                        }
                        pipeline.add_idea(run_id, idea)
                        
                        result = pipeline.run_pipeline(run_id)
                        user_results.append({
                            "user_id": user_id,
                            "operation_id": op_id,
                            "success": result["status"] == "completed",
                            "run_id": run_id
                        })
                        
                    except Exception as e:
                        user_results.append({
                            "user_id": user_id,
                            "operation_id": op_id,
                            "success": False,
                            "error": str(e)
                        })
                    finally:
                        # Nettoyer
                        del cache, llm_client, pipeline
                
                return user_results
            
            # Exécuter en parallèle
            with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                futures = [executor.submit(user_operations, i) for i in range(concurrent_users)]
                all_results = []
                
                for future in as_completed(futures):
                    user_results = future.result()
                    all_results.extend(user_results)
            
            end_time = time.time()
            
            # Mesurer les ressources après le test
            final_memory = psutil.Process().memory_info().rss
            final_cpu = psutil.cpu_percent(interval=1)
            
            # Analyser les résultats
            total_operations = len(all_results)
            successful_operations = len([r for r in all_results if r["success"]])
            total_time = end_time - start_time
            
            success_rate = successful_operations / total_operations
            operations_per_second = total_operations / total_time
            memory_increase = final_memory - initial_memory
            
            # Assertions
            assert total_operations == concurrent_users * operations_per_user
            assert success_rate > 0.95  # Au moins 95% de succès
            assert operations_per_second > 10  # Au moins 10 opérations par seconde
            assert memory_increase < 200 * 1024 * 1024  # Moins de 200MB supplémentaires
            
            print(f"\n📊 Load Test Results:")
            print(f"  Concurrent users: {concurrent_users}")
            print(f"  Operations per user: {operations_per_user}")
            print(f"  Total operations: {total_operations}")
            print(f"  Success rate: {success_rate:.2%}")
            print(f"  Operations/sec: {operations_per_second:.2f}")
            print(f"  Memory increase: {memory_increase / 1024 / 1024:.2f}MB")
            print(f"  Duration: {total_time:.2f}s")
    
    def test_stress_test(self, performance_config):
        """Test de stress - limites du système"""
        stress_duration = 30  # secondes
        max_concurrent = 50
        
        # Mock LLM
        with patch('app.core.llm.httpx.AsyncClient') as mock_client:
            mock_response = type('MockResponse', (), {
                'status_code': 200,
                'json': lambda: {"response": "Stress test response", "done": True}
            })()
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Variables pour le suivi
            operations_completed = 0
            operations_failed = 0
            start_time = time.time()
            
            def stress_worker():
                nonlocal operations_completed, operations_failed
                
                while time.time() - start_time < stress_duration:
                    try:
                        cache = CacheManager(max_size=50, ttl_seconds=300)
                        llm_client = LLMClient()
                        pipeline = VenturePipeline(cache_manager=cache, llm_client=llm_client)
                        
                        run_id = pipeline.create_run()
                        pipeline.add_idea(run_id, {
                            "name": f"Stress {random.randint(1, 1000)}",
                            "description": "Stress test idea"
                        })
                        
                        result = pipeline.run_pipeline(run_id)
                        
                        if result["status"] == "completed":
                            operations_completed += 1
                        else:
                            operations_failed += 1
                        
                        # Nettoyer
                        del cache, llm_client, pipeline
                        
                    except Exception:
                        operations_failed += 1
                    
                    # Petite pause pour ne pas surcharger
                    time.sleep(0.1)
            
            # Démarrer les workers de stress
            with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                futures = [executor.submit(stress_worker) for _ in range(max_concurrent)]
                
                # Attendre la fin du stress test
                for future in as_completed(futures):
                    future.result()
            
            # Calculer les métriques
            actual_duration = time.time() - start_time
            total_operations = operations_completed + operations_failed
            ops_per_second = total_operations / actual_duration
            success_rate = operations_completed / total_operations if total_operations > 0 else 0
            
            # Assertions
            assert actual_duration >= stress_duration
            assert total_operations > 0
            assert success_rate > 0.8  # Au moins 80% de succès même sous stress
            assert ops_per_second > 5  # Maintenir une performance minimale
            
            print(f"\n🔥 Stress Test Results:")
            print(f"  Duration: {actual_duration:.2f}s")
            print(f"  Max concurrent: {max_concurrent}")
            print(f"  Total operations: {total_operations}")
            print(f"  Completed: {operations_completed}")
            print(f"  Failed: {operations_failed}")
            print(f"  Success rate: {success_rate:.2%}")
            print(f"  Operations/sec: {ops_per_second:.2f}")
    
    def test_memory_leak_detection(self, performance_config):
        """Test de détection de fuites mémoire"""
        iterations = 100
        memory_samples = []
        
        # Mock LLM
        with patch('app.core.llm.httpx.AsyncClient') as mock_client:
            mock_response = type('MockResponse', (), {
                'status_code': 200,
                'json': lambda: {"response": "Memory test response", "done": True}
            })()
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            for i in range(iterations):
                # Mesurer la mémoire avant l'opération
                memory_before = psutil.Process().memory_info().rss
                
                # Créer et utiliser des composants
                cache = CacheManager(max_size=100, ttl_seconds=300)
                llm_client = LLMClient()
                pipeline = VenturePipeline(cache_manager=cache, llm_client=llm_client)
                
                run_id = pipeline.create_run()
                pipeline.add_idea(run_id, {"name": f"Memory test {i}", "description": "Test"})
                pipeline.run_pipeline(run_id)
                
                # Mesurer la mémoire après
                memory_after = psutil.Process().memory_info().rss
                memory_delta = memory_after - memory_before
                
                memory_samples.append(memory_delta)
                
                # Nettoyer explicitement
                del cache, llm_client, pipeline
                
                # Forcer le garbage collection périodiquement
                if i % 10 == 0:
                    gc.collect()
            
            # Analyser les échantillons de mémoire
            avg_memory_per_op = statistics.mean(memory_samples)
            max_memory_per_op = max(memory_samples)
            min_memory_per_op = min(memory_samples)
            
            # Vérifier qu'il n'y a pas de fuite mémoire significative
            # La mémoire utilisée par opération devrait être relativement stable
            memory_variance = statistics.stdev(memory_samples) if len(memory_samples) > 1 else 0
            
            assert avg_memory_per_op < 10 * 1024 * 1024  # Moins de 10MB par opération
            assert max_memory_per_op < 50 * 1024 * 1024  # Moins de 50MB pour une opération
            assert memory_variance < avg_memory_per_op * 0.5  # Variance < 50% de la moyenne
            
            print(f"\n💾 Memory Leak Test Results:")
            print(f"  Iterations: {iterations}")
            print(f"  Avg memory/op: {avg_memory_per_op / 1024 / 1024:.2f}MB")
            print(f"  Max memory/op: {max_memory_per_op / 1024 / 1024:.2f}MB")
            print(f"  Min memory/op: {min_memory_per_op / 1024 / 1024:.2f}MB")
            print(f"  Memory variance: {memory_variance / 1024 / 1024:.2f}MB")
    
    def test_cache_performance_under_load(self, performance_config):
        """Test de performance du cache sous charge"""
        cache_sizes = [100, 500, 1000, 2000]
        operations_per_size = 1000
        
        results = []
        
        for cache_size in cache_sizes:
            cache = CacheManager(max_size=cache_size, ttl_seconds=300)
            
            # Test d'écriture
            write_start = time.time()
            for i in range(operations_per_size):
                cache.set(f"key_{i}", f"value_{i}")
            write_time = time.time() - write_start
            
            # Test de lecture
            read_start = time.time()
            for i in range(operations_per_size):
                value = cache.get(f"key_{i}")
                assert value == f"value_{i}"
            read_time = time.time() - read_start
            
            # Test de lecture/écriture mixte
            mixed_start = time.time()
            for i in range(operations_per_size // 2):
                cache.set(f"mixed_key_{i}", f"mixed_value_{i}")
                value = cache.get(f"key_{i}")
            mixed_time = time.time() - mixed_start
            
            results.append({
                "cache_size": cache_size,
                "write_time": write_time,
                "read_time": read_time,
                "mixed_time": mixed_time,
                "write_ops_sec": operations_per_size / write_time,
                "read_ops_sec": operations_per_size / read_time,
                "mixed_ops_sec": (operations_per_size // 2) / mixed_time
            })
            
            # Nettoyer
            del cache
            gc.collect()
        
        # Analyser les résultats
        for result in results:
            assert result["write_ops_sec"] > 1000  # Au moins 1000 écritures/sec
            assert result["read_ops_sec"] > 5000   # Au moins 5000 lectures/sec
            assert result["mixed_ops_sec"] > 500   # Au moins 500 opérations mixtes/sec
        
        # Vérifier que la performance ne se dégrade pas trop avec la taille
        write_throughputs = [r["write_ops_sec"] for r in results]
        read_throughputs = [r["read_ops_sec"] for r in results]
        
        assert statistics.stdev(write_throughputs) < statistics.mean(write_throughputs) * 0.3
        assert statistics.stdev(read_throughputs) < statistics.mean(read_throughputs) * 0.3
        
        print(f"\n🗄️ Cache Performance Results:")
        for result in results:
            print(f"  Size {result['cache_size']}: "
                  f"Write {result['write_ops_sec']:.0f} ops/s, "
                  f"Read {result['read_ops_sec']:.0f} ops/s, "
                  f"Mixed {result['mixed_ops_sec']:.0f} ops/s")
    
    def test_scalability_analysis(self, performance_config):
        """Analyse de scalabilité"""
        scale_factors = [1, 2, 5, 10]  # Multiplicateurs de charge
        
        baseline_results = None
        scalability_results = []
        
        for factor in scale_factors:
            operations = int(10 * factor)  # 10, 20, 50, 100 opérations
            
            # Mock LLM
            with patch('app.core.llm.httpx.AsyncClient') as mock_client:
                mock_response = type('MockResponse', (), {
                    'status_code': 200,
                    'json': lambda: {"response": "Scalability test", "done": True}
                })()
                mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
                
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss
                
                # Exécuter les opérations
                with ThreadPoolExecutor(max_workers=min(10, operations)) as executor:
                    futures = []
                    
                    for i in range(operations):
                        def scale_operation(index):
                            cache = CacheManager(max_size=100, ttl_seconds=300)
                            llm_client = LLMClient()
                            pipeline = VenturePipeline(cache_manager=cache, llm_client=llm_client)
                            
                            run_id = pipeline.create_run()
                            pipeline.add_idea(run_id, {"name": f"Scale {index}", "description": "Test"})
                            result = pipeline.run_pipeline(run_id)
                            
                            return result["status"] == "completed"
                        
                        future = executor.submit(scale_operation, i)
                        futures.append(future)
                    
                    # Attendre les résultats
                    results = [future.result() for future in as_completed(futures)]
                
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss
                
                # Calculer les métriques
                duration = end_time - start_time
                memory_used = end_memory - start_memory
                success_rate = sum(results) / len(results)
                throughput = operations / duration
                
                result_data = {
                    "factor": factor,
                    "operations": operations,
                    "duration": duration,
                    "memory_used": memory_used,
                    "success_rate": success_rate,
                    "throughput": throughput
                }
                
                scalability_results.append(result_data)
                
                # Garder le baseline (factor = 1)
                if factor == 1:
                    baseline_results = result_data
        
        # Analyser la scalabilité
        baseline_throughput = baseline_results["throughput"]
        baseline_memory_per_op = baseline_results["memory_used"] / baseline_results["operations"]
        
        for result in scalability_results[1:]:  # Skip baseline
            factor = result["factor"]
            
            # Calculer l'efficacité de scalabilité
            expected_throughput = baseline_throughput * factor
            throughput_efficiency = result["throughput"] / expected_throughput
            
            expected_memory_per_op = baseline_memory_per_op
            actual_memory_per_op = result["memory_used"] / result["operations"]
            memory_efficiency = expected_memory_per_op / actual_memory_per_op
            
            # Assertions de scalabilité
            assert throughput_efficiency > 0.7  # Au moins 70% de l'accélération linéaire
            assert memory_efficiency > 0.8     # Pas plus de 25% de mémoire supplémentaire par opération
            assert result["success_rate"] > 0.95  # Maintenir un haut taux de succès
            
            print(f"  Scale {factor}x: Throughput efficiency {throughput_efficiency:.2%}, "
                  f"Memory efficiency {memory_efficiency:.2%}")
        
        print(f"\n📈 Scalability Analysis:")
        print(f"  Baseline throughput: {baseline_throughput:.2f} ops/sec")
        print(f"  Baseline memory/op: {baseline_memory_per_op / 1024:.2f}KB")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
