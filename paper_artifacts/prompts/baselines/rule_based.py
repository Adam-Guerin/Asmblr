"""
Rule-based baseline - simple keyword extraction and heuristic scoring.
"""

import re
from typing import Any

from .base import BaseBaseline


class RuleBasedBaseline(BaseBaseline):
    """Rule-based baseline using keyword extraction and heuristics."""
    
    deterministic = True
    
    def __init__(self, config: Any):
        super().__init__(config)
        
        # Pain extraction keywords
        self.pain_keywords = {
            "problems": ["problem", "issue", "challenge", "difficulty", "trouble", "concern"],
            "negative": ["can't", "cannot", "unable", "fail", "broken", "slow", "expensive", "complex"],
            "frustration": ["frustrated", "annoying", "difficult", "time-consuming", "manual"]
        }
        
        # Opportunity keywords
        self.opportunity_keywords = {
            "solutions": ["solution", "platform", "tool", "system", "software", "service"],
            "technology": ["AI", "machine learning", "automation", "cloud", "mobile", "web"],
            "benefits": ["improve", "optimize", "reduce", "increase", "enhance", "streamline"]
        }
        
        # Competitor indicators
        self.competitor_keywords = ["competitor", "alternative", "existing", "current", "market", "solution"]
        
        # Decision rules
        self.decision_rules = {
            "PASS": ["opportunity", "market", "demand", "solution", "viable"],
            "KILL": ["saturated", "competitive", "expensive", "complex", "risky"],
            "ABORT": ["unclear", "no market", "technical", "impossible", "regulatory"]
        }
    
    def process_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Process a single dataset item using rule-based approach."""
        topic = item.get("topic", "Unknown Topic")
        documents = item.get("documents", [])
        
        # Extract text content
        all_text = " ".join([doc.get("text", "") for doc in documents]).lower()
        
        # Extract pains using keyword rules
        pains = self._extract_pains_rule_based(all_text, documents)
        
        # Generate opportunities using heuristics
        opportunities = self._generate_opportunities_rule_based(topic, pains, all_text)
        
        # Identify competitors using keyword matching
        competitors = self._extract_competitors_rule_based(all_text)
        
        # Make decision using rule-based logic
        decision, confidence = self._make_decision_rule_based(opportunities, competitors, all_text)
        
        return {
            "dataset_id": item.get("id"),
            "topic": topic,
            "pains": pains,
            "opportunities": opportunities,
            "competitors": competitors,
            "decision": decision,
            "confidence": confidence,
            "success": True
        }
    
    def _extract_pains_rule_based(self, text: str, documents: list[dict]) -> list[dict]:
        """Extract pains using keyword-based rules."""
        pains = []
        
        # Split text into sentences for better extraction
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check for pain indicators
            pain_score = 0
            pain_indicators = []
            
            for category, keywords in self.pain_keywords.items():
                for keyword in keywords:
                    if keyword in sentence:
                        pain_score += 1
                        pain_indicators.append(keyword)
            
            # If sentence has pain indicators, extract as pain
            if pain_score >= 2:  # Require at least 2 pain indicators
                pain = {
                    "actor": self._extract_actor(sentence),
                    "context": self._extract_context(sentence),
                    "problem": sentence,
                    "severity": min(5, max(1, pain_score))  # Scale severity with pain score
                }
                pains.append(pain)
        
        # Limit to top 3 pains to avoid noise
        return pains[:3]
    
    def _extract_actor(self, sentence: str) -> str:
        """Extract actor from sentence."""
        actor_patterns = [
            r'(i|we|they|users|customers|business|team|organization)',
            r'(user|customer|client|employee|manager|admin)'
        ]
        
        for pattern in actor_patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "User"
    
    def _extract_context(self, sentence: str) -> str:
        """Extract context from sentence."""
        context_patterns = [
            r'(management|operations|planning|analysis|reporting|communication)',
            r'(daily|weekly|monthly|strategic|operational)',
            r'(data|process|workflow|system|tool|platform)'
        ]
        
        for pattern in context_patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "General"
    
    def _generate_opportunities_rule_based(self, topic: str, pains: list[dict], text: str) -> list[dict]:
        """Generate opportunities using rule-based heuristics."""
        opportunities = []
        
        # Use pain count to determine opportunity strength
        pain_count = len(pains)
        
        if pain_count == 0:
            return opportunities
        
        # Generate opportunity based on most common pain themes
        pain_themes = self._extract_pain_themes(pains)
        
        for theme in pain_themes[:2]:  # Top 2 themes
            opportunity = {
                "title": f"{theme['technology']} {theme['domain']} Solution",
                "description": f"Address {theme['problem']} using {theme['technology']}",
                "solution": f"Automated {theme['domain']} platform",
                "market": topic,
                "features": [
                    f"Automated {theme['domain']} management",
                    "Real-time analytics and reporting",
                    "Integration with existing systems"
                ],
                "confidence": min(0.8, 0.3 + pain_count * 0.2)
            }
            opportunities.append(opportunity)
        
        return opportunities
    
    def _extract_pain_themes(self, pains: list[dict]) -> list[dict]:
        """Extract common themes from pains."""
        themes = []
        
        # Simple theme extraction based on problem keywords
        domain_keywords = {
            "management": ["management", "coordination", "planning", "organization"],
            "data": ["data", "information", "tracking", "reporting"],
            "process": ["process", "workflow", "automation", "efficiency"],
            "communication": ["communication", "collaboration", "messaging", "notification"]
        }
        
        tech_keywords = {
            "AI": ["artificial intelligence", "AI", "machine learning", "automation"],
            "Cloud": ["cloud", "web", "online", "saas"],
            "Mobile": ["mobile", "app", "smartphone", "tablet"],
            "Analytics": ["analytics", "insights", "reporting", "dashboard"]
        }
        
        # Count keyword occurrences
        all_problems = " ".join([pain.get("problem", "") for pain in pains]).lower()
        
        for domain, keywords in domain_keywords.items():
            domain_count = sum(1 for keyword in keywords if keyword in all_problems)
            if domain_count > 0:
                themes.append({"domain": domain, "count": domain_count})
        
        for tech, keywords in tech_keywords.items():
            tech_count = sum(1 for keyword in keywords if keyword in all_problems)
            if tech_count > 0:
                # Add technology to existing theme or create new one
                if themes:
                    themes[0]["technology"] = tech
                else:
                    themes.append({"domain": "general", "technology": tech, "count": tech_count})
        
        return sorted(themes, key=lambda x: x["count"], reverse=True)
    
    def _extract_competitors_rule_based(self, text: str) -> list[dict]:
        """Extract competitors using keyword matching."""
        competitors = []
        
        # Look for company names and product mentions
        company_patterns = [
            r'(\w+tech|\w+soft|\w+corp|\w+systems|\w+solutions)',
            r'(google|microsoft|apple|amazon|facebook|oracle|salesforce)',
            r'(adobe|sap|oracle|intuit|zoom|slack)'
        ]
        
        found_companies = set()
        for pattern in company_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found_companies.update(matches)
        
        # Generate competitor entries
        for i, company in enumerate(list(found_companies)[:3]):  # Limit to 3
            competitor = {
                "name": company.title(),
                "positioning": "Existing solution provider",
                "pricing": "$" + str(10 + i * 20) + "/month",
                "market_share": str(30 - i * 10) + "%"
            }
            competitors.append(competitor)
        
        return competitors
    
    def _make_decision_rule_based(self, opportunities: list[dict], 
                                competitors: list[dict], 
                                text: str) -> tuple[str, float]:
        """Make decision using rule-based logic."""
        # Count positive and negative indicators
        positive_score = 0
        negative_score = 0
        
        for keyword in self.decision_rules["PASS"]:
            if keyword in text:
                positive_score += 1
        
        for keyword in self.decision_rules["KILL"]:
            if keyword in text:
                negative_score += 1
        
        for keyword in self.decision_rules["ABORT"]:
            if keyword in text:
                negative_score += 2  # ABORT indicators weighted more heavily
        
        # Decision logic
        if positive_score > negative_score and len(opportunities) > 0:
            decision = "PASS"
            confidence = min(0.8, 0.5 + len(opportunities) * 0.1)
        elif negative_score > positive_score and len(competitors) > 2:
            decision = "KILL"
            confidence = min(0.7, 0.4 + len(competitors) * 0.1)
        elif negative_score >= 2:
            decision = "ABORT"
            confidence = 0.3
        else:
            # Default decision based on balance
            decision = "KILL" if len(competitors) > len(opportunities) else "PASS"
            confidence = 0.5
        
        return decision, confidence
