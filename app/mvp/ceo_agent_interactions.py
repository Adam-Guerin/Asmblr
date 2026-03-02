"""
CEO Agent Interaction Orchestrator
Le CEO module et contrôle toutes les interactions entre les agents.
Aucune interaction automatique - tout est contrôlé par le CEO.
"""

import json
from pathlib import Path
from typing import Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from loguru import logger
from app.core.config import Settings
from app.core.llm import LLMClient
from app.mvp.ceo_toolkit import CEOToolkit
from app.mvp.ceo_micromanagement import AgentType, CEOMicromanager


class InteractionType(Enum):
    """Types d'interactions entre agents"""
    COLLABORATION = "collaboration"  # Collaboration bidirectionnelle
    SEQUENTIAL = "sequential"  # Un agent envoie à l'autre
    PARALLEL = "parallel"  # Agents travaillent en parallèle
    REVIEW = "review"  # Un agent review le travail d'un autre
    VALIDATION = "validation"  # Un agent valide le travail d'un autre
    FEEDBACK = "feedback"  # Feedback d'un agent à un autre
    SYNC = "sync"  # Synchronisation entre agents
    BLOCKED = "blocked"  # Interaction bloquée par le CEO


class InteractionPriority(Enum):
    """Priorités d'interactions"""
    CRITICAL = "critical"  # Doit se produire immédiatement
    HIGH = "high"  # Priorité haute
    NORMAL = "normal"  # Priorité normale
    LOW = "low"  # Priorité basse
    OPTIONAL = "optional"  # Optionnel


@dataclass
class AgentInteraction:
    """Définition d'une interaction entre agents"""
    from_agent: AgentType
    to_agent: AgentType
    interaction_type: InteractionType
    priority: InteractionPriority = InteractionPriority.NORMAL
    allowed: bool = True
    conditions: list[str] = field(default_factory=list)
    data_requirements: dict[str, Any] = field(default_factory=dict)
    timing_constraints: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class InteractionFlow:
    """Définition d'un flux d'interactions"""
    name: str
    interactions: list[AgentInteraction]
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class InteractionExecution:
    """Exécution d'une interaction"""
    interaction: AgentInteraction
    status: str = "pending"  # pending, executing, completed, blocked, failed
    result: dict[str, Any] | None = None
    error: str | None = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class CEOAgentInteractionOrchestrator:
    """
    CEO Agent Interaction Orchestrator - Contrôle total des interactions
    
    Le CEO contrôle TOUTES les interactions entre agents:
    - Quels agents peuvent interagir
    - Comment ils interagissent
    - Quand ils interagissent
    - Quelles données sont partagées
    - Quelle est la priorité
    - Si l'interaction est autorisée
    
    Aucune interaction automatique - tout est orchestré par le CEO.
    """
    
    def __init__(
        self,
        settings: Settings,
        llm_client: LLMClient,
        toolkit: CEOToolkit,
        micromanager: CEOMicromanager,
        run_dir: Path
    ):
        self.settings = settings
        self.llm_client = llm_client
        self.toolkit = toolkit
        self.micromanager = micromanager
        self.run_dir = run_dir
        
        # Définitions des interactions
        self.interaction_rules: dict[tuple[AgentType, AgentType], AgentInteraction] = {}
        self.interaction_flows: dict[str, InteractionFlow] = {}
        
        # Historique des exécutions
        self.execution_history: list[InteractionExecution] = []
        
        # Statistiques
        self.interaction_stats: dict[str, Any] = {
            "total_interactions": 0,
            "completed": 0,
            "blocked": 0,
            "failed": 0,
            "by_type": {},
            "by_priority": {}
        }
    
    async def define_interaction_rules(
        self,
        topic: str,
        vision: str
    ):
        """
        Définit les règles d'interactions entre agents
        
        Le CEO décide quels agents peuvent interagir, comment et quand.
        """
        
        logger.info("🔗 CEO defining interaction rules between agents")
        
        rules_prompt = f"""
        EN TANT QUE CEO POUR "{topic}", DÉFINIS LES RÈGLES D'INTERACTIONS ENTRE AGENTS:
        
        Vision CEO: {vision}
        
        AGENTS: Researcher, Analyst, Product, Tech Lead, Growth, Brand
        
        POUR CHAQUE PAIRE D'AGENTS (from → to):
        
        1. **Interaction Type**:
           - collaboration: Collaboration bidirectionnelle
           - sequential: Un agent envoie à l'autre
           - parallel: Agents travaillent en parallèle
           - review: Un agent review le travail
           - validation: Un agent valide
           - feedback: Feedback
           - sync: Synchronisation
           - blocked: Interaction bloquée
        
        2. **Priority**: critical, high, normal, low, optional
        3. **Allowed**: true/false
        4. **Conditions**: Conditions pour l'interaction
        5. **Data Requirements**: Quelles données doivent être partagées
        6. **Timing Constraints**: Quand l'interaction doit se produire
        
        IMPORTANT:
        - Le CEO contrôle TOUTES les interactions
        - Aucune interaction automatique
        - Chaque interaction doit être justifiée
        - Prioriser les interactions critiques
        - Bloquer les interactions non nécessaires
        
        JSON structuré attendu avec règles pour chaque paire d'agents.
        """
        
        try:
            response = await self.llm_client.generate_async(rules_prompt)
            
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                rules_data = json.loads(json_match.group())
            else:
                rules_data = self._create_default_interaction_rules(topic, vision)
                
        except Exception as exc:
            logger.warning(f"Interaction rules creation failed, default: {exc}")
            rules_data = self._create_default_interaction_rules(topic, vision)
        
        # Créer les règles d'interactions
        for from_agent in AgentType:
            for to_agent in AgentType:
                if from_agent == to_agent:
                    continue
                
                key = f"{from_agent.value}_to_{to_agent.value}"
                if key in rules_data:
                    rule_data = rules_data[key]
                    
                    interaction = AgentInteraction(
                        from_agent=from_agent,
                        to_agent=to_agent,
                        interaction_type=InteractionType(rule_data.get("interaction_type", "sequential")),
                        priority=InteractionPriority(rule_data.get("priority", "normal")),
                        allowed=rule_data.get("allowed", True),
                        conditions=rule_data.get("conditions", []),
                        data_requirements=rule_data.get("data_requirements", {}),
                        timing_constraints=rule_data.get("timing_constraints"),
                        metadata=rule_data.get("metadata", {})
                    )
                    
                    self.interaction_rules[(from_agent, to_agent)] = interaction
                    
                    logger.info(
                        f"🔗 CEO defined interaction: {from_agent.value} → {to_agent.value} "
                        f"({interaction.interaction_type.value}, {interaction.priority.value})"
                    )
    
    def _create_default_interaction_rules(
        self,
        topic: str,
        vision: str
    ) -> dict[str, Any]:
        """Crée des règles d'interactions par défaut"""
        
        # Flux standard CEO: Researcher → Analyst → Product → Tech Lead → Growth → Brand
        return {
            "researcher_to_analyst": {
                "interaction_type": "sequential",
                "priority": "critical",
                "allowed": True,
                "conditions": ["Researcher output approved"],
                "data_requirements": {"market_data": True, "competitor_data": True},
                "timing_constraints": {"after": "researcher_completion"}
            },
            "analyst_to_product": {
                "interaction_type": "sequential",
                "priority": "critical",
                "allowed": True,
                "conditions": ["Analyst output approved"],
                "data_requirements": {"market_sizing": True, "opportunity_assessment": True},
                "timing_constraints": {"after": "analyst_completion"}
            },
            "product_to_tech_lead": {
                "interaction_type": "collaboration",
                "priority": "high",
                "allowed": True,
                "conditions": ["PRD approved"],
                "data_requirements": {"feature_requirements": True, "user_stories": True},
                "timing_constraints": {"after": "product_completion"}
            },
            "tech_lead_to_growth": {
                "interaction_type": "sequential",
                "priority": "normal",
                "allowed": True,
                "conditions": ["Tech stack approved"],
                "data_requirements": {"architecture": True, "implementation_plan": True},
                "timing_constraints": {"after": "tech_lead_completion"}
            },
            "growth_to_brand": {
                "interaction_type": "collaboration",
                "priority": "normal",
                "allowed": True,
                "conditions": ["Growth strategy approved"],
                "data_requirements": {"target_audience": True, "value_proposition": True},
                "timing_constraints": {"after": "growth_completion"}
            },
            # Interactions de review/validation
            "product_to_researcher": {
                "interaction_type": "review",
                "priority": "normal",
                "allowed": True,
                "conditions": ["PRD draft created"],
                "data_requirements": {"prd_document": True},
                "timing_constraints": {"during": "product_phase"}
            },
            "tech_lead_to_product": {
                "interaction_type": "validation",
                "priority": "high",
                "allowed": True,
                "conditions": ["Architecture designed"],
                "data_requirements": {"tech_constraints": True},
                "timing_constraints": {"during": "tech_lead_phase"}
            },
            # Interactions bloquées par défaut
            "brand_to_researcher": {
                "interaction_type": "blocked",
                "priority": "optional",
                "allowed": False,
                "conditions": [],
                "data_requirements": {},
                "timing_constraints": {}
            },
            "growth_to_researcher": {
                "interaction_type": "blocked",
                "priority": "optional",
                "allowed": False,
                "conditions": [],
                "data_requirements": {},
                "timing_constraints": {}
            }
        }
    
    async def create_interaction_flows(
        self,
        topic: str,
        vision: str
    ):
        """
        Crée des flux d'interactions orchestrés
        
        Le CEO définit des flux complets d'interactions entre agents.
        """
        
        logger.info("🌊 CEO creating interaction flows")
        
        flows_prompt = f"""
        EN TANT QUE CEO POUR "{topic}", CRÉE DES FLUX D'INTERACTIONS ORCHESTRÉS:
        
        Vision CEO: {vision}
        
        CRÉE 3-5 FLUX D'INTERACTIONS:
        
        1. **Primary Flow**: Flux principal de création
        2. **Review Flow**: Flux de review et validation
        3. **Optimization Flow**: Flux d'optimisation et amélioration
        4. **Sync Flow**: Flux de synchronisation
        5. **Emergency Flow**: Flux d'urgence
        
        Pour chaque flux:
        - Nom du flux
        - Description
        - Séquence d'interactions (from → to → type)
        - Dépendances entre interactions
        - Conditions d'exécution
        
        IMPORTANT:
        - Chaque flux doit être orchestré par le CEO
        - Aucune interaction automatique
        - Séquences claires et logiques
        - Dépendances explicites
        
        JSON structuré attendu.
        """
        
        try:
            response = await self.llm_client.generate_async(flows_prompt)
            
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                flows_data = json.loads(json_match.group())
            else:
                flows_data = self._create_default_interaction_flows(topic, vision)
                
        except Exception as exc:
            logger.warning(f"Interaction flows creation failed, default: {exc}")
            flows_data = self._create_default_interaction_flows(topic, vision)
        
        # Créer les flux d'interactions
        for flow_name, flow_data in flows_data.items():
            interactions = []
            
            for interaction_data in flow_data.get("interactions", []):
                from_agent = AgentType(interaction_data["from"])
                to_agent = AgentType(interaction_data["to"])
                
                # Récupérer ou créer l'interaction
                key = (from_agent, to_agent)
                if key in self.interaction_rules:
                    interaction = self.interaction_rules[key]
                else:
                    interaction = AgentInteraction(
                        from_agent=from_agent,
                        to_agent=to_agent,
                        interaction_type=InteractionType(interaction_data.get("type", "sequential")),
                        priority=InteractionPriority(interaction_data.get("priority", "normal")),
                        allowed=interaction_data.get("allowed", True)
                    )
                
                interactions.append(interaction)
            
            flow = InteractionFlow(
                name=flow_name,
                interactions=interactions,
                description=flow_data.get("description", ""),
                dependencies=flow_data.get("dependencies", []),
                metadata=flow_data.get("metadata", {})
            )
            
            self.interaction_flows[flow_name] = flow
            
            logger.info(f"🌊 CEO created flow: {flow_name} with {len(interactions)} interactions")
    
    def _create_default_interaction_flows(
        self,
        topic: str,
        vision: str
    ) -> dict[str, Any]:
        """Crée des flux d'interactions par défaut"""
        
        return {
            "primary_creation_flow": {
                "description": "Flux principal de création du MVP",
                "interactions": [
                    {"from": "researcher", "to": "analyst", "type": "sequential", "priority": "critical", "allowed": True},
                    {"from": "analyst", "to": "product", "type": "sequential", "priority": "critical", "allowed": True},
                    {"from": "product", "to": "tech_lead", "type": "collaboration", "priority": "high", "allowed": True},
                    {"from": "tech_lead", "to": "growth", "type": "sequential", "priority": "normal", "allowed": True},
                    {"from": "growth", "to": "brand", "type": "collaboration", "priority": "normal", "allowed": True}
                ],
                "dependencies": [],
                "metadata": {"type": "primary"}
            },
            "review_validation_flow": {
                "description": "Flux de review et validation",
                "interactions": [
                    {"from": "product", "to": "researcher", "type": "review", "priority": "normal", "allowed": True},
                    {"from": "tech_lead", "to": "product", "type": "validation", "priority": "high", "allowed": True},
                    {"from": "brand", "to": "product", "type": "validation", "priority": "normal", "allowed": True}
                ],
                "dependencies": ["primary_creation_flow"],
                "metadata": {"type": "review"}
            },
            "optimization_flow": {
                "description": "Flux d'optimisation et amélioration",
                "interactions": [
                    {"from": "analyst", "to": "growth", "type": "feedback", "priority": "normal", "allowed": True},
                    {"from": "tech_lead", "to": "product", "type": "feedback", "priority": "high", "allowed": True},
                    {"from": "brand", "to": "growth", "type": "collaboration", "priority": "normal", "allowed": True}
                ],
                "dependencies": ["primary_creation_flow"],
                "metadata": {"type": "optimization"}
            },
            "sync_flow": {
                "description": "Flux de synchronisation entre agents",
                "interactions": [
                    {"from": "product", "to": "tech_lead", "type": "sync", "priority": "normal", "allowed": True},
                    {"from": "growth", "to": "brand", "type": "sync", "priority": "normal", "allowed": True}
                ],
                "dependencies": ["primary_creation_flow"],
                "metadata": {"type": "sync"}
            },
            "emergency_flow": {
                "description": "Flux d'urgence pour corrections rapides",
                "interactions": [
                    {"from": "tech_lead", "to": "product", "type": "sequential", "priority": "critical", "allowed": True},
                    {"from": "product", "to": "tech_lead", "type": "sequential", "priority": "critical", "allowed": True}
                ],
                "dependencies": [],
                "metadata": {"type": "emergency"}
            }
        }
    
    async def execute_interaction(
        self,
        from_agent: AgentType,
        to_agent: AgentType,
        data: dict[str, Any] | None = None
    ) -> InteractionExecution:
        """
        Exécute une interaction entre agents
        
        Le CEO supervise et contrôle chaque interaction.
        """
        
        logger.info(f"🔗 CEO executing interaction: {from_agent.value} → {to_agent.value}")
        
        # Récupérer la règle d'interaction
        key = (from_agent, to_agent)
        if key not in self.interaction_rules:
            logger.warning(f"No interaction rule defined for {from_agent.value} → {to_agent.value}")
            return InteractionExecution(
                interaction=AgentInteraction(
                    from_agent=from_agent,
                    to_agent=to_agent,
                    interaction_type=InteractionType.BLOCKED,
                    priority=InteractionPriority.OPTIONAL,
                    allowed=False
                ),
                status="blocked",
                error="No interaction rule defined"
            )
        
        interaction = self.interaction_rules[key]
        
        # Vérifier si l'interaction est autorisée
        if not interaction.allowed:
            logger.warning(f"Interaction blocked by CEO: {from_agent.value} → {to_agent.value}")
            execution = InteractionExecution(
                interaction=interaction,
                status="blocked",
                error="Interaction blocked by CEO"
            )
            self.execution_history.append(execution)
            self.interaction_stats["blocked"] += 1
            return execution
        
        # Vérifier les conditions
        if interaction.conditions:
            conditions_met = await self._check_interaction_conditions(interaction, data)
            if not conditions_met:
                logger.warning(f"Interaction conditions not met: {from_agent.value} → {to_agent.value}")
                execution = InteractionExecution(
                    interaction=interaction,
                    status="blocked",
                    error="Interaction conditions not met"
                )
                self.execution_history.append(execution)
                self.interaction_stats["blocked"] += 1
                return execution
        
        # Exécuter l'interaction
        start_time = datetime.utcnow()
        
        try:
            # Simuler l'exécution de l'interaction
            result = await self._execute_interaction_logic(interaction, data)
            
            execution = InteractionExecution(
                interaction=interaction,
                status="completed",
                result=result,
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
            
            logger.info(f"✅ Interaction completed: {from_agent.value} → {to_agent.value}")
            
        except Exception as exc:
            execution = InteractionExecution(
                interaction=interaction,
                status="failed",
                error=str(exc),
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
            
            logger.error(f"❌ Interaction failed: {from_agent.value} → {to_agent.value} - {exc}")
        
        self.execution_history.append(execution)
        self.interaction_stats["total_interactions"] += 1
        
        if execution.status == "completed":
            self.interaction_stats["completed"] += 1
        elif execution.status == "failed":
            self.interaction_stats["failed"] += 1
        
        # Mettre à jour les statistiques par type
        interaction_type = interaction.interaction_type.value
        if interaction_type not in self.interaction_stats["by_type"]:
            self.interaction_stats["by_type"][interaction_type] = 0
        self.interaction_stats["by_type"][interaction_type] += 1
        
        # Mettre à jour les statistiques par priorité
        priority = interaction.priority.value
        if priority not in self.interaction_stats["by_priority"]:
            self.interaction_stats["by_priority"][priority] = 0
        self.interaction_stats["by_priority"][priority] += 1
        
        return execution
    
    async def _check_interaction_conditions(
        self,
        interaction: AgentInteraction,
        data: dict[str, Any] | None
    ) -> bool:
        """Vérifie si les conditions d'interaction sont remplies"""
        
        for condition in interaction.conditions:
            # Simuler la vérification des conditions
            # Dans une vraie implémentation, ceci vérifierait les conditions réelles
            if "approved" in condition:
                # Vérifier si l'agent source a son output approuvé
                if data and data.get("approved", False):
                    continue
                else:
                    return False
        
        return True
    
    async def _execute_interaction_logic(
        self,
        interaction: AgentInteraction,
        data: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Exécute la logique de l'interaction"""
        
        # Simuler l'exécution basée sur le type d'interaction
        if interaction.interaction_type == InteractionType.SEQUENTIAL:
            return {
                "type": "sequential",
                "data_transferred": data or {},
                "message": f"{interaction.from_agent.value} sent data to {interaction.to_agent.value}"
            }
        elif interaction.interaction_type == InteractionType.COLLABORATION:
            return {
                "type": "collaboration",
                "collaboration_data": data or {},
                "message": f"{interaction.from_agent.value} collaborating with {interaction.to_agent.value}"
            }
        elif interaction.interaction_type == InteractionType.REVIEW:
            return {
                "type": "review",
                "review_data": data or {},
                "message": f"{interaction.from_agent.value} reviewing {interaction.to_agent.value}'s work"
            }
        elif interaction.interaction_type == InteractionType.VALIDATION:
            return {
                "type": "validation",
                "validation_data": data or {},
                "message": f"{interaction.from_agent.value} validating {interaction.to_agent.value}'s work"
            }
        else:
            return {
                "type": interaction.interaction_type.value,
                "data": data or {},
                "message": f"{interaction.from_agent.value} → {interaction.to_agent.value} ({interaction.interaction_type.value})"
            }
    
    async def execute_interaction_flow(
        self,
        flow_name: str,
        data: dict[str, Any] | None = None
    ) -> list[InteractionExecution]:
        """
        Exécute un flux d'interactions complet
        
        Le CEO orchestre l'exécution séquentielle des interactions.
        """
        
        logger.info(f"🌊 CEO executing interaction flow: {flow_name}")
        
        if flow_name not in self.interaction_flows:
            logger.error(f"Flow not found: {flow_name}")
            return []
        
        flow = self.interaction_flows[flow_name]
        executions = []
        
        # Vérifier les dépendances
        for dependency in flow.dependencies:
            if dependency in self.interaction_flows:
                # Dans une vraie implémentation, vérifier si le flux dépendant est complété
                pass
        
        # Exécuter les interactions séquentiellement
        for interaction in flow.interactions:
            execution = await self.execute_interaction(
                from_agent=interaction.from_agent,
                to_agent=interaction.to_agent,
                data=data
            )
            
            executions.append(execution)
            
            # Si une interaction échoue, arrêter le flux
            if execution.status in ["blocked", "failed"]:
                logger.warning(f"Flow {flow_name} stopped at {interaction.from_agent.value} → {interaction.to_agent.value}")
                break
        
        logger.info(f"🌊 Flow {flow_name} completed with {len(executions)} interactions")
        
        return executions
    
    async def get_interaction_report(self) -> dict[str, Any]:
        """Génère un rapport des interactions"""
        
        report = {
            "total_interactions": self.interaction_stats["total_interactions"],
            "completed": self.interaction_stats["completed"],
            "blocked": self.interaction_stats["blocked"],
            "failed": self.interaction_stats["failed"],
            "success_rate": 0.0,
            "by_type": self.interaction_stats["by_type"],
            "by_priority": self.interaction_stats["by_priority"],
            "interaction_rules": {},
            "interaction_flows": {},
            "execution_history": [
                {
                    "from": e.interaction.from_agent.value,
                    "to": e.interaction.to_agent.value,
                    "type": e.interaction.interaction_type.value,
                    "status": e.status,
                    "execution_time": e.execution_time
                }
                for e in self.execution_history[-20:]  # Dernières 20 exécutions
            ]
        }
        
        # Calculer le taux de succès
        if report["total_interactions"] > 0:
            report["success_rate"] = (report["completed"] / report["total_interactions"]) * 100
        
        # Ajouter les règles d'interactions
        for key, interaction in self.interaction_rules.items():
            report["interaction_rules"][f"{key[0].value}_to_{key[1].value}"] = {
                "type": interaction.interaction_type.value,
                "priority": interaction.priority.value,
                "allowed": interaction.allowed,
                "conditions": interaction.conditions
            }
        
        # Ajouter les flux d'interactions
        for flow_name, flow in self.interaction_flows.items():
            report["interaction_flows"][flow_name] = {
                "description": flow.description,
                "interactions": len(flow.interactions),
                "dependencies": flow.dependencies
            }
        
        return report
    
    async def export_interaction_report(self) -> Path:
        """Exporte le rapport d'interactions"""
        
        report = await self.get_interaction_report()
        
        # Créer le fichier de rapport
        report_path = self.run_dir / "ceo_interaction_report.json"
        report_path.write_text(
            json.dumps(report, indent=2, default=str),
            encoding="utf-8"
        )
        
        # Créer un fichier lisible
        readable_report = await self._create_readable_interaction_report(report)
        readable_path = self.run_dir / "CEO_INTERACTION_REPORT.md"
        readable_path.write_text(readable_report, encoding="utf-8")
        
        logger.info(f"🔗 CEO interaction report exported to {report_path}")
        
        return report_path
    
    async def _create_readable_interaction_report(self, report: dict[str, Any]) -> str:
        """Crée un rapport lisible"""
        
        readable = f"""# CEO Interaction Report

## Overview
- Total Interactions: {report['total_interactions']}
- Completed: {report['completed']}
- Blocked: {report['blocked']}
- Failed: {report['failed']}
- Success Rate: {report['success_rate']:.1f}%

## By Type

"""
        
        for interaction_type, count in report["by_type"].items():
            readable += f"- {interaction_type.title()}: {count}\n"
        
        readable += "\n## By Priority\n\n"
        
        for priority, count in report["by_priority"].items():
            readable += f"- {priority.title()}: {count}\n"
        
        readable += "\n## Interaction Rules\n\n"
        
        for rule_key, rule in report["interaction_rules"].items():
            readable += f"""### {rule_key}
- Type: {rule['type']}
- Priority: {rule['priority']}
- Allowed: {rule['allowed']}
- Conditions: {', '.join(rule['conditions']) if rule['conditions'] else 'None'}

"""
        
        readable += "## Interaction Flows\n\n"
        
        for flow_name, flow in report["interaction_flows"].items():
            readable += f"""### {flow_name}
- Description: {flow['description']}
- Interactions: {flow['interactions']}
- Dependencies: {', '.join(flow['dependencies']) if flow['dependencies'] else 'None'}

"""
        
        readable += "## Recent Executions\n\n"
        
        for execution in report["execution_history"]:
            readable += f"- {execution['from']} → {execution['to']} ({execution['type']}): {execution['status']}\n"
        
        readable += """

---
*Generated by CEO Agent Interaction Orchestrator - Total Control*
"""
        
        return readable


# Fonction utilitaire pour créer un orchestrateur d'interactions
async def create_ceo_interaction_orchestrator(
    settings: Settings,
    llm_client: LLMClient,
    toolkit: CEOToolkit,
    micromanager: CEOMicromanager,
    run_dir: Path
) -> CEOAgentInteractionOrchestrator:
    """
    Crée un orchestrateur d'interactions CEO
    
    Args:
        settings: Configuration Asmblr
        llm_client: Client LLM
        toolkit: CEO Toolkit
        micromanager: CEO Micromanager
        run_dir: Répertoire de travail
        
    Returns:
        CEOAgentInteractionOrchestrator avec contrôle total des interactions
    """
    
    orchestrator = CEOAgentInteractionOrchestrator(
        settings=settings,
        llm_client=llm_client,
        toolkit=toolkit,
        micromanager=micromanager,
        run_dir=run_dir
    )
    
    logger.info("🔗 CEO Agent Interaction Orchestrator created - Total control over agent interactions")
    
    return orchestrator
