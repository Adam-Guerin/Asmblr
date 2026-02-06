import json
from pathlib import Path

from app.core.models import IdeaScore
from app.project_build import ProjectBuilder


def test_project_builder_creates_documents_and_app(tmp_path: Path) -> None:
    idea = IdeaScore(name="Signal Vault", score=92, rationale="Turn noise into decisions.", risks=[], signals={})
    project_dir = tmp_path / "project_build"
    builder = ProjectBuilder(
        project_dir=project_dir,
        topic="Structured signal engine",
        idea=idea,
        vision="Make signal extraction repeatable and auditable.",
        roadmap=["Validate pains with interviews", "Ship MVP frontend + backend", "Measure signal quality"],
        stack="Next.js + FastAPI + SQLite",
        tech_spec="## Stack: Next.js + FastAPI\n## API: FastAPI REST",
        opportunities=[{"idea": {"name": "Signal Vault"}, "score": {"score": 92}}],
    )
    builder.build()

    doc = (project_dir / "vision_roadmap.md").read_text()
    assert "Vision" in doc
    assert "Roadmap" in doc
    assert "Next.js + FastAPI + SQLite" in doc

    frontend_readme = (project_dir / "app" / "frontend" / "README.md").read_text()
    assert "Stack target" in frontend_readme

    backend_main = (project_dir / "app" / "backend" / "main.py").read_text()
    assert "FastAPI" in backend_main

    stack_config = json.loads((project_dir / "app" / "stack_config.json").read_text())
    assert stack_config["stack"] == "Next.js + FastAPI + SQLite"
    assert (project_dir / ".git").exists()
