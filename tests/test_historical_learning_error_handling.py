"""Test error handling in historical learning functions."""

from unittest.mock import Mock

from app.core.models import IdeaScore, Idea


def test_build_historical_learning_memory_handles_load_feedback_records_error():
    """Test that _build_historical_learning_memory handles feedback loading errors gracefully."""
    # Create a minimal mock pipeline object with just the methods we need
    pipeline = Mock()
    pipeline.settings = Mock()
    pipeline.manager = Mock()
    pipeline._load_feedback_records = Mock(side_effect=Exception("Database error"))
    pipeline.manager.list_runs = Mock(return_value=[])
    pipeline._topic_tokens = Mock(return_value={"test"})
    pipeline._load_text_artifact = Mock(return_value="")
    
    # Import the actual function and bind it to our mock
    from app.core.pipeline import VenturePipeline
    func = VenturePipeline._build_historical_learning_memory
    
    result = func(pipeline, "test topic")
    
    # Should return a valid structure even with errors
    assert "topic" in result
    assert result["topic"] == "test topic"
    assert result["feedback_records"] == 0
    assert result["finalized_runs"] == 0
    assert isinstance(result["success_keywords"], list)
    assert isinstance(result["failure_keywords"], list)
    assert isinstance(result["success_topic_sets"], list)
    assert isinstance(result["failure_topic_sets"], list)
    assert isinstance(result["recent_failure_reasons"], list)
    assert "exploration_rate" in result


def test_build_historical_learning_memory_handles_list_runs_error():
    """Test that _build_historical_learning_memory handles run listing errors gracefully."""
    pipeline = Mock()
    pipeline.settings = Mock()
    pipeline.manager = Mock()
    pipeline._load_feedback_records = Mock(return_value=[])
    pipeline.manager.list_runs = Mock(side_effect=Exception("Run manager error"))
    pipeline._topic_tokens = Mock(return_value={"test"})
    pipeline._load_text_artifact = Mock(return_value="")
    
    from app.core.pipeline import VenturePipeline
    func = VenturePipeline._build_historical_learning_memory
    
    result = func(pipeline, "test topic")
    
    # Should return a valid structure even with errors
    assert "topic" in result
    assert result["topic"] == "test topic"
    assert result["feedback_records"] == 0
    assert result["finalized_runs"] == 0


def test_build_historical_learning_memory_handles_settings_errors():
    """Test that _build_historical_learning_memory handles settings errors gracefully."""
    pipeline = Mock()
    pipeline.settings = Mock()
    pipeline.settings.learning_history_max_runs = Mock(side_effect=Exception("Settings error"))
    pipeline.manager = Mock()
    pipeline._load_feedback_records = Mock(return_value=[])
    pipeline.manager.list_runs = Mock(return_value=[])
    pipeline._topic_tokens = Mock(return_value={"test"})
    pipeline._load_text_artifact = Mock(return_value="")
    
    from app.core.pipeline import VenturePipeline
    func = VenturePipeline._build_historical_learning_memory
    
    result = func(pipeline, "test topic")
    
    # Should use default values and return valid structure
    assert "topic" in result
    assert result["topic"] == "test topic"
    assert result["finalized_runs"] == 0


def test_apply_historical_learning_to_scores_handles_memory_errors():
    """Test that _apply_historical_learning_to_scores handles memory errors gracefully."""
    pipeline = Mock()
    pipeline.settings = Mock()
    pipeline._topic_tokens = Mock(return_value={"test"})
    pipeline._token_similarity = Mock(return_value=0.5)
    
    from app.core.pipeline import VenturePipeline
    func = VenturePipeline._apply_historical_learning_to_scores
    
    scores = [
        IdeaScore(name="test idea", score=50, rationale="test rationale", risks=[], signals={})
    ]
    ideas = [Idea(name="test idea", one_liner="test", target_user="test user", problem="test", solution="test", key_features=[])]
    
    # Test with invalid memory structure that should cause the function to return original scores
    invalid_memory = {"invalid": "data"}
    
    result = func(pipeline, scores, ideas, "test topic", "test-run", invalid_memory)
    
    # Should return scores (they may be modified by the learning algorithm even with invalid memory)
    assert len(result) == 1
    assert result[0].name == "test idea"
    # Score may be different due to processing, but should be valid
    assert 0 <= result[0].score <= 100


def test_apply_historical_learning_to_scores_handles_individual_score_errors():
    """Test that _apply_historical_learning_to_scores handles individual score processing errors gracefully."""
    pipeline = Mock()
    pipeline.settings = Mock()
    pipeline.settings.learning_success_bonus_max = Mock(return_value=5)
    pipeline.settings.learning_failure_penalty_max = Mock(return_value=5)
    pipeline.settings.learning_novelty_bonus_max = Mock(return_value=3)
    pipeline.settings.learning_clone_penalty_start = Mock(return_value=0.7)
    
    # Mock _topic_tokens to fail for one idea
    def mock_topic_tokens(text):
        if "bad idea" in text:
            raise Exception("Token processing failed")
        return {"test"}
    
    pipeline._topic_tokens = Mock(side_effect=mock_topic_tokens)
    pipeline._token_similarity = Mock(return_value=0.5)
    
    from app.core.pipeline import VenturePipeline
    func = VenturePipeline._apply_historical_learning_to_scores
    
    scores = [
        IdeaScore(name="good idea", score=50, rationale="test rationale", risks=[], signals={}),
        IdeaScore(name="bad idea", score=60, rationale="test rationale", risks=[], signals={}),
    ]
    ideas = [
        Idea(name="good idea", one_liner="test", target_user="test user", problem="test", solution="test", key_features=[]),
        Idea(name="bad idea", one_liner="test", target_user="test user", problem="test", solution="test", key_features=[]),
    ]
    
    result = func(pipeline, scores, ideas, "test topic", "test-run", {"success_keywords": [], "failure_keywords": []})
    
    # Should return both scores, with the bad one unchanged
    assert len(result) == 2
    assert result[0].name == "good idea"
    assert result[1].name == "bad idea"
    assert result[1].score == 60  # Should be unchanged


def test_apply_historical_learning_to_scores_handles_settings_errors():
    """Test that _apply_historical_learning_to_scores handles settings errors gracefully."""
    pipeline = Mock()
    pipeline.settings = Mock()
    pipeline.settings.learning_success_bonus_max = Mock(side_effect=Exception("Settings error"))
    pipeline.settings.learning_failure_penalty_max = Mock(side_effect=Exception("Settings error"))
    pipeline.settings.learning_novelty_bonus_max = Mock(side_effect=Exception("Settings error"))
    pipeline.settings.learning_clone_penalty_start = Mock(side_effect=Exception("Settings error"))
    pipeline._topic_tokens = Mock(return_value={"test"})
    pipeline._token_similarity = Mock(return_value=0.5)
    
    from app.core.pipeline import VenturePipeline
    func = VenturePipeline._apply_historical_learning_to_scores
    
    scores = [
        IdeaScore(name="test idea", score=50, rationale="test rationale", risks=[], signals={})
    ]
    ideas = [Idea(name="test idea", one_liner="test", target_user="test user", problem="test", solution="test", key_features=[])]
    
    result = func(pipeline, scores, ideas, "test topic", "test-run", {"success_keywords": [], "failure_keywords": []})
    
    # Should return scores with default values applied
    assert len(result) == 1
    assert result[0].name == "test idea"


def test_apply_historical_learning_to_scores_handles_complete_failure():
    """Test that _apply_historical_learning_to_scores handles complete function failure gracefully."""
    pipeline = Mock()
    pipeline.settings = Mock()
    pipeline._topic_tokens = Mock(side_effect=Exception("Complete failure"))
    
    from app.core.pipeline import VenturePipeline
    func = VenturePipeline._apply_historical_learning_to_scores
    
    scores = [
        IdeaScore(name="test idea", score=50, rationale="test rationale", risks=[], signals={})
    ]
    ideas = [Idea(name="test idea", one_liner="test", target_user="test user", problem="test", solution="test", key_features=[])]
    
    result = func(pipeline, scores, ideas, "test topic", "test-run", {"success_keywords": [], "failure_keywords": []})
    
    # Should return original scores when everything fails
    assert len(result) == 1
    assert result[0].name == "test idea"
    assert result[0].score == 50
    assert result[0].rationale == "test rationale"
