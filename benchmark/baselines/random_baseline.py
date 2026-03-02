"""
Random baseline - generates random decisions and dummy outputs.
"""

import random
from typing import Any

from .base import BaseBaseline


class RandomBaseline(BaseBaseline):
    """Random baseline that generates random decisions and dummy outputs."""
    
    deterministic = False
    
    def process_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Process a single dataset item with random outputs."""
        topic = item.get("topic", "Unknown Topic")
        documents = item.get("documents", [])
        
        # Generate random pains
        pains = self._generate_random_pains(topic, documents)
        
        # Generate random opportunities
        opportunities = self._generate_random_opportunities(topic, pains)
        
        # Generate random competitors
        competitors = self._generate_random_competitors(topic)
        
        # Generate random decision
        decision = random.choice(["PASS", "KILL", "ABORT"])
        confidence = random.uniform(0.3, 0.9)
        
        return {
            "dataset_id": item.get("id"),
            "topic": topic,
            "pains": pains,
            "opportunities": opportunities,
            "competitors": competitors,
            "decision": decision,
            "confidence": confidence,
            "success": True  # Always succeeds in processing
        }
    
    def _generate_random_pains(self, topic: str, documents: list[dict]) -> list[dict]:
        """Generate random pain points."""
        num_pains = random.randint(1, 3)
        pains = []
        
        actors = ["Users", "Customers", "Business", "Team", "Organization"]
        contexts = ["Daily operations", "Strategic planning", "Customer interactions", "Data management"]
        problems = [
            "Manual process is time-consuming",
            "Current solution is too expensive",
            "Lack of real-time visibility",
            "Integration challenges exist",
            "Compliance requirements are burdensome"
        ]
        
        for i in range(num_pains):
            pain = {
                "actor": random.choice(actors),
                "context": random.choice(contexts),
                "problem": random.choice(problems),
                "severity": random.randint(2, 5)
            }
            pains.append(pain)
        
        return pains
    
    def _generate_random_opportunities(self, topic: str, pains: list[dict]) -> list[dict]:
        """Generate random opportunities."""
        num_opportunities = random.randint(1, 2)
        opportunities = []
        
        solution_templates = [
            "AI-powered {domain} solution",
            "Automated {domain} platform", 
            "{domain} optimization tool",
            "Smart {domain} system"
        ]
        
        domains = ["management", "analytics", "coordination", "automation", "monitoring"]
        
        for i in range(num_opportunities):
            opportunity = {
                "title": random.choice(solution_templates).format(domain=random.choice(domains)),
                "description": f"Random solution for {topic}",
                "solution": f"Automated approach to address identified pains",
                "market": topic,
                "features": [f"Feature {j}" for j in range(1, random.randint(2, 5))],
                "confidence": random.uniform(0.4, 0.8)
            }
            opportunities.append(opportunity)
        
        return opportunities
    
    def _generate_random_competitors(self, topic: str) -> list[dict]:
        """Generate random competitors."""
        num_competitors = random.randint(2, 4)
        competitors = []
        
        company_names = ["TechCorp", "InnoSoft", "DataFlow", "CloudBase", "SmartSys", "ProSolve", "NextGen"]
        positionings = [
            "Leading solution in the space",
            "Enterprise-focused platform",
            "Cost-effective alternative",
            "Advanced technology approach"
        ]
        pricings = [
            "$29/month per user",
            "$99/month basic plan",
            "Enterprise pricing available",
            "Free tier with paid upgrades"
        ]
        
        for i in range(num_competitors):
            competitor = {
                "name": f"{random.choice(company_names)} {i+1}",
                "positioning": random.choice(positionings),
                "pricing": random.choice(pricings)
            }
            competitors.append(competitor)
        
        return competitors
