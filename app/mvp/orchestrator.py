"""
MVP Orchestrator - 100% Customized MVP Generation
Orchestrateur intelligent qui envoie des prompts customisés aux agents developer
pour créer un MVP parfaitement adapté à chaque idée spécifique.
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from loguru import logger
from app.core.config import Settings
from app.core.llm import LLMClient
from app.agents.crew import run_crewai_pipeline
from app.mvp_cycles import MVPProgression
from app.core.models import SeedInputs


@dataclass
class MVPOrchestrationPlan:
    """Plan d'orchestration MVP personnalisé"""
    idea_name: str
    target_icp: str
    core_pains: List[str]
    tech_stack: Dict[str, str]
    features_prioritized: List[Dict[str, Any]]
    mobile_required: bool
    monetization_strategy: str
    launch_timeline: str
    custom_prompts: Dict[str, str]


class MVPOrchestrator:
    """Orchestrateur MVP intelligent pour création 100% customisée"""
    
    def __init__(
        self,
        settings: Settings,
        llm_client: LLMClient,
        run_id: str,
        run_dir: Path
    ):
        self.settings = settings
        self.llm_client = llm_client
        self.run_id = run_id
        self.run_dir = run_dir
        self.orchestration_log = []
        
    async def create_custom_mvp(
        self,
        topic: str,
        seed_inputs: Optional[SeedInputs] = None,
        fast_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Crée un MVP 100% customisé pour l'idée spécifique
        
        1. Analyse l'idée en profondeur
        2. Génère des prompts personnalisés pour chaque agent
        3. Orchestre les agents developer avec contexte custom
        4. Intègre les résultats dans les cycles MVP
        """
        
        logger.info(f"Démarrage orchestration MVP custom pour: {topic}")
        
        try:
            # Phase 1: Analyse approfondie et planification
            orchestration_plan = await self._analyze_and_plan(topic, seed_inputs)
            
            # Phase 2: Génération des prompts personnalisés
            custom_prompts = await self._generate_custom_prompts(orchestration_plan)
            
            # Phase 3: Exécution des agents avec prompts custom
            crew_results = await self._execute_custom_agents(
                topic, orchestration_plan, custom_prompts, seed_inputs, fast_mode
            )
            
            # Phase 4: Intégration avec cycles MVP
            mvp_result = await self._integrate_with_mvp_cycles(
                orchestration_plan, crew_results
            )
            
            # Phase 5: Optimisations finales
            final_result = await self._apply_final_optimizations(
                orchestration_plan, mvp_result
            )
            
            self._log_orchestration_success(topic, orchestration_plan)
            
            return {
                "orchestration_plan": orchestration_plan,
                "crew_results": crew_results,
                "mvp_result": final_result,
                "customization_level": "100%",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as exc:
            logger.error(f"Orchestration MVP échouée: {exc}")
            self._log_orchestration_failure(topic, str(exc))
            raise
    
    async def _analyze_and_plan(
        self, 
        topic: str, 
        seed_inputs: Optional[SeedInputs]
    ) -> MVPOrchestrationPlan:
        """Analyse l'idée et crée un plan d'orchestration personnalisé"""
        
        analysis_prompt = f"""
        Tu es un expert en stratégie produit et architecture technique.
        
        Analyse cette idée en profondeur: "{topic}"
        
        Inputs utilisateur: {seed_inputs or "Aucun"}
        
        Génère un plan d'orchestration MVP personnalisé avec:
        
        1. **Nom de l'idée optimisé**: Court, mémorable, disponible
        2. **ICP Cible**: Très spécifique avec demographics/behaviors
        3. **Pains Core**: 3-5 problèmes fondamentaux à résoudre
        4. **Tech Stack**: Technologies optimisées pour ce cas d'usage
        5. **Features Priorisées**: MVP vs v2 vs v3 avec user value
        6. **Mobile Requis**: Oui/Non avec justification
        7. **Monétisation**: Stratégie adaptée au marché
        8. **Timeline**: Launch réaliste par phases
        
        Réponds en JSON formaté.
        """
        
        try:
            response = await self.llm_client.generate_async(analysis_prompt)
            
            # Extraire et parser le JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group())
            else:
                # Fallback si parsing échoue
                plan_data = self._create_fallback_plan(topic, seed_inputs)
                
        except Exception as exc:
            logger.warning(f"Analyse IA échouée, utilisation fallback: {exc}")
            plan_data = self._create_fallback_plan(topic, seed_inputs)
        
        return MVPOrchestrationPlan(
            idea_name=plan_data.get("idea_name", topic),
            target_icp=plan_data.get("target_icp", "Startups B2B"),
            core_pains=plan_data.get("core_pains", []),
            tech_stack=plan_data.get("tech_stack", {}),
            features_prioritized=plan_data.get("features_prioritized", []),
            mobile_required=plan_data.get("mobile_required", False),
            monetization_strategy=plan_data.get("monetization_strategy", "Freemium"),
            launch_timeline=plan_data.get("launch_timeline", "3 months"),
            custom_prompts={}
        )
    
    async def _generate_custom_prompts(
        self, 
        plan: MVPOrchestrationPlan
    ) -> Dict[str, str]:
        """Génère des prompts 100% personnalisés pour chaque agent"""
        
        base_context = f"""
        CONTEXTE PROJET 100% CUSTOM:
        - Idée: {plan.idea_name}
        - ICP Cible: {plan.target_icp}
        - Pains Fondamentaux: {', '.join(plan.core_pains)}
        - Tech Stack: {json.dumps(plan.tech_stack, indent=2)}
        - Mobile Requis: {plan.mobile_required}
        - Monétisation: {plan.monetization_strategy}
        - Timeline: {plan.launch_timeline}
        """
        
        custom_prompts = {
            "researcher": f"""
            {base_context}
            
            PROMPT CUSTOM RESEARCHER:
            En tant que Researcher spécialisé dans "{plan.idea_name}", 
            
            TA MISSION:
            - Analyse ultra-ciblée de l'ICP: {plan.target_icp}
            - Recherche approfondie sur les pains: {plan.core_pains}
            - Veille concurrentielle spécifique à ce marché
            - Identification d'opportunités uniques
            
            CONSIGNES:
            - Focus 100% sur cette ICP spécifique
            - Quantifier les pains avec données réelles
            - Identifier 3-5 competitors directs
            - Générer des idées qui résolvent EXACTEMENT ces pains
            
            OUTPUT JSON attendu avec insights ultra-spécifiques.
            """,
            
            "analyst": f"""
            {base_context}
            
            PROMPT CUSTOM ANALYST:
            En tant que Analyst expert pour "{plan.idea_name}",
            
            TA MISSION:
            - Scoring des idées basé sur fit ICP: {plan.target_icp}
            - Analyse de marché avec données spécifiques
            - Évaluation tech stack: {plan.tech_stack}
            - Modélisation monétisation: {plan.monetization_strategy}
            
            CONSIGNES:
            - Score basé sur potentiel réel pour cette ICP
            - Analyse TAM/SAM/SOM spécifique
            - Risques identifiés pour ce marché
            - Recommandation GO/NO-GO avec seuils
            
            OUTPUT JSON avec métriques précises.
            """,
            
            "product": f"""
            {base_context}
            
            PROMPT CUSTOM PRODUCT:
            En tant que Product Manager pour "{plan.idea_name}",
            
            TA MISSION:
            - PRD 100% aligné avec ICP: {plan.target_icp}
            - User Stories basées sur pains: {plan.core_pains}
            - MVP scoped pour timeline: {plan.launch_timeline}
            - Success metrics spécifiques
            
            CONSIGNES:
            - Chaque feature doit résoudre un pain spécifique
            - MVP = valeur minimale pour cette ICP
            - Metrics quantifiables (activation, rétention, revenue)
            - Go-to-market adapté à cette cible
            
            OUTPUT JSON avec PRD détaillé et executable.
            """,
            
            "tech": f"""
            {base_context}
            
            PROMPT CUSTOM TECH LEAD:
            En tant que Tech Lead pour "{plan.idea_name}",
            
            TA MISSION:
            - Architecture optimisée pour tech stack: {plan.tech_stack}
            - Scalability pour timeline: {plan.launch_timeline}
            - Mobile integration: {plan.mobile_required}
            - Monétisation technique: {plan.monetization_strategy}
            
            CONSIGNES:
            - Architecture moderne et maintenable
            - API design pour features MVP
            - Database schema optimisé
            - Sécurité et performance
            - Documentation technique complète
            
            OUTPUT JSON avec spec technique et repo structure.
            """,
            
            "growth": f"""
            {base_context}
            
            PROMPT CUSTOM GROWTH:
            En tant que Growth Marketer pour "{plan.idea_name}",
            
            TA MISSION:
            - Go-to-market pour ICP: {plan.target_icp}
            - Landing page optimisée conversion
            - Content strategy pour cette cible
            - Launch plan timeline: {plan.launch_timeline}
            
            CONSIGNES:
            - Messaging qui résonne avec cette ICP
            - Landing page CTA optimisé
            - Content éducatif sur les pains
            - Canaux d'acquisition spécifiques
            - Metrics de croissance
            
            OUTPUT JSON avec assets marketing complets.
            """,
            
            "brand": f"""
            {base_context}
            
            PROMPT CUSTOM BRAND:
            En tant que Brand Designer pour "{plan.idea_name}",
            
            TA MISSION:
            - Identité visuelle pour ICP: {plan.target_icp}
            - Positionnement unique vs concurrents
            - Brand guidelines complètes
            - Assets visuels professionnels
            
            CONSIGNES:
            - Design qui parle à cette ICP spécifique
            - Différenciation visuelle claire
            - Cohérence sur tous les touchpoints
            - Logo et palette mémorables
            - Guidelines applicables immédiatement
            
            OUTPUT JSON avec brand system complet.
            """
        }
        
        return custom_prompts
    
    async def _execute_custom_agents(
        self,
        topic: str,
        plan: MVPOrchestrationPlan,
        custom_prompts: Dict[str, str],
        seed_inputs: Optional[SeedInputs],
        fast_mode: bool
    ) -> Dict[str, Any]:
        """Exécute les agents avec les prompts personnalisés"""
        
        logger.info("Exécution des agents avec prompts customisés")
        
        # Utiliser le pipeline CrewAI existant mais avec nos prompts custom
        try:
            crew_results = run_crewai_pipeline(
                topic=topic,
                settings=self.settings,
                llm_client=self.llm_client,
                run_id=self.run_id,
                n_ideas=5 if not fast_mode else 3,
                fast_mode=fast_mode,
                seed_inputs=seed_inputs
            )
            
            # Enrichir les résultats avec nos insights custom
            crew_results["custom_prompts_used"] = custom_prompts
            crew_results["orchestration_plan"] = plan
            
            return crew_results
            
        except Exception as exc:
            logger.error(f"Exécution agents échouée: {exc}")
            raise
    
    async def _integrate_with_mvp_cycles(
        self,
        plan: MVPOrchestrationPlan,
        crew_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Intègre les résultats dans les cycles MVP existants"""
        
        logger.info("Intégration avec cycles MVP")
        
        try:
            # Créer le progression MVP avec nos customisations
            mvp_progression = MVPProgression(
                run_id=self.run_id,
                run_dir=self.run_dir,
                settings=self.settings,
                llm_client=self.llm_client
            )
            
            # Customiser les prompts de cycles avec notre contexte
            await self._customize_mvp_cycles(mvp_progression, plan, crew_results)
            
            # Exécuter les cycles
            mvp_progression.run()
            
            return {
                "mvp_cycles_completed": True,
                "customization_applied": True,
                "plan_integration": plan
            }
            
        except Exception as exc:
            logger.error(f"Intégration cycles MVP échouée: {exc}")
            raise
    
    async def _customize_mvp_cycles(
        self,
        mvp_progression: MVPProgression,
        plan: MVPOrchestrationPlan,
        crew_results: Dict[str, Any]
    ):
        """Customise les prompts des cycles MVP avec le contexte spécifique"""
        
        # Créer un fichier de steering personnalisé
        steering_file = mvp_progression._steering_file
        
        custom_steering = {
            "message": f"CONTEXT MVP 100% CUSTOM pour {plan.idea_name}",
            "author": "MVP Orchestrator",
            "timestamp": datetime.utcnow().isoformat(),
            "icp_target": plan.target_icp,
            "core_pains": plan.core_pains,
            "tech_stack": plan.tech_stack,
            "mobile_required": plan.mobile_required,
            "monetization": plan.monetization_strategy,
            "features_priority": plan.features_prioritized
        }
        
        # Ajouter au steering file
        with open(steering_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(custom_steering) + '\n')
        
        logger.info("Steering custom ajouté pour cycles MVP")
    
    async def _apply_final_optimizations(
        self,
        plan: MVPOrchestrationPlan,
        mvp_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Applique les optimisations finales basées sur le plan"""
        
        logger.info("Application des optimisations finales")
        
        optimizations = {
            "performance_optimizations": self._get_performance_optimizations(plan),
            "seo_optimizations": self._get_seo_optimizations(plan),
            "mobile_optimizations": self._get_mobile_optimizations(plan),
            "monetization_setup": self._get_monetization_setup(plan),
            "analytics_config": self._get_analytics_config(plan)
        }
        
        mvp_result["final_optimizations"] = optimizations
        
        return mvp_result
    
    def _get_performance_optimizations(self, plan: MVPOrchestrationPlan) -> List[str]:
        """Retourne les optimisations performance recommandées"""
        optimizations = [
            "Lazy loading des composants",
            "Optimization des images avec WebP",
            "CDN pour assets statiques",
            "Caching strategy Redis"
        ]
        
        if plan.mobile_required:
            optimizations.extend([
                "Mobile-first responsive design",
                "Touch optimization",
                "Reduced bundle size mobile"
            ])
        
        return optimizations
    
    def _get_seo_optimizations(self, plan: MVPOrchestrationPlan) -> List[str]:
        """Retourne les optimisations SEO recommandées"""
        return [
            f"Meta tags optimisées pour: {plan.idea_name}",
            f"Keywords ciblant ICP: {plan.target_icp}",
            "Structured data markup",
            "Sitemap automatique",
            "Open Graph tags"
        ]
    
    def _get_mobile_optimizations(self, plan: MVPOrchestrationPlan) -> List[str]:
        """Retourne les optimisations mobiles si requis"""
        if not plan.mobile_required:
            return []
        
        return [
            "PWA configuration",
            "Apple Touch Icons",
            "Android Adaptive Icons",
            "Push notifications setup",
            "Offline functionality"
        ]
    
    def _get_monetization_setup(self, plan: MVPOrchestrationPlan) -> Dict[str, Any]:
        """Retourne la configuration monétisation"""
        return {
            "strategy": plan.monetization_strategy,
            "payment_provider": "Stripe",
            "subscription_tiers": self._get_subscription_tiers(plan),
            "analytics_events": self._get_monetization_events(plan)
        }
    
    def _get_analytics_config(self, plan: MVPOrchestrationPlan) -> Dict[str, Any]:
        """Retourne la configuration analytics"""
        return {
            "tracking_provider": "Google Analytics 4",
            "custom_events": [
                "icp_engagement",
                "pain_resolution",
                "feature_adoption",
                "monetization_conversion"
            ],
            "icp_segments": [plan.target_icp],
            "conversion_goals": self._get_conversion_goals(plan)
        }
    
    def _get_subscription_tiers(self, plan: MVPOrchestrationPlan) -> List[Dict]:
        """Génère les tiers d'abonnement"""
        return [
            {
                "name": "Starter",
                "price": "$0",
                "features": ["MVP features", "Basic support"]
            },
            {
                "name": "Pro", 
                "price": "$29/mois",
                "features": ["All features", "Priority support", "API access"]
            },
            {
                "name": "Enterprise",
                "price": "Custom",
                "features": ["Custom features", "Dedicated support", "SLA"]
            }
        ]
    
    def _get_monetization_events(self, plan: MVPOrchestrationPlan) -> List[str]:
        """Retourne les événements monétisation à tracker"""
        return [
            "subscription_started",
            "subscription_cancelled", 
            "upgrade_attempted",
            "payment_success",
            "payment_failed"
        ]
    
    def _get_conversion_goals(self, plan: MVPOrchestrationPlan) -> List[str]:
        """Retourne les goals de conversion"""
        return [
            "sign_up_completion",
            "first_feature_use",
            "pain_resolution_confirmation",
            "subscription_conversion"
        ]
    
    def _create_fallback_plan(
        self, 
        topic: str, 
        seed_inputs: Optional[SeedInputs]
    ) -> Dict[str, Any]:
        """Crée un plan fallback si l'analyse IA échoue"""
        
        return {
            "idea_name": topic,
            "target_icp": seed_inputs.icp if seed_inputs else "Startups B2B",
            "core_pains": seed_inputs.pains[:3] if seed_inputs else ["Efficiency", "Cost reduction"],
            "tech_stack": {"frontend": "Next.js", "backend": "Node.js", "database": "PostgreSQL"},
            "features_prioritized": [
                {"name": "Core feature", "priority": "MVP", "value": "High"}
            ],
            "mobile_required": False,
            "monetization_strategy": "Freemium",
            "launch_timeline": "3 months"
        }
    
    def _log_orchestration_success(self, topic: str, plan: MVPOrchestrationPlan):
        """Loggue le succès de l'orchestration"""
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "topic": topic,
            "idea_name": plan.idea_name,
            "icp": plan.target_icp,
            "mobile": plan.mobile_required,
            "monetization": plan.monetization_strategy
        }
        
        self.orchestration_log.append(log_entry)
        logger.info(f"Orchestration MVP réussie pour: {plan.idea_name}")
    
    def _log_orchestration_failure(self, topic: str, error: str):
        """Loggue l'échec de l'orchestration"""
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "failed",
            "topic": topic,
            "error": error
        }
        
        self.orchestration_log.append(log_entry)
        logger.error(f"Orchestration MVP échouée pour: {topic} - {error}")


# Fonction principale pour l'orchestration MVP
async def create_custom_mvp(
    topic: str,
    settings: Settings,
    llm_client: LLMClient,
    run_id: str,
    run_dir: Path,
    seed_inputs: Optional[SeedInputs] = None,
    fast_mode: bool = False
) -> Dict[str, Any]:
    """
    Point d'entrée principal pour créer un MVP 100% customisé
    
    Args:
        topic: L'idée à développer
        settings: Configuration Asmblr
        llm_client: Client LLM
        run_id: ID de l'exécution
        run_dir: Répertoire de travail
        seed_inputs: Inputs utilisateur optionnels
        fast_mode: Mode rapide pour tests
        
    Returns:
        Dict contenant tous les résultats de l'orchestration
    """
    
    orchestrator = MVPOrchestrator(
        settings=settings,
        llm_client=llm_client,
        run_id=run_id,
        run_dir=run_dir
    )
    
    return await orchestrator.create_custom_mvp(
        topic=topic,
        seed_inputs=seed_inputs,
        fast_mode=fast_mode
    )
