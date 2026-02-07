#!/usr/bin/env python3
"""
Demo script to show the collection actions rule in action.

This script demonstrates how the rule automatically proposes collection actions
when critical fields are marked as "unknown" in the data source.
"""

import json
import tempfile
from pathlib import Path

from app.core.pipeline import VenturePipeline
from app.core.config import Settings


def main():
    """Demonstrate the collection actions rule."""
    print("🚀 Asmblr Collection Actions Rule Demo")
    print("=" * 50)
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Setup minimal configuration
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
        run_id = "demo_run_001"
        topic = "AI productivity tools for remote teams"
        
        # Create run directory
        run_dir = settings.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Run directory: {run_dir}")
        print(f"🎯 Topic: {topic}")
        print()
        
        # Scenario 1: Multiple unknown critical fields
        print("🔍 Scenario 1: Multiple unknown critical fields")
        print("-" * 40)
        
        data_source_scenario1 = {
            "pages": "unknown",
            "pains": "real", 
            "competitors": "unknown",
            "seeds": "none"
        }
        
        print("Data source status:")
        for field, status in data_source_scenario1.items():
            emoji = "❓" if status == "unknown" else "✅" if status == "real" else "⚪"
            print(f"  {emoji} {field}: {status}")
        
        print()
        
        decision_missing = []
        pipeline._propose_collection_actions_for_unknown_fields(
            run_id, data_source_scenario1, topic, decision_missing
        )
        
        # Read and display the generated collection actions
        collection_actions_file = run_dir / "collection_actions.json"
        if collection_actions_file.exists():
            with open(collection_actions_file, 'r', encoding='utf-8') as f:
                collection_actions = json.load(f)
            
            print("📋 Generated Collection Actions:")
            for action in collection_actions["actions"]:
                priority_emoji = "🔴" if action["priority"] == "HIGH" else "🟡"
                print(f"  {priority_emoji} {action['field'].upper()}")
                print(f"     Issue: {action['source_missing']}")
                print(f"     Next step: {action['next_step']}")
                print(f"     Impact: {action['estimated_impact']}")
                print()
        
        print("📝 Added to decision missing:")
        for missing in decision_missing:
            print(f"  • {missing}")
        
        print("\n" + "=" * 50)
        
        # Scenario 2: All fields real (no actions needed)
        print("🔍 Scenario 2: All critical fields are real")
        print("-" * 40)
        
        data_source_scenario2 = {
            "pages": "real",
            "pains": "real", 
            "competitors": "real",
            "seeds": "seed"
        }
        
        print("Data source status:")
        for field, status in data_source_scenario2.items():
            emoji = "✅" if status == "real" else "⚪"
            print(f"  {emoji} {field}: {status}")
        
        print()
        
        decision_missing.clear()
        pipeline._propose_collection_actions_for_unknown_fields(
            run_id, data_source_scenario2, topic, decision_missing
        )
        
        # Check if no collection actions were generated
        collection_actions_file = run_dir / "collection_actions.json"
        if collection_actions_file.exists():
            print("❌ Unexpected: Collection actions were generated!")
        else:
            print("✅ Correct: No collection actions needed for all-real fields")
        
        print(f"\n📝 Decision missing entries: {len(decision_missing)}")
        
        print("\n" + "=" * 50)
        print("🎯 Rule Summary:")
        print("• Automatically detects unknown critical fields")
        print("• Proposes specific collection actions for each field")
        print("• Prioritizes actions based on impact")
        print("• Integrates with existing decision pipeline")
        print("• Creates structured JSON output for downstream processing")


if __name__ == "__main__":
    main()
