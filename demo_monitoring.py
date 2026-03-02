"""
Script de démonstration du monitoring complet pour Asmblr
Montre l'utilisation de tous les composants de monitoring
"""

import asyncio
import time
import random
import json
from pathlib import Path

from app.core.config import Settings
from app.monitoring.prometheus_metrics import AsmblrMetrics
from app.monitoring.structured_logger import StructuredLogger, LogCategory
from app.monitoring.alerting import AlertManager, AlertSeverity
from app.monitoring.distributed_tracing import (
    initialize_tracing, trace_function, trace_llm_request,
    SpanKind, get_trace_id, get_span_id
)
from app.monitoring.health_checks import HealthChecker


class MonitoringDemo:
    """Démonstration complète du monitoring Asmblr"""
    
    def __init__(self):
        self.settings = Settings()
        self.metrics = AsmblrMetrics()
        self.logger = StructuredLogger("monitoring-demo", "demo")
        self.tracer = initialize_tracing(self.settings, self.logger)
        self.alert_manager = AlertManager(self.settings, self.metrics)
        self.health_checker = HealthChecker(self.settings, self.metrics, self.logger)
        
        # Adapter le logger pour le tracing
        from app.monitoring.distributed_tracing import TraceLoggerAdapter
        self.trace_logger = TraceLoggerAdapter(self.tracer, self.logger)
    
    async def start_all_services(self):
        """Démarrer tous les services de monitoring"""
        self.logger.system("Starting all monitoring services")
        
        await self.tracer.start()
        await self.alert_manager.start()
        
        self.logger.system("All monitoring services started")
    
    async def stop_all_services(self):
        """Arrêter tous les services de monitoring"""
        self.logger.system("Stopping all monitoring services")
        
        await self.tracer.shutdown()
        await self.alert_manager.stop()
        
        self.logger.system("All monitoring services stopped")
    
    @trace_function(name="simulate_pipeline_execution", kind=SpanKind.PIPELINE)
    async def simulate_pipeline_execution(self, pipeline_id: str):
        """Simuler l'exécution d'une pipeline avec monitoring complet"""
        
        # Enregistrer le début de la pipeline
        self.metrics.business_metrics.record_pipeline_start(pipeline_id)
        self.logger.business(f"Pipeline {pipeline_id} started", pipeline_id=pipeline_id)
        
        try:
            # Simuler la génération d'idées
            await self.simulate_idea_generation(pipeline_id)
            
            # Simuler l'évaluation des idées
            await self.simulate_idea_evaluation(pipeline_id)
            
            # Simuler la construction du MVP
            await self.simulate_mvp_build(pipeline_id)
            
            # Marquer la pipeline comme réussie
            self.metrics.business_metrics.record_pipeline_completion(pipeline_type="demo", duration=45.2, status="success")
            self.logger.business(f"Pipeline {pipeline_id} completed successfully", 
                              pipeline_id=pipeline_id, duration=45.2)
            
            return {"status": "success", "pipeline_id": pipeline_id}
            
        except Exception as e:
            # Marquer la pipeline comme échouée
            self.metrics.business_metrics.record_pipeline_completion(pipeline_type="demo", duration=0, status="failed")
            self.logger.error(LogCategory.SYSTEM, f"Pipeline {pipeline_id} failed", 
                            pipeline_id=pipeline_id, error=str(e))
            
            # Créer une alerte
            await self.alert_manager.create_alert(
                name="PipelineFailure",
                severity=AlertSeverity.WARNING,
                message=f"Pipeline {pipeline_id} failed: {str(e)}",
                description="Pipeline execution encountered an error",
                labels={"pipeline_id": pipeline_id, "component": "pipeline"}
            )
            
            return {"status": "failed", "pipeline_id": pipeline_id, "error": str(e)}
    
    @trace_llm_request(model="llama3.1:8b", operation="generation")
    async def simulate_idea_generation(self, pipeline_id: str):
        """Simuler la génération d'idées avec LLM"""
        
        # Simuler un appel LLM
        await asyncio.sleep(random.uniform(1, 3))
        
        # Enregistrer les métriques LLM
        self.metrics.business_metrics.record_llm_request(
            model="llama3.1:8b",
            operation="generation",
            response_time=random.uniform(1, 3),
            status="success",
            tokens=random.randint(100, 500)
        )
        
        # Générer des idées
        ideas_count = random.randint(3, 8)
        for i in range(ideas_count):
            self.metrics.business_metrics.record_idea_generation(
                source="ai",
                quality="high" if random.random() > 0.3 else "medium",
                count=1
            )
        
        self.logger.business(f"Generated {ideas_count} ideas for pipeline {pipeline_id}",
                            pipeline_id=pipeline_id, ideas_count=ideas_count)
        
        # Simuler une erreur occasionnelle
        if random.random() < 0.1:
            raise Exception("LLM service temporarily unavailable")
    
    async def simulate_idea_evaluation(self, pipeline_id: str):
        """Simuler l'évaluation des idées"""
        
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Simuler l'évaluation
        ideas_evaluated = random.randint(3, 8)
        selected_ideas = random.randint(1, 3)
        
        self.logger.business(f"Evaluated {ideas_evaluated} ideas, selected {selected_ideas}",
                            pipeline_id=pipeline_id, evaluated=ideas_evaluated, 
                            selected=selected_ideas)
    
    async def simulate_mvp_build(self, pipeline_id: str):
        """Simuler la construction du MVP"""
        
        await asyncio.sleep(random.uniform(2, 5))
        
        # Enregistrer la construction du MVP
        self.metrics.business_metrics.record_mvp_build("web", "success")
        
        self.logger.business(f"MVP built for pipeline {pipeline_id}",
                            pipeline_id=pipeline_id, build_type="web")
        
        # Simuler une erreur occasionnelle
        if random.random() < 0.05:
            raise Exception("Build resources insufficient")
    
    @trace_function(name="simulate_api_requests", kind=SpanKind.HTTP)
    async def simulate_api_requests(self, count: int = 20):
        """Simuler des requêtes API avec monitoring"""
        
        endpoints = [
            "/api/ideas",
            "/api/pipelines",
            "/api/mvp",
            "/api/health",
            "/api/metrics"
        ]
        
        methods = ["GET", "POST", "PUT", "DELETE"]
        
        for i in range(count):
            # Simuler une requête API
            method = random.choice(methods)
            endpoint = random.choice(endpoints)
            status_code = random.choices(
                [200, 201, 400, 404, 500],
                weights=[70, 10, 10, 5, 5]
            )[0]
            duration = random.uniform(0.1, 2.0)
            
            # Enregistrer la métrique
            self.metrics.record_request(method, endpoint, status_code, duration)
            
            # Logger avec tracing
            self.trace_logger.log_with_trace(
                "info",
                f"API request: {method} {endpoint}",
                {
                    "method": method,
                    "endpoint": endpoint,
                    "status_code": status_code,
                    "duration_ms": duration * 1000,
                    "trace_id": get_trace_id(),
                    "span_id": get_span_id()
                }
            )
            
            # Créer une alerte pour les erreurs 5xx
            if status_code >= 500:
                await self.alert_manager.create_alert(
                    name="ServerError",
                    severity=AlertSeverity.WARNING,
                    message=f"Server error: {method} {endpoint} returned {status_code}",
                    description="API endpoint returned server error",
                    labels={"method": method, "endpoint": endpoint, "status": str(status_code)}
                )
            
            await asyncio.sleep(0.1)
    
    async def simulate_system_metrics(self):
        """Simuler des métriques système"""
        
        # Simuler l'utilisation CPU
        cpu_usage = random.uniform(20, 90)
        self.metrics.system_metrics.update_cpu_usage(cpu_usage)
        
        # Simuler l'utilisation mémoire
        memory_usage = random.uniform(30, 85)
        self.metrics.system_metrics.update_memory_usage(memory_usage * 1024 * 1024 * 1024)
        
        # Simuler l'utilisation disque
        disk_usage = random.uniform(40, 80)
        self.metrics.system_metrics.update_disk_usage(disk_usage * 1024 * 1024 * 1024)
        
        # Simuler des utilisateurs actifs
        active_users = random.randint(10, 100)
        self.metrics.business_metrics.update_active_users(active_users, "daily")
        
        # Créer des alertes si nécessaire
        if cpu_usage > 80:
            await self.alert_manager.create_alert(
                name="HighCPUUsage",
                severity=AlertSeverity.WARNING if cpu_usage < 90 else AlertSeverity.CRITICAL,
                message=f"CPU usage is {cpu_usage:.1f}%",
                description="System CPU usage is high",
                labels={"metric": "cpu", "value": str(cpu_usage)}
            )
        
        if memory_usage > 80:
            await self.alert_manager.create_alert(
                name="HighMemoryUsage",
                severity=AlertSeverity.WARNING if memory_usage < 90 else AlertSeverity.CRITICAL,
                message=f"Memory usage is {memory_usage:.1f}%",
                description="System memory usage is high",
                labels={"metric": "memory", "value": str(memory_usage)}
            )
    
    async def simulate_cache_operations(self):
        """Simuler des opérations de cache"""
        
        # Simuler des opérations de cache
        for i in range(50):
            operation = random.choice(["get", "set", "delete"])
            cache_type = random.choice(["ideas", "pipelines", "mvp", "llm"])
            
            if operation == "get":
                hit = random.random() > 0.3  # 70% hit rate
                self.metrics.cache_metrics.record_cache_operation(
                    cache_type, operation, hit
                )
            elif operation == "set":
                self.metrics.cache_metrics.record_cache_operation(
                    cache_type, operation, True
                )
            else:  # delete
                self.metrics.cache_metrics.record_cache_operation(
                    cache_type, operation, True
                )
        
        # Mettre à jour la taille du cache
        cache_size = random.randint(100, 1000)
        self.metrics.cache_metrics.update_cache_size(cache_size * 1024)
        
        # Mettre à jour le hit ratio
        hit_ratio = random.uniform(0.6, 0.9)
        self.metrics.cache_metrics.update_hit_ratio(hit_ratio)
    
    async def run_health_checks(self):
        """Exécuter les health checks et logger les résultats"""
        
        self.logger.system("Running health checks")
        
        results = await self.health_checker.run_all_checks()
        overall_status = self.health_checker.get_overall_status(results)
        
        # Logger les résultats
        for check_name, result in results.items():
            level = "info" if result.status.value == "healthy" else "warning"
            self.trace_logger.log_with_trace(
                level,
                f"Health check {check_name}: {result.status.value}",
                {
                    "check_name": check_name,
                    "status": result.status.value,
                    "message": result.message,
                    "duration_ms": result.duration_ms,
                    "critical": result.critical
                }
            )
        
        # Logger le statut global
        self.logger.system(f"Overall health status: {overall_status.value}",
                          overall_status=overall_status.value,
                          checks_count=len(results))
        
        # Créer une alerte si le statut n'est pas healthy
        if overall_status.value != "healthy":
            await self.alert_manager.create_alert(
                name="HealthCheckFailed",
                severity=AlertSeverity.WARNING,
                message=f"Health check status: {overall_status.value}",
                description="System health checks indicate issues",
                labels={"status": overall_status.value, "checks": str(len(results))}
            )
        
        return results
    
    async def generate_monitoring_report(self):
        """Générer un rapport de monitoring complet"""
        
        # Récupérer les métriques
        metrics_summary = self.metrics.get_metrics_summary()
        
        # Récupérer les alertes
        active_alerts = self.alert_manager.get_active_alerts()
        alert_stats = self.alert_manager.get_alert_stats()
        
        # Récupérer les health checks
        health_results = await self.run_health_checks()
        health_summary = self.health_checker.get_health_summary()
        
        # Générer le rapport
        report = {
            "timestamp": time.time(),
            "metrics": metrics_summary,
            "alerts": {
                "active_count": len(active_alerts),
                "stats": alert_stats,
                "active": [alert.to_dict() for alert in active_alerts[:5]]  # Top 5
            },
            "health": health_summary,
            "system": {
                "trace_id": get_trace_id(),
                "span_id": get_span_id(),
                "services": {
                    "metrics": "running",
                    "alerts": "running",
                    "tracing": "running",
                    "health_checks": "running"
                }
            }
        }
        
        # Logger le rapport
        self.logger.system("Generated monitoring report",
                          metrics_count=metrics_summary["registered_metrics"],
                          active_alerts=len(active_alerts),
                          health_status=health_summary["status"])
        
        # Sauvegarder le rapport
        report_file = Path("monitoring_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str, ensure_ascii=False)
        
        self.logger.system(f"Monitoring report saved to {report_file}")
        
        return report
    
    async def run_demo(self, duration: int = 60):
        """Exécuter la démonstration complète"""
        
        self.logger.system(f"Starting monitoring demo for {duration} seconds")
        
        # Démarrer les services
        await self.start_all_services()
        
        try:
            start_time = time.time()
            
            # Boucle de démonstration
            while time.time() - start_time < duration:
                # Exécuter une pipeline
                pipeline_id = f"demo-pipeline-{int(time.time())}"
                await self.simulate_pipeline_execution(pipeline_id)
                
                # Simuler des requêtes API
                await self.simulate_api_requests(random.randint(10, 30))
                
                # Simuler des métriques système
                await self.simulate_system_metrics()
                
                # Simuler des opérations de cache
                await self.simulate_cache_operations()
                
                # Exécuter les health checks
                await self.run_health_checks()
                
                # Attendre avant la prochaine itération
                await asyncio.sleep(5)
            
            # Générer le rapport final
            final_report = await self.generate_monitoring_report()
            
            self.logger.system("Monitoring demo completed successfully")
            
            return final_report
            
        finally:
            # Arrêter les services
            await self.stop_all_services()


async def main():
    """Point d'entrée principal de la démonstration"""
    
    print("🚀 Asmblr Monitoring Demo")
    print("=" * 50)
    
    demo = MonitoringDemo()
    
    try:
        # Exécuter la démo
        report = await demo.run_demo(duration=30)  # 30 secondes de démo
        
        # Afficher le résumé
        print("\n📊 Demo Summary:")
        print(f"  Metrics registered: {report['metrics']['registered_metrics']}")
        print(f"  Active alerts: {report['alerts']['active_count']}")
        print(f"  Health status: {report['health']['status']}")
        print(f"  Services running: {len([s for s in report['system']['services'].values() if s == 'running'])}")
        
        print("\n✅ Demo completed successfully!")
        print("📄 Check monitoring_report.json for detailed results")
        
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
    finally:
        await demo.stop_all_services()


if __name__ == "__main__":
    asyncio.run(main())
