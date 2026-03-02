"""
Single-agent baseline - monolithic output using deterministic heuristics.
"""

import re
from typing import Dict, List, Any
from collections import Counter

from .base import BaseBaseline


class SingleAgentBaseline(BaseBaseline):
    """Single-agent baseline using deterministic heuristics without LLM."""
    
    deterministic = True
    
    def __init__(self, config: Any):
        super().__init__(config)
        
        # Heuristic rules for analysis
        self.analysis_rules = {
            "pain_indicators": [
                "difficult", "challenge", "problem", "issue", "struggle",
                "manual", "time-consuming", "expensive", "complex"
            ],
            "opportunity_indicators": [
                "market", "demand", "need", "solution", "opportunity",
                "automation", "efficiency", "improvement"
            ],
            "risk_indicators": [
                "competition", "saturated", "expensive", "risky", "complex",
                "regulation", "compliance", "technical", "resource"
            ]
        }
        
        # Scoring matrices
        self.pain_severity_scores = {
            "low": 1, "medium": 2, "high": 3, "critical": 4, "severe": 5
        }
    
    def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single dataset item using single-agent heuristics."""
        topic = item.get("topic", "Unknown Topic")
        documents = item.get("documents", [])
        
        # Extract and analyze text
        all_text = " ".join([doc.get("text", "") for doc in documents])
        
        # Single-agent analysis
        analysis = self._analyze_single_agent(all_text)
        
        # Generate outputs based on analysis
        pains = self._generate_pains_single_agent(topic, analysis)
        opportunities = self._generate_opportunities_single_agent(topic, pains, analysis)
        competitors = self._generate_competitors_single_agent(topic, analysis)
        decision, confidence = self._make_decision_single_agent(analysis, opportunities, competitors)
        
        return {
            "dataset_id": item.get("id"),
            "topic": topic,
            "pains": pains,
            "opportunities": opportunities,
            "competitors": competitors,
            "decision": decision,
            "confidence": confidence,
            "success": True,
            "analysis": analysis
        }
    
    def _analyze_single_agent(self, text: str) -> Dict[str, Any]:
        """Perform single-agent analysis of text."""
        text_lower = text.lower()
        
        # Count indicators
        pain_count = sum(1 for indicator in self.analysis_rules["pain_indicators"] 
                          if indicator in text_lower)
        opportunity_count = sum(1 for indicator in self.analysis_rules["opportunity_indicators"] 
                               if indicator in text_lower)
        risk_count = sum(1 for indicator in self.analysis_rules["risk_indicators"] 
                        if indicator in text_lower)
        
        # Extract key themes
        words = re.findall(r'\b\w+\b', text_lower)
        word_freq = Counter(words)
        
        # Domain identification
        domains = {
            "technology": ["software", "app", "platform", "system", "digital", "online"],
            "business": ["business", "company", "organization", "enterprise", "startup"],
            "data": ["data", "analytics", "insights", "reporting", "metrics"],
            "process": ["process", "workflow", "automation", "efficiency", "streamline"]
        }
        
        domain_scores = {}
        for domain, keywords in domains.items():
            domain_scores[domain] = sum(word_freq.get(keyword, 0) for keyword in keywords)
        
        # Complexity assessment
        complexity_indicators = ["complex", "difficult", "challenging", "sophisticated", "advanced"]
        complexity_score = sum(word_freq.get(indicator, 0) for indicator in complexity_indicators)
        
        return {
            "pain_count": pain_count,
            "opportunity_count": opportunity_count,
            "risk_count": risk_count,
            "domain_scores": domain_scores,
            "complexity_score": complexity_score,
            "word_frequency": dict(word_freq.most_common(10)),
            "text_length": len(text),
            "sentence_count": len(re.split(r'[.!?]+', text))
        }
    
    def _generate_pains_single_agent(self, topic: str, analysis: Dict[str, Any]) -> List[Dict]:
        """Generate pains using single-agent analysis."""
        pains = []
        
        # Use analysis to generate structured pains
        pain_count = min(3, analysis["pain_count"])
        
        # Extract most relevant domain
        primary_domain = max(analysis["domain_scores"].items(), key=lambda x: x[1])[0] if analysis["domain_scores"] else "general"
        
        # Generate pains based on domain and complexity
        pain_templates = {
            "technology": [
                "Current {domain} solutions are outdated and inefficient",
                "Manual {domain} processes are error-prone and time-consuming",
                "Lack of integration between {domain} systems creates data silos"
            ],
            "business": [
                "{domain} operations suffer from poor visibility and control",
                "Manual {domain} workflows lead to inconsistencies and delays",
                "{domain} teams struggle with coordination and communication"
            ],
            "data": [
                "{domain} analysis is manual and prone to errors",
                "Lack of real-time {domain} insights hinders decision-making",
                "{domain} quality issues lead to poor business outcomes"
            ],
            "process": [
                "{domain} processes are fragmented and inefficient",
                "Manual {domain} workflows create bottlenecks and delays",
                "Lack of standardization in {domain} processes causes errors"
            ]
        }
        
        templates = pain_templates.get(primary_domain, pain_templates["general"])
        
        for i in range(pain_count):
            template = templates[i % len(templates)]
            pain_text = template.format(domain=primary_domain)
            
            # Determine severity based on complexity
            severity = min(5, max(1, analysis["complexity_score"] // 2 + 2))
            
            pain = {
                "actor": self._infer_actor(primary_domain, pain_text),
                "context": f"{primary_domain.title()} operations",
                "problem": pain_text,
                "severity": severity
            }
            pains.append(pain)
        
        return pains
    
    def _infer_actor(self, domain: str, problem_text: str) -> str:
        """Infer actor from domain and problem."""
        actor_mapping = {
            "technology": "IT Team",
            "business": "Business Manager", 
            "data": "Data Analyst",
            "process": "Operations Manager"
        }
        
        return actor_mapping.get(domain, "User")
    
    def _generate_opportunities_single_agent(self, topic: str, pains: List[Dict], 
                                          analysis: Dict[str, Any]) -> List[Dict]:
        """Generate opportunities using single-agent analysis."""
        opportunities = []
        
        if not pains:
            return opportunities
        
        # Use primary domain for opportunity generation
        primary_domain = max(analysis["domain_scores"].items(), key=lambda x: x[1])[0] if analysis["domain_scores"] else "general"
        
        # Generate opportunity based on pain patterns
        opportunity_templates = {
            "technology": [
                "AI-powered {domain} automation platform",
                "Cloud-based {domain} management system",
                "Real-time {domain} analytics and insights"
            ],
            "business": [
                "Integrated {domain} management solution",
                "Streamlined {domain} workflow automation",
                "Data-driven {domain} decision platform"
            ],
            "data": [
                "Automated {domain} processing and analysis",
                "Real-time {domain} intelligence platform",
                "Predictive {domain} analytics system"
            ],
            "process": [
                "Digital {domain} transformation platform",
                "Automated {domain} workflow optimization",
                "Intelligent {domain} process management"
            ]
        }
        
        templates = opportunity_templates.get(primary_domain, opportunity_templates["general"])
        
        # Generate 1-2 opportunities
        num_opportunities = min(2, analysis["opportunity_count"])
        
        for i in range(num_opportunities):
            template = templates[i % len(templates)]
            opportunity = {
                "title": template.format(domain=primary_domain),
                "description": f"Address identified {primary_domain} challenges using advanced technology",
                "solution": f"Comprehensive {primary_domain} solution with automation and analytics",
                "market": topic,
                "features": [
                    f"Automated {primary_domain} workflows",
                    "Real-time monitoring and alerts",
                    "Integration with existing systems",
                    "Advanced analytics and reporting"
                ],
                "confidence": min(0.8, 0.4 + len(pains) * 0.1)
            }
            opportunities.append(opportunity)
        
        return opportunities
    
    def _generate_competitors_single_agent(self, topic: str, analysis: Dict[str, Any]) -> List[Dict]:
        """Generate competitors using single-agent analysis."""
        competitors = []
        
        # Generate competitors based on topic and domain
        base_competitors = [
            {"name": "TechCorp Solutions", "positioning": "Enterprise-grade platform", "pricing": "$199/month"},
            {"name": "InnoSoft Systems", "positioning": "Cloud-based solution", "pricing": "$99/month"},
            {"name": "DataFlow Analytics", "positioning": "Data-driven insights", "pricing": "$149/month"},
            {"name": "CloudBase Platform", "positioning": "All-in-one solution", "pricing": "$79/month"}
        ]
        
        # Select competitors based on analysis
        num_competitors = min(3, max(1, analysis["risk_count"] // 2))
        
        for i in range(num_competitors):
            competitor = base_competitors[i % len(base_competitors)].copy()
            competitor["name"] = f"{competitor['name']} {i+1}"
            competitors.append(competitor)
        
        return competitors
    
    def _make_decision_single_agent(self, analysis: Dict[str, Any], 
                                   opportunities: List[Dict], 
                                   competitors: List[Dict]) -> tuple[str, float]:
        """Make decision using single-agent analysis."""
        # Decision logic based on analysis scores
        opportunity_strength = len(opportunities) * 0.3
        competition_level = len(competitors) * 0.2
        risk_level = analysis["risk_count"] * 0.3
        complexity_level = analysis["complexity_score"] * 0.2
        
        # Calculate decision score
        decision_score = opportunity_strength - competition_level - risk_level - complexity_level
        
        # Normalize to [0,1] range
        normalized_score = max(0, min(1, (decision_score + 5) / 10))
        
        # Decision thresholds
        if normalized_score > 0.7:
            decision = "PASS"
            confidence = 0.6 + normalized_score * 0.3
        elif normalized_score > 0.4:
            decision = "KILL"
            confidence = 0.4 + normalized_score * 0.3
        else:
            decision = "ABORT"
            confidence = 0.3 + normalized_score * 0.3
        
        return decision, min(0.9, confidence)
