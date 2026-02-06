from __future__ import annotations

import difflib
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from loguru import logger

from app.core.config import Settings
from app.core.llm import LLMClient
from app.mvp.ui_lint import count_components, count_pages, run_ui_lint


CycleInput = Tuple[str, str, str]
BuildRunner = Callable[[str, Path, int], Tuple[bool, str]]
TestRunner = Callable[[str, Path, int], Tuple[bool, str]]


class MVPProgressionError(Exception):
    pass


class MVPProgression:
    CYCLES: List[CycleInput] = [
        ("foundation", "foundation_prompt.txt", "Establish layout, core pages, navigation, and a buildable baseline."),
        ("ux", "ux_prompt.txt", "Apply typography hierarchy, spacing rhythm, and component consistency."),
        ("polish", "polish_prompt.txt", "Add loading/empty/error states, toasts, and microcopy polish."),
    ]

    def __init__(
        self,
        run_id: str,
        run_dir: Path,
        settings: Settings,
        build_runner: Optional[BuildRunner] = None,
        test_runner: Optional[TestRunner] = None,
        llm_client: Optional[LLMClient] = None,
        max_auto_fixes: int = 5,
        cycle_keys: list[str] | None = None,
        llm_enabled: bool | None = None,
    ) -> None:
        self.run_id = run_id
        self.run_dir = Path(run_dir)
        self.settings = settings
        self.build_runner = build_runner or self._make_command_runner("build", self.settings.mvp_build_command)
        self.test_runner = test_runner or self._make_command_runner("test", self.settings.mvp_test_command)
        self.install_runner = self._make_command_runner("install", self.settings.mvp_install_command)
        self.max_auto_fixes = max_auto_fixes
        self.cycles_dir = self.run_dir / "mvp_cycles"
        self.repo_dir = self.run_dir / "mvp_repo"
        self.prompts_dir = Path(__file__).resolve().parents[1] / "prompts" / "mvp"
        self.last_build_log = ""
        self.last_test_log = ""
        self.last_build_ok = False
        self.last_ui_lint_ok = False
        self._install_done = False
        self.llm_enabled = (not settings.mvp_disable_llm) if llm_enabled is None else llm_enabled
        self.llm_client = None
        if self.llm_enabled:
            self.llm_client = llm_client or LLMClient(settings.ollama_base_url, settings.code_model)
        self.dev_command = settings.mvp_dev_command
        self.dev_base_url = settings.mvp_dev_base_url.rstrip("/")
        self.dev_startup_timeout = settings.mvp_dev_startup_timeout
        self.dev_check_paths = [
            path.strip() for path in settings.mvp_dev_check_paths.split(",") if path.strip()
        ]
        self.force_autofix = settings.mvp_force_autofix
        self._autofix_marker = self.repo_dir / ".asmblr" / "autofix_stability_ok"
        self._steering_file = self.run_dir / "mvp_steering.jsonl"
        self._secret_scan_cache: list[dict] | None = None
        self._security_events: list[str] = []
        allowed = set(cycle_keys or [cycle_key for cycle_key, *_ in self.CYCLES])
        self.cycle_definitions = [
            (cycle_key, prompt, objective)
            for cycle_key, prompt, objective in self.CYCLES
            if cycle_key in allowed
        ]
        self.cycle_results: list[dict] = []

    def run(self) -> None:
        self.generate_base_repo()
        automation_summary = {
            "run_id": self.run_id,
            "started_at": datetime.utcnow().isoformat(),
            "cycle_plan": [cycle_key for cycle_key, *_ in self.cycle_definitions],
            "cycles": [],
            "status": "in_progress",
        }
        self._write_automation_summary(automation_summary)
        for idx, (cycle_key, prompt_file, objective) in enumerate(self.cycle_definitions, start=1):
            cycle_started_at = datetime.utcnow().isoformat()
            cycle_dir = self.cycles_dir / f"cycle_{idx}_{cycle_key}"
            cycle_dir.mkdir(parents=True, exist_ok=True)
            self._init_cycle_automation(cycle_dir, cycle_key, idx, cycle_started_at)
            plan = self.plan_cycle(cycle_key, objective, prompt_file, cycle_dir)
            self.apply_patch(cycle_key, cycle_dir, plan, prompt_file)
            if cycle_key == "foundation":
                self._ensure_foundation_basics()
                self.run_install(cycle_dir)
            build_ok, build_log = self.run_build(cycle_key, cycle_dir, attempt=1)
            test_ok, test_log = self.run_tests(cycle_key, cycle_dir, attempt=1)
            ui_lint_ok, _ = self.run_ui_lint(cycle_key, cycle_dir, attempt=1)
            smoke_ok = True
            if cycle_key == "foundation":
                smoke_ok = self.run_smoke_checks(cycle_dir)
            self.last_build_log = build_log
            self.last_test_log = test_log
            self.last_build_ok = build_ok
            self.last_ui_lint_ok = ui_lint_ok
            checks_ok = self.verify_cycle_requirements(cycle_key, cycle_dir)
            success = build_ok and test_ok and smoke_ok and checks_ok and ui_lint_ok
            attempts = 1
            failure_reason = None
            auto_fix_attempted = False
            auto_fix_attempts = 0
            if not success:
                failure_reason = self._derive_failure_reason(build_ok, test_ok, checks_ok, smoke_ok)
                auto_success, extra_attempts, auto_reason = self.auto_fix_loop(
                    cycle_key, cycle_dir
                )
                auto_fix_attempted = True
                auto_fix_attempts = extra_attempts
                attempts += extra_attempts
                success = auto_success
                if auto_reason:
                    failure_reason = auto_reason
                elif auto_success:
                    failure_reason = None
            status = "pass" if success else "fail"
            self._write_verdict(
                cycle_dir,
                cycle_key,
                success,
                attempts,
                failure_reason,
                auto_fix_attempted,
                build_ok=self.last_build_ok,
                ui_lint_ok=self.last_ui_lint_ok,
            )
            cycle_finished_at = datetime.utcnow().isoformat()
            automation_entry = self._write_cycle_automation(
                cycle_dir,
                cycle_key,
                idx,
                cycle_started_at,
                cycle_finished_at,
                status,
                attempts,
                auto_fix_attempted,
                auto_fix_attempts,
            )
            self.cycle_results.append(
                {"cycle": cycle_key, "status": status, "attempts": attempts, "reason": failure_reason}
            )
            automation_summary["cycles"].append(automation_entry)
            self._write_automation_summary(automation_summary)
            if not success and cycle_key == "foundation":
                raise MVPProgressionError(
                    f"{cycle_key} cycle failed after {self.max_auto_fixes} fix attempts."
                )
        automation_summary["status"] = "complete"
        automation_summary["finished_at"] = datetime.utcnow().isoformat()
        self._write_automation_summary(automation_summary)

    def plan_cycle(self, cycle_key: str, objective: str, prompt_file: str, cycle_dir: Path) -> str:
        prompt_path = self.prompts_dir / prompt_file
        prompt_text = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
        steering_context = self._format_manual_steering_context()
        checklist = self._cycle_checklist(cycle_key)
        checklist_block = "\n".join([f"- [ ] {item}" for item in checklist]) or "- [ ] Review cycle objective"
        content = (
            f"# {cycle_key.title()} cycle plan\n\n"
            f"## Objective\n{objective}\n\n"
            f"## Checklist\n{checklist_block}\n\n"
            f"## Manual steering\n{steering_context}\n\n"
            f"## Prompt context\n{prompt_text}\n\n"
            f"## Last build log\n{self.last_build_log or 'N/A'}\n\n"
            f"## Last test log\n{self.last_test_log or 'N/A'}\n"
        )
        (cycle_dir / "plan.md").write_text(content, encoding="utf-8")
        return content

    def _cycle_checklist(self, cycle_key: str) -> list[str]:
        if cycle_key == "foundation":
            return [
                "Layout scaffold builds",
                "Core pages + navigation present",
                "Landing + app shell pages present",
                "Build and UI lint pass",
            ]
        if cycle_key == "ux":
            return [
                "Typography hierarchy enforced",
                "Spacing rhythm consistent",
                "Component styles aligned",
            ]
        if cycle_key == "polish":
            return [
                "Loading/empty/error states present",
                "Toasts + microcopy verified",
                "Subtle motion or polish pass",
            ]
        return []

    def apply_patch(self, cycle_key: str, cycle_dir: Path, plan: str, prompt_file: str) -> None:
        patch_path = cycle_dir / "patch.diff"
        if cycle_key == "foundation":
            diff = self._generate_foundation_patch(prompt_file, plan)
            patch_path.write_text(diff, encoding="utf-8")
            self._write_patch_log(cycle_dir, cycle_key, prompt_file, plan, diff)
            self._apply_patch_to_repo(diff)
        else:
            diff = self._generate_cycle_patch(cycle_key)
            patch_path.write_text(diff, encoding="utf-8")
            self._write_patch_log(cycle_dir, cycle_key, prompt_file, plan, diff)

    def run_build(self, cycle_key: str, cycle_dir: Path, attempt: int) -> Tuple[bool, str]:
        result, log = self.build_runner(cycle_key, cycle_dir, attempt)
        log_path = cycle_dir / "build.log"
        log_path.write_text(log, encoding="utf-8")
        self._record_cycle_step(
            cycle_dir=cycle_dir,
            step="build",
            attempt=attempt,
            ok=result,
            log_name="build.log",
        )
        return result, log

    def run_tests(self, cycle_key: str, cycle_dir: Path, attempt: int) -> Tuple[bool, str]:
        result, log = self.test_runner(cycle_key, cycle_dir, attempt)
        log_path = cycle_dir / "test.log"
        log_path.write_text(log, encoding="utf-8")
        self._record_cycle_step(
            cycle_dir=cycle_dir,
            step="test",
            attempt=attempt,
            ok=result,
            log_name="test.log",
        )
        return result, log

    def run_ui_lint(self, cycle_key: str, cycle_dir: Path, attempt: int) -> Tuple[bool, str]:
        result = run_ui_lint(self.repo_dir, cycle_dir)
        ok = bool(result.get("ok"))
        self._record_cycle_step(
            cycle_dir=cycle_dir,
            step="ui_lint",
            attempt=attempt,
            ok=ok,
            log_name="ui_lint.json",
        )
        self._write_cycle_alias(cycle_key, cycle_dir, "ui_lint.json")
        summary = f"UI lint {'pass' if ok else 'fail'}"
        return ok, summary

    def run_install(self, cycle_dir: Path) -> Tuple[bool, str]:
        if self._install_done:
            return True, "Install skipped (already completed)."
        result, log = self.install_runner("foundation", cycle_dir, attempt=1)
        log_path = cycle_dir / "install.log"
        log_path.write_text(log, encoding="utf-8")
        self._record_cycle_step(
            cycle_dir=cycle_dir,
            step="install",
            attempt=1,
            ok=result,
            log_name="install.log",
        )
        self._install_done = result
        return result, log

    def auto_fix_loop(
        self,
        cycle_key: str,
        cycle_dir: Path,
    ) -> Tuple[bool, int, str | None]:
        for attempt_index in range(1, self.max_auto_fixes + 1):
            attempt_number = attempt_index + 1
            fix_path = cycle_dir / f"fix_{attempt_index}.log"
            fix_path.write_text(
                f"Auto-fix attempt {attempt_index} for {cycle_key}", encoding="utf-8"
            )
            self._attempt_auto_fix(cycle_key, cycle_dir, attempt_index)
            build_ok, build_log = self.run_build(cycle_key, cycle_dir, attempt=attempt_number)
            test_ok, test_log = self.run_tests(cycle_key, cycle_dir, attempt=attempt_number)
            ui_lint_ok, _ = self.run_ui_lint(cycle_key, cycle_dir, attempt=attempt_number)
            smoke_ok = True
            if cycle_key == "foundation":
                smoke_ok = self.run_smoke_checks(cycle_dir, attempt_index)
            self.last_build_log = build_log
            self.last_test_log = test_log
            self.last_build_ok = build_ok
            self.last_ui_lint_ok = ui_lint_ok
            checks_ok = self.verify_cycle_requirements(cycle_key, cycle_dir)
            if build_ok and test_ok and smoke_ok and checks_ok and ui_lint_ok:
                return True, attempt_index, None
        return False, self.max_auto_fixes, "Auto-fix loop did not resolve cycle failure."

    def _derive_failure_reason(
        self, build_ok: bool, test_ok: bool, checks_ok: bool, smoke_ok: bool
    ) -> str:
        if not checks_ok:
            return "cycle requirements failed"
        if not smoke_ok:
            return "smoke checks failed"
        if not build_ok and not test_ok:
            return "build and test failed"
        if not build_ok:
            return "build failed"
        if not test_ok:
            return "tests failed"
        return "cycle had unknown failure"

    def _make_command_runner(self, command_name: str, command: str) -> BuildRunner:
        def runner(cycle_key: str, cycle_dir: Path, attempt: int) -> Tuple[bool, str]:
            return self._run_shell_command(command, command_name, cycle_key, attempt)

        return runner

    def _run_shell_command(
        self, command: str, command_name: str, cycle_key: str, attempt: int
    ) -> Tuple[bool, str]:
        message = f"{command_name.title()} {cycle_key} (attempt {attempt})"
        if not command:
            return True, f"{message} skipped because MVP_{command_name.upper()}_COMMAND is empty."
        timeout_s = self.settings.mvp_build_timeout
        if command_name == "install":
            timeout_s = self.settings.mvp_install_timeout
        elif command_name == "test":
            timeout_s = self.settings.mvp_test_timeout
        try:
            proc = subprocess.run(
                command,
                cwd=self.repo_dir,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return False, f"{message} timed out after {timeout_s} seconds."
        except Exception as exc:
            return False, f"{message} execution failed: {exc}"
        output = [f"{message}", f"Command: {command}", f"Return code: {proc.returncode}"]
        if proc.stdout.strip():
            output.append("stdout:\n" + proc.stdout.strip())
        if proc.stderr.strip():
            output.append("stderr:\n" + proc.stderr.strip())
        return proc.returncode == 0, "\n".join(output)

    def generate_base_repo(self) -> None:
        self.repo_dir.mkdir(parents=True, exist_ok=True)
        readme = self.repo_dir / "README.md"
        if not readme.exists():
            readme.write_text(
                "# MVP Repository\nGenerated incrementally by Asmblr progressive cycles.",
                encoding="utf-8",
            )
        if not (self.repo_dir / "app" / "page.tsx").exists():
            try:
                from app.mvp.frontend_kit.scaffold import write_frontend_scaffold

                write_frontend_scaffold(
                    self.repo_dir,
                    "Launchpad",
                    brief="A clean launch-ready experience for early teams.",
                    style="startup_clean",
                )
            except Exception as exc:
                logger.warning("Frontend scaffold unavailable in base repo: {}", exc)

    def _write_patch_log(
        self, cycle_dir: Path, cycle_key: str, prompt_file: str, plan: str, diff: str
    ) -> None:
        log_path = cycle_dir / "patch.log"
        snippet = plan.strip().replace("\n", " ")[:600]
        log_content = (
            f"Cycle: {cycle_key}\n"
            f"Prompt: {prompt_file}\n"
            f"Plan preview: {snippet}\n\n"
            f"Diff:\n{diff}\n"
        )
        log_path.write_text(log_content, encoding="utf-8")

    def _write_verdict(
        self,
        cycle_dir: Path,
        cycle_key: str,
        success: bool,
        attempts: int,
        reason: str | None,
        auto_fix_attempted: bool,
        build_ok: bool,
        ui_lint_ok: bool,
    ) -> None:
        pages_count = count_pages(self.repo_dir)
        components_count = count_components(self.repo_dir)
        verdict = {
            "cycle": cycle_key,
            "status": "pass" if success else "fail",
            "attempts": attempts,
            "reason": reason or ("pass" if success else "unspecified failure"),
            "auto_fix_attempted": auto_fix_attempted,
            "build_ok": build_ok,
            "ui_lint_ok": ui_lint_ok,
            "pages_count": pages_count,
            "components_count": components_count,
            "timestamp": datetime.utcnow().isoformat(),
        }
        (cycle_dir / "verdict.json").write_text(json.dumps(verdict, indent=2), encoding="utf-8")
        self._write_cycle_alias(cycle_key, cycle_dir, "verdict.json")
        (cycle_dir / "autofix.log").write_text(
            "Auto-fix loop triggered." if auto_fix_attempted else "Auto-fix loop not required.",
            encoding="utf-8",
        )

    def _init_cycle_automation(
        self, cycle_dir: Path, cycle_key: str, index: int, started_at: str
    ) -> None:
        stub = {
            "cycle": cycle_key,
            "index": index,
            "status": "in_progress",
            "attempts": 0,
            "auto_fix_attempted": False,
            "auto_fix_attempts": 0,
            "started_at": started_at,
            "finished_at": None,
            "steps": [],
            "logs": {
                "build": "build.log",
                "test": "test.log",
                "ui_lint": "ui_lint.json",
                "smoke": "smoke_1.log" if cycle_key == "foundation" else None,
                "autofix": "autofix.log",
                "patch": "patch.log",
                "verdict": "verdict.json",
                "fix_logs": [],
                "fix_diffs": [],
            },
        }
        (cycle_dir / "automation.json").write_text(
            json.dumps(stub, indent=2), encoding="utf-8"
        )
        (cycle_dir / "autofix.log").write_text(
            "Auto-fix loop pending.", encoding="utf-8"
        )

    def _write_cycle_automation(
        self,
        cycle_dir: Path,
        cycle_key: str,
        index: int,
        started_at: str,
        finished_at: str,
        status: str,
        attempts: int,
        auto_fix_attempted: bool,
        auto_fix_attempts: int,
    ) -> dict:
        fix_logs = sorted(
            p.name for p in cycle_dir.glob("fix_*.log") if p.is_file()
        )
        fix_diffs = sorted(
            p.name for p in cycle_dir.glob("fix_*.diff") if p.is_file()
        )
        existing_steps = []
        automation_path = cycle_dir / "automation.json"
        if automation_path.exists():
            try:
                existing_steps = json.loads(automation_path.read_text(encoding="utf-8")).get(
                    "steps", []
                )
            except Exception:
                existing_steps = []
        automation = {
            "cycle": cycle_key,
            "index": index,
            "status": status,
            "attempts": attempts,
            "auto_fix_attempted": auto_fix_attempted,
            "auto_fix_attempts": auto_fix_attempts,
            "started_at": started_at,
            "finished_at": finished_at,
            "steps": existing_steps,
            "logs": {
                "build": "build.log",
                "test": "test.log",
                "ui_lint": "ui_lint.json",
                "smoke": "smoke_1.log" if cycle_key == "foundation" else None,
                "autofix": "autofix.log",
                "patch": "patch.log",
                "verdict": "verdict.json",
                "fix_logs": fix_logs,
                "fix_diffs": fix_diffs,
            },
        }
        (cycle_dir / "automation.json").write_text(
            json.dumps(automation, indent=2), encoding="utf-8"
        )
        return automation

    def _write_automation_summary(self, summary: dict) -> None:
        summary_path = self.run_dir / "mvp_automation_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        log_lines = [
            f"Run: {summary.get('run_id')}",
            f"Status: {summary.get('status')}",
            f"Started: {summary.get('started_at')}",
        ]
        if summary.get("finished_at"):
            log_lines.append(f"Finished: {summary.get('finished_at')}")
        if summary.get("cycle_plan"):
            log_lines.append(f"Cycle plan: {', '.join(summary['cycle_plan'])}")
        for entry in summary.get("cycles", []):
            log_lines.append(
                f"[{entry['index']}] {entry['cycle']} -> {entry['status']} "
                f"({entry['attempts']} attempt(s), auto-fix: {entry['auto_fix_attempted']})"
            )
        (self.run_dir / "mvp_automation.log").write_text(
            "\n".join(log_lines) + "\n", encoding="utf-8"
        )

    def _generate_foundation_patch(self, prompt_file: str, plan: str) -> str:
        prompt_path = self.prompts_dir / prompt_file
        instructions = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
        steering_context = self._format_manual_steering_context()
        prompt = (
            "Foundation cycle patch request:\n"
            f"{instructions}\n\n"
            f"Plan:\n{plan}\n\n"
            f"Manual steering from founder:\n{steering_context}\n\n"
            f"Repository tree snapshot:\n{self._repo_tree_snapshot()}\n\n"
            "Please respond with a git diff targeting files within mvp_repo/."
        )
        if self.llm_client and self.llm_client.available():
            try:
                return self.llm_client.generate(prompt)
            except Exception as exc:
                logger.warning("Foundation patch LLM failed: {}", exc)
        return self._default_foundation_patch()

    def _repo_tree_snapshot(self) -> str:
        if not self.repo_dir.exists():
            return "mvp_repo/ (empty)"
        files = sorted(
            str(p.relative_to(self.repo_dir))
            for p in self.repo_dir.rglob("*")
            if p.is_file()
        )
        return "\n".join(files) if files else "mvp_repo/ (empty)"

    def _default_foundation_patch(self) -> str:
        return """diff --git a/mvp_repo/foundation_notes.md b/mvp_repo/foundation_notes.md
new file mode 100644
index 0000000..e69de29
--- /dev/null
+++ b/mvp_repo/foundation_notes.md
@@ -0,0 +1,4 @@
+Foundation cycle initialized.
+Objective: the repo must have a baseline README and structure.
+This file captures the first automated addition.
+Follow-up cycles will elaborate on this scaffold.
+"""

    def _generate_cycle_patch(self, cycle_key: str) -> str:
        before = self._snapshot_repo_files()
        touched = self._sync_manual_steering_file(cycle_key)
        if cycle_key == "ux":
            touched.extend(self._apply_ux_changes())
        elif cycle_key == "polish":
            touched.extend(self._apply_polish_changes())
        after = self._snapshot_repo_files()
        return self._diff_snapshots(before, after, touched, cycle_key)

    def _load_manual_steering_messages(self, limit: int = 8) -> list[dict]:
        if not self._steering_file.exists():
            return []
        entries: list[dict] = []
        try:
            lines = self._steering_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            return []
        for line in lines:
            raw = line.strip()
            if not raw:
                continue
            payload: dict
            try:
                payload = json.loads(raw)
            except Exception:
                payload = {"message": raw}
            message = str(
                payload.get("message")
                or payload.get("prompt")
                or payload.get("text")
                or ""
            ).strip()
            if not message:
                continue
            entries.append(
                {
                    "timestamp": payload.get("timestamp") or payload.get("at") or "",
                    "author": payload.get("author") or payload.get("source") or "user",
                    "message": message,
                }
            )
        if limit <= 0:
            return entries
        return entries[-limit:]

    def _format_manual_steering_context(self, limit: int = 8) -> str:
        entries = self._load_manual_steering_messages(limit=limit)
        if not entries:
            return "No manual steering message provided."
        lines: list[str] = []
        for item in entries:
            stamp = str(item.get("timestamp") or "").strip() or "unknown-time"
            author = str(item.get("author") or "user").strip()
            message = str(item.get("message") or "").strip().replace("\n", " ")
            if len(message) > 320:
                message = message[:320].rstrip() + "..."
            lines.append(f"- [{stamp}] {author}: {message}")
        return "\n".join(lines)

    def _sync_manual_steering_file(self, cycle_key: str) -> list[str]:
        entries = self._load_manual_steering_messages(limit=20)
        if not entries:
            return []
        notes_dir = self.repo_dir / ".asmblr"
        notes_dir.mkdir(parents=True, exist_ok=True)
        notes_path = notes_dir / "steering.md"
        lines = ["# Manual steering", "", f"Cycle: {cycle_key}", ""]
        for item in entries:
            stamp = str(item.get("timestamp") or "").strip() or "unknown-time"
            author = str(item.get("author") or "user").strip()
            message = str(item.get("message") or "").strip()
            lines.append(f"- [{stamp}] {author}: {message}")
        content = "\n".join(lines).rstrip() + "\n"
        current = ""
        if notes_path.exists():
            current = notes_path.read_text(encoding="utf-8", errors="ignore")
        if current == content:
            return []
        notes_path.write_text(content, encoding="utf-8")
        return ["mvp_repo/.asmblr/steering.md"]

    def _snapshot_repo_files(self) -> dict[str, list[str]]:
        snapshot: dict[str, list[str]] = {}
        if not self.repo_dir.exists():
            return snapshot
        for path in self.repo_dir.rglob("*"):
            if not path.is_file():
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except Exception:
                continue
            rel = f"mvp_repo/{path.relative_to(self.repo_dir).as_posix()}"
            snapshot[rel] = content.splitlines(keepends=True)
        return snapshot

    def _diff_snapshots(
        self,
        before: dict[str, list[str]],
        after: dict[str, list[str]],
        touched: list[str],
        cycle_key: str,
    ) -> str:
        diffs: list[str] = []
        candidates = touched or sorted(set(before.keys()) | set(after.keys()))
        for rel in candidates:
            old = before.get(rel, [])
            new = after.get(rel, [])
            if old == new:
                continue
            diffs.append(f"diff --git a/{rel} b/{rel}")
            diffs.extend(
                difflib.unified_diff(
                    old,
                    new,
                    fromfile=f"a/{rel}",
                    tofile=f"b/{rel}",
                    lineterm="",
                )
            )
        return "\n".join(diffs) if diffs else f"--- {cycle_key} no-op (no changes)\n"

    def verify_cycle_requirements(self, cycle_key: str, cycle_dir: Path) -> bool:
        checks: list[dict] = []
        repo_root = self.repo_dir
        checks.extend(self._check_logs(cycle_dir, cycle_key))
        checks.extend(self._check_security(cycle_key, cycle_dir))
        checks.extend(self._check_automation(cycle_dir))
        checks.extend(self._check_ui_lint(cycle_dir))
        if cycle_key != "foundation":
            checks.extend(self._check_patch_diff(cycle_dir))
        if cycle_key == "foundation":
            checks.extend(self._check_foundation_repo(repo_root))
            checks.extend(self._check_foundation_smoke(cycle_dir))
        if cycle_key == "ux":
            checks.extend(self._check_ux(repo_root))
        if cycle_key == "polish":
            checks.extend(self._check_polish(repo_root))
        ok = all(item.get("ok") for item in checks) if checks else True
        evidence = {
            "cycle": cycle_key,
            "ok": ok,
            "checks": checks,
        }
        (cycle_dir / "evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        return ok

    def _check_logs(self, cycle_dir: Path, cycle_key: str) -> list[dict]:
        checks: list[dict] = []
        build_log = cycle_dir / "build.log"
        test_log = cycle_dir / "test.log"
        if build_log.exists():
            content = build_log.read_text(encoding="utf-8", errors="ignore")
            checks.append(
                {
                    "name": "build_log_clean",
                    "ok": "Return code: 0" in content and "Error:" not in content,
                    "path": "build.log",
                }
            )
        else:
            checks.append({"name": "build_log_clean", "ok": False, "path": "build.log"})
        if test_log.exists():
            content = test_log.read_text(encoding="utf-8", errors="ignore")
            checks.append(
                {
                    "name": "test_log_clean",
                    "ok": "Return code: 0" in content and "Error:" not in content,
                    "path": "test.log",
                }
            )
        else:
            checks.append({"name": "test_log_clean", "ok": False, "path": "test.log"})
        if cycle_key == "foundation":
            smoke_log = cycle_dir / "smoke_1.log"
            if smoke_log.exists():
                content = smoke_log.read_text(encoding="utf-8", errors="ignore")
                checks.append(
                    {
                        "name": "smoke_log_pass",
                        "ok": "Result: pass" in content,
                        "path": "smoke_1.log",
                    }
                )
        return checks

    def _check_ui_lint(self, cycle_dir: Path) -> list[dict]:
        lint_path = cycle_dir / "ui_lint.json"
        if not lint_path.exists():
            return [{"name": "ui_lint", "ok": False, "path": "ui_lint.json"}]
        try:
            payload = json.loads(lint_path.read_text(encoding="utf-8"))
            ok = bool(payload.get("ok"))
        except Exception:
            ok = False
        return [{"name": "ui_lint", "ok": ok, "path": "ui_lint.json"}]

    def _check_automation(self, cycle_dir: Path) -> list[dict]:
        checks: list[dict] = []
        automation = cycle_dir / "automation.json"
        autofix_log = cycle_dir / "autofix.log"
        checks.append(
            {"name": "automation_log", "ok": automation.exists(), "path": "automation.json"}
        )
        checks.append(
            {"name": "autofix_log", "ok": autofix_log.exists(), "path": "autofix.log"}
        )
        summary = self.run_dir / "mvp_automation_summary.json"
        checks.append(
            {"name": "automation_summary", "ok": summary.exists(), "path": "mvp_automation_summary.json"}
        )
        steps_ok = False
        if automation.exists():
            try:
                data = json.loads(automation.read_text(encoding="utf-8"))
                steps = data.get("steps", [])
                steps_ok = (
                    any(step.get("step") == "build" for step in steps)
                    and any(step.get("step") == "test" for step in steps)
                    and any(step.get("step") == "ui_lint" for step in steps)
                )
            except Exception:
                steps_ok = False
        checks.append({"name": "automation_steps", "ok": steps_ok, "path": "automation.json"})
        return checks

    def _record_cycle_step(
        self,
        cycle_dir: Path,
        step: str,
        attempt: int,
        ok: bool,
        log_name: str,
    ) -> None:
        automation_path = cycle_dir / "automation.json"
        if not automation_path.exists():
            return
        try:
            data = json.loads(automation_path.read_text(encoding="utf-8"))
        except Exception:
            return
        steps = data.get("steps", [])
        steps.append(
            {
                "step": step,
                "attempt": attempt,
                "ok": ok,
                "log": log_name,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        data["steps"] = steps
        automation_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _write_cycle_alias(self, cycle_key: str, cycle_dir: Path, filename: str) -> None:
        alias_dir = self.cycles_dir / cycle_key
        if alias_dir == cycle_dir:
            return
        src = cycle_dir / filename
        if not src.exists():
            return
        alias_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, alias_dir / filename)

    def _check_security(self, cycle_key: str, cycle_dir: Path) -> list[dict]:
        checks: list[dict] = []
        repo_within_run = self._is_within_run(self.repo_dir)
        cycle_within_run = self._is_within_run(cycle_dir)
        patch_info = self._collect_patch_targets(cycle_dir)
        secrets = self._scan_for_secrets()
        forbidden_files = self._scan_for_forbidden_files()
        external_symlinks = self._scan_for_external_symlinks()
        checks.append(
            {
                "name": "repo_within_run_dir",
                "ok": repo_within_run,
                "path": str(self.repo_dir),
            }
        )
        checks.append(
            {
                "name": "cycle_within_run_dir",
                "ok": cycle_within_run,
                "path": str(cycle_dir),
            }
        )
        checks.append(
            {
                "name": "patch_targets_scoped",
                "ok": not patch_info["invalid_targets"],
                "path": "patch.diff|fix_*.diff",
            }
        )
        checks.append(
            {
                "name": "secrets_scan_clean",
                "ok": len(secrets) == 0,
                "path": "mvp_repo/**",
            }
        )
        checks.append(
            {
                "name": "forbidden_files_clean",
                "ok": len(forbidden_files) == 0,
                "path": "mvp_repo/**",
            }
        )
        checks.append(
            {
                "name": "external_symlinks_blocked",
                "ok": len(external_symlinks) == 0,
                "path": "mvp_repo/**",
            }
        )
        self._write_security_report(
            cycle_key,
            cycle_dir,
            patch_info,
            secrets,
            forbidden_files,
            external_symlinks,
        )
        return checks

    def _is_within_run(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.run_dir.resolve())
            return True
        except ValueError:
            return False

    def _collect_patch_targets(self, cycle_dir: Path) -> dict:
        patch_targets: list[str] = []
        invalid_targets: list[str] = []
        diffs = [cycle_dir / "patch.diff"]
        diffs.extend(sorted(cycle_dir.glob("fix_*.diff")))
        for diff_path in diffs:
            if not diff_path.exists():
                continue
            content = diff_path.read_text(encoding="utf-8", errors="ignore")
            for rel in self._parse_patch_targets(content):
                patch_targets.append(rel)
                is_absolute = rel.startswith("/") or re.match(r"^[A-Za-z]:", rel) is not None
                if not rel.startswith("mvp_repo/") or ".." in rel or is_absolute:
                    invalid_targets.append(rel)
        return {
            "patch_targets": sorted(set(patch_targets)),
            "invalid_targets": sorted(set(invalid_targets)),
        }

    def _parse_patch_targets(self, diff_text: str) -> list[str]:
        targets: list[str] = []
        for line in diff_text.splitlines():
            if line.startswith("+++ b/"):
                target = line[len("+++ b/") :].strip()
                if target:
                    targets.append(target)
        return targets

    def _scan_for_secrets(self) -> list[dict]:
        if self._secret_scan_cache is not None:
            return self._secret_scan_cache
        ignore_dirs = {
            ".git",
            ".next",
            "node_modules",
            "dist",
            "build",
            ".cache",
            "__pycache__",
            ".venv",
            "venv",
        }
        ignore_files = {
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
        }
        patterns = [
            ("openai_key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
            ("aws_key", re.compile(r"AKIA[0-9A-Z]{16}")),
            ("private_key", re.compile(r"-----BEGIN (?:RSA|EC|DSA|OPENSSH) PRIVATE KEY-----")),
            ("generic_api_key", re.compile(r"(?i)api[_-]?key\\s*[:=]\\s*['\\\"][^'\\\"]{8,}['\\\"]")),
            ("generic_secret", re.compile(r"(?i)secret\\s*[:=]\\s*['\\\"][^'\\\"]{8,}['\\\"]")),
            ("generic_password", re.compile(r"(?i)password\\s*[:=]\\s*['\\\"][^'\\\"]{6,}['\\\"]")),
            ("bearer_token", re.compile(r"(?i)bearer\\s+[A-Za-z0-9\\-_.]{12,}")),
        ]
        allow_markers = ("example", "placeholder", "your_", "YOUR_", "REPLACE_ME", "changeme")
        findings: list[dict] = []
        repo_root = self.repo_dir
        for root, dirs, files in os.walk(repo_root):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for filename in files:
                if filename in ignore_files:
                    continue
                path = Path(root) / filename
                try:
                    if path.stat().st_size > 256_000:
                        continue
                except OSError:
                    continue
                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                for line_no, line in enumerate(content.splitlines(), start=1):
                    lowered = line.lower()
                    if any(marker in lowered for marker in allow_markers):
                        continue
                    for label, pattern in patterns:
                        if pattern.search(line):
                            rel = path.relative_to(repo_root).as_posix()
                            findings.append(
                                {
                                    "file": f"mvp_repo/{rel}",
                                    "line": line_no,
                                    "type": label,
                                }
                            )
                            break
        self._secret_scan_cache = findings
        return findings

    def _scan_for_forbidden_files(self) -> list[dict]:
        repo_root = self.repo_dir
        forbidden_names = {
            ".env",
            ".env.local",
            ".env.production",
            ".env.development",
            ".env.test",
            "id_rsa",
            "id_ed25519",
        }
        forbidden_exts = {".pem", ".key", ".p12", ".pfx", ".cer", ".crt"}
        allow_suffixes = {".example", ".sample", ".template"}
        findings: list[dict] = []
        for path in repo_root.rglob("*"):
            if not path.is_file():
                continue
            name = path.name
            if name in forbidden_names:
                rel = path.relative_to(repo_root).as_posix()
                findings.append({"file": f"mvp_repo/{rel}", "type": "forbidden_name"})
                continue
            if any(name.endswith(suffix) for suffix in allow_suffixes):
                continue
            if path.suffix.lower() in forbidden_exts:
                rel = path.relative_to(repo_root).as_posix()
                findings.append({"file": f"mvp_repo/{rel}", "type": "forbidden_extension"})
        return findings

    def _scan_for_external_symlinks(self) -> list[dict]:
        repo_root = self.repo_dir.resolve()
        findings: list[dict] = []
        for path in repo_root.rglob("*"):
            try:
                if not path.is_symlink():
                    continue
                target = path.resolve()
            except OSError:
                rel = path.relative_to(repo_root).as_posix()
                findings.append({"file": f"mvp_repo/{rel}", "type": "broken_symlink"})
                continue
            try:
                target.relative_to(repo_root)
            except ValueError:
                rel = path.relative_to(repo_root).as_posix()
                findings.append(
                    {"file": f"mvp_repo/{rel}", "type": "external_symlink", "target": str(target)}
                )
        return findings

    def _write_security_report(
        self,
        cycle_key: str,
        cycle_dir: Path,
        patch_info: dict,
        secrets: list[dict],
        forbidden_files: list[dict],
        external_symlinks: list[dict],
    ) -> None:
        report = {
            "run_id": self.run_id,
            "cycle": cycle_key,
            "timestamp": datetime.utcnow().isoformat(),
            "run_dir": str(self.run_dir),
            "repo_dir": str(self.repo_dir),
            "repo_within_run_dir": self._is_within_run(self.repo_dir),
            "cycle_within_run_dir": self._is_within_run(cycle_dir),
            "patch_targets": patch_info.get("patch_targets", []),
            "invalid_patch_targets": patch_info.get("invalid_targets", []),
            "secrets_found": secrets,
            "forbidden_files": forbidden_files,
            "external_symlinks": external_symlinks,
            "security_events": list(self._security_events),
        }
        (self.run_dir / "mvp_security_report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        (cycle_dir / "security.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )

    def _check_patch_diff(self, cycle_dir: Path) -> list[dict]:
        patch_path = cycle_dir / "patch.diff"
        ok = False
        if patch_path.exists():
            content = patch_path.read_text(encoding="utf-8", errors="ignore")
            ok = "diff --git" in content
        return [{"name": "patch_diff_non_empty", "ok": ok, "path": "patch.diff"}]

    def _check_foundation_smoke(self, cycle_dir: Path) -> list[dict]:
        checks: list[dict] = []
        smoke_log = cycle_dir / "smoke_1.log"
        checks.append(
            {"name": "smoke_log_exists", "ok": smoke_log.exists(), "path": "smoke_1.log"}
        )
        return checks

    def run_smoke_checks(self, cycle_dir: Path, attempt: int = 1) -> bool:
        log_path = cycle_dir / f"smoke_{attempt}.log"
        if not self.dev_command:
            log_path.write_text(
                "Smoke checks failed: MVP_DEV_COMMAND is empty.", encoding="utf-8"
            )
            self._record_cycle_step(
                cycle_dir=cycle_dir,
                step="smoke",
                attempt=attempt,
                ok=False,
                log_name=log_path.name,
            )
            return False
        dev_log_path = cycle_dir / f"devserver_{attempt}.log"
        dev_log = dev_log_path.open("w", encoding="utf-8")
        process = subprocess.Popen(
            self.dev_command,
            cwd=self.repo_dir,
            shell=True,
            stdout=dev_log,
            stderr=dev_log,
            text=True,
        )
        start_time = time.time()
        try:
            checks = self._resolve_smoke_paths()
            results: list[str] = []
            ok = False
            while time.time() - start_time < self.dev_startup_timeout:
                ok = True
                results.clear()
                for path in checks:
                    url = f"{self.dev_base_url}{path}"
                    status, error = self._probe_url(url)
                    results.append(f"{url} -> {status or 'error'} {error or ''}".strip())
                    if status is None or status >= 400:
                        ok = False
                if ok:
                    break
                time.sleep(1.0)
            log_path.write_text(
                "Smoke checks\n"
                f"Command: {self.dev_command}\n"
                f"Base URL: {self.dev_base_url}\n"
                f"Paths: {', '.join(checks)}\n"
                f"Result: {'pass' if ok else 'fail'}\n"
                + "\n".join(results),
                encoding="utf-8",
            )
            self._record_cycle_step(
                cycle_dir=cycle_dir,
                step="smoke",
                attempt=attempt,
                ok=ok,
                log_name=log_path.name,
            )
            return ok
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            dev_log.close()

    def _probe_url(self, url: str) -> tuple[Optional[int], Optional[str]]:
        try:
            with urllib.request.urlopen(url, timeout=4) as response:
                return response.getcode(), None
        except urllib.error.HTTPError as exc:
            return exc.code, str(exc)
        except Exception as exc:
            return None, str(exc)

    def _resolve_smoke_paths(self) -> list[str]:
        paths = list(self.dev_check_paths) or ["/"]
        # Ensure required API checks when route exists.
        api_status = self.repo_dir / "app" / "api" / "status" / "route.ts"
        api_health = self.repo_dir / "app" / "api" / "health" / "route.ts"
        if api_status.exists() and "/api/status" not in paths:
            paths.append("/api/status")
        if api_health.exists() and "/api/health" not in paths:
            paths.append("/api/health")
        if "/" not in paths:
            paths.insert(0, "/")
        return paths

    def _check_foundation_repo(self, repo_root: Path) -> list[dict]:
        checks: list[dict] = []
        package_json = repo_root / "package.json"
        requirements = repo_root / "requirements.txt"
        pyproject = repo_root / "pyproject.toml"
        readme = repo_root / "README.md"
        landing = repo_root / "app" / "page.tsx"
        dashboard = repo_root / "app" / "app" / "page.tsx"
        marketplace = repo_root / "app" / "app" / "marketplace" / "page.tsx"
        app_shell = repo_root / "components" / "layout" / "app-shell.tsx"
        status_route = repo_root / "app" / "api" / "status" / "route.ts"
        health_route = repo_root / "app" / "api" / "health" / "route.ts"
        checks.append(
            {"name": "mvp_repo_exists", "ok": repo_root.exists(), "path": str(repo_root)}
        )
        checks.append(
            {
                "name": "package_or_python_manifest",
                "ok": package_json.exists() or requirements.exists() or pyproject.exists(),
                "path": "package.json|requirements.txt|pyproject.toml",
            }
        )
        readme_ok = False
        if readme.exists():
            text = readme.read_text(encoding="utf-8")
            readme_ok = "npm" in text or "pip" in text or "run" in text.lower()
        checks.append({"name": "readme_run_instructions", "ok": readme_ok, "path": "README.md"})
        checks.append({"name": "landing_page", "ok": landing.exists(), "path": "app/page.tsx"})
        checks.append({"name": "dashboard_page", "ok": dashboard.exists(), "path": "app/app/page.tsx"})
        checks.append({"name": "marketplace_page", "ok": marketplace.exists(), "path": "app/app/marketplace/page.tsx"})
        checks.append({"name": "app_shell", "ok": app_shell.exists(), "path": "components/layout/app-shell.tsx"})
        checks.append(
            {
                "name": "api_route",
                "ok": status_route.exists() or health_route.exists(),
                "path": "app/api/status|health",
            }
        )
        return checks

    def _check_stability(self, repo_root: Path) -> list[dict]:
        checks: list[dict] = []
        error_page = repo_root / "app" / "error.tsx"
        global_error = repo_root / "app" / "global-error.tsx"
        not_found = repo_root / "app" / "not-found.tsx"
        status_route = repo_root / "app" / "api" / "status" / "route.ts"
        health_route = repo_root / "app" / "api" / "health" / "route.ts"
        checks.append({"name": "error_boundary", "ok": error_page.exists(), "path": "app/error.tsx"})
        checks.append(
            {"name": "global_error_boundary", "ok": global_error.exists(), "path": "app/global-error.tsx"}
        )
        checks.append({"name": "not_found", "ok": not_found.exists(), "path": "app/not-found.tsx"})
        if error_page.exists():
            content = error_page.read_text(encoding="utf-8")
            checks.append(
                {
                    "name": "error_logging",
                    "ok": "console.error" in content,
                    "path": "app/error.tsx",
                }
            )
        api_ok = status_route.exists() or health_route.exists()
        checks.append(
            {"name": "api_route", "ok": api_ok, "path": "app/api/status|health"}
        )
        if status_route.exists():
            content = status_route.read_text(encoding="utf-8")
            checks.append(
                {
                    "name": "status_error_handling",
                    "ok": "try" in content and "catch" in content,
                    "path": "app/api/status/route.ts",
                }
            )
            checks.append(
                {
                    "name": "status_has_timestamp",
                    "ok": "timestamp" in content,
                    "path": "app/api/status/route.ts",
                }
            )
        if health_route.exists():
            content = health_route.read_text(encoding="utf-8")
            checks.append(
                {
                    "name": "health_error_handling",
                    "ok": "try" in content and "catch" in content,
                    "path": "app/api/health/route.ts",
                }
            )
            checks.append(
                {
                    "name": "health_has_timestamp",
                    "ok": "timestamp" in content,
                    "path": "app/api/health/route.ts",
                }
            )
        if self.force_autofix:
            checks.append(
                {
                    "name": "autofix_marker",
                    "ok": self._autofix_marker.exists(),
                    "path": ".asmblr/autofix_stability_ok",
                }
            )
        return checks

    def _check_ux(self, repo_root: Path) -> list[dict]:
        checks: list[dict] = []
        globals_css = repo_root / "app" / "globals.css"
        page = repo_root / "app" / "page.tsx"
        components = [
            "components/ui/button.tsx",
            "components/ui/card.tsx",
            "components/ui/badge.tsx",
            "components/ui/input.tsx",
            "components/ui/label.tsx",
            "components/ui/empty-state.tsx",
            "components/ui/skeleton.tsx",
            "components/ui/toast.tsx",
            "components/ui/toaster.tsx",
            "components/layout/app-shell.tsx",
        ]
        css_ok = False
        if globals_css.exists():
            content = globals_css.read_text(encoding="utf-8")
            css_ok = (
                "font-family" in content
                and "--color-" in content
                and "--space-" in content
                and "--radius-" in content
                and "--shadow-" in content
                and "--font-sans" in content
            )
        checks.append({"name": "globals_css", "ok": css_ok, "path": "app/globals.css"})
        page_ok = False
        if page.exists():
            content = page.read_text(encoding="utf-8")
            page_ok = "<h1" in content and "<h2" in content and "max-w-" in content
        checks.append({"name": "page_ux_usage", "ok": page_ok, "path": "app/page.tsx"})
        for path in components:
            checks.append({"name": f"component_{Path(path).stem}", "ok": (repo_root / path).exists(), "path": path})
        return checks

    def _check_polish(self, repo_root: Path) -> list[dict]:
        checks: list[dict] = []
        loading_root = repo_root / "app" / "loading.tsx"
        loading_app = repo_root / "app" / "app" / "loading.tsx"
        empty_state = repo_root / "components" / "ui" / "empty-state.tsx"
        skeleton = repo_root / "components" / "ui" / "skeleton.tsx"
        toaster = repo_root / "components" / "ui" / "toaster.tsx"
        toast = repo_root / "components" / "ui" / "toast.tsx"
        page = repo_root / "app" / "app" / "settings" / "page.tsx"
        globals_css = repo_root / "app" / "globals.css"
        checks.append(
            {
                "name": "loading_state",
                "ok": loading_root.exists() or loading_app.exists(),
                "path": "app/loading.tsx|app/app/loading.tsx",
            }
        )
        checks.append({"name": "empty_state", "ok": empty_state.exists(), "path": "components/ui/empty-state.tsx"})
        checks.append({"name": "skeleton", "ok": skeleton.exists(), "path": "components/ui/skeleton.tsx"})
        checks.append({"name": "toaster", "ok": toaster.exists(), "path": "components/ui/toaster.tsx"})
        checks.append({"name": "toast", "ok": toast.exists(), "path": "components/ui/toast.tsx"})
        page_ok = False
        if page.exists():
            content = page.read_text(encoding="utf-8")
            page_ok = "useToast" in content and "required" in content
        checks.append({"name": "page_polish_usage", "ok": page_ok, "path": "app/app/settings/page.tsx"})
        animation_ok = False
        if globals_css.exists():
            content = globals_css.read_text(encoding="utf-8")
            animation_ok = "shadow-soft" in content and "shadow-card" in content
        checks.append({"name": "animations", "ok": animation_ok, "path": "app/globals.css"})
        return checks

    def _attempt_auto_fix(self, cycle_key: str, cycle_dir: Path, attempt: int) -> None:
        if cycle_key == "ux":
            self._apply_ux_changes()
        elif cycle_key == "polish":
            self._apply_polish_changes()
        prompt = (
            f"Auto-fix attempt {attempt} for cycle {cycle_key}.\n\n"
            f"Last build log:\n{self.last_build_log}\n\n"
            f"Last test log:\n{self.last_test_log}\n\n"
            f"Repo snapshot:\n{self._repo_tree_snapshot()}\n\n"
            "Provide a git diff for files under mvp_repo/ to fix the failure."
        )
        diff = ""
        if self.llm_client and self.llm_client.available():
            try:
                diff = self.llm_client.generate(prompt)
            except Exception as exc:
                logger.warning("Auto-fix LLM failed: {}", exc)
        if diff:
            (cycle_dir / f"fix_{attempt}.diff").write_text(diff, encoding="utf-8")
            self._apply_patch_to_repo(diff)

    def _apply_stability_changes(self) -> list[str]:
        touched: list[str] = []
        error_path = self.repo_dir / "app" / "error.tsx"
        global_error_path = self.repo_dir / "app" / "global-error.tsx"
        not_found_path = self.repo_dir / "app" / "not-found.tsx"
        status_route = self.repo_dir / "app" / "api" / "status" / "route.ts"
        health_route = self.repo_dir / "app" / "api" / "health" / "route.ts"

        error_ui = """'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => {
    console.error('Runtime error:', error);
  }, [error]);

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center space-y-4 px-6 text-center">
      <h1 className="text-3xl font-semibold text-slate-900">We hit a snag</h1>
      <p className="text-sm text-slate-600">Refresh the page or try again.</p>
      <Button onClick={() => reset()}>Try again</Button>
    </div>
  );
}
"""
        not_found = """import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center space-y-4 px-6 text-center">
      <h1 className="text-3xl font-semibold text-slate-900">Page not found</h1>
      <p className="text-sm text-slate-600">Return to the main experience to keep moving.</p>
      <Button asChild>
        <Link href="/">Back to home</Link>
      </Button>
    </div>
  );
}
"""
        global_error = """'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';

export default function GlobalError({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => {
    console.error('Global error:', error);
  }, [error]);

  return (
    <html lang="en">
      <body>
        <div className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center space-y-4 px-6 text-center">
          <h1 className="text-3xl font-semibold text-slate-900">We hit a snag</h1>
          <p className="text-sm text-slate-600">Try again or reach out if the issue continues.</p>
          <Button onClick={() => reset()}>Try again</Button>
        </div>
      </body>
    </html>
  );
}
"""
        status_template = """import { NextResponse } from 'next/server';

export function GET(request: Request) {
  try {
    const apiKey = process.env.API_KEY;
    const providedKey = request.headers.get('x-api-key');
    if (apiKey && providedKey != apiKey) {
      return NextResponse.json({ status: 'unauthorized', timestamp: new Date().toISOString() }, { status: 401 });
    }
    return NextResponse.json({
      status: 'ok',
      stack: 'Next.js + Tailwind + SQLite',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('status route failed', error);
    return NextResponse.json(
      { status: 'error', stack: 'Next.js + Tailwind + SQLite', timestamp: new Date().toISOString() },
      { status: 500 }
    );
  }
}
"""
        health_template = """import { NextResponse } from 'next/server';

export function GET() {
  try {
    return NextResponse.json({ status: 'ok', timestamp: new Date().toISOString() });
  } catch (error) {
    console.error('health route failed', error);
    return NextResponse.json({ status: 'error', timestamp: new Date().toISOString() }, { status: 500 });
  }
}
"""

        if not error_path.exists() or "console.error" not in error_path.read_text(encoding="utf-8", errors="ignore"):
            error_path.parent.mkdir(parents=True, exist_ok=True)
            error_path.write_text(error_ui, encoding="utf-8")
            touched.append("mvp_repo/app/error.tsx")
        if not not_found_path.exists():
            not_found_path.parent.mkdir(parents=True, exist_ok=True)
            not_found_path.write_text(not_found, encoding="utf-8")
            touched.append("mvp_repo/app/not-found.tsx")
        if not global_error_path.exists():
            global_error_path.parent.mkdir(parents=True, exist_ok=True)
            global_error_path.write_text(global_error, encoding="utf-8")
            touched.append("mvp_repo/app/global-error.tsx")
        if not status_route.exists():
            status_route.parent.mkdir(parents=True, exist_ok=True)
            status_route.write_text(status_template, encoding="utf-8")
            touched.append("mvp_repo/app/api/status/route.ts")
        if not health_route.exists():
            health_route.parent.mkdir(parents=True, exist_ok=True)
            health_route.write_text(health_template, encoding="utf-8")
            touched.append("mvp_repo/app/api/health/route.ts")

        return touched

    def _apply_ux_changes(self) -> list[str]:
        touched: list[str] = []
        globals_css = self.repo_dir / "app" / "globals.css"
        if globals_css.exists():
            content = globals_css.read_text(encoding="utf-8")
            if "--color-bg" not in content or "--shadow-soft" not in content:
                addition = """
:root {
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-text: #0f172a;
  --color-muted: #64748b;
  --color-border: #e2e8f0;
  --color-accent: #0ea5e9;
  --radius-sm: 10px;
  --radius-md: 14px;
  --radius-lg: 18px;
  --radius-xl: 24px;
  --space-2: 0.5rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-12: 3rem;
  --shadow-soft: 0 12px 30px rgba(15, 23, 42, 0.08);
  --shadow-card: 0 8px 24px rgba(15, 23, 42, 0.08);
}
"""
                globals_css.write_text(content + addition, encoding="utf-8")
                touched.append("mvp_repo/app/globals.css")
        return touched

    def _apply_polish_changes(self) -> list[str]:
        touched: list[str] = []
        settings_page = self.repo_dir / "app" / "app" / "settings" / "page.tsx"
        if settings_page.exists():
            content = settings_page.read_text(encoding="utf-8")
            if "useToast" not in content:
                updated = content.replace(
                    "const handleSave",
                    "const { addToast } = useToast();\n\n  const handleSave",
                )
                updated = updated.replace(
                    "setError('');",
                    "setError('');\n    addToast({ title: 'Settings saved', description: 'Your launch profile is up to date.' });",
                )
                settings_page.write_text(updated, encoding="utf-8")
                touched.append("mvp_repo/app/app/settings/page.tsx")
        return touched

    def _apply_patch_to_repo(self, diff: str) -> None:
        if not diff or "diff --git" not in diff:
            self._security_events.append("patch_rejected:missing_diff_header")
            raise MVPProgressionError("Patch rejected: missing unified diff header.")

        invalid_targets: list[str] = []
        has_hunk = False
        for line in diff.splitlines():
            if line.startswith("+++ b/"):
                rel = line[len("+++ b/") :].strip()
                if not rel.startswith("mvp_repo/") or ".." in rel or rel.startswith("/"):
                    invalid_targets.append(rel or "<empty>")
            if line.startswith("@@"):
                has_hunk = True

        if invalid_targets:
            for target in invalid_targets:
                self._security_events.append(f"blocked_patch_target:{target}")
            raise MVPProgressionError("Patch rejected: invalid targets outside mvp_repo/.")
        if not has_hunk:
            self._security_events.append("patch_rejected:missing_hunks")
            raise MVPProgressionError("Patch rejected: no hunks found.")

        patch_path = self.run_dir / "mvp_cycles" / "patch.apply.diff"
        patch_path.write_text(diff, encoding="utf-8")

        try:
            proc = subprocess.run(
                ["git", "apply", "--whitespace=nowarn", "--unsafe-paths", "--directory", "."],
                cwd=self.run_dir,
                input=diff,
                text=True,
                capture_output=True,
                check=False,
            )
        except Exception as exc:
            self._security_events.append(f"patch_apply_failed:{exc}")
            raise MVPProgressionError(f"Patch apply failed to start: {exc}") from exc

        if proc.returncode != 0:
            self._security_events.append("patch_apply_failed:git_apply")
            raise MVPProgressionError(
                "Patch apply failed: git apply returned non-zero.\n"
                f"stdout:\n{proc.stdout.strip()}\n"
                f"stderr:\n{proc.stderr.strip()}"
            )

    def _is_within_repo(self, path: Path) -> bool:
        try:
            path.relative_to(self.repo_dir.resolve())
            return True
        except ValueError:
            return False

    def _ensure_foundation_basics(self) -> None:
        status_route = self.repo_dir / "app" / "api" / "status" / "route.ts"
        health_route = self.repo_dir / "app" / "api" / "health" / "route.ts"
        readme = self.repo_dir / "README.md"
        package_json = self.repo_dir / "package.json"
        smoke_script = self.repo_dir / "scripts" / "smoke.mjs"
        if not readme.exists():
            readme.write_text(
                "# MVP Repository\n\n"
                "## Getting started\n"
                "```bash\n"
                "npm install\n"
                "npm run dev\n"
                "```\n",
                encoding="utf-8",
            )
        if package_json.exists():
            try:
                payload = json.loads(package_json.read_text(encoding="utf-8"))
            except Exception:
                payload = {}
            scripts = payload.get("scripts")
            if not isinstance(scripts, dict):
                scripts = {}
            if "test" not in scripts:
                scripts["test"] = "node scripts/smoke.mjs"
                payload["scripts"] = scripts
                package_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        if not smoke_script.exists():
            smoke_script.parent.mkdir(parents=True, exist_ok=True)
            smoke_script.write_text(
                "console.log('Smoke test placeholder.');\n",
                encoding="utf-8",
            )
        if status_route.exists() and health_route.exists():
            return
        status_route.parent.mkdir(parents=True, exist_ok=True)
        if not status_route.exists():
            status_route.write_text(
                """import { NextResponse } from 'next/server';

export function GET() {
  try {
    return NextResponse.json({
      status: 'ok',
      stack: 'Next.js + Tailwind + SQLite',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('status route failed', error);
    return NextResponse.json(
      { status: 'error', stack: 'Next.js + Tailwind + SQLite' },
      { status: 500 }
    );
  }
}
""",
                encoding="utf-8",
            )
        if not health_route.exists():
            health_route.parent.mkdir(parents=True, exist_ok=True)
            health_route.write_text(
                """import { NextResponse } from 'next/server';

export function GET() {
  try {
    return NextResponse.json({ status: 'ok', timestamp: new Date().toISOString() });
  } catch (error) {
    console.error('health route failed', error);
    return NextResponse.json({ status: 'error', timestamp: new Date().toISOString() }, { status: 500 });
  }
}
""",
                encoding="utf-8",
            )


def progressive_cycles(
    run_id: str,
    run_dir: Path,
    settings: Settings,
    build_runner: Optional[BuildRunner] = None,
    test_runner: Optional[TestRunner] = None,
) -> None:
    if not settings.enable_progressive_cycles:
        return
    progression = MVPProgression(
        run_id=run_id,
        run_dir=run_dir,
        settings=settings,
        build_runner=build_runner,
        test_runner=test_runner,
    )
    progression.run()
