"""Integration tests for UI components."""

import streamlit as st
from unittest.mock import Mock, patch

from app.ui.theme_manager import ThemeManager, get_theme_manager
from app.ui.charts import ChartManager, get_chart_manager
from app.ui.export_manager import ExportManager, get_export_manager


class TestThemeManager:
    """Test suite for theme management functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.theme_manager = ThemeManager()
    
    def test_theme_availability(self):
        """Test that all required themes are available."""
        available_themes = self.theme_manager.themes
        
        assert "light" in available_themes
        assert "dark" in available_themes
        assert "blue" in available_themes
        assert "green" in available_themes
    
    def test_theme_css_generation(self):
        """Test CSS generation for different themes."""
        for theme_name in self.theme_manager.themes.keys():
            css = self.theme_manager.get_theme_css(theme_name)
            
            assert isinstance(css, str)
            assert len(css) > 0
            assert ".main-header" in css
            assert ".status-box" in css
            assert ".idea-card" in css
    
    def test_dark_theme_css(self):
        """Test dark theme specific CSS properties."""
        css = self.theme_manager.get_theme_css("dark")
        
        # Should contain dark theme specific colors
        assert self.theme_manager.colors.dark_background in css
        assert self.theme_manager.colors.dark_surface in css
        assert self.theme_manager.colors.dark_text in css
    
    def test_status_color_mapping(self):
        """Test status color mapping."""
        test_cases = [
            ("completed", self.theme_manager.colors.success),
            ("running", self.theme_manager.colors.primary),
            ("failed", self.theme_manager.colors.error),
            ("pending", self.theme_manager.colors.text_secondary),
            ("warning", self.theme_manager.colors.warning),
        ]
        
        for status, expected_color in test_cases:
            color = self.theme_manager.get_status_color(status)
            assert color == expected_color
    
    @patch('streamlit.session_state', {})
    def test_theme_selector_rendering(self):
        """Test theme selector rendering."""
        with patch.object(st, 'selectbox') as mock_selectbox:
            mock_selectbox.return_value = "light"
            
            theme = self.theme_manager.render_theme_selector()
            
            assert mock_selectbox.called
            assert theme == "light"
    
    def test_progress_stage_rendering(self):
        """Test progress stage rendering."""
        with patch.object(st, 'markdown') as mock_markdown:
            self.theme_manager.render_progress_stage(
                "Test Stage", 
                "active", 
                "Processing..."
            )
            
            mock_markdown.assert_called()
            call_args = mock_markdown.call_args[0][0]
            assert "Test Stage" in call_args
            assert "active" in call_args
            assert "Processing..." in call_args


class TestChartManager:
    """Test suite for chart management functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.chart_manager = ChartManager()
    
    def test_idea_scoring_chart_creation(self):
        """Test idea scoring chart creation."""
        sample_data = [
            {"name": "Idea 1", "score": 85.5},
            {"name": "Idea 2", "score": 72.3},
            {"name": "Idea 3", "score": 91.2}
        ]
        
        fig = self.chart_manager.create_idea_scoring_chart(sample_data)
        
        assert fig is not None
        assert len(fig.data) > 0
        assert fig.layout.title.text == "📊 Scores des Idées"
    
    def test_confidence_gauge_creation(self):
        """Test confidence gauge creation."""
        fig = self.chart_manager.create_confidence_gauge(78.5)
        
        assert fig is not None
        assert len(fig.data) > 0
        assert "Score de Confiance" in fig.layout.title.text
    
    def test_empty_chart_handling(self):
        """Test handling of empty data."""
        fig = self.chart_manager.create_idea_scoring_chart([])
        
        assert fig is not None
        assert "Aucune idée à afficher" in str(fig.layout.annotations)
    
    def test_market_signals_chart(self):
        """Test market signals chart creation."""
        signals_data = {
            "Sources": 12,
            "Pain Points": 8,
            "Competitors": 6,
            "Opportunities": 15
        }
        
        fig = self.chart_manager.create_market_signals_chart(signals_data)
        
        assert fig is not None
        assert len(fig.data) > 0
        assert "Signaux de Marché" in fig.layout.title.text
    
    def test_risk_assessment_radar(self):
        """Test risk assessment radar chart."""
        risk_data = {
            "Technical": 7.5,
            "Market": 6.2,
            "Financial": 8.1,
            "Competition": 5.8,
            "Timing": 4.9
        }
        
        fig = self.chart_manager.create_risk_assessment_radar(risk_data)
        
        assert fig is not None
        assert len(fig.data) > 0
        assert "Évaluation des Risques" in fig.layout.title.text
    
    def test_competitor_analysis_chart(self):
        """Test competitor analysis chart."""
        competitors_data = [
            {
                "name": "Competitor A",
                "overall_score": 85.2,
                "features": {"UI": 8, "Performance": 7, "Features": 9}
            },
            {
                "name": "Competitor B", 
                "overall_score": 72.8,
                "features": {"UI": 6, "Performance": 8, "Features": 7}
            }
        ]
        
        fig = self.chart_manager.create_competitor_analysis(competitors_data)
        
        assert fig is not None
        assert len(fig.data) > 0
        assert "Analyse Concurrentielle" in fig.layout.title.text
    
    def test_execution_metrics_chart(self):
        """Test execution metrics dashboard."""
        metrics_data = {
            "execution_time": 120.5,
            "memory_usage": {"initial": 100, "peak": 250, "final": 150},
            "success_rate": 87.5,
            "token_consumption": {"input": 1000, "output": 500, "total": 1500}
        }
        
        fig = self.chart_manager.create_execution_metrics(metrics_data)
        
        assert fig is not None
        assert len(fig.data) > 0
        assert "Métriques d'Exécution" in fig.layout.title.text
    
    @patch.object(st, 'plotly_chart')
    def test_chart_rendering(self, mock_plotly_chart):
        """Test chart rendering in Streamlit."""
        fig = self.chart_manager.create_confidence_gauge(75.0)
        
        self.chart_manager.render_chart(fig)
        
        mock_plotly_chart.assert_called_once_with(fig, use_container_width=True)
    
    def test_metrics_summary_creation(self):
        """Test metrics summary creation."""
        metrics = {
            "total_ideas": 15,
            "avg_score": 78.5,
            "confidence": 82.3,
            "execution_time": 145.7,
            "success_rate": 91.2,
            "tokens_used": 2500
        }
        
        summary = self.chart_manager.create_metrics_summary(metrics)
        
        assert summary["total_ideas"] == 15
        assert summary["avg_score"] == 78.5
        assert summary["confidence"] == 82.3


class TestExportManager:
    """Test suite for export management functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.export_manager = ExportManager()
        self.sample_results = {
            "research": {
                "ideas": [
                    {
                        "name": "AI Compliance Tool",
                        "score": 85.2,
                        "one_liner": "Automated compliance checking",
                        "target_user": "Compliance officers",
                        "problem": "Manual compliance processes",
                        "solution": "AI-powered automation"
                    }
                ],
                "pain_statements": [
                    "Manual compliance checking is time-consuming",
                    "Regulatory changes are hard to track"
                ]
            },
            "analysis": {
                "top_idea": {
                    "name": "AI Compliance Tool",
                    "score": 85.2,
                    "rationale": "High market demand and clear value proposition"
                }
            },
            "product": {
                "prd_markdown": "# Product Requirements\n\n## Overview\nAI Compliance Tool..."
            },
            "tech": {
                "tech_spec_markdown": "# Technical Specifications\n\n## Architecture\n..."
            }
        }
    
    def test_json_export(self):
        """Test JSON export functionality."""
        data = self.export_manager.export_results(self.sample_results, "json", "test_run_123")
        
        assert data is not None
        assert isinstance(data, bytes)
        
        # Verify JSON structure
        import json
        decoded = json.loads(data.decode('utf-8'))
        assert decoded["run_id"] == "test_run_123"
        assert "results" in decoded
        assert "export_timestamp" in decoded
    
    def test_csv_export(self):
        """Test CSV export functionality."""
        data = self.export_manager.export_results(self.sample_results, "csv", "test_run_123")
        
        assert data is not None
        assert isinstance(data, bytes)
        
        # Verify CSV structure
        csv_content = data.decode('utf-8')
        assert "run_id" in csv_content
        assert "idea" in csv_content
        assert "AI Compliance Tool" in csv_content
    
    def test_markdown_export(self):
        """Test Markdown export functionality."""
        data = self.export_manager.export_results(self.sample_results, "markdown", "test_run_123")
        
        assert data is not None
        assert isinstance(data, bytes)
        
        # Verify Markdown structure
        md_content = data.decode('utf-8')
        assert "# 🚀 Asmblr Results Report" in md_content
        assert "AI Compliance Tool" in md_content
        assert "test_run_123" in md_content
    
    def test_zip_export(self):
        """Test ZIP export functionality."""
        data = self.export_manager.export_results(self.sample_results, "zip", "test_run_123")
        
        assert data is not None
        assert isinstance(data, bytes)
        
        # Verify ZIP structure
        import zipfile
        import io
        
        zip_buffer = io.BytesIO(data)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            file_list = zip_file.namelist()
            assert "test_run_123_results.json" in file_list
            assert "test_run_123_results.csv" in file_list
            assert "test_run_123_report.md" in file_list
            assert "README.txt" in file_list
    
    def test_unsupported_format(self):
        """Test handling of unsupported export formats."""
        data = self.export_manager.export_results(self.sample_results, "unsupported", "test_run_123")
        
        assert data is None
    
    def test_download_link_generation(self):
        """Test download link generation."""
        test_data = b"test export data"
        
        link = self.export_manager.get_download_link(test_data, "test.json", "json")
        
        assert isinstance(link, str)
        assert "data:application/json;base64," in link
        assert "download=test.json" in link
        assert "Télécharger JSON" in link
    
    @patch.object(st, 'button')
    @patch.object(st, 'spinner')
    @patch.object(st, 'success')
    def test_export_buttons_rendering(self, mock_success, mock_spinner, mock_button):
        """Test export buttons rendering."""
        mock_button.return_value = True
        mock_spinner.return_value.__enter__ = Mock(return_value=None)
        mock_spinner.return_value.__exit__ = Mock(return_value=None)
        
        with patch.object(self.export_manager, 'export_results') as mock_export:
            mock_export.return_value = b"test data"
            
            self.export_manager.render_export_buttons(self.sample_results, "test_run_123")
            
            # Should call export for each format
            assert mock_export.call_count >= len(self.export_manager.supported_formats)
    
    def test_export_preview(self):
        """Test export preview functionality."""
        # Test JSON preview
        with patch.object(st, 'json') as mock_json:
            self.export_manager.render_export_preview(self.sample_results, "json")
            mock_json.assert_called_with(self.sample_results)
        
        # Test CSV preview
        with patch.object(st, 'dataframe') as mock_dataframe:
            self.export_manager.render_export_preview(self.sample_results, "csv")
            mock_dataframe.assert_called()
        
        # Test Markdown preview
        with patch.object(st, 'markdown') as mock_markdown:
            self.export_manager.render_export_preview(self.sample_results, "markdown")
            mock_markdown.assert_called()


class TestUIIntegration:
    """Integration tests for UI components."""
    
    def test_global_managers(self):
        """Test global manager instances."""
        theme_manager = get_theme_manager()
        chart_manager = get_chart_manager()
        export_manager = get_export_manager()
        
        # Should return singleton instances
        assert get_theme_manager() is theme_manager
        assert get_chart_manager() is chart_manager
        assert get_export_manager() is export_manager
    
    @patch('streamlit.session_state', {})
    def test_theme_persistence(self):
        """Test theme persistence across sessions."""
        theme_manager = get_theme_manager()
        
        with patch.object(st, 'selectbox') as mock_selectbox:
            mock_selectbox.return_value = "dark"
            
            theme = theme_manager.render_theme_selector()
            
            assert theme == "dark"
    
    def test_chart_data_flow(self):
        """Test data flow through chart system."""
        chart_manager = get_chart_manager()
        
        # Test with realistic data
        ideas_data = [
            {"name": f"Idea {i}", "score": 70 + i * 5}
            for i in range(5)
        ]
        
        fig = chart_manager.create_idea_scoring_chart(ideas_data)
        
        assert len(fig.data) == 1
        assert len(fig.data[0].x) == 5
        assert len(fig.data[0].y) == 5
    
    def test_export_data_integrity(self):
        """Test data integrity through export system."""
        export_manager = get_export_manager()
        
        # Test with complex nested data
        complex_results = {
            "metadata": {
                "run_id": "complex_test",
                "timestamp": "2024-01-01T12:00:00Z",
                "version": "1.0.0"
            },
            "nested": {
                "level1": {
                    "level2": {
                        "data": [1, 2, 3, 4, 5]
                    }
                }
            },
            "arrays": ["item1", "item2", "item3"],
            "numbers": 42,
            "booleans": True,
            "null_value": None
        }
        
        # Test JSON export preserves structure
        json_data = export_manager.export_results(complex_results, "json", "test")
        import json
        decoded = json.loads(json_data.decode('utf-8'))
        
        assert decoded["results"]["metadata"]["run_id"] == "complex_test"
        assert decoded["results"]["nested"]["level1"]["level2"]["data"] == [1, 2, 3, 4, 5]
        assert decoded["results"]["arrays"] == ["item1", "item2", "item3"]
        assert decoded["results"]["numbers"] == 42
        assert decoded["results"]["booleans"] is True
        assert decoded["results"]["null_value"] is None
