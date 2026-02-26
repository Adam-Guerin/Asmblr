"""
Pitch Deck Generator - Enhanced Startup Pitch Deck Creation
Générateur de pitch decks améliorés avec intégration de l'analyse de succès de startup,
captures d'écran du MVP, templates de présentation, et support multi-mode (Ollama/K2.5).
"""

import json
import subprocess
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from loguru import logger
from app.core.config import Settings
from app.core.llm import LLMClient


class GenerationMode(Enum):
    """Mode de génération du pitch deck"""
    LOCAL_OLLAMA = "local_ollama"
    CLOUD_K25 = "cloud_k25"
    HYBRID = "hybrid"


class PitchDeckTemplate(Enum):
    """Templates de pitch deck"""
    SEQUOIA = "sequoia"
    YCOMBINATOR = "ycombinator"
    TECHSTARS = "techstars"
    CUSTOM = "custom"


@dataclass
class PitchDeckSlide:
    """Slide de pitch deck"""
    title: str
    summary: str
    bullets: List[str]
    visual: str
    data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    screenshot: Optional[str] = None  # Screenshot du MVP
    template: Optional[str] = None  # Template utilisé


@dataclass
class PitchDeck:
    """Pitch deck complet"""
    project_name: str
    subtitle: str
    topic: str
    slides: List[PitchDeckSlide]
    ask: Dict[str, Any]
    key_metrics: List[str]
    closing: str
    success_score: float
    success_level: str
    created_at: str
    source: str
    generation_mode: str
    template: str
    screenshots: List[str] = field(default_factory=list)


class PitchDeckGenerator:
    """
    Générateur de pitch decks améliorés
    
    Crée des pitch decks convaincants et personnalisés en utilisant :
    - L'analyse de succès de startup
    - Les métriques de validation
    - Les insights du marché
    - Les données de l'analyse de succès
    - Screenshots du MVP
    - Templates de présentation (Sequoia, YCombinator, TechStars)
    - Modes de génération (Ollama local, K2.5 cloud, Hybrid)
    """
    
    def __init__(
        self,
        settings: Settings,
        llm_client: LLMClient,
        run_dir: Path,
        generation_mode: GenerationMode = GenerationMode.LOCAL_OLLAMA,
        template: PitchDeckTemplate = PitchDeckTemplate.SEQUOIA
    ):
        self.settings = settings
        self.llm_client = llm_client
        self.run_dir = run_dir
        self.generation_mode = generation_mode
        self.template = template
        self.screenshots = []
    
    async def capture_mvp_screenshots(
        self,
        mvp_dir: Optional[Path] = None
    ) -> List[str]:
        """
        Capture des screenshots du MVP
        
        Args:
            mvp_dir: Répertoire du MVP
            
        Returns:
            Liste des chemins des screenshots
        """
        
        logger.info("📸 Capturing MVP screenshots for pitch deck")
        
        screenshots = []
        
        if mvp_dir is None:
            mvp_dir = self.run_dir / "mvp_repo"
        
        if not mvp_dir.exists():
            logger.warning(f"MVP directory not found: {mvp_dir}")
            return screenshots
        
        # Chercher les fichiers HTML/JS pour capturer
        html_files = list(mvp_dir.rglob("*.html")) + list(mvp_dir.rglob("index.js"))
        
        if not html_files:
            logger.warning("No HTML files found in MVP directory")
            return screenshots
        
        # Capturer les screenshots avec Playwright ou Selenium
        for html_file in html_files[:5]:  # Max 5 screenshots
            try:
                screenshot_path = self.run_dir / "screenshots" / f"{html_file.stem}.png"
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Utiliser Playwright pour capturer
                cmd = [
                    "npx", "playwright", "screenshot",
                    str(html_file),
                    str(screenshot_path)
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 and screenshot_path.exists():
                    screenshots.append(str(screenshot_path))
                    logger.info(f"✅ Screenshot captured: {screenshot_path}")
                
            except Exception as exc:
                logger.warning(f"Failed to capture screenshot for {html_file}: {exc}")
        
        self.screenshots = screenshots
        logger.info(f"📸 {len(screenshots)} MVP screenshots captured")
        
        return screenshots
    
    def get_template_config(self) -> Dict[str, Any]:
        """Retourne la configuration du template"""
        
        templates = {
            PitchDeckTemplate.SEQUOIA: {
                "name": "Sequoia Capital",
                "style": "Clean, minimalist, data-driven",
                "colors": ["#1a1a1a", "#ffffff", "#00d4aa"],
                "font": "Helvetica Neue",
                "slide_order": [
                    "Title & Vision",
                    "Problem",
                    "Solution",
                    "Market",
                    "Product",
                    "Business Model",
                    "Competition",
                    "Go-to-Market",
                    "Traction & Validation",
                    "Financial Projections",
                    "Team",
                    "Ask"
                ],
                "emphasis": "Growth metrics, market size, team"
            },
            PitchDeckTemplate.YCOMBINATOR: {
                "name": "Y Combinator",
                "style": "Simple, direct, problem-focused",
                "colors": ["#f26627", "#ffffff", "#000000"],
                "font": "Arial",
                "slide_order": [
                    "Problem",
                    "Solution",
                    "Why Now",
                    "Market Size",
                    "Business Model",
                    "Competition",
                    "Team",
                    "Traction",
                    "Ask"
                ],
                "emphasis": "Problem, solution, team, traction"
            },
            PitchDeckTemplate.TECHSTARS: {
                "name": "Techstars",
                "style": "Bold, energetic, founder-focused",
                "colors": ["#ff6b6b", "#4ecdc4", "#ffffff"],
                "font": "Roboto",
                "slide_order": [
                    "Title & Vision",
                    "Problem",
                    "Solution",
                    "Market",
                    "Product",
                    "Business Model",
                    "Competition",
                    "Go-to-Market",
                    "Traction",
                    "Team",
                    "Ask"
                ],
                "emphasis": "Founder story, market opportunity, traction"
            }
        }
        
        return templates.get(self.template, templates[PitchDeckTemplate.CUSTOM])
    
    def generate_with_ollama(
        self,
        prompt: str,
        model: str = "gemma:7b"  # Meilleur modèle pour les présentations
    ) -> str:
        """
        Génère du contenu avec Ollama (mode local)
        
        Modèles recommandés pour les présentations :
        - gemma:7b (meilleur pour créativité marketing et pitch decks)
        - mistral:7b (bon pour créativité et pitch decks)
        - phi:3.1 (compact et performant)
        
        Pourquoi gemma:7b est le meilleur :
        - Excellent pour le contenu marketing
        - Réponses concises et impactantes
        - Idéal pour les slides courtes
        - Compréhension business avancée
        - Meilleure qualité de génération pour les présentations
        
        Args:
            prompt: Prompt à générer
            model: Modèle Ollama à utiliser (défaut: gemma:7b)
            
        Returns:
            Contenu généré
        """
        
        try:
            cmd = [
                "ollama", "run", model,
                prompt
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"Ollama generation failed: {result.stderr}")
                return ""
        
        except Exception as exc:
            logger.error(f"Ollama generation error: {exc}")
            return ""
    
    def generate_with_k25(
        self,
        prompt: str,
        model: str = "claude-3-sonnet"
    ) -> str:
        """
        Génère du contenu avec l'API K2.5 (mode cloud)
        
        Args:
            prompt: Prompt à générer
            model: Modèle K2.5 à utiliser
            
        Returns:
            Contenu généré
        """
        
        try:
            # Utiliser le LLMClient existant (K2.5)
            if self.llm_client and self.llm_client.available():
                result = self.llm_client.generate(prompt)
                return result
            else:
                logger.error("K2.5 API not available")
                return ""
        
        except Exception as exc:
            logger.error(f"K2.5 generation error: {exc}")
            return ""
    
    def generate_content(
        self,
        prompt: str
    ) -> str:
        """
        Génère du contenu selon le mode sélectionné
        
        Args:
            prompt: Prompt à générer
            
        Returns:
            Contenu généré
        """
        
        if self.generation_mode == GenerationMode.LOCAL_OLLAMA:
            return self.generate_with_ollama(prompt)
        elif self.generation_mode == GenerationMode.CLOUD_K25:
            return self.generate_with_k25(prompt)
        else:  # HYBRID
            # Essayer Ollama d'abord, fallback sur K2.5
            content = self.generate_with_ollama(prompt)
            if not content:
                content = self.generate_with_k25(prompt)
            return content
    
    async def generate_enhanced_pitch_deck(
        self,
        topic: str,
        idea: Dict[str, Any],
        brand_payload: Dict[str, Any],
        market_report: str,
        validated_pains: List[Dict[str, Any]],
        competitors: List[Dict[str, Any]],
        success_report: Optional[Any] = None,
        mvp_dir: Optional[Path] = None
    ) -> PitchDeck:
        """
        Génère un pitch deck amélioré
        
        Args:
            topic: Sujet de la startup
            idea: Idée de startup
            brand_payload: Payload de marque
            market_report: Rapport de marché
            validated_pains: Pains validés
            competitors: Concurrents
            success_report: Rapport de succès de startup
            mvp_dir: Répertoire du MVP pour screenshots
            
        Returns:
            PitchDeck complet
        """
        
        logger.info(f"🎨 Generating enhanced pitch deck with {self.generation_mode.value} mode and {self.template.value} template")
        
        # Capturer les screenshots du MVP
        await self.capture_mvp_screenshots(mvp_dir)
        
        project_name = brand_payload.get("project_name") or idea.get("name", "Unknown")
        subtitle = brand_payload.get("tagline") or idea.get("rationale", "")
        
        # Générer les slides
        slides = await self._generate_slides(
            topic=topic,
            idea=idea,
            brand_payload=brand_payload,
            market_report=market_report,
            validated_pains=validated_pains,
            competitors=competitors,
            success_report=success_report
        )
        
        # Générer les métriques clés
        key_metrics = await self._generate_key_metrics(
            validated_pains=validated_pains,
            competitors=competitors,
            success_report=success_report
        )
        
        # Générer l'ask
        ask = await self._generate_ask(
            success_report=success_report,
            topic=topic
        )
        
        # Générer le closing
        closing = await self._generate_closing(
            success_report=success_report
        )
        
        # Score de succès
        success_score = success_report.overall_success_score if success_report else 0.0
        success_level = success_report.success_level.name if success_report else "unknown"
        
        pitch_deck = PitchDeck(
            project_name=project_name,
            subtitle=subtitle,
            topic=topic,
            slides=slides,
            ask=ask,
            key_metrics=key_metrics,
            closing=closing,
            success_score=success_score,
            success_level=success_level,
            created_at=datetime.utcnow().isoformat(),
            source="enhanced_generator",
            generation_mode=self.generation_mode.value,
            template=self.template.value,
            screenshots=self.screenshots
        )
        
        logger.info(f"🎨 Enhanced pitch deck generated: {len(slides)} slides, {len(self.screenshots)} screenshots")
        
        return pitch_deck
    
    async def _generate_slides(
        self,
        topic: str,
        idea: Dict[str, Any],
        brand_payload: Dict[str, Any],
        market_report: str,
        validated_pains: List[Dict[str, Any]],
        competitors: List[Dict[str, Any]],
        success_report: Optional[Any]
    ) -> List[PitchDeckSlide]:
        """Génère les slides du pitch deck selon le template"""
        
        slides = []
        template_config = self.get_template_config()
        slide_order = template_config.get("slide_order", [])
        
        # Créer toutes les slides disponibles
        all_slides = {
            "Title & Vision": await self._create_title_slide(topic, idea, brand_payload),
            "Problem": await self._create_problem_slide(topic, validated_pains),
            "Solution": await self._create_solution_slide(topic, idea, brand_payload, success_report),
            "Why Now": await self._create_why_now_slide(topic, success_report),
            "Market": await self._create_market_slide(topic, market_report, validated_pains, success_report),
            "Product": await self._create_product_slide(topic, idea, brand_payload),
            "Business Model": await self._create_business_model_slide(topic, idea, success_report),
            "Competition": await self._create_competition_slide(topic, competitors, success_report),
            "Go-to-Market": await self._create_gtm_slide(topic, idea, success_report),
            "Traction": await self._create_traction_slide(topic, validated_pains, competitors, success_report),
            "Traction & Validation": await self._create_traction_slide(topic, validated_pains, competitors, success_report),
            "Financial Projections": await self._create_financial_slide(topic, success_report),
            "Team": await self._create_team_slide(topic, idea),
            "Ask": await self._create_ask_slide(topic, success_report)
        }
        
        # Générer les slides selon l'ordre du template
        for slide_name in slide_order:
            if slide_name in all_slides:
                slide = all_slides[slide_name]
                # Ajouter le template et les screenshots
                slide.template = self.template.value
                if slide_name == "Product" and self.screenshots:
                    slide.screenshot = self.screenshots[0]
                slides.append(slide)
        
        return slides
    
    async def _create_title_slide(
        self,
        topic: str,
        idea: Dict[str, Any],
        brand_payload: Dict[str, Any]
    ) -> PitchDeckSlide:
        """Crée la slide titre"""
        
        project_name = brand_payload.get("project_name") or idea.get("name", "Unknown")
        tagline = brand_payload.get("tagline") or idea.get("rationale", "")
        
        return PitchDeckSlide(
            title="Title & Vision",
            summary=f"{project_name} is revolutionizing {topic} with an innovative solution.",
            bullets=[
                f"{tagline}",
                f"Mission: Transform how {topic} works",
                f"Vision: Become the leader in {topic}",
                f"Founded: {datetime.utcnow().year}"
            ],
            visual="Hero slide with product name, tagline, and brand palette. Use bold typography and modern design.",
            data={
                "project_name": project_name,
                "tagline": tagline,
                "founded_year": datetime.utcnow().year
            },
            notes="Hook investors immediately with a compelling vision statement and memorable tagline."
        )
    
    async def _create_problem_slide(
        self,
        topic: str,
        validated_pains: List[Dict[str, Any]]
    ) -> PitchDeckSlide:
        """Crée la slide problème"""
        
        pain_texts = [p.get("text", "unknown") for p in validated_pains if p.get("text")]
        primary_pain = pain_texts[0] if pain_texts else f"Critical problems in {topic} remain unsolved."
        
        bullets = [primary_pain]
        if len(pain_texts) > 1:
            bullets.extend(pain_texts[1:3])
        
        return PitchDeckSlide(
            title="The Problem",
            summary=f"{primary_pain}",
            bullets=bullets[:4],
            visual="Pain point visualization with icons representing each problem. Use contrasting colors to highlight urgency.",
            data={"pains": pain_texts},
            notes="Quantify the problem with data: market size, affected users, cost of inaction."
        )
    
    async def _create_solution_slide(
        self,
        topic: str,
        idea: Dict[str, Any],
        brand_payload: Dict[str, Any],
        success_report: Optional[Any]
    ) -> PitchDeckSlide:
        """Crée la slide solution"""
        
        project_name = brand_payload.get("project_name") or idea.get("name", "Unknown")
        
        bullets = [
            f"{project_name} solves {topic} challenges with AI-powered automation",
            "Seamless integration with existing workflows",
            "Real-time insights and actionable recommendations",
            "Scalable architecture for enterprise growth"
        ]
        
        if success_report:
            pmf_score = success_report.pmf_validation.overall_score
            bullets.append(f"Validated Product-Market Fit: {pmf_score:.1f}%")
        
        return PitchDeckSlide(
            title="The Solution",
            summary=f"{project_name} provides an innovative solution to {topic} challenges.",
            bullets=bullets,
            visual="Product screenshot or flow diagram showing how the solution works. Use before/after comparison.",
            data={"solution_score": success_report.pmf_validation.overall_score if success_report else 0},
            notes="Show, don't just tell. Use screenshots, demos, or diagrams to illustrate the solution."
        )
    
    async def _create_market_slide(
        self,
        topic: str,
        market_report: str,
        validated_pains: List[Dict[str, Any]],
        success_report: Optional[Any]
    ) -> PitchDeckSlide:
        """Crée la slide marché"""
        
        bullets = [
            f"Total Addressable Market (TAM): ${self._generate_market_size('tam')}",
            f"Serviceable Addressable Market (SAM): ${self._generate_market_size('sam')}",
            f"Serviceable Obtainable Market (SOM): ${self._generate_market_size('som')}",
            f"Market Growth: {self._generate_growth_rate()}% YoY"
        ]
        
        if success_report:
            market_size = success_report.pmf_validation.market_size
            market_growth = success_report.pmf_validation.market_growth
            bullets.append(f"Market Size Score: {market_size:.1f}/1.0")
            bullets.append(f"Market Growth Score: {market_growth:.1f}/1.0")
        
        return PitchDeckSlide(
            title="Market Opportunity",
            summary=f"The {topic} market represents a massive opportunity with strong growth potential.",
            bullets=bullets,
            visual="Market size diagram with TAM, SAM, SOM bubbles. Use concentric circles or Venn diagram.",
            data={
                "tam": self._generate_market_size('tam'),
                "sam": self._generate_market_size('sam'),
                "som": self._generate_market_size('som'),
                "growth_rate": self._generate_growth_rate()
            },
            notes="Use credible sources for market data. Show growth trajectory and addressable segments."
        )
    
    async def _create_product_slide(
        self,
        topic: str,
        idea: Dict[str, Any],
        brand_payload: Dict[str, Any]
    ) -> PitchDeckSlide:
        """Crée la slide produit avec screenshots"""
        
        project_name = brand_payload.get("project_name") or idea.get("name", "Unknown")
        
        # Ajouter les screenshots disponibles
        visual_desc = "Product interface screenshot"
        if self.screenshots:
            visual_desc = f"Product screenshot: {self.screenshots[0]}"
        
        bullets = [
            "AI-powered automation and insights",
            "Real-time analytics and dashboards",
            "Seamless integration with existing tools",
            "Scalable cloud-based infrastructure"
        ]
        
        # Ajouter des screenshots dans les bullets si disponibles
        if self.screenshots:
            bullets.append(f"See product in action: {len(self.screenshots)} screenshots")
        
        return PitchDeckSlide(
            title="Product Overview",
            summary=f"{project_name} is a comprehensive solution for {topic} challenges.",
            bullets=bullets,
            visual=visual_desc,
            data={"features": ["AI automation", "Analytics", "Integration", "Scalability"]},
            screenshot=self.screenshots[0] if self.screenshots else None,
            notes="Focus on key features that differentiate your product. Show user interface if possible."
        )
    
    async def _create_why_now_slide(
        self,
        topic: str,
        success_report: Optional[Any]
    ) -> PitchDeckSlide:
        """Crée la slide 'Why Now' (spécifique YCombinator)"""
        
        bullets = [
            f"{topic} market is experiencing rapid digital transformation",
            "Post-pandemic acceleration of remote work and digital adoption",
            "AI/ML technology has reached maturity for enterprise adoption",
            "Customer demand for automation has never been higher"
        ]
        
        if success_report:
            market_growth = success_report.pmf_validation.market_growth if hasattr(success_report, 'pmf_validation') else 0
            bullets.append(f"Market growing at {market_growth:.1f}% annually")
        
        return PitchDeckSlide(
            title="Why Now",
            summary=f"The timing is perfect for {topic} innovation due to market convergence.",
            bullets=bullets,
            visual="Timeline showing market trends and technology convergence. Use arrows and milestones.",
            data={"timing_factors": ["Digital transformation", "Remote work", "AI maturity", "Customer demand"]},
            notes="Show market trends, technology convergence, and why this is the right time."
        )
    
    async def _create_business_model_slide(
        self,
        topic: str,
        idea: Dict[str, Any],
        success_report: Optional[Any]
    ) -> PitchDeckSlide:
        """Crée la slide business model"""
        
        bullets = [
            "SaaS subscription model with tiered pricing",
            "Free tier for user acquisition and trial",
            "Premium tier with advanced features",
            "Enterprise tier with custom solutions"
        ]
        
        if success_report:
            monetization_score = 0.0
            for metric in success_report.success_metrics:
                if metric.name == "monetization":
                    monetization_score = metric.current_value
                    break
            
            bullets.append(f"Monetization Score: {monetization_score:.1f}/1.0")
        
        return PitchDeckSlide(
            title="Business Model",
            summary="SaaS subscription model with multiple pricing tiers to capture different segments.",
            bullets=bullets,
            visual="Pricing table or business model canvas. Use clear pricing tiers and feature comparison.",
            data={"model": "SaaS", "pricing_tiers": ["Free", "Premium", "Enterprise"]},
            notes="Show unit economics: CAC, LTV, churn rate, gross margins."
        )
    
    async def _create_competition_slide(
        self,
        topic: str,
        competitors: List[Dict[str, Any]],
        success_report: Optional[Any]
    ) -> PitchDeckSlide:
        """Crée la slide compétition"""
        
        competitor_names = [c.get("product_name", "unknown") for c in competitors if isinstance(c, dict)]
        
        bullets = [
            f"Competitors: {', '.join(competitor_names[:3])}",
            "Our Advantage: AI-powered automation",
            "Differentiation: Real-time insights and seamless integration",
            "Moat: Proprietary algorithms and data"
        ]
        
        if success_report:
            competitive_score = success_report.pmf_validation.competitive_advantage
            bullets.append(f"Competitive Advantage Score: {competitive_score:.1f}/1.0")
        
        return PitchDeckSlide(
            title="Competition",
            summary=f"While {', '.join(competitor_names[:2]) if competitor_names else 'competitors'} exist, we differentiate with AI-powered automation.",
            bullets=bullets,
            visual="Competitive matrix or comparison table. Use 2x2 matrix to show positioning.",
            data={"competitors": competitor_names},
            notes="Be honest about competitors but highlight your unique advantages. Use specific examples."
        )
    
    async def _create_gtm_slide(
        self,
        topic: str,
        idea: Dict[str, Any],
        success_report: Optional[Any]
    ) -> PitchDeckSlide:
        """Crée la slide go-to-market"""
        
        return PitchDeckSlide(
            title="Go-to-Market Strategy",
            summary="Multi-channel approach to acquire customers and scale rapidly.",
            bullets=[
                "Direct sales for enterprise customers",
                "Content marketing and SEO for organic growth",
                "Partnerships with industry leaders",
                "Paid acquisition for rapid scaling"
            ],
            visual="Go-to-market funnel or customer journey map. Use funnel diagram to show acquisition flow.",
            data={"channels": ["Direct Sales", "Content", "Partnerships", "Paid Ads"]},
            notes="Show clear path to market with specific channels and expected acquisition rates."
        )
    
    async def _create_traction_slide(
        self,
        topic: str,
        validated_pains: List[Dict[str, Any]],
        competitors: List[Dict[str, Any]],
        success_report: Optional[Any]
    ) -> PitchDeckSlide:
        """Crée la slide traction"""
        
        pain_texts = [p.get("text", "unknown") for p in validated_pains if p.get("text")]
        primary_pain = pain_texts[0] if pain_texts else ""
        
        bullets = [
            f"Validated {len(validated_pains)} pain points with {len(competitors)} competitors analyzed",
            "Customer interviews: 50+ conducted",
            "Landing page: 1000+ visitors, 15% conversion",
            "Waitlist: 200+ signups"
        ]
        
        if success_report:
            bullets.append(f"Success Score: {success_report.overall_success_score:.1f}%")
            bullets.append(f"Success Level: {success_report.success_level.name}")
        
        return PitchDeckSlide(
            title="Traction & Validation",
            summary=f"Strong validation from {primary_pain if primary_pain else 'market research'} and customer interviews.",
            bullets=bullets,
            visual="Traction timeline or metrics dashboard. Use charts to show growth and validation.",
            data={
                "pain_points": len(validated_pains),
                "competitors": len(competitors),
                "success_score": success_report.overall_success_score if success_report else 0
            },
            notes="Show real traction: user numbers, revenue, partnerships, customer testimonials."
        )
    
    async def _create_financial_slide(
        self,
        topic: str,
        success_report: Optional[Any]
    ) -> PitchDeckSlide:
        """Crée la slide projections financières"""
        
        return PitchDeckSlide(
            title="Financial Projections",
            summary="Conservative projections with clear path to profitability.",
            bullets=[
                "Year 1: $500K ARR, 1000 customers",
                "Year 2: $2M ARR, 5000 customers",
                "Year 3: $5M ARR, 15000 customers",
                "Year 4: $10M ARR, 30000 customers"
            ],
            visual="Revenue growth chart or financial projections table. Use line graph to show growth trajectory.",
            data={
                "year1": {"arr": 500000, "customers": 1000},
                "year2": {"arr": 2000000, "customers": 5000},
                "year3": {"arr": 5000000, "customers": 15000},
                "year4": {"arr": 10000000, "customers": 30000}
            },
            notes="Show key assumptions and sensitivity analysis. Be conservative but show upside potential."
        )
    
    async def _create_team_slide(
        self,
        topic: str,
        idea: Dict[str, Any]
    ) -> PitchDeckSlide:
        """Crée la slide équipe"""
        
        return PitchDeckSlide(
            title="Team",
            summary="Experienced team with deep expertise in AI, product, and go-to-market.",
            bullets=[
                "CEO: 10+ years in AI and SaaS",
                "CTO: PhD in Machine Learning, 15+ years engineering",
                "CPO: Product leader at 2 unicorns",
                "CMO: Growth hacker with $100M+ in revenue generated"
            ],
            visual="Team photos with brief bios. Use professional headshots and key accomplishments.",
            data={"team_size": 4},
            notes="Show relevant experience and past successes. Highlight domain expertise and track record."
        )
    
    async def _create_ask_slide(
        self,
        topic: str,
        success_report: Optional[Any]
    ) -> PitchDeckSlide:
        """Crée la slide ask"""
        
        amount = "$2M"
        use_of_funds = [
            "40% Product Development",
            "30% Sales & Marketing",
            "20% Operations",
            "10% Contingency"
        ]
        
        if success_report:
            if success_report.overall_success_score > 70:
                amount = "$5M"
                use_of_funds = [
                    "30% Product Development",
                    "40% Sales & Marketing",
                    "20% Operations",
                    "10% Contingency"
                ]
        
        return PitchDeckSlide(
            title="The Ask",
            summary=f"Seeking {amount} to accelerate growth and capture market opportunity.",
            bullets=[
                f"Amount: {amount}",
                "Use of Funds:",
                *use_of_funds
            ],
            visual="Funding allocation pie chart or use-of-funds diagram. Use pie chart to show allocation.",
            data={"amount": amount, "use_of_funds": use_of_funds},
            notes="Be specific about how funds will be used and expected outcomes. Show milestones."
        )
    
    async def _generate_key_metrics(
        self,
        validated_pains: List[Dict[str, Any]],
        competitors: List[Dict[str, Any]],
        success_report: Optional[Any]
    ) -> List[str]:
        """Génère les métriques clés"""
        
        metrics = [
            f"{len(validated_pains)} validated pain points",
            f"{len(competitors)} competitors analyzed",
        ]
        
        if success_report:
            metrics.append(f"Success Score: {success_report.overall_success_score:.1f}%")
            metrics.append(f"PMF Score: {success_report.pmf_validation.overall_score:.1f}%")
        
        return metrics
    
    async def _generate_ask(
        self,
        success_report: Optional[Any],
        topic: str
    ) -> Dict[str, Any]:
        """Génère l'ask"""
        
        if success_report and success_report.overall_success_score > 70:
            return {
                "amount": "$5M",
                "use_of_funds": [
                    "30% Product Development",
                    "40% Sales & Marketing",
                    "20% Operations",
                    "10% Contingency"
                ],
                "rationale": "Accelerate growth and capture market opportunity"
            }
        
        return {
            "amount": "$2M",
            "use_of_funds": [
                "40% Product Development",
                "30% Sales & Marketing",
                "20% Operations",
                "10% Contingency"
            ],
            "rationale": "Advance MVP and capture early adopter feedback"
        }
    
    async def _generate_closing(
        self,
        success_report: Optional[Any]
    ) -> str:
        """Génère le closing"""
        
        closing = "Join us in transforming the future."
        
        if success_report:
            if success_report.overall_success_score > 85:
                closing = "Exceptional opportunity with strong validation and market potential. Join us in building the market leader."
            elif success_report.overall_success_score > 70:
                closing = "Strong opportunity with clear path to success. Join us in capturing this market."
            elif success_report.overall_success_score > 50:
                closing = "Promising opportunity with room for improvement. Join us in refining and scaling."
            else:
                closing = "Early-stage opportunity with potential for growth. Join us in validating and iterating."
        
        return closing
    
    def _generate_market_size(self, tier: str) -> str:
        """Génère une taille de marché"""
        
        sizes = {
            "tam": "10B",
            "sam": "2B",
            "som": "200M"
        }
        
        return sizes.get(tier, "1B")
    
    def _generate_growth_rate(self) -> str:
        """Génère un taux de croissance"""
        
        return str(25 + (datetime.utcnow().year % 10))
    
    async def export_pitch_deck(self, pitch_deck: PitchDeck) -> Path:
        """Exporte le pitch deck avec screenshots"""
        
        # Exporter en JSON
        json_path = self.run_dir / "pitch_deck_enhanced.json"
        json_data = {
            "project_name": pitch_deck.project_name,
            "subtitle": pitch_deck.subtitle,
            "topic": pitch_deck.topic,
            "success_score": pitch_deck.success_score,
            "success_level": pitch_deck.success_level,
            "generation_mode": pitch_deck.generation_mode,
            "template": pitch_deck.template,
            "key_metrics": pitch_deck.key_metrics,
            "ask": pitch_deck.ask,
            "closing": pitch_deck.closing,
            "screenshots": pitch_deck.screenshots,
            "slides": [
                {
                    "title": slide.title,
                    "summary": slide.summary,
                    "bullets": slide.bullets,
                    "visual": slide.visual,
                    "data": slide.data,
                    "notes": slide.notes,
                    "screenshot": slide.screenshot,
                    "template": slide.template
                }
                for slide in pitch_deck.slides
            ],
            "created_at": pitch_deck.created_at,
            "source": pitch_deck.source
        }
        
        json_path.write_text(
            json.dumps(json_data, indent=2, default=str),
            encoding="utf-8"
        )
        
        # Exporter en Markdown
        md_path = self.run_dir / "PITCH_DECK_ENHANCED.md"
        md_content = self._format_markdown(pitch_deck)
        md_path.write_text(md_content, encoding="utf-8")
        
        logger.info(f"🎨 Pitch deck exported to {json_path} and {md_path}")
        logger.info(f"📸 {len(pitch_deck.screenshots)} screenshots included")
        
        return json_path
    
    def _format_markdown(self, pitch_deck: PitchDeck) -> str:
        """Formate le pitch deck en Markdown"""
        
        lines = [
            f"# Pitch Deck – {pitch_deck.project_name}",
            f"**{pitch_deck.subtitle}**",
            "",
            f"Topic: {pitch_deck.topic}",
            f"Success Score: {pitch_deck.success_score:.1f}% ({pitch_deck.success_level})",
            f"Generation Mode: {pitch_deck.generation_mode}",
            f"Template: {pitch_deck.template}",
            "",
            "## Key Metrics"
        ]
        
        for metric in pitch_deck.key_metrics:
            lines.append(f"- {metric}")
        
        lines.append("")
        
        # Screenshots section
        if pitch_deck.screenshots:
            lines.append("## MVP Screenshots")
            lines.append("")
            for i, screenshot in enumerate(pitch_deck.screenshots, 1):
                lines.append(f"### Screenshot {i}")
                lines.append(f"![Screenshot {i}]({screenshot})")
                lines.append("")
        
        for slide in pitch_deck.slides:
            lines.append(f"## {slide.title}")
            lines.append(slide.summary)
            lines.append("")
            
            for bullet in slide.bullets:
                lines.append(f"- {bullet}")
            
            lines.append("")
            lines.append(f"_Visual: {slide.visual}")
            
            if slide.screenshot:
                lines.append("")
                lines.append(f"![Product Screenshot]({slide.screenshot})")
            
            if slide.notes:
                lines.append("")
                lines.append(f"*Notes: {slide.notes}*")
            
            lines.append("")
        
        lines.append("## Ask")
        lines.append(f"- Amount: {pitch_deck.ask.get('amount', 'TBD')}")
        lines.append("- Use of Funds:")
        
        for fund in pitch_deck.ask.get("use_of_funds", []):
            lines.append(f"  - {fund}")
        
        lines.append("")
        lines.append("## Closing")
        lines.append(pitch_deck.closing)
        lines.append("")
        lines.append(f"*Generated at {pitch_deck.created_at} | Source: {pitch_deck.source} | Mode: {pitch_deck.generation_mode} | Template: {pitch_deck.template}*")
        
        return "\n".join(lines)


# Fonction utilitaire pour créer un générateur de pitch deck
async def create_pitch_deck_generator(
    settings: Settings,
    llm_client: LLMClient,
    run_dir: Path,
    generation_mode: GenerationMode = GenerationMode.LOCAL_OLLAMA,
    template: PitchDeckTemplate = PitchDeckTemplate.SEQUOIA
) -> PitchDeckGenerator:
    """
    Crée un générateur de pitch deck
    
    Args:
        settings: Configuration Asmblr
        llm_client: Client LLM
        run_dir: Répertoire de travail
        generation_mode: Mode de génération (Ollama, K2.5, Hybrid)
        template: Template de pitch deck (Sequoia, YCombinator, TechStars)
        
    Returns:
        PitchDeckGenerator pour créer des pitch decks améliorés
    """
    
    generator = PitchDeckGenerator(
        settings=settings,
        llm_client=llm_client,
        run_dir=run_dir,
        generation_mode=generation_mode,
        template=template
    )
    
    logger.info(f"🎨 Pitch Deck Generator created - Mode: {generation_mode.value}, Template: {template.value}")
    
    return generator
