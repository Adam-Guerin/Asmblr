"""
Startup Success Optimizer
Optimise le pipeline pour maximiser le potentiel de succès de la startup créée.

Facteurs clés de succès d'une startup :
1. Product-Market Fit (PMF) - Produit que le marché veut vraiment
2. Validation rapide - Tester avec des vrais utilisateurs
3. KPIs mesurables - Métriques claires de succès
4. Feedback loop - Itérer rapidement basé sur les données
5. Priorisation - Se concentrer sur ce qui compte vraiment
6. MVP minimal - Livrer le minimum viable pour tester rapidement
7. Validation de la demande - S'assurer qu'il y a une vraie demande
8. Compétitivité - Avoir un avantage compétitif
9. Scalabilité - Être capable de scaler
10. Monétisation - Avoir un modèle économique viable
"""

import json
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from loguru import logger
from app.core.config import Settings
from app.core.llm import LLMClient


class SuccessFactor(Enum):
    """Facteurs de succès d'une startup"""
    PRODUCT_MARKET_FIT = "product_market_fit"
    DEMAND_VALIDATION = "demand_validation"
    COMPETITIVE_ADVANTAGE = "competitive_advantage"
    SCALABILITY = "scalability"
    MONETIZATION = "monetization"
    USER_ADOPTION = "user_adoption"
    RETENTION = "retention"
    GROWTH_POTENTIAL = "growth_potential"
    TECHNICAL_FEASIBILITY = "technical_feasibility"
    MARKET_TIMING = "market_timing"


class SuccessScore(Enum):
    """Niveaux de score de succès"""
    CRITICAL_FAILURE = 0  # < 30%
    FAILURE = 1  # 30-50%
    MARGINAL = 2  # 50-70%
    SUCCESS = 3  # 70-85%
    STRONG_SUCCESS = 4  # 85-95%
    EXCEPTIONAL = 5  # > 95%


@dataclass
class SuccessMetric:
    """Métrique de succès"""
    name: str
    description: str
    target_value: float
    current_value: float
    weight: float  # 0.0 à 1.0
    measurement: str
    status: str = "pending"


@dataclass
class PMFValidation:
    """Validation du Product-Market Fit"""
    market_size: float  # Taille du marché (en millions)
    market_growth: float  # Croissance du marché (%)
    pain_severity: float  # Sévérité du problème (0.0-1.0)
    solution_fit: float  # Adéquation de la solution (0.0-1.0)
    user_willingness_to_pay: float  # Volonté à payer (0.0-1.0)
    competitive_advantage: float  # Avantage compétitif (0.0-1.0)
    overall_score: float = 0.0
    
    def calculate_score(self) -> float:
        """Calcule le score PMF global"""
        # Pondération des facteurs PMF
        weights = {
            "market_size": 0.15,
            "market_growth": 0.10,
            "pain_severity": 0.25,
            "solution_fit": 0.25,
            "user_willingness_to_pay": 0.15,
            "competitive_advantage": 0.10
        }
        
        score = (
            self.market_size * weights["market_size"] +
            self.market_growth * weights["market_growth"] +
            self.pain_severity * weights["pain_severity"] +
            self.solution_fit * weights["solution_fit"] +
            self.user_willingness_to_pay * weights["user_willingness_to_pay"] +
            self.competitive_advantage * weights["competitive_advantage"]
        ) * 100
        
        self.overall_score = score
        return score


@dataclass
class StartupSuccessReport:
    """Rapport de succès de la startup"""
    pmf_validation: PMFValidation
    success_metrics: list[SuccessMetric]
    overall_success_score: float
    success_level: SuccessScore
    recommendations: list[str]
    critical_issues: list[str]
    strengths: list[str]
    improvement_areas: list[str]
    validation_kpis: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class StartupSuccessOptimizer:
    """
    Optimiseur de succès de startup
    
    Analyse et optimise le pipeline pour maximiser le potentiel de succès.
    """
    
    def __init__(
        self,
        settings: Settings,
        llm_client: LLMClient,
        run_dir: Path
    ):
        self.settings = settings
        self.llm_client = llm_client
        self.run_dir = run_dir
        
        # Métriques de succès par défaut
        self.default_metrics = self._create_default_metrics()
        
        # KPIs de validation
        self.validation_kpis = self._create_validation_kpis()
    
    def _create_default_metrics(self) -> list[SuccessMetric]:
        """Crée les métriques de succès par défaut"""
        
        return [
            SuccessMetric(
                name="product_market_fit",
                description="Adéquation produit-marché",
                target_value=0.85,
                current_value=0.0,
                weight=0.25,
                measurement="Score PMF global (0.0-1.0)"
            ),
            SuccessMetric(
                name="demand_validation",
                description="Validation de la demande",
                target_value=0.80,
                current_value=0.0,
                weight=0.15,
                measurement="Intention d'achat des utilisateurs"
            ),
            SuccessMetric(
                name="competitive_advantage",
                description="Avantage compétitif",
                target_value=0.75,
                current_value=0.0,
                weight=0.15,
                measurement="Différenciation par rapport aux concurrents"
            ),
            SuccessMetric(
                name="scalability",
                description="Scalabilité",
                target_value=0.80,
                current_value=0.0,
                weight=0.10,
                measurement="Capacité à scaler sans coûts linéaires"
            ),
            SuccessMetric(
                name="monetization",
                description="Monétisation",
                target_value=0.70,
                current_value=0.0,
                weight=0.15,
                measurement="Modèle économique viable"
            ),
            SuccessMetric(
                name="user_adoption",
                description="Adoption utilisateur",
                target_value=0.75,
                current_value=0.0,
                weight=0.10,
                measurement="Taux d'adoption des utilisateurs cibles"
            ),
            SuccessMetric(
                name="retention",
                description="Rétention",
                target_value=0.70,
                current_value=0.0,
                weight=0.10,
                measurement="Taux de rétention sur 30 jours"
            )
        ]
    
    def _create_validation_kpis(self) -> dict[str, Any]:
        """Crée les KPIs de validation"""
        
        return {
            "primary_kpis": {
                "conversion_rate": {
                    "target": "15%",
                    "current": "0%",
                    "measurement": "Sign-ups / visiteurs uniques"
                },
                "activation_rate": {
                    "target": "60%",
                    "current": "0%",
                    "measurement": "Utilisateurs qui complètent onboarding / sign-ups"
                },
                "retention_day_7": {
                    "target": "40%",
                    "current": "0%",
                    "measurement": "Utilisateurs actifs jour 7 / sign-ups"
                }
            },
            "secondary_kpis": {
                "engagement_time": {
                    "target": "2+ minutes",
                    "current": "0 min",
                    "measurement": "Temps moyen par session"
                },
                "feature_adoption": {
                    "target": "3+ fonctionnalités",
                    "current": "0",
                    "measurement": "Nombre de fonctionnalités utilisées par utilisateur"
                },
                "nps_score": {
                    "target": "+40",
                    "current": "N/A",
                    "measurement": "Net Promoter Score après 7 jours"
                }
            },
            "success_criteria": {
                "minimum_viable": "Conversion > 10% ET Activation > 40%",
                "target_achieved": "Conversion > 15% ET Activation > 60%",
                "exceptional": "Conversion > 25% ET Retention > 50%"
            },
            "tracking_setup": [
                "Google Analytics 4 installé",
                "Événements de conversion définis",
                "Dashboard KPI créé",
                "Alertes quotidiennes configurées"
            ]
        }
    
    async def analyze_startup_success(
        self,
        topic: str,
        market_analysis: dict[str, Any],
        prd: dict[str, Any],
        architecture: dict[str, Any]
    ) -> StartupSuccessReport:
        """
        Analyse le potentiel de succès de la startup
        
        Args:
            topic: Le sujet de la startup
            market_analysis: Analyse du marché
            prd: PRD du produit
            architecture: Architecture technique
            
        Returns:
            Rapport de succès de la startup
        """
        
        logger.info("📊 Startup Success Optimizer analyzing startup potential")
        
        # Valider le Product-Market Fit
        pmf_validation = await self._validate_product_market_fit(
            topic, market_analysis, prd
        )
        
        # Calculer les métriques de succès
        success_metrics = await self._calculate_success_metrics(
            pmf_validation, market_analysis, prd, architecture
        )
        
        # Calculer le score global de succès
        overall_score = self._calculate_overall_success_score(success_metrics)
        
        # Déterminer le niveau de succès
        success_level = self._determine_success_level(overall_score)
        
        # Générer les recommandations
        recommendations = await self._generate_recommendations(
            pmf_validation, success_metrics, success_level
        )
        
        # Identifier les problèmes critiques
        critical_issues = self._identify_critical_issues(success_metrics)
        
        # Identifier les forces
        strengths = self._identify_strengths(success_metrics)
        
        # Identifier les domaines d'amélioration
        improvement_areas = self._identify_improvement_areas(success_metrics)
        
        report = StartupSuccessReport(
            pmf_validation=pmf_validation,
            success_metrics=success_metrics,
            overall_success_score=overall_score,
            success_level=success_level,
            recommendations=recommendations,
            critical_issues=critical_issues,
            strengths=strengths,
            improvement_areas=improvement_areas,
            validation_kpis=self.validation_kpis
        )
        
        logger.info(
            f"📊 Startup success analysis complete: "
            f"Score {overall_score:.1f}% ({success_level.name})"
        )
        
        return report
    
    async def _validate_product_market_fit(
        self,
        topic: str,
        market_analysis: dict[str, Any],
        prd: dict[str, Any]
    ) -> PMFValidation:
        """Valide le Product-Market Fit"""
        
        logger.info("🎯 Validating Product-Market Fit")
        
        # Analyser le marché
        market_size = market_analysis.get("market_size", 0) / 100  # Normaliser 0-1
        market_growth = market_analysis.get("market_growth", 0) / 100  # Normaliser 0-1
        
        # Analyser la sévérité du problème
        pain_severity = prd.get("pain_severity", 0.5)
        
        # Analyser l'adéquation de la solution
        solution_fit = prd.get("solution_fit", 0.5)
        
        # Analyser la volonté à payer
        willingness_to_pay = prd.get("willingness_to_pay", 0.5)
        
        # Analyser l'avantage compétitif
        competitive_advantage = prd.get("competitive_advantage", 0.5)
        
        pmf_validation = PMFValidation(
            market_size=market_size,
            market_growth=market_growth,
            pain_severity=pain_severity,
            solution_fit=solution_fit,
            user_willingness_to_pay=willingness_to_pay,
            competitive_advantage=competitive_advantage
        )
        
        pmf_validation.calculate_score()
        
        logger.info(f"🎯 PMF Score: {pmf_validation.overall_score:.1f}%")
        
        return pmf_validation
    
    async def _calculate_success_metrics(
        self,
        pmf_validation: PMFValidation,
        market_analysis: dict[str, Any],
        prd: dict[str, Any],
        architecture: dict[str, Any]
    ) -> list[SuccessMetric]:
        """Calcule les métriques de succès"""
        
        metrics = []
        
        for default_metric in self.default_metrics:
            metric = SuccessMetric(
                name=default_metric.name,
                description=default_metric.description,
                target_value=default_metric.target_value,
                current_value=0.0,
                weight=default_metric.weight,
                measurement=default_metric.measurement
            )
            
            # Calculer la valeur actuelle basée sur les données
            if metric.name == "product_market_fit":
                metric.current_value = pmf_validation.overall_score / 100
            elif metric.name == "demand_validation":
                metric.current_value = pmf_validation.user_willingness_to_pay
            elif metric.name == "competitive_advantage":
                metric.current_value = pmf_validation.competitive_advantage
            elif metric.name == "scalability":
                metric.current_value = architecture.get("scalability_score", 0.5)
            elif metric.name == "monetization":
                metric.current_value = prd.get("monetization_score", 0.5)
            elif metric.name == "user_adoption":
                metric.current_value = prd.get("adoption_score", 0.5)
            elif metric.name == "retention":
                metric.current_value = prd.get("retention_score", 0.5)
            
            # Déterminer le statut
            if metric.current_value >= metric.target_value:
                metric.status = "achieved"
            elif metric.current_value >= metric.target_value * 0.8:
                metric.status = "on_track"
            elif metric.current_value >= metric.target_value * 0.6:
                metric.status = "needs_improvement"
            else:
                metric.status = "critical"
            
            metrics.append(metric)
        
        return metrics
    
    def _calculate_overall_success_score(self, metrics: list[SuccessMetric]) -> float:
        """Calcule le score global de succès"""
        
        weighted_sum = sum(
            metric.current_value * metric.weight
            for metric in metrics
        )
        
        return weighted_sum * 100
    
    def _determine_success_level(self, score: float) -> SuccessScore:
        """Détermine le niveau de succès"""
        
        if score < 30:
            return SuccessScore.CRITICAL_FAILURE
        elif score < 50:
            return SuccessScore.FAILURE
        elif score < 70:
            return SuccessScore.MARGINAL
        elif score < 85:
            return SuccessScore.SUCCESS
        elif score < 95:
            return SuccessScore.STRONG_SUCCESS
        else:
            return SuccessScore.EXCEPTIONAL
    
    async def _generate_recommendations(
        self,
        pmf_validation: PMFValidation,
        metrics: list[SuccessMetric],
        success_level: SuccessScore
    ) -> list[str]:
        """Génère des recommandations pour améliorer le succès"""
        
        recommendations = []
        
        # Recommandations basées sur les métriques critiques
        critical_metrics = [m for m in metrics if m.status == "critical"]
        
        for metric in critical_metrics:
            if metric.name == "product_market_fit":
                recommendations.append(
                    "⚠️ PMF critique: Revoir le problème et la solution. "
                    "Le marché n'est pas prêt ou la solution n'est pas adaptée."
                )
            elif metric.name == "demand_validation":
                recommendations.append(
                    "⚠️ Demande non validée: Tester avec des utilisateurs réels "
                    "avant de continuer. Faire des interviews utilisateurs."
                )
            elif metric.name == "competitive_advantage":
                recommendations.append(
                    "⚠️ Pas d'avantage compétitif: Identifier un USP unique. "
                    "Comment se différencier des concurrents?"
                )
            elif metric.name == "scalability":
                recommendations.append(
                    "⚠️ Scalabilité faible: Revoir l'architecture. "
                    "Peut-on scaler sans coûts linéaires?"
                )
            elif metric.name == "monetization":
                recommendations.append(
                    "⚠️ Monétisation non viable: Repenser le modèle économique. "
                    "Comment générer des revenus?"
                )
        
        # Recommandations basées sur le niveau de succès
        if success_level == SuccessScore.CRITICAL_FAILURE:
            recommendations.append(
                "🚨 ÉCHEC CRITIQUE: Le projet a peu de chances de succès. "
                "Revoir la stratégie ou pivoter."
            )
        elif success_level == SuccessScore.FAILURE:
            recommendations.append(
                "⚠️ ÉCHEC PROBABLE: Le projet a des problèmes majeurs. "
                "Corriger les problèmes critiques avant de continuer."
            )
        elif success_level == SuccessScore.MARGINAL:
            recommendations.append(
                "⚡ POTENTIEL MARGINAL: Le projet a du potentiel mais nécessite "
                "des améliorations significatives."
            )
        elif success_level == SuccessScore.SUCCESS:
            recommendations.append(
                "✅ SUCCÈS: Le projet a un bon potentiel. "
                "Continuer à optimiser et valider."
            )
        elif success_level == SuccessScore.STRONG_SUCCESS:
            recommendations.append(
                "🚀 SUCCÈS FORT: Le projet a un excellent potentiel. "
                "Accélérer le développement et la validation."
            )
        elif success_level == SuccessScore.EXCEPTIONAL:
            recommendations.append(
                "🏆 SUCCÈS EXCEPTIONNEL: Le projet a un potentiel exceptionnel. "
                "Maximiser l'exécution et scaler rapidement."
            )
        
        return recommendations
    
    def _identify_critical_issues(self, metrics: list[SuccessMetric]) -> list[str]:
        """Identifie les problèmes critiques"""
        
        return [
            f"{metric.name}: {metric.current_value:.1f}% (target: {metric.target_value:.1f}%)"
            for metric in metrics
            if metric.status == "critical"
        ]
    
    def _identify_strengths(self, metrics: list[SuccessMetric]) -> list[str]:
        """Identifie les forces"""
        
        return [
            f"{metric.name}: {metric.current_value:.1f}%"
            for metric in metrics
            if metric.status == "achieved"
        ]
    
    def _identify_improvement_areas(self, metrics: list[SuccessMetric]) -> list[str]:
        """Identifie les domaines d'amélioration"""
        
        return [
            f"{metric.name}: {metric.current_value:.1f}% (target: {metric.target_value:.1f}%)"
            for metric in metrics
            if metric.status in ["needs_improvement", "on_track"]
        ]
    
    async def export_success_report(self, report: StartupSuccessReport) -> Path:
        """Exporte le rapport de succès"""
        
        # Créer le fichier JSON
        report_path = self.run_dir / "startup_success_report.json"
        report_data = {
            "overall_success_score": report.overall_success_score,
            "success_level": report.success_level.name,
            "pmf_validation": {
                "score": report.pmf_validation.overall_score,
                "market_size": report.pmf_validation.market_size,
                "market_growth": report.pmf_validation.market_growth,
                "pain_severity": report.pmf_validation.pain_severity,
                "solution_fit": report.pmf_validation.solution_fit,
                "user_willingness_to_pay": report.pmf_validation.user_willingness_to_pay,
                "competitive_advantage": report.pmf_validation.competitive_advantage
            },
            "success_metrics": [
                {
                    "name": m.name,
                    "description": m.description,
                    "target_value": m.target_value,
                    "current_value": m.current_value,
                    "weight": m.weight,
                    "measurement": m.measurement,
                    "status": m.status
                }
                for m in report.success_metrics
            ],
            "recommendations": report.recommendations,
            "critical_issues": report.critical_issues,
            "strengths": report.strengths,
            "improvement_areas": report.improvement_areas,
            "validation_kpis": report.validation_kpis,
            "timestamp": report.timestamp.isoformat()
        }
        
        report_path.write_text(
            json.dumps(report_data, indent=2, default=str),
            encoding="utf-8"
        )
        
        # Créer le rapport lisible
        readable_report = await self._create_readable_report(report)
        readable_path = self.run_dir / "STARTUP_SUCCESS_REPORT.md"
        readable_path.write_text(readable_report, encoding="utf-8")
        
        logger.info(f"📊 Startup success report exported to {report_path}")
        
        return report_path
    
    async def _create_readable_report(self, report: StartupSuccessReport) -> str:
        """Crée un rapport lisible"""
        
        readable = f"""# Startup Success Report

## Executive Summary

**Overall Success Score**: {report.overall_success_score:.1f}%
**Success Level**: {report.success_level.name.replace('_', ' ').title()}

---

## Product-Market Fit Validation

**PMF Score**: {report.pmf_validation.overall_score:.1f}%

- **Market Size**: {report.pmf_validation.market_size:.1f}
- **Market Growth**: {report.pmf_validation.market_growth:.1f}
- **Pain Severity**: {report.pmf_validation.pain_severity:.1f}
- **Solution Fit**: {report.pmf_validation.solution_fit:.1f}
- **User Willingness to Pay**: {report.pmf_validation.user_willingness_to_pay:.1f}
- **Competitive Advantage**: {report.pmf_validation.competitive_advantage:.1f}

---

## Success Metrics

"""
        
        for metric in report.success_metrics:
            status_emoji = {
                "achieved": "✅",
                "on_track": "🟢",
                "needs_improvement": "🟡",
                "critical": "🔴"
            }.get(metric.status, "⚪")
            
            readable += f"""### {metric.name}
{status_emoji} **Status**: {metric.status}
- **Target**: {metric.target_value:.1f}
- **Current**: {metric.current_value:.1f}
- **Weight**: {metric.weight:.1f}
- **Measurement**: {metric.measurement}

"""
        
        readable += """---

## Critical Issues

"""
        
        for issue in report.critical_issues:
            readable += f"- 🔴 {issue}\n"
        
        readable += "\n## Strengths\n\n"
        
        for strength in report.strengths:
            readable += f"- ✅ {strength}\n"
        
        readable += "\n## Improvement Areas\n\n"
        
        for area in report.improvement_areas:
            readable += f"- 🟡 {area}\n"
        
        readable += "\n## Recommendations\n\n"
        
        for recommendation in report.recommendations:
            readable += f"{recommendation}\n\n"
        
        readable += """---

## Validation KPIs

### Primary KPIs

"""
        
        for kpi_name, kpi_data in report.validation_kpis["primary_kpis"].items():
            readable += f"""- **{kpi_name}**: {kpi_data["current"]} / {kpi_data["target"]}
  - Measurement: {kpi_data["measurement"]}

"""
        
        readable += "### Secondary KPIs\n\n"
        
        for kpi_name, kpi_data in report.validation_kpis["secondary_kpis"].items():
            readable += f"""- **{kpi_name}**: {kpi_data["current"]} / {kpi_data["target"]}
  - Measurement: {kpi_data["measurement"]}

"""
        
        readable += "### Success Criteria\n\n"
        
        for criteria_name, criteria_value in report.validation_kpis["success_criteria"].items():
            readable += f"- **{criteria_name}**: {criteria_value}\n"
        
        readable += "\n### Tracking Setup\n\n"
        
        for setup_item in report.validation_kpis["tracking_setup"]:
            readable += f"- {setup_item}\n"
        
        readable += """

---

*Generated by Startup Success Optimizer - Maximizing Startup Potential*
"""
        
        return readable


# Fonction utilitaire pour créer un optimiseur
async def create_startup_success_optimizer(
    settings: Settings,
    llm_client: LLMClient,
    run_dir: Path
) -> StartupSuccessOptimizer:
    """
    Crée un optimiseur de succès de startup
    
    Args:
        settings: Configuration Asmblr
        llm_client: Client LLM
        run_dir: Répertoire de travail
        
    Returns:
        StartupSuccessOptimizer pour maximiser le potentiel de succès
    """
    
    optimizer = StartupSuccessOptimizer(
        settings=settings,
        llm_client=llm_client,
        run_dir=run_dir
    )
    
    logger.info("📊 Startup Success Optimizer created - Maximizing startup potential")
    
    return optimizer
