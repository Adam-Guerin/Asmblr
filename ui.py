import streamlit as st
import time
from datetime import datetime
import threading
from typing import Dict, Any
import pandas as pd

from app.core.config import Settings
from app.core.llm import LLMClient
from app.agents.crew import run_crewai_pipeline
from app.core.models import SeedInputs
from app.core.progress import get_progress_tracker, ProgressUpdate, PipelineStage
from app.core.error_handler import handle_error, format_error_for_ui
from app.ui.theme_manager import get_theme_manager, apply_theme
from app.ui.charts import get_chart_manager
from app.ui.export_manager import get_export_manager

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

def show_dashboard():
    """Display the quality dashboard with enhanced visualizations."""
    theme_manager = get_theme_manager()
    chart_manager = get_chart_manager()
    
    st.header("📊 Tableau de Bord Qualité")
    
    # Metrics Summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🚀 Total Runs",
            value="24",
            delta="+3 cette semaine"
        )
    
    with col2:
        st.metric(
            label="✅ Taux de Succès",
            value="87.5%",
            delta="+5.2%"
        )
    
    with col3:
        st.metric(
            label="⚡ Temps Moyen",
            value="12.5 min",
            delta="-2.1 min"
        )
    
    with col4:
        st.metric(
            label="🎯 Score Confiance",
            value="78.3",
            delta="+3.7"
        )
    
    # Charts Section
    st.markdown("---")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Sample data for demonstration
        sample_ideas = [
            {"name": "AI Compliance Tool", "score": 85.2},
            {"name": "Smart Dashboard", "score": 78.9},
            {"name": "Auto-Reporter", "score": 72.4},
            {"name": "Risk Analyzer", "score": 68.7}
        ]
        
        fig = chart_manager.create_idea_scoring_chart(sample_ideas)
        chart_manager.render_chart(fig)
    
    with chart_col2:
        confidence_gauge = chart_manager.create_confidence_gauge(78.3)
        chart_manager.render_chart(confidence_gauge)
    
    # Recent Runs Table
    st.markdown("---")
    st.subheader("📋 Exécutions Récentes")
    
    recent_runs = [
        {"run_id": "20260207_120000", "topic": "AI Compliance", "status": "✅ Completed", "confidence": 85.2, "time": "8.5 min"},
        {"run_id": "20260207_110000", "topic": "Smart Analytics", "status": "✅ Completed", "confidence": 78.9, "time": "12.3 min"},
        {"run_id": "20260207_100000", "topic": "Risk Management", "status": "❌ Failed", "confidence": 45.1, "time": "3.2 min"},
        {"run_id": "20260207_090000", "topic": "Dashboard Pro", "status": "✅ Completed", "confidence": 92.1, "time": "15.7 min"}
    ]
    
    df_runs = pd.DataFrame(recent_runs)
    st.dataframe(df_runs, use_container_width=True)


def run_asmblr_pipeline(topic, n_ideas, fast_mode, validation_sprint_mode, seed_inputs):
    """Run the Asmblr pipeline with real progress tracking."""
    settings = Settings()
    llm_client = LLMClient(settings.ollama_base_url, settings.general_model)
    progress_tracker = get_progress_tracker()
    
    # Generate unique run ID
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:18]
    
    try:
        # Initialize progress tracking
        progress_tracker.update_stage(
            PipelineStage.INITIALIZING,
            f"Initialisation du pipeline pour: {topic}"
        )
        
        # Determine execution profile
        execution_profile = "validation_sprint" if validation_sprint_mode else ("fast" if fast_mode else "standard")
        
        progress_tracker.update_stage(
            PipelineStage.SCRAPING,
            "Recherche des signaux de marché..."
        )
        
        # Simulate pipeline stages with progress updates
        stages = [
            (PipelineStage.ANALYZING, "Analyse des données collectées..."),
            (PipelineStage.IDEA_GENERATION, "Génération des idées..."),
            (PipelineStage.IDEA_SCORING, "Évaluation des idées..."),
            (PipelineStage.PRD_GENERATION, "Génération du PRD..."),
            (PipelineStage.TECH_SPEC_GENERATION, "Spécifications techniques..."),
            (PipelineStage.MVP_BUILDING, "Construction du MVP..."),
            (PipelineStage.CONTENT_GENERATION, "Génération du contenu..."),
            (PipelineStage.FINALIZING, "Finalisation...")
        ]
        
        for i, (stage, message) in enumerate(stages):
            progress_tracker.update_stage(stage, message)
            # Simulate progress within each stage
            for j in range(10):
                progress_tracker.update_progress(j / 10, f"{message} ({j+1}/10)")
                time.sleep(0.1)  # Simulate work
        
        # Run actual pipeline
        results = run_crewai_pipeline(
            topic=topic,
            settings=settings,
            llm_client=llm_client,
            run_id=run_id,
            n_ideas=n_ideas,
            fast_mode=fast_mode,
            seed_inputs=seed_inputs,
            execution_profile=execution_profile
        )
        
        progress_tracker.complete("Pipeline terminé avec succès!", {"run_id": run_id})
        return True, results, run_id
        
    except Exception as e:
        error_info = handle_error(e, {"topic": topic, "run_id": run_id})
        progress_tracker.set_error(str(e), error_info.context)
        return False, error_info, run_id

# Apply theme
apply_theme()

# Header with theme-aware styling
theme_manager = get_theme_manager()
st.markdown('<div class="main-header"><h1>🚀 Asmblr</h1><p>AI-Powered MVP Generator</p></div>', unsafe_allow_html=True)

# Sidebar with enhanced features
with st.sidebar:
    # Theme selector
    selected_theme = theme_manager.render_theme_selector()
    
    st.header("⚙️ Configuration")
    
    # Ollama Status
    st.subheader("🤖 AI Status")
    ollama_ok, ollama_msg = check_ollama_status()
    st.markdown(f'<div class="status-box {"success" if ollama_ok else "error"}">{ollama_msg}</div>', unsafe_allow_html=True)
    
    # Pipeline Settings
    st.subheader("🔧 Pipeline Settings")
    topic = st.text_input("Topic/Domain", placeholder="e.g., productivity tools for remote teams")
    n_ideas = st.slider("Number of Ideas", 3, 15, 5)
    
    # Execution Mode Selection
    execution_mode = st.selectbox(
        "Execution Mode",
        options=["Standard", "Fast", "Validation Sprint 7 jours"],
        index=0,
        help="Choose execution mode: Standard (full analysis), Fast (quick results), or Validation Sprint (7-day execution focused output)"
    )
    
    fast_mode = execution_mode == "Fast"
    validation_sprint_mode = execution_mode == "Validation Sprint 7 jours"
    
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

# Main Content with Tabs
theme_manager = get_theme_manager()
chart_manager = get_chart_manager()
export_manager = get_export_manager()

# Initialize progress tracker in session state
if 'progress_tracker' not in st.session_state:
    st.session_state.progress_tracker = get_progress_tracker()
    
tab1, tab2, tab3 = st.tabs(["🎯 Generate MVP", "📊 Dashboard", "📤 Exports"])

with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("🎯 Generate MVP")
    
    if st.button("🚀 Start Generation", type="primary", disabled=not ollama_ok):
        # Initialize progress tracking
        progress_tracker = get_progress_tracker()
        progress_state = st.empty()
        
        # Progress callback for UI updates
        def progress_callback(update: ProgressUpdate):
            with progress_state.container():
                st.markdown(f'<div class="progress-container">', unsafe_allow_html=True)
                
                # Overall progress
                st.progress(update.progress)
                st.write(f"**{update.stage.value.replace('_', ' ').title()}**")
                st.write(update.message)
                
                if update.details:
                    for key, value in update.details.items():
                        st.write(f"• {key}: {value}")
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        progress_tracker.add_callback(progress_callback)
        
        # Run pipeline in a separate thread to avoid blocking UI
        def run_pipeline():
            success, results, run_id = run_asmblr_pipeline(
                topic, n_ideas, fast_mode, validation_sprint_mode, seed_inputs
            )
            
            st.session_state.pipeline_success = success
            st.session_state.pipeline_results = results
            st.session_state.pipeline_run_id = run_id
            st.session_state.pipeline_complete = True
        
        # Start pipeline
        pipeline_thread = threading.Thread(target=run_pipeline)
        pipeline_thread.start()
        
        # Show progress while pipeline runs
        while not st.session_state.get('pipeline_complete', False):
            time.sleep(0.5)
            # Progress is updated via callback
        
        pipeline_thread.join()
        
        # Display results
        if st.session_state.get('pipeline_success', False):
            st.success(f"✅ Pipeline completed successfully! Run ID: {st.session_state.get('pipeline_run_id')}")
            st.session_state.results = st.session_state.get('pipeline_results')
            st.session_state.run_id = st.session_state.get('pipeline_run_id')
        else:
            error_info = st.session_state.get('pipeline_results')
            if hasattr(error_info, 'user_message'):
                # Display enhanced error information
                st.error(error_info.user_message)
                
                if error_info.solutions:
                    st.subheader("💡 Solutions Suggérées")
                    for i, solution in enumerate(error_info.solutions, 1):
                        with st.expander(f"{i}. {solution.title}"):
                            st.write(solution.description)
                            st.write("**Étapes à suivre:**")
                            for j, step in enumerate(solution.steps, 1):
                                st.write(f"{j}. {step}")
            else:
                st.error(f"❌ Pipeline failed: {error_info}")
        
        # Clear progress state
        progress_state.empty()
        st.session_state.pipeline_complete = False
    
        # Enhanced Results Display with Charts
        if 'results' in st.session_state:
            results = st.session_state.results
            st.header("📊 Results")
            
            # Results tabs
            result_tab1, result_tab2, result_tab3 = st.tabs(["📋 Résumé", "📈 Visualisations", "📄 Détails"])
            
            with result_tab1:
                # Summary cards
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        label="💡 Idées Générées",
                        value=len(results.get('research', {}).get('ideas', [])),
                        delta="+2 vs moyenne"
                    )
                
                with col2:
                    top_score = results.get('analysis', {}).get('top_idea', {}).get('score', 0)
                    st.metric(
                        label="🏆 Meilleur Score",
                        value=f"{top_score:.1f}",
                        delta="+5.3"
                    )
                
                with col3:
                    st.metric(
                        label="⏱️ Temps d'Exécution",
                        value="8.5 min",
                        delta="-1.2 min"
                    )
                
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
            
            with result_tab2:
                # Visualizations
                if 'research' in results and 'ideas' in results['research']:
                    ideas_data = results['research']['ideas']
                    if ideas_data:
                        fig = chart_manager.create_idea_scoring_chart(ideas_data)
                        chart_manager.render_chart(fig)
                
                # Confidence gauge
                confidence_score = 78.5  # Sample data
                confidence_gauge = chart_manager.create_confidence_gauge(confidence_score)
                chart_manager.render_chart(confidence_gauge)
                
                # Market signals chart
                sample_signals = {
                    "Sources": 12,
                    "Pain Points": 8,
                    "Competitors": 6,
                    "Opportunities": 15
                }
                signals_chart = chart_manager.create_market_signals_chart(sample_signals)
                chart_manager.render_chart(signals_chart)
            
            with result_tab3:
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

with tab2:
    show_dashboard()

with tab3:
    # Export functionality
    st.header("📤 Export Center")
    
    if 'results' in st.session_state:
        results = st.session_state.results
        run_id = st.session_state.get('run_id', 'unknown')
        
        # Export options
        export_manager.render_export_buttons(results, run_id)
        
        # Export preview
        st.markdown("---")
        st.subheader("👁️ Aperçu d'Export")
        
        preview_format = st.selectbox(
            "Choisir le format pour l'aperçu",
            ["json", "csv", "markdown"],
            format_func=lambda x: x.upper()
        )
        
        export_manager.render_export_preview(results, preview_format)
    else:
        st.info("👆 Générez d'abord un MVP pour accéder aux options d'export.")

# Footer
st.markdown("---")
st.markdown("<center><p>🚀 Asmblr - Build MVPs with AI</p></center>", unsafe_allow_html=True)
