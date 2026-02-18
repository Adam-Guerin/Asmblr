import json
from pathlib import Path
import json

import pytest

from app.core.config import Settings
from app.mvp.builder import MVPBuilder


class DummyVerifier:
    def __init__(self, build_success: bool = True, test_success: bool = True) -> None:
        self.build_success = build_success
        self.test_success = test_success

    def run_build(self, attempt: int | None = None) -> tuple[bool, str]:
        return self.build_success, f"build attempt {attempt}"

    def run_test(self, attempt: int | None = None) -> tuple[bool, str]:
        return self.test_success, f"test attempt {attempt}"


@pytest.fixture(autouse=True)
def stub_ollama(monkeypatch):
    monkeypatch.setattr("app.mvp.builder.check_ollama", lambda *args, **kwargs: {})


def _patch_verifier(monkeypatch, build_success: bool = True, test_success: bool = True):
    verifier = DummyVerifier(build_success=build_success, test_success=test_success)
    monkeypatch.setattr("app.mvp.builder.MVPVerifier", lambda repo_dir: verifier)
    return verifier


def test_build_mvp_creates_directories_even_on_failure(tmp_path: Path, monkeypatch) -> None:
    settings = Settings(runs_dir=tmp_path / "runs", data_dir=tmp_path / "data")
    builder = MVPBuilder(settings)
    run_id = builder.manager.create_run("mvp audit")
    builder.manager.update_status(run_id, "RUNNING")
    _patch_verifier(monkeypatch, build_success=False, test_success=True)

    result = builder.build_from_run(run_id, brief="Test MVP build", max_fix_iter=1, force=True)

    run_dir = settings.runs_dir / run_id
    assert (run_dir / "mvp_repo").exists()
    assert (run_dir / "mvp_cycles" / "cycle_1_foundation").exists()
    assert (run_dir / "mvp_cycles" / "cycle_1_foundation" / "build.log").exists()
    assert (run_dir / "mvp_cycles" / "cycle_1_foundation" / "test.log").exists()
    assert (run_dir / "mvp_cycles" / "cycle_1_foundation" / "verdict.json").exists()
    assert (run_dir / "mvp_build_summary.md").exists()
    assert (run_dir / "mvp_data_source.json").exists()
    assert not result.success


def test_build_mvp_from_abort_run_marks_seed_source(tmp_path: Path, monkeypatch) -> None:
    settings = Settings(runs_dir=tmp_path / "runs", data_dir=tmp_path / "data")
    builder = MVPBuilder(settings)
    run_id = builder.manager.create_run("urgent idea")
    builder.manager.update_status(run_id, "ABORT")
    _patch_verifier(monkeypatch, build_success=True, test_success=True)

    result = builder.build_from_run(run_id, brief="Urgent MVP build", force=True)
    data_source = json.loads((result.run_dir / "mvp_data_source.json").read_text(encoding="utf-8"))
    assert data_source["data_source"] == "seed/abort"


def test_build_mvp_brief_creates_adhoc_run(tmp_path: Path, monkeypatch) -> None:
    settings = Settings(runs_dir=tmp_path / "runs", data_dir=tmp_path / "data")
    builder = MVPBuilder(settings)
    output_dir = settings.runs_dir / "_adhoc" / "brief-test"
    _patch_verifier(monkeypatch, build_success=True, test_success=True)

    result = builder.build_from_brief("Tiny automation", output_dir, force=True)

    assert (result.run_dir / "mvp_repo").exists()
    assert (result.run_dir / "mvp_scope.json").exists()


def test_smoke_build_mvp_repo(tmp_path: Path, monkeypatch) -> None:
    settings = Settings(runs_dir=tmp_path / "runs", data_dir=tmp_path / "data")
    # Override dev command for test environment to skip smoke checks
    settings.mvp_dev_command = ""
    builder = MVPBuilder(settings)
    _patch_verifier(monkeypatch, build_success=True, test_success=True)

    kit_lock = Path(__file__).resolve().parents[1] / "app" / "mvp" / "frontend_kit" / "lockfile.json"
    required_files = json.loads(kit_lock.read_text(encoding="utf-8")).get("required_files", [])

    def build_runner(cycle_key: str, cycle_dir: Path, attempt: int) -> tuple[bool, str]:
        repo_dir = cycle_dir.parents[1] / "mvp_repo"  # Go up to smoke-build then mvp_repo
        missing = [path for path in required_files if not (repo_dir / path).exists()]
        ok = len(missing) == 0
        return ok, f"Return code: {0 if ok else 1}\nbuild {attempt} ok={ok}"

    def test_runner(cycle_key: str, cycle_dir: Path, attempt: int) -> tuple[bool, str]:
        return True, f"Return code: 0\nsmoke test {cycle_key} attempt {attempt}"

    output_dir = settings.runs_dir / "_adhoc" / "smoke-build"
    result = builder.build_from_brief(
        "Smoke build MVP",
        output_dir,
        force=True,
        build_runner=build_runner,
        test_runner=test_runner,
    )

    assert result.success
