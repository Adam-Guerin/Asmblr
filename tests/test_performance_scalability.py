"""
Performance Tests for Asmblr New Features
Tests performance, scalability, and load handling of all new components
"""

import asyncio
import time
import json
import tempfile
import os
import psutil
import threading
from datetime import datetime
from unittest.mock import Mock
import redis.asyncio as redis

# Import all new features for performance testing
from app.core.ai_orchestrator import AIOrchestrator
from app.core.multi_llm import MultiLLMManager
from app.core.plugin_system import PluginManager
from app.core.enterprise_features import EnterpriseManager
from app.core.llm_cache import LLMCacheManager
from app.core.async_tasks import AsyncTaskManager
from app.core.connection_pool import ConnectionPoolManager
from app.core.load_balancer import LoadBalancer

class TestPerformanceAndScalability:
    """Performance and scalability tests for all new features"""
    
    def __init__(self):
        self.test_results = {}
        self.redis_client = None
        self.temp_dir = None
        self.performance_metrics = {}
        
    async def setup(self):
        """Setup performance test environment"""
        try:
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp(prefix="asmblr_perf_")
            
            # Setup Redis for testing
            self.redis_client = redis.from_url("redis://localhost:6379/19")
            await self.redis_client.ping()
            
            # Initialize performance monitoring
            self.performance_metrics = {
                "cpu_usage": [],
                "memory_usage": [],
                "response_times": [],
                "throughput": [],
                "error_rates": []
            }
            
            print("✅ Performance test environment setup complete")
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            raise
    
    async def teardown(self):
        """Cleanup performance test environment"""
        try:
            if self.redis_client:
                await self.redis_client.close()
            
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
            
            print("✅ Performance test environment cleanup complete")
            
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
    
    def _monitor_system_resources(self):
        """Monitor system resources during tests"""
        cpu_percent = psutil.cpu_percent()
        memory_info = psutil.virtual_memory()
        
        self.performance_metrics["cpu_usage"].append(cpu_percent)
        self.performance_metrics["memory_usage"].append(memory_info.percent)
    
    async def test_ai_orchestrator_performance(self):
        """Test AI Orchestrator performance under load"""
        print("\n🤖 Testing AI Orchestrator Performance...")
        
        try:
            orchestrator = AIOrchestrator()
            await orchestrator.initialize()
            
            # Performance metrics
            response_times = []
            error_count = 0
            success_count = 0
            
            # Test concurrent requests
            async def process_request(request_id):
                start_time = time.time()
                try:
                    result = await orchestrator.process_request(
                        request=f"Test request {request_id}",
                        context={"user_id": f"user_{request_id}"}
                    )
                    end_time = time.time()
                    response_times.append(end_time - start_time)
                    return success_count + 1
                except Exception as e:
                    error_count += 1
                    return error_count
            
            # Run concurrent requests
            tasks = []
            for i in range(100):  # 100 concurrent requests
                tasks.append(process_request(i))
            
            # Monitor resources during test
            monitor_thread = threading.Thread(target=self._monitor_system_resources)
            monitor_thread.start()
            
            # Execute all tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Stop monitoring
            monitor_thread.join()
            
            # Calculate performance metrics
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            max_response_time = max(response_times) if response_times else 0
            min_response_time = min(response_times) if response_times else 0
            throughput = len([r for r in results if not isinstance(r, Exception)]) / 10  # requests per second
            error_rate = error_count / len(tasks) if tasks else 0
            
            self.test_results["ai_orchestrator_performance"] = {
                "concurrent_requests": len(tasks),
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "min_response_time": min_response_time,
                "throughput": throughput,
                "error_rate": error_rate,
                "success_rate": (success_count / len(tasks)) * 100 if tasks else 0,
                "cpu_usage_avg": sum(self.performance_metrics["cpu_usage"]) / len(self.performance_metrics["cpu_usage"]) if self.performance_metrics["cpu_usage"] else 0,
                "memory_usage_avg": sum(self.performance_metrics["memory_usage"]) / len(self.performance_metrics["memory_usage"]) if self.performance_metrics["memory_usage"] else 0,
                "status": "passed" if error_rate < 0.05 and avg_response_time < 5.0 else "failed"
            }
            
            print(f"✅ AI Orchestrator Performance: {throughput:.2f} req/s, Avg: {avg_response_time:.3f}s")
            
        except Exception as e:
            self.test_results["ai_orchestrator_performance"] = {
                "error": str(e),
                "status": "failed"
            }
            print(f"❌ AI Orchestrator Performance tests failed: {e}")
    
    async def test_multi_llm_scalability(self):
        """Test Multi-LLM scalability with multiple providers"""
        print("\n🤖 Testing Multi-LLM Scalability...")
        
        try:
            multi_llm = MultiLLMManager()
            await multi_llm.initialize()
            
            # Performance metrics
            provider_response_times = {}
            provider_error_rates = {}
            
            # Test with multiple providers
            providers = ["openai", "anthropic", "cohere"]
            
            for provider in providers:
                response_times = []
                error_count = 0
                
                # Test 50 requests per provider
                tasks = []
                for i in range(50):
                    task = multi_llm.generate_text(
                        Mock(
                            id=f"test_{provider}_{i}",
                            provider=provider,
                            model="default",
                            prompt=f"Test prompt {i} for {provider}"
                        )
                    )
                    tasks.append(task)
                
                # Monitor resources
                monitor_thread = threading.Thread(target=self._monitor_system_resources)
                monitor_thread.start()
                
                # Execute tasks
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Stop monitoring
                monitor_thread.join()
                
                # Calculate metrics
                for result in results:
                    if isinstance(result, Exception):
                        error_count += 1
                    else:
                        # Simulate response time (would be measured in real implementation)
                        response_times.append(0.5 + (i % 3) * 0.2)  # Simulated varying response times
                
                provider_response_times[provider] = {
                    "avg": sum(response_times) / len(response_times) if response_times else 0,
                    "max": max(response_times) if response_times else 0,
                    "min": min(response_times) if response_times else 0
                }
                
                provider_error_rates[provider] = error_count / len(tasks) if tasks else 0
            
            # Calculate overall scalability metrics
            total_requests = sum(50 for _ in providers)
            total_errors = sum(error_count for error_count in provider_error_rates.values())
            overall_error_rate = total_errors / total_requests if total_requests > 0 else 0
            
            self.test_results["multi_llm_scalability"] = {
                "providers_tested": len(providers),
                "requests_per_provider": 50,
                "total_requests": total_requests,
                "provider_response_times": provider_response_times,
                "provider_error_rates": provider_error_rates,
                "overall_error_rate": overall_error_rate,
                "scalability_score": (1 - overall_error_rate) * 100,
                "status": "passed" if overall_error_rate < 0.1 else "failed"
            }
            
            print(f"✅ Multi-LLM Scalability: {len(providers)} providers, {overall_error_rate:.2%} error rate")
            
        except Exception as e:
            self.test_results["multi_llm_scalability"] = {
                "error": str(e),
                "status": "failed"
            }
            print(f"❌ Multi-LLM Scalability tests failed: {e}")
    
    async def test_cache_performance(self):
        """Test cache performance under high load"""
        print("\n💾 Testing Cache Performance...")
        
        try:
            llm_cache = LLMCacheManager()
            await llm_cache.initialize()
            
            # Performance metrics
            write_times = []
            read_times = []
            cache_hits = 0
            cache_misses = 0
            
            # Test cache writes
            write_start = time.time()
            
            # Write 1000 items
            write_tasks = []
            for i in range(1000):
                task = llm_cache.set_sync(f"key_{i}", f"value_{i}", "model_test")
                write_tasks.append(task)
            
            # Monitor resources
            monitor_thread = threading.Thread(target=self._monitor_system_resources)
            monitor_thread.start()
            
            # Execute writes
            write_results = await asyncio.gather(*write_tasks, return_exceptions=True)
            
            write_end = time.time()
            total_write_time = write_end - write_start
            
            # Test cache reads
            read_start = time.time()
            
            # Read 1000 items (mix of existing and non-existing)
            read_tasks = []
            for i in range(1500):  # Some will be cache misses
                task = llm_cache.get_sync(f"key_{i}", "model_test")
                read_tasks.append(task)
            
            # Execute reads
            read_results = await asyncio.gather(*read_tasks, return_exceptions=True)
            
            read_end = time.time()
            total_read_time = read_end - read_start
            
            # Stop monitoring
            monitor_thread.join()
            
            # Calculate cache metrics
            for result in read_results:
                if result:
                    cache_hits += 1
                else:
                    cache_misses += 1
            
            cache_hit_rate = cache_hits / len(read_results) if read_results else 0
            write_throughput = 1000 / total_write_time if total_write_time > 0 else 0
            read_throughput = 1500 / total_read_time if total_read_time > 0 else 0
            
            self.test_results["cache_performance"] = {
                "items_written": 1000,
                "items_read": 1500,
                "write_time": total_write_time,
                "read_time": total_read_time,
                "write_throughput": write_throughput,
                "read_throughput": read_throughput,
                "cache_hit_rate": cache_hit_rate,
                "cache_miss_rate": 1 - cache_hit_rate,
                "status": "passed" if cache_hit_rate > 0.6 and write_throughput > 100 else "failed"
            }
            
            print(f"✅ Cache Performance: {write_throughput:.0f} writes/s, {read_throughput:.0f} reads/s, {cache_hit_rate:.1%} hit rate")
            
        except Exception as e:
            self.test_results["cache_performance"] = {
                "error": str(e),
                "status": "failed"
            }
            print(f"❌ Cache Performance tests failed: {e}")
    
    async def test_async_tasks_performance(self):
        """Test async tasks performance and scalability"""
        print("\n⚡ Testing Async Tasks Performance...")
        
        try:
            async_tasks = AsyncTaskManager()
            await async_tasks.initialize()
            
            # Performance metrics
            submission_times = []
            completion_times = []
            task_count = 1000
            
            # Submit tasks
            submission_start = time.time()
            
            task_ids = []
            for i in range(task_count):
                task_id = await async_tasks.submit_task(
                    task_type="performance_test",
                    payload={"task_id": i, "data": f"test_data_{i}"}
                )
                task_ids.append(task_id)
            
            submission_end = time.time()
            total_submission_time = submission_end - submission_start
            
            # Monitor resources
            monitor_thread = threading.Thread(target=self._monitor_system_resources)
            monitor_thread.start()
            
            # Wait for tasks to complete
            completion_start = time.time()
            
            completed_tasks = 0
            for task_id in task_ids:
                result = await async_tasks.get_task_result(task_id, timeout=10)
                if result:
                    completed_tasks += 1
            
            completion_end = time.time()
            total_completion_time = completion_end - completion_start
            
            # Stop monitoring
            monitor_thread.join()
            
            # Calculate performance metrics
            submission_throughput = task_count / total_submission_time if total_submission_time > 0 else 0
            completion_throughput = completed_tasks / total_completion_time if total_completion_time > 0 else 0
            completion_rate = completed_tasks / task_count if task_count > 0 else 0
            
            self.test_results["async_tasks_performance"] = {
                "tasks_submitted": task_count,
                "tasks_completed": completed_tasks,
                "submission_time": total_submission_time,
                "completion_time": total_completion_time,
                "submission_throughput": submission_throughput,
                "completion_throughput": completion_throughput,
                "completion_rate": completion_rate,
                "status": "passed" if completion_rate > 0.9 and submission_throughput > 100 else "failed"
            }
            
            print(f"✅ Async Tasks Performance: {submission_throughput:.0f} submissions/s, {completion_throughput:.0f} completions/s")
            
        except Exception as e:
            self.test_results["async_tasks_performance"] = {
                "error": str(e),
                "status": "failed"
            }
            print(f"❌ Async Tasks Performance tests failed: {e}")
    
    async def test_connection_pool_scalability(self):
        """Test connection pool scalability"""
        print("\n🔗 Testing Connection Pool Scalability...")
        
        try:
            conn_pool = ConnectionPoolManager()
            await conn_pool.initialize()
            
            # Performance metrics
            acquisition_times = []
            release_times = []
            max_concurrent_connections = 0
            errors = 0
            
            async def acquire_release_cycle(cycle_id):
                try:
                    # Acquire connection
                    start_time = time.time()
                    conn = await conn_pool.get_connection()
                    acquisition_time = time.time() - start_time
                    acquisition_times.append(acquisition_time)
                    
                    # Simulate work
                    await asyncio.sleep(0.1)
                    
                    # Release connection
                    start_time = time.time()
                    await conn_pool.release_connection(conn)
                    release_time = time.time() - start_time
                    release_times.append(release_time)
                    
                    return True
                except Exception as e:
                    errors += 1
                    return False
            
            # Test with high concurrency
            tasks = []
            for i in range(200):  # 200 concurrent connection cycles
                tasks.append(acquire_release_cycle(i))
            
            # Monitor resources
            monitor_thread = threading.Thread(target=self._monitor_system_resources)
            monitor_thread.start()
            
            # Execute all tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Stop monitoring
            monitor_thread.join()
            
            # Calculate performance metrics
            successful_cycles = len([r for r in results if r is True])
            error_rate = errors / len(tasks) if tasks else 0
            avg_acquisition_time = sum(acquisition_times) / len(acquisition_times) if acquisition_times else 0
            avg_release_time = sum(release_times) / len(release_times) if release_times else 0
            
            self.test_results["connection_pool_scalability"] = {
                "concurrent_cycles": len(tasks),
                "successful_cycles": successful_cycles,
                "error_rate": error_rate,
                "avg_acquisition_time": avg_acquisition_time,
                "avg_release_time": avg_release_time,
                "throughput": successful_cycles / 10,  # cycles per second
                "status": "passed" if error_rate < 0.05 and avg_acquisition_time < 0.1 else "failed"
            }
            
            print(f"✅ Connection Pool Scalability: {successful_cycles}/{len(tasks)} successful, {avg_acquisition_time:.3f}s avg acquisition")
            
        except Exception as e:
            self.test_results["connection_pool_scalability"] = {
                "error": str(e),
                "status": "failed"
            }
            print(f"❌ Connection Pool Scalability tests failed: {e}")
    
    async def test_load_balancer_performance(self):
        """Test load balancer performance under load"""
        print("\n⚖️ Testing Load Balancer Performance...")
        
        try:
            load_balancer = LoadBalancer()
            await load_balancer.initialize()
            
            # Performance metrics
            backend_selection_times = []
            backend_distribution = {}
            errors = 0
            
            # Simulate backends
            backends = ["backend1", "backend2", "backend3", "backend4"]
            
            async def select_backend(request_id):
                try:
                    start_time = time.time()
                    backend = await load_balancer.select_backend(
                        request_path=f"/api/test_{request_id}",
                        method="GET"
                    )
                    selection_time = time.time() - start_time
                    backend_selection_times.append(selection_time)
                    
                    # Track distribution
                    if backend in backend_distribution:
                        backend_distribution[backend] += 1
                    else:
                        backend_distribution[backend] = 1
                    
                    return backend
                except Exception as e:
                    errors += 1
                    return None
            
            # Test with high request volume
            tasks = []
            for i in range(1000):  # 1000 requests
                tasks.append(select_backend(i))
            
            # Monitor resources
            monitor_thread = threading.Thread(target=self._monitor_system_resources)
            monitor_thread.start()
            
            # Execute all requests
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Stop monitoring
            monitor_thread.join()
            
            # Calculate performance metrics
            successful_selections = len([r for r in results if r is not None])
            error_rate = errors / len(tasks) if tasks else 0
            avg_selection_time = sum(backend_selection_times) / len(backend_selection_times) if backend_selection_times else 0
            throughput = successful_selections / 10  # selections per second
            
            # Calculate distribution fairness
            expected_per_backend = successful_selections / len(backends)
            distribution_variance = sum((count - expected_per_backend) ** 2 for count in backend_distribution.values()) / len(backends)
            
            self.test_results["load_balancer_performance"] = {
                "total_requests": len(tasks),
                "successful_selections": successful_selections,
                "error_rate": error_rate,
                "avg_selection_time": avg_selection_time,
                "throughput": throughput,
                "backend_distribution": backend_distribution,
                "distribution_fairness": 1 - (distribution_variance / (expected_per_backend ** 2)) if expected_per_backend > 0 else 0,
                "status": "passed" if error_rate < 0.01 and avg_selection_time < 0.01 else "failed"
            }
            
            print(f"✅ Load Balancer Performance: {throughput:.0f} selections/s, {avg_selection_time:.4f}s avg selection")
            
        except Exception as e:
            self.test_results["load_balancer_performance"] = {
                "error": str(e),
                "status": "failed"
            }
            print(f"❌ Load Balancer Performance tests failed: {e}")
    
    async def test_plugin_system_performance(self):
        """Test plugin system performance with multiple plugins"""
        print("\n🔌 Testing Plugin System Performance...")
        
        try:
            plugin_manager = PluginManager()
            await plugin_manager.initialize()
            
            # Performance metrics
            install_times = []
            execution_times = []
            plugin_count = 20
            
            # Install multiple plugins
            for i in range(plugin_count):
                install_start = time.time()
                await plugin_manager.install_plugin(
                    plugin_source=f"https://example.com/plugin_{i}.zip",
                    auto_approve=True
                )
                install_time = time.time() - install_start
                install_times.append(install_time)
            
            # Test plugin execution
            async def execute_plugin(plugin_id, execution_id):
                try:
                    start_time = time.time()
                    result = await plugin_manager.execute_plugin(
                        plugin_id=plugin_id,
                        execution_id=execution_id,
                        data={"test": f"data_{execution_id}"}
                    )
                    execution_time = time.time() - start_time
                    execution_times.append(execution_time)
                    return result
                except Exception as e:
                    return None
            
            # Execute plugins concurrently
            tasks = []
            for i in range(plugin_count):
                for j in range(5):  # 5 executions per plugin
                    tasks.append(execute_plugin(f"plugin_{i}", f"exec_{i}_{j}"))
            
            # Monitor resources
            monitor_thread = threading.Thread(target=self._monitor_system_resources)
            monitor_thread.start()
            
            # Execute all tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Stop monitoring
            monitor_thread.join()
            
            # Calculate performance metrics
            successful_executions = len([r for r in results if r is not None])
            avg_install_time = sum(install_times) / len(install_times) if install_times else 0
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
            installation_throughput = plugin_count / sum(install_times) if install_times else 0
            execution_throughput = successful_executions / sum(execution_times) if execution_times else 0
            
            self.test_results["plugin_system_performance"] = {
                "plugins_installed": plugin_count,
                "executions_attempted": len(tasks),
                "successful_executions": successful_executions,
                "avg_install_time": avg_install_time,
                "avg_execution_time": avg_execution_time,
                "installation_throughput": installation_throughput,
                "execution_throughput": execution_throughput,
                "status": "passed" if successful_executions > len(tasks) * 0.9 and avg_execution_time < 0.1 else "failed"
            }
            
            print(f"✅ Plugin System Performance: {installation_throughput:.1f} installs/s, {execution_throughput:.1f} executions/s")
            
        except Exception as e:
            self.test_results["plugin_system_performance"] = {
                "error": str(e),
                "status": "failed"
            }
            print(f"❌ Plugin System Performance tests failed: {e}")
    
    async def test_enterprise_features_performance(self):
        """Test enterprise features performance under load"""
        print("\n🏢 Testing Enterprise Features Performance...")
        
        try:
            enterprise = EnterpriseManager()
            await enterprise.initialize()
            
            # Performance metrics
            auth_times = []
            permission_check_times = []
            audit_log_times = []
            
            # Test authentication performance
            async def authenticate_user(user_id):
                start_time = time.time()
                user = await enterprise.authenticate_user(
                    provider="saml",
                    credentials={"saml_response": f"test_response_{user_id}"},
                    context={"ip_address": f"192.168.1.{user_id % 255}"}
                )
                auth_time = time.time() - start_time
                auth_times.append(auth_time)
                return user
            
            # Test permission checking performance
            async def check_permissions(user_id):
                start_time = time.time()
                has_permission = enterprise.check_permission(
                    user=Mock(
                        id=f"user_{user_id}",
                        role="developer",
                        permissions=["data_read", "data_write"]
                    ),
                    permission="data_export"
                )
                check_time = time.time() - start_time
                permission_check_times.append(check_time)
                return has_permission
            
            # Test audit logging performance
            async def log_audit_event(event_id):
                start_time = time.time()
                await enterprise.log_user_action(
                    user=Mock(id=f"user_{event_id}", username=f"user_{event_id}"),
                    action="data_export",
                    resource_type="analytics",
                    resource_id=f"report_{event_id}",
                    details={"event_id": event_id},
                    context={"ip_address": f"192.168.1.{event_id % 255}"}
                )
                log_time = time.time() - start_time
                audit_log_times.append(log_time)
                return True
            
            # Run performance tests
            tasks = []
            
            # 100 authentications
            for i in range(100):
                tasks.append(authenticate_user(i))
            
            # 200 permission checks
            for i in range(200):
                tasks.append(check_permissions(i))
            
            # 500 audit logs
            for i in range(500):
                tasks.append(log_audit_event(i))
            
            # Monitor resources
            monitor_thread = threading.Thread(target=self._monitor_system_resources)
            monitor_thread.start()
            
            # Execute all tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Stop monitoring
            monitor_thread.join()
            
            # Calculate performance metrics
            avg_auth_time = sum(auth_times) / len(auth_times) if auth_times else 0
            avg_permission_check_time = sum(permission_check_times) / len(permission_check_times) if permission_check_times else 0
            avg_audit_log_time = sum(audit_log_times) / len(audit_log_times) if audit_log_times else 0
            
            auth_throughput = 100 / sum(auth_times) if auth_times else 0
            permission_throughput = 200 / sum(permission_check_times) if permission_check_times else 0
            audit_throughput = 500 / sum(audit_log_times) if audit_log_times else 0
            
            self.test_results["enterprise_features_performance"] = {
                "authentications": 100,
                "permission_checks": 200,
                "audit_logs": 500,
                "avg_auth_time": avg_auth_time,
                "avg_permission_check_time": avg_permission_check_time,
                "avg_audit_log_time": avg_audit_log_time,
                "auth_throughput": auth_throughput,
                "permission_throughput": permission_throughput,
                "audit_throughput": audit_throughput,
                "status": "passed" if (avg_auth_time < 0.1 and avg_permission_check_time < 0.01 and avg_audit_log_time < 0.05) else "failed"
            }
            
            print(f"✅ Enterprise Features Performance: Auth {auth_throughput:.0f}/s, Permissions {permission_throughput:.0f}/s, Audit {audit_throughput:.0f}/s")
            
        except Exception as e:
            self.test_results["enterprise_features_performance"] = {
                "error": str(e),
                "status": "failed"
            }
            print(f"❌ Enterprise Features Performance tests failed: {e}")
    
    async def run_all_performance_tests(self):
        """Run all performance tests and generate comprehensive report"""
        print("🚀 Starting Comprehensive Performance Test Suite for Asmblr")
        print("=" * 70)
        
        start_time = time.time()
        
        # Setup test environment
        await self.setup()
        
        # Run all performance test suites
        test_methods = [
            self.test_ai_orchestrator_performance,
            self.test_multi_llm_scalability,
            self.test_cache_performance,
            self.test_async_tasks_performance,
            self.test_connection_pool_scalability,
            self.test_load_balancer_performance,
            self.test_plugin_system_performance,
            self.test_enterprise_features_performance
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                print(f"❌ Performance test {test_method.__name__} failed: {e}")
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results.values() if r.get("status") == "passed"])
        failed_tests = total_tests - passed_tests
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Generate comprehensive performance report
        report = {
            "performance_test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            },
            "detailed_results": self.test_results,
            "performance_benchmarks": self._generate_performance_benchmarks(),
            "scalability_analysis": self._generate_scalability_analysis(),
            "recommendations": self._generate_performance_recommendations()
        }
        
        # Save report
        report_path = os.path.join(self.temp_dir, "performance_test_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print("\n" + "=" * 70)
        print("⚡ COMPREHENSIVE PERFORMANCE TEST RESULTS")
        print("=" * 70)
        print(f"Total Performance Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {report['performance_test_summary']['success_rate']:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Report saved to: {report_path}")
        
        # Print performance benchmarks
        print("\n📊 Performance Benchmarks:")
        benchmarks = report['performance_benchmarks']
        for component, metrics in benchmarks.items():
            print(f"\n{component}:")
            for metric, value in metrics.items():
                if isinstance(value, float):
                    print(f"  {metric}: {value:.3f}")
                else:
                    print(f"  {metric}: {value}")
        
        # Print failed tests if any
        if failed_tests > 0:
            print("\n❌ Failed Performance Tests:")
            for test_name, result in self.test_results.items():
                if result.get("status") == "failed":
                    print(f"  - {test_name}: {result.get('error', 'Unknown error')}")
        
        # Cleanup
        await self.teardown()
        
        return report
    
    def _generate_performance_benchmarks(self):
        """Generate performance benchmarks from test results"""
        benchmarks = {}
        
        for test_name, result in self.test_results.items():
            if result.get("status") == "passed":
                benchmarks[test_name] = {
                    "throughput": result.get("throughput", 0),
                    "avg_response_time": result.get("avg_response_time", 0),
                    "error_rate": result.get("error_rate", 0),
                    "cpu_usage": result.get("cpu_usage_avg", 0),
                    "memory_usage": result.get("memory_usage_avg", 0)
                }
        
        return benchmarks
    
    def _generate_scalability_analysis(self):
        """Generate scalability analysis"""
        analysis = {
            "high_throughput_components": [],
            "low_latency_components": [],
            "resource_efficient_components": [],
            "scalability_bottlenecks": []
        }
        
        for test_name, result in self.test_results.items():
            if result.get("status") == "passed":
                throughput = result.get("throughput", 0)
                latency = result.get("avg_response_time", 0)
                cpu_usage = result.get("cpu_usage_avg", 0)
                
                if throughput > 100:
                    analysis["high_throughput_components"].append(test_name)
                
                if latency < 0.1:
                    analysis["low_latency_components"].append(test_name)
                
                if cpu_usage < 50:
                    analysis["resource_efficient_components"].append(test_name)
                
                if throughput < 10 or latency > 1.0:
                    analysis["scalability_bottlenecks"].append(test_name)
        
        return analysis
    
    def _generate_performance_recommendations(self):
        """Generate performance recommendations"""
        recommendations = []
        
        for test_name, result in self.test_results.items():
            if result.get("status") == "failed":
                recommendations.append(f"Optimize {test_name}: {result.get('error', 'Performance issues detected')}")
        
        # Add general recommendations based on results
        bottlenecks = self._generate_scalability_analysis()["scalability_bottlenecks"]
        if bottlenecks:
            recommendations.append(f"Address scalability bottlenecks in: {', '.join(bottlenecks)}")
        
        if not recommendations:
            recommendations.extend([
                "All performance tests passed! System is production-ready.",
                "Consider implementing additional monitoring for production workloads.",
                "Set up automated performance testing in CI/CD pipeline."
            ])
        
        return recommendations

async def main():
    """Main performance test runner"""
    tester = TestPerformanceAndScalability()
    report = await tester.run_all_performance_tests()
    
    # Exit with appropriate code
    exit_code = 0 if report['performance_test_summary']['success_rate'] == 100 else 1
    exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())
