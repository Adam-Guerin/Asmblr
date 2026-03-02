"""
Tests complexes et d'intégration pour Asmblr
Tests de bout en bout, performance, charge et résilience
"""

import pytest
import asyncio
import time
import tempfile
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.core.config import Settings
from app.core.pipeline import VenturePipeline
from app.core.llm import LLMClient
from app.core.cache import ArtifactCache
from app.monitoring.prometheus_metrics import AsmblrMetrics
from app.monitoring.structured_logger import StructuredLogger, TraceContext


class TestComplexIntegration:
    """Tests d'intégration complexes pour Asmblr"""
    
    @pytest.fixture
    def test_environment(self):
        """Fixture pour l'environnement de test complexe"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Configuration de test
            test_config = {
                "OLLAMA_BASE_URL": "http://localhost:11434",
                "GENERAL_MODEL": "llama3.1:8b",
                "DEFAULT_N_IDEAS": "5",
                "FAST_MODE": "true",
                "REDIS_URL": "redis://localhost:6379/1",
                "RUNS_DIR": temp_dir,
                "CACHE_DIR": temp_dir
            }
            
            with patch.dict('os.environ', test_config):
                yield {
                    "temp_dir": temp_dir,
                    "config": Settings()
                }
    
    def test_full_pipeline_integration(self, test_environment):
        """Test d'intégration complète de la pipeline"""
        config = test_environment["config"]
        temp_dir = test_environment["temp_dir"]
        
        # Initialiser tous les composants
        cache = ArtifactCache(max_size=100, ttl_seconds=300)
        metrics = AsmblrMetrics()
        logger = StructuredLogger("test-asmblr", "test")
        
        # Mock LLM client
        with patch('app.core.llm.httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": "Test response",
                "model": "llama3.1:8b",
                "done": True
            }
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            llm_client = LLMClient("http://localhost:11434", "llama3.1:8b")
            
            # Créer la pipeline
            pipeline = VenturePipeline(config)
            
            # Configurer le cache et le LLM client si nécessaire
            if hasattr(pipeline, 'cache_manager'):
                pipeline.cache_manager = cache
            if hasattr(pipeline, 'llm_client'):
                pipeline.llm_client = llm_client
            if hasattr(pipeline, 'metrics'):
                pipeline.metrics = metrics
            
            # Exécuter une pipeline complète avec tracing
            with TraceContext("test_full_pipeline", logger.logger.category, logger):
                # Créer un run
                run_id = pipeline.create_run()
                
                # Ajouter des données de test
                test_ideas = [
                    {"name": "Test Idea 1", "description": "Test description 1"},
                    {"name": "Test Idea 2", "description": "Test description 2"}
                ]
                
                for idea in test_ideas:
                    pipeline.add_idea(run_id, idea)
                
                # Exécuter la pipeline
                result = pipeline.run_pipeline(run_id)
                
                # Vérifications
                assert result["status"] == "completed"
                assert len(result["ideas"]) == 2
                assert pipeline.get_run_status(run_id) == "completed"
                
                # Vérifier les métriques
                metrics_summary = metrics.get_metrics_summary()
                assert metrics_summary["registered_metrics"] > 0
                
                # Vérifier le cache
                cached_ideas = cache.get(f"run_{run_id}_ideas")
                assert cached_ideas is not None
                assert len(cached_ideas) == 2
    
    def test_concurrent_pipeline_execution(self, test_environment):
        """Test d'exécution concurrente de pipelines"""
        config = test_environment["config"]
        
        # Mock des dépendances
        with patch('app.core.llm.httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "Test", "done": True}
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Créer plusieurs pipelines
            pipelines = []
            for i in range(5):
                cache = ArtifactCache(max_size=50, ttl_seconds=300)
                llm_client = LLMClient("http://localhost:11434", "llama3.1:8b")
                pipeline = VenturePipeline(config)
            
            # Configurer les composants si nécessaire
            if hasattr(pipeline, 'cache_manager'):
                pipeline.cache_manager = cache
            if hasattr(pipeline, 'llm_client'):
                pipeline.llm_client = llm_client
                pipelines.append(pipeline)
            
            # Exécuter les pipelines en parallèle
            async def run_pipeline_async(pipeline, index):
                run_id = pipeline.create_run()
                pipeline.add_idea(run_id, {"name": f"Idea {index}", "description": f"Description {index}"})
                return pipeline.run_pipeline(run_id)
            
            # Exécuter toutes les pipelines
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                tasks = [run_pipeline_async(pipeline, i) for i, pipeline in enumerate(pipelines)]
                results = loop.run_until_complete(asyncio.gather(*tasks))
                
                # Vérifications
                assert len(results) == 5
                for result in results:
                    assert result["status"] == "completed"
                    assert "ideas" in result
                
            finally:
                loop.close()
    
    def test_error_recovery_and_resilience(self, test_environment):
        """Test de récupération d'erreur et résilience"""
        config = test_environment["config"]
        
        # Mock LLM client avec des erreurs
        with patch('app.core.llm.httpx.AsyncClient') as mock_client:
            # Simuler des erreurs intermittentes
            call_count = 0
            
            async def mock_post(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    raise Exception("Network error")
                else:
                    response = Mock()
                    response.status_code = 200
                    response.json.return_value = {"response": "Success", "done": True}
                    return response
            
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            # Créer la pipeline avec retry
            cache = ArtifactCache(max_size=100, ttl_seconds=300)
            llm_client = LLMClient("http://localhost:11434", "llama3.1:8b")
            pipeline = VenturePipeline(config)
            
            # Configurer les composants si nécessaire
            if hasattr(pipeline, 'cache_manager'):
                pipeline.cache_manager = cache
            if hasattr(pipeline, 'llm_client'):
                pipeline.llm_client = llm_client
            
            # Exécuter avec retry
            run_id = pipeline.create_run()
            pipeline.add_idea(run_id, {"name": "Test", "description": "Test"})
            
            # Devrait réussir après les retries
            result = pipeline.run_pipeline(run_id)
            assert result["status"] == "completed"
            assert call_count > 2  # Vérifier que les retries ont eu lieu
    
    def test_performance_under_load(self, test_environment):
        """Test de performance sous charge"""
        config = test_environment["config"]
        
        # Mock des dépendances pour performance
        with patch('app.core.llm.httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "Fast response", "done": True}
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Mesurer le temps de réponse
            start_time = time.time()
            
            # Exécuter 100 opérations en parallèle
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                
                for i in range(100):
                    def run_operation(index):
                        cache = ArtifactCache(max_size=50, ttl_seconds=300)
                        llm_client = LLMClient("http://localhost:11434", "llama3.1:8b")
                        pipeline = VenturePipeline(config)
            
                        # Configurer les composants si nécessaire
                        if hasattr(pipeline, 'cache_manager'):
                            pipeline.cache_manager = cache
                        if hasattr(pipeline, 'llm_client'):
                            pipeline.llm_client = llm_client
                        
                        run_id = pipeline.create_run()
                        pipeline.add_idea(run_id, {"name": f"Idea {index}", "description": f"Desc {index}"})
                        result = pipeline.run_pipeline(run_id)
                        return result
                    
                    future = executor.submit(run_operation, i)
                    futures.append(future)
                
                # Attendre toutes les opérations
                results = [future.result() for future in as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Vérifications
            assert len(results) == 100
            assert all(result["status"] == "completed" for result in results)
            assert total_time < 30  # Devrait prendre moins de 30 secondes
            assert len(results) / total_time > 3  # Au moins 3 opérations par seconde
    
    def test_memory_usage_under_load(self, test_environment):
        """Test de l'utilisation mémoire sous charge"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Mock des dépendances
        with patch('app.core.llm.httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "Test", "done": True}
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Exécuter beaucoup d'opérations
            for i in range(50):
                cache = ArtifactCache(max_size=100, ttl_seconds=300)
                llm_client = LLMClient("http://localhost:11434", "llama3.1:8b")
                pipeline = VenturePipeline(config)
            
            # Configurer les composants si nécessaire
            if hasattr(pipeline, 'cache_manager'):
                pipeline.cache_manager = cache
            if hasattr(pipeline, 'llm_client'):
                pipeline.llm_client = llm_client
                
                run_id = pipeline.create_run()
                pipeline.add_idea(run_id, {"name": f"Idea {i}", "description": f"Description {i}"})
                pipeline.run_pipeline(run_id)
                
                # Nettoyer manuellement
                del cache
                del llm_client
                del pipeline
                
                if i % 10 == 0:
                    # Forcer le garbage collection
                    import gc
                    gc.collect()
            
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # La mémoire ne devrait pas augmenter de plus de 100MB
            assert memory_increase < 100 * 1024 * 1024  # 100MB
    
    def test_data_consistency_under_concurrent_access(self, test_environment):
        """Test de la consistance des données sous accès concurrent"""
        config = test_environment["config"]
        
        # Cache partagé
        shared_cache = ArtifactCache(max_size=1000, ttl_seconds=600)
        
        # Mock LLM client
        with patch('app.core.llm.httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "Test", "done": True}
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Fonction pour les threads
            def worker_thread(thread_id):
                results = []
                for i in range(10):
                    llm_client = LLMClient("http://localhost:11434", "llama3.1:8b")
                    pipeline = VenturePipeline(cache_manager=shared_cache, llm_client=llm_client)
                    
                    run_id = pipeline.create_run()
                    idea = {"name": f"Idea {thread_id}-{i}", "description": f"Description {thread_id}-{i}"}
                    pipeline.add_idea(run_id, idea)
                    
                    result = pipeline.run_pipeline(run_id)
                    results.append((run_id, result))
                
                return results
            
            # Exécuter 5 threads en parallèle
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(worker_thread, i) for i in range(5)]
                all_results = [future.result() for future in as_completed(futures)]
            
            # Aplatener les résultats
            flat_results = [item for sublist in all_results for item in sublist]
            
            # Vérifications
            assert len(flat_results) == 50  # 5 threads * 10 opérations
            
            # Vérifier qu'il n'y a pas de doublons de run_id
            run_ids = [result[0] for result in flat_results]
            assert len(set(run_ids)) == len(run_ids)  # Pas de doublons
            
            # Vérifier que toutes les opérations ont réussi
            assert all(result[1]["status"] == "completed" for result in flat_results)
    
    def test_cache_performance_and_consistency(self, test_environment):
        """Test de performance et consistance du cache"""
        cache = ArtifactCache(max_size=1000, ttl_seconds=300)
        
        # Test de performance d'écriture
        start_time = time.time()
        for i in range(1000):
            cache.set(f"key_{i}", f"value_{i}")
        write_time = time.time() - start_time
        
        # Test de performance de lecture
        start_time = time.time()
        for i in range(1000):
            value = cache.get(f"key_{i}")
            assert value == f"value_{i}"
        read_time = time.time() - start_time
        
        # Vérifications de performance
        assert write_time < 1.0  # 1000 écritures en moins de 1 seconde
        assert read_time < 0.5  # 1000 lectures en moins de 0.5 seconde
        
        # Test de consistance sous accès concurrent
        def cache_worker(worker_id):
            for i in range(100):
                key = f"concurrent_{worker_id}_{i}"
                cache.set(key, f"value_{worker_id}_{i}")
                value = cache.get(key)
                assert value == f"value_{worker_id}_{i}"
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(cache_worker, i) for i in range(10)]
            for future in as_completed(futures):
                future.result()  # Lever les exceptions si any
        
        # Vérifier que le cache a bien fonctionné
        assert cache.size() <= 1000  # Respect de la taille maximale
    
    def test_metrics_accuracy_under_load(self, test_environment):
        """Test de l'exactitude des métriques sous charge"""
        metrics = AsmblrMetrics()
        
        # Simuler une charge importante
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            
            for i in range(200):
                def record_metrics(index):
                    # Enregistrer différents types de métriques
                    metrics.record_request("GET", f"/api/test/{index}", 200, 0.1)
                    metrics.business_metrics.record_pipeline_start("test")
                    metrics.business_metrics.record_idea_generation("ai", "high", 1)
                    metrics.business_metrics.record_llm_request("test_model", "generation", 0.5, "success", 50)
                
                future = executor.submit(record_metrics, i)
                futures.append(future)
            
            # Attendre toutes les opérations
            for future in as_completed(futures):
                future.result()
        
        # Vérifier les métriques
        summary = metrics.get_metrics_summary()
        
        # Les métriques devraient refléter toutes les opérations
        assert summary["registered_metrics"] > 0
        
        # Générer les métriques et vérifier le format
        metrics_output = metrics.generate_metrics()
        assert isinstance(metrics_output, str)
        assert "asmblr_requests_total" in metrics_output
        assert "200.0" in metrics_output  # 200 requêtes avec status 200
        
        # Vérifier les compteurs
        assert "asmblr_pipeline_runs_total" in metrics_output
        assert "asmblr_ideas_generated_total" in metrics_output
        assert "asmblr_llm_requests_total" in metrics_output


class TestEndToEndScenarios:
    """Tests de bout en bout pour des scénarios réels"""
    
    def test_venture_creation_workflow(self):
        """Test complet du workflow de création de venture"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Configuration
            test_config = {
                "RUNS_DIR": temp_dir,
                "CACHE_DIR": temp_dir,
                "DEFAULT_N_IDEAS": "3",
                "FAST_MODE": "true"
            }
            
            with patch.dict('os.environ', test_config):
                # Mock LLM
                with patch('app.core.llm.httpx.AsyncClient') as mock_client:
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "response": "Generated venture content",
                        "done": True
                    }
                    mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
                    
                    # Initialiser les composants
                    settings = Settings()
                    cache = ArtifactCache(max_size=100, ttl_seconds=300)
                    llm_client = LLMClient("http://localhost:11434", "llama3.1:8b")
                    metrics = AsmblrMetrics()
                    logger = StructuredLogger("test-venture", "test")
                    
                    # Créer la pipeline
                    pipeline = VenturePipeline(
                        cache_manager=cache,
                        llm_client=llm_client,
                        metrics=metrics
                    )
                    
                    # Workflow complet
                    with TraceContext("venture_creation", LogCategory.BUSINESS, logger):
                        # 1. Créer le run
                        run_id = pipeline.create_run()
                        logger.business(f"Run créé: {run_id}")
                        
                        # 2. Ajouter les données de marché
                        market_data = {
                            "target_market": "Tech startups",
                            "pain_points": ["Inefficiency", "High costs"],
                            "competitors": ["Competitor A", "Competitor B"]
                        }
                        pipeline.set_market_data(run_id, market_data)
                        logger.business("Données de marché ajoutées")
                        
                        # 3. Générer les idées
                        ideas = pipeline.generate_ideas(run_id)
                        assert len(ideas) >= 3
                        logger.business(f"{len(ideas)} idées générées")
                        
                        # 4. Évaluer les idées
                        assessments = pipeline.evaluate_ideas(run_id)
                        assert len(assessments) == len(ideas)
                        logger.business("Idées évaluées")
                        
                        # 5. Sélectionner les meilleures idées
                        selected = pipeline.select_best_ideas(run_id, count=2)
                        assert len(selected) == 2
                        logger.business(f"{len(selected)} idées sélectionnées")
                        
                        # 6. Générer le MVP
                        mvp_result = pipeline.generate_mvp(run_id, selected[0])
                        assert mvp_result["status"] == "success"
                        logger.business("MVP généré avec succès")
                        
                        # 7. Finaliser le run
                        final_result = pipeline.finalize_run(run_id)
                        assert final_result["status"] == "completed"
                        
                        # Vérifications finales
                        run_data = pipeline.get_run_data(run_id)
                        assert run_data["status"] == "completed"
                        assert "mvp" in run_data
                        assert len(run_data["ideas"]) >= 3
                        
                        # Vérifier les métriques
                        metrics_summary = metrics.get_metrics_summary()
                        assert metrics_summary["registered_metrics"] > 0
                        
                        logger.business("Workflow de création de venture complété")
    
    def test_error_handling_and_recovery(self):
        """Test de gestion d'erreurs et récupération"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_config = {
                "RUNS_DIR": temp_dir,
                "CACHE_DIR": temp_dir,
                "DEFAULT_N_IDEAS": "2"
            }
            
            with patch.dict('os.environ', test_config):
                # Mock LLM avec des erreurs
                with patch('app.core.llm.httpx.AsyncClient') as mock_client:
                    call_count = 0
                    
                    async def mock_post(*args, **kwargs):
                        nonlocal call_count
                        call_count += 1
                        if call_count <= 3:
                            raise Exception("Simulated network error")
                        else:
                            response = Mock()
                            response.status_code = 200
                            response.json.return_value = {"response": "Success after retry", "done": True}
                            return response
                    
                    mock_client.return_value.__aenter__.return_value.post = mock_post
                    
                    # Initialiser
                    cache = ArtifactCache(max_size=100, ttl_seconds=300)
                    llm_client = LLMClient("http://localhost:11434", "llama3.1:8b")
                    metrics = AsmblrMetrics()
                    logger = StructuredLogger("test-error", "test")
                    
                    pipeline = VenturePipeline(
                        cache_manager=cache,
                        llm_client=llm_client,
                        metrics=metrics
                    )
                    
                    # Tenter une opération qui devrait échouer puis réussir
                    run_id = pipeline.create_run()
                    pipeline.add_idea(run_id, {"name": "Test", "description": "Test"})
                    
                    # Devrait réussir après les retries
                    result = pipeline.run_pipeline(run_id)
                    assert result["status"] == "completed"
                    assert call_count > 3  # Vérifier que les retries ont eu lieu
                    
                    # Vérifier que les erreurs ont été enregistrées
                    metrics_output = metrics.generate_metrics()
                    assert "asmblr_errors_total" in metrics_output
                    
                    logger.error("Test de récupération d'erreur réussi")
    
    def test_performance_benchmark(self):
        """Benchmark de performance"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Mesurer les ressources initiales
        initial_memory = process.memory_info().rss
        initial_cpu_time = process.cpu_times()
        
        # Mock pour performance
        with patch('app.core.llm.httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "Fast response", "done": True}
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Exécuter un benchmark
            start_time = time.time()
            operations_count = 50
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                
                for i in range(operations_count):
                    def benchmark_operation(index):
                        cache = ArtifactCache(max_size=50, ttl_seconds=300)
                        llm_client = LLMClient("http://localhost:11434", "llama3.1:8b")
                        metrics = AsmblrMetrics()
                        
                        pipeline = VenturePipeline(
                            cache_manager=cache,
                            llm_client=llm_client,
                            metrics=metrics
                        )
                        
                        run_id = pipeline.create_run()
                        pipeline.add_idea(run_id, {"name": f"Benchmark {index}", "description": "Test"})
                        result = pipeline.run_pipeline(run_id)
                        
                        return {
                            "result": result,
                            "cache_size": cache.size(),
                            "metrics_count": len(metrics.registry.metrics)
                        }
                    
                    future = executor.submit(benchmark_operation, i)
                    futures.append(future)
                
                # Collecter les résultats
                results = [future.result() for future in as_completed(futures)]
            
            end_time = time.time()
            
            # Mesurer les ressources finales
            final_memory = process.memory_info().rss
            final_cpu_time = process.cpu_times()
            
            # Calculer les métriques
            total_time = end_time - start_time
            operations_per_second = operations_count / total_time
            memory_increase = final_memory - initial_memory
            cpu_time_used = (final_cpu_time.user - initial_cpu_time.user) + (final_cpu_time.system - initial_cpu_time.system)
            
            # Vérifications
            assert len(results) == operations_count
            assert all(result["result"]["status"] == "completed" for result in results)
            assert operations_per_second > 2  # Au moins 2 opérations par seconde
            assert memory_increase < 50 * 1024 * 1024  # Moins de 50MB de mémoire supplémentaire
            
            # Afficher les résultats du benchmark
            print(f"\n📊 Benchmark Results:")
            print(f"  Operations: {operations_count}")
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Operations/sec: {operations_per_second:.2f}")
            print(f"  Memory increase: {memory_increase / 1024 / 1024:.2f}MB")
            print(f"  CPU time used: {cpu_time_used:.2f}s")
            print(f"  Avg cache size: {sum(r['cache_size'] for r in results) / len(results):.1f}")
            print(f"  Avg metrics count: {sum(r['metrics_count'] for r in results) / len(results):.1f}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
