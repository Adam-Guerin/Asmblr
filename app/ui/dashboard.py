"""Dashboard UI for product metrics."""
from pathlib import Path

import streamlit as st
from app.core.product_metrics import PRODUCT_METRICS

def show_dashboard():
    """Render the product metrics dashboard."""
    if PRODUCT_METRICS is None:
        st.error("Product metrics not initialized")
        return
    
    st.title("📊 Tableau de Bord Produit")
    
    # Get metrics for last 30 days
    metrics = PRODUCT_METRICS.get_dashboard_metrics(days=30)
    
    # Display KPIs in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="% MVP Publiés",
            value=f"{metrics['mvp_published_pct']}%",
            help="Pourcentage de runs ayant abouti à un MVP publié"
        )
    
    with col2:
        st.metric(
            label="Temps Moyen Idée → Landing",
            value=f"{metrics['avg_idea_to_landing_days']}j",
            help="Délai moyen entre la génération d'une idée et la création d'une landing page"
        )
    
    with col3:
        st.metric(
            label="% Runs avec Feedback",
            value=f"{metrics['runs_with_feedback_pct']}%",
            help="Pourcentage de runs ayant reçu du feedback utilisateur"
        )
    
    with col4:
        st.metric(
            label="% Runs Itérés",
            value=f"{metrics['runs_with_iterations_pct']}%",
            help="Pourcentage de runs ayant été itérés suite à du feedback"
        )
    
    # Add some visualizations
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Évolution des KPIs")
        # Placeholder for time series chart
        st.line_chart({
            'MVP Publiés (%)': [0, metrics['mvp_published_pct']],
            'Avec Feedback (%)': [0, metrics['runs_with_feedback_pct']],
            'Itérés (%)': [0, metrics['runs_with_iterations_pct']]
        }, use_container_width=True)
    
    with col2:
        st.subheader("Répartition des Runs")
        # Placeholder for pie chart
        if metrics['runs_count'] > 0:
            data = {
                'MVP Publiés': metrics['mvp_published_pct'],
                'En Cours': 100 - metrics['mvp_published_pct']
            }
            st.bar_chart(data)
    
    # Last updated
    st.caption(f"Dernière mise à jour: {metrics['last_updated']}")

def init_dashboard(data_dir: Path | None = None) -> None:
    """Initialize the dashboard with data directory."""
    if data_dir is None:
        data_dir = Path("data")
    
    from app.core.product_metrics import init_product_metrics
    init_product_metrics(data_dir)
