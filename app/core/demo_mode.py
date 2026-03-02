"""
Demo Mode for Asmblr
Provides pre-configured examples and demo data for public users
"""

import json
from pathlib import Path
from typing import Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DemoExample:
    """Demo example configuration"""
    name: str
    description: str
    topic: str
    icp: str
    seed_pains: list[str]
    seed_competitors: list[str]
    expected_outcomes: list[str]
    difficulty: str  # easy, medium, hard


class DemoModeManager:
    """Manages demo mode functionality"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.demo_data_dir = base_dir / "demo_data"
        self.demo_data_dir.mkdir(exist_ok=True)
        
        # Demo examples
        self.demo_examples = [
            DemoExample(
                name="AI Task Management",
                description="Smart scheduling and task management for remote teams",
                topic="AI-powered task management for remote teams",
                icp="Remote team managers and distributed workforce",
                seed_pains=[
                    "Difficulty coordinating across time zones",
                    "Task priority conflicts and missed deadlines",
                    "Lack of visibility into team workload",
                    "Inefficient meeting scheduling"
                ],
                seed_competitors=[
                    "Asana",
                    "Trello",
                    "Monday.com",
                    "Notion"
                ],
                expected_outcomes=[
                    "Automated task prioritization",
                    "Smart scheduling assistant",
                    "Team workload balancing",
                    "Integration with existing tools"
                ],
                difficulty="easy"
            ),
            DemoExample(
                name="Freelancer Finance",
                description="Automated expense tracking and invoicing for freelancers",
                topic="AI-powered financial management for freelancers",
                icp="Freelancers and solopreneurs",
                seed_pains=[
                    "Time-consuming expense tracking",
                    "Irregular cash flow management",
                    "Complex tax preparation",
                    "Client payment delays"
                ],
                seed_competitors=[
                    "QuickBooks Self-Employed",
                    "FreshBooks",
                    "Wave Accounting",
                    "Xero"
                ],
                expected_outcomes=[
                    "Automated expense categorization",
                    "Cash flow predictions",
                    "Smart invoicing system",
                    "Tax optimization suggestions"
                ],
                difficulty="medium"
            ),
            DemoExample(
                name="Eco Shopping Assistant",
                description="AI-powered sustainable product recommendations",
                topic="AI shopping assistant for eco-conscious consumers",
                icp="Environmentally conscious consumers",
                seed_pains=[
                    "Difficulty verifying product sustainability",
                    "Greenwashing concerns",
                    "Price comparison for eco products",
                    "Finding local sustainable options"
                ],
                seed_competitors=[
                    "Good On You",
                    "Ecosia",
                    "Buycott",
                    "EarthHero"
                ],
                expected_outcomes=[
                    "Sustainability scoring system",
                    "Price-eco balance recommendations",
                    "Local eco-friendly store finder",
                    "Carbon footprint tracking"
                ],
                difficulty="medium"
            ),
            DemoExample(
                name="Healthcare Scheduler",
                description="AI-powered medical appointment management",
                topic="Intelligent healthcare appointment scheduling system",
                icp="Healthcare providers and patients",
                seed_pains=[
                    "Appointment no-shows",
                    "Inefficient scheduling",
                    "Patient wait times",
                    "Emergency slot management"
                ],
                seed_competitors=[
                    "Zocdoc",
                    "Healthgrades",
                    "WebMD",
                    "MyChart"
                ],
                expected_outcomes=[
                    "Predictive no-show prevention",
                    "Optimized scheduling algorithms",
                    "Real-time availability updates",
                    "Emergency triage integration"
                ],
                difficulty="hard"
            ),
            DemoExample(
                name="Learning Platform",
                description="Personalized AI learning assistant",
                topic="AI-powered personalized learning platform",
                icp="Students and lifelong learners",
                seed_pains=[
                    "One-size-fits-all learning approaches",
                    "Difficulty maintaining motivation",
                    "Inefficient study planning",
                    "Knowledge gap identification"
                ],
                seed_competitors=[
                    "Coursera",
                    "Khan Academy",
                    "Duolingo",
                    "Quizlet"
                ],
                expected_outcomes=[
                    "Adaptive learning paths",
                    "Motivation tracking system",
                    "Smart study scheduling",
                    "Personalized content recommendations"
                ],
                difficulty="medium"
            )
        ]
    
    def get_demo_examples(self) -> list[DemoExample]:
        """Get all available demo examples"""
        return self.demo_examples
    
    def get_demo_example(self, name: str) -> DemoExample:
        """Get specific demo example by name"""
        for example in self.demo_examples:
            if example.name == name:
                return example
        raise ValueError(f"Demo example '{name}' not found")
    
    def generate_demo_config(self, example: DemoExample) -> dict[str, Any]:
        """Generate demo configuration for a specific example"""
        return {
            "demo_mode": True,
            "demo_example": example.name,
            "topic": example.topic,
            "n_ideas": 5,
            "fast_mode": True,
            "seed_icp": example.icp,
            "seed_pains": example.seed_pains,
            "seed_competitors": example.seed_competitors,
            "max_sources": 5,
            "signal_sources_target": 3,
            "signal_pains_target": 4,
            "market_signal_threshold": 30,
            "enable_demo_data": True
        }
    
    def create_demo_run_data(self, example: DemoExample) -> dict[str, Any]:
        """Create pre-generated demo run data for quick demonstration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = f"demo_{timestamp}_{hash(example.name) % 1000000:06d}"
        
        # Mock market research data
        market_data = {
            "market_size": f"${(hash(example.name) % 50 + 10)}B",
            "growth_rate": f"{(hash(example.name) % 30 + 10)}%",
            "key_trends": [
                "AI integration",
                "Mobile-first approach",
                "Subscription models",
                "Data privacy focus"
            ],
            "competitor_analysis": {
                comp: {
                    "market_share": f"{(hash(comp) % 25 + 5)}%",
                    "strengths": ["Brand recognition", "User base"],
                    "weaknesses": ["Limited AI features", "High pricing"]
                }
                for comp in example.seed_competitors[:3]
            }
        }
        
        # Mock MVP features
        mvp_features = [
            f"AI-powered {example.name.lower()} core functionality",
            "User dashboard and analytics",
            "Mobile application",
            "Integration capabilities",
            "Basic reporting system"
        ]
        
        # Mock tech stack
        tech_stack = {
            "frontend": "Next.js + TypeScript + Tailwind CSS",
            "backend": "FastAPI + Python + PostgreSQL",
            "ai": "Ollama + LangChain + CrewAI",
            "deployment": "Docker + AWS/Azure"
        }
        
        return {
            "run_id": run_id,
            "example": example.name,
            "topic": example.topic,
            "status": "completed",
            "generated_at": datetime.now().isoformat(),
            "artifacts": {
                "market_research": market_data,
                "mvp_features": mvp_features,
                "tech_stack": tech_stack,
                "business_model": "Subscription-based with freemium tier",
                "target_audience": example.icp,
                "key_differentiators": [
                    "AI-first approach",
                    "Superior user experience",
                    "Competitive pricing",
                    "Advanced analytics"
                ]
            },
            "demo_notes": {
                "difficulty": example.difficulty,
                "estimated_development_time": self._estimate_dev_time(example.difficulty),
                "key_challenges": example.seed_pains[:2],
                "market_opportunity": "High growth in AI-powered solutions"
            }
        }
    
    def _estimate_dev_time(self, difficulty: str) -> str:
        """Estimate development time based on difficulty"""
        time_map = {
            "easy": "2-3 months",
            "medium": "4-6 months",
            "hard": "6-9 months"
        }
        return time_map.get(difficulty, "3-6 months")
    
    def save_demo_data(self, example: DemoExample) -> str:
        """Save demo data to file and return path"""
        demo_data = self.create_demo_run_data(example)
        
        # Create demo file
        demo_file = self.demo_data_dir / f"demo_{example.name.lower().replace(' ', '_')}.json"
        
        with open(demo_file, 'w', encoding='utf-8') as f:
            json.dump(demo_data, f, indent=2, ensure_ascii=False)
        
        return str(demo_file)
    
    def load_demo_data(self, example_name: str) -> dict[str, Any]:
        """Load demo data for a specific example"""
        demo_file = self.demo_data_dir / f"demo_{example_name.lower().replace(' ', '_')}.json"
        
        if demo_file.exists():
            with open(demo_file, encoding='utf-8') as f:
                return json.load(f)
        
        # Generate and save if doesn't exist
        example = self.get_demo_example(example_name)
        self.save_demo_data(example)
        return self.create_demo_run_data(example)
    
    def get_demo_tour_steps(self) -> list[dict[str, Any]]:
        """Get interactive demo tour steps"""
        return [
            {
                "step": 1,
                "title": "Welcome to Asmblr!",
                "content": "Asmblr transforms your ideas into launch-ready MVPs using AI. Let's take a quick tour!",
                "highlight": "welcome_section",
                "action": "next"
            },
            {
                "step": 2,
                "title": "Choose Your Approach",
                "content": "Start with a vague idea, a validated concept, or analyze competitors. Each path is optimized for different starting points.",
                "highlight": "approach_selector",
                "action": "select_approach"
            },
            {
                "step": 3,
                "title": "Configure Your ICP",
                "content": "Define your Ideal Customer Profile to focus the AI analysis on your target market.",
                "highlight": "icp_section",
                "action": "configure_icp"
            },
            {
                "step": 4,
                "title": "AI Agents at Work",
                "content": "Watch our specialized AI agents research, analyze, and generate your MVP components in real-time.",
                "highlight": "pipeline_status",
                "action": "monitor_pipeline"
            },
            {
                "step": 5,
                "title": "Review Generated Artifacts",
                "content": "Explore market reports, PRDs, tech specs, and generated code. Everything is production-ready!",
                "highlight": "results_section",
                "action": "explore_results"
            },
            {
                "step": 6,
                "title": "Launch Your MVP!",
                "content": "Your MVP is ready to deploy. Check out the generated repository and landing page.",
                "highlight": "launch_section",
                "action": "launch_mvp"
            }
        ]
    
    def get_demo_checklist(self) -> dict[str, Any]:
        """Get demo mode checklist for users"""
        return {
            "pre_demo": [
                "✅ Ollama installed and running",
                "✅ AI models downloaded (llama3.1:8b, qwen2.5-coder:7b)",
                "✅ Python environment setup",
                "✅ Dependencies installed"
            ],
            "demo_steps": [
                "🎯 Select a demo example",
                "⚙️ Review configuration",
                "🚀 Start the generation",
                "👀 Monitor AI agents",
                "📊 Review results",
                "🎉 Explore generated MVP"
            ],
            "post_demo": [
                "📚 Read the documentation",
                "🔧 Try your own idea",
                "🤝 Join the community",
                "⭐ Star the repository"
            ],
            "tips": [
                "💡 Start with 'AI Task Management' for an easy demo",
                "💡 Use Fast Mode for quicker results",
                "💡 Check the runs/ directory for all artifacts",
                "💡 Each demo generates a complete MVP package"
            ]
        }


def is_demo_mode_enabled() -> bool:
    """Check if demo mode is enabled"""
    from app.core.public_config import is_demo_mode
    return is_demo_mode()


def get_demo_manager(base_dir: Path = None) -> DemoModeManager:
    """Get demo mode manager instance"""
    if base_dir is None:
        from app.core.config import get_settings
        settings = get_settings()
        base_dir = settings.base_dir
    
    return DemoModeManager(base_dir)


def run_demo_presentation(example_name: str = "AI Task Management"):
    """Run a complete demo presentation"""
    manager = get_demo_manager()
    
    print(f"""
    🎭 Asmblr Demo Presentation: {example_name}
    {'='*50}
    """)
    
    try:
        example = manager.get_demo_example(example_name)
        
        print(f"📋 Example: {example.name}")
        print(f"📝 Description: {example.description}")
        print(f"🎯 Topic: {example.topic}")
        print(f"👥 Target Audience: {example.icp}")
        print(f"⚡ Difficulty: {example.difficulty}")
        
        print(f"\n🔍 Key Pain Points:")
        for i, pain in enumerate(example.seed_pains, 1):
            print(f"  {i}. {pain}")
        
        print(f"\n🏆 Expected Solutions:")
        for i, solution in enumerate(example.expected_outcomes, 1):
            print(f"  {i}. {solution}")
        
        print(f"\n📊 Demo Data:")
        demo_data = manager.create_demo_run_data(example)
        
        print(f"  📈 Market Size: {demo_data['artifacts']['market_research']['market_size']}")
        print(f"  📈 Growth Rate: {demo_data['artifacts']['market_research']['growth_rate']}")
        print(f"  ⏱️  Development Time: {demo_data['demo_notes']['estimated_development_time']}")
        
        print(f"\n🛠️  Tech Stack:")
        tech_stack = demo_data['artifacts']['tech_stack']
        for component, technology in tech_stack.items():
            print(f"  {component.title()}: {technology}")
        
        print(f"\n🚀 MVP Features:")
        for i, feature in enumerate(demo_data['artifacts']['mvp_features'], 1):
            print(f"  {i}. {feature}")
        
        print(f"\n✨ Demo completed successfully!")
        print(f"💡 Try it yourself: streamlit run app/ui.py")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("💡 Make sure Asmblr is properly installed and configured")


# Demo data generator for testing
def generate_sample_market_data(topic: str) -> dict[str, Any]:
    """Generate sample market research data for testing"""
    return {
        "topic": topic,
        "market_analysis": {
            "total_addressable_market": f"${(hash(topic) % 100 + 10)}B",
            "serviceable_addressable_market": f"${(hash(topic) % 50 + 5)}B",
            "serviceable_obtainable_market": f"${(hash(topic) % 20 + 1)}B",
            "growth_rate": f"{(hash(topic) % 30 + 10)}% CAGR"
        },
        "competitors": [
            {
                "name": f"Competitor {i}",
                "market_share": f"{(hash(topic + str(i)) % 25 + 5)}%",
                "strengths": ["Brand recognition", "User base"],
                "weaknesses": ["Limited features", "High pricing"]
            }
            for i in range(3)
        ],
        "trends": [
            "AI integration",
            "Mobile-first approach",
            "Subscription models",
            "Data privacy focus"
        ],
        "opportunities": [
            "Underserved market segments",
            "Technology gaps",
            "User experience improvements",
            "Pricing innovation"
        ]
    }


if __name__ == "__main__":
    # Run demo presentation
    run_demo_presentation()
