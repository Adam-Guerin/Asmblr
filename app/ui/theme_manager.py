"""Theme management for Streamlit UI with light/dark modes and customization."""

from __future__ import annotations
import streamlit as st
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ThemeColors:
    """Color palette for UI theme."""
    primary: str = "#FF6B6B"
    secondary: str = "#4ECDC4"
    accent: str = "#45B7D1"
    background: str = "#FFFFFF"
    surface: str = "#F8F9FA"
    text: str = "#2C3E50"
    text_secondary: str = "#7F8C8D"
    success: str = "#27AE60"
    warning: str = "#F39C12"
    error: str = "#E74C3C"
    border: str = "#E1E8ED"
    
    # Dark mode colors
    dark_background: str = "#1E1E1E"
    dark_surface: str = "#2D2D2D"
    dark_text: str = "#E1E8ED"
    dark_text_secondary: str = "#95A5A6"
    dark_border: str = "#404040"


class ThemeManager:
    """Manages UI themes and styling."""
    
    def __init__(self):
        self.themes = {
            "light": {
                "primaryColor": "#FF6B6B",
                "backgroundColor": "#FFFFFF",
                "secondaryBackgroundColor": "#F8F9FA",
                "textColor": "#2C3E50",
                "font": "sans serif"
            },
            "dark": {
                "primaryColor": "#4ECDC4",
                "backgroundColor": "#1E1E1E",
                "secondaryBackgroundColor": "#2D2D2D",
                "textColor": "#E1E8ED",
                "font": "sans serif"
            },
            "blue": {
                "primaryColor": "#45B7D1",
                "backgroundColor": "#FFFFFF",
                "secondaryBackgroundColor": "#F0F8FF",
                "textColor": "#2C3E50",
                "font": "sans serif"
            },
            "green": {
                "primaryColor": "#27AE60",
                "backgroundColor": "#FFFFFF",
                "secondaryBackgroundColor": "#F0FFF0",
                "textColor": "#2C3E50",
                "font": "sans serif"
            }
        }
        
        self.colors = ThemeColors()
    
    def get_theme_css(self, theme_name: str) -> str:
        """Generate CSS for the selected theme."""
        theme_config = self.themes.get(theme_name, self.themes["light"])
        is_dark = theme_name == "dark"
        
        if is_dark:
            colors = {
                "bg": self.colors.dark_background,
                "surface": self.colors.dark_surface,
                "text": self.colors.dark_text,
                "text_secondary": self.colors.dark_text_secondary,
                "border": self.colors.dark_border,
                "primary": theme_config["primaryColor"],
                "success": self.colors.success,
                "warning": self.colors.warning,
                "error": self.colors.error
            }
        else:
            colors = {
                "bg": theme_config["backgroundColor"],
                "surface": theme_config["secondaryBackgroundColor"],
                "text": theme_config["textColor"],
                "text_secondary": self.colors.text_secondary,
                "border": self.colors.border,
                "primary": theme_config["primaryColor"],
                "success": self.colors.success,
                "warning": self.colors.warning,
                "error": self.colors.error
            }
        
        return f"""
        <style>
            /* Global Styles */
            .stApp {{
                background-color: {colors['bg']};
                color: {colors['text']};
            }}
            
            /* Header Styles */
            .main-header {{
                background: linear-gradient(135deg, {colors['primary']}20, {colors['secondary']}20);
                padding: 2rem 0;
                border-radius: 1rem;
                margin-bottom: 2rem;
                text-align: center;
            }}
            
            /* Status Boxes */
            .status-box {{
                padding: 1rem;
                border-radius: 0.5rem;
                margin: 1rem 0;
                border-left: 4px solid;
                background-color: {colors['surface']};
                color: {colors['text']};
            }}
            
            .success {{ 
                border-left-color: {colors['success']};
                background-color: {colors['success']}20;
            }}
            
            .warning {{ 
                border-left-color: {colors['warning']};
                background-color: {colors['warning']}20;
            }}
            
            .error {{ 
                border-left-color: {colors['error']};
                background-color: {colors['error']}20;
            }}
            
            /* Idea Cards */
            .idea-card {{
                border: 1px solid {colors['border']};
                border-radius: 0.5rem;
                padding: 1rem;
                margin: 0.5rem 0;
                background-color: {colors['surface']};
                transition: all 0.3s ease;
            }}
            
            .idea-card:hover {{
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                transform: translateY(-2px);
            }}
            
            /* Progress Bar */
            .progress-container {{
                background-color: {colors['surface']};
                border-radius: 1rem;
                padding: 1rem;
                margin: 1rem 0;
                border: 1px solid {colors['border']};
            }}
            
            .progress-stage {{
                display: flex;
                align-items: center;
                margin: 0.5rem 0;
                padding: 0.5rem;
                border-radius: 0.25rem;
                background-color: {colors['bg']};
            }}
            
            .progress-stage.active {{
                background-color: {colors['primary']}20;
                border-left: 3px solid {colors['primary']};
            }}
            
            .progress-stage.completed {{
                background-color: {colors['success']}20;
                border-left: 3px solid {colors['success']};
            }}
            
            /* Error Display */
            .error-container {{
                background-color: {colors['surface']};
                border: 1px solid {colors['error']};
                border-radius: 0.5rem;
                padding: 1rem;
                margin: 1rem 0;
            }}
            
            .solution-steps {{
                background-color: {colors['bg']};
                border-radius: 0.25rem;
                padding: 0.5rem;
                margin: 0.5rem 0;
            }}
            
            .solution-steps ol {{
                margin: 0;
                padding-left: 1.5rem;
            }}
            
            .solution-steps li {{
                margin: 0.25rem 0;
                color: {colors['text_secondary']};
            }}
            
            /* Charts Container */
            .chart-container {{
                background-color: {colors['surface']};
                border-radius: 0.5rem;
                padding: 1rem;
                margin: 1rem 0;
                border: 1px solid {colors['border']};
            }}
            
            /* Export Buttons */
            .export-buttons {{
                display: flex;
                gap: 0.5rem;
                margin: 1rem 0;
                flex-wrap: wrap;
            }}
            
            .export-button {{
                padding: 0.5rem 1rem;
                border-radius: 0.25rem;
                border: 1px solid {colors['border']};
                background-color: {colors['surface']};
                color: {colors['text']};
                text-decoration: none;
                transition: all 0.3s ease;
            }}
            
            .export-button:hover {{
                background-color: {colors['primary']};
                color: white;
            }}
            
            /* Sidebar */
            .css-1d391kg {{
                background-color: {colors['surface']};
            }}
            
            /* Metrics Cards */
            .metric-card {{
                background: linear-gradient(135deg, {colors['primary']}10, {colors['secondary']}10);
                border-radius: 0.5rem;
                padding: 1rem;
                margin: 0.5rem 0;
                border: 1px solid {colors['border']};
                text-align: center;
            }}
            
            .metric-value {{
                font-size: 2rem;
                font-weight: bold;
                color: {colors['primary']};
            }}
            
            .metric-label {{
                color: {colors['text_secondary']};
                font-size: 0.9rem;
            }}
            
            /* Animations */
            @keyframes pulse {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.7; }}
                100% {{ opacity: 1; }}
            }}
            
            .loading {{
                animation: pulse 1.5s infinite;
            }}
            
            /* Responsive Design */
            @media (max-width: 768px) {{
                .main-header {{
                    padding: 1rem 0;
                }}
                
                .export-buttons {{
                    flex-direction: column;
                }}
                
                .metric-card {{
                    margin: 0.25rem 0;
                }}
            }}
        </style>
        """
    
    def apply_theme(self, theme_name: str) -> None:
        """Apply the selected theme to the Streamlit app."""
        if theme_name not in self.themes:
            theme_name = "light"
        
        # Apply Streamlit's built-in theme configuration
        theme_config = self.themes[theme_name]
        
        # Inject custom CSS
        css = self.get_theme_css(theme_name)
        st.markdown(css, unsafe_allow_html=True)
    
    def render_theme_selector(self) -> str:
        """Render theme selector in sidebar."""
        st.sidebar.subheader("🎨 Thème")
        
        current_theme = st.session_state.get('theme', 'light')
        
        # Theme selection with preview
        theme_options = {
            "light": "☀️ Clair",
            "dark": "🌙 Sombre", 
            "blue": "💙 Bleu",
            "green": "💚 Vert"
        }
        
        selected_theme = st.sidebar.selectbox(
            "Choisir un thème",
            options=list(theme_options.keys()),
            format_func=lambda x: theme_options[x],
            index=list(theme_options.keys()).index(current_theme)
        )
        
        # Update theme if changed
        if selected_theme != current_theme:
            st.session_state.theme = selected_theme
            st.rerun()
        
        return selected_theme
    
    def get_status_color(self, status: str) -> str:
        """Get color for status indicators."""
        status_colors = {
            "completed": self.colors.success,
            "running": self.colors.primary,
            "failed": self.colors.error,
            "pending": self.colors.text_secondary,
            "warning": self.colors.warning
        }
        return status_colors.get(status.lower(), self.colors.text_secondary)
    
    def render_progress_stage(self, stage_name: str, status: str, message: str = "") -> None:
        """Render a single progress stage."""
        status_class = status.lower()
        icon = {
            "completed": "✅",
            "active": "🔄",
            "failed": "❌",
            "pending": "⏳"
        }.get(status_class, "⏳")
        
        st.markdown(f"""
        <div class="progress-stage {status_class}">
            <span style="margin-right: 0.5rem;">{icon}</span>
            <span style="font-weight: bold;">{stage_name}</span>
            {f'<span style="margin-left: auto; color: {self.colors.text_secondary};">{message}</span>' if message else ''}
        </div>
        """, unsafe_allow_html=True)


# Global theme manager instance
_global_theme_manager = ThemeManager()


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance."""
    return _global_theme_manager


def apply_theme(theme_name: Optional[str] = None) -> None:
    """Apply theme to the current app."""
    if theme_name is None:
        theme_name = st.session_state.get('theme', 'light')
    
    _global_theme_manager.apply_theme(theme_name)
