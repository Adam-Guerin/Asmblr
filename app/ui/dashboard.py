"""Dashboard UI for product metrics with enhanced error handling."""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any

import streamlit as st

from app.core.error_formatter import format_runtime_error, ErrorSeverity
from app.core.logging_system import get_logger


class DashboardManager:
    """Manages dashboard functionality with enhanced error handling."""
    
    def __init__(self) -> None:
        self.logger = get_logger()
        self.product_metrics = None
        self._initialize_metrics()
    
    def _initialize_metrics(self) -> None:
        """Initialize product metrics with error handling."""
        try:
            from app.core.product_metrics import PRODUCT_METRICS
            self.product_metrics = PRODUCT_METRICS
        except ImportError as e:
            self.logger.error("Failed to import product metrics", e)
            self.product_metrics = None
    
    def render_dashboard(self) -> None:
        """Render the product metrics dashboard with error handling."""
        try:
            if self.product_metrics is None:
                st.error("📊 Product metrics not available")
                st.info("Please ensure the product metrics system is initialized")
                return
            
            st.title("📊 Tableau de Bord Produit")
            
            # Get metrics for last 30 days with error handling
            try:
                metrics = self.product_metrics.get_dashboard_metrics(days=30)
                if not metrics:
                    st.warning("No metrics data available for the selected period")
                    return
            except Exception as e:
                self.logger.error("Failed to get dashboard metrics", e)
                st.error("Failed to load metrics data")
                return
            
            # Validate metrics data
            validated_metrics = self._validate_metrics(metrics)
            
            # Display KPIs in columns
            self._render_kpi_section(validated_metrics)
            
            # Add visualizations
            st.markdown("---")
            self._render_visualizations(validated_metrics)
            
        except Exception as e:
            self.logger.error("Dashboard rendering failed", e)
            st.error("Failed to render dashboard")
    
    def _validate_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize metrics data."""
        validated = {}
        
        # Define expected metrics with default values
        expected_metrics = {
            'mvp_published_pct': 0,
            'avg_idea_to_landing_days': 0,
            'runs_with_feedback_pct': 0,
            'runs_with_iterations_pct': 0,
            'runs_count': 0,
            'last_updated': 'Unknown'
        }
        
        for key, default_value in expected_metrics.items():
            value = metrics.get(key, default_value)
            
            # Validate numeric values
            if key.endswith('_pct'):
                validated[key] = max(0, min(100, float(value)))
            elif key == 'avg_idea_to_landing_days':
                validated[key] = max(0, float(value))
            elif key == 'runs_count':
                validated[key] = max(0, int(value))
            else:
                validated[key] = str(value)
        
        return validated
    
    def _render_kpi_section(self, metrics: Dict[str, Any]) -> None:
        """Render KPI metrics section."""
        try:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="% MVP Publiés",
                    value=f"{metrics['mvp_published_pct']:.1f}%",
                    help="Pourcentage de runs ayant abouti à un MVP publié"
                )
            
            with col2:
                st.metric(
                    label="Temps Moyen Idée → Landing",
                    value=f"{metrics['avg_idea_to_landing_days']:.1f}j",
                    help="Délai moyen entre la génération d'une idée et la création d'une landing page"
                )
            
            with col3:
                st.metric(
                    label="% Runs avec Feedback",
                    value=f"{metrics['runs_with_feedback_pct']:.1f}%",
                    help="Pourcentage de runs ayant reçu du feedback utilisateur"
                )
            
            with col4:
                st.metric(
                    label="% Runs Itérés",
                    value=f"{metrics['runs_with_iterations_pct']:.1f}%",
                    help="Pourcentage de runs ayant été itérés suite à du feedback"
                )
        except Exception as e:
            self.logger.error("Failed to render KPI section", e)
            st.error("Failed to display KPI metrics")
    
    def _render_visualizations(self, metrics: Dict[str, Any]) -> None:
        """Render visualization section."""
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Évolution des KPIs")
                # Create time series chart with validated data
                chart_data = {
                    'MVP Publiés (%)': [0, metrics['mvp_published_pct']],
                    'Avec Feedback (%)': [0, metrics['runs_with_feedback_pct']],
                    'Itérés (%)': [0, metrics['runs_with_iterations_pct']]
                }
                st.line_chart(chart_data, use_container_width=True)
            
            with col2:
                st.subheader("Répartition des Runs")
                # Create pie chart with validated data
                if metrics['runs_count'] > 0:
                    data = {
                        'MVP Publiés': metrics['mvp_published_pct'],
                        'En Cours': 100 - metrics['mvp_published_pct']
                    }
                    st.bar_chart(data)
                else:
                    st.info("Aucune donnée disponible")
            
            # Last updated
            st.caption(f"Dernière mise à jour: {metrics['last_updated']}")
            
        except Exception as e:
            self.logger.error("Failed to render visualizations", e)
            st.error("Failed to display visualizations")


def show_dashboard() -> None:
    """Render the product metrics dashboard."""
    try:
        manager = get_dashboard_manager()
        manager.render_dashboard()
    except Exception as e:
        st.error("Failed to show dashboard")
        get_logger().error("Dashboard display failed", e)


# Create global instance with proper initialization
_dashboard_manager: Optional[DashboardManager] = None


def get_dashboard_manager() -> DashboardManager:
    """Get the global dashboard manager instance."""
    global _dashboard_manager
    if _dashboard_manager is None:
        _dashboard_manager = DashboardManager()
    return _dashboard_manager


def init_dashboard(data_dir: Optional[Path] = None) -> None:
    """Initialize the dashboard with data directory."""
    try:
        if data_dir is None:
            data_dir = Path("data")
        
        # Ensure data directory exists
        data_dir.mkdir(exist_ok=True)
        
        from app.core.product_metrics import init_product_metrics
        init_product_metrics(data_dir)
        
        get_logger().info(f"Dashboard initialized with data directory: {data_dir}")
        
    except ImportError as e:
        get_logger().error("Product metrics module not available", e)
        st.warning("Product metrics system not available")
    except Exception as e:
        get_logger().error("Dashboard initialization failed", e)
        st.error("Failed to initialize dashboard")


def get_dashboard_health() -> Dict[str, Any]:
    """Get dashboard health status."""
    try:
        manager = get_dashboard_manager()
        return {
            "status": "healthy" if manager.product_metrics else "degraded",
            "metrics_available": manager.product_metrics is not None,
            "last_check": "now"
        }
    except Exception as e:
        get_logger().error("Health check failed", e)
        return {
            "status": "error",
            "metrics_available": False,
            "last_check": "now",
            "error": str(e)
        }
