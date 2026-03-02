import os
import time

from app.core.config import get_settings
from app.core.llm import check_ollama
from app.core.models import SeedInputs
from app.core.run_manager import RunManager
from app.ui_quality import render_quality_dashboard
from app.core.rate_limit import RateLimiter

settings = get_settings()
if settings.ui_host:
    os.environ.setdefault("STREAMLIT_SERVER_ADDRESS", settings.ui_host)
if settings.ui_port:
    os.environ.setdefault("STREAMLIT_SERVER_PORT", str(settings.ui_port))

import streamlit as st
manager = RunManager(settings.runs_dir, settings.data_dir)
ui_run_limiter = RateLimiter(settings.run_rate_limit_per_min, settings.run_rate_limit_burst)

# Enhanced UI Configuration
st.set_page_config(
    page_title="Asmblr - AI Venture Factory",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.asmblr.ai',
        'Report a bug': "https://github.com/asmblr/asmblr/issues",
        'About': "Asmblr v2.0 - AI-Powered Venture Factory"
    }
)

# Custom CSS for modern, professional design
st.markdown("""
<style>
/* Main theme colors */
:root {
    --primary-color: #6366f1;
    --secondary-color: #8b5cf6;
    --accent-color: #ec4899;
    --success-color: #10b981;
    --warning-color: #f59e0b;
    --error-color: #ef4444;
    --dark-bg: #0f172a;
    --light-bg: #f8fafc;
    --card-bg: #ffffff;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --border-color: #e2e8f0;
}

/* Dark mode support */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

/* Header styling */
.main-header {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    color: white;
    padding: 2rem;
    border-radius: 1rem;
    margin-bottom: 2rem;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

/* Card styling */
.metric-card {
    background: var(--card-bg);
    padding: 1.5rem;
    border-radius: 0.75rem;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    border: 1px solid var(--border-color);
    transition: all 0.3s ease;
    margin: 0.5rem 0;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.12);
}

/* Status indicators */
.status-running {
    background: linear-gradient(45deg, #10b981, #34d399);
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    font-size: 0.875rem;
    font-weight: 600;
}

.status-completed {
    background: linear-gradient(45deg, #6366f1, #8b5cf6);
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    font-size: 0.875rem;
    font-weight: 600;
}

.status-failed {
    background: linear-gradient(45deg, #ef4444, #f87171);
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    font-size: 0.875rem;
    font-weight: 600;
}

/* Button styling */
.stButton > button {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
}

/* Input styling */
.stTextInput > div > div > input,
.stSelectbox > div > div > select,
.stTextArea > div > div > textarea {
    border-radius: 0.5rem;
    border: 2px solid var(--border-color);
    transition: all 0.3s ease;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div > select:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

/* Progress bar styling */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
    border-radius: 0.5rem;
}

/* Agent thinking animation */
.agent-thinking {
    color: var(--text-secondary);
    font-size: 0.92rem;
    line-height: 1.45;
    padding: 0.35rem 0.5rem;
    margin: 0.15rem 0;
    border-left: 3px solid var(--primary-color);
    background: linear-gradient(
        110deg,
        rgba(99, 102, 241, 0.08) 8%,
        rgba(255, 255, 255, 0.2) 18%,
        rgba(99, 102, 241, 0.08) 33%
    );
    background-size: 220% 100%;
    animation: thinking-shimmer 2.8s linear infinite;
    border-radius: 0.25rem;
}

@keyframes thinking-shimmer {
    to {
        background-position: -220% 0;
    }
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: var(--card-bg);
    border-right: 1px solid var(--border-color);
}

/* Footer styling */
.footer {
    text-align: center;
    padding: 2rem;
    color: var(--text-secondary);
    border-top: 1px solid var(--border-color);
    margin-top: 3rem;
}

/* Responsive design */
@media (max-width: 768px) {
    .main-header {
        padding: 1rem;
    }
    
    .metric-card {
        padding: 1rem;
    }
}
</style>
""", unsafe_allow_html=True)

def render_header():
    """Render modern header with branding"""
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem; font-weight: 700;">
            🚀 Asmblr
        </h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">
            AI-Powered Venture Factory - Transform Ideas into Reality
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_metrics_dashboard():
    """Render enhanced metrics dashboard"""
    runs = manager.list_runs()
    
    if not runs:
        st.info("🎯 Start your first venture with Asmblr!")
        return
    
    # Calculate metrics
    total_runs = len(runs)
    completed_runs = len([r for r in runs if r.get('status') == 'completed'])
    running_runs = len([r for r in runs if r.get('status') == 'running'])
    failed_runs = len([r for r in runs if r.get('status') == 'failed'])
    
    # Recent activity
    recent_runs = sorted(runs, key=lambda x: x.get('updated_at', ''), reverse=True)[:5]
    
    # Render metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: var(--primary-color); margin: 0;">{total_runs}</h3>
            <p style="margin: 0.25rem 0; color: var(--text-secondary);">Total Ventures</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: var(--success-color); margin: 0;">{completed_runs}</h3>
            <p style="margin: 0.25rem 0; color: var(--text-secondary);">Completed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: var(--warning-color); margin: 0;">{running_runs}</h3>
            <p style="margin: 0.25rem 0; color: var(--text-secondary);">Running</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        success_rate = (completed_runs / total_runs * 100) if total_runs > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: var(--secondary-color); margin: 0;">{success_rate:.1f}%</h3>
            <p style="margin: 0.25rem 0; color: var(--text-secondary);">Success Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent activity
    if recent_runs:
        st.subheader("📊 Recent Activity")
        for run in recent_runs:
            status = run.get('status', 'unknown')
            status_class = f"status-{status}"
            
            st.markdown(f"""
            <div class="metric-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{run.get('topic', 'Unknown Topic')}</strong>
                        <br>
                        <small style="color: var(--text-secondary);">
                            {run.get('run_id', '')[:20]}... • {run.get('updated_at', '')[:16]}
                        </small>
                    </div>
                    <span class="{status_class}">{status.upper()}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

def render_venture_form():
    """Render enhanced venture creation form"""
    st.subheader("🎯 Create New Venture")
    
    # Form with better UX
    with st.form("venture_form"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            topic = st.text_input(
                "💡 Venture Topic",
                placeholder="e.g., AI-powered compliance for SMBs",
                help="Describe your venture idea in 3-200 characters"
            )
            
            description = st.text_area(
                "📝 Description",
                placeholder="Provide more details about your venture idea...",
                help="Optional: Add more context about your venture"
            )
        
        with col2:
            n_ideas = st.selectbox(
                "🔢 Number of Ideas",
                options=[1, 3, 5, 10],
                index=1,
                help="How many venture ideas to generate"
            )
            
            fast_mode = st.checkbox(
                "⚡ Fast Mode",
                value=True,
                help="Quick generation with optimized settings"
            )
            
            profile = st.selectbox(
                "⚙️ Execution Profile",
                options=["quick", "standard", "deep"],
                index=0,
                help="Depth of analysis and generation"
            )
        
        # Advanced options in expander
        with st.expander("🔧 Advanced Options"):
            col1, col2 = st.columns(2)
            
            with col1:
                seed_icp = st.text_input(
                    "Target ICP",
                    placeholder="e.g., B2B SaaS founders",
                    help="Ideal Customer Profile"
                )
                
                seed_pains = st.text_input(
                    "Pain Points",
                    placeholder="e.g., compliance complexity, cost",
                    help="Key problems to solve"
                )
            
            with col2:
                seed_competitors = st.text_input(
                    "Competitors",
                    placeholder="e.g., Compliance.ai, RegTech",
                    help="Main competitors"
                )
                
                seed_context = st.text_input(
                    "Context",
                    placeholder="e.g., Post-COVID remote work",
                    help="Market context"
                )
        
        # Submit button with loading state
        submitted = st.form_submit_button(
            "🚀 Launch Venture",
            help="Start generating your AI-powered venture"
        )
        
        if submitted:
            if not topic or len(topic.strip()) < 3:
                st.error("❌ Please provide a topic (minimum 3 characters)")
                return
            
            if len(topic) > 200:
                st.error("❌ Topic too long (maximum 200 characters)")
                return
            
            # Create venture
            with st.spinner("🤖 AI agents are working on your venture..."):
                try:
                    run_id = manager.create_run(
                        topic=topic.strip(),
                        n_ideas=n_ideas,
                        fast_mode=fast_mode,
                        execution_profile=profile,
                        seed_inputs=SeedInputs(
                            icp=seed_icp,
                            pains=[p.strip() for p in seed_pains.split(',') if p.strip()] if seed_pains else [],
                            competitors=[c.strip() for c in seed_competitors.split(',') if c.strip()] if seed_competitors else [],
                            context=seed_context,
                            theme=None
                        )
                    )
                    
                    st.success(f"✅ Venture launched successfully! Run ID: {run_id}")
                    st.balloons()
                    
                    # Auto-refresh after 5 seconds
                    time.sleep(2)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Failed to launch venture: {str(e)}")

def render_quality_section():
    """Render quality dashboard section"""
    if st.session_state.get('show_quality', False):
        st.subheader("📈 Quality Dashboard")
        render_quality_dashboard(manager, settings)

def main():
    """Main enhanced UI application"""
    # Initialize session state
    if 'show_quality' not in st.session_state:
        st.session_state.show_quality = False
    
    # Render header
    render_header()
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🧭 Navigation")
        
        page = st.selectbox(
            "Choose a page",
            ["🏠 Dashboard", "🚀 New Venture", "📊 Quality", "⚙️ Settings"]
        )
        
        st.divider()
        
        # System status
        st.subheader("🔧 System Status")
        
        # Ollama status
        try:
            ollama_status = check_ollama()
            if ollama_status:
                st.success("🤖 Ollama: Connected")
            else:
                st.error("🤖 Ollama: Disconnected")
        except:
            st.warning("🤖 Ollama: Unknown")
        
        # Rate limiting status
        if ui_run_limiter:
            st.info("⏱️ Rate Limiter: Active")
        else:
            st.warning("⏱️ Rate Limiter: Inactive")
        
        st.divider()
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        if st.button("📊 Show Quality Dashboard"):
            st.session_state.show_quality = not st.session_state.show_quality
            st.rerun()
        
        if st.button("🔄 Refresh Data"):
            st.rerun()
    
    # Main content area
    if page == "🏠 Dashboard":
        render_metrics_dashboard()
        
        # Quality section if enabled
        if st.session_state.get('show_quality', False):
            render_quality_section()
    
    elif page == "🚀 New Venture":
        render_venture_form()
    
    elif page == "📊 Quality":
        st.session_state.show_quality = True
        render_quality_section()
    
    elif page == "⚙️ Settings":
        st.subheader("⚙️ Settings")
        st.info("Settings panel coming soon...")
    
    # Footer
    st.markdown("""
    <div class="footer">
        <p>🚀 Asmblr v2.0 - AI Venture Factory</p>
        <p style="font-size: 0.875rem; margin-top: 0.5rem;">
            Built with ❤️ using cutting-edge AI technology
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
