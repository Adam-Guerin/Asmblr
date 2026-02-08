#!/usr/bin/env python3
"""
Test d'intégration des micro-services Asmblr - Phase 2
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Configuration des services
SERVICES = {
    "api_gateway": "http://localhost:8000",
    "core": "http://localhost:8001", 
    "agents": "http://localhost:8002",
    "media": "http://localhost:8003"
}

class MicroserviceTester:
    """Testeur d'intégration pour les micro-services"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results = {}
    
    async def test_service_health(self, service_name: str, url: str) -> Dict[str, Any]:
        """Test le health check d'un service"""
        try:
            response = await self.client.get(f"{url}/health")
            return {
                "service": service_name,
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
            }
        except Exception as e:
            return {
                "service": service_name,
                "status": "error",
                "error": str(e),
                "response_time": None
            }
    
    async def test_service_readiness(self, service_name: str, url: str) -> Dict[str, Any]:
        """Test le readiness check d'un service"""
        try:
            response = await self.client.get(f"{url}/ready")
            return {
                "service": service_name,
                "ready": response.status_code == 200,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
            }
        except Exception as e:
            return {
                "service": service_name,
                "ready": False,
                "error": str(e),
                "response_time": None
            }
    
    async def test_api_gateway_routing(self) -> Dict[str, Any]:
        """Test le routing de l'API Gateway"""
        gateway_url = SERVICES["api_gateway"]
        tests = []
        
        # Test création de pipeline (route vers core)
        try:
            pipeline_data = {
                "topic": "AI compliance for SMBs",
                "config": {"mode": "quick"},
                "mode": "standard"
            }
            response = await self.client.post(f"{gateway_url}/api/v1/pipelines", json=pipeline_data)
            tests.append({
                "test": "create_pipeline_via_gateway",
                "status": "success" if response.status_code in [200, 201] else "failed",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            })
        except Exception as e:
            tests.append({
                "test": "create_pipeline_via_gateway",
                "status": "error",
                "error": str(e)
            })
        
        # Test listing des pipelines (route vers core)
        try:
            response = await self.client.get(f"{gateway_url}/api/v1/pipelines")
            tests.append({
                "test": "list_pipelines_via_gateway",
                "status": "success" if response.status_code == 200 else "failed",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            })
        except Exception as e:
            tests.append({
                "test": "list_pipelines_via_gateway",
                "status": "error",
                "error": str(e)
            })
        
        # Test exécution d'agent (route vers agents)
        try:
            agent_data = {
                "task_type": "idea_generation",
                "input_data": {"topic": "AI compliance tools"},
                "model": "llama3.1:8b"
            }
            response = await self.client.post(f"{gateway_url}/api/v1/agents/execute", json=agent_data)
            tests.append({
                "test": "execute_agent_via_gateway",
                "status": "success" if response.status_code == 200 else "failed",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            })
        except Exception as e:
            tests.append({
                "test": "execute_agent_via_gateway",
                "status": "error",
                "error": str(e)
            })
        
        return {
            "component": "api_gateway_routing",
            "tests": tests,
            "success_rate": len([t for t in tests if t["status"] == "success"]) / len(tests) * 100
        }
    
    async def test_service_isolation(self) -> Dict[str, Any]:
        """Test l'isolation des services"""
        tests = []
        
        # Test service core directement
        try:
            response = await self.client.get(f"{SERVICES['core']}/api/v1/pipelines")
            tests.append({
                "test": "core_direct_access",
                "status": "success" if response.status_code == 200 else "failed",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            })
        except Exception as e:
            tests.append({
                "test": "core_direct_access",
                "status": "error",
                "error": str(e)
            })
        
        # Test service agents directement
        try:
            response = await self.client.get(f"{SERVICES['agents']}/api/v1/agents/status")
            tests.append({
                "test": "agents_direct_access",
                "status": "success" if response.status_code == 200 else "failed",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            })
        except Exception as e:
            tests.append({
                "test": "agents_direct_access",
                "status": "error",
                "error": str(e)
            })
        
        # Test service media directement
        try:
            response = await self.client.get(f"{SERVICES['media']}/api/v1/media/stats")
            tests.append({
                "test": "media_direct_access",
                "status": "success" if response.status_code == 200 else "failed",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            })
        except Exception as e:
            tests.append({
                "test": "media_direct_access",
                "status": "error",
                "error": str(e)
            })
        
        return {
            "component": "service_isolation",
            "tests": tests,
            "success_rate": len([t for t in tests if t["status"] == "success"]) / len(tests) * 100
        }
    
    async def test_pipeline_flow(self) -> Dict[str, Any]:
        """Test un flux complet de pipeline"""
        gateway_url = SERVICES["api_gateway"]
        steps = []
        
        try:
            # Étape 1: Créer un pipeline
            pipeline_data = {
                "topic": "Test microservices integration",
                "config": {"mode": "quick"},
                "mode": "quick"
            }
            response = await self.client.post(f"{gateway_url}/api/v1/pipelines", json=pipeline_data)
            
            if response.status_code not in [200, 201]:
                steps.append({
                    "step": "create_pipeline",
                    "status": "failed",
                    "error": f"Status code: {response.status_code}"
                })
                return {"component": "pipeline_flow", "steps": steps, "success_rate": 0}
            
            pipeline = response.json()
            pipeline_id = pipeline.get("id")
            steps.append({
                "step": "create_pipeline",
                "status": "success",
                "pipeline_id": pipeline_id
            })
            
            # Étape 2: Récupérer le pipeline
            response = await self.client.get(f"{gateway_url}/api/v1/pipelines/{pipeline_id}")
            if response.status_code == 200:
                steps.append({
                    "step": "get_pipeline",
                    "status": "success",
                    "pipeline_id": pipeline_id
                })
            else:
                steps.append({
                    "step": "get_pipeline",
                    "status": "failed",
                    "error": f"Status code: {response.status_code}"
                })
            
            # Étape 3: Exécuter le pipeline (si disponible)
            try:
                response = await self.client.post(f"{gateway_url}/api/v1/pipelines/{pipeline_id}/run")
                if response.status_code == 200:
                    steps.append({
                        "step": "run_pipeline",
                        "status": "success",
                        "pipeline_id": pipeline_id
                    })
                else:
                    steps.append({
                        "step": "run_pipeline",
                        "status": "failed",
                        "error": f"Status code: {response.status_code}"
                    })
            except Exception as e:
                steps.append({
                    "step": "run_pipeline",
                    "status": "error",
                    "error": str(e)
                })
            
        except Exception as e:
            steps.append({
                "step": "pipeline_flow_error",
                "status": "error",
                "error": str(e)
            })
        
        success_count = len([s for s in steps if s["status"] == "success"])
        return {
            "component": "pipeline_flow",
            "steps": steps,
            "success_rate": success_count / len(steps) * 100 if steps else 0
        }
    
    async def test_monitoring(self) -> Dict[str, Any]:
        """Test les endpoints de monitoring"""
        tests = []
        
        for service_name, url in SERVICES.items():
            try:
                response = await self.client.get(f"{url}/metrics")
                tests.append({
                    "test": f"{service_name}_metrics",
                    "status": "success" if response.status_code == 200 else "failed",
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "response_time": response.elapsed.total_seconds()
                })
            except Exception as e:
                tests.append({
                    "test": f"{service_name}_metrics",
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "component": "monitoring",
            "tests": tests,
            "success_rate": len([t for t in tests if t["status"] == "success"]) / len(tests) * 100
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Exécute tous les tests d'intégration"""
        print("🚀 DÉMARRAGE DES TESTS D'INTÉGRATION MICRO-SERVICES")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test 1: Health checks
        print("\n📋 Test 1: Health Checks")
        health_results = []
        for service_name, url in SERVICES.items():
            result = await self.test_service_health(service_name, url)
            health_results.append(result)
            status_icon = "✅" if result["status"] == "healthy" else "❌"
            print(f"  {status_icon} {service_name}: {result['status']} ({result.get('response_time', 'N/A'):.3f}s)")
        
        # Test 2: Readiness checks
        print("\n📋 Test 2: Readiness Checks")
        readiness_results = []
        for service_name, url in SERVICES.items():
            result = await self.test_service_readiness(service_name, url)
            readiness_results.append(result)
            status_icon = "✅" if result["ready"] else "❌"
            print(f"  {status_icon} {service_name}: {'ready' if result['ready'] else 'not ready'}")
        
        # Test 3: API Gateway routing
        print("\n📋 Test 3: API Gateway Routing")
        gateway_result = await self.test_api_gateway_routing()
        for test in gateway_result["tests"]:
            status_icon = "✅" if test["status"] == "success" else "❌"
            print(f"  {status_icon} {test['test']}: {test['status']}")
        print(f"  📊 Success Rate: {gateway_result['success_rate']:.1f}%")
        
        # Test 4: Service isolation
        print("\n📋 Test 4: Service Isolation")
        isolation_result = await self.test_service_isolation()
        for test in isolation_result["tests"]:
            status_icon = "✅" if test["status"] == "success" else "❌"
            print(f"  {status_icon} {test['test']}: {test['status']}")
        print(f"  📊 Success Rate: {isolation_result['success_rate']:.1f}%")
        
        # Test 5: Pipeline flow
        print("\n📋 Test 5: Pipeline Flow")
        flow_result = await self.test_pipeline_flow()
        for step in flow_result["steps"]:
            status_icon = "✅" if step["status"] == "success" else "❌"
            print(f"  {status_icon} {step['step']}: {step['status']}")
        print(f"  📊 Success Rate: {flow_result['success_rate']:.1f}%")
        
        # Test 6: Monitoring
        print("\n📋 Test 6: Monitoring Endpoints")
        monitoring_result = await self.test_monitoring()
        for test in monitoring_result["tests"]:
            status_icon = "✅" if test["status"] == "success" else "❌"
            print(f"  {status_icon} {test['test']}: {test['status']}")
        print(f"  📊 Success Rate: {monitoring_result['success_rate']:.1f}%")
        
        # Résultats globaux
        total_time = time.time() - start_time
        
        all_tests = (
            len(health_results) + 
            len(readiness_results) + 
            len(gateway_result["tests"]) + 
            len(isolation_result["tests"]) + 
            len(flow_result["steps"]) + 
            len(monitoring_result["tests"])
        )
        
        successful_tests = (
            len([r for r in health_results if r["status"] == "healthy"]) +
            len([r for r in readiness_results if r["ready"]]) +
            len([t for t in gateway_result["tests"] if t["status"] == "success"]) +
            len([t for t in isolation_result["tests"] if t["status"] == "success"]) +
            len([s for s in flow_result["steps"] if s["status"] == "success"]) +
            len([t for t in monitoring_result["tests"] if t["status"] == "success"])
        )
        
        overall_success_rate = (successful_tests / all_tests) * 100 if all_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 RÉSULTATS GLOBAUX")
        print("=" * 60)
        print(f"⏱️  Temps total: {total_time:.2f} secondes")
        print(f"📋 Tests exécutés: {all_tests}")
        print(f"✅ Tests réussis: {successful_tests}")
        print(f"❌ Tests échoués: {all_tests - successful_tests}")
        print(f"📈 Taux de réussite: {overall_success_rate:.1f}%")
        
        # Évaluation
        if overall_success_rate >= 80:
            print("🎉 EXCELLENT: L'intégration micro-services est fonctionnelle!")
        elif overall_success_rate >= 60:
            print("⚠️  BON: L'intégration fonctionne avec quelques problèmes mineurs.")
        else:
            print("🚨 CRITIQUE: L'intégration a des problèmes majeurs à résoudre.")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_time": total_time,
            "total_tests": all_tests,
            "successful_tests": successful_tests,
            "failed_tests": all_tests - successful_tests,
            "overall_success_rate": overall_success_rate,
            "health_checks": health_results,
            "readiness_checks": readiness_results,
            "gateway_routing": gateway_result,
            "service_isolation": isolation_result,
            "pipeline_flow": flow_result,
            "monitoring": monitoring_result
        }
    
    async def close(self):
        """Ferme le client HTTP"""
        await self.client.aclose()


async def main():
    """Fonction principale"""
    tester = MicroserviceTester()
    
    try:
        results = await tester.run_all_tests()
        
        # Sauvegarder les résultats
        with open("microservices_integration_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Résultats sauvegardés dans: microservices_integration_test_results.json")
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrompus par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
