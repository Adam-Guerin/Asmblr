from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.core.llm import LLMClient
from app.loop.runner import LoopRunner
from app.loop.schemas import LoopConfig


@dataclass
class RalphConfig:
    prd_path: Path
    progress_path: Path
    max_iter: int
    tests_command: str
    dry_run: bool
    approve_mode: str
    tail_lines: int


class RalphLoopError(Exception):
    pass


class RalphLoop:
    def __init__(self, settings: Settings, config: RalphConfig) -> None:
        self.settings = settings
        self.config = config
        self.repo_root = Path.cwd()

    def run(self) -> int:
        self._ensure_inputs()
        self._ensure_branch()
        completed = 0

        for _ in range(self.config.max_iter):
            prd = self._load_prd()
            story, story_idx = self._select_story(prd)
            if story is None:
                logger.info("<promise>COMPLETE</promise>")
                return 0

            goal = self._render_goal(prd, story)
            loop_config = LoopConfig(
                goal=goal,
                max_iter=1,
                tests_command=self._resolve_tests_command(prd),
                dry_run=self.config.dry_run,
                approve_mode=self.config.approve_mode,
            )
            plan_llm = LLMClient(self.settings.ollama_base_url, self.settings.general_model)
            patch_llm = LLMClient(self.settings.ollama_base_url, self.settings.code_model)
            runner = LoopRunner(self.settings, loop_config, plan_llm=plan_llm, patch_llm=patch_llm)
            result = runner.run()

            status = result.status
            self._append_progress(prd, story, status, result.run_id, result.run_dir)
            if status == "completed" and not self.config.dry_run:
                self._mark_story_passed(prd, story_idx)
                self._commit_prd_update(story)
                completed += 1
            else:
                return 1

        return 0 if completed else 1

    def _ensure_inputs(self) -> None:
        if not self.config.prd_path.exists():
            raise RalphLoopError(
                f"Missing {self.config.prd_path}. Create it (see prd.json.example)."
            )
        if not self.config.progress_path.exists():
            self.config.progress_path.write_text(
                "# Ralph progress log\n\n", encoding="utf-8"
            )

    def _load_prd(self) -> dict:
        return json.loads(self.config.prd_path.read_text(encoding="utf-8"))

    def _save_prd(self, prd: dict) -> None:
        self.config.prd_path.write_text(json.dumps(prd, indent=2), encoding="utf-8")

    def _stories_key(self, prd: dict) -> str:
        for key in ("stories", "userStories", "tasks", "items"):
            if isinstance(prd.get(key), list):
                return key
        raise RalphLoopError("PRD missing stories list (stories/userStories/tasks/items).")

    def _select_story(self, prd: dict) -> tuple[dict | None, int | None]:
        key = self._stories_key(prd)
        stories = prd.get(key, [])
        pending: list[tuple[int, int, dict]] = []
        for idx, story in enumerate(stories):
            if story.get("passes") is True:
                continue
            priority = story.get("priority")
            priority_val = int(priority) if isinstance(priority, int) or str(priority).isdigit() else 9999
            pending.append((priority_val, idx, story))
        if not pending:
            return None, None
        pending.sort(key=lambda item: (item[0], item[1]))
        _, idx, story = pending[0]
        return story, idx

    def _render_goal(self, prd: dict, story: dict) -> str:
        progress_tail = self._tail_progress()
        criteria = self._normalize_list(
            story.get("acceptanceCriteria")
            or story.get("acceptance")
            or story.get("criteria")
        )
        criteria_block = "\n".join(f"- {item}" for item in criteria) or "- (none provided)"
        description = story.get("description") or story.get("details") or ""
        story_id = story.get("id") or story.get("key") or "story"
        title = story.get("title") or story.get("name") or "Untitled story"
        return (
            "You are Ralph Loop. Each iteration is a fresh context.\n"
            "Do NOT edit prd.json or progress.txt; the orchestrator handles that.\n\n"
            f"Story ID: {story_id}\n"
            f"Title: {title}\n"
            f"Description: {description}\n"
            "Acceptance criteria:\n"
            f"{criteria_block}\n\n"
            "Recent progress (tail):\n"
            f"{progress_tail}\n"
        )

    def _tail_progress(self) -> str:
        text = self.config.progress_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        if len(lines) <= self.config.tail_lines:
            return text.strip()
        return "\n".join(lines[-self.config.tail_lines :]).strip()

    def _normalize_list(self, value: Any) -> list[str]:
        if not value:
            return []
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        return [str(value)]

    def _append_progress(self, prd: dict, story: dict, status: str, run_id: str, run_dir: Path) -> None:
        story_id = story.get("id") or story.get("key") or "story"
        title = story.get("title") or story.get("name") or "Untitled story"
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        tests_cmd = self._resolve_tests_command(prd)
        entry = [
            f"## {timestamp} - {story_id} {title}",
            f"Status: {status}",
            f"Run: {run_id}",
            f"Tests: {tests_cmd}",
            f"Run dir: {run_dir}",
            "",
        ]
        with self.config.progress_path.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(entry))

    def _mark_story_passed(self, prd: dict, story_idx: int) -> None:
        key = self._stories_key(prd)
        story = prd[key][story_idx]
        story["passes"] = True
        story["updatedAt"] = datetime.utcnow().isoformat()
        prd[key][story_idx] = story
        self._save_prd(prd)

    def _resolve_tests_command(self, prd: dict) -> str:
        override = prd.get("testCommand") or prd.get("qualityChecks")
        if isinstance(override, str) and override.strip():
            return override.strip()
        if isinstance(override, list) and override:
            return " && ".join(item for item in override if isinstance(item, str))
        return self.config.tests_command

    def _ensure_branch(self) -> None:
        prd = self._load_prd()
        branch = prd.get("branchName")
        self._ensure_clean_worktree()
        if not branch:
            return
        try:
            subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                check=True,
                capture_output=True,
                cwd=self.repo_root,
            )
        except subprocess.CalledProcessError:
            return
        exists = subprocess.run(
            ["git", "rev-parse", "--verify", branch],
            check=False,
            capture_output=True,
            cwd=self.repo_root,
        )
        if exists.returncode == 0:
            subprocess.run(["git", "checkout", branch], check=True, cwd=self.repo_root)
        else:
            subprocess.run(["git", "checkout", "-b", branch], check=True, cwd=self.repo_root)

    def _ensure_clean_worktree(self) -> None:
        try:
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                check=True,
                capture_output=True,
                text=True,
                cwd=self.repo_root,
            )
        except subprocess.CalledProcessError as exc:
            raise RalphLoopError(f"Git status failed: {exc}") from exc
        if status.stdout.strip():
            raise RalphLoopError("Git worktree is dirty; commit or stash before running Ralph loop.")

    def _commit_prd_update(self, story: dict) -> None:
        story_id = story.get("id") or story.get("key") or "story"
        try:
            subprocess.run(
                ["git", "add", str(self.config.prd_path), str(self.config.progress_path)],
                check=True,
                cwd=self.repo_root,
            )
            subprocess.run(
                ["git", "commit", "-m", f"ralph: mark {story_id} passed"],
                check=True,
                cwd=self.repo_root,
            )
        except subprocess.CalledProcessError:
            pass


def run_ralph_loop(settings: Settings, config: RalphConfig) -> int:
    loop = RalphLoop(settings, config)
    return loop.run()
