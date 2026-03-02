"""
Idea Novelty metric - embedding-based novelty proxy using TF-IDF fallback.
"""

from typing import Any
import math
import re
from collections import Counter

from .base import BaseMetric, MetricResult


class IdeaNovelty(BaseMetric):
    """Measures novelty of generated ideas using TF-IDF cosine distance."""
    
    requires_ground_truth = False
    output_type = "score"
    
    def __init__(self, config: Any):
        super().__init__(config)
        self.corpus = self._load_known_ideas_corpus()
    
    def compute(self, run_result: dict[str, Any], dataset: list[dict]) -> MetricResult:
        """Compute idea novelty metrics."""
        # Extract system ideas
        system_ideas = self._extract_system_ideas(run_result)
        if not system_ideas:
            return MetricResult(
                score=0.0,
                explanation="No ideas extracted from system",
                evidence={"system_ideas_count": 0}
            )
        
        # Calculate novelty scores
        novelty_scores = []
        corpus_similarities = []
        
        for idea in system_ideas:
            novelty_score, corpus_similarity = self._calculate_idea_novelty(idea)
            novelty_scores.append(novelty_score)
            corpus_similarities.append(corpus_similarity)
        
        # Overall metrics
        avg_novelty = sum(novelty_scores) / len(novelty_scores) if novelty_scores else 0.0
        max_novelty = max(novelty_scores) if novelty_scores else 0.0
        avg_corpus_similarity = sum(corpus_similarities) / len(corpus_similarities) if corpus_similarities else 0.0
        
        # Final score (higher novelty = higher score, but penalize too low corpus similarity)
        corpus_penalty = max(0.0, avg_corpus_similarity - 0.3)  # Allow some similarity
        final_score = max(0.0, avg_novelty - corpus_penalty)
        
        explanation = f"Idea novelty: {final_score:.3f} (avg: {avg_novelty:.3f}, corpus similarity: {avg_corpus_similarity:.3f})"
        
        evidence = {
            "system_ideas_count": len(system_ideas),
            "avg_novelty": avg_novelty,
            "max_novelty": max_novelty,
            "avg_corpus_similarity": avg_corpus_similarity,
            "corpus_penalty": corpus_penalty,
            "individual_scores": novelty_scores
        }
        
        return MetricResult(
            score=final_score,
            explanation=explanation,
            evidence=evidence,
            details={
                "idea_novelty_scores": list(zip(range(len(system_ideas)), novelty_scores)),
                "corpus_similarities": list(zip(range(len(system_ideas)), corpus_similarities)),
                "system_ideas": system_ideas[:3]  # First 3 for brevity
            }
        )
    
    def _extract_system_ideas(self, run_result: dict[str, Any]) -> list[dict]:
        """Extract ideas from system output."""
        ideas = []
        
        # Try opportunities_structured.json
        opportunities = self._extract_artifact(run_result, "opportunities_structured")
        if opportunities and isinstance(opportunities, dict):
            if "opportunities" in opportunities:
                ideas.extend(opportunities["opportunities"])
            elif "ideas" in opportunities:
                ideas.extend(opportunities["ideas"])
        
        # Try opportunities.json
        simple_opportunities = self._extract_artifact(run_result, "opportunities")
        if simple_opportunities and isinstance(simple_opportunities, list):
            ideas.extend(simple_opportunities)
        
        # Normalize idea format
        normalized_ideas = []
        for idea in ideas:
            normalized = self._normalize_idea(idea)
            if normalized:
                normalized_ideas.append(normalized)
        
        return normalized_ideas
    
    def _normalize_idea(self, idea: Any) -> Optional[dict]:
        """Normalize idea to standard format."""
        if isinstance(idea, dict):
            return {
                "title": idea.get("title", ""),
                "description": idea.get("description", idea.get("problem", "")),
                "solution": idea.get("solution", ""),
                "market": idea.get("market", ""),
                "features": idea.get("features", [])
            }
        elif isinstance(idea, str):
            return {
                "title": idea,
                "description": idea,
                "solution": "",
                "market": "",
                "features": []
            }
        return None
    
    def _load_known_ideas_corpus(self) -> list[dict]:
        """Load corpus of known ideas for comparison."""
        # Built-in corpus of common startup ideas
        corpus = [
            {
                "title": "AI-powered customer service chatbot",
                "description": "Automated customer service using artificial intelligence",
                "solution": "Chatbot with natural language processing",
                "market": "Customer service",
                "features": ["NLP", "24/7 support", "multilingual"]
            },
            {
                "title": "Blockchain supply chain tracking",
                "description": "Transparent supply chain management using blockchain",
                "solution": "Distributed ledger for supply chain visibility",
                "market": "Logistics",
                "features": ["blockchain", "real-time tracking", "smart contracts"]
            },
            {
                "title": "SaaS project management tool",
                "description": "Cloud-based project management for teams",
                "solution": "Collaborative project management platform",
                "market": "Project management",
                "features": ["task tracking", "team collaboration", "reporting"]
            },
            {
                "title": "EdTech personalized learning platform",
                "description": "Adaptive learning platform for students",
                "solution": "AI-powered personalized education",
                "market": "Education",
                "features": ["personalization", "progress tracking", "content adaptation"]
            },
            {
                "title": "HealthTech remote patient monitoring",
                "description": "Remote health monitoring for chronic conditions",
                "solution": "IoT devices with health data analytics",
                "market": "Healthcare",
                "features": ["remote monitoring", "alerts", "data analytics"]
            },
            {
                "title": "FinTech automated investing",
                "description": "AI-powered investment portfolio management",
                "solution": "Automated investment advisory platform",
                "market": "Finance",
                "features": ["AI investing", "portfolio management", "risk assessment"]
            },
            {
                "title": "ClimateTech carbon tracking",
                "description": "Carbon footprint tracking and reduction",
                "solution": "Carbon accounting and offset platform",
                "market": "Sustainability",
                "features": ["carbon tracking", "offset marketplace", "reporting"]
            },
            {
                "title": "Retail inventory optimization",
                "description": "AI-powered inventory management for retail",
                "solution": "Predictive inventory optimization system",
                "market": "Retail",
                "features": ["demand forecasting", "automated ordering", "analytics"]
            },
            {
                "title": "Restaurant delivery logistics",
                "description": "Efficient delivery management for restaurants",
                "solution": "Delivery optimization platform",
                "market": "Food service",
                "features": ["route optimization", "delivery tracking", "customer app"]
            },
            {
                "title": "Freelancer productivity tools",
                "description": "Productivity suite for independent workers",
                "solution": "Integrated freelancer management platform",
                "market": "Freelance work",
                "features": ["time tracking", "invoicing", "project management"]
            }
        ]
        
        return corpus
    
    def _calculate_idea_novelty(self, idea: dict) -> tuple[float, float]:
        """Calculate novelty score for a single idea."""
        # Combine all text fields for comparison
        idea_text = self._combine_idea_text(idea)
        
        if not idea_text:
            return 0.0, 0.0
        
        # Calculate TF-IDF vectors
        idea_vector = self._tfidf_vector(idea_text)
        
        # Calculate similarity to corpus
        similarities = []
        for corpus_idea in self.corpus:
            corpus_text = self._combine_idea_text(corpus_idea)
            if corpus_text:
                corpus_vector = self._tfidf_vector(corpus_text)
                similarity = self._cosine_similarity(idea_vector, corpus_vector)
                similarities.append(similarity)
        
        # Novelty is inversely related to maximum similarity
        max_similarity = max(similarities) if similarities else 0.0
        novelty_score = 1.0 - max_similarity
        
        return novelty_score, max_similarity
    
    def _combine_idea_text(self, idea: dict) -> str:
        """Combine all text fields of an idea."""
        fields = [
            idea.get("title", ""),
            idea.get("description", ""),
            idea.get("solution", ""),
            idea.get("market", ""),
            " ".join(idea.get("features", []))
        ]
        
        combined = " ".join(filter(None, fields)).lower()
        return combined
    
    def _tfidf_vector(self, text: str) -> dict[str, float]:
        """Calculate TF-IDF vector for text."""
        if not text:
            return {}
        
        # Tokenize
        tokens = self._tokenize(text)
        if not tokens:
            return {}
        
        # Calculate term frequencies
        tf = Counter(tokens)
        total_terms = len(tokens)
        
        # Calculate document frequencies for corpus
        corpus_texts = [self._combine_idea_text(idea) for idea in self.corpus]
        corpus_tokens = [self._tokenize(txt) for txt in corpus_texts]
        
        df = {}
        for term in set(tokens):
            df[term] = sum(1 for doc_tokens in corpus_tokens if term in doc_tokens)
        
        # Calculate TF-IDF
        tfidf = {}
        corpus_size = len(self.corpus) + 1  # +1 for current document
        
        for term, term_freq in tf.items():
            idf = math.log(corpus_size / (df.get(term, 0) + 1))
            tfidf[term] = (term_freq / total_terms) * idf
        
        return tfidf
    
    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into words."""
        # Simple tokenization - can be enhanced
        tokens = re.findall(r'\b\w+\b', text.lower())
        # Remove very common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
        tokens = [token for token in tokens if token not in stop_words and len(token) > 2]
        
        return tokens
    
    def _cosine_similarity(self, vector1: dict[str, float], vector2: dict[str, float]) -> float:
        """Calculate cosine similarity between two TF-IDF vectors."""
        # Get common terms
        terms = set(vector1.keys()).union(set(vector2.keys()))
        
        if not terms:
            return 0.0
        
        # Calculate dot product and magnitudes
        dot_product = sum(vector1.get(term, 0) * vector2.get(term, 0) for term in terms)
        
        magnitude1 = math.sqrt(sum(vector1.get(term, 0) ** 2 for term in vector1))
        magnitude2 = math.sqrt(sum(vector2.get(term, 0) ** 2 for term in vector2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def get_required_artifacts(self) -> list[str]:
        """Get required artifacts for this metric."""
        return ["opportunities_structured", "opportunities"]
    
    def get_required_ground_truth(self) -> list[str]:
        """Get required ground truth fields."""
        return []
