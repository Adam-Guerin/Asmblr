"""
Base class for all baseline systems.
"""

from abc import ABC, abstractmethod
from typing import Any
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class BaseBaseline(ABC):
    """Base class for all baseline systems."""
    
    def __init__(self, config: Any):
        self.config = config
        self.name = self.__class__.__name__.lower().replace('baseline', '').replace('_', '')
    
    @abstractmethod
    def process_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Process a single dataset item and return baseline output."""
        pass
    
    def save_results(self, results: list[dict[str, Any]], output_dir: Path):
        """Save baseline results to output directory."""
        # Save individual results
        for i, result in enumerate(results):
            output_file = output_dir / f"result_{i:04d}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        # Save aggregated results in Asmblr-like format
        self._save_asmblr_format(results, output_dir)
    
    def _save_asmblr_format(self, results: list[dict[str, Any]], output_dir: Path):
        """Save results in Asmblr-compatible format."""
        # Extract pains
        pains = []
        for result in results:
            if "pains" in result:
                pains.extend(result["pains"])
        
        # Extract opportunities
        opportunities = []
        for result in results:
            if "opportunities" in result:
                opportunities.extend(result["opportunities"])
        
        # Extract competitor analysis
        competitor_analysis = []
        for result in results:
            if "competitors" in result:
                competitor_analysis.extend(result["competitors"])
        
        # Extract decisions
        decisions = []
        confidences = []
        for result in results:
            if "decision" in result:
                decisions.append(result["decision"])
            if "confidence" in result:
                confidences.append(result["confidence"])
        
        # Save in Asmblr format
        if pains:
            with open(output_dir / "pains_structured.json", 'w', encoding='utf-8') as f:
                json.dump({"pains": pains}, f, indent=2, ensure_ascii=False)
        
        if opportunities:
            with open(output_dir / "opportunities.json", 'w', encoding='utf-8') as f:
                json.dump(opportunities, f, indent=2, ensure_ascii=False)
            
            with open(output_dir / "opportunities_structured.json", 'w', encoding='utf-8') as f:
                json.dump({"opportunities": opportunities}, f, indent=2, ensure_ascii=False)
        
        if competitor_analysis:
            with open(output_dir / "competitor_analysis.json", 'w', encoding='utf-8') as f:
                json.dump(competitor_analysis, f, indent=2, ensure_ascii=False)
        
        if decisions:
            # Create decision.md
            decision_text = f"# Decision\n\n{decisions[0] if decisions else 'PASS'}\n\nConfidence: {confidences[0] if confidences else 0.5}"
            with open(output_dir / "decision.md", 'w', encoding='utf-8') as f:
                f.write(decision_text)
            
            # Create confidence.json
            with open(output_dir / "confidence.json", 'w', encoding='utf-8') as f:
                json.dump({
                    "decision": decisions[0] if decisions else "PASS",
                    "confidence": confidences[0] if confidences else 0.5
                }, f, indent=2, ensure_ascii=False)
        
        # Create basic PRD and tech spec
        if opportunities:
            prd_content = self._generate_basic_prd(opportunities[0] if opportunities else {})
            with open(output_dir / "prd.md", 'w', encoding='utf-8') as f:
                f.write(prd_content)
            
            tech_spec_content = self._generate_basic_tech_spec(opportunities[0] if opportunities else {})
            with open(output_dir / "tech_spec.md", 'w', encoding='utf-8') as f:
                f.write(tech_spec_content)
    
    def _generate_basic_prd(self, opportunity: dict[str, Any]) -> str:
        """Generate a basic PRD from opportunity."""
        title = opportunity.get("title", "Generated Opportunity")
        description = opportunity.get("description", "Auto-generated solution")
        
        return f"""# Product Requirements Document

## Overview
**Title**: {title}
**Description**: {description}

## Target Customer
- Generated based on market analysis

## Problem Statement
- Identified through baseline analysis

## Solution
- {description}

## Success Metrics
- Basic metrics to be defined

## MVP Scope
- Core functionality only
- Basic implementation

## Non-Goals
- Extended features
- Advanced functionality

## Risks
- Implementation risks
- Market risks
"""
    
    def _generate_basic_tech_spec(self, opportunity: dict[str, Any]) -> str:
        """Generate a basic tech spec from opportunity."""
        title = opportunity.get("title", "Generated Solution")
        
        return f"""# Technical Specification

## Overview
**Project**: {title}

## Architecture
- Basic web application
- Client-server architecture
- RESTful API design

## Data Model
- Simple relational database
- Core entities identified
- Basic relationships

## API Endpoints
- CRUD operations
- Basic authentication
- Data validation

## Deployment
- Cloud hosting
- Basic scalability
- Monitoring setup

## Technology Stack
- Backend: Python/Node.js
- Database: PostgreSQL/MongoDB
- Frontend: React/Vue.js
- Deployment: Docker/Cloud

## Testing
- Unit tests
- Integration tests
- Basic QA process

## Risks
- Technical complexity
- Integration challenges
- Performance considerations
"""
