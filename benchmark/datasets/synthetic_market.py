"""
Synthetic market dataset - programmatically generated with controllable noise.
"""

import json
import random
from pathlib import Path


class SyntheticMarketDataset:
    """Programmatically generated dataset with controllable noise levels."""
    
    has_ground_truth = True
    size = 100  # Default size
    
    def __init__(self, custom_path: str | None = None, size: int = 100, noise_level: float = 0.1):
        self.custom_path = custom_path
        self.size = size
        self.noise_level = noise_level
        self.data = None
        
        # Templates for generation
        self.topics = [
            "AI-powered customer service",
            "Blockchain supply chain tracking", 
            "SaaS project management",
            "EdTech personalized learning",
            "HealthTech remote monitoring",
            "FinTech automated investing",
            "ClimateTech carbon tracking",
            "Retail inventory optimization",
            "Restaurant delivery logistics",
            "Freelancer productivity tools"
        ]
        
        self.actors = [
            "Small business owner", "Enterprise manager", "Freelancer", 
            "Student", "Healthcare provider", "Financial advisor",
            "Restaurant owner", "Retail manager", "Software developer",
            "Marketing professional", "HR manager", "Operations manager"
        ]
        
        self.contexts = [
            "Daily operations", "Strategic planning", "Customer interactions",
            "Team collaboration", "Financial management", "Compliance reporting",
            "Product development", "Marketing campaigns", "Sales processes",
            "Inventory management", "Quality control", "Risk assessment"
        ]
        
        self.problem_templates = [
            "Manual {process} takes too much time and leads to errors",
            "Current {tool} is too expensive for {actor}",
            "Difficulty coordinating {activity} across multiple stakeholders",
            "Lack of real-time visibility into {metric}",
            "Compliance requirements for {regulation} are burdensome",
            "Customer satisfaction suffers due to {issue}",
            "Data silos prevent effective {decision}",
            "Scaling {process} requires manual intervention",
            "Risk management for {area} is inadequate",
            "Communication breakdown in {context} causes delays"
        ]
    
    def load(self) -> list[dict]:
        """Load or generate the synthetic dataset."""
        if self.data is not None:
            return self.data
        
        if self.custom_path:
            # Load from custom path
            with open(self.custom_path, encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            # Generate synthetic data
            self.data = self._generate_synthetic_data()
        
        return self.data
    
    def _generate_synthetic_data(self) -> list[dict]:
        """Generate synthetic market data."""
        data = []
        
        for i in range(self.size):
            # Generate topic
            topic = random.choice(self.topics)
            
            # Generate documents
            documents = self._generate_documents(topic, i)
            
            # Generate ground truth
            ground_truth = self._generate_ground_truth(topic, i)
            
            # Add noise
            if self.noise_level > 0:
                ground_truth = self._add_noise(ground_truth)
            
            item = {
                "id": f"synthetic_{i:04d}",
                "topic": topic,
                "documents": documents,
                "ground_truth": ground_truth
            }
            data.append(item)
        
        return data
    
    def _generate_documents(self, topic: str, index: int) -> list[dict]:
        """Generate synthetic documents for a topic."""
        num_documents = random.randint(2, 4)
        documents = []
        
        sources = ["reddit", "forum", "blog", "news", "twitter"]
        
        for i in range(num_documents):
            source = random.choice(sources)
            
            # Generate text based on topic
            text = self._generate_document_text(topic, source)
            
            doc = {
                "source": source,
                "url": f"local://synthetic_{index:04d}_{source}_{i}",
                "text": text
            }
            documents.append(doc)
        
        return documents
    
    def _generate_document_text(self, topic: str, source: str) -> str:
        """Generate realistic text for a document."""
        templates = {
            "reddit": [
                f"I've been struggling with {topic.lower()} for months. The current solutions are either too expensive or don't really solve the core problem. Anyone else facing this?",
                f"Working in {topic.lower()} space and the tools available are frustrating. There's got to be a better way to handle this.",
                f"Does anyone know of good alternatives for {topic.lower()}? Everything I've tried has major drawbacks."
            ],
            "forum": [
                f"Looking for advice on {topic.lower()}. Our organization is spending too much time on manual processes and existing tools don't fit our needs.",
                f"We're evaluating solutions for {topic.lower()}. The market seems crowded but most options miss key features we need.",
                f"Has anyone implemented {topic.lower()} successfully? We're hitting roadblocks with current approaches."
            ],
            "blog": [
                f"The challenges of implementing {topic.lower()} in modern organizations. Many companies struggle with outdated tools and processes.",
                f"Why {topic.lower()} matters more than ever: Industry trends and best practices for 2024.",
                f"Common mistakes to avoid when selecting {topic.lower()} solutions."
            ],
            "news": [
                f"Market analysis shows growing demand for {topic.lower()} solutions as companies seek efficiency gains.",
                f"New developments in {topic.lower()} space promise to address long-standing industry challenges.",
                f"Investment in {topic.lower()} startups reaches record highs as digital transformation accelerates."
            ],
            "twitter": [
                f"Really excited about the potential of {topic.lower()} to transform how we work! #innovation #tech",
                f"The {topic.lower()} landscape is evolving fast. So many new approaches emerging! #startups #SaaS",
                f"Still waiting for the perfect {topic.lower()} solution. Current options all have trade-offs. #entrepreneurship"
            ]
        }
        
        template_list = templates.get(source, templates["reddit"])
        return random.choice(template_list)
    
    def _generate_ground_truth(self, topic: str, index: int) -> dict:
        """Generate ground truth for a topic."""
        # Generate pains
        num_pains = random.randint(2, 4)
        pains = []
        
        for i in range(num_pains):
            actor = random.choice(self.actors)
            context = random.choice(self.contexts)
            
            # Generate problem
            problem = self._generate_problem(actor, context)
            severity = random.randint(2, 5)
            
            pain = {
                "actor": actor,
                "context": context,
                "problem": problem,
                "severity": severity
            }
            pains.append(pain)
        
        # Generate clusters
        num_clusters = min(num_pains, random.randint(1, 3))
        clusters = []
        
        for i in range(num_clusters):
            cluster_size = random.randint(1, max(1, num_pains // num_clusters))
            start_idx = i * cluster_size
            end_idx = min(start_idx + cluster_size, num_pains)
            pain_ids = list(range(start_idx, end_idx))
            
            cluster = {
                "label": f"Cluster_{i+1}",
                "pain_ids": pain_ids
            }
            clusters.append(cluster)
        
        # Generate competitors
        num_competitors = random.randint(2, 4)
        competitors = []
        
        competitor_names = [
            "TechCorp", "InnoSoft", "DataFlow", "CloudBase", "SmartSys",
            "AgileTech", "NextGen", "ProSolve", "FlowState", "OptiMax"
        ]
        
        for i in range(num_competitors):
            name = random.choice(competitor_names) + f" {i+1}"
            positioning = f"Leading {topic.lower()} solution with advanced features"
            pricing = f"${random.randint(10, 200)}/month"
            
            competitor = {
                "name": name,
                "positioning": positioning,
                "pricing": pricing
            }
            competitors.append(competitor)
        
        # Generate opportunity and decision
        opportunity_score = random.uniform(0.3, 0.9)
        
        if opportunity_score > 0.7:
            decision = "PASS"
            confidence = random.uniform(0.6, 0.9)
        elif opportunity_score > 0.4:
            decision = "KILL"
            confidence = random.uniform(0.4, 0.7)
        else:
            decision = "ABORT"
            confidence = random.uniform(0.2, 0.5)
        
        best_opportunity = {
            "title": f"AI-powered {topic.lower()} solution",
            "reason": f"Strong market need with clear competitive differentiation"
        }
        
        return {
            "pains": pains,
            "clusters": clusters,
            "competitors": competitors,
            "best_opportunity": best_opportunity,
            "decision": decision,
            "confidence": confidence
        }
    
    def _generate_problem(self, actor: str, context: str) -> str:
        """Generate a problem statement."""
        processes = ["data entry", "reporting", "coordination", "analysis", "planning"]
        tools = ["spreadsheets", "manual systems", "legacy software", "generic solutions"]
        activities = ["team projects", "customer interactions", "compliance tasks", "quality control"]
        metrics = ["performance", "costs", "efficiency", "satisfaction"]
        regulations = ["data privacy", "financial reporting", "industry standards"]
        issues = ["slow response times", "poor user experience", "integration problems"]
        decisions = ["strategic choices", "resource allocation", "risk assessment"]
        areas = ["operations", "finance", "customer service", "compliance"]
        
        template = random.choice(self.problem_templates)
        
        # Fill template
        replacements = {
            "{process}": random.choice(processes),
            "{tool}": random.choice(tools),
            "{activity}": random.choice(activities),
            "{metric}": random.choice(metrics),
            "{regulation}": random.choice(regulations),
            "{issue}": random.choice(issues),
            "{decision}": random.choice(decisions),
            "{area}": random.choice(areas),
            "{actor}": actor.lower(),
            "{context}": context.lower()
        }
        
        problem = template
        for placeholder, replacement in replacements.items():
            problem = problem.replace(placeholder, replacement)
        
        return problem
    
    def _add_noise(self, ground_truth: dict) -> dict:
        """Add controlled noise to ground truth."""
        noisy_gt = ground_truth.copy()
        
        # Add noise to pain severity
        for pain in noisy_gt["pains"]:
            if random.random() < self.noise_level:
                pain["severity"] = max(1, min(5, pain["severity"] + random.randint(-1, 1)))
        
        # Add noise to confidence
        if random.random() < self.noise_level:
            noisy_gt["confidence"] = max(0, min(1, 
                noisy_gt["confidence"] + random.uniform(-0.2, 0.2)))
        
        # Occasionally flip decision
        if random.random() < self.noise_level * 0.5:
            decisions = ["PASS", "KILL", "ABORT"]
            current = noisy_gt["decision"]
            decisions.remove(current)
            noisy_gt["decision"] = random.choice(decisions)
        
        return noisy_gt
    
    def save_dataset(self, output_path: str):
        """Save generated dataset to file."""
        data = self.load()
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_schema(self) -> dict:
        """Get dataset schema (same as toy_pains)."""
        return {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "topic": {"type": "string"},
                "documents": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string"},
                            "url": {"type": "string"},
                            "text": {"type": "string"}
                        }
                    }
                },
                "ground_truth": {
                    "type": "object",
                    "properties": {
                        "pains": {"type": "array"},
                        "clusters": {"type": "array"},
                        "competitors": {"type": "array"},
                        "best_opportunity": {"type": "object"},
                        "decision": {"type": "string"},
                        "confidence": {"type": "number"}
                    }
                }
            }
        }
