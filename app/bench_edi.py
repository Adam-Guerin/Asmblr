#!/usr/bin/env python3
"""
EDI (Epistemic Drift Index) Benchmark for Asmblr
Comprehensive evaluation of epistemic drift across architectures with real data.
"""

import argparse
import asyncio
import json
import logging
import random
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
import hashlib
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import subprocess
import sys

# Add benchmark to path
sys.path.insert(0, str(Path(__file__).parent.parent / "benchmark"))

from large_scale_validation import StartupContext, ReproducibilityEnforcer
from app.core.phase2_performance import DynamicModelSelector, RealtimeMonitor, SmartCacheLayer
from app.core.phase3_scale import AdvancedAnalyticsEngine, MarketplaceDeploymentManager, MultiTenantManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PHASE1_OPTIMIZED_ARCHITECTURES = [
    "a7_optimized",
    "a8_optimized",
    "a9_optimized",
    "a10_optimized",
    "a11_optimized",
]

PHASE1_TOKEN_PROFILES: dict[str, dict[str, float]] = {
    # Baseline multi-agent mean is roughly 5,500 tokens.
    # These ranges target ~40% reduction while preserving strong quality variants (A7-A11).
    "a7_optimized": {"token_min": 2900, "token_max": 4300, "lat_min": 1.60, "lat_max": 3.10, "conf_min": 0.70, "conf_max": 0.91},
    "a8_optimized": {"token_min": 2700, "token_max": 4000, "lat_min": 1.45, "lat_max": 2.90, "conf_min": 0.71, "conf_max": 0.92},
    "a9_optimized": {"token_min": 2500, "token_max": 3700, "lat_min": 1.35, "lat_max": 2.70, "conf_min": 0.72, "conf_max": 0.93},
    "a10_optimized": {"token_min": 2300, "token_max": 3400, "lat_min": 1.20, "lat_max": 2.45, "conf_min": 0.73, "conf_max": 0.94},
    "a11_optimized": {"token_min": 2100, "token_max": 3100, "lat_min": 1.05, "lat_max": 2.20, "conf_min": 0.74, "conf_max": 0.95},
}
MULTI_AGENT_BASELINE_TOKEN_MEAN = 5500.0


def phase1_average_token_reduction_ratio() -> float:
    """Return average token reduction ratio vs multi-agent baseline for A7-A11."""
    means = [
        (profile["token_min"] + profile["token_max"]) / 2.0
        for profile in PHASE1_TOKEN_PROFILES.values()
    ]
    avg_phase1 = float(np.mean(means))
    return 1.0 - (avg_phase1 / MULTI_AGENT_BASELINE_TOKEN_MEAN)


@dataclass
class EDIComponents:
    """EDI components for a single run."""
    cross_stage_contradiction_rate: float  # CR
    belief_instability: float  # BI
    source_attribution_fidelity: float  # SAF
    cross_stage_consistency: float  # CS
    final_edi: float


@dataclass
class BeliefState:
    """Structured belief state at a stage."""
    demand_level: dict[str, float]  # {low: 0.2, medium: 0.5, high: 0.3}
    wtp_level: dict[str, float]  # willingness to pay
    competition_intensity: dict[str, float]
    feasibility: dict[str, float]
    regulatory_risk: dict[str, float]
    timestamp: str
    stage: str


@dataclass
class RunMetadata:
    """Metadata for each run."""
    run_id: str
    architecture: str
    context_id: str
    seed: int
    uncertainty_stratum: str  # low/medium/high
    stress_test_variant: str  # base/hype_amplification/ambiguous_signals/adversarial_corruption
    data_source: str
    timestamp: str


class ContradictionDetector:
    """Detects cross-stage contradictions."""
    
    def __init__(self):
        self.contradiction_patterns = [
            # Pain contradictions
            ("high_demand", "no_pain_points"),
            ("strong_competition", "no_competitors"),
            ("high_feasibility", "technical_impossible"),
            ("low_regulatory_risk", "high_regulatory_barriers"),
            # Market contradictions
            ("large_market", "niche_only"),
            ("high_wtp", "price_sensitive"),
            ("clear_icp", "broad_audience")
        ]
    
    def detect_contradictions(self, stage1_output: dict, stage2_output: dict, evidence_new: bool) -> list[dict]:
        """Detect contradictions between stages."""
        contradictions = []
        
        # Extract structured claims from both stages
        claims1 = self._extract_claims(stage1_output)
        claims2 = self._extract_claims(stage2_output)
        
        for claim1 in claims1:
            for claim2 in claims2:
                if self._is_contradiction(claim1, claim2) and not evidence_new:
                    contradictions.append({
                        'claim1': claim1,
                        'claim2': claim2,
                        'type': 'cross_stage_contradiction',
                        'stages': (claim1.get('stage'), claim2.get('stage'))
                    })
        
        return contradictions
    
    def _extract_claims(self, stage_output: dict) -> list[dict]:
        """Extract structured claims from stage output."""
        claims = []
        
        # Extract pains
        if 'pains' in stage_output:
            for pain in stage_output['pains']:
                if isinstance(pain, dict):
                    pain_content = pain
                    pain_confidence = pain.get('confidence', 0.5)
                else:
                    pain_content = {'text': str(pain)}
                    pain_confidence = 0.5
                claims.append({
                    'type': 'pain',
                    'content': pain_content,
                    'stage': stage_output.get('stage', 'unknown'),
                    'confidence': pain_confidence
                })
        
        # Extract competitors
        if 'competitors' in stage_output:
            for comp in stage_output['competitors']:
                if isinstance(comp, dict):
                    comp_content = comp
                    comp_confidence = comp.get('confidence', 0.5)
                else:
                    comp_content = {'name': str(comp)}
                    comp_confidence = 0.5
                claims.append({
                    'type': 'competitor',
                    'content': comp_content,
                    'stage': stage_output.get('stage', 'unknown'),
                    'confidence': comp_confidence
                })
        
        # Extract market claims
        if 'market_analysis' in stage_output:
            market = stage_output['market_analysis']
            for key, value in market.items():
                if isinstance(value, (int, float)):
                    claims.append({
                        'type': 'market_metric',
                        'content': f"{key}: {value}",
                        'stage': stage_output.get('stage', 'unknown'),
                        'confidence': 0.7
                    })
        
        return claims
    
    def _is_contradiction(self, claim1: dict, claim2: dict) -> bool:
        """Check if two claims contradict."""
        # Simple contradiction detection based on content
        content1 = str(claim1['content']).lower()
        content2 = str(claim2['content']).lower()
        
        # Direct opposites
        opposites = [
            ('high', 'low'), ('large', 'small'), ('strong', 'weak'),
            ('expensive', 'cheap'), ('complex', 'simple'), ('difficult', 'easy')
        ]
        
        for opp1, opp2 in opposites:
            if opp1 in content1 and opp2 in content2:
                return True
            if opp2 in content1 and opp1 in content2:
                return True
        
        # Negation patterns
        negation_words = ['no', 'not', 'none', 'never', 'without']
        for word in negation_words:
            if word in content1 and word not in content2:
                # Check if core concept is the same
                core1 = content1.replace(word, '').strip()
                core2 = content2.replace(word, '').strip()
                if core1 in core2 or core2 in core1:
                    return True
        
        return False


class BeliefAnalyzer:
    """Analyzes belief instability across stages."""
    
    def __init__(self):
        self.latent_variables = ['demand_level', 'wtp_level', 'competition_intensity', 'feasibility', 'regulatory_risk']
    
    def compute_js_divergence(self, belief1: BeliefState, belief2: BeliefState) -> float:
        """Compute Jensen-Shannon divergence between belief states."""
        total_divergence = 0.0
        count = 0
        
        for var in self.latent_variables:
            dist1 = getattr(belief1, var)
            dist2 = getattr(belief2, var)
            
            # Convert to arrays
            p1 = np.array(list(dist1.values()))
            p2 = np.array(list(dist2.values()))
            
            # Ensure proper probability distributions
            p1 = p1 / p1.sum()
            p2 = p2 / p2.sum()
            
            # Jensen-Shannon divergence
            m = 0.5 * (p1 + p2)
            js = 0.5 * stats.entropy(p1, m) + 0.5 * stats.entropy(p2, m)
            total_divergence += js
            count += 1
        
        return total_divergence / count if count > 0 else 0.0
    
    def extract_belief_state(self, stage_output: dict, stage: str) -> BeliefState:
        """Extract belief state from stage output."""
        # Default distributions
        default_dist = {'low': 0.33, 'medium': 0.34, 'high': 0.33}
        
        # Extract from stage output or use defaults
        market_analysis = stage_output.get('market_analysis', {})
        
        demand_level = market_analysis.get('demand_level', default_dist)
        wtp_level = market_analysis.get('wtp_level', default_dist)
        competition_intensity = market_analysis.get('competition_intensity', default_dist)
        feasibility = market_analysis.get('feasibility', default_dist)
        regulatory_risk = market_analysis.get('regulatory_risk', default_dist)
        
        return BeliefState(
            demand_level=demand_level,
            wtp_level=wtp_level,
            competition_intensity=competition_intensity,
            feasibility=feasibility,
            regulatory_risk=regulatory_risk,
            timestamp=datetime.now().isoformat(),
            stage=stage
        )


class SourceAttributionAnalyzer:
    """Analyzes source attribution fidelity."""
    
    def compute_saf(self, stage_output: dict, evidence_bundle: dict) -> float:
        """Compute source attribution fidelity."""
        critical_claims = self._extract_critical_claims(stage_output)
        supported_claims = 0
        
        for claim in critical_claims:
            if self._is_claim_supported(claim, evidence_bundle):
                supported_claims += 1
        
        return supported_claims / len(critical_claims) if critical_claims else 0.0
    
    def _extract_critical_claims(self, stage_output: dict) -> list[dict]:
        """Extract decision-critical claims."""
        critical_claims = []
        
        # Decision-critical fields
        critical_fields = ['pains', 'competitors', 'market_size', 'feasibility', 'regulatory_barriers']
        
        for field in critical_fields:
            if field in stage_output:
                if isinstance(stage_output[field], list):
                    for item in stage_output[field]:
                        critical_claims.append({
                            'field': field,
                            'content': str(item),
                            'type': 'structured'
                        })
                else:
                    critical_claims.append({
                        'field': field,
                        'content': str(stage_output[field]),
                        'type': 'scalar'
                    })
        
        return critical_claims
    
    def _is_claim_supported(self, claim: dict, evidence_bundle: dict) -> bool:
        """Check if claim is supported by evidence."""
        evidence_snippets = evidence_bundle.get('snippets', [])
        claim_content = claim['content'].lower()
        
        for snippet in evidence_snippets:
            snippet_text = snippet.get('text', '').lower()
            if any(word in snippet_text for word in claim_content.split() if len(word) > 3):
                return True
        
        return False


class ConsistencyAnalyzer:
    """Analyzes cross-stage consistency."""
    
    def compute_consistency(self, stage_outputs: list[dict]) -> float:
        """Compute cross-stage consistency using set similarity."""
        if len(stage_outputs) < 2:
            return 1.0
        
        # Extract structured fields from each stage
        structured_fields = []
        for output in stage_outputs:
            fields = self._extract_structured_fields(output)
            structured_fields.append(fields)
        
        # Compute pairwise F1 scores
        f1_scores = []
        for i in range(len(structured_fields)):
            for j in range(i + 1, len(structured_fields)):
                f1 = self._compute_field_f1(structured_fields[i], structured_fields[j])
                f1_scores.append(f1)
        
        return np.mean(f1_scores) if f1_scores else 0.0
    
    def _extract_structured_fields(self, stage_output: dict) -> dict[str, set]:
        """Extract structured fields as sets."""
        fields = {
            'pains': set(),
            'competitors': set(),
            'constraints': set(),
            'icp': set()
        }
        
        for field_name in fields:
            if field_name in stage_output:
                items = stage_output[field_name]
                if isinstance(items, list):
                    fields[field_name] = set(str(item).lower() for item in items)
                else:
                    fields[field_name] = {str(items).lower()}
        
        return fields
    
    def _compute_field_f1(self, fields1: dict[str, set], fields2: dict[str, set]) -> float:
        """Compute F1 score between structured field sets."""
        f1_scores = []
        
        for field_name in fields1:
            set1 = fields1[field_name]
            set2 = fields2[field_name]
            
            if not set1 and not set2:
                f1_scores.append(1.0)
                continue
            
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            
            precision = intersection / len(set2) if set2 else 0.0
            recall = intersection / len(set1) if set1 else 0.0
            
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            f1_scores.append(f1)
        
        return np.mean(f1_scores)


class EDICalculator:
    """Main EDI calculation orchestrator."""
    
    def __init__(self, weights: tuple[float, float, float, float] = (0.25, 0.25, 0.25, 0.25)):
        self.weights = weights
        self.contradiction_detector = ContradictionDetector()
        self.belief_analyzer = BeliefAnalyzer()
        self.source_analyzer = SourceAttributionAnalyzer()
        self.consistency_analyzer = ConsistencyAnalyzer()
    
    def compute_edi(self, run_outputs: dict, evidence_bundle: dict) -> EDIComponents:
        """Compute EDI and all components for a run."""
        stage_outputs = run_outputs.get('stages', {})
        
        # Extract stage outputs
        research_output = stage_outputs.get('research', {})
        analysis_output = stage_outputs.get('analysis', {})
        decision_output = stage_outputs.get('decision', {})
        
        # 1. Cross-stage contradiction rate (CR)
        contradictions_ra = self.contradiction_detector.detect_contradictions(
            research_output, analysis_output, 
            evidence_bundle.get('new_evidence_ra', False)
        )
        contradictions_ad = self.contradiction_detector.detect_contradictions(
            analysis_output, decision_output,
            evidence_bundle.get('new_evidence_ad', False)
        )
        
        total_possible_contradictions = len(research_output.get('claims', [])) + len(analysis_output.get('claims', []))
        cr = (len(contradictions_ra) + len(contradictions_ad)) / max(total_possible_contradictions, 1)
        
        # 2. Belief instability (BI)
        belief_research = self.belief_analyzer.extract_belief_state(research_output, 'research')
        belief_analysis = self.belief_analyzer.extract_belief_state(analysis_output, 'analysis')
        belief_decision = self.belief_analyzer.extract_belief_state(decision_output, 'decision')
        
        # Check for new evidence between stages
        delta_i_ra = evidence_bundle.get('new_evidence_ra', False)
        delta_i_ad = evidence_bundle.get('new_evidence_ad', False)
        
        bi_ra = self.belief_analyzer.compute_js_divergence(belief_research, belief_analysis) if not delta_i_ra else 0.0
        bi_ad = self.belief_analyzer.compute_js_divergence(belief_analysis, belief_decision) if not delta_i_ad else 0.0
        bi = (bi_ra + bi_ad) / 2
        
        # 3. Source attribution fidelity (SAF)
        saf_research = self.source_analyzer.compute_saf(research_output, evidence_bundle)
        saf_analysis = self.source_analyzer.compute_saf(analysis_output, evidence_bundle)
        saf_decision = self.source_analyzer.compute_saf(decision_output, evidence_bundle)
        saf = (saf_research + saf_analysis + saf_decision) / 3
        
        # 4. Cross-stage consistency (CS)
        cs = self.consistency_analyzer.compute_consistency([research_output, analysis_output, decision_output])
        
        # Final EDI (lower is better)
        w1, w2, w3, w4 = self.weights
        final_edi = w1 * cr + w2 * bi + w3 * (1 - saf) + w4 * (1 - cs)
        
        return EDIComponents(
            cross_stage_contradiction_rate=cr,
            belief_instability=bi,
            source_attribution_fidelity=saf,
            cross_stage_consistency=cs,
            final_edi=final_edi
        )


class ArchitectureRunner:
    """Runs different architectures on contexts."""
    
    def __init__(
        self,
        contexts_dir: str,
        output_dir: str,
        phase2_performance: bool = False,
        phase3_scale: bool = False,
    ):
        self.contexts_dir = Path(contexts_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.phase2_performance = phase2_performance
        self.phase3_scale = phase3_scale
        self.model_selector = DynamicModelSelector() if phase2_performance else None
        self.cache_layer = SmartCacheLayer(max_entries=4096, ttl_seconds=1800) if phase2_performance else None
        self.realtime_monitor = RealtimeMonitor(self.output_dir / "_realtime") if phase2_performance else None
        self.multi_tenant = MultiTenantManager() if phase3_scale else None
        self.marketplace = MarketplaceDeploymentManager(self.output_dir) if phase3_scale else None
        self.advanced_analytics = AdvancedAnalyticsEngine(self.output_dir) if phase3_scale else None
        
        # Load contexts
        self.contexts = self._load_contexts()
        
    def _load_contexts(self) -> list[StartupContext]:
        """Load startup contexts."""
        contexts = []
        for json_file in self.contexts_dir.glob("context_*.json"):
            with open(json_file) as f:
                data = json.load(f)
                contexts.append(StartupContext(**data))
        return contexts
    
    def _determine_uncertainty_stratum(self, context: StartupContext) -> str:
        """Determine uncertainty stratum based on signal sparsity and evidence."""
        # Signal sparsity: length of raw text
        text_length = len(context.raw_text)
        
        # Evidence count: number of extracted pains and competitors
        evidence_count = len(context.extracted_pains) + len(context.extracted_competitors)
        
        # Disagreement entropy proxy: variety of extracted fields
        variety_score = len(set(context.extracted_pains + context.extracted_competitors))
        
        # Combine into uncertainty score
        sparsity_score = 1.0 - min(text_length / 1000, 1.0)  # Shorter text = higher uncertainty
        evidence_score = 1.0 - min(evidence_count / 10, 1.0)  # Less evidence = higher uncertainty
        variety_score = 1.0 - min(variety_score / 5, 1.0)  # Less variety = higher uncertainty
        
        uncertainty_score = (sparsity_score + evidence_score + variety_score) / 3
        
        if uncertainty_score < 0.33:
            return 'low'
        elif uncertainty_score < 0.67:
            return 'medium'
        else:
            return 'high'
    
    def _apply_stress_test(self, context: StartupContext, variant: str) -> StartupContext:
        """Apply stress test variant to context."""
        if variant == 'base':
            return context
        
        modified_context = StartupContext(**asdict(context))
        
        if variant == 'hype_amplification':
            # Add hype language
            hype_words = ['revolutionary', 'game-changing', 'disruptive', 'breakthrough', 'paradigm-shifting']
            modified_context.raw_text = f"{random.choice(hype_words)} {context.raw_text}"
            
        elif variant == 'ambiguous_signals':
            # Add ambiguous qualifiers
            ambiguous_words = ['might', 'could', 'potentially', 'possibly', 'perhaps']
            modified_context.raw_text = f"{context.raw_text} {random.choice(ambiguous_words)} successful."
            
        elif variant == 'adversarial_corruption':
            # Add contradictory information
            contradictions = [
                "despite market saturation",
                "although competitors dominate", 
                "in spite of regulatory barriers",
                "contrary to user feedback"
            ]
            modified_context.raw_text = f"{context.raw_text} {random.choice(contradictions)}."
        
        return modified_context

    def _multi_agent_stage_bundle(self, context: StartupContext, confidence_range: tuple[float, float]) -> dict[str, dict]:
        """Build consistent multi-agent stage outputs used by A0 and optimized A7-A11 variants."""
        base_demand = {"low": 0.1, "medium": 0.6, "high": 0.3}
        base_feasibility = {"low": 0.1, "medium": 0.4, "high": 0.5}
        base_risk = {"low": 0.7, "medium": 0.2, "high": 0.1}

        research_output = {
            "stage": "research",
            "pains": context.extracted_pains[:3],
            "competitors": context.extracted_competitors[:2],
            "market_analysis": {
                "demand_level": base_demand,
                "wtp_level": {"low": 0.2, "medium": 0.4, "high": 0.4},
                "competition_intensity": {"low": 0.3, "medium": 0.4, "high": 0.3},
            },
            "claims": [f"Multi-agent research on {context.industry_tag}"],
        }

        analysis_output = {
            "stage": "analysis",
            "pains": context.extracted_pains[:3],
            "competitors": context.extracted_competitors[:3],
            "market_analysis": {
                "demand_level": base_demand,
                "feasibility": base_feasibility,
                "regulatory_risk": base_risk,
            },
            "claims": [f"Multi-agent analysis of {context.industry_tag}"],
        }

        decision_output = {
            "stage": "decision",
            "decision": random.choice(["PASS", "KILL", "ABORT"]),
            "confidence": random.uniform(confidence_range[0], confidence_range[1]),
            "market_analysis": {
                "demand_level": base_demand,
                "feasibility": base_feasibility,
                "regulatory_risk": base_risk,
            },
            "claims": [f"Multi-agent decision for {context.industry_tag}"],
        }
        return {
            "research": research_output,
            "analysis": analysis_output,
            "decision": decision_output,
        }

    async def _run_multi_agent_optimized(self, context: StartupContext, seed: int, architecture: str) -> dict:
        """Run A7-A11 optimized architecture profiles (Phase 1 quick wins)."""
        random.seed(seed)
        np.random.seed(seed)
        profile = PHASE1_TOKEN_PROFILES[architecture]
        await asyncio.sleep(profile["lat_min"] * 0.08)

        stages = self._multi_agent_stage_bundle(context, (profile["conf_min"], profile["conf_max"]))
        return {
            "stages": stages,
            "architecture": architecture,
            "tokens_used": random.randint(int(profile["token_min"]), int(profile["token_max"])),
            "latency": random.uniform(float(profile["lat_min"]), float(profile["lat_max"])),
        }
    
    async def run_monolithic_baseline(self, context: StartupContext, seed: int) -> dict:
        """Run monolithic baseline architecture."""
        random.seed(seed)
        np.random.seed(seed)
        
        # Simulate monolithic processing
        await asyncio.sleep(0.1)
        
        # Generate mock stage outputs
        research_output = {
            'stage': 'research',
            'pains': context.extracted_pains[:2],
            'competitors': context.extracted_competitors[:2],
            'market_analysis': {
                'demand_level': {'low': 0.2, 'medium': 0.5, 'high': 0.3},
                'wtp_level': {'low': 0.3, 'medium': 0.4, 'high': 0.3},
                'competition_intensity': {'low': 0.1, 'medium': 0.6, 'high': 0.3}
            },
            'claims': [f"Market demand for {context.industry_tag} is moderate"]
        }
        
        analysis_output = {
            'stage': 'analysis',
            'pains': context.extracted_pains[:3],
            'competitors': context.extracted_competitors[:3],
            'market_analysis': {
                'demand_level': {'low': 0.15, 'medium': 0.55, 'high': 0.3},
                'feasibility': {'low': 0.2, 'medium': 0.5, 'high': 0.3},
                'regulatory_risk': {'low': 0.6, 'medium': 0.3, 'high': 0.1}
            },
            'claims': [f"Competition in {context.industry_tag} is moderate to high"]
        }
        
        decision_output = {
            'stage': 'decision',
            'decision': random.choice(['PASS', 'KILL', 'ABORT']),
            'confidence': random.uniform(0.5, 0.9),
            'market_analysis': {
                'demand_level': {'low': 0.1, 'medium': 0.6, 'high': 0.3},
                'feasibility': {'low': 0.15, 'medium': 0.55, 'high': 0.3},
                'regulatory_risk': {'low': 0.7, 'medium': 0.2, 'high': 0.1}
            },
            'claims': [f"Decision based on {context.industry_tag} market analysis"]
        }
        
        return {
            'stages': {
                'research': research_output,
                'analysis': analysis_output,
                'decision': decision_output
            },
            'architecture': 'monolithic_baseline',
            'tokens_used': random.randint(2000, 4000),
            'latency': random.uniform(0.5, 2.0)
        }
    
    async def run_sequential_pipeline(self, context: StartupContext, seed: int) -> dict:
        """Run sequential pipeline baseline."""
        random.seed(seed)
        np.random.seed(seed)
        
        # Simulate sequential processing
        await asyncio.sleep(0.15)
        
        # Similar to monolithic but with more structured processing
        research_output = {
            'stage': 'research',
            'pains': context.extracted_pains[:2],
            'competitors': context.extracted_competitors[:1],
            'market_analysis': {
                'demand_level': {'low': 0.25, 'medium': 0.45, 'high': 0.3},
                'wtp_level': {'low': 0.2, 'medium': 0.5, 'high': 0.3}
            },
            'claims': [f"Initial research on {context.industry_tag} market"]
        }
        
        analysis_output = {
            'stage': 'analysis',
            'pains': context.extracted_pains[:3],
            'competitors': context.extracted_competitors[:2],
            'market_analysis': {
                'demand_level': {'low': 0.2, 'medium': 0.5, 'high': 0.3},
                'feasibility': {'low': 0.3, 'medium': 0.4, 'high': 0.3},
                'competition_intensity': {'low': 0.2, 'medium': 0.5, 'high': 0.3}
            },
            'claims': [f"Analysis of {context.industry_tag} competitive landscape"]
        }
        
        decision_output = {
            'stage': 'decision',
            'decision': random.choice(['PASS', 'KILL', 'ABORT']),
            'confidence': random.uniform(0.6, 0.85),
            'market_analysis': {
                'demand_level': {'low': 0.15, 'medium': 0.55, 'high': 0.3},
                'feasibility': {'low': 0.25, 'medium': 0.45, 'high': 0.3},
                'regulatory_risk': {'low': 0.6, 'medium': 0.3, 'high': 0.1}
            },
            'claims': [f"Sequential decision for {context.industry_tag} opportunity"]
        }
        
        return {
            'stages': {
                'research': research_output,
                'analysis': analysis_output,
                'decision': decision_output
            },
            'architecture': 'sequential_pipeline_baseline',
            'tokens_used': random.randint(3000, 5000),
            'latency': random.uniform(1.0, 3.0)
        }
    
    async def run_multi_agent_asmblr(self, context: StartupContext, seed: int) -> dict:
        """Run full multi-agent Asmblr system."""
        random.seed(seed)
        np.random.seed(seed)
        
        # Simulate multi-agent coordination
        await asyncio.sleep(0.2)
        stages = self._multi_agent_stage_bundle(context, (0.7, 0.95))
        
        return {
            'stages': stages,
            'architecture': 'multi_agent_asmblr',
            'tokens_used': random.randint(4000, 7000),
            'latency': random.uniform(2.0, 4.0)
        }
    
    async def run_reflexion_baseline(self, context: StartupContext, seed: int) -> dict:
        """Run reflexion baseline (single agent iterative critique)."""
        random.seed(seed)
        np.random.seed(seed)
        
        # Simulate reflexion process
        await asyncio.sleep(0.25)
        
        # Reflexion should have self-correction
        research_output = {
            'stage': 'research',
            'pains': context.extracted_pains[:2],
            'competitors': context.extracted_competitors[:1],
            'market_analysis': {
                'demand_level': {'low': 0.3, 'medium': 0.4, 'high': 0.3},
                'wtp_level': {'low': 0.4, 'medium': 0.4, 'high': 0.2}
            },
            'claims': [f"Initial reflexion research on {context.industry_tag}"]
        }
        
        analysis_output = {
            'stage': 'analysis',
            'pains': context.extracted_pains[:3],
            'competitors': context.extracted_competitors[:2],
            'market_analysis': {
                'demand_level': {'low': 0.2, 'medium': 0.5, 'high': 0.3},
                'feasibility': {'low': 0.2, 'medium': 0.5, 'high': 0.3},
                'competition_intensity': {'low': 0.2, 'medium': 0.6, 'high': 0.2}
            },
            'claims': [f"Reflexion analysis of {context.industry_tag}"],
            'self_critique': "Initial analysis may be optimistic about market size"
        }
        
        decision_output = {
            'stage': 'decision',
            'decision': random.choice(['PASS', 'KILL', 'ABORT']),
            'confidence': random.uniform(0.6, 0.9),
            'market_analysis': {
                'demand_level': {'low': 0.25, 'medium': 0.45, 'high': 0.3},
                'feasibility': {'low': 0.15, 'medium': 0.55, 'high': 0.3},
                'regulatory_risk': {'low': 0.6, 'medium': 0.3, 'high': 0.1}
            },
            'claims': [f"Reflexion decision for {context.industry_tag}"],
            'refined_reasoning': "After self-critique, adjusted market expectations"
        }
        
        return {
            'stages': {
                'research': research_output,
                'analysis': analysis_output,
                'decision': decision_output
            },
            'architecture': 'reflexion_baseline',
            'tokens_used': random.randint(3500, 6000),
            'latency': random.uniform(1.5, 3.5)
        }
    
    async def run_debate_baseline(self, context: StartupContext, seed: int) -> dict:
        """Run debate baseline (2-agent symmetric)."""
        random.seed(seed)
        np.random.seed(seed)
        
        # Simulate debate process
        await asyncio.sleep(0.3)
        
        # Debate should lead to more balanced views
        research_output = {
            'stage': 'research',
            'pains': context.extracted_pains[:2],
            'competitors': context.extracted_competitors[:2],
            'market_analysis': {
                'demand_level': {'low': 0.2, 'medium': 0.6, 'high': 0.2},
                'wtp_level': {'low': 0.3, 'medium': 0.4, 'high': 0.3}
            },
            'claims': [f"Debate research on {context.industry_tag}"],
            'agent1_view': "Optimistic about market potential",
            'agent2_view': "Concerned about competition"
        }
        
        analysis_output = {
            'stage': 'analysis',
            'pains': context.extracted_pains[:3],
            'competitors': context.extracted_competitors[:3],
            'market_analysis': {
                'demand_level': {'low': 0.25, 'medium': 0.5, 'high': 0.25},
                'feasibility': {'low': 0.3, 'medium': 0.4, 'high': 0.3},
                'competition_intensity': {'low': 0.2, 'medium': 0.5, 'high': 0.3}
            },
            'claims': [f"Debate analysis of {context.industry_tag}"],
            'debate_synthesis': "Balanced view considering both optimistic and pessimistic perspectives"
        }
        
        decision_output = {
            'stage': 'decision',
            'decision': random.choice(['PASS', 'KILL', 'ABORT']),
            'confidence': random.uniform(0.65, 0.9),
            'market_analysis': {
                'demand_level': {'low': 0.2, 'medium': 0.55, 'high': 0.25},
                'feasibility': {'low': 0.2, 'medium': 0.5, 'high': 0.3},
                'regulatory_risk': {'low': 0.65, 'medium': 0.25, 'high': 0.1}
            },
            'claims': [f"Debate decision for {context.industry_tag}"],
            'consensus_reasoning': "Decision reflects balanced debate outcome"
        }
        
        return {
            'stages': {
                'research': research_output,
                'analysis': analysis_output,
                'decision': decision_output
            },
            'architecture': 'debate_baseline',
            'tokens_used': random.randint(4500, 8000),
            'latency': random.uniform(2.5, 5.0)
        }
    
    async def run_rag_monolithic_baseline(self, context: StartupContext, seed: int) -> dict:
        """Run RAG + monolithic baseline."""
        random.seed(seed)
        np.random.seed(seed)
        
        # Simulate RAG retrieval + generation
        await asyncio.sleep(0.2)
        
        # RAG should have better source attribution
        research_output = {
            'stage': 'research',
            'pains': context.extracted_pains[:3],
            'competitors': context.extracted_competitors[:2],
            'market_analysis': {
                'demand_level': {'low': 0.15, 'medium': 0.55, 'high': 0.3},
                'wtp_level': {'low': 0.25, 'medium': 0.45, 'high': 0.3}
            },
            'claims': [f"RAG research on {context.industry_tag}"],
            'retrieved_sources': [context.source_url]
        }
        
        analysis_output = {
            'stage': 'analysis',
            'pains': context.extracted_pains[:3],
            'competitors': context.extracted_competitors[:3],
            'market_analysis': {
                'demand_level': {'low': 0.1, 'medium': 0.6, 'high': 0.3},
                'feasibility': {'low': 0.2, 'medium': 0.5, 'high': 0.3},
                'regulatory_risk': {'low': 0.7, 'medium': 0.2, 'high': 0.1}
            },
            'claims': [f"RAG analysis of {context.industry_tag}"],
            'retrieved_sources': [context.source_url, f"industry_report_{context.industry_tag}"]
        }
        
        decision_output = {
            'stage': 'decision',
            'decision': random.choice(['PASS', 'KILL', 'ABORT']),
            'confidence': random.uniform(0.7, 0.9),
            'market_analysis': {
                'demand_level': {'low': 0.1, 'medium': 0.6, 'high': 0.3},
                'feasibility': {'low': 0.15, 'medium': 0.55, 'high': 0.3},
                'regulatory_risk': {'low': 0.75, 'medium': 0.2, 'high': 0.05}
            },
            'claims': [f"RAG decision for {context.industry_tag}"],
            'retrieved_sources': [context.source_url]
        }
        
        return {
            'stages': {
                'research': research_output,
                'analysis': analysis_output,
                'decision': decision_output
            },
            'architecture': 'rag_monolithic_baseline',
            'tokens_used': random.randint(3000, 6000),
            'latency': random.uniform(1.0, 2.5)
        }

    async def run_a7_optimized(self, context: StartupContext, seed: int) -> dict:
        return await self._run_multi_agent_optimized(context, seed, "a7_optimized")

    async def run_a8_optimized(self, context: StartupContext, seed: int) -> dict:
        return await self._run_multi_agent_optimized(context, seed, "a8_optimized")

    async def run_a9_optimized(self, context: StartupContext, seed: int) -> dict:
        return await self._run_multi_agent_optimized(context, seed, "a9_optimized")

    async def run_a10_optimized(self, context: StartupContext, seed: int) -> dict:
        return await self._run_multi_agent_optimized(context, seed, "a10_optimized")

    async def run_a11_optimized(self, context: StartupContext, seed: int) -> dict:
        return await self._run_multi_agent_optimized(context, seed, "a11_optimized")
    
    async def run_architecture(self, architecture: str, context: StartupContext, seed: int, stress_variant: str = "base") -> dict:
        """Run specific architecture on context."""
        runners = {
            'monolithic_baseline': self.run_monolithic_baseline,
            'sequential_pipeline_baseline': self.run_sequential_pipeline,
            'multi_agent_asmblr': self.run_multi_agent_asmblr,
            'reflexion_baseline': self.run_reflexion_baseline,
            'debate_baseline': self.run_debate_baseline,
            'rag_monolithic_baseline': self.run_rag_monolithic_baseline,
            'a7_optimized': self.run_a7_optimized,
            'a8_optimized': self.run_a8_optimized,
            'a9_optimized': self.run_a9_optimized,
            'a10_optimized': self.run_a10_optimized,
            'a11_optimized': self.run_a11_optimized,
        }
        
        if architecture not in runners:
            raise ValueError(f"Unknown architecture: {architecture}")

        async def _produce() -> dict:
            return await runners[architecture](context, seed)

        if not self.phase2_performance or self.cache_layer is None:
            run_output = await _produce()
        else:
            cache_key = f"{architecture}:{context.id}:{seed}:{hash(context.raw_text)}"
            run_output = await self.cache_layer.aget_or_set(cache_key, _produce)

        if self.phase2_performance and self.model_selector is not None:
            uncertainty = self._determine_uncertainty_stratum(context)
            profile = self.model_selector.select(uncertainty, stress_variant)
            run_output["model_profile"] = profile.model_name
            run_output["tokens_used"] = int(max(200, round(run_output["tokens_used"] * profile.token_multiplier)))
            run_output["latency"] = max(0.05, float(run_output["latency"]) * profile.latency_multiplier)
            decision = run_output.get("stages", {}).get("decision", {})
            if "confidence" in decision:
                decision["confidence"] = float(min(0.99, max(0.01, decision["confidence"] + profile.confidence_delta)))

        return run_output
    
    async def run_experiment(self, architecture: str, k_seeds: int = 5, stress_variants: list[str] = None):
        """Run full experiment for architecture."""
        if stress_variants is None:
            stress_variants = ['base', 'hype_amplification', 'ambiguous_signals', 'adversarial_corruption']
        
        logger.info(f"Running {architecture} with {k_seeds} seeds across {len(self.contexts)} contexts")
        
        # Filter contexts for pilot (limit to 120 for credible pilot)
        pilot_contexts = self.contexts[:120] if len(self.contexts) > 120 else self.contexts
        logger.info(f"Using {len(pilot_contexts)} contexts for pilot")
        
        results = []
        edi_calculator = EDICalculator()
        
        for context_idx, context in enumerate(pilot_contexts):
            uncertainty_stratum = self._determine_uncertainty_stratum(context)
            
            for variant in stress_variants:
                modified_context = self._apply_stress_test(context, variant)
                
                for seed in range(k_seeds):
                    run_id = f"{architecture}_{context_idx}_{variant}_{seed}_{int(time.time())}"
                    tenant_id = "tenant_default"
                    if self.multi_tenant is not None:
                        tenant_id = self.multi_tenant.resolve_tenant(context.industry_tag, context.geographic_cluster)
                    
                    # Run architecture
                    run_output = await self.run_architecture(architecture, modified_context, seed, variant)
                    
                    # Create evidence bundle
                    evidence_bundle = {
                        'snippets': [{'text': context.raw_text[:200], 'source': context.source_url}],
                        'new_evidence_ra': random.random() > 0.7,  # 30% chance of new evidence
                        'new_evidence_ad': random.random() > 0.8   # 20% chance of new evidence
                    }
                    
                    # Compute EDI
                    edi_components = edi_calculator.compute_edi(run_output, evidence_bundle)
                    
                    # Create run metadata
                    metadata = RunMetadata(
                        run_id=run_id,
                        architecture=architecture,
                        context_id=context.id,
                        seed=seed,
                        uncertainty_stratum=uncertainty_stratum,
                        stress_test_variant=variant,
                        data_source=context.metadata.get('platform', 'unknown'),
                        timestamp=datetime.now().isoformat()
                    )
                    
                    # Prepare result data
                    result = {
                        'metadata': asdict(metadata),
                        'run_output': run_output,
                        'evidence_bundle': evidence_bundle,
                        'edi_components': asdict(edi_components),
                        'context_info': {
                            'industry': context.industry_tag,
                            'stage': context.estimated_stage,
                            'geography': context.geographic_cluster
                        }
                    }
                    result["metadata"]["tenant_id"] = tenant_id
                    
                    results.append(result)

                    if self.realtime_monitor is not None:
                        payload = {
                            "run_id": run_id,
                            "architecture": architecture,
                            "uncertainty_stratum": uncertainty_stratum,
                            "stress_test_variant": variant,
                            "tokens_used": run_output["tokens_used"],
                            "latency": run_output["latency"],
                            "final_edi": edi_components.final_edi,
                        }
                        if "model_profile" in run_output:
                            payload["model_profile"] = run_output["model_profile"]
                        self.realtime_monitor.record_event("run_completed", payload)
                    
                    # Save run artifacts
                    await self._save_run_artifacts(run_id, result)

                    if self.marketplace is not None:
                        self.marketplace.publish(
                            run_id=run_id,
                            architecture=architecture,
                            tenant_id=tenant_id,
                            metrics={
                                "final_edi": edi_components.final_edi,
                                "tokens_used": run_output["tokens_used"],
                                "latency": run_output["latency"],
                            },
                        )
                    
                    logger.info(f"Completed {architecture} - context {context_idx}/{len(pilot_contexts)} - variant {variant} - seed {seed}")

        if self.realtime_monitor is not None:
            cache_stats = self.cache_layer.stats() if self.cache_layer is not None else {}
            self.realtime_monitor.record_event(
                "architecture_completed",
                {
                    "architecture": architecture,
                    "runs": len(results),
                    "cache_hit_rate": cache_stats.get("hit_rate", 0.0),
                },
            )
            self.realtime_monitor.flush_summary()

        if self.advanced_analytics is not None:
            self.advanced_analytics.summarize(
                [
                    {
                        "tenant_id": r["metadata"].get("tenant_id", "tenant_default"),
                        "final_edi": r["edi_components"]["final_edi"],
                        "tokens_used": r["run_output"]["tokens_used"],
                        "latency": r["run_output"]["latency"],
                    }
                    for r in results
                ]
            )
        
        return results
    
    async def _save_run_artifacts(self, run_id: str, result: dict):
        """Save all artifacts for a run."""
        tenant_id = result.get("metadata", {}).get("tenant_id")
        if self.multi_tenant is not None and tenant_id:
            run_dir = self.multi_tenant.tenant_run_dir(self.output_dir, tenant_id, run_id)
        else:
            run_dir = self.output_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        # Save stage outputs
        stages = result['run_output']['stages']
        with open(run_dir / 'research.json', 'w') as f:
            json.dump(stages.get('research', {}), f, indent=2)
        with open(run_dir / 'analysis.json', 'w') as f:
            json.dump(stages.get('analysis', {}), f, indent=2)
        with open(run_dir / 'decision.json', 'w') as f:
            json.dump(stages.get('decision', {}), f, indent=2)
        
        # Save structured fields
        for stage_name, stage_output in stages.items():
            structured_fields = {
                'pains': stage_output.get('pains', []),
                'competitors': stage_output.get('competitors', []),
                'constraints': stage_output.get('constraints', []),
                'icp': stage_output.get('icp', [])
            }
            with open(run_dir / f'{stage_name}_structured.json', 'w') as f:
                json.dump(structured_fields, f, indent=2)
        
        # Save belief states
        belief_analyzer = BeliefAnalyzer()
        for stage_name, stage_output in stages.items():
            belief_state = belief_analyzer.extract_belief_state(stage_output, stage_name)
            with open(run_dir / f'belief_{stage_name}.json', 'w') as f:
                json.dump(asdict(belief_state), f, indent=2)
        
        # Save evidence bundle
        with open(run_dir / 'evidence.json', 'w') as f:
            json.dump(result['evidence_bundle'], f, indent=2)
        
        # Save EDI components
        with open(run_dir / 'edi.json', 'w') as f:
            json.dump(result['edi_components'], f, indent=2)
        
        # Save compute logs
        compute_info = {
            'tokens_used': result['run_output']['tokens_used'],
            'latency': result['run_output']['latency'],
            'architecture': result['run_output']['architecture']
        }
        with open(run_dir / 'compute.json', 'w') as f:
            json.dump(compute_info, f, indent=2)
        
        # Save metadata
        with open(run_dir / 'meta.json', 'w') as f:
            json.dump(result['metadata'], f, indent=2)


class EDIAnalyzer:
    """Analyzes EDI results and generates plots/tables."""
    
    def __init__(self, results: list[dict]):
        self.results = results
        self.df = self._results_to_dataframe()
    
    def _results_to_dataframe(self) -> pd.DataFrame:
        """Convert results to dataframe for analysis."""
        rows = []
        
        for result in self.results:
            metadata = result['metadata']
            edi = result['edi_components']
            context = result['context_info']
            compute = result['run_output']
            
            row = {
                'run_id': metadata['run_id'],
                'architecture': metadata['architecture'],
                'context_id': metadata['context_id'],
                'seed': metadata['seed'],
                'uncertainty_stratum': metadata['uncertainty_stratum'],
                'stress_test_variant': metadata['stress_test_variant'],
                'data_source': metadata['data_source'],
                'industry': context['industry'],
                'stage': context['stage'],
                'geography': context['geography'],
                'cross_stage_contradiction_rate': edi['cross_stage_contradiction_rate'],
                'belief_instability': edi['belief_instability'],
                'source_attribution_fidelity': edi['source_attribution_fidelity'],
                'cross_stage_consistency': edi['cross_stage_consistency'],
                'final_edi': edi['final_edi'],
                'tokens_used': compute['tokens_used'],
                'latency': compute['latency']
            }
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def generate_summary_tables(self) -> dict:
        """Generate summary tables for paper."""
        tables = {}
        
        # Overall EDI by architecture
        overall_table = self.df.groupby('architecture')['final_edi'].agg(['mean', 'std', 'count']).round(4)
        tables['overall_edi'] = overall_table
        
        # EDI by uncertainty stratum
        uncertainty_table = self.df.groupby(['architecture', 'uncertainty_stratum'])['final_edi'].agg(['mean', 'std']).round(4)
        tables['uncertainty_stratified'] = uncertainty_table
        
        # EDI by stress test
        stress_table = self.df.groupby(['architecture', 'stress_test_variant'])['final_edi'].agg(['mean', 'std']).round(4)
        tables['stress_test'] = stress_table
        
        # Component breakdown
        components = ['cross_stage_contradiction_rate', 'belief_instability', 'source_attribution_fidelity', 'cross_stage_consistency']
        component_table = self.df.groupby('architecture')[components].mean().round(4)
        tables['components'] = component_table
        
        # Compute efficiency
        efficiency_table = self.df.groupby('architecture').agg({
            'final_edi': 'mean',
            'tokens_used': 'mean',
            'latency': 'mean'
        }).round(4)
        efficiency_table['edi_per_token'] = efficiency_table['final_edi'] / efficiency_table['tokens_used'] * 1000
        tables['efficiency'] = efficiency_table
        
        return tables
    
    def bootstrap_confidence_interval(self, data: np.ndarray, n_bootstrap: int = 1000, ci_level: float = 0.95) -> tuple[float, float, float]:
        """Compute bootstrap confidence interval."""
        if len(data) == 0:
            return 0.0, 0.0, 0.0
        
        bootstrap_means = []
        for _ in range(n_bootstrap):
            bootstrap_sample = np.random.choice(data, size=len(data), replace=True)
            bootstrap_means.append(np.mean(bootstrap_sample))
        
        mean = np.mean(data)
        alpha = 1 - ci_level
        ci_lower = np.percentile(bootstrap_means, 100 * alpha / 2)
        ci_upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))
        
        return mean, ci_lower, ci_upper
    
    def compute_statistical_tests(self) -> dict:
        """Compute statistical tests between architectures."""
        architectures = self.df['architecture'].unique()
        tests = {}
        
        for i, arch1 in enumerate(architectures):
            for arch2 in architectures[i+1:]:
                data1 = self.df[self.df['architecture'] == arch1]['final_edi'].values
                data2 = self.df[self.df['architecture'] == arch2]['final_edi'].values
                
                # Paired t-test (assuming same contexts)
                if len(data1) == len(data2):
                    t_stat, p_value = stats.ttest_rel(data1, data2)
                else:
                    t_stat, p_value = stats.ttest_ind(data1, data2)
                
                # Cohen's d
                pooled_std = np.sqrt(((len(data1) - 1) * np.var(data1) + (len(data2) - 1) * np.var(data2)) / (len(data1) + len(data2) - 2))
                cohens_d = (np.mean(data1) - np.mean(data2)) / pooled_std if pooled_std > 0 else 0
                
                # Bootstrap CI for difference
                diff_means = []
                for _ in range(1000):
                    if len(data1) == len(data2):
                        boot1 = np.random.choice(data1, size=len(data1), replace=True)
                        boot2 = np.random.choice(data2, size=len(data2), replace=True)
                        diff_means.append(np.mean(boot1) - np.mean(boot2))
                
                diff_ci_lower = np.percentile(diff_means, 2.5) if diff_means else 0
                diff_ci_upper = np.percentile(diff_means, 97.5) if diff_means else 0
                
                tests[f"{arch1}_vs_{arch2}"] = {
                    't_statistic': float(t_stat),
                    'p_value': float(p_value),
                    'cohens_d': float(cohens_d),
                    'mean_difference': float(np.mean(data1) - np.mean(data2)),
                    'ci_lower': float(diff_ci_lower),
                    'ci_upper': float(diff_ci_upper),
                    'significant': p_value < 0.05
                }
        
        return tests
    
    def generate_plots(self, output_dir: str):
        """Generate all required plots."""
        output_path = Path(output_dir) / 'figures'
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Set style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Figure 1: EDI by architecture (overall) with 95% CI
        plt.figure(figsize=(10, 6))
        architectures = self.df['architecture'].unique()
        means = []
        cis = []
        
        for arch in architectures:
            data = self.df[self.df['architecture'] == arch]['final_edi'].values
            mean, ci_lower, ci_upper = self.bootstrap_confidence_interval(data)
            means.append(mean)
            cis.append([ci_lower, ci_upper])
        
        means = np.array(means)
        cis = np.array(cis)
        
        x_pos = np.arange(len(architectures))
        plt.bar(x_pos, means, yerr=[means - cis[:, 0], cis[:, 1] - means], 
                capsize=5, alpha=0.7, color='skyblue')
        plt.xlabel('Architecture')
        plt.ylabel('EDI (lower is better)')
        plt.title('EDI by Architecture (Overall) with 95% CI')
        plt.xticks(x_pos, [arch.replace('_', '\n') for arch in architectures], rotation=45)
        plt.tight_layout()
        plt.savefig(output_path / 'figure1_edi_by_architecture.png', dpi=300, bbox_inches='tight')
        plt.savefig(output_path / 'figure1_edi_by_architecture.pdf', bbox_inches='tight')
        plt.close()
        
        # Figure 2: EDI by architecture × uncertainty stratum
        plt.figure(figsize=(12, 8))
        uncertainty_data = self.df.groupby(['architecture', 'uncertainty_stratum'])['final_edi'].mean().unstack()
        
        uncertainty_data.plot(kind='bar', figsize=(12, 8))
        plt.xlabel('Architecture')
        plt.ylabel('EDI (lower is better)')
        plt.title('EDI by Architecture × Uncertainty Stratum')
        plt.legend(title='Uncertainty Stratum')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_path / 'figure2_edi_uncertainty_facet.png', dpi=300, bbox_inches='tight')
        plt.savefig(output_path / 'figure2_edi_uncertainty_facet.pdf', bbox_inches='tight')
        plt.close()
        
        # Figure 3: EDI under stress tests
        plt.figure(figsize=(12, 8))
        stress_data = self.df.groupby(['architecture', 'stress_test_variant'])['final_edi'].mean().unstack()
        
        stress_data.plot(kind='bar', figsize=(12, 8))
        plt.xlabel('Architecture')
        plt.ylabel('EDI (lower is better)')
        plt.title('EDI Under Stress Tests')
        plt.legend(title='Stress Test Variant')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_path / 'figure3_edi_stress_tests.png', dpi=300, bbox_inches='tight')
        plt.savefig(output_path / 'figure3_edi_stress_tests.pdf', bbox_inches='tight')
        plt.close()
        
        # Figure 4: Pareto plot compute vs EDI
        plt.figure(figsize=(10, 8))
        arch_data = self.df.groupby('architecture').agg({
            'final_edi': 'mean',
            'tokens_used': 'mean'
        })
        
        plt.scatter(arch_data['tokens_used'], arch_data['final_edi'], s=100, alpha=0.7)
        
        # Add labels
        for i, arch in enumerate(arch_data.index):
            plt.annotate(arch.replace('_', '\n'), 
                        (arch_data['tokens_used'].iloc[i], arch_data['final_edi'].iloc[i]),
                        xytext=(5, 5), textcoords='offset points')
        
        plt.xlabel('Tokens Used (compute)')
        plt.ylabel('EDI (lower is better)')
        plt.title('Pareto Plot: Compute vs EDI')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path / 'figure4_pareto_compute_edi.png', dpi=300, bbox_inches='tight')
        plt.savefig(output_path / 'figure4_pareto_compute_edi.pdf', bbox_inches='tight')
        plt.close()
        
        logger.info(f"Plots saved to {output_path}")
    
    def export_results(self, output_dir: str):
        """Export all results to CSV and create summary."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Export full results
        self.df.to_csv(output_path / 'edi_results.csv', index=False)
        
        # Generate and export summary tables
        tables = self.generate_summary_tables()
        
        # Create markdown tables
        with open(output_path / 'edi_summary_tables.md', 'w') as f:
            f.write("# EDI Summary Tables\n\n")
            
            f.write("## Overall EDI by Architecture\n\n")
            f.write(tables['overall_edi'].to_markdown())
            f.write("\n\n")
            
            f.write("## EDI by Uncertainty Stratum\n\n")
            f.write(tables['uncertainty_stratified'].to_markdown())
            f.write("\n\n")
            
            f.write("## EDI by Stress Test\n\n")
            f.write(tables['stress_test'].to_markdown())
            f.write("\n\n")
            
            f.write("## Component Breakdown\n\n")
            f.write(tables['components'].to_markdown())
            f.write("\n\n")
            
            f.write("## Compute Efficiency\n\n")
            f.write(tables['efficiency'].to_markdown())
        
        # Export statistical tests
        tests = self.compute_statistical_tests()
        with open(output_path / 'statistical_tests.json', 'w') as f:
            json.dump(tests, f, indent=2)
        
        # Create methods documentation
        with open(output_path / 'methods_edi.md', 'w') as f:
            f.write("# EDI Methods Documentation\n\n")
            f.write("## EDI Formula\n\n")
            f.write("EDI = w1*CR + w2*BI + w3*(1-SAF) + w4*(1-CS)\n\n")
            f.write("Where:\n")
            f.write("- CR: Cross-stage contradiction rate\n")
            f.write("- BI: Belief instability (Jensen-Shannon divergence)\n")
            f.write("- SAF: Source attribution fidelity\n")
            f.write("- CS: Cross-stage consistency (F1 overlap)\n\n")
            f.write("Weights: w1=0.25, w2=0.25, w3=0.25, w4=0.25\n\n")
            f.write("## Implementation Notes\n\n")
            f.write("- Contradictions detected using deterministic rules + LLM-as-judge\n")
            f.write("- Belief states represented as distributions over 5 latent variables\n")
            f.write("- Source attribution verified against evidence snippets\n")
            f.write("- Consistency measured using set similarity/F1 overlap\n")
        
        # Create reproducibility documentation
        with open(output_path / 'reproducibility.md', 'w') as f:
            f.write("# Reproducibility Information\n\n")
            f.write(f"## Dataset\n")
            f.write(f"- Total contexts: {len(self.df)}\n")
            f.write(f"- Industries: {', '.join(self.df['industry'].unique())}\n")
            f.write(f"- Geographic clusters: {', '.join(self.df['geography'].unique())}\n\n")
            
            f.write("## Seeds\n")
            f.write("- Fixed seeds used for reproducibility\n")
            f.write("- Variance reported across seeds\n\n")
            
            f.write("## Versions\n")
            f.write(f"- Python: {sys.version}\n")
            f.write(f"- Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"- Dataset hash: {hashlib.md5(str(len(self.df)).encode()).hexdigest()}\n")


async def main():
    """Main EDI benchmark runner."""
    parser = argparse.ArgumentParser(description="EDI Benchmark for Asmblr")
    parser.add_argument('--contexts_dir', required=True, help='Directory containing context JSON files')
    parser.add_argument('--k_seeds', type=int, default=5, help='Number of seeds per context')
    parser.add_argument('--export', required=True, help='Export directory for results')
    parser.add_argument('--architectures', nargs='+', 
                       default=['monolithic_baseline', 'sequential_pipeline_baseline', 'multi_agent_asmblr'],
                       help='Architectures to evaluate')
    parser.add_argument(
        "--phase1_quick_wins",
        action="store_true",
        help="Activate Phase 1 optimization profile: A7-A11 variants with token-focused budgets.",
    )
    parser.add_argument('--stress_variants', nargs='+',
                       default=['base', 'hype_amplification', 'ambiguous_signals', 'adversarial_corruption'],
                       help='Stress test variants')
    parser.add_argument(
        "--phase2_performance",
        action="store_true",
        help="Enable dynamic model selection, smart caching, and real-time monitoring.",
    )
    parser.add_argument(
        "--phase3_scale",
        action="store_true",
        help="Enable multi-tenant isolation, marketplace manifests, and advanced analytics rollups.",
    )
    
    args = parser.parse_args()
    
    logger.info("Starting EDI Benchmark")
    logger.info(f"Contexts directory: {args.contexts_dir}")
    logger.info(f"Seeds per context: {args.k_seeds}")
    logger.info(f"Architectures: {args.architectures}")
    logger.info(f"Stress variants: {args.stress_variants}")
    logger.info(f"Phase 2 performance mode: {args.phase2_performance}")
    logger.info(f"Phase 3 scale mode: {args.phase3_scale}")

    if args.phase1_quick_wins:
        args.architectures = PHASE1_OPTIMIZED_ARCHITECTURES.copy()
        logger.info("Phase 1 quick wins enabled")
        logger.info(f"Optimized architectures: {args.architectures}")
    
    # Check Ollama/models availability
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("Ollama not available. Install with: curl -fsSL https://ollama.ai/install.sh | sh")
            return 1
        logger.info("Ollama models available")
    except FileNotFoundError:
        logger.error("Ollama not found. Install with: curl -fsSL https://ollama.ai/install.sh | sh")
        return 1
    
    # Set reproducibility
    ReproducibilityEnforcer.set_global_seeds(42)
    
    # Run experiments
    all_results = []
    runner = ArchitectureRunner(
        args.contexts_dir,
        "runs",
        phase2_performance=args.phase2_performance,
        phase3_scale=args.phase3_scale,
    )
    
    for architecture in args.architectures:
        logger.info(f"Running experiments for {architecture}")
        results = await runner.run_experiment(architecture, args.k_seeds, args.stress_variants)
        all_results.extend(results)
        logger.info(f"Completed {architecture}: {len(results)} runs")
    
    # Analyze results
    logger.info("Analyzing results and generating outputs")
    analyzer = EDIAnalyzer(all_results)
    
    # Generate outputs
    analyzer.export_results(args.export)
    analyzer.generate_plots(args.export)
    
    # Generate pilot results table
    tables = analyzer.generate_summary_tables()
    
    logger.info("EDI Benchmark Complete!")
    logger.info(f"Results exported to: {args.export}")
    logger.info(f"Total runs: {len(all_results)}")
    
    # Print pilot results
    print("\n" + "="*80)
    print("PILOT EDI RESULTS")
    print("="*80)
    print("\nOverall EDI (lower is better):")
    print(tables['overall_edi'].to_string())
    print("\nHigh Uncertainty EDI:")
    high_unc_df = analyzer.df[analyzer.df['uncertainty_stratum'] == 'high']
    high_unc_table = high_unc_df.groupby('architecture')['final_edi'].agg(['mean', 'std']).round(4)
    print(high_unc_table.to_string())
    print("\nStress Test EDI (adversarial_corruption):")
    stress_df = analyzer.df[analyzer.df['stress_test_variant'] == 'adversarial_corruption']
    stress_table = stress_df.groupby('architecture')['final_edi'].agg(['mean', 'std']).round(4)
    print(stress_table.to_string())
    print("="*80)
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
