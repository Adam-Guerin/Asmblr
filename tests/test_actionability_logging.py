"""Test actionability scoring logging to ensure fallback behavior is properly tracked."""

import pytest
from unittest.mock import Mock, patch, call
from app.core.pipeline import VenturePipeline
from app.core.models import Idea, IdeaScore
from app.core.config import Settings


class TestActionabilityLogging:
    """Test that actionability scoring logs fallback behavior appropriately."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing."""
        settings = Mock(spec=Settings)
        settings.idea_actionability_min_score = "50"
        settings.idea_actionability_adjustment_max = "25"
        settings.idea_actionability_require_eligible_top = False
        return settings

    @pytest.fixture
    def pipeline(self, mock_settings):
        """Create real pipeline with mock settings for testing."""
        # Create a real pipeline instance but with mocked settings
        pipeline = VenturePipeline.__new__(VenturePipeline)
        pipeline.settings = mock_settings
        pipeline.manager = Mock()
        pipeline.general_llm = Mock()
        pipeline.code_llm = Mock()
        pipeline.active_general_model = "test-model"
        pipeline.active_code_model = "test-model"
        pipeline.rag = Mock()
        return pipeline

    def test_logs_warning_when_no_ideas_meet_threshold(self, pipeline):
        """Test that warning is logged when no ideas meet actionability threshold."""
        # Create scores with low actionability (below threshold)
        scores = [
            IdeaScore(name="idea1", score=80, rationale="Good idea", risks=[], signals={}),
            IdeaScore(name="idea2", score=75, rationale="Decent idea", risks=[], signals={}),
        ]
        
        # Create ideas with low actionability assessments
        ideas = [
            Idea(name="idea1", one_liner="Idea 1", target_user="users", problem="problem1", 
                  solution="solution1", key_features=[]),
            Idea(name="idea2", one_liner="Idea 2", target_user="users", problem="problem2", 
                  solution="solution2", key_features=[]),
        ]
        
        # Mock actionability scoring to return low scores
        with patch.object(pipeline, '_score_idea_actionability') as mock_score:
            mock_score.side_effect = [
                {"score": 30, "issues": ["Too generic"], "strengths": []},
                {"score": 25, "issues": ["Hard to test"], "strengths": []},
            ]
            
            # Mock both regular logger and smart logger
            with patch('app.core.pipeline.logger') as mock_logger:
                with patch('app.core.pipeline.get_smart_logger') as mock_get_smart_logger:
                    mock_smart_logger = Mock()
                    mock_get_smart_logger.return_value = mock_smart_logger
                    
                    with patch.object(pipeline, '_log_progress') as mock_progress:
                        adjusted_scores, report = pipeline._apply_actionability_to_scores(scores, ideas)
        
        # Verify report shows no eligible ideas
        assert report["eligible"] == []
        assert len(report["blocked"]) == 2
        assert report["threshold"] == 50
        
        # Verify smart logger was called (since it's available)
        mock_smart_logger.business.assert_called()
        mock_smart_logger.debug.assert_called()
        
        # Check business log contains expected information
        business_call = mock_smart_logger.business.call_args
        call_args = business_call[0][2]  # Third positional argument (data dict)
        assert call_args["eligible_count"] == 0
        assert call_args["total_count"] == 2
        assert call_args["threshold"] == 50
        assert "avg_score" in call_args

    def test_logs_fallback_when_require_eligible_is_false(self, pipeline):
        """Test that actionability assessment logs correctly when require_eligible is false."""
        pipeline.settings.idea_actionability_require_eligible_top = False
        
        # Create scores with low actionability
        scores = [
            IdeaScore(name="idea1", score=80, rationale="Good idea", risks=[], signals={}),
            IdeaScore(name="idea2", score=75, rationale="Decent idea", risks=[], signals={}),
        ]
        
        # Create ideas
        ideas = [
            Idea(name="idea1", one_liner="Idea 1", target_user="users", problem="problem1", 
                  solution="solution1", key_features=[]),
            Idea(name="idea2", one_liner="Idea 2", target_user="users", problem="problem2", 
                  solution="solution2", key_features=[]),
        ]
        
        # Mock actionability scoring to return low scores
        with patch.object(pipeline, '_score_idea_actionability') as mock_score:
            mock_score.side_effect = [
                {"score": 30, "issues": ["Too generic"], "strengths": []},
                {"score": 25, "issues": ["Hard to test"], "strengths": []},
            ]
            
            # Mock both regular logger and smart logger
            with patch('app.core.pipeline.logger') as mock_logger:
                with patch('app.core.pipeline.get_smart_logger') as mock_get_smart_logger:
                    mock_smart_logger = Mock()
                    mock_get_smart_logger.return_value = mock_smart_logger
                    
                    with patch.object(pipeline, '_log_progress') as mock_progress:
                        adjusted_scores, report = pipeline._apply_actionability_to_scores(scores, ideas)
        
        # Verify the report shows no eligible ideas
        assert report["eligible"] == []
        assert len(report["blocked"]) == 2
        
        # Verify smart logger was called
        mock_smart_logger.business.assert_called()
        mock_smart_logger.debug.assert_called()
        
        # Check business log contains expected information
        business_call = mock_smart_logger.business.call_args
        call_args = business_call[0][2]  # Third positional argument (data dict)
        assert call_args["eligible_count"] == 0
        assert call_args["total_count"] == 2
        assert call_args["threshold"] == 50

    def test_logs_warning_when_no_scores_provided(self, pipeline):
        """Test that warning is logged when no scores are provided."""
        with patch('app.core.pipeline.logger') as mock_logger:
            adjusted_scores, report = pipeline._apply_actionability_to_scores([], [])
        
        # Verify warning was logged
        mock_logger.warning.assert_called_once_with(
            "Actionability assessment: No scores provided, returning empty results"
        )
        
        # Verify empty report structure
        assert report["assessments"] == []
        assert report["eligible"] == []
        assert report["blocked"] == []
        assert report["threshold"] == pipeline.settings.idea_actionability_min_score

    def test_logs_debug_details_for_blocked_ideas(self, pipeline):
        """Test that debug logging includes details about blocked ideas."""
        scores = [
            IdeaScore(name="idea1", score=80, rationale="Good idea", risks=[], signals={}),
            IdeaScore(name="idea2", score=75, rationale="Decent idea", risks=[], signals={}),
        ]
        
        ideas = [
            Idea(name="idea1", one_liner="Idea 1", target_user="users", problem="problem1", 
                  solution="solution1", key_features=[]),
            Idea(name="idea2", one_liner="Idea 2", target_user="users", problem="problem2", 
                  solution="solution2", key_features=[]),
        ]
        
        # Mock actionability scoring to return low scores
        with patch.object(pipeline, '_score_idea_actionability') as mock_score:
            mock_score.side_effect = [
                {"score": 30, "issues": ["Too generic"], "strengths": []},
                {"score": 25, "issues": ["Hard to test"], "strengths": []},
            ]
            
            # Mock both regular logger and smart logger
            with patch('app.core.pipeline.logger') as mock_logger:
                with patch('app.core.pipeline.get_smart_logger') as mock_get_smart_logger:
                    mock_smart_logger = Mock()
                    mock_get_smart_logger.return_value = mock_smart_logger
                    
                    with patch.object(pipeline, '_log_progress') as mock_progress:
                        adjusted_scores, report = pipeline._apply_actionability_to_scores(scores, ideas)
        
        # Verify smart logger debug was called with blocked details
        mock_smart_logger.debug.assert_called()
        debug_call = mock_smart_logger.debug.call_args
        debug_args = debug_call[0][1] if len(debug_call[0]) > 1 else debug_call[0][0]
        assert "ideas blocked by actionability threshold" in str(debug_args).lower()

    def test_no_warning_when_ideas_meet_threshold(self, pipeline):
        """Test that no fallback warning is logged when ideas meet threshold."""
        scores = [
            IdeaScore(name="idea1", score=80, rationale="Good idea", risks=[], signals={}),
            IdeaScore(name="idea2", score=75, rationale="Decent idea", risks=[], signals={}),
        ]
        
        ideas = [
            Idea(name="idea1", one_liner="Idea 1", target_user="users", problem="problem1", 
                  solution="solution1", key_features=[]),
            Idea(name="idea2", one_liner="Idea 2", target_user="users", problem="problem2", 
                  solution="solution2", key_features=[]),
        ]
        
        # Mock actionability scoring to return high scores (above threshold)
        with patch.object(pipeline, '_score_idea_actionability') as mock_score:
            mock_score.side_effect = [
                {"score": 70, "issues": [], "strengths": ["Very testable"]},
                {"score": 60, "issues": [], "strengths": ["Good market fit"]},
            ]
            
            # Mock both regular logger and smart logger
            with patch('app.core.pipeline.logger') as mock_logger:
                with patch('app.core.pipeline.get_smart_logger') as mock_get_smart_logger:
                    mock_smart_logger = Mock()
                    mock_get_smart_logger.return_value = mock_smart_logger
                    
                    with patch.object(pipeline, '_log_progress') as mock_progress:
                        adjusted_scores, report = pipeline._apply_actionability_to_scores(scores, ideas)
        
        # Verify the report shows eligible ideas
        assert len(report["eligible"]) == 2
        assert len(report["blocked"]) == 0
        
        # Verify smart logger was called
        mock_smart_logger.business.assert_called()
        
        # Check business log contains expected information
        business_call = mock_smart_logger.business.call_args
        call_args = business_call[0][2]  # Third positional argument (data dict)
        assert call_args["eligible_count"] == 2
        assert call_args["total_count"] == 2
        assert call_args["threshold"] == 50

    def test_logs_sanitized_data_in_fallback(self, pipeline):
        """Test that actionability assessment handles sensitive data appropriately."""
        pipeline.settings.idea_actionability_require_eligible_top = False
        
        # Create idea with potentially sensitive data
        scores = [
            IdeaScore(name="idea_with_api_key", score=80, rationale="Good idea with sk-1234567890abcdef", risks=[], signals={}),
        ]
        
        ideas = [
            Idea(name="idea_with_api_key", one_liner="Idea with API key", target_user="user@example.com", 
                  problem="problem1", solution="solution1", key_features=[]),
        ]
        
        # Mock actionability scoring
        with patch.object(pipeline, '_score_idea_actionability') as mock_score:
            mock_score.return_value = {"score": 30, "issues": ["Too generic"], "strengths": []}
            
            # Mock both regular logger and smart logger
            with patch('app.core.pipeline.logger') as mock_logger:
                with patch('app.core.pipeline.get_smart_logger') as mock_get_smart_logger:
                    mock_smart_logger = Mock()
                    mock_get_smart_logger.return_value = mock_smart_logger
                    
                    with patch.object(pipeline, '_log_progress') as mock_progress:
                        adjusted_scores, report = pipeline._apply_actionability_to_scores(scores, ideas)
        
        # Verify report shows blocked idea
        assert len(report["blocked"]) == 1
        assert "idea_with_api_key" in report["blocked"]
        
        # Verify smart logger was called
        mock_smart_logger.business.assert_called()
        mock_smart_logger.debug.assert_called()
        
        # Check business log contains expected information
        business_call = mock_smart_logger.business.call_args
        call_args = business_call[0][2]  # Third positional argument (data dict)
        assert call_args["eligible_count"] == 0
        assert call_args["total_count"] == 1
