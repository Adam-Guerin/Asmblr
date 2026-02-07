"""Test threshold constants and validation functions."""

import pytest
from app.core.thresholds import (
    SIGNAL_SOURCES_TARGET,
    SIGNAL_PAINS_TARGET,
    IDEA_ACTIONABILITY_MIN_SCORE,
    LEARNING_HISTORY_MAX_RUNS,
    validate_threshold_range,
    get_threshold_summary,
)


class TestThresholdConstants:
    """Test that threshold constants are within reasonable ranges."""

    def test_signal_processing_thresholds_are_reasonable(self):
        """Test that signal processing thresholds are within expected ranges."""
        # Signal processing thresholds should be positive and reasonable
        assert SIGNAL_SOURCES_TARGET == 6, "Sources target should be 6"
        assert SIGNAL_PAINS_TARGET == 8, "Pains target should be 8"
        
        # Should be within recommended ranges
        assert 3 <= SIGNAL_SOURCES_TARGET <= 10, "Sources should be 3-10"
        assert 5 <= SIGNAL_PAINS_TARGET <= 15, "Pains should be 5-15"

    def test_idea_scoring_thresholds_are_reasonable(self):
        """Test that idea scoring thresholds are within expected ranges."""
        # Actionability thresholds should be reasonable
        assert IDEA_ACTIONABILITY_MIN_SCORE == 55, "Actionability min score should be 55"
        
        # Should be within recommended ranges
        assert 40 <= IDEA_ACTIONABILITY_MIN_SCORE <= 70, "Actionability should be 40-70"

    def test_learning_thresholds_are_reasonable(self):
        """Test that learning thresholds are within expected ranges."""
        # Learning thresholds should be positive and reasonable
        assert LEARNING_HISTORY_MAX_RUNS == 200, "History max runs should be 200"
        
        # Should be within recommended ranges
        assert 50 <= LEARNING_HISTORY_MAX_RUNS <= 500, "History runs should be 50-500"

    def test_threshold_summary_structure(self):
        """Test that threshold summary provides expected structure."""
        summary = get_threshold_summary()
        
        # Should have main categories
        assert "signal_processing" in summary
        assert "idea_scoring" in summary
        assert "historical_learning" in summary
        assert "text_processing" in summary
        
        # Should contain expected keys
        signal_cat = summary["signal_processing"]
        assert "sources_target" in signal_cat
        assert "pains_target" in signal_cat
        
        idea_cat = summary["idea_scoring"]
        assert "actionability_min_score" in idea_cat
        assert "actionability_adjustment_max" in idea_cat

    def test_validate_threshold_range_accepts_valid_values(self):
        """Test that validation accepts values within range."""
        # Should not raise exception for valid values
        validate_threshold_range(50, 30, 70, "test_threshold")
        validate_threshold_range(0.18, 0.1, 0.3, "exploration_rate")

    def test_validate_threshold_range_rejects_invalid_values(self):
        """Test that validation rejects values outside range."""
        # Should raise exception for values outside range
        with pytest.raises(ValueError, match="test_threshold=100 is outside recommended range"):
            validate_threshold_range(100, 30, 70, "test_threshold")
        
        with pytest.raises(ValueError, match="exploration_rate=0.5 is outside recommended range"):
            validate_threshold_range(0.5, 0.1, 0.3, "exploration_rate")

    def test_threshold_values_are_immutable(self):
        """Test that threshold constants are properly defined as Final."""
        # These should be constants that can't be modified
        with pytest.raises(AttributeError):
            SIGNAL_SOURCES_TARGET = 999
        
        with pytest.raises(AttributeError):
            IDEA_ACTIONABILITY_MIN_SCORE = 999

    def test_threshold_documentation_completeness(self):
        """Test that all thresholds have proper docstrings."""
        # All threshold constants should have docstrings
        assert SIGNAL_SOURCES_TARGET.__doc__ is not None
        assert SIGNAL_PAINS_TARGET.__doc__ is not None
        assert IDEA_ACTIONABILITY_MIN_SCORE.__doc__ is not None
        assert LEARNING_HISTORY_MAX_RUNS.__doc__ is not None
        
        # Docstrings should contain key information
        assert "Rationale:" in SIGNAL_SOURCES_TARGET.__doc__
        assert "Impact:" in SIGNAL_SOURCES_TARGET.__doc__
        assert "Recommended Range:" in SIGNAL_SOURCES_TARGET.__doc__


class TestThresholdIntegration:
    """Test that thresholds are properly integrated throughout the codebase."""

    def test_thresholds_used_in_pipeline(self):
        """Test that thresholds are imported and used in pipeline."""
        # This test ensures the constants are actually being used
        from app.core import pipeline
        
        # Check that the module has the threshold constants available
        assert hasattr(pipeline, 'SIGNAL_SOURCES_TARGET') or hasattr(pipeline.VenturePipeline, '_apply_actionability_to_scores')
        
        # The actual usage will be tested in integration tests

    def test_threshold_values_match_env_example(self):
        """Test that threshold values match .env.example defaults."""
        # These should match the documented defaults
        assert SIGNAL_SOURCES_TARGET == 6, "Should match SIGNAL_SOURCES_TARGET=6"
        assert SIGNAL_PAINS_TARGET == 8, "Should match SIGNAL_PAINS_TARGET=8"
        assert IDEA_ACTIONABILITY_MIN_SCORE == 55, "Should match IDEA_ACTIONABILITY_MIN_SCORE=55"
        assert LEARNING_HISTORY_MAX_RUNS == 200, "Should match LEARNING_HISTORY_MAX_RUNS=200"


class TestThresholdRationale:
    """Test the rationale behind threshold values."""

    def test_actionability_calculation_rationale(self):
        """Test that actionability threshold has sound rationale."""
        # 55 = 50% (neutral) + 5% (minimum viability buffer)
        expected_neutral = 50
        expected_buffer = 5
        expected_threshold = expected_neutral + expected_buffer
        
        assert IDEA_ACTIONABILITY_MIN_SCORE == expected_threshold
        
        # Should be based on 0-100 scale
        assert 0 <= IDEA_ACTIONABILITY_MIN_SCORE <= 100

    def test_exploration_rate_rationale(self):
        """Test that exploration rate has sound rationale."""
        # 0.18 = 18% exploration, 82% exploitation
        # This balances innovation with leveraging proven patterns
        from app.core.thresholds import LEARNING_EXPLORATION_RATE
        
        assert 0.1 <= LEARNING_EXPLORATION_RATE <= 0.3
        assert LEARNING_EXPLORATION_RATE == 0.18  # 18% exploration

    def test_signal_target_rationale(self):
        """Test that signal targets balance quality with practicality."""
        # These targets should provide sufficient data without being overwhelming
        assert 3 <= SIGNAL_SOURCES_TARGET <= 10, "Should be manageable but diverse"
        assert 5 <= SIGNAL_PAINS_TARGET <= 15, "Should capture key pains without noise"
        
        # Should work together as a system
        total_signal_requirements = SIGNAL_SOURCES_TARGET + SIGNAL_PAINS_TARGET
        assert total_signal_requirements <= 25, "Should not require excessive data collection"
