"""
CEO Asset and Synergy Manager
Le CEO gère et utilise tous les assets créés par les agents.
Identifie les synergies et optimise l'utilisation des ressources.
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
from app.mvp.ceo_micromanagement import AgentType


class AssetType(Enum):
    """Types d'assets créés par les agents"""
    DOCUMENT = "document"  # Documents textes
    CODE = "code"  # Code source
    DESIGN = "design"  # Assets visuels
    DATA = "data"  # Données
    STRATEGY = "strategy"  # Stratégies
    REPORT = "report"  # Rapports
    TEMPLATE = "template"  # Templates
    CONFIG = "config"  # Configurations
    METADATA = "metadata"  # Métadonnées


class AssetStatus(Enum):
    """Statuts des assets"""
    CREATED = "created"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_USE = "in_use"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class SynergyType(Enum):
    """Types de synergies entre assets"""
    COMPLEMENTARY = "complementary"  # Assets complémentaires
    DERIVED = "derived"  # Un asset dérive d'un autre
    ENHANCED = "enhanced"  # Un asset en améliore un autre
    INTEGRATED = "integrated"  # Assets intégrés
    REUSED = "reused"  # Un asset réutilise un autre
    CONFLICTING = "conflicting"  # Assets en conflit


@dataclass
class Asset:
    """Asset créé par un agent"""
    id: str
    agent_type: AgentType
    asset_type: AssetType
    name: str
    path: Path
    content: str | None = None
    status: AssetStatus = AssetStatus.CREATED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    related_assets: list[str] = field(default_factory=dict)


@dataclass
class Synergy:
    """Synergie entre deux assets"""
    asset1_id: str
    asset2_id: str
    synergy_type: SynergyType
    strength: float  # 0.0 à 1.0
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AssetUsage:
    """Utilisation d'un asset"""
    asset_id: str
    used_by_agent: AgentType
    used_for: str
    usage_count: int = 1
    last_used: datetime = field(default_factory=datetime.utcnow)
    effectiveness: float = 0.0  # 0.0 à 1.0


class CEOAssetAndSynergyManager:
    """
    CEO Asset and Synergy Manager - Gestion des assets et synergies
    
    Le CEO gère tous les assets créés par les agents:
    - Track tous les assets créés
    - Identifie les synergies entre assets
    - Optimise l'utilisation des ressources
    - Facilite la réutilisation
    - Crée des connexions intelligentes
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
        
        # Stockage des assets
        self.assets: dict[str, Asset] = {}
        
        # Stockage des synergies
        self.synergies: dict[str, Synergy] = {}
        
        # Stockage des utilisations
        self.asset_usage: dict[str, list[AssetUsage]] = {}
        
        # Statistiques
        self.asset_stats = {
            "total_assets": 0,
            "by_type": {},
            "by_agent": {},
            "by_status": {},
            "total_synergies": 0,
            "synergy_strength_avg": 0.0
        }
    
    async def register_asset(
        self,
        agent_type: AgentType,
        asset_type: AssetType,
        name: str,
        path: Union[str, Path],
        content: str | None = None,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None
    ) -> Asset:
        """
        Enregistre un asset créé par un agent
        
        Le CEO track tous les assets créés par les agents.
        """
        
        logger.info(f"📦 CEO registering asset: {name} from {agent_type.value}")
        
        asset_id = f"{agent_type.value}_{asset_type.value}_{name}_{datetime.utcnow().timestamp()}"
        path = Path(path)
        
        # Lire le contenu si non fourni
        if content is None and path.exists():
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                content = ""
        
        asset = Asset(
            id=asset_id,
            agent_type=agent_type,
            asset_type=asset_type,
            name=name,
            path=path,
            content=content,
            metadata=metadata or {},
            tags=tags or []
        )
        
        self.assets[asset_id] = asset
        
        # Mettre à jour les statistiques
        self.asset_stats["total_assets"] += 1
        
        asset_type_key = asset_type.value
        if asset_type_key not in self.asset_stats["by_type"]:
            self.asset_stats["by_type"][asset_type_key] = 0
        self.asset_stats["by_type"][asset_type_key] += 1
        
        agent_key = agent_type.value
        if agent_key not in self.asset_stats["by_agent"]:
            self.asset_stats["by_agent"][agent_key] = 0
        self.asset_stats["by_agent"][agent_key] += 1
        
        status_key = asset.status.value
        if status_key not in self.asset_stats["by_status"]:
            self.asset_stats["by_status"][status_key] = 0
        self.asset_stats["by_status"][status_key] += 1
        
        logger.info(f"✅ Asset registered: {asset_id}")
        
        return asset
    
    async def identify_synergies(self):
        """
        Identifie les synergies entre les assets
        
        Le CEO analyse tous les assets pour identifier les synergies.
        """
        
        logger.info("🔗 CEO identifying synergies between assets")
        
        asset_ids = list(self.assets.keys())
        
        for i, asset1_id in enumerate(asset_ids):
            for asset2_id in asset_ids[i+1:]:
                asset1 = self.assets[asset1_id]
                asset2 = self.assets[asset2_id]
                
                # Analyser la synergie potentielle
                synergy = await self._analyze_synergy(asset1, asset2)
                
                if synergy and synergy.strength > 0.5:  # Seulement les synergies fortes
                    synergy_key = f"{asset1_id}_{asset2_id}"
                    self.synergies[synergy_key] = synergy
                    
                    self.asset_stats["total_synergies"] += 1
                    
                    logger.info(
                        f"🔗 Synergy found: {asset1.name} ↔ {asset2.name} "
                        f"({synergy.synergy_type.value}, strength: {synergy.strength:.2f})"
                    )
        
        # Calculer la force moyenne des synergies
        if self.synergies:
            avg_strength = sum(s.strength for s in self.synergies.values()) / len(self.synergies)
            self.asset_stats["synergy_strength_avg"] = avg_strength
        
        logger.info(f"🔗 Synergy identification complete: {len(self.synergies)} synergies found")
    
    async def _analyze_synergy(
        self,
        asset1: Asset,
        asset2: Asset
    ) -> Synergy | None:
        """Analyse la synergie potentielle entre deux assets"""
        
        # Critères de synergie
        synergy_score = 0.0
        synergy_type = None
        description = ""
        
        # Même créateur → Synergie dérivée potentielle
        if asset1.agent_type == asset2.agent_type:
            synergy_score += 0.2
            synergy_type = SynergyType.DERIVED
            description = f"Both assets created by {asset1.agent_type.value}"
        
        # Même type → Synergie complémentaire potentielle
        if asset1.asset_type == asset2.asset_type:
            synergy_score += 0.3
            if not synergy_type:
                synergy_type = SynergyType.COMPLEMENTARY
            description += f". Same type: {asset1.asset_type.value}"
        
        # Tags communs → Synergie de réutilisation
        common_tags = set(asset1.tags) & set(asset2.tags)
        if common_tags:
            synergy_score += 0.3 * len(common_tags)
            if not synergy_type:
                synergy_type = SynergyType.REUSED
            description += f". Common tags: {', '.join(common_tags)}"
        
        # Contenu similaire → Synergie d'intégration
        if asset1.content and asset2.content:
            # Simple similitude basée sur le contenu
            similarity = self._calculate_content_similarity(asset1.content, asset2.content)
            if similarity > 0.3:
                synergy_score += similarity * 0.5
                if not synergy_type:
                    synergy_type = SynergyType.INTEGRATED
                description += f". Content similarity: {similarity:.2f}"
        
        # Créer la synergie si score suffisant
        if synergy_score > 0.5:
            return Synergy(
                asset1_id=asset1.id,
                asset2_id=asset2.id,
                synergy_type=synergy_type or SynergyType.COMPLEMENTARY,
                strength=min(synergy_score, 1.0),
                description=description or "Synergy detected"
            )
        
        return None
    
    def _calculate_content_similarity(
        self,
        content1: str,
        content2: str
    ) -> float:
        """Calcule la similarité entre deux contenus"""
        
        # Simple similarité basée sur les mots communs
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    async def find_related_assets(
        self,
        asset_id: str,
        max_results: int = 5
    ) -> list[Asset]:
        """
        Trouve les assets liés à un asset donné
        
        Le CEO identifie les assets qui peuvent être utilisés ensemble.
        """
        
        if asset_id not in self.assets:
            return []
        
        related_assets = []
        
        # Trouver les synergies
        for synergy_key, synergy in self.synergies.items():
            if synergy.asset1_id == asset_id:
                if synergy.asset2_id in self.assets:
                    related_assets.append((self.assets[synergy.asset2_id], synergy.strength))
            elif synergy.asset2_id == asset_id:
                if synergy.asset1_id in self.assets:
                    related_assets.append((self.assets[synergy.asset1_id], synergy.strength))
        
        # Trier par force de synergie
        related_assets.sort(key=lambda x: x[1], reverse=True)
        
        return [asset for asset, _ in related_assets[:max_results]]
    
    async def optimize_asset_usage(
        self,
        topic: str,
        vision: str
    ) -> dict[str, Any]:
        """
        Optimise l'utilisation des assets
        
        Le CEO identifie comment optimiser l'utilisation des assets existants.
        """
        
        logger.info("⚡ CEO optimizing asset usage")
        
        optimization_prompt = f"""
        EN TANT QUE CEO POUR "{topic}", OPTIMISE L'UTILISATION DES ASSETS:
        
        Vision CEO: {vision}
        
        ASSETS DISPONIBLES:
        {self._format_assets_for_prompt()}
        
        SYNERGIES IDENTIFIÉES:
        {self._format_synergies_for_prompt()}
        
        OPTIMISATIONS À SUGGÉRER:
        
        1. **Asset Reuse**: Quels assets peuvent être réutilisés?
        2. **Asset Enhancement**: Quels assets peuvent être améliorés?
        3. **Asset Integration**: Quels assets peuvent être intégrés?
        4. **Asset Deprecation**: Quels assets sont obsolètes?
        5. **New Assets Needed**: Quels nouveaux assets sont nécessaires?
        
        Pour chaque optimisation:
        - Asset concerné
        - Type d'optimisation
        - Pourquoi c'est nécessaire
        - Comment l'implémenter
        - Bénéfices attendus
        
        JSON structuré attendu.
        """
        
        try:
            response = await self.llm_client.generate_async(optimization_prompt)
            
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                optimizations = json.loads(json_match.group())
            else:
                optimizations = self._create_default_optimizations()
                
        except Exception as exc:
            logger.warning(f"Asset optimization failed, default: {exc}")
            optimizations = self._create_default_optimizations()
        
        logger.info(f"⚡ Asset optimization complete: {len(optimizations.get('optimizations', []))} optimizations")
        
        return optimizations
    
    def _format_assets_for_prompt(self) -> str:
        """Formate les assets pour le prompt"""
        
        assets_text = ""
        for asset_id, asset in self.assets.items():
            assets_text += f"- {asset.name} ({asset.asset_type.value}) by {asset.agent_type.value}\n"
        
        return assets_text or "No assets available"
    
    def _format_synergies_for_prompt(self) -> str:
        """Formate les synergies pour le prompt"""
        
        synergies_text = ""
        for synergy_key, synergy in self.synergies.items():
            asset1 = self.assets.get(synergy.asset1_id)
            asset2 = self.assets.get(synergy.asset2_id)
            if asset1 and asset2:
                synergies_text += (
                    f"- {asset1.name} ↔ {asset2.name} "
                    f"({synergy.synergy_type.value}, strength: {synergy.strength:.2f})\n"
                )
        
        return synergies_text or "No synergies identified"
    
    def _create_default_optimizations(self) -> dict[str, Any]:
        """Crée des optimisations par défaut"""
        
        return {
            "optimizations": [
                {
                    "asset": "PRD Document",
                    "type": "enhancement",
                    "reason": "Can be enhanced with more specific requirements",
                    "implementation": "Add detailed user stories and acceptance criteria",
                    "benefits": "Better clarity for development team"
                },
                {
                    "asset": "Market Analysis",
                    "type": "reuse",
                    "reason": "Can be reused for competitive analysis",
                    "implementation": "Extract reusable market data templates",
                    "benefits": "Faster future market research"
                }
            ]
        }
    
    async def track_asset_usage(
        self,
        asset_id: str,
        used_by_agent: AgentType,
        used_for: str,
        effectiveness: float = 0.0
    ):
        """
        Track l'utilisation d'un asset
        
        Le CEO track comment les assets sont utilisés.
        """
        
        if asset_id not in self.assets:
            logger.warning(f"Asset not found: {asset_id}")
            return
        
        usage = AssetUsage(
            asset_id=asset_id,
            used_by_agent=used_by_agent,
            used_for=used_for,
            effectiveness=effectiveness
        )
        
        if asset_id not in self.asset_usage:
            self.asset_usage[asset_id] = []
        
        self.asset_usage[asset_id].append(usage)
        
        logger.info(f"📊 Asset usage tracked: {asset_id} used by {used_by_agent.value}")
    
    async def get_asset_report(self) -> dict[str, Any]:
        """Génère un rapport des assets"""
        
        report = {
            "total_assets": self.asset_stats["total_assets"],
            "by_type": self.asset_stats["by_type"],
            "by_agent": self.asset_stats["by_agent"],
            "by_status": self.asset_stats["by_status"],
            "total_synergies": self.asset_stats["total_synergies"],
            "synergy_strength_avg": self.asset_stats["synergy_strength_avg"],
            "top_synergies": [],
            "most_used_assets": [],
            "assets": {}
        }
        
        # Top synergies
        sorted_synergies = sorted(
            self.synergies.values(),
            key=lambda s: s.strength,
            reverse=True
        )
        
        for synergy in sorted_synergies[:10]:
            asset1 = self.assets.get(synergy.asset1_id)
            asset2 = self.assets.get(synergy.asset2_id)
            if asset1 and asset2:
                report["top_synergies"].append({
                    "asset1": asset1.name,
                    "asset2": asset2.name,
                    "type": synergy.synergy_type.value,
                    "strength": synergy.strength
                })
        
        # Most used assets
        usage_counts = {
            asset_id: len(usages)
            for asset_id, usages in self.asset_usage.items()
        }
        
        sorted_usage = sorted(
            usage_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for asset_id, count in sorted_usage[:10]:
            if asset_id in self.assets:
                report["most_used_assets"].append({
                    "name": self.assets[asset_id].name,
                    "usage_count": count
                })
        
        # Détails des assets
        for asset_id, asset in self.assets.items():
            report["assets"][asset_id] = {
                "name": asset.name,
                "type": asset.asset_type.value,
                "agent": asset.agent_type.value,
                "status": asset.status.value,
                "tags": asset.tags,
                "usage_count": len(self.asset_usage.get(asset_id, []))
            }
        
        return report
    
    async def export_asset_report(self) -> Path:
        """Exporte le rapport des assets"""
        
        report = await self.get_asset_report()
        
        # Créer le fichier de rapport
        report_path = self.run_dir / "ceo_assets_report.json"
        report_path.write_text(
            json.dumps(report, indent=2, default=str),
            encoding="utf-8"
        )
        
        # Créer un fichier lisible
        readable_report = await self._create_readable_asset_report(report)
        readable_path = self.run_dir / "CEO_ASSETS_REPORT.md"
        readable_path.write_text(readable_report, encoding="utf-8")
        
        logger.info(f"📦 CEO asset report exported to {report_path}")
        
        return report_path
    
    async def _create_readable_asset_report(self, report: dict[str, Any]) -> str:
        """Crée un rapport lisible"""
        
        readable = f"""# CEO Assets Report

## Overview
- Total Assets: {report['total_assets']}
- Total Synergies: {report['total_synergies']}
- Average Synergy Strength: {report['synergy_strength_avg']:.2f}

## By Type

"""
        
        for asset_type, count in report["by_type"].items():
            readable += f"- {asset_type.title()}: {count}\n"
        
        readable += "\n## By Agent\n\n"
        
        for agent, count in report["by_agent"].items():
            readable += f"- {agent.title()}: {count}\n"
        
        readable += "\n## Top Synergies\n\n"
        
        for synergy in report["top_synergies"]:
            readable += f"- {synergy['asset1']} ↔ {synergy['asset2']} ({synergy['type']}, {synergy['strength']:.2f})\n"
        
        readable += "\n## Most Used Assets\n\n"
        
        for asset in report["most_used_assets"]:
            readable += f"- {asset['name']}: {asset['usage_count']} uses\n"
        
        readable += "\n## Assets\n\n"
        
        for asset_id, asset_data in report["assets"].items():
            readable += f"""### {asset_data['name']}
- Type: {asset_data['type']}
- Agent: {asset_data['agent']}
- Status: {asset_data['status']}
- Tags: {', '.join(asset_data['tags']) if asset_data['tags'] else 'None'}
- Usage Count: {asset_data['usage_count']}

"""
        
        readable += """

---
*Generated by CEO Asset and Synergy Manager - Total Control*
"""
        
        return readable


# Fonction utilitaire pour créer un manager d'assets
async def create_ceo_asset_manager(
    settings: Settings,
    llm_client: LLMClient,
    toolkit: CEOToolkit,
    run_dir: Path
) -> CEOAssetAndSynergyManager:
    """
    Crée un manager d'assets CEO
    
    Args:
        settings: Configuration Asmblr
        llm_client: Client LLM
        toolkit: CEO Toolkit
        run_dir: Répertoire de travail
        
    Returns:
        CEOAssetAndSynergyManager avec contrôle total des assets
    """
    
    manager = CEOAssetAndSynergyManager(
        settings=settings,
        llm_client=llm_client,
        toolkit=toolkit,
        run_dir=run_dir
    )
    
    logger.info("📦 CEO Asset and Synergy Manager created - Total control over assets")
    
    return manager
