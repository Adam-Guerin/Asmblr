"""
Comprehensive UI components system for Asmblr
Provides reusable UI components with consistent styling and error handling
"""

from __future__ import annotations
import streamlit as st
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from pathlib import Path
import time

from app.core.error_formatter import format_runtime_error, ErrorSeverity
from app.core.logging_system import get_logger
from app.ui.theme_manager import get_theme_manager


@dataclass
class UIComponentConfig:
    """Configuration for UI components"""
    show_help: bool = True
    show_validation: bool = True
    show_loading: bool = True
    auto_validate: bool = True
    theme_aware: bool = True


class UIComponents:
    """Comprehensive UI components library with error handling."""
    
    def __init__(self, config: Optional[UIComponentConfig] = None):
        self.config = config or UIComponentConfig()
        self.logger = get_logger()
        self.theme_manager = get_theme_manager()
    
    def status_card(
        self,
        title: str,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        actions: Optional[List[Dict[str, str]]] = None
    ) -> None:
        """Render a status card with consistent styling."""
        try:
            # Get status color from theme manager
            color = self.theme_manager.get_status_color(status)
            
            # Create status indicator
            status_icons = {
                "completed": "✅",
                "running": "🔄",
                "failed": "❌",
                "pending": "⏳",
                "warning": "⚠️"
            }
            icon = status_icons.get(status.lower(), "📝")
            
            # Render card
            with st.container():
                st.markdown(f"""
                <div class="status-box {status.lower()}" style="
                    border-left: 4px solid {color};
                    padding: 1rem;
                    margin: 0.5rem 0;
                    background-color: var(--surface-color);
                    border-radius: 0.5rem;
                ">
                    <h4 style="margin: 0 0 0.5rem 0; color: {color};">
                        {icon} {title}
                    </h4>
                    <p style="margin: 0 0 1rem 0;">{message}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Show details if provided
                if details:
                    with st.expander("📋 Détails"):
                        for key, value in details.items():
                            st.write(f"**{key}:** {value}")
                
                # Show actions if provided
                if actions:
                    cols = st.columns(len(actions))
                    for i, action in enumerate(actions):
                        with cols[i]:
                            if st.button(action.get("label", f"Action {i+1}"), key=f"action_{i}_{title}"):
                                # Handle action (would need callback system)
                                st.info(f"Action '{action.get('label')}' triggered")
        
        except Exception as e:
            self.logger.error("Failed to render status card", e)
            st.error("Failed to display status card")
    
    def progress_indicator(
        self,
        steps: List[str],
        current_step: int,
        show_descriptions: bool = True
    ) -> None:
        """Render a progress indicator with steps."""
        try:
            st.markdown("### 📋 Progression")
            
            for i, step in enumerate(steps):
                # Determine step status
                if i < current_step:
                    status = "completed"
                    icon = "✅"
                elif i == current_step:
                    status = "active"
                    icon = "🔄"
                else:
                    status = "pending"
                    icon = "⏳"
                
                # Get color based on status
                color = self.theme_manager.get_status_color(status)
                
                # Render step
                st.markdown(f"""
                <div class="progress-stage {status}" style="
                    padding: 0.75rem;
                    margin: 0.25rem 0;
                    border-radius: 0.25rem;
                    background-color: var(--surface-color);
                    border-left: 3px solid {color};
                ">
                    <span style="margin-right: 0.5rem;">{icon}</span>
                    <span style="font-weight: bold;">{step}</span>
                </div>
                """, unsafe_allow_html=True)
        
        except Exception as e:
            self.logger.error("Failed to render progress indicator", e)
            st.error("Failed to display progress")
    
    def metric_card(
        self,
        title: str,
        value: Union[str, int, float],
        delta: Optional[Union[str, int, float]] = None,
        help_text: Optional[str] = None,
        color: Optional[str] = None
    ) -> None:
        """Render a styled metric card."""
        try:
            # Format value
            if isinstance(value, (int, float)):
                if value >= 1000000:
                    formatted_value = f"{value/1000000:.1f}M"
                elif value >= 1000:
                    formatted_value = f"{value/1000:.1f}K"
                else:
                    formatted_value = f"{value:.1f}"
            else:
                formatted_value = str(value)
            
            # Format delta
            delta_str = None
            if delta is not None:
                delta_prefix = "📈" if delta > 0 else "📉" if delta < 0 else "➡️"
                delta_str = f"{delta_prefix} {abs(delta):.1f}"
            
            # Render metric
            with st.container():
                st.markdown(f"""
                <div class="metric-card" style="
                    background: linear-gradient(135deg, var(--primary-color)10, var(--secondary-color)10);
                    border-radius: 0.5rem;
                    padding: 1rem;
                    margin: 0.5rem 0;
                    border: 1px solid var(--border-color);
                    text-align: center;
                ">
                    <div style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 0.5rem;">
                        {title}
                    </div>
                    <div style="font-size: 2rem; font-weight: bold; color: {color or 'var(--primary-color)'};">
                        {formatted_value}
                    </div>
                    {f'<div style="color: var(--text-secondary); font-size: 0.8rem;">{delta_str}</div>' if delta_str else ''}
                </div>
                """, unsafe_allow_html=True)
                
                if help_text:
                    st.caption(help_text)
        
        except Exception as e:
            self.logger.error("Failed to render metric card", e)
            st.error("Failed to display metric")
    
    def info_panel(
        self,
        title: str,
        content: Union[str, List[str]],
        icon: str = "ℹ️",
        expandable: bool = False
    ) -> None:
        """Render an information panel."""
        try:
            if isinstance(content, str):
                content_lines = [content]
            else:
                content_lines = content
            
            if expandable:
                with st.expander(f"{icon} {title}"):
                    for line in content_lines:
                        st.write(line)
            else:
                st.markdown(f"""
                <div style="
                    background-color: var(--surface-color);
                    border-left: 4px solid var(--primary-color);
                    padding: 1rem;
                    margin: 1rem 0;
                    border-radius: 0.5rem;
                ">
                    <h4 style="margin: 0 0 0.5rem 0;">{icon} {title}</h4>
                    {''.join(f'<p style="margin: 0.25rem 0;">{line}</p>' for line in content_lines)}
                </div>
                """, unsafe_allow_html=True)
        
        except Exception as e:
            self.logger.error("Failed to render info panel", e)
            st.error("Failed to display information")
    
    def action_buttons(
        self,
        actions: List[Dict[str, Any]],
        layout: str = "horizontal"
    ) -> None:
        """Render action buttons with consistent styling."""
        try:
            if layout == "horizontal":
                cols = st.columns(len(actions))
                for i, action in enumerate(actions):
                    with cols[i]:
                        self._render_action_button(action, f"action_{i}")
            else:
                for i, action in enumerate(actions):
                    self._render_action_button(action, f"action_{i}")
        
        except Exception as e:
            self.logger.error("Failed to render action buttons", e)
            st.error("Failed to display actions")
    
    def _render_action_button(self, action: Dict[str, Any], key: str) -> None:
        """Render a single action button."""
        button_type = action.get("type", "primary")
        label = action.get("label", "Action")
        disabled = action.get("disabled", False)
        
        # Style based on type
        button_styles = {
            "primary": "background-color: var(--primary-color); color: white;",
            "secondary": "background-color: var(--secondary-color); color: white;",
            "danger": "background-color: var(--error-color); color: white;",
            "success": "background-color: var(--success-color); color: white;"
        }
        
        style = button_styles.get(button_type, button_styles["primary"])
        
        if st.button(label, key=key, disabled=disabled):
            # Handle action callback
            callback = action.get("callback")
            if callback and callable(callback):
                callback()
            else:
                st.info(f"Action '{label}' triggered")
    
    def file_uploader(
        self,
        label: str,
        file_types: List[str],
        help_text: Optional[str] = None,
        max_size_mb: int = 10
    ) -> Optional[bytes]:
        """Render a file uploader with validation."""
        try:
            # Create file type description
            file_type_desc = ", ".join(file_types)
            
            # Help text
            help_content = f"Formats supportés: {file_type_desc}"
            if help_text:
                help_content += f"\n{help_text}"
            help_content += f"\nTaille maximale: {max_size_mb}MB"
            
            # File uploader
            uploaded_file = st.file_uploader(
                label=label,
                type=file_types,
                help=help_content,
                key=f"uploader_{label}"
            )
            
            if uploaded_file is not None:
                # Check file size
                file_size_mb = uploaded_file.size / (1024 * 1024)
                if file_size_mb > max_size_mb:
                    st.error(f"Le fichier est trop volumineux ({file_size_mb:.1f}MB > {max_size_mb}MB)")
                    return None
                
                # Read file content
                try:
                    content = uploaded_file.read()
                    st.success(f"Fichier '{uploaded_file.name}' chargé avec succès ({file_size_mb:.1f}MB)")
                    return content
                except Exception as e:
                    self.logger.error("Failed to read uploaded file", e)
                    st.error("Erreur lors de la lecture du fichier")
                    return None
            
            return None
        
        except Exception as e:
            self.logger.error("Failed to render file uploader", e)
            st.error("Erreur lors du chargement du fichier")
            return None
    
    def data_table(
        self,
        data: List[Dict[str, Any]],
        title: Optional[str] = None,
        show_index: bool = False,
        height: Optional[int] = None
    ) -> None:
        """Render a data table with styling."""
        try:
            if not data:
                st.info("Aucune donnée à afficher")
                return
            
            if title:
                st.subheader(title)
            
            # Convert to DataFrame for better display
            import pandas as pd
            df = pd.DataFrame(data)
            
            # Display table
            st.dataframe(df, use_container_width=True, hide_index=not show_index, height=height)
            
            # Show summary statistics
            if len(data) > 1:
                with st.expander("📊 Statistiques"):
                    st.write(f"**Nombre d'entrées:** {len(data)}")
                    st.write(f"**Colonnes:** {', '.join(df.columns)}")
                    
                    # Numeric columns statistics
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    if len(numeric_cols) > 0:
                        st.write("**Statistiques numériques:**")
                        st.write(df[numeric_cols].describe())
        
        except Exception as e:
            self.logger.error("Failed to render data table", e)
            st.error("Erreur lors de l'affichage des données")
    
    def form_section(
        self,
        title: str,
        fields: List[Dict[str, Any]],
        submit_label: str = "Soumettre",
        on_submit: Optional[Callable] = None
    ) -> bool:
        """Render a form section with validation."""
        try:
            with st.form(key=f"form_{title}"):
                st.subheader(title)
                
                form_data = {}
                
                # Render fields
                for field in fields:
                    field_type = field.get("type", "text")
                    field_name = field.get("name", "")
                    field_label = field.get("label", field_name)
                    field_default = field.get("default", "")
                    field_help = field.get("help", "")
                    field_required = field.get("required", False)
                    
                    # Render based on type
                    if field_type == "text":
                        value = st.text_input(
                            label=field_label,
                            value=field_default,
                            help=field_help,
                            key=f"field_{field_name}"
                        )
                    elif field_type == "number":
                        value = st.number_input(
                            label=field_label,
                            value=field_default,
                            help=field_help,
                            key=f"field_{field_name}"
                        )
                    elif field_type == "select":
                        value = st.selectbox(
                            label=field_label,
                            options=field.get("options", []),
                            index=field.get("default_index", 0),
                            help=field_help,
                            key=f"field_{field_name}"
                        )
                    elif field_type == "textarea":
                        value = st.text_area(
                            label=field_label,
                            value=field_default,
                            help=field_help,
                            key=f"field_{field_name}"
                        )
                    elif field_type == "checkbox":
                        value = st.checkbox(
                            label=field_label,
                            value=field_default,
                            help=field_help,
                            key=f"field_{field_name}"
                        )
                    else:
                        value = st.text_input(
                            label=field_label,
                            value=field_default,
                            help=field_help,
                            key=f"field_{field_name}"
                        )
                    
                    # Validation
                    if field_required and not value:
                        st.error(f"Le champ '{field_label}' est requis")
                        return False
                    
                    form_data[field_name] = value
                
                # Submit button
                submitted = st.form_submit_button(submit_label)
                
                if submitted and on_submit:
                    on_submit(form_data)
                
                return submitted
        
        except Exception as e:
            self.logger.error("Failed to render form section", e)
            st.error("Erreur lors de l'affichage du formulaire")
            return False
    
    def loading_overlay(self, message: str = "Chargement...") -> None:
        """Render a loading overlay."""
        try:
            with st.spinner(message):
                time.sleep(0.1)  # Small delay to ensure spinner is visible
        except Exception as e:
            self.logger.error("Failed to render loading overlay", e)


# Global UI components instance
_ui_components: Optional[UIComponents] = None


def get_ui_components(config: Optional[UIComponentConfig] = None) -> UIComponents:
    """Get the global UI components instance."""
    global _ui_components
    if _ui_components is None:
        _ui_components = UIComponents(config)
    return _ui_components


# Convenience functions for common components
def status_card(title: str, status: str, message: str, **kwargs) -> None:
    """Render a status card."""
    get_ui_components().status_card(title, status, message, **kwargs)


def progress_indicator(steps: List[str], current_step: int, **kwargs) -> None:
    """Render a progress indicator."""
    get_ui_components().progress_indicator(steps, current_step, **kwargs)


def metric_card(title: str, value: Union[str, int, float], **kwargs) -> None:
    """Render a metric card."""
    get_ui_components().metric_card(title, value, **kwargs)


def info_panel(title: str, content: Union[str, List[str]], **kwargs) -> None:
    """Render an information panel."""
    get_ui_components().info_panel(title, content, **kwargs)


def action_buttons(actions: List[Dict[str, Any]], **kwargs) -> None:
    """Render action buttons."""
    get_ui_components().action_buttons(actions, **kwargs)


def file_uploader(label: str, file_types: List[str], **kwargs) -> Optional[bytes]:
    """Render a file uploader."""
    return get_ui_components().file_uploader(label, file_types, **kwargs)


def data_table(data: List[Dict[str, Any]], **kwargs) -> None:
    """Render a data table."""
    get_ui_components().data_table(data, **kwargs)


def form_section(title: str, fields: List[Dict[str, Any]], **kwargs) -> bool:
    """Render a form section."""
    return get_ui_components().form_section(title, fields, **kwargs)
