"""Test Validation Sprint 7 jours mode functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from app.core.pipeline import VenturePipeline
from app.core.config import Settings
from app.core.models import IdeaScore


def test_validation_sprint_profile_configuration():
    """Test that validation_sprint profile is properly configured."""
    settings = Settings()
    pipeline = VenturePipeline(settings)
    
    profile = pipeline._resolve_execution_profile("validation_sprint", False)
    
    assert profile["name"] == "validation_sprint"
    assert profile["time_budget_min"] == 15
    assert profile["token_budget_est"] == 25000
    assert profile["max_sources"] == 5
    assert profile["max_n_ideas"] == 1
    assert profile["stage_retry_attempts"] == 1
    assert profile["force_fast_mode"] is True
    assert profile["output_mode"] == "execution_focused"


def test_generate_validation_hypothesis():
    """Test hypothesis generation for validation sprint."""
    settings = Settings()
    pipeline = VenturePipeline(settings)
    
    # Mock data
    topic = "AI productivity tools"
    top_idea = IdeaScore(
        name="TaskFlow AI",
        score=75,
        rationale="Targets solo founders with workflow automation needs",
        risks=[],
        signals={}
    )
    validated_pains = [
        {"problem": "Manual task tracking is inefficient"},
        {"problem": "Context switching kills productivity"},
        {"problem": "No unified workflow management"}
    ]
    
    hypothesis = pipeline._generate_validation_hypothesis(topic, top_idea, validated_pains)
    
    # Check that hypothesis contains expected elements (more flexible check)
    assert "Solo founders" in hypothesis["target_segment"] or "solo founders" in hypothesis["target_segment"].lower()
    assert "inefficient workflows" in hypothesis["key_problem"].lower()
    assert hypothesis["solution"] == "TaskFlow AI"
    assert "15%" in hypothesis["success_metric"]
    assert hypothesis["risk_level"] == "MEDIUM"
    assert hypothesis["confidence"] == 65


def test_generate_ab_test_plan():
    """Test A/B test plan generation."""
    settings = Settings()
    pipeline = VenturePipeline(settings)
    
    hypothesis = {
        "target_segment": "Solo founders",
        "key_problem": "inefficient workflows"
    }
    top_idea = IdeaScore(
        name="TaskFlow AI",
        score=75,
        rationale="Targets solo founders",
        risks=[],
        signals={}
    )
    
    test_plan = pipeline._generate_ab_test_plan(hypothesis, top_idea)
    
    assert test_plan["duration_days"] == 7
    assert test_plan["traffic_split"] == "50/50"
    assert "Control - MVP Features" in test_plan["variants"]["A"]["name"]
    assert "Enhanced Value Prop" in test_plan["variants"]["B"]["name"]
    assert len(test_plan["success_criteria"]) == 3


def test_generate_landing_copy():
    """Test landing page copy generation."""
    settings = Settings()
    pipeline = VenturePipeline(settings)
    
    hypothesis = {
        "target_segment": "Solo founders",
        "key_problem": "inefficient workflows"
    }
    top_idea = IdeaScore(
        name="TaskFlow AI",
        score=75,
        rationale="Targets solo founders",
        risks=[],
        signals={}
    )
    topic = "AI productivity tools"
    
    landing = pipeline._generate_landing_copy(hypothesis, top_idea, topic)
    
    assert "TaskFlow AI" in landing["headline"]
    assert "Solo founders" in landing["headline"]
    assert landing["cta_primary"] == "Commencer l'essai gratuit - 7 jours"
    assert landing["pricing"]["trial"] == "Gratuit 7 jours"
    assert len(landing["key_benefits"]) == 3
    assert len(landing["faq_items"]) == 2


def test_generate_outreach_messages():
    """Test outreach messages generation."""
    settings = Settings()
    pipeline = VenturePipeline(settings)
    
    hypothesis = {
        "target_segment": "Solo founders",
        "key_problem": "inefficient workflows"
    }
    top_idea = IdeaScore(
        name="TaskFlow AI",
        score=75,
        rationale="Targets solo founders",
        risks=[],
        signals={}
    )
    competitors = []
    
    messages = pipeline._generate_outreach_messages(hypothesis, top_idea, competitors)
    
    assert len(messages) == 3
    assert messages[0]["channel"] == "Email - Cold Outreach"
    assert messages[1]["channel"] == "LinkedIn - Message direct"
    assert messages[2]["channel"] == "Communauté - Post engagement"
    assert "Aide pour" in messages[0]["subject"]
    assert "Solution pour" in messages[1]["subject"]


def test_generate_target_kpis():
    """Test KPI generation for validation sprint."""
    settings = Settings()
    pipeline = VenturePipeline(settings)
    
    hypothesis = {
        "target_segment": "Solo founders",
        "key_problem": "inefficient workflows"
    }
    topic = "AI productivity tools"
    
    kpis = pipeline._generate_target_kpis(hypothesis, topic)
    
    # Check primary KPIs
    assert kpis["primary_kpis"]["conversion_rate"]["target"] == "15%"
    assert kpis["primary_kpis"]["activation_rate"]["target"] == "60%"
    assert kpis["primary_kpis"]["retention_day_7"]["target"] == "40%"
    
    # Check secondary KPIs
    assert kpis["secondary_kpis"]["engagement_time"]["target"] == "2+ minutes"
    assert kpis["secondary_kpis"]["feature_adoption"]["target"] == "3+ fonctionnalités"
    assert kpis["secondary_kpis"]["nps_score"]["target"] == "+40"
    
    # Check success criteria
    assert "Conversion > 10%" in kpis["success_criteria"]["minimum_viable"]
    assert "Conversion > 15%" in kpis["success_criteria"]["target_achieved"]


def test_validation_sprint_output_integration():
    """Test complete validation sprint output generation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Setup
        settings = Settings()
        settings.runs_dir = tmp_path / "runs"
        settings.data_dir = tmp_path / "data"
        settings.config_dir = tmp_path / "configs"
        
        # Create directories
        settings.runs_dir.mkdir(parents=True, exist_ok=True)
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        settings.config_dir.mkdir(parents=True, exist_ok=True)
        
        pipeline = VenturePipeline(settings)
        run_id = "test_validation_sprint"
        run_dir = settings.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock manager
        pipeline.manager = Mock()
        pipeline.manager.write_json = Mock()
        pipeline.manager.write_artifact = Mock()
        pipeline._log_progress = Mock()
        
        # Test data
        topic = "AI productivity tools"
        top_idea = IdeaScore(
            name="TaskFlow AI",
            score=75,
            rationale="Targets solo founders with workflow automation",
            risks=[],
            signals={}
        )
        validated_pains = [{"problem": "Inefficient workflows"}]
        competitor_candidates = []
        
        # Generate validation sprint output
        output = pipeline._generate_validation_sprint_output(
            run_id, topic, top_idea, validated_pains, competitor_candidates
        )
        
        # Verify output structure
        assert output["mode"] == "validation_sprint"
        assert output["duration_days"] == 7
        assert "hypothesis" in output
        assert "test_plan" in output
        assert "landing_page" in output
        assert "outreach_messages" in output
        assert "target_kpis" in output
        assert "next_steps" in output
        assert len(output["next_steps"]) == 4
        
        # Verify JSON was written
        pipeline.manager.write_json.assert_called_once_with(
            run_id, "validation_sprint_output.json", output
        )
        
        # Verify markdown was written
        pipeline.manager.write_artifact.assert_called_once()
        artifact_call_args = pipeline.manager.write_artifact.call_args
        assert artifact_call_args[0][0] == run_id
        assert artifact_call_args[0][1] == "validation_sprint_plan.md"
        
        # Verify logging
        pipeline._log_progress.assert_called()
        log_call_args = pipeline._log_progress.call_args
        assert "Validation Sprint output generated" in log_call_args[0][1]


def test_execution_mode_parameter_in_ui():
    """Test that execution mode parameter is properly passed to pipeline."""
    # This would be tested in the UI integration
    # For now, we test the profile resolution logic
    settings = Settings()
    pipeline = VenturePipeline(settings)
    
    # Test different execution modes
    standard_profile = pipeline._resolve_execution_profile("standard", False)
    fast_profile = pipeline._resolve_execution_profile("fast", True)
    validation_profile = pipeline._resolve_execution_profile("validation_sprint", False)
    
    assert standard_profile["name"] == "standard"
    assert fast_profile["name"] == "quick"  # Fast mode maps to quick profile
    assert validation_profile["name"] == "validation_sprint"
    assert validation_profile["output_mode"] == "execution_focused"


if __name__ == "__main__":
    pytest.main([__file__])
