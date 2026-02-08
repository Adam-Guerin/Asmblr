from __future__ import annotations

import json
import subprocess
from pathlib import Path
from collections.abc import Sequence

from loguru import logger

from app.core.models import IdeaScore


class ProjectBuilder:
    def __init__(
        self,
        project_dir: Path,
        topic: str,
        idea: IdeaScore,
        vision: str,
        roadmap: Sequence[str] | None,
        stack: str,
        tech_spec: str,
        opportunities: Sequence[dict] | None = None,
    ) -> None:
        self.project_dir = project_dir
        self.topic = topic
        self.idea = idea
        self.vision = vision.strip()
        self.roadmap = list(roadmap or [])
        self.stack = stack.strip() or "Next.js frontend + FastAPI backend + SQLite"
        self.tech_spec = tech_spec.strip()
        self.opportunities = list(opportunities or [])

    def build(self) -> Path:
        self.project_dir.mkdir(parents=True, exist_ok=True)
        (self.project_dir / "vision_roadmap.md").write_text(
            self._compose_vision_doc(), encoding="utf-8"
        )
        self._scaffold_app()
        self._init_git_repo()
        return self.project_dir

    def _compose_vision_doc(self) -> str:
        lines: list[str] = [
            "# Vision & Roadmap",
            "",
            "## Vision",
            self.vision or self.idea.rationale or "Top idea vision pending.",
            "",
            "## Stack",
            self.stack,
            "",
        ]
        lines.extend(self._format_roadmap())
        lines.append("")
        lines.extend(self._format_opportunities())
        lines.append("")
        lines.append("## Technical Spec Highlights")
        for snippet in self._snippet_lines(self.tech_spec, 4):
            lines.append(f"- {snippet}")
        lines.append("")
        lines.append("## App Scaffold")
        lines.append(f"- Project name: {self.idea.name}")
        lines.append(f"- Topic context: {self.topic}")
        return "\n".join(line for line in lines if line is not None).rstrip() + "\n"

    def _format_roadmap(self) -> list[str]:
        lines: list[str] = ["## Roadmap"]
        if not self.roadmap:
            lines.append("1. Validate the confirmed pains and hypotheses.")
            lines.append("2. Build the minimal MVP artifacts using the chosen stack.")
            lines.append("3. Measure signals and iterate.")
            return lines
        for idx, step in enumerate(self.roadmap, start=1):
            lines.append(f"{idx}. {step}")
        return lines

    def _format_opportunities(self) -> list[str]:
        lines: list[str] = ["## Opportunities"]
        if not self.opportunities:
            lines.append("- None captured yet.")
            return lines
        for opportunity in self.opportunities[:3]:
            idea = opportunity.get("idea", {})
            score = opportunity.get("score", {})
            name = idea.get("name") or opportunity.get("idea_name") or self.idea.name
            score_value = score.get("score") or score.get("value") or "n/a"
            lines.append(f"- {name} (score: {score_value})")
        return lines

    def _snippet_lines(self, text: str, limit: int) -> list[str]:
        return [line.strip() for line in text.splitlines() if line.strip()][:limit]

    def _scaffold_app(self) -> None:
        app_dir = self.project_dir / "app"
        frontend_dir = app_dir / "frontend"
        backend_dir = app_dir / "backend"
        frontend_dir.mkdir(parents=True, exist_ok=True)
        backend_dir.mkdir(parents=True, exist_ok=True)
        stack_config = {
            "stack": self.stack,
            "topic": self.topic,
            "idea": self.idea.name,
        }
        (app_dir / "stack_config.json").write_text(json.dumps(stack_config, indent=2), encoding="utf-8")
        (frontend_dir / "README.md").write_text(
            self._frontend_readme(), encoding="utf-8"
        )
        (frontend_dir / "index.html").write_text(self._frontend_html(), encoding="utf-8")
        (backend_dir / "main.py").write_text(self._backend_main(), encoding="utf-8")
        (backend_dir / "requirements.txt").write_text(self._backend_requirements(), encoding="utf-8")

    def _init_git_repo(self) -> None:
        if (self.project_dir / ".git").exists():
            return
        try:
            subprocess.run(["git", "init"], cwd=self.project_dir, check=True, capture_output=True, text=True)
            subprocess.run(["git", "add", "."], cwd=self.project_dir, check=True, capture_output=True, text=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial MVP scaffold"],
                cwd=self.project_dir,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            logger.warning("Git scaffolding failed: {}", exc)

    def _frontend_readme(self) -> str:
        target_user = getattr(self.idea, "target_user", "customer")
        problem = getattr(self.idea, "problem", "key problem")
        return (
            f"# Frontend Scaffold\n"
            f"Stack target: {self.stack}\n\n"
            f"Focus on the {target_user} who is burdened by {problem}.\n"
            "Components:\n"
            "- Landing experience with clear CTA\n"
            "- Dashboard for monitoring signal quality\n"
        )

    def _frontend_html(self) -> str:
        return (
            "<!DOCTYPE html>\n"
            "<html lang=\"en\">\n"
            "<head>\n"
            "  <meta charset=\"UTF-8\" />\n"
            "  <title>Prototype</title>\n"
            "</head>\n"
            "<body>\n"
            f"  <h1>{self.idea.name}</h1>\n"
            f"  <p>{self.vision or self.idea.rationale}</p>\n"
            f"  <p>Stack: {self.stack}</p>\n"
            "</body>\n"
            "</html>\n"
        )

    def _backend_main(self) -> str:
        if "fastapi" in self.stack.lower():
            return (
                "from fastapi import FastAPI\n\n"
                "app = FastAPI()\n\n"
                "@app.get('/')\n"
                "def root():\n"
                f"    return {{'project': '{self.idea.name}', 'status': 'scaffolded', 'stack': '{self.stack}'}}\n"
            )
        return (
            "def main():\n"
            f"    logger.info('Project {self.idea.name} scaffolded with stack: {self.stack}')\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        )

    def _backend_requirements(self) -> str:
        if "fastapi" in self.stack.lower():
            return "fastapi\nuvicorn\n"
        return "click\n"
