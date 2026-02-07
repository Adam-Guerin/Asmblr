import app.loop.runner as loop_runner_module
import json
import subprocess
import sys
from pathlib import Path

from app.core.config import Settings
from app.loop.git_ops import GitOps
from app.loop.rollback import run_loop_rollback
from app.loop.runner import LoopConfig, LoopRunner
from app.loop.schemas import LoopPlan, PatchMetadata, PatchOutcome

loop_runner_module.check_ollama = lambda base_url, models: None


def _init_git_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Loop Test"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "loop@example.com"], cwd=root, check=True)


def _write_settings(tmp_path: Path) -> Settings:
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    settings.config_dir = tmp_path / "configs"
    settings.knowledge_dir = tmp_path / "knowledge"
    for directory in (
        settings.runs_dir,
        settings.data_dir,
        settings.config_dir,
        settings.knowledge_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    return settings


class StubPlanner:
    def plan(self, goal: str, iteration: int) -> LoopPlan:
        return LoopPlan(
            steps=[f"Adjust foo.txt for iteration {iteration}"],
            rationale="Keep track of iterations.",
            files_hint=["foo.txt"],
        )


class StubPatcher:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def create_patch(self, goal: str, plan: LoopPlan, iteration: int) -> PatchOutcome:
        target = self.repo_root / "foo.txt"
        old = target.read_text(encoding="utf-8").strip()
        new_line = f"iteration {iteration}"
        patch_text = (
            "diff --git a/foo.txt b/foo.txt\n"
            "index 0000000..0000000 100644\n"
            "--- a/foo.txt\n"
            "+++ b/foo.txt\n"
            "@@ -1 +1 @@\n"
            f"-{old}\n"
            f"+{new_line}\n"
        )
        metadata = PatchMetadata(touched_files=["foo.txt"], line_count=2)
        return PatchOutcome(text=patch_text, metadata=metadata)


class InvalidPatchPatcher(StubPatcher):
    def create_patch(self, goal: str, plan: LoopPlan, iteration: int) -> PatchOutcome:
        patch_text = (
            "diff --git a/nope.txt b/nope.txt\n"
            "index 0000000..0000000 100644\n"
            "--- a/nope.txt\n"
            "+++ b/nope.txt\n"
            "@@ -0,0 +1 @@\n"
            "+ghost\n"
        )
        metadata = PatchMetadata(touched_files=["nope.txt"], line_count=1)
        return PatchOutcome(text=patch_text, metadata=metadata)


def _build_runner(
    repo_root: Path,
    settings: Settings,
    config: LoopConfig,
    approval_callback=None,
    patcher=None,
) -> LoopRunner:
    git_ops = GitOps(repo_root)
    return LoopRunner(
        settings=settings,
        config=config,
        planner=StubPlanner(),
        patcher=patcher or StubPatcher(repo_root),
        git_ops=git_ops,
        approval_callback=approval_callback,
    )


def _tests_command() -> str:
    return f"{sys.executable} -c \"print('ok')\""


def _run_simple_loop(tmp_path: Path, config: LoopConfig, patcher=None, approval_callback=None):
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    (repo / "foo.txt").write_text("initial\n", encoding="utf-8")
    subprocess.run(["git", "add", "foo.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True)
    settings = _write_settings(tmp_path)
    runner = _build_runner(
        repo,
        settings,
        config,
        patcher=patcher,
        approval_callback=approval_callback,
    )
    return repo, settings, runner


def test_loop_state_machine_happy_path(tmp_path: Path):
    config = LoopConfig(
        goal="Update foo",
        max_iter=1,
        tests_command=_tests_command(),
    )
    repo, settings, runner = _run_simple_loop(tmp_path, config)
    result = runner.run()
    assert result.status == "completed"
    loop_dir = settings.runs_dir / result.run_id / "loop"
    assert (loop_dir / "iter_01" / "plan.md").exists()
    assert (loop_dir / "iter_01" / "patch.diff").exists()
    assert (loop_dir / "iter_01" / "apply.log").exists()
    assert (loop_dir / "iter_01" / "test.log").exists()
    assert (loop_dir / "iter_01" / "files_touched.json").exists()
    assert (loop_dir / "iter_01" / "verdict.json").exists()
    assert (loop_dir / "iter_01" / "commit.txt").exists()
    assert (repo / "foo.txt").read_text(encoding="utf-8").strip() == "iteration 1"


def test_loop_aborts_on_invalid_patch(tmp_path: Path):
    config = LoopConfig(
        goal="Fail patch",
        max_iter=1,
        tests_command=_tests_command(),
    )
    repo, settings, runner = _run_simple_loop(
        tmp_path, config, patcher=InvalidPatchPatcher(tmp_path / "repo")
    )
    result = runner.run()
    assert result.status == "aborted"
    verdict = json.loads(
        (settings.runs_dir / result.run_id / "loop" / "iter_01" / "verdict.json").read_text(
            encoding="utf-8"
        )
    )
    assert verdict["status"] == "aborted"
    assert any("Patch apply failed" in reason for reason in verdict["reasons"])


def test_loop_manual_approval_blocks_apply(tmp_path: Path):
    config = LoopConfig(
        goal="Manual guard",
        max_iter=1,
        tests_command=_tests_command(),
        approve_mode="manual",
    )
    repo, settings, runner = _run_simple_loop(
        tmp_path, config, approval_callback=lambda _: False
    )
    result = runner.run()
    assert result.status == "aborted"
    log = (
        settings.runs_dir
        / result.run_id
        / "loop"
        / "iter_01"
        / "apply.log"
    ).read_text(encoding="utf-8")
    assert "Manual approval declined" in log
    assert (repo / "foo.txt").read_text(encoding="utf-8").strip() == "initial"


def test_loop_rollback(tmp_path: Path):
    config = LoopConfig(
        goal="Rollback test",
        max_iter=2,
        tests_command=_tests_command(),
    )
    repo, settings, runner = _run_simple_loop(tmp_path, config)
    result = runner.run()
    run_dir = settings.runs_dir / result.run_id / "loop"
    commit1 = (run_dir / "iter_01" / "commit.txt").read_text(encoding="utf-8").strip()
    assert commit1
    assert (repo / "foo.txt").read_text(encoding="utf-8").strip() == "iteration 2"
    run_loop_rollback(settings, result.run_id, 1, repo_root=repo)
    new_head = (
        subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        )
        .stdout.strip()
    )
    assert new_head == commit1
    assert (repo / "foo.txt").read_text(encoding="utf-8").strip() == "iteration 1"
