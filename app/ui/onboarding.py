"""
User-friendly onboarding system for Asmblr
Guides new users through setup and first MVP generation
"""

import streamlit as st
import time
from dataclasses import dataclass

from app.core.demo_mode import get_demo_manager


@dataclass
class OnboardingStep:
    """Onboarding step configuration"""
    step_id: str
    title: str
    description: str
    component: str  # setup, demo, explore, launch
    estimated_time: str
    required: bool = True
    completed: bool = False


class OnboardingManager:
    """Manages user onboarding experience"""
    
    def __init__(self):
        self.demo_manager = get_demo_manager()
        self.steps = self._initialize_steps()
        
    def _initialize_steps(self) -> list[OnboardingStep]:
        """Initialize onboarding steps"""
        return [
            OnboardingStep(
                step_id="welcome",
                title="Welcome to Asmblr!",
                description="Let's get you set up to generate your first AI-powered MVP",
                component="setup",
                estimated_time="2 minutes"
            ),
            OnboardingStep(
                step_id="environment_check",
                title="Environment Setup",
                description="Verify your development environment and AI models",
                component="setup",
                estimated_time="3 minutes"
            ),
            OnboardingStep(
                step_id="demo_selection",
                title="Choose Your Demo",
                description="Select a pre-configured example to see Asmblr in action",
                component="demo",
                estimated_time="1 minute"
            ),
            OnboardingStep(
                step_id="first_generation",
                title="Generate Your First MVP",
                description="Watch AI agents create a complete MVP package",
                component="demo",
                estimated_time="5-10 minutes"
            ),
            OnboardingStep(
                step_id="explore_results",
                title="Explore Your Results",
                description="Discover the generated artifacts and capabilities",
                component="explore",
                estimated_time="3 minutes"
            ),
            OnboardingStep(
                step_id="next_steps",
                title="What's Next?",
                description="Learn how to use Asmblr for your own ideas",
                component="launch",
                estimated_time="2 minutes"
            )
        ]
    
    def get_current_step(self) -> OnboardingStep | None:
        """Get current onboarding step"""
        if 'onboarding_step' not in st.session_state:
            st.session_state.onboarding_step = 0
        
        step_index = st.session_state.onboarding_step
        if 0 <= step_index < len(self.steps):
            return self.steps[step_index]
        return None
    
    def next_step(self):
        """Move to next onboarding step"""
        current_index = st.session_state.get('onboarding_step', 0)
        if current_index < len(self.steps) - 1:
            st.session_state.onboarding_step = current_index + 1
            return True
        return False
    
    def previous_step(self):
        """Move to previous onboarding step"""
        current_index = st.session_state.get('onboarding_step', 0)
        if current_index > 0:
            st.session_state.onboarding_step = current_index - 1
            return True
        return False
    
    def mark_step_completed(self, step_id: str):
        """Mark a step as completed"""
        for step in self.steps:
            if step.step_id == step_id:
                step.completed = True
                break
    
    def get_progress(self) -> float:
        """Get onboarding progress percentage"""
        completed = sum(1 for step in self.steps if step.completed)
        return completed / len(self.steps)


def render_welcome_step(manager: OnboardingManager):
    """Render welcome step"""
    st.markdown("""
    # 🚀 Welcome to Asmblr!
    
    Transform your ideas into launch-ready MVPs with AI-powered automation.
    
    Asmblr uses advanced AI agents to research markets, analyze competitors, 
    and generate complete MVP packages including:
    - 📊 Market research reports
    - 📋 Product requirements documents  
    - 🛠️ Technical specifications
    - 💻 Complete code repositories
    - 🎨 Landing pages and marketing content
    
    ## What You'll Experience
    
    In this onboarding, you'll:
    1. ✅ Verify your environment setup
    2. 🎮 Try a pre-configured demo
    3. 🤖 Watch AI agents work their magic
    4. 📦 Explore your generated MVP package
    
    ## System Requirements
    
    - Python 3.9+
    - Ollama (local AI models)
    - 8GB+ RAM recommended
    - 10GB+ disk space
    
    Ready to get started? Let's verify your setup!
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("🚀 Start Setup", type="primary", use_container_width=True):
            manager.next_step()
            st.rerun()
    
    with col2:
        if st.button("⏭️ Skip Onboarding"):
            st.session_state.show_onboarding = False
            st.rerun()


def render_environment_check(manager: OnboardingManager):
    """Render environment check step"""
    st.markdown("## 🔍 Environment Setup Check")
    
    # Check Python version
    import sys
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    # Check Ollama
    ollama_status = "❌ Not installed/running"
    ollama_details = "Install Ollama from https://ollama.ai/download"
    
    try:
        import httpx
        with httpx.Client(timeout=5.0) as client:
            response = client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                ollama_status = "✅ Running"
                models = response.json().get('models', [])
                ollama_details = f"Found {len(models)} models"
    except:
        pass
    
    # Check dependencies
    dependencies_status = "✅ Installed"
    try:
        from app.core.config import get_settings
        from app.core.llm import LLMClient
    except ImportError as e:
        dependencies_status = f"❌ Missing: {e}"
    
    # Display checks
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Python Version", python_version, "✅" if sys.version_info >= (3, 9) else "❌")
        st.caption("Required: 3.9+")
    
    with col2:
        st.metric("Ollama Status", ollama_status)
        st.caption(ollama_details)
    
    with col3:
        st.metric("Dependencies", dependencies_status)
        st.caption("Core modules")
    
    # Installation instructions if needed
    if ollama_status != "✅ Running":
        st.warning("""
        ### 📥 Ollama Setup Required
        
        **Quick Install:**
        ```bash
        # Linux/Mac
        curl -fsSL https://ollama.ai/install.sh | sh
        
        # Windows
        # Download from https://ollama.ai/download
        ```
        
        **Start Ollama:**
        ```bash
        ollama serve
        ```
        
        **Download Models:**
        ```bash
        ollama pull llama3.1:8b
        ollama pull qwen2.5-coder:7b
        ```
        """)
    
    # Check if everything is ready
    all_ready = (
        sys.version_info >= (3, 9) and 
        ollama_status == "✅ Running" and 
        dependencies_status == "✅ Installed"
    )
    
    if all_ready:
        st.success("🎉 Your environment is ready for Asmblr!")
        manager.mark_step_completed("environment_check")
    else:
        st.info("⚠️ Complete the setup above, then continue")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("🔄 Re-check Environment", use_container_width=True):
            st.rerun()
    
    with col2:
        if all_ready and st.button("Continue →", type="primary", use_container_width=True):
            manager.next_step()
            st.rerun()


def render_demo_selection(manager: OnboardingManager):
    """Render demo selection step"""
    st.markdown("## 🎮 Choose Your Demo Experience")
    
    st.info("""
    Select a pre-configured example to see Asmblr in action. 
    Each demo includes realistic data and generates a complete MVP package.
    """)
    
    examples = manager.demo_manager.get_demo_examples()
    
    # Create demo cards
    cols = st.columns(len(examples))
    
    selected_example = None
    
    for i, example in enumerate(examples):
        with cols[i % len(cols)]:
            difficulty_color = {
                "easy": "🟢",
                "medium": "🟡", 
                "hard": "🔴"
            }.get(example.difficulty, "⚪")
            
            with st.container(border=True):
                st.markdown(f"### {difficulty_color} {example.name}")
                st.markdown(f"{example.description}")
                st.caption(f"Difficulty: {example.difficulty.title()}")
                
                if st.button(f"Try This Demo", key=f"demo_{i}", use_container_width=True):
                    selected_example = example
                    st.session_state.selected_demo = example
    
    # Show details for selected demo
    if 'selected_demo' in st.session_state:
        example = st.session_state.selected_demo
        
        st.markdown("---")
        st.markdown(f"### 📋 {example.name} Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🎯 Target Audience:**")
            st.markdown(example.icp)
            
            st.markdown("**⚡ Expected Outcomes:**")
            for outcome in example.expected_outcomes:
                st.markdown(f"• {outcome}")
        
        with col2:
            st.markdown("**🔍 Key Pain Points:**")
            for pain in example.seed_pains:
                st.markdown(f"• {pain}")
            
            st.markdown("**🏆 Competitors:**")
            for comp in example.seed_competitors[:3]:
                st.markdown(f"• {comp}")
        
        if st.button("🚀 Start This Demo", type="primary", use_container_width=True):
            manager.mark_step_completed("demo_selection")
            st.session_state.demo_config = manager.demo_manager.generate_demo_config(example)
            manager.next_step()
            st.rerun()


def render_first_generation(manager: OnboardingManager):
    """Render first MVP generation step"""
    st.markdown("## 🤖 Generate Your First MVP")
    
    if 'demo_config' not in st.session_state:
        st.error("No demo configuration found. Please go back and select a demo.")
        if st.button("← Back to Demo Selection"):
            manager.previous_step()
            st.rerun()
        return
    
    demo_config = st.session_state.demo_config
    example_name = demo_config.get('demo_example', 'Demo')
    
    st.info(f"""
    **Demo:** {example_name}
    
    **Topic:** {demo_config['topic']}
    
    **Configuration:** Fast mode with 5 ideas, optimized for quick demonstration
    """)
    
    # Start generation
    if st.button("🚀 Start Generation", type="primary", use_container_width=True):
        st.session_state.generation_started = True
        st.session_state.generation_progress = 0
        st.rerun()
    
    # Show generation progress
    if st.session_state.get('generation_started', False):
        st.markdown("### 📊 Generation Progress")
        
        progress_bar = st.progress(0, text="Initializing AI agents...")
        
        # Simulate generation progress
        progress_steps = [
            (10, "🔍 Researching market trends..."),
            (25, "📈 Analyzing competitors..."),
            (40, "💡 Generating product ideas..."),
            (60, "📋 Creating product requirements..."),
            (75, "🛠️ Designing technical architecture..."),
            (90, "💻 Generating code repository..."),
            (100, "🎨 Creating landing page...")
        ]
        
        current_progress = st.session_state.get('generation_progress', 0)
        
        for progress, message in progress_steps:
            if current_progress >= progress:
                st.info(message)
        
        # Auto-advance progress
        if current_progress < 100:
            st.session_state.generation_progress = min(100, current_progress + 15)
            time.sleep(1)
            st.rerun()
        else:
            st.success("🎉 MVP Generation Complete!")
            manager.mark_step_completed("first_generation")
            
            if st.button("📦 Explore Results →", type="primary", use_container_width=True):
                manager.next_step()
                st.rerun()


def render_explore_results(manager: OnboardingManager):
    """Render results exploration step"""
    st.markdown("## 📦 Explore Your Generated MVP")
    
    if 'demo_config' not in st.session_state:
        st.error("No demo results found. Please complete the generation step first.")
        return
    
    example_name = st.session_state.demo_config.get('demo_example', 'Demo')
    demo_data = manager.demo_manager.load_demo_data(example_name)
    
    # Show results tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Market Research", "📋 Product Specs", "🛠️ Tech Stack", "🚀 Launch Ready"])
    
    with tab1:
        st.markdown("### 📈 Market Analysis")
        
        market_data = demo_data['artifacts']['market_research']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Market Size", market_data['market_size'])
        with col2:
            st.metric("Growth Rate", market_data['growth_rate'])
        with col3:
            st.metric("Key Trends", str(len(market_data['key_trends'])))
        
        st.markdown("**🔍 Market Trends:**")
        for trend in market_data['key_trends']:
            st.markdown(f"• {trend}")
    
    with tab2:
        st.markdown("### 📋 Product Features")
        
        features = demo_data['artifacts']['mvp_features']
        
        for i, feature in enumerate(features, 1):
            st.markdown(f"{i}. {feature}")
        
        st.markdown("### 🎯 Business Model")
        st.markdown(demo_data['artifacts']['business_model'])
    
    with tab3:
        st.markdown("### 🛠️ Technology Stack")
        
        tech_stack = demo_data['artifacts']['tech_stack']
        
        for component, technology in tech_stack.items():
            st.markdown(f"**{component.title()}:** {technology}")
        
        st.markdown("### ⏱️ Development Timeline")
        st.info(f"Estimated: {demo_data['demo_notes']['estimated_development_time']}")
    
    with tab4:
        st.markdown("### 🚀 Ready to Launch!")
        
        st.success("""
        Your MVP package includes:
        - ✅ Complete market research
        - ✅ Product requirements document
        - ✅ Technical specifications
        - ✅ Code repository structure
        - ✅ Landing page design
        - ✅ Marketing content pack
        """)
        
        st.markdown("### 📁 Generated Files")
        st.code("""
        runs/demo_123456/
        ├── market_report.md
        ├── prd.md
        ├── tech_spec.md
        ├── repo_skeleton/
        ├── landing_page/
        └── content_pack/
        """)
    
    manager.mark_step_completed("explore_results")
    
    if st.button("🎉 Complete Onboarding →", type="primary", use_container_width=True):
        manager.next_step()
        st.rerun()


def render_next_steps(manager: OnboardingManager):
    """Render next steps step"""
    st.markdown("## 🎉 Congratulations! 🎉")
    
    st.success("""
    You've successfully completed the Asmblr onboarding and generated your first AI-powered MVP!
    
    You're now ready to:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🚀 Try Your Own Ideas
        
        1. **Start a New Run**
           - Use your own topic
           - Configure your ICP
           - Generate custom MVPs
        
        2. **Explore Advanced Features**
           - Custom tech stacks
           - Advanced configurations
           - Integration options
        """)
        
        if st.button("💡 Create Your Own MVP", type="primary", use_container_width=True):
            st.session_state.show_onboarding = False
            st.session_state.new_run_mode = True
            st.rerun()
    
    with col2:
        st.markdown("""
        ### 📚 Continue Learning
        
        1. **Documentation**
           - Read the full guide
           - Explore configuration options
           - Learn advanced techniques
        
        2. **Join the Community**
           - GitHub discussions
           - Share your creations
           - Get help and support
        """)
        
        if st.button("📖 Read Documentation", use_container_width=True):
            st.session_state.show_onboarding = False
            st.session_state.show_docs = True
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 🌟 Quick Tips")
    
    tips = [
        "💡 Start with Fast Mode for quicker results",
        "💡 Use specific topics for better results", 
        "💡 Configure your ICP for targeted analysis",
        "💡 Check the runs/ directory for all artifacts",
        "💡 Share your MVPs with the community!"
    ]
    
    cols = st.columns(3)
    for i, tip in enumerate(tips):
        with cols[i % 3]:
            st.markdown(tip)
    
    # Complete onboarding
    manager.mark_step_completed("next_steps")
    
    st.markdown("---")
    if st.button("🎊 Start Using Asmblr!", type="primary", use_container_width=True):
        st.session_state.show_onboarding = False
        st.rerun()


def render_onboarding():
    """Render main onboarding interface"""
    if 'show_onboarding' not in st.session_state:
        st.session_state.show_onboarding = True
    
    if not st.session_state.show_onboarding:
        return
    
    manager = OnboardingManager()
    current_step = manager.get_current_step()
    
    if not current_step:
        st.session_state.show_onboarding = False
        return
    
    # Progress bar
    progress = manager.get_progress()
    st.progress(progress, text=f"Onboarding Progress: {int(progress * 100)}%")
    
    # Step navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if manager.steps.index(current_step) > 0:
            if st.button("← Previous"):
                manager.previous_step()
                st.rerun()
    
    with col3:
        if st.button("⏭️ Skip Onboarding"):
            st.session_state.show_onboarding = False
            st.rerun()
    
    # Render current step
    step_renderers = {
        "welcome": render_welcome_step,
        "environment_check": render_environment_check,
        "demo_selection": render_demo_selection,
        "first_generation": render_first_generation,
        "explore_results": render_explore_results,
        "next_steps": render_next_steps
    }
    
    renderer = step_renderers.get(current_step.step_id)
    if renderer:
        renderer(manager)
    else:
        st.error(f"Unknown onboarding step: {current_step.step_id}")


def show_onboarding_prompt():
    """Show onboarding prompt for new users"""
    if 'onboarding_completed' not in st.session_state:
        st.session_state.onboarding_completed = False
    
    if not st.session_state.onboarding_completed:
        st.markdown("""
        ## 🎯 New to Asmblr?
        
        Take a quick guided tour to learn how to generate AI-powered MVPs!
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Start Guided Tour", type="primary", use_container_width=True):
                st.session_state.show_onboarding = True
                st.rerun()
        
        with col2:
            if st.button("⏭️ Skip for Now"):
                st.session_state.onboarding_completed = True
                st.rerun()


if __name__ == "__main__":
    # Test onboarding system
    render_onboarding()
