"""Interactive charts and visualizations for Asmblr results."""

from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

from app.core.error_formatter import format_runtime_error, ErrorSeverity


@dataclass
class ChartData:
    """Structured data for chart creation"""
    labels: List[str]
    values: List[Union[int, float]]
    metadata: Optional[Dict[str, Any]] = None


class ChartManager:
    """Manages interactive charts and visualizations with enhanced error handling."""
    
    def __init__(self) -> None:
        self.color_palette: List[str] = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#27AE60", 
            "#F39C12", "#E74C3C", "#9B59B6", "#3498DB"
        ]
        self.default_height: int = 400
        self.default_margin: Dict[str, int] = {"l": 20, "r": 20, "t": 40, "b": 40}
    
    def create_idea_scoring_chart(self, ideas_data: List[Dict[str, Any]]) -> go.Figure:
        """Create an interactive idea scoring chart with validation."""
        if not ideas_data:
            return self._empty_chart("Aucune idée à afficher")
        
        try:
            # Validate data structure
            validated_data = self._validate_ideas_data(ideas_data)
            df = pd.DataFrame(validated_data)
            
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
                height=self.default_height,
                showlegend=False,
                margin=dict(l=20, r=20, t=40, b=80)
            )
            
            # Rotate x-axis labels for better readability
            fig.update_xaxes(tickangle=45)
            
            return fig
            
        except Exception as e:
            st.error(format_runtime_error(f"Failed to create idea scoring chart: {e}", ErrorSeverity.MEDIUM))
            return self._empty_chart("Erreur lors de la création du graphique")
    
    def create_confidence_gauge(self, confidence_score: float) -> go.Figure:
        """Create a confidence score gauge chart with validation."""
        try:
            # Validate confidence score
            if not isinstance(confidence_score, (int, float)):
                raise ValueError("Confidence score must be a number")
            if not 0 <= confidence_score <= 100:
                raise ValueError("Confidence score must be between 0 and 100")
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=confidence_score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Score de Confiance"},
                delta={'reference': 70},
                gauge={
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
            
        except Exception as e:
            st.error(format_runtime_error(f"Failed to create confidence gauge: {e}", ErrorSeverity.MEDIUM))
            return self._empty_chart("Erreur lors de la création du graphique")
    
    def create_pipeline_timeline(self, stages_data: List[Dict[str, Any]]) -> go.Figure:
        """Create a pipeline execution timeline with validation."""
        if not stages_data:
            return self._empty_chart("Aucune donnée de timeline")
        
        try:
            # Validate timeline data
            validated_data = self._validate_timeline_data(stages_data)
            df = pd.DataFrame(validated_data)
            
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
            
        except Exception as e:
            st.error(format_runtime_error(f"Failed to create pipeline timeline: {e}", ErrorSeverity.MEDIUM))
            return self._empty_chart("Erreur lors de la création du graphique")
    
    def create_market_signals_chart(self, signals_data: Dict[str, Any]) -> go.Figure:
        """Create market signals visualization with validation."""
        if not signals_data:
            return self._empty_chart("Aucun signal de marché")
        
        try:
            # Validate signals data
            validated_data = self._validate_signals_data(signals_data)
            categories = list(validated_data.keys())
            values = list(validated_data.values())
            
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
                height=self.default_height,
                showlegend=False,
                margin=dict(l=20, r=20, t=40, b=80)
            )
            
            fig.update_xaxes(tickangle=45)
            
            return fig
            
        except Exception as e:
            st.error(format_runtime_error(f"Failed to create market signals chart: {e}", ErrorSeverity.MEDIUM))
            return self._empty_chart("Erreur lors de la création du graphique")
    
    def create_risk_assessment_radar(self, risk_data: Dict[str, float]) -> go.Figure:
        """Create a risk assessment radar chart with validation."""
        if not risk_data:
            return self._empty_chart("Aucune donnée de risque")
        
        try:
            # Validate risk data
            validated_data = self._validate_risk_data(risk_data)
            categories = list(validated_data.keys())
            values = list(validated_data.values())
            
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
                height=self.default_height,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            return fig
            
        except Exception as e:
            st.error(format_runtime_error(f"Failed to create risk assessment radar: {e}", ErrorSeverity.MEDIUM))
            return self._empty_chart("Erreur lors de la création du graphique")
    
    def create_competitor_analysis(self, competitors_data: List[Dict[str, Any]]) -> go.Figure:
        """Create competitor analysis chart with validation."""
        if not competitors_data:
            return self._empty_chart("Aucune donnée concurrentielle")
        
        try:
            # Validate competitor data
            validated_data = self._validate_competitor_data(competitors_data)
            df = pd.DataFrame(validated_data)
            
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
                height=self.default_height,
                showlegend=True,
                margin=dict(l=20, r=20, t=40, b=40)
            )
            
            return fig
            
        except Exception as e:
            st.error(format_runtime_error(f"Failed to create competitor analysis: {e}", ErrorSeverity.MEDIUM))
            return self._empty_chart("Erreur lors de la création du graphique")
    
    def create_execution_metrics(self, metrics_data: Dict[str, Any]) -> go.Figure:
        """Create execution metrics dashboard with validation."""
        if not metrics_data:
            return self._empty_chart("Aucune métrique d'exécution")
        
        try:
            # Validate metrics data
            validated_data = self._validate_metrics_data(metrics_data)
            
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Temps d\'Exécution', 'Utilisation Mémoire', 'Taux de Succès', 'Tokens Consommés'),
                specs=[[{"type": "bar"}, {"type": "scatter"}],
                       [{"type": "pie"}, {"type": "bar"}]]
            )
            
            # Execution time
            if 'execution_time' in validated_data:
                fig.add_trace(
                    go.Bar(
                        x=['Temps Total'],
                        y=[validated_data['execution_time']],
                        marker_color=self.color_palette[0],
                        name='Temps (s)'
                    ),
                    row=1, col=1
                )
            
            # Memory usage
            if 'memory_usage' in validated_data:
                memory_data = validated_data['memory_usage']
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
            if 'success_rate' in validated_data:
                success_data = validated_data['success_rate']
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
            if 'token_consumption' in validated_data:
                token_data = validated_data['token_consumption']
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
            
        except Exception as e:
            st.error(format_runtime_error(f"Failed to create execution metrics: {e}", ErrorSeverity.MEDIUM))
            return self._empty_chart("Erreur lors de la création du graphique")
    
    def _validate_ideas_data(self, ideas_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate ideas data structure"""
        validated = []
        for item in ideas_data:
            if not isinstance(item, dict):
                continue
            
            validated_item = {
                'name': str(item.get('name', 'Unknown')),
                'score': float(item.get('score', 0))
            }
            
            # Validate score range
            if not 0 <= validated_item['score'] <= 100:
                validated_item['score'] = max(0, min(100, validated_item['score']))
            
            validated.append(validated_item)
        
        return validated
    
    def _validate_timeline_data(self, stages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate timeline data structure"""
        validated = []
        for item in stages_data:
            if not isinstance(item, dict):
                continue
            
            validated_item = {
                'stage': str(item.get('stage', 'Unknown')),
                'start_time': float(item.get('start_time', 0)),
                'end_time': float(item.get('end_time', 0)),
                'duration': float(item.get('duration', 0))
            }
            
            # Ensure end_time >= start_time
            if validated_item['end_time'] < validated_item['start_time']:
                validated_item['end_time'] = validated_item['start_time']
                validated_item['duration'] = 0
            
            validated.append(validated_item)
        
        return validated
    
    def _validate_signals_data(self, signals_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate signals data structure"""
        validated = {}
        for key, value in signals_data.items():
            if isinstance(value, (int, float)):
                validated[str(key)] = float(value)
            elif isinstance(value, str) and value.isdigit():
                validated[str(key)] = float(value)
        
        return validated
    
    def _validate_risk_data(self, risk_data: Dict[str, float]) -> Dict[str, float]:
        """Validate risk data structure"""
        validated = {}
        for key, value in risk_data.items():
            if isinstance(value, (int, float)):
                # Ensure risk values are in 0-10 range
                validated[str(key)] = max(0, min(10, float(value)))
        
        return validated
    
    def _validate_competitor_data(self, competitors_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate competitor data structure"""
        validated = []
        for item in competitors_data:
            if not isinstance(item, dict):
                continue
            
            validated_item = {
                'name': str(item.get('name', 'Unknown')),
                'overall_score': float(item.get('overall_score', 0)),
                'features': item.get('features', {})
            }
            
            # Validate score range
            if not 0 <= validated_item['overall_score'] <= 100:
                validated_item['overall_score'] = max(0, min(100, validated_item['overall_score']))
            
            validated.append(validated_item)
        
        return validated
    
    def _validate_metrics_data(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate metrics data structure"""
        validated = {}
        
        for key, value in metrics_data.items():
            if key == 'execution_time' and isinstance(value, (int, float)):
                validated[key] = max(0, float(value))
            elif key == 'success_rate' and isinstance(value, (int, float)):
                validated[key] = max(0, min(100, float(value)))
            elif key == 'memory_usage' and isinstance(value, dict):
                validated[key] = {k: max(0, float(v)) for k, v in value.items() if isinstance(v, (int, float))}
            elif key == 'token_consumption' and isinstance(value, dict):
                validated[key] = {k: max(0, int(v)) for k, v in value.items() if isinstance(v, (int, float))}
        
        return validated
    
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
    
    def render_chart(self, fig: go.Figure, use_container_width: bool = True, height: Optional[int] = None) -> None:
        """Render a chart in Streamlit with error handling."""
        try:
            if height:
                fig.update_layout(height=height)
            st.plotly_chart(fig, use_container_width=use_container_width)
        except Exception as e:
            st.error(format_runtime_error(f"Failed to render chart: {e}", ErrorSeverity.MEDIUM))
            st.error("Le graphique ne peut pas être affiché en raison d'une erreur")
    
    def create_metrics_summary(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Create a metrics summary for display with validation."""
        try:
            return {
                "total_ideas": max(0, int(metrics.get("total_ideas", 0))),
                "avg_score": max(0, min(100, float(metrics.get("avg_score", 0)))),
                "confidence": max(0, min(100, float(metrics.get("confidence", 0)))),
                "execution_time": max(0, float(metrics.get("execution_time", 0))),
                "success_rate": max(0, min(100, float(metrics.get("success_rate", 0)))),
                "tokens_used": max(0, int(metrics.get("tokens_used", 0)))
            }
        except Exception as e:
            st.warning(f"Error creating metrics summary: {e}")
            return {
                "total_ideas": 0,
                "avg_score": 0,
                "confidence": 0,
                "execution_time": 0,
                "success_rate": 0,
                "tokens_used": 0
            }


# Global chart manager instance
_global_chart_manager = ChartManager()


def get_chart_manager() -> ChartManager:
    """Get the global chart manager instance."""
    return _global_chart_manager
