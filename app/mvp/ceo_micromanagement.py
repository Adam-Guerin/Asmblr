"""
CEO Micromanagement System
Le CEO micromane ses agents pour s'assurer qu'ils font exactement ce qu'il veut.
Aucune autonomie, contrôle total, supervision directe.
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


class AgentType(Enum):
    """Types d'agents que le CEO micromane"""
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    PRODUCT = "product"
    TECH_LEAD = "tech_lead"
    GROWTH = "growth"
    BRAND = "brand"


class ApprovalStatus(Enum):
    """Statuts d'approbation CEO"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUIRED = "revision_required"
    FORCE_APPROVED = "force_approved"


@dataclass
class AgentInstruction:
    """Instruction CEO spécifique pour un agent"""
    agent_type: AgentType
    instruction: str
    constraints: list[str] = field(default_factory=list)
    required_outputs: list[str] = field(default_factory=list)
    forbidden_outputs: list[str] = field(default_factory=list)
    tone: str = "strict"
    deadline: str | None = None


@dataclass
class AgentOutput:
    """Output d'un agent"""
    agent_type: AgentType
    output: Any
    timestamp: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    ceo_feedback: str | None = None
    revisions: int = 0


@dataclass
class MicromanagementSession:
    """Session de micromanagement CEO"""
    topic: str
    agent_instructions: dict[AgentType, AgentInstruction] = field(default_factory=dict)
    agent_outputs: dict[AgentType, list[AgentOutput]] = field(default_factory=dict)
    approval_decisions: dict[AgentType, ApprovalStatus] = field(default_factory=dict)
    micromanagement_log: list[str] = field(default_factory=list)


class CEOMicromanager:
    """
    CEO Micromanager - Contrôle total sur les agents
    
    Le CEO ne laisse rien au hasard. Il:
    - Donne des instructions ultra-spécifiques à chaque agent
    - Supervise chaque output en temps réel
    - Force les agents à suivre exactement sa vision
    - Révise et corrige jusqu'à satisfaction
    - Aucune autonomie laissée aux agents
    """
    
    def __init__(
        self,
        settings: Settings,
        llm_client: LLMClient,
        toolkit: CEOToolkit,
        run_dir: Path
    ):
        self.settings = settings
        self.llm_client = llm_client
        self.toolkit = toolkit
        self.run_dir = run_dir
        self.session: MicromanagementSession | None = None
        
    async def start_micromanagement_session(
        self,
        topic: str,
        vision: str,
        risk_level: str = "EXTREME"
    ) -> MicromanagementSession:
        """
        Démarre une session de micromanagement CEO
        
        Le CEO définit des instructions ultra-spécifiques pour chaque agent
        pour s'assurer qu'ils font exactement ce qu'il veut.
        """
        
        logger.info(f"🎯 CEO MICROMANAGEMENT STARTED: {topic}")
        
        self.session = MicromanagementSession(topic=topic)
        
        # Créer des instructions spécifiques pour chaque agent
        await self._create_agent_instructions(topic, vision, risk_level)
        
        # Logger le début de la session
        self.session.micromanagement_log.append(
            f"CEO micromanagement session started for: {topic}"
        )
        
        return self.session
    
    async def _create_agent_instructions(
        self,
        topic: str,
        vision: str,
        risk_level: str
    ):
        """Crée des instructions ultra-spécifiques pour chaque agent"""
        
        instructions_prompt = f"""
        EN TANT QUE CEO POUR "{topic}", CRÉE DES INSTRUCTIONS ULTRA-SPECIFIQUES POUR CHAQUE AGENT:
        
        Vision CEO: {vision}
        Risk Level: {risk_level}
        
        POUR CHAQUE AGENT (Researcher, Analyst, Product, Tech Lead, Growth, Brand):
        
        1. **Instruction Spécifique**: Ce que l'agent DOIT faire exactement
        2. **Contraintes**: Ce que l'agent NE DOIT PAS faire
        3. **Outputs Requis**: Ce que l'agent DOIT produire
        4. **Outputs Interdits**: Ce que l'agent NE DOIT PAS produire
        5. **Tone**: Comment l'agent doit communiquer (strict, direct, etc.)
        
        IMPORTANT:
        - Aucune autonomie laissée aux agents
        - Instructions ultra-spécifiques et détaillées
        - Contraintes strictes pour éviter les dérives
        - Outputs formatés exactement comme le CEO veut
        - Tone agressif et direct
        
        JSON structuré attendu avec instructions pour chaque agent.
        """
        
        try:
            response = await self.llm_client.generate_async(instructions_prompt)
            
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                instructions_data = json.loads(json_match.group())
            else:
                instructions_data = self._create_fallback_instructions(topic, vision)
                
        except Exception as exc:
            logger.warning(f"Instructions CEO échouées, fallback: {exc}")
            instructions_data = self._create_fallback_instructions(topic, vision)
        
        # Créer des instructions pour chaque agent
        for agent_type in AgentType:
            if agent_type.value in instructions_data:
                agent_data = instructions_data[agent_type.value]
                
                instruction = AgentInstruction(
                    agent_type=agent_type,
                    instruction=agent_data.get("instruction", ""),
                    constraints=agent_data.get("constraints", []),
                    required_outputs=agent_data.get("required_outputs", []),
                    forbidden_outputs=agent_data.get("forbidden_outputs", []),
                    tone=agent_data.get("tone", "strict"),
                    deadline=agent_data.get("deadline")
                )
                
                self.session.agent_instructions[agent_type] = instruction
                
                logger.info(f"📋 CEO instruction for {agent_type.value}: {instruction.instruction[:50]}...")
    
    def _create_fallback_instructions(
        self,
        topic: str,
        vision: str
    ) -> dict[str, Any]:
        """Instructions fallback si tout échoue"""
        
        return {
            "researcher": {
                "instruction": f"Recherche approfondie sur {topic} avec focus sur la vision CEO: {vision}",
                "constraints": ["Pas de généralités", "Données spécifiques uniquement", "Sources vérifiées"],
                "required_outputs": ["Market analysis", "Competitor analysis", "ICP definition"],
                "forbidden_outputs": ["Vague statements", "Unverified claims"],
                "tone": "strict"
            },
            "analyst": {
                "instruction": f"Analyse critique de {topic} basée sur la vision CEO",
                "constraints": ["Pas de biais positifs", "Analyse objective", "Données quantitatives"],
                "required_outputs": ["Market sizing", "Competitor scoring", "Opportunity assessment"],
                "forbidden_outputs": ["Optimistic assumptions", "Unsubstantiated claims"],
                "tone": "critical"
            },
            "product": {
                "instruction": f"PRD pour {topic} aligné avec la vision CEO: {vision}",
                "constraints": ["Features CEO-level uniquement", "Pas de features superflues", "Priorité absolue"],
                "required_outputs": ["PRD document", "Feature prioritization", "User stories"],
                "forbidden_outputs": ["Nice-to-have features", "Vague requirements"],
                "tone": "strategic"
            },
            "tech_lead": {
                "instruction": f"Architecture technique pour {topic} optimisée pour la vision CEO",
                "constraints": ["Technologies modernes uniquement", "Scalabilité maximale", "Performance prioritaire"],
                "required_outputs": ["Tech stack", "Architecture diagram", "Implementation plan"],
                "forbidden_outputs": ["Legacy technologies", "Over-engineering"],
                "tone": "technical"
            },
            "growth": {
                "instruction": f"Stratégie growth pour {topic} alignée avec la vision CEO",
                "constraints": ["Stratégies agressives uniquement", "ROI mesurable", "Scalabilité"],
                "required_outputs": ["Growth channels", "Metrics", "Budget allocation"],
                "forbidden_outputs": ["Conservative approaches", "Unmeasurable tactics"],
                "tone": "aggressive"
            },
            "brand": {
                "instruction": f"Identité de marque pour {topic} qui reflète la vision CEO: {vision}",
                "constraints": ["Positionnement audacieux uniquement", "Pas de compromis", "Impact maximal"],
                "required_outputs": ["Brand guidelines", "Visual identity", "Messaging"],
                "forbidden_outputs": ["Safe approaches", "Generic branding"],
                "tone": "bold"
            }
        }
    
    async def supervise_agent_output(
        self,
        agent_type: AgentType,
        output: Any
    ) -> AgentOutput:
        """
        Supervise l'output d'un agent et décide de l'approbation
        
        Le CEO examine chaque output et décide:
        - APPROVED: Output parfait, continue
        - REJECTED: Output inacceptable, refaire
        - REVISION_REQUIRED: Output partiel, réviser
        - FORCE_APPROVED: Output acceptable malgré défauts (CEO pressé)
        """
        
        logger.info(f"👀 CEO supervising output from {agent_type.value}")
        
        # Enregistrer l'output
        agent_output = AgentOutput(
            agent_type=agent_type,
            output=output,
            timestamp=datetime.utcnow()
        )
        
        # Récupérer l'instruction CEO pour cet agent
        instruction = self.session.agent_instructions.get(agent_type)
        
        if not instruction:
            logger.warning(f"No CEO instruction for {agent_type.value}, force approving")
            agent_output.status = ApprovalStatus.FORCE_APPROVED
            self._record_agent_output(agent_output)
            return agent_output
        
        # Évaluer l'output selon les instructions CEO
        evaluation = await self._evaluate_agent_output(output, instruction)
        
        # Décider de l'approbation
        if evaluation["meets_all_requirements"]:
            agent_output.status = ApprovalStatus.APPROVED
            logger.info(f"✅ CEO APPROVED output from {agent_type.value}")
        elif evaluation["meets_minimum"]:
            agent_output.status = ApprovalStatus.FORCE_APPROVED
            agent_output.ceo_feedback = "Acceptable but could be better. Proceeding."
            logger.info(f"⚡ CEO FORCE APPROVED output from {agent_type.value}")
        elif evaluation["needs_revision"]:
            agent_output.status = ApprovalStatus.REVISION_REQUIRED
            agent_output.ceo_feedback = evaluation["feedback"]
            agent_output.revisions += 1
            logger.warning(f"🔄 CEO REVISION REQUIRED for {agent_type.value}: {evaluation['feedback']}")
        else:
            agent_output.status = ApprovalStatus.REJECTED
            agent_output.ceo_feedback = evaluation["feedback"]
            logger.error(f"❌ CEO REJECTED output from {agent_type.value}: {evaluation['feedback']}")
        
        self._record_agent_output(agent_output)
        
        return agent_output
    
    async def _evaluate_agent_output(
        self,
        output: Any,
        instruction: AgentInstruction
    ) -> dict[str, Any]:
        """Évalue l'output d'un agent selon les instructions CEO"""
        
        evaluation_prompt = f"""
        EN TANT QUE CEO, ÉVALUE CET OUTPUT D'AGENT:
        
        Instruction CEO: {instruction.instruction}
        Contraintes: {instruction.constraints}
        Outputs Requis: {instruction.required_outputs}
        Outputs Interdits: {instruction.forbidden_outputs}
        
        Output à évaluer: {str(output)[:2000]}
        
        CRITÈRES D'ÉVALUATION:
        
        1. **Meets All Requirements**: Output parfait, tous les requis satisfaits
        2. **Meets Minimum**: Output acceptable mais peut être amélioré
        3. **Needs Revision**: Output partiel, révisions nécessaires
        4. **Rejected**: Output inacceptable, refaire complètement
        
        Pour chaque critère:
        - Pourquoi ce statut
        - Feedback spécifique
        - Ce qui doit être corrigé (si applicable)
        
        JSON structuré attendu.
        """
        
        try:
            response = await self.llm_client.generate_async(evaluation_prompt)
            
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group())
            else:
                evaluation = self._create_fallback_evaluation(output, instruction)
                
        except Exception as exc:
            logger.warning(f"Évaluation CEO échouée, fallback: {exc}")
            evaluation = self._create_fallback_evaluation(output, instruction)
        
        return evaluation
    
    def _create_fallback_evaluation(
        self,
        output: Any,
        instruction: AgentInstruction
    ) -> dict[str, Any]:
        """Évaluation fallback si tout échoue"""
        
        output_str = str(output)
        
        # Vérifier si les outputs requis sont présents
        required_present = all(
            req.lower() in output_str.lower()
            for req in instruction.required_outputs
        )
        
        # Vérifier si les outputs interdits sont absents
        forbidden_absent = all(
            forbid.lower() not in output_str.lower()
            for forbid in instruction.forbidden_outputs
        )
        
        if required_present and forbidden_absent:
            return {
                "meets_all_requirements": True,
                "meets_minimum": True,
                "needs_revision": False,
                "feedback": "Output meets all CEO requirements. Excellent."
            }
        elif required_present:
            return {
                "meets_all_requirements": False,
                "meets_minimum": True,
                "needs_revision": False,
                "feedback": "Output acceptable but could be improved."
            }
        else:
            return {
                "meets_all_requirements": False,
                "meets_minimum": False,
                "needs_revision": True,
                "feedback": "Output does not meet CEO requirements. Revision needed."
            }
    
    def _record_agent_output(self, agent_output: AgentOutput):
        """Enregistre l'output d'un agent"""
        
        if agent_output.agent_type not in self.session.agent_outputs:
            self.session.agent_outputs[agent_output.agent_type] = []
        
        self.session.agent_outputs[agent_output.agent_type].append(agent_output)
        
        # Logger dans la session
        log_entry = (
            f"Agent {agent_output.agent_type.value} output: "
            f"{agent_output.status.value} - "
            f"Revisions: {agent_output.revisions}"
        )
        self.session.micromanagement_log.append(log_entry)
    
    async def force_agent_revision(
        self,
        agent_type: AgentType,
        feedback: str
    ) -> AgentInstruction:
        """
        Force un agent à réviser son output
        
        Le CEO donne un feedback spécifique et l'agent doit réviser
        exactement selon les instructions CEO.
        """
        
        logger.info(f"🔄 CEO FORCING REVISION for {agent_type.value}: {feedback}")
        
        # Récupérer l'instruction existante
        instruction = self.session.agent_instructions.get(agent_type)
        
        if not instruction:
            logger.error(f"No instruction for {agent_type.value}")
            return None
        
        # Créer une instruction de révision
        revision_prompt = f"""
        EN TANT QUE CEO, CRÉE UNE INSTRUCTION DE RÉVISION POUR L'AGENT {agent_type.value}:
        
        Instruction Originale: {instruction.instruction}
        Contraintes: {instruction.constraints}
        Outputs Requis: {instruction.required_outputs}
        
        Feedback CEO: {feedback}
        
        NOUVELLE INSTRUCTION DE RÉVISION:
        - Ce que l'agent a mal fait
        - Ce qu'il doit corriger spécifiquement
        - Comment il doit corriger
        - Nouvelles contraintes si nécessaires
        
        Sois direct et précis. L'agent doit comprendre exactement quoi corriger.
        JSON structuré attendu.
        """
        
        try:
            response = await self.llm_client.generate_async(revision_prompt)
            
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                revision_data = json.loads(json_match.group())
            else:
                revision_data = {"instruction": feedback}
                
        except Exception as exc:
            logger.warning(f"Révision CEO échouée, fallback: {exc}")
            revision_data = {"instruction": feedback}
        
        # Mettre à jour l'instruction
        instruction.instruction = revision_data.get("instruction", feedback)
        
        # Logger la révision
        log_entry = f"CEO forced revision for {agent_type.value}: {feedback}"
        self.session.micromanagement_log.append(log_entry)
        
        return instruction
    
    async def get_micromanagement_report(self) -> dict[str, Any]:
        """Génère un rapport de micromanagement CEO"""
        
        report = {
            "topic": self.session.topic,
            "session_started": self.session.micromanagement_log[0] if self.session.micromanagement_log else None,
            "total_outputs": sum(len(outputs) for outputs in self.session.agent_outputs.values()),
            "agent_outputs": {},
            "approval_rates": {},
            "revisions_needed": {},
            "ceo_satisfaction": 0.0
        }
        
        # Calculer les statistiques par agent
        for agent_type, outputs in self.session.agent_outputs.items():
            approved = sum(1 for o in outputs if o.status == ApprovalStatus.APPROVED)
            rejected = sum(1 for o in outputs if o.status == ApprovalStatus.REJECTED)
            revisions = sum(1 for o in outputs if o.status == ApprovalStatus.REVISION_REQUIRED)
            total = len(outputs)
            
            if total > 0:
                approval_rate = (approved / total) * 100
            else:
                approval_rate = 0
            
            report["agent_outputs"][agent_type.value] = {
                "total": total,
                "approved": approved,
                "rejected": rejected,
                "revisions": revisions,
                "approval_rate": approval_rate
            }
            
            report["approval_rates"][agent_type.value] = approval_rate
            report["revisions_needed"][agent_type.value] = revisions
        
        # Calculer la satisfaction CEO
        total_outputs = report["total_outputs"]
        if total_outputs > 0:
            total_approved = sum(
                len([o for o in outputs if o.status == ApprovalStatus.APPROVED])
                for outputs in self.session.agent_outputs.values()
            )
            report["ceo_satisfaction"] = (total_approved / total_outputs) * 100
        
        # Ajouter le log de micromanagement
        report["micromanagement_log"] = self.session.micromanagement_log
        
        return report
    
    async def export_micromanagement_session(self) -> Path:
        """Exporte la session de micromanagement"""
        
        report = await self.get_micromanagement_report()
        
        # Créer le fichier de rapport
        report_path = self.run_dir / "ceo_micromanagement_report.json"
        report_path.write_text(
            json.dumps(report, indent=2, default=str),
            encoding="utf-8"
        )
        
        # Créer un fichier lisible
        readable_report = await self._create_readable_report(report)
        readable_path = self.run_dir / "CEO_MICROMANAGEMENT_REPORT.md"
        readable_path.write_text(readable_report, encoding="utf-8")
        
        logger.info(f"📊 CEO micromanagement report exported to {report_path}")
        
        return report_path
    
    async def _create_readable_report(self, report: dict[str, Any]) -> str:
        """Crée un rapport lisible"""
        
        readable = f"""# CEO Micromanagement Report

## Topic
{report['topic']}

## Session Overview
- Total Outputs: {report['total_outputs']}
- CEO Satisfaction: {report['ceo_satisfaction']:.1f}%

## Agent Outputs

"""
        
        for agent_type, stats in report["agent_outputs"].items():
            readable += f"""### {agent_type.title()}
- Total: {stats['total']}
- Approved: {stats['approved']}
- Rejected: {stats['rejected']}
- Revisions: {stats['revisions']}
- Approval Rate: {stats['approval_rate']:.1f}%

"""
        
        readable += """## Micromanagement Log

"""
        
        for log_entry in report["micromanagement_log"]:
            readable += f"- {log_entry}\n"
        
        readable += """

---
*Generated by CEO Micromanager - Total Control*
"""
        
        return readable


# Fonction utilitaire pour créer un micromanager
async def create_ceo_micromanager(
    settings: Settings,
    llm_client: LLMClient,
    toolkit: CEOToolkit,
    run_dir: Path
) -> CEOMicromanager:
    """
    Crée un micromanager CEO
    
    Args:
        settings: Configuration Asmblr
        llm_client: Client LLM
        toolkit: CEO Toolkit
        run_dir: Répertoire de travail
        
    Returns:
        CEOMicromanager avec contrôle total sur les agents
    """
    
    micromanager = CEOMicromanager(
        settings=settings,
        llm_client=llm_client,
        toolkit=toolkit,
        run_dir=run_dir
    )
    
    logger.info("🎯 CEO Micromanager created - Total control over agents")
    
    return micromanager
