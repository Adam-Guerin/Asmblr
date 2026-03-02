"""Interactive charts and visualizations for Asmblr results."""

from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Any


class ChartManager:
    """Manages interactive charts and visualizations."""
    
    def __init__(self):
        self.color_palette = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#27AE60", 
            "#F39C12", "#E74C3C", "#9B59B6", "#3498DB"
        ]
    
    def create_idea_scoring_chart(self, ideas_data: list[dict[str, Any]]) -> go.Figure:
        """Create an interactive idea scoring chart."""
        if not ideas_data:
            return self._empty_chart("Aucune idée à afficher")
        
        df = pd.DataFrame(ideas_data)
        
        fig = go.Figure()
        
        # Add bars for scores
        fig.add_trace(go.Bar(
            x=df['name'],
            y=df['score'],
            marker_color=self.color_palette[0],
            text=df['score'],
            texttemplate='%{y:.1f}',
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Score: %{y:.1f}<extra></extra>'
        ))
        
        fig.update_layout(
            title="📊 Scores des Idées",
            xaxis_title="Idées",
            yaxis_title="Score",
            height=400,
            showlegend=False,
            margin=dict(l=20, r=20, t=40, b=80)
        )
        
        # Rotate x-axis labels for better readability
        fig.update_xaxes(tickangle=45)
        
        return fig
    
    def create_confidence_gauge(self, confidence_score: float) -> go.Figure:
        """Create a confidence score gauge chart."""
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = confidence_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Score de Confiance"},
            delta = {'reference': 70},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': self.color_palette[0]},
                'steps': [
                    {'range': [0, 30], 'color': "lightgray"},
                    {'range': [30, 70], 'color': "lightyellow"},
                    {'range': [70, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
    
    def create_pipeline_timeline(self, stages_data: list[dict[str, Any]]) -> go.Figure:
        """Create a pipeline execution timeline."""
        if not stages_data:
            return self._empty_chart("Aucune donnée de timeline")
        
        df = pd.DataFrame(stages_data)
        
        fig = go.Figure()
        
        # Add timeline bars
        for i, stage in enumerate(df.iterrows()):
            _, row = stage
            fig.add_trace(go.Scatter(
                x=[row['start_time'], row['end_time']],
                y=[row['stage'], row['stage']],
                mode='lines+markers',
                line=dict(color=self.color_palette[i % len(self.color_palette)], width=3),
                marker=dict(size=8),
                name=row['stage'],
                hovertemplate=f"<b>{row['stage']}</b><br>Durée: {row['duration']:.2f}s<extra></extra>"
            ))
        
        fig.update_layout(
            title="⏱️ Timeline d'Exécution",
            xaxis_title="Temps",
            yaxis_title="Étapes",
            height=max(300, len(stages_data) * 50),
            showlegend=True,
            margin=dict(l=100, r=20, t=40, b=40)
        )
        
        return fig
    
    def create_market_signals_chart(self, signals_data: dict[str, Any]) -> go.Figure:
        """Create market signals visualization."""
        if not signals_data:
            return self._empty_chart("Aucun signal de marché")
        
        categories = list(signals_data.keys())
        values = list(signals_data.values())
        
        fig = go.Figure(data=[
            go.Bar(
                x=categories,
                y=values,
                marker_color=self.color_palette[:len(categories)],
                text=values,
                texttemplate='%{y}',
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Valeur: %{y}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title="📈 Signaux de Marché",
            xaxis_title="Catégories",
            yaxis_title="Valeur",
            height=400,
            showlegend=False,
            margin=dict(l=20, r=20, t=40, b=80)
        )
        
        fig.update_xaxes(tickangle=45)
        
        return fig
    
    def create_risk_assessment_radar(self, risk_data: dict[str, float]) -> go.Figure:
        """Create a risk assessment radar chart."""
        if not risk_data:
            return self._empty_chart("Aucune donnée de risque")
        
        categories = list(risk_data.keys())
        values = list(risk_data.values())
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Évaluation des Risques',
            line_color=self.color_palette[0],
            fillcolor=f'{self.color_palette[0]}40'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )
            ),
            title="🎯 Évaluation des Risques",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
    
    def create_competitor_analysis(self, competitors_data: list[dict[str, Any]]) -> go.Figure:
        """Create competitor analysis chart."""
        if not competitors_data:
            return self._empty_chart("Aucune donnée concurrentielle")
        
        df = pd.DataFrame(competitors_data)
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Score Global', 'Caractéristiques'),
            specs=[[{"type": "bar"}, {"type": "scatter"}]]
        )
        
        # Overall scores
        fig.add_trace(
            go.Bar(
                x=df['name'],
                y=df['overall_score'],
                marker_color=self.color_palette[0],
                name='Score Global'
            ),
            row=1, col=1
        )
        
        # Features comparison (if available)
        if 'features' in df.columns:
            for i, competitor in enumerate(df.iterrows()):
                _, row = competitor
                if isinstance(row['features'], dict):
                    features = list(row['features'].keys())
                    scores = list(row['features'].values())
                    
                    fig.add_trace(
                        go.Scatter(
                            x=features,
                            y=scores,
                            mode='markers+lines',
                            name=row['name'],
                            line=dict(color=self.color_palette[i % len(self.color_palette)])
                        ),
                        row=1, col=2
                    )
        
        fig.update_layout(
            title="🏢 Analyse Concurrentielle",
            height=400,
            showlegend=True,
            margin=dict(l=20, r=20, t=40, b=40)
        )
        
        return fig
    
    def create_execution_metrics(self, metrics_data: dict[str, Any]) -> go.Figure:
        """Create execution metrics dashboard."""
        if not metrics_data:
            return self._empty_chart("Aucune métrique d'exécution")
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Temps d\'Exécution', 'Utilisation Mémoire', 'Taux de Succès', 'Tokens Consommés'),
            specs=[[{"type": "bar"}, {"type": "scatter"}],
                   [{"type": "pie"}, {"type": "bar"}]]
        )
        
        # Execution time
        if 'execution_time' in metrics_data:
            fig.add_trace(
                go.Bar(
                    x=['Temps Total'],
                    y=[metrics_data['execution_time']],
                    marker_color=self.color_palette[0],
                    name='Temps (s)'
                ),
                row=1, col=1
            )
        
        # Memory usage
        if 'memory_usage' in metrics_data:
            memory_data = metrics_data['memory_usage']
            if isinstance(memory_data, dict):
                fig.add_trace(
                    go.Scatter(
                        x=list(memory_data.keys()),
                        y=list(memory_data.values()),
                        mode='lines+markers',
                        line=dict(color=self.color_palette[1]),
                        name='Mémoire (MB)'
                    ),
                    row=1, col=2
                )
        
        # Success rate
        if 'success_rate' in metrics_data:
            success_data = metrics_data['success_rate']
            fig.add_trace(
                go.Pie(
                    labels=['Succès', 'Échec'],
                    values=[success_data, 100 - success_data],
                    marker_colors=[self.color_palette[2], self.color_palette[3]],
                    name='Taux de Succès'
                ),
                row=2, col=1
            )
        
        # Token consumption
        if 'token_consumption' in metrics_data:
            token_data = metrics_data['token_consumption']
            if isinstance(token_data, dict):
                fig.add_trace(
                    go.Bar(
                        x=list(token_data.keys()),
                        y=list(token_data.values()),
                        marker_color=self.color_palette[4],
                        name='Tokens'
                    ),
                    row=2, col=2
                )
        
        fig.update_layout(
            title="📊 Métriques d'Exécution",
            height=600,
            showlegend=False,
            margin=dict(l=20, r=20, t=40, b=40)
        )
        
        return fig
    
    def _empty_chart(self, message: str) -> go.Figure:
        """Create an empty chart with message."""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig
    
    def render_chart(self, fig: go.Figure, use_container_width: bool = True) -> None:
        """Render a chart in Streamlit."""
        st.plotly_chart(fig, use_container_width=use_container_width)
    
    def create_metrics_summary(self, metrics: dict[str, Any]) -> dict[str, Any]:
        """Create a metrics summary for display."""
        return {
            "total_ideas": metrics.get("total_ideas", 0),
            "avg_score": metrics.get("avg_score", 0),
            "confidence": metrics.get("confidence", 0),
            "execution_time": metrics.get("execution_time", 0),
            "success_rate": metrics.get("success_rate", 0),
            "tokens_used": metrics.get("tokens_used", 0)
        }


# Global chart manager instance
_global_chart_manager = ChartManager()


def get_chart_manager() -> ChartManager:
    """Get the global chart manager instance."""
    return _global_chart_manager
