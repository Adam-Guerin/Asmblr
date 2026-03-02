"""Test the automatic collection actions rule for unknown critical fields."""

from pathlib import Path
from unittest.mock import Mock


from app.core.pipeline import VenturePipeline
from app.core.config import Settings


def test_collection_actions_proposed_for_unknown_fields(tmp_path: Path) -> None:
    """Test that collection actions are automatically proposed when critical fields are unknown."""
    
    # Create minimal settings
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    settings.config_dir = tmp_path / "configs"
    
    # Create directories
    settings.runs_dir.mkdir(parents=True, exist_ok=True)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.config_dir.mkdir(parents=True, exist_ok=True)
    
    # Create pipeline
    pipeline = VenturePipeline(settings)
    run_id = "test_run_001"
    topic = "productivity tools"
    
    # Create run directory
    run_dir = settings.runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock manager methods
    pipeline.manager = Mock()
    pipeline.manager.write_json = Mock()
    pipeline._log_progress = Mock()
    
    # Test data with unknown critical fields
    data_source = {
        "pages": "unknown",
        "pains": "real", 
        "competitors": "unknown",
        "seeds": "none"
    }
    
    decision_missing = []
    
    # Call the method
    pipeline._propose_collection_actions_for_unknown_fields(run_id, data_source, topic, decision_missing)
    
    # Verify collection actions were written
    pipeline.manager.write_json.assert_called_once()
    call_args = pipeline.manager.write_json.call_args
    assert call_args[0][0] == run_id
    assert call_args[0][1] == "collection_actions.json"
    
    # Check the content of collection actions
    collection_actions = call_args[0][2]
    assert collection_actions["topic"] == topic
    assert set(collection_actions["unknown_fields"]) == {"pages", "competitors"}
    assert len(collection_actions["actions"]) == 2
    
    # Verify specific actions
    actions_by_field = {action["field"]: action for action in collection_actions["actions"]}
    
    # Check pages action
    pages_action = actions_by_field["pages"]
    assert pages_action["priority"] == "HIGH"
    assert "Configure pain_sources" in pages_action["next_step"]
    assert pages_action["estimated_impact"] == "CRITICAL - No market signals available"
    
    # Check competitors action  
    competitors_action = actions_by_field["competitors"]
    assert competitors_action["priority"] == "MEDIUM"
    assert "Configure competitor_sources" in competitors_action["next_step"]
    assert competitors_action["estimated_impact"] == "MEDIUM - No competitive analysis"
    
    # Verify logging
    pipeline._log_progress.assert_called_once()
    log_call = pipeline._log_progress.call_args[0][1]
    assert "Collection actions auto-proposed" in log_call
    assert "pages (HIGH)" in log_call
    assert "competitors (MEDIUM)" in log_call
    
    # Verify decision_missing was updated
    assert len(decision_missing) == 2
    assert any("pages" in missing and "Configure pain_sources" in missing for missing in decision_missing)
    assert any("competitors" in missing and "Configure competitor_sources" in missing for missing in decision_missing)


def test_no_collection_actions_for_all_real_fields(tmp_path: Path) -> None:
    """Test that no collection actions are proposed when all critical fields are real."""
    
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    settings.config_dir = tmp_path / "configs"
    
    # Create directories
    settings.runs_dir.mkdir(parents=True, exist_ok=True)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.config_dir.mkdir(parents=True, exist_ok=True)
    
    pipeline = VenturePipeline(settings)
    run_id = "test_run_002"
    topic = "productivity tools"
    
    # Mock manager methods
    pipeline.manager = Mock()
    pipeline.manager.write_json = Mock()
    pipeline._log_progress = Mock()
    
    # Test data with all real fields
    data_source = {
        "pages": "real",
        "pains": "real", 
        "competitors": "real",
        "seeds": "seed"
    }
    
    decision_missing = []
    
    # Call the method
    pipeline._propose_collection_actions_for_unknown_fields(run_id, data_source, topic, decision_missing)
    
    # Verify no collection actions were written
    pipeline.manager.write_json.assert_not_called()
    pipeline._log_progress.assert_not_called()
    
    # Verify decision_missing was not updated
    assert len(decision_missing) == 0


def test_field_impact_estimation(tmp_path: Path) -> None:
    """Test the field impact estimation function."""
    
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    settings.config_dir = tmp_path / "configs"
    
    pipeline = VenturePipeline(settings)
    
    # Test impact estimation for each field
    assert pipeline._estimate_field_impact("pages") == "CRITICAL - No market signals available"
    assert pipeline._estimate_field_impact("pains") == "HIGH - Limited problem understanding"
    assert pipeline._estimate_field_impact("competitors") == "MEDIUM - No competitive analysis"
    assert pipeline._estimate_field_impact("seeds") == "LOW - Can proceed with generic analysis"
    assert pipeline._estimate_field_impact("unknown_field") == "UNKNOWN"


def test_collection_actions_json_structure(tmp_path: Path) -> None:
    """Test that the collection actions JSON has the correct structure."""
    
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    settings.config_dir = tmp_path / "configs"
    
    # Create directories
    settings.runs_dir.mkdir(parents=True, exist_ok=True)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.config_dir.mkdir(parents=True, exist_ok=True)
    
    pipeline = VenturePipeline(settings)
    run_id = "test_run_003"
    topic = "productivity tools"
    
    # Mock manager methods
    pipeline.manager = Mock()
    pipeline.manager.write_json = Mock()
    pipeline._log_progress = Mock()
    
    # Test data with unknown fields
    data_source = {
        "pages": "unknown",
        "pains": "unknown",
        "competitors": "real",
        "seeds": "none"
    }
    
    decision_missing = []
    
    # Call the method
    pipeline._propose_collection_actions_for_unknown_fields(run_id, data_source, topic, decision_missing)
    
    # Get the written JSON
    call_args = pipeline.manager.write_json.call_args
    collection_actions = call_args[0][2]
    
    # Verify JSON structure
    required_keys = {"topic", "unknown_fields", "actions", "generated_at", "rule_applied"}
    assert set(collection_actions.keys()) == required_keys
    
    # Verify rule metadata
    assert collection_actions["rule_applied"] == "auto-propose-collection-for-unknown-critical-fields"
    assert "generated_at" in collection_actions
    assert isinstance(collection_actions["generated_at"], str)
    
    # Verify actions structure
    for action in collection_actions["actions"]:
        required_action_keys = {"field", "source_missing", "next_step", "priority", "estimated_impact"}
        assert set(action.keys()) == required_action_keys
        assert action["priority"] in {"HIGH", "MEDIUM"}
        assert isinstance(action["source_missing"], str)
        assert isinstance(action["next_step"], str)
        assert isinstance(action["estimated_impact"], str)
