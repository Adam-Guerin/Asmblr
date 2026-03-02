"""
Tests de résilience et de récupération pour Asmblr
Tests de scénarios extrêmes et de récupération d'erreur
"""

import pytest
import asyncio
import time
import random
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.core.pipeline import VenturePipeline
from app.core.cache import CacheManager
from app.core.llm import LLMClient


class TestResilienceAndRecovery:
    """Tests de résilience et de récupération"""
    
    @pytest.fixture
    def resilience_config(self):
        """Configuration pour les tests de résilience"""
        return {
            "DEFAULT_N_IDEAS": "5",
            "FAST_MODE": "true",
            "RETRY_MAX_ATTEMPTS": "5",
            "RETRY_MIN_WAIT": "1",
            "RETRY_MAX_WAIT": "10"
        }
    
    def test_network_failure_recovery(self, resilience_config):
        """Test de récupération après défaillance réseau"""
        failure_count = 0
        max_failures = 3
        
        # Mock LLM avec défaillances réseau
        with patch('app.core.llm.httpx.AsyncClient') as mock_client:
            async def mock_post(*args, **kwargs):
                nonlocal failure_count
                failure_count += 1
                
                if failure_count <= max_failures:
                    # Simuler différentes types d'erreurs réseau
                    errors = [
                        Exception("Connection timeout"),
                        Exception("Connection refused"),
                        Exception("DNS resolution failed"),
                        Exception("Network unreachable")
                    ]
                    raise errors[failure_count - 1]
                else:
                    # Succès après les échecs
                    response = Mock()
                    response.status_code = 200
                    response.json.return_value = {"response": "Recovered response", "done": True}
                    return response
            
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            # Créer les composants
            cache = CacheManager(max_size=100, ttl_seconds=300)
            llm_client = LLMClient()
            pipeline = VenturePipeline(cache_manager=cache, llm_client=llm_client)
            
            # Tenter l'opération qui devrait récupérer
            run_id = pipeline.create_run()
            pipeline.add_idea(run_id, {"name": "Resilience Test", "description": "Test"})
            
            start_time = time.time()
            result = pipeline.run_pipeline(run_id)
            end_time = time.time()
            
            # Vérifications
            assert result["status"] == "completed"
            assert failure_count > max_failures  # Les retries ont eu lieu
            assert end_time - start_time > 5  # Temps de retry significatif
            
            # Vérifier que les erreurs ont été enregistrées
            assert failure_count == max_failures + 1  # Échecs + succès
            
            print(f"✅ Network recovery: {failure_count-1} failures, recovered in {end_time-start_time:.2f}s")
    
    def test_resource_exhaustion_recovery(self, resilience_config):
        """Test de récupération après épuisement des ressources"""
        resource_exhausted = False
        
        # Mock LLM avec épuisement de ressources
        with patch('app.core.llm.httpx.AsyncClient') as mock_client:
            async def mock_post(*args, **kwargs):
                nonlocal resource_exhausted
                
                if not resource_exhausted:
                    resource_exhausted = True
                    raise Exception("Resource temporarily unavailable (503)")
                else:
                    # Récupération après un délai
                    await asyncio.sleep(0.1)  # Simuler la récupération
                    response = Mock()
                    response.status_code = 200
                    response.json.return_value = {"response": "Resource recovered", "done": True}
                    return response
            
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            # Créer les composants
            cache = CacheManager(max_size=100, ttl_seconds=300)
            llm_client = LLMClient()
            pipeline = VenturePipeline(cache_manager=cache, llm_client=llm_client)
            
            # Première tentative (échec)
            run_id1 = pipeline.create_run()
            pipeline.add_idea(run_id1, {"name": "Resource Test 1", "description": "Test"})
            
            try:
                result1 = pipeline.run_pipeline(run_id1)
                # Si ça réussit, c'est que la récupération a fonctionné
                assert result1["status"] == "completed"
            except Exception:
                # Si ça échoue, réessayer avec un nouveau run
                pass
            
            # Deuxième tentative (devrait réussir)
            run_id2 = pipeline.create_run()
            pipeline.add_idea(run_id2, {"name": "Resource Test 2", "description": "Test"})
            
            result2 = pipeline.run_pipeline(run_id2)
            assert result2["status"] == "completed"
            
            print("✅ Resource exhaustion recovery: Successfully recovered after resource exhaustion")
    
    def test_partial_failure_handling(self, resilience_config):
        """Test de gestion d'échecs partiels"""
        # Mock LLM avec succès/échec partiels
        with patch('app.core.llm.httpx.AsyncClient') as mock_client:
            call_count = 0
            
            async def mock_post(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                
                # 30% de chance d'échec
                if random.random() < 0.3:
                    raise Exception("Partial failure")
                else:
                    response = Mock()
                    response.status_code = 200
                    response.json.return_value = {"response": f"Partial success {call_count}", "done": True}
                    return response
            
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            # Exécuter plusieurs opérations
            successful_operations = 0
            failed_operations = 0
            total_operations = 20
            
            for i in range(total_operations):
                cache = CacheManager(max_size=50, ttl_seconds=300)
                llm_client = LLMClient()
                pipeline = VenturePipeline(cache_manager=cache, llm_client=llm_client)
                
                try:
                    run_id = pipeline.create_run()
                    pipeline.add_idea(run_id, {"name": f"Partial Test {i}", "description": "Test"})
                    result = pipeline.run_pipeline(run_id)
                    
                    if result["status"] == "completed":
                        successful_operations += 1
                    else:
                        failed_operations += 1
                        
                except Exception:
                    failed_operations += 1
                
                # Nettoyer
                del cache, llm_client, pipeline
            
            # Vérifications
            success_rate = successful_operations / total_operations
            assert success_rate > 0.6  # Au moins 60% de succès malgré les échecs partiels
            assert successful_operations + failed_operations == total_operations
            
            print(f"✅ Partial failure handling: {successful_operations}/{total_operations} successful ({success_rate:.1%})")
    
    def test_cascade_failure_recovery(self, resilience_config):
        """Test de récupération après défaillances en cascade"""
        failure_stages = [3, 2, 1]  # Échecs puis succès
        current_stage = 0
        
        # Mock LLM avec défaillances en cascade
        with patch('app.core.llm.httpx.AsyncClient') as mock_client:
            async def mock_post(*args, **kwargs):
                nonlocal current_stage
                
                if current_stage < len(failure_stages):
                    failures_remaining = failure_stages[current_stage]
                    failure_stages[current_stage] = failures_remaining - 1
                    
                    if failures_remaining > 0:
                        raise Exception(f"Cascade failure stage {current_stage}")
                    else:
                        current_stage += 1
                        raise Exception(f"Moving to stage {current_stage}")
                else:
                    # Succès après toutes les étapes
                    response = Mock()
                    response.status_code = 200
                    response.json.return_value = {"response": "Cascade recovered", "done": True}
                    return response
            
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            # Créer les composants
            cache = CacheManager(max_size=100, ttl_seconds=300)
            llm_client = LLMClient()
            pipeline = VenturePipeline(cache_manager=cache, llm_client=llm_client)
            
            # Exécuter avec récupération en cascade
            run_id = pipeline.create_run()
            pipeline.add_idea(run_id, {"name": "Cascade Test", "description": "Test"})
            
            start_time = time.time()
            result = pipeline.run_pipeline(run_id)
            end_time = time.time()
            
            # Vérifications
            assert result["status"] == "completed"
            assert current_stage == len(failure_stages)  # Toutes les étapes traversées
            assert end_time - start_time > 10  # Temps de récupération significatif
            
            print(f"✅ Cascade failure recovery: {len(failure_stages)} stages, recovered in {end_time-start_time:.2f}s")
    
    def test_memory_pressure_handling(self, resilience_config):
        """Test de gestion sous pression mémoire"""
        import psutil
        import gc
        
        # Mock LLM
        with patch('app.core.llm.httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "Memory pressure test", "done": True}
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            process = psutil.Process()
            initial_memory = process.memory_info().rss
            
            # Créer beaucoup d'objets pour simuler la pression mémoire
            large_objects = []
            
            def memory_intensive_operation(index):
                try:
                    # Créer un objet volumineux
                    large_data = "x" * (1024 * 1024)  # 1MB de données
                    large_objects.append(large_data)
                    
                    # Exécuter l'opération normale
                    cache = CacheManager(max_size=50, ttl_seconds=300)
                    llm_client = LLMClient()
                    pipeline = VenturePipeline(cache_manager=cache, llm_client=llm_client)
                    
                    run_id = pipeline.create_run()
                    pipeline.add_idea(run_id, {"name": f"Memory Test {index}", "description": large_data[:100]})
                    result = pipeline.run_pipeline(run_id)
                    
                    return result["status"] == "completed"
                    
                except MemoryError:
                    return False
                finally:
                    # Nettoyer
                    gc.collect()
            
            # Exécuter sous pression mémoire
            successful_ops = 0
            total_ops = 20
            
            for i in range(total_ops):
                success = memory_intensive_operation(i)
                if success:
                    successful_ops += 1
                
                # Vérifier la mémoire actuelle
                current_memory = process.memory_info().rss
                memory_increase = current_memory - initial_memory
                
                # Si la mémoire devient trop élevée, nettoyer
                if memory_increase > 500 * 1024 * 1024:  # 500MB
                    large_objects.clear()
                    gc.collect()
            
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # Vérifications
            success_rate = successful_ops / total_ops
            assert success_rate > 0.7  # Au moins 70% de succès sous pression
            assert memory_increase < 300 * 1024 * 1024  # Moins de 300MB d'augmentation finale
            
            print(f"✅ Memory pressure handling: {successful_ops}/{total_ops} successful, memory increase: {memory_increase/1024/1024:.1f}MB")
    
    def test_concurrent_failure_isolation(self, resilience_config):
        """Test d'isolation des défaillances concurrentes"""
        failure_rate = 0.3  # 30% des opérations échouent
        
        # Mock LLM avec échecs aléatoires
        with patch('app.core.llm.httpx.AsyncClient') as mock_client:
            async def mock_post(*args, **kwargs):
                if random.random() < failure_rate:
                    raise Exception("Random concurrent failure")
                else:
                    response = Mock()
                    response.status_code = 200
                    response.json.return_value = {"response": "Concurrent success", "done": True}
                    return response
            
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            # Exécuter des opérations concurrentes avec isolation
            def isolated_operation(operation_id):
                # Chaque opération a ses propres composants
                cache = CacheManager(max_size=20, ttl_seconds=300)
                llm_client = LLMClient()
                pipeline = VenturePipeline(cache_manager=cache, llm_client=llm_client)
                
                try:
                    run_id = pipeline.create_run()
                    pipeline.add_idea(run_id, {"name": f"Isolated {operation_id}", "description": "Test"})
                    result = pipeline.run_pipeline(run_id)
                    
                    return {
                        "operation_id": operation_id,
                        "success": result["status"] == "completed",
                        "error": None
                    }
                    
                except Exception as e:
                    return {
                        "operation_id": operation_id,
                        "success": False,
                        "error": str(e)
                    }
                finally:
                    # Nettoyer pour l'isolation
                    del cache, llm_client, pipeline
            
            # Exécuter 20 opérations concurrentes
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(isolated_operation, i) for i in range(20)]
                results = [future.result() for future in as_completed(futures)]
            
            # Analyser les résultats
            successful = [r for r in results if r["success"]]
            failed = [r for r in results if not r["success"]]
            
            success_rate = len(successful) / len(results)
            
            # Vérifications
            assert success_rate > 0.6  # Au moins 60% de succès
            assert len(results) == 20  # Toutes les opérations ont été tentées
            
            # Vérifier que les échecs sont isolés (pas de cascade)
            error_types = [r["error"] for r in failed if r["error"]]
            unique_errors = set(error_types)
            
            # Les erreurs devraient être similaires mais isolées
            assert len(unique_errors) <= 3  # Pas trop de types d'erreurs différents
            
            print(f"✅ Concurrent failure isolation: {len(successful)}/{len(results)} successful, {len(unique_errors)} error types")
    
    def test_graceful_degradation(self, resilience_config):
        """Test de dégradation gracieuse"""
        degradation_levels = [
            {"response": "Full response", "quality": "high"},
            {"response": "Simplified response", "quality": "medium"},
            {"response": "Basic response", "quality": "low"},
            {"response": "Fallback response", "quality": "minimal"}
        ]
        current_level = 0
        
        # Mock LLM avec dégradation gracieuse
        with patch('app.core.llm.httpx.AsyncClient') as mock_client:
            async def mock_post(*args, **kwargs):
                nonlocal current_level
                
                if current_level < len(degradation_levels):
                    level_data = degradation_levels[current_level]
                    current_level += 1
                    
                    response = Mock()
                    response.status_code = 200
                    response.json.return_value = {
                        "response": level_data["response"],
                        "quality": level_data["quality"],
                        "done": True
                    }
                    return response
                else:
                    raise Exception("Complete failure")
            
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            # Créer les composants
            cache = CacheManager(max_size=100, ttl_seconds=300)
            llm_client = LLMClient()
            pipeline = VenturePipeline(cache_manager=cache, llm_client=llm_client)
            
            # Exécuter plusieurs opérations pour tester la dégradation
            results = []
            
            for i in range(len(degradation_levels)):
                run_id = pipeline.create_run()
                pipeline.add_idea(run_id, {"name": f"Degradation Test {i}", "description": "Test"})
                
                try:
                    result = pipeline.run_pipeline(run_id)
                    results.append({
                        "attempt": i,
                        "success": result["status"] == "completed",
                        "data": result
                    })
                except Exception as e:
                    results.append({
                        "attempt": i,
                        "success": False,
                        "error": str(e)
                    })
            
            # Vérifications
            successful_attempts = [r for r in results if r["success"]]
            
            # Au moins les premières tentatives devraient réussir
            assert len(successful_attempts) >= 2  # Au moins 2 niveaux de dégradation
            
            # Vérifier la qualité de dégradation
            qualities = [r["data"].get("quality", "unknown") for r in successful_attempts if "data" in r]
            expected_qualities = ["high", "medium", "low", "minimal"][:len(qualities)]
            
            for i, quality in enumerate(qualities):
                assert quality == expected_qualities[i]
            
            print(f"✅ Graceful degradation: {len(successful_attempts)}/{len(results)} successful, quality levels: {qualities}")
    
    def test_circuit_breaker_pattern(self, resilience_config):
        """Test du pattern circuit breaker"""
        circuit_state = "closed"  # closed, open, half-open
        failure_count = 0
        failure_threshold = 3
        recovery_timeout = 2  # secondes
        
        # Mock LLM avec circuit breaker
        with patch('app.core.llm.httpx.AsyncClient') as mock_client:
            async def mock_post(*args, **kwargs):
                nonlocal circuit_state, failure_count
                
                if circuit_state == "open":
                    # Vérifier si on peut passer en half-open
                    if time.time() - last_failure_time > recovery_timeout:
                        circuit_state = "half-open"
                    else:
                        raise Exception("Circuit breaker is open")
                
                if circuit_state == "half-open":
                    # Une seule tentative en half-open
                    circuit_state = "closed"  # Si succès, sinon retourne à open
                    failure_count = 0
                
                # Simuler des échecs
                if random.random() < 0.7:  # 70% d'échecs
                    failure_count += 1
                    last_failure_time = time.time()
                    
                    if failure_count >= failure_threshold:
                        circuit_state = "open"
                    
                    raise Exception(f"Circuit breaker failure (count: {failure_count})")
                else:
                    # Succès
                    failure_count = 0
                    circuit_state = "closed"
                    
                    response = Mock()
                    response.status_code = 200
                    response.json.return_value = {"response": "Circuit breaker success", "done": True}
                    return response
            
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            # Initialiser
            last_failure_time = time.time()
            
            # Créer les composants
            cache = CacheManager(max_size=100, ttl_seconds=300)
            llm_client = LLMClient()
            pipeline = VenturePipeline(cache_manager=cache, llm_client=llm_client)
            
            # Exécuter des opérations pour tester le circuit breaker
            results = []
            
            for i in range(15):
                try:
                    run_id = pipeline.create_run()
                    pipeline.add_idea(run_id, {"name": f"Circuit Test {i}", "description": "Test"})
                    result = pipeline.run_pipeline(run_id)
                    
                    results.append({
                        "attempt": i,
                        "success": True,
                        "circuit_state": circuit_state
                    })
                    
                except Exception as e:
                    results.append({
                        "attempt": i,
                        "success": False,
                        "circuit_state": circuit_state,
                        "error": str(e)
                    })
                
                # Petite pause entre les tentatives
                time.sleep(0.5)
            
            # Analyser les résultats
            successful = [r for r in results if r["success"]]
            circuit_states = [r["circuit_state"] for r in results]
            
            # Vérifier que le circuit breaker a fonctionné
            assert "open" in circuit_states  # Le circuit s'est ouvert
            assert len(successful) > 0  # Il y a eu des succès après récupération
            
            # Vérifier que les échecs sont groupés (pattern de circuit breaker)
            consecutive_failures = 0
            max_consecutive_failures = 0
            
            for result in results:
                if not result["success"]:
                    consecutive_failures += 1
                    max_consecutive_failures = max(max_consecutive_failures, consecutive_failures)
                else:
                    consecutive_failures = 0
            
            assert max_consecutive_failures >= failure_threshold  # Le pattern de circuit breaker
            
            print(f"✅ Circuit breaker pattern: {len(successful)}/{len(results)} successful, max consecutive failures: {max_consecutive_failures}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
