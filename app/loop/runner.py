from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

from app.core.config import Settings
from app.core.llm import LLMClient, check_ollama
from app.loop.applier import LoopApplier
from app.loop.errors import LoopException
from app.loop.git_ops import GitOps
from app.loop.judge import LoopJudge
from app.loop.patcher import LoopPatcher
from app.loop.planner import LoopPlanner
from app.loop.schemas import IterationVerdict, LoopConfig, LoopPlan, PatchOutcome
from app.loop.verifier import LoopVerifier

logger = logging.getLogger(__name__)


@dataclass
class LoopRunResult:
    run_id: str
    status: str
    iterations: int
    verdict: Optional[IterationVerdict]
    run_dir: Path


class LoopRunner:
    def __init__(
        self,
        settings: Settings,
        config: LoopConfig,
        plan_llm: Optional[LLMClient] = None,
        patch_llm: Optional[LLMClient] = None,
        planner: Optional[LoopPlanner] = None,
        patcher: Optional[LoopPatcher] = None,
        applier: Optional[LoopApplier] = None,
        verifier: Optional[LoopVerifier] = None,
        judge: Optional[LoopJudge] = None,
        git_ops: Optional[GitOps] = None,
        approval_callback: Optional[Callable[[int], bool]] = None,
    ) -> None:
        self.settings = settings
        self.config = config
        self.plan_llm = plan_llm
        self.patch_llm = patch_llm
        self._provided_planner = planner
        self._provided_patcher = patcher
        self._provided_applier = applier
        self._provided_verifier = verifier
        self._provided_judge = judge
        self.git_ops = git_ops or GitOps(Path.cwd())
        self.approval_callback = approval_callback or self._default_manual_prompt
        self.planner: LoopPlanner | None = None
        self.patcher: LoopPatcher | None = None
        self.applier: LoopApplier | None = None
        self.verifier: LoopVerifier | None = None
        self.judge: LoopJudge | None = None

    def run(self) -> LoopRunResult:
        self._validate_config()
        run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        run_dir = self.settings.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        loop_dir = run_dir / "loop"
        loop_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Starting Asmblr loop %s goal=%s", run_id, self.config.goal)

        try:
            working_root = self._preflight(loop_dir)
        except LoopException as exc:
            raise

        self._setup_components(working_root)
        start_time = datetime.utcnow()
        total_lines = 0
        iteration = 1
        handled_iterations = 0
        last_verdict: Optional[IterationVerdict] = None

        while iteration <= self.config.max_iter:
            if self._time_exceeded(start_time):
                last_verdict = IterationVerdict(
                    status="aborted",
                    reasons=["Time budget exceeded."],
                    metrics={"iteration": iteration},
                )
                break

            iteration_dir = loop_dir / f"iter_{iteration:02d}"
            iteration_dir.mkdir(parents=True, exist_ok=True)

            try:
                plan = self.planner.plan(self.config.goal, iteration)
            except LoopException as exc:
                last_verdict = IterationVerdict(
                    status="aborted",
                    reasons=[f"Plan generation failed: {exc}"],
                    metrics={"iteration": iteration},
                )
                self._write_iteration_artifacts(
                    iteration_dir,
                    run_id,
                    iteration,
                    apply_log="Plan failure aborted loop.",
                    test_log="",
                    files_touched=[],
                    verdict=last_verdict,
                    total_lines=total_lines,
                )
                break

            plan_path = iteration_dir / "plan.md"
            plan_path.write_text(self._format_plan(plan, iteration), encoding="utf-8")

            try:
                patch_outcome = self.patcher.create_patch(self.config.goal, plan, iteration)
            except LoopException as exc:
                last_verdict = IterationVerdict(
                    status="aborted",
                    reasons=[str(exc)],
                    metrics={"iteration": iteration},
                )
                self._write_iteration_artifacts(
                    iteration_dir,
                    run_id,
                    iteration,
                    apply_log="",
                    test_log="",
                    files_touched=[],
                    verdict=last_verdict,
                    total_lines=total_lines,
                )
                break

            patch_path = iteration_dir / "patch.diff"
            patch_path.write_text(patch_outcome.text, encoding="utf-8")
            total_lines += patch_outcome.metadata.line_count

            apply_log = ""
            test_log = ""
            files_touched = patch_outcome.metadata.touched_files
            apply_success = False

            if self.config.approve_mode == "manual":
                approved = self.approval_callback(iteration)
                if not approved:
                    last_verdict = IterationVerdict(
                        status="aborted",
                        reasons=["Manual approval declined."],
                        metrics={"iteration": iteration},
                    )
                    self._write_iteration_artifacts(
                        iteration_dir,
                        run_id,
                        iteration,
                        apply_log="Manual approval declined; patch not applied.",
                        test_log="Manual approval declined before verification.",
                        files_touched=files_touched,
                        verdict=last_verdict,
                        total_lines=total_lines,
                    )
                    break

            try:
                apply_log, apply_success = self.applier.apply_patch(
                    patch_outcome.text, dry_run=self.config.dry_run
                )
            except LoopException as exc:
                last_verdict = IterationVerdict(
                    status="aborted",
                    reasons=[f"Patch apply failed: {exc}"],
                    metrics={
                        "iteration": iteration,
                        "patch_lines": patch_outcome.metadata.line_count,
                    },
                )
                self._write_iteration_artifacts(
                    iteration_dir,
                    run_id,
                    iteration,
                    apply_log=str(exc),
                    test_log="",
                    files_touched=files_touched,
                    verdict=last_verdict,
                    total_lines=total_lines,
                )
                break

            if self.config.dry_run:
                tests_pass = True
                test_log = "Dry run: tests skipped."
            else:
                tests_pass, test_log = self.verifier.run(self.config.tests_command)

            verdict = self.judge.evaluate(
                iteration,
                patch_outcome.metadata.line_count,
                total_lines,
                tests_pass,
                apply_success,
                self.config.dry_run,
            )
            last_verdict = verdict

            self._write_iteration_artifacts(
                iteration_dir,
                run_id,
                iteration,
                apply_log=apply_log,
                test_log=test_log,
                files_touched=files_touched,
                verdict=verdict,
                total_lines=total_lines,
            )

            if verdict.status == "aborted":
                break

            handled_iterations = iteration

            if not self.config.dry_run:
                commit_hash = self.git_ops.commit(f"loop iter {iteration}")
                (iteration_dir / "commit.txt").write_text(commit_hash, encoding="utf-8")

            if iteration >= self.config.max_iter:
                last_verdict = IterationVerdict(
                    status="completed",
                    reasons=["Iteration budget reached."],
                    metrics=verdict.metrics,
                )
                break

            iteration += 1

        final_status = last_verdict.status if last_verdict else "aborted"
        if not handled_iterations:
            handled_iterations = iteration if final_status == "completed" else 0

        return LoopRunResult(
            run_id=run_id,
            status=final_status,
            iterations=handled_iterations,
            verdict=last_verdict,
            run_dir=run_dir,
        )

    def _validate_config(self) -> None:
        if self.config.approve_mode not in {"auto", "manual"}:
            raise LoopException(
                f"Unknown approve mode '{self.config.approve_mode}'. Use 'auto' or 'manual'."
            )
        if not self.config.goal.strip():
            raise LoopException("Loop goal must be provided.")

    def _preflight(self, loop_dir: Path) -> Path:
        try:
            check_ollama(
                self.settings.ollama_base_url,
                [self.settings.general_model, self.settings.code_model],
            )
        except Exception as exc:
            raise LoopException(f"Ollama preflight failed: {exc}")

        working_root = self.git_ops.prepare_workspace(loop_dir)
        return working_root

    def _setup_components(self, working_root: Path) -> None:
        if self._provided_planner:
            self.planner = self._provided_planner
        else:
            if not self.plan_llm:
                raise LoopException("Planner requires an LLM instance.")
            self.planner = LoopPlanner(self.plan_llm)

        if self._provided_patcher:
            self.patcher = self._provided_patcher
        else:
            if not self.patch_llm:
                raise LoopException("Patcher requires an LLM instance.")
            self.patcher = LoopPatcher(self.patch_llm, working_root)

        self.applier = self._provided_applier or LoopApplier(working_root)
        self.verifier = self._provided_verifier or LoopVerifier(working_root)
        self.judge = self._provided_judge or LoopJudge(
            self.config.max_total_diff_lines, self.config.max_patch_lines
        )

    def _format_plan(self, plan: LoopPlan, iteration: int) -> str:
        lines = [f"# Iteration {iteration} plan", f"Goal: {self.config.goal}", "", "## Steps"]
        for idx, step in enumerate(plan.steps, start=1):
            lines.append(f"{idx}. {step}")
        if plan.files_hint:
            lines.append("")
            lines.append("## Files hint")
            for file in plan.files_hint:
                lines.append(f"- {file}")
        lines.append("")
        lines.append("## Rationale")
        lines.append(plan.rationale or "No rationale provided.")
        return "\n".join(lines)

    def _write_iteration_artifacts(
        self,
        iteration_dir: Path,
        run_id: str,
        iteration: int,
        apply_log: str,
        test_log: str,
        files_touched: List[str],
        verdict: IterationVerdict,
        total_lines: int,
    ) -> None:
        (iteration_dir / "apply.log").write_text(apply_log or "", encoding="utf-8")
        (iteration_dir / "test.log").write_text(test_log or "", encoding="utf-8")
        (iteration_dir / "files_touched.json").write_text(
            json.dumps(files_touched, indent=2), encoding="utf-8"
        )
        verdict_payload = {
            "status": verdict.status,
            "reasons": verdict.reasons,
            "metrics": verdict.metrics,
            "total_patch_lines": total_lines,
        }
        (iteration_dir / "verdict.json").write_text(
            json.dumps(verdict_payload, indent=2), encoding="utf-8"
        )
        rollback = iteration_dir / "rollback_hint.md"
        rollback.write_text(
            f"To revert to this iteration run:\npython -m app loop-rollback --run-id {run_id} --to-iter {iteration}\n",
            encoding="utf-8",
        )

    def _time_exceeded(self, start_time: datetime) -> bool:
        if self.config.time_minutes is None:
            return False
        elapsed = datetime.utcnow() - start_time
        return elapsed.total_seconds() > self.config.time_minutes * 60

    def _manual_prompt(self, iteration: int) -> bool:
        prompt = (
            f"Iteration {iteration} produced a patch. Apply now? [y/N]: "
        )
        response = input(prompt).strip().lower()
        return response in {"y", "yes"}

    def _default_manual_prompt(self, iteration: int) -> bool:
        return self._manual_prompt(iteration)
