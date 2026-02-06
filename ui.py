import streamlit as st
import json
import time
from pathlib import Path
from datetime import datetime

from app.core.config import Settings
from app.core.llm import LLMClient
from app.agents.crew import run_crewai_pipeline
from app.core.models import SeedInputs

st.set_page_config(
    page_title="Asmblr - MVP Generator",
    page_icon="🚀",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success { background-color: #d4edda; border-left: 4px solid #28a745; }
    .warning { background-color: #fff3cd; border-left: 4px solid #ffc107; }
    .error { background-color: #f8d7da; border-left: 4px solid #dc3545; }
    .idea-card {
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def check_ollama_status():
    """Check if Ollama is running and models are available."""
    try:
        llm = LLMClient('http://localhost:11434', 'llama3.1:8b')
        if llm.available():
            # Test with a simple generation
            result = llm.generate('Say "hello"')
            return True, "✅ Ollama is running and responding"
        else:
            return False, "❌ Ollama not available"
    except Exception as e:
        return False, f"❌ Ollama error: {str(e)}"

def run_asmblr_pipeline(topic, n_ideas, fast_mode, seed_inputs):
    """Run the Asmblr pipeline and return results."""
    settings = Settings()
    llm_client = LLMClient(settings.ollama_base_url, settings.general_model)
    
    # Generate unique run ID
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:18]
    
    try:
        results = run_crewai_pipeline(
            topic=topic,
            settings=settings,
            llm_client=llm_client,
            run_id=run_id,
            n_ideas=n_ideas,
            fast_mode=fast_mode,
            seed_inputs=seed_inputs
        )
        return True, results, run_id
    except Exception as e:
        return False, str(e), run_id

# Header
st.markdown('<div class="main-header"><h1>🚀 Asmblr</h1><p>AI-Powered MVP Generator</p></div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Ollama Status
    st.subheader("🤖 AI Status")
    ollama_ok, ollama_msg = check_ollama_status()
    st.markdown(f'<div class="status-box {"success" if ollama_ok else "error"}">{ollama_msg}</div>', unsafe_allow_html=True)
    
    # Pipeline Settings
    st.subheader("🔧 Pipeline Settings")
    topic = st.text_input("Topic/Domain", placeholder="e.g., productivity tools for remote teams")
    n_ideas = st.slider("Number of Ideas", 3, 15, 5)
    fast_mode = st.checkbox("Fast Mode", help="Use fewer sources and simpler analysis")
    
    # Seed Inputs
    st.subheader("🌱 Seed Data")
    with st.expander("Advanced Seed Inputs"):
        icp = st.text_area("Ideal Customer Profile", placeholder="Describe your target user...")
        context = st.text_area("Context", placeholder="Additional context about the market...")
        pains = st.text_area("Pain Points", placeholder="One pain point per line...")
        competitors = st.text_area("Competitors", placeholder="One competitor per line...")
        
        seed_inputs = SeedInputs(
            icp=icp.strip() if icp else None,
            context=context.strip() if context else None,
            pains=[p.strip() for p in pains.split('\n') if p.strip()],
            competitors=[c.strip() for c in competitors.split('\n') if c.strip()]
        )

# Main Content
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🎯 Generate MVP")
    
    if st.button("🚀 Start Generation", type="primary", disabled=not ollama_ok):
        with st.spinner("🔄 Running Asmblr pipeline..."):
            progress = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("Initializing pipeline...")
                progress.progress(10)
                time.sleep(1)
                
                status_text.text("Researching market signals...")
                progress.progress(30)
                time.sleep(2)
                
                status_text.text("Analyzing ideas...")
                progress.progress(50)
                time.sleep(2)
                
                status_text.text("Generating MVP...")
                progress.progress(80)
                time.sleep(2)
                
                status_text.text("Finalizing...")
                progress.progress(100)
                
                success, results, run_id = run_asmblr_pipeline(topic, n_ideas, fast_mode, seed_inputs)
                
                if success:
                    st.success(f"✅ Pipeline completed successfully! Run ID: {run_id}")
                    st.session_state.results = results
                    st.session_state.run_id = run_id
                else:
                    st.error(f"❌ Pipeline failed: {results}")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Display Results
    if 'results' in st.session_state:
        results = st.session_state.results
        st.header("📊 Results")
        
        # Research Results
        if 'research' in results:
            research = results['research']
            st.subheader("🔍 Research Findings")
            
            if research.get('pain_statements'):
                st.write("**Pain Points Identified:**")
                for pain in research['pain_statements'][:5]:
                    st.write(f"• {pain}")
            
            if research.get('ideas'):
                st.write("**Generated Ideas:**")
                for idea in research['ideas']:
                    with st.expander(f"💡 {idea.get('name', 'Unnamed Idea')}"):
                        st.write(f"**One-liner:** {idea.get('one_liner', 'N/A')}")
                        st.write(f"**Target User:** {idea.get('target_user', 'N/A')}")
                        st.write(f"**Problem:** {idea.get('problem', 'N/A')}")
                        st.write(f"**Solution:** {idea.get('solution', 'N/A')}")
                        if idea.get('key_features'):
                            st.write("**Key Features:**")
                            for feature in idea['key_features']:
                                st.write(f"  • {feature}")
        
        # Analysis Results
        if 'analysis' in results:
            analysis = results['analysis']
            st.subheader("📈 Analysis")
            
            if analysis.get('top_idea'):
                top_idea = analysis['top_idea']
                st.markdown(f'<div class="idea-card"><h3>🏆 Top Idea: {top_idea.get("name", "N/A")}</h3><p><strong>Score:</strong> {top_idea.get("score", "N/A")}</p><p><strong>Rationale:</strong> {top_idea.get("rationale", "N/A")}</p></div>', unsafe_allow_html=True)
        
        # Product Results
        if 'product' in results:
            product = results['product']
            st.subheader("📋 Product Requirements")
            if product.get('prd_markdown'):
                st.markdown(product['prd_markdown'])
        
        # Tech Results
        if 'tech' in results:
            tech = results['tech']
            st.subheader("🛠️ Technical Specification")
            if tech.get('tech_spec_markdown'):
                st.markdown(tech['tech_spec_markdown'])
            if tech.get('repo_dir'):
                st.info(f"📁 Repository generated at: {tech['repo_dir']}")

with col2:
    st.header("📋 Quick Guide")
    
    with st.expander("🚀 Getting Started", expanded=True):
        st.markdown("""
        1. **Install Ollama**: Download and install Ollama from [ollama.ai](https://ollama.ai)
        2. **Start Ollama**: Run `ollama serve` in terminal
        3. **Pull Models**: 
           ```bash
           ollama pull llama3.1:8b
           ollama pull qwen2.5-coder:7b
           ```
        4. **Generate MVP**: Enter a topic and click "Start Generation"
        """)
    
    with st.expander("⚡ Tips"):
        st.markdown("""
        - **Fast Mode**: Quicker but less detailed analysis
        - **Seed Data**: Provide context for better results
        - **Number of Ideas**: More ideas = longer processing time
        - **Check Status**: Ensure Ollama is running before starting
        """)
    
    with st.expander("🔧 Troubleshooting"):
        st.markdown("""
        **Ollama not responding?**
        - Check if Ollama is running: `ollama list`
        - Restart Ollama service
        - Verify models are installed
        
        **Pipeline fails?**
        - Check internet connection
        - Try with Fast Mode enabled
        - Reduce number of ideas
        """)

# Footer
st.markdown("---")
st.markdown("<center><p>🚀 Asmblr - Build MVPs with AI</p></center>", unsafe_allow_html=True)
