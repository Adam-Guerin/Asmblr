from pathlib import Path
import json

from app.core.config import Settings
from app.mvp_cycles import MVPProgression


class FakeLLM:
    def __init__(self, diff: str) -> None:
        self.diff = diff
        self.last_prompt = ""

    def available(self) -> bool:
        return True

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.diff


FOUNDATION_DIFF = """diff --git a/mvp_repo/foundation_notes.md b/mvp_repo/foundation_notes.md
new file mode 100644
index 0000000..e69de29
--- /dev/null
+++ b/mvp_repo/foundation_notes.md
@@ -0,0 +1,3 @@
+LLM foundation note.
+Cycle 1 ensures the repo baseline.
+Signal: prompt-driven patch applied.
+"""


def test_foundation_cycle_applies_prompt_patch(tmp_path: Path) -> None:
    settings = Settings(enable_progressive_cycles=True, runs_dir=tmp_path)
    settings.mvp_build_command = ""
    settings.mvp_test_command = ""
    settings.mvp_dev_command = ""
    llm = FakeLLM(FOUNDATION_DIFF)
    run_dir = tmp_path / "run-mvp"
    progression = MVPProgression(
        run_id="run-mvp",
        run_dir=run_dir,
        settings=settings,
        llm_client=llm,
    )
    progression.run_ui_lint = lambda *_args, **_kwargs: (True, "ok")  # type: ignore[method-assign]
    progression.verify_cycle_requirements = lambda *_args, **_kwargs: True  # type: ignore[method-assign]
    progression.run_smoke_checks = lambda *_args, **_kwargs: True  # type: ignore[method-assign]
    progression.run()

    foundation_note = run_dir / "mvp_repo" / "foundation_notes.md"
    assert foundation_note.exists()
    assert "LLM foundation note" in foundation_note.read_text()

    patch_log = run_dir / "mvp_cycles" / "cycle_1_foundation" / "patch.log"
    assert patch_log.exists()
    assert "Diff" in patch_log.read_text()

    build_log = run_dir / "mvp_cycles" / "cycle_1_foundation" / "build.log"
    test_log = run_dir / "mvp_cycles" / "cycle_1_foundation" / "test.log"
    assert "skipped" in build_log.read_text().lower()
    assert "skipped" in test_log.read_text().lower()


def test_manual_steering_is_injected_into_cycle_prompt_and_repo(tmp_path: Path) -> None:
    settings = Settings(enable_progressive_cycles=True, runs_dir=tmp_path)
    settings.mvp_build_command = ""
    settings.mvp_test_command = ""
    settings.mvp_dev_command = ""
    llm = FakeLLM(FOUNDATION_DIFF)
    run_dir = tmp_path / "run-mvp-steering"
    steering_path = run_dir / "mvp_steering.jsonl"
    steering_path.parent.mkdir(parents=True, exist_ok=True)
    steering_path.write_text(
        json.dumps(
            {
                "timestamp": "2026-02-06T00:00:00Z",
                "author": "founder",
                "message": "Pivot vers freelances et onboarding ultra-court.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    progression = MVPProgression(
        run_id="run-mvp-steering",
        run_dir=run_dir,
        settings=settings,
        llm_client=llm,
    )
    progression.run_ui_lint = lambda *_args, **_kwargs: (True, "ok")  # type: ignore[method-assign]
    progression.verify_cycle_requirements = lambda *_args, **_kwargs: True  # type: ignore[method-assign]
    progression.run_smoke_checks = lambda *_args, **_kwargs: True  # type: ignore[method-assign]
    progression.run()

    assert "Pivot vers freelances" in llm.last_prompt
    plan_md = (run_dir / "mvp_cycles" / "cycle_1_foundation" / "plan.md").read_text(encoding="utf-8")
    assert "Manual steering" in plan_md
    assert "onboarding ultra-court" in plan_md
    steering_note = run_dir / "mvp_repo" / ".asmblr" / "steering.md"
    assert steering_note.exists()
    assert "Pivot vers freelances" in steering_note.read_text(encoding="utf-8")
