"""
Analyse complète de l'état actuel du monitoring et de l'observabilité pour Asmblr
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MonitoringComponent:
    """Représente un composant de monitoring"""
    name: str
    type: str  # metrics, logs, tracing, alerting, dashboard
    status: str  # implemented, partial, missing, planned
    description: str
    files: List[str]
    features: List[str]
    gaps: List[str]
    recommendations: List[str]


class MonitoringAnalyzer:
    """Analyseur de l'état du monitoring et de l'observabilité"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.components = []
        self.analysis_results = {}
    
    def analyze_current_state(self) -> Dict[str, Any]:
        """Analyse l'état actuel du monitoring"""
        print("🔍 Analyse de l'état actuel du monitoring et de l'observabilité...")
        
        # Analyser chaque composant
        self._analyze_metrics_system()
        self._analyze_logging_system()
        self._analyze_tracing_system()
        self._analyze_alerting_system()
        self._analyze_dashboard_system()
        self._analyze_health_checks()
        self._analyze_infrastructure()
        
        # Calculer les métriques globales
        self._calculate_global_metrics()
        
        return self.analysis_results
    
    def _analyze_metrics_system(self):
        """Analyse le système de métriques"""
        print("📊 Analyse du système de métriques...")
        
        component = MonitoringComponent(
            name="Metrics System",
            type="metrics",
            status="partial",
            description="Système de collecte de métriques avec Prometheus",
            files=[
                "app/monitoring/metrics.py",
                "app/core/metrics_prom.py",
                "app/core/enhanced_monitoring.py",
                "app/core/performance_optimizer_enhanced.py"
            ],
            features=[
                "Métriques Prometheus basiques",
                "Counters, Histograms, Gauges",
                "Métriques de performance worker",
                "Monitoring des ressources système",
                "Métriques custom pour les pipelines"
            ],
            gaps=[
                "Pas d'exportateur Prometheus configuré",
                "Pas de registry centralisé",
                "Métriques business limitées",
                "Pas de agrégation automatique",
                "Labels non standardisés"
            ],
            recommendations=[
                "Configurer Prometheus exporter",
                "Standardiser les labels et noms",
                "Ajouter des métriques business",
                "Implémenter des histogrammes de latence",
                "Ajouter des métriques de taux d'erreur"
            ]
        )
        
        self.components.append(component)
    
    def _analyze_logging_system(self):
        """Analyse le système de logs"""
        print("📝 Analyse du système de logs...")
        
        component = MonitoringComponent(
            name="Logging System",
            type="logs",
            status="partial",
            description="Système de logs avec Loguru et smart logger",
            files=[
                "app/core/smart_logger.py",
                "app/core/error_handler.py",
                "app/monitoring/metrics.py"
            ],
            features=[
                "Smart logger avec filtrage",
                "Logs structurés basiques",
                "Catégorisation des logs",
                "Gestion des niveaux de log",
                "Logs de performance"
            ],
            gaps=[
                "Pas d'intégration ELK Stack",
                "Pas de centralisation des logs",
                "Format non standardisé",
                "Pas de log shipping",
                "Logs de tracing limités"
            ],
            recommendations=[
                "Intégrer ELK Stack (Elasticsearch, Logstash, Kibana)",
                "Standardiser le format JSON",
                "Configurer log shipping",
                "Ajouter des correlation IDs",
                "Implémenter le log sampling"
            ]
        )
        
        self.components.append(component)
    
    def _analyze_tracing_system(self):
        """Analyse le système de tracing"""
        print("🔍 Analyse du système de tracing...")
        
        component = MonitoringComponent(
            name="Distributed Tracing",
            type="tracing",
            status="partial",
            description="Tracing distribué avec OpenTelemetry et Jaeger",
            files=[
                "app/core/enhanced_monitoring.py",
                "app/core/public_config.py"
            ],
            features=[
                "OpenTelemetry integration",
                "Jaeger exporter configuré",
                "Spans automatiques pour FastAPI",
                "Context propagation basique",
                "Custom spans possibles"
            ],
            gaps=[
                "Jaeger non déployé",
                "Sampling non configuré",
                "Spans manuels limités",
                "Pas de tracing des workers",
                "Correlation avec logs faible"
            ],
            recommendations=[
                "Déployer Jaeger dans Docker",
                "Configurer le sampling rate",
                "Ajouter des spans manuels détaillés",
                "Intégrer tracing dans les workers",
                "Corréler traces et logs"
            ]
        )
        
        self.components.append(component)
    
    def _analyze_alerting_system(self):
        """Analyse le système d'alerting"""
        print("🚨 Analyse du système d'alerting...")
        
        component = MonitoringComponent(
            name="Alerting System",
            type="alerting",
            status="partial",
            description="Système d'alertes avec notification channels",
            files=[
                "app/monitoring/alerts.py"
            ],
            features=[
                "Gestion d'alertes basique",
                "Multiple channels (email, webhook, Slack)",
                "Severity levels",
                "Alert rules configurables",
                "Notification templates"
            ],
            gaps=[
                "Pas d'intégration Prometheus Alertmanager",
                "Pas de règles d'alerte prédéfinies",
                "Pas de dashboard d'alertes",
                "Pas de escalation automatique",
                "Pas de suppression de bruit"
            ],
            recommendations=[
                "Intégrer Prometheus Alertmanager",
                "Créer des règles d'alertes SLA",
                "Ajouter des dashboards d'alertes",
                "Implémenter l'alert escalation",
                "Ajouter le alert grouping"
            ]
        )
        
        self.components.append(component)
    
    def _analyze_dashboard_system(self):
        """Analyse le système de dashboards"""
        print("📈 Analyse du système de dashboards...")
        
        component = MonitoringComponent(
            name="Dashboard System",
            type="dashboard",
            status="missing",
            description="Dashboards de monitoring et de visualisation",
            files=[
                "app/ui.py",  # Streamlit dashboard basique
                "app/ui_quality.py"
            ],
            features=[
                "Dashboard Streamlit basique",
                "Métriques de qualité de code",
                "Visualisation simple",
                "Status checks basiques"
            ],
            gaps=[
                "Pas d'intégration Grafana",
                "Pas de dashboards techniques",
                "Pas de dashboards business",
                "Pas de visualisation temps réel",
                "Pas de drill-down capabilities"
            ],
            recommendations=[
                "Déployer Grafana",
                "Créer des dashboards techniques",
                "Ajouter des dashboards business",
                "Implémenter le temps réel",
                "Ajouter des drill-downs"
            ]
        )
        
        self.components.append(component)
    
    def _analyze_health_checks(self):
        """Analyse les health checks"""
        print("🏥 Analyse des health checks...")
        
        component = MonitoringComponent(
            name="Health Checks",
            type="health",
            status="partial",
            description="Health checks pour les services et dépendances",
            files=[
                "app/core/doctor.py",
                "worker_improved_v3.py"
            ],
            features=[
                "Health checks basiques",
                "Vérification des dépendances",
                "Status endpoints",
                "Métriques de santé",
                "Auto-diagnostic"
            ],
            gaps=[
                "Pas de health checks détaillés",
                "Pas de monitoring externe",
                "Pas de SLA monitoring",
                "Pas de synthetic transactions",
                "Pas de dependency health tracking"
            ],
            recommendations=[
                "Étendre les health checks",
                "Ajouter le monitoring externe",
                "Implémenter le SLA monitoring",
                "Ajouter des synthetic transactions",
                "Tracker la santé des dépendances"
            ]
        )
        
        self.components.append(component)
    
    def _analyze_infrastructure(self):
        """Analyse l'infrastructure de monitoring"""
        print("🏗️ Analyse de l'infrastructure...")
        
        component = MonitoringComponent(
            name="Infrastructure Monitoring",
            type="infrastructure",
            status="missing",
            description="Infrastructure de monitoring et d'observabilité",
            files=[
                "docker-compose.yml"
            ],
            features=[
                "Docker Compose basique",
                "Services Redis et Ollama",
                "Configuration réseau simple"
            ],
            gaps=[
                "Pas de stack monitoring déployée",
                "Pas de Prometheus configuré",
                "Pas de Grafana déployé",
                "Pas de ELK Stack",
                "Pas de Jaeger déployé"
            ],
            recommendations=[
                "Déployer la stack complète de monitoring",
                "Configurer Prometheus et Grafana",
                "Déployer ELK Stack",
                "Ajouter Jaeger",
                "Configurer le log aggregation"
            ]
        )
        
        self.components.append(component)
    
    def _calculate_global_metrics(self):
        """Calcule les métriques globales de monitoring"""
        total_components = len(self.components)
        implemented = len([c for c in self.components if c.status == "implemented"])
        partial = len([c for c in self.components if c.status == "partial"])
        missing = len([c for c in self.components if c.status == "missing"])
        
        maturity_score = (implemented * 100 + partial * 50 + missing * 0) / total_components
        
        self.analysis_results = {
            "summary": {
                "total_components": total_components,
                "implemented": implemented,
                "partial": partial,
                "missing": missing,
                "maturity_score": maturity_score,
                "analysis_date": datetime.now().isoformat()
            },
            "components": [
                {
                    "name": comp.name,
                    "type": comp.type,
                    "status": comp.status,
                    "features_count": len(comp.features),
                    "gaps_count": len(comp.gaps),
                    "recommendations_count": len(comp.recommendations)
                }
                for comp in self.components
            ],
            "detailed_components": [
                {
                    "name": comp.name,
                    "type": comp.type,
                    "status": comp.status,
                    "description": comp.description,
                    "files": comp.files,
                    "features": comp.features,
                    "gaps": comp.gaps,
                    "recommendations": comp.recommendations
                }
                for comp in self.components
            ],
            "priority_recommendations": self._get_priority_recommendations(),
            "implementation_plan": self._create_implementation_plan()
        }
    
    def _get_priority_recommendations(self) -> List[Dict[str, Any]]:
        """Génère les recommandations priorisées"""
        all_recommendations = []
        
        for comp in self.components:
            for rec in comp.recommendations:
                priority = self._calculate_recommendation_priority(comp, rec)
                all_recommendations.append({
                    "component": comp.name,
                    "recommendation": rec,
                    "priority": priority,
                    "estimated_effort": self._estimate_effort(rec)
                })
        
        # Trier par priorité
        all_recommendations.sort(key=lambda x: x["priority"], reverse=True)
        
        return all_recommendations[:15]  # Top 15 recommandations
    
    def _calculate_recommendation_priority(self, component: MonitoringComponent, recommendation: str) -> int:
        """Calcule la priorité d'une recommandation"""
        priority = 50  # Base
        
        # Priorité plus haute pour les composants critiques
        if component.name in ["Metrics System", "Logging System", "Health Checks"]:
            priority += 20
        
        # Priorité plus haute si le composant est manquant
        if component.status == "missing":
            priority += 15
        elif component.status == "partial":
            priority += 10
        
        # Mots-clés de priorité
        high_priority_keywords = ["sécurité", "sla", "critique", "production", "déploiement"]
        for keyword in high_priority_keywords:
            if keyword.lower() in recommendation.lower():
                priority += 10
        
        return min(priority, 100)
    
    def _estimate_effort(self, recommendation: str) -> str:
        """Estime l'effort pour une recommandation"""
        if "déployer" in recommendation.lower() or "configurer" in recommendation.lower():
            return "medium"
        elif "créer" in recommendation.lower() or "ajouter" in recommendation.lower():
            return "low"
        elif "implémenter" in recommendation.lower():
            return "high"
        else:
            return "medium"
    
    def _create_implementation_plan(self) -> Dict[str, Any]:
        """Crée un plan d'implémentation par phases"""
        phases = {
            "phase_1_foundation": {
                "name": "Phase 1: Fondations",
                "duration": "2-3 semaines",
                "components": ["Metrics System", "Logging System"],
                "tasks": [
                    "Déployer Prometheus",
                    "Standardiser les métriques",
                    "Configurer ELK Stack",
                    "Standardiser les logs"
                ]
            },
            "phase_2_observability": {
                "name": "Phase 2: Observabilité",
                "duration": "2-3 semaines",
                "components": ["Distributed Tracing", "Health Checks"],
                "tasks": [
                    "Déployer Jaeger",
                    "Étendre les health checks",
                    "Intégrer tracing et logs",
                    "Ajouter le SLA monitoring"
                ]
            },
            "phase_3_visualization": {
                "name": "Phase 3: Visualisation",
                "duration": "1-2 semaines",
                "components": ["Dashboard System"],
                "tasks": [
                    "Déployer Grafana",
                    "Créer des dashboards techniques",
                    "Ajouter des dashboards business",
                    "Implémenter le temps réel"
                ]
            },
            "phase_4_alerting": {
                "name": "Phase 4: Alerting",
                "duration": "1-2 semaines",
                "components": ["Alerting System"],
                "tasks": [
                    "Intégrer Alertmanager",
                    "Créer des règles d'alertes",
                    "Configurer les notifications",
                    "Implémenter l'escalation"
                ]
            }
        }
        
        return phases
    
    def generate_report(self) -> str:
        """Génère un rapport détaillé"""
        if not self.analysis_results:
            self.analyze_current_state()
        
        report = []
        report.append("# 📊 Rapport d'Analyse - Monitoring & Observabilité")
        report.append("=" * 60)
        
        # Résumé
        summary = self.analysis_results["summary"]
        report.append("\n## 📈 Résumé Exécutif")
        report.append(f"- **Score de Maturité**: {summary['maturity_score']:.1f}/100")
        report.append(f"- **Composants Implémentés**: {summary['implemented']}/{summary['total_components']}")
        report.append(f"- **Composants Partiels**: {summary['partial']}/{summary['total_components']}")
        report.append(f"- **Composants Manquants**: {summary['missing']}/{summary['total_components']}")
        
        # État actuel
        report.append("\n## 🔍 État Actuel par Composant")
        for comp in self.analysis_results["components"]:
            status_emoji = {"implemented": "✅", "partial": "⚠️", "missing": "❌"}[comp["status"]]
            report.append(f"- {status_emoji} **{comp['name']}**: {comp['status'].upper()}")
            report.append(f"  - Features: {comp['features_count']} | Gaps: {comp['gaps_count']}")
        
        # Recommandations prioritaires
        report.append("\n## 🎯 Recommandations Prioritaires")
        for i, rec in enumerate(self.analysis_results["priority_recommendations"][:10], 1):
            priority_emoji = "🔴" if rec["priority"] > 80 else "🟡" if rec["priority"] > 60 else "🟢"
            report.append(f"{i}. {priority_emoji} **{rec['recommendation']}** ({rec['component']})")
            report.append(f"   Effort: {rec['estimated_effort']} | Priorité: {rec['priority']}/100")
        
        # Plan d'implémentation
        report.append("\n## 🚀 Plan d'Implémentation")
        phases = self.analysis_results["implementation_plan"]
        for phase_key, phase in phases.items():
            report.append(f"\n### {phase['name']} ({phase['duration']})")
            for task in phase['tasks']:
                report.append(f"- {task}")
        
        return "\n".join(report)


def main():
    """Point d'entrée principal"""
    project_root = Path(".")
    analyzer = MonitoringAnalyzer(project_root)
    
    # Analyse
    results = analyzer.analyze_current_state()
    
    # Afficher les résultats
    print("\n" + "="*60)
    print("📊 RAPPORT DE MONITORING & OBSERVABILITÉ")
    print("="*60)
    
    summary = results["summary"]
    print(f"\n📈 Score de Maturité: {summary['maturity_score']:.1f}/100")
    print(f"✅ Implémentés: {summary['implemented']}")
    print(f"⚠️ Partiels: {summary['partial']}")
    print(f"❌ Manquants: {summary['missing']}")
    
    # État par composant
    print(f"\n🔍 État des Composants:")
    for comp in results["components"]:
        status_emoji = {"implemented": "✅", "partial": "⚠️", "missing": "❌"}[comp["status"]]
        print(f"  {status_emoji} {comp['name']}: {comp['status'].upper()}")
    
    # Top 5 recommandations
    print(f"\n🎯 Top 5 Recommandations:")
    for i, rec in enumerate(results["priority_recommendations"][:5], 1):
        priority_emoji = "🔴" if rec["priority"] > 80 else "🟡" if rec["priority"] > 60 else "🟢"
        print(f"  {i}. {priority_emoji} {rec['recommendation']}")
    
    # Générer le rapport détaillé
    report = analyzer.generate_report()
    
    # Sauvegarder le rapport
    report_path = project_root / "monitoring_analysis_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Sauvegarder les résultats JSON
    json_path = project_root / "monitoring_analysis.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Rapport détaillé: {report_path}")
    print(f"📊 Données JSON: {json_path}")
    
    # Évaluation
    if summary['maturity_score'] < 40:
        print(f"\n⚠️  Monitoring immature - Investissement requis")
    elif summary['maturity_score'] < 70:
        print(f"\n🟡 Monitoring partiel - Améliorations nécessaires")
    else:
        print(f"\n✅ Monitoring mature - Maintenir et optimiser")


if __name__ == "__main__":
    main()
