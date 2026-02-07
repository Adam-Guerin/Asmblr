from pathlib import Path

from app.mvp_cycles import MVPProgression
from app.core.config import Settings


def _make_settings(tmp_path: Path) -> Settings:
    settings = Settings()
    settings.runs_dir = tmp_path
    settings.data_dir = tmp_path / "data"
    return settings


def _mk_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_check_logs_parses_success(tmp_path: Path) -> None:
    settings = _make_settings(tmp_path)
    run_dir = settings.runs_dir / "run1"
    cycle_dir = run_dir / "mvp_cycles" / "cycle_1_foundation"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _mk_file(cycle_dir / "build.log", "Return code: 0\n")
    _mk_file(cycle_dir / "test.log", "Return code: 0\n")
    _mk_file(cycle_dir / "smoke_1.log", "Result: pass\n")

    prog = MVPProgression(run_id="run1", run_dir=run_dir, settings=settings, llm_enabled=False)
    checks = prog._check_logs(cycle_dir, "foundation")
    assert any(c["name"] == "build_log_clean" and c["ok"] for c in checks)
    assert any(c["name"] == "test_log_clean" and c["ok"] for c in checks)
    assert any(c["name"] == "smoke_log_pass" and c["ok"] for c in checks)


def test_check_logs_detects_failure(tmp_path: Path) -> None:
    settings = _make_settings(tmp_path)
    run_dir = settings.runs_dir / "run2"
    cycle_dir = run_dir / "mvp_cycles" / "cycle_2_ux"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _mk_file(cycle_dir / "build.log", "Return code: 1\nError:\nboom\n")
    _mk_file(cycle_dir / "test.log", "Return code: 1\n")

    prog = MVPProgression(run_id="run2", run_dir=run_dir, settings=settings, llm_enabled=False)
    checks = prog._check_logs(cycle_dir, "ux")
    assert any(c["name"] == "build_log_clean" and not c["ok"] for c in checks)
    assert any(c["name"] == "test_log_clean" and not c["ok"] for c in checks)


def test_check_ux_and_polish_requirements(tmp_path: Path) -> None:
    settings = _make_settings(tmp_path)
    run_dir = settings.runs_dir / "run3"
    repo = run_dir / "mvp_repo"

    # UX requirements
    _mk_file(
        repo / "app" / "globals.css",
        "body { font-family: var(--font-sans); }\n"
        "--font-sans: test;\n--color-bg: #fff;\n--space-2: 0.5rem;\n--radius-sm: 10px;\n--shadow-soft: test;\n",
    )
    for name in [
        "button.tsx",
        "card.tsx",
        "badge.tsx",
        "input.tsx",
        "label.tsx",
        "empty-state.tsx",
        "skeleton.tsx",
        "toast.tsx",
        "toaster.tsx",
    ]:
        _mk_file(repo / "components" / "ui" / name, "export const X = () => null;\n")
    _mk_file(repo / "components" / "layout" / "app-shell.tsx", "export const X = () => null;\n")
    _mk_file(repo / "app" / "page.tsx", "<h1>Heading</h1><h2>Subheading</h2><div className='max-w-6xl'></div>\n")

    prog = MVPProgression(run_id="run3", run_dir=run_dir, settings=settings, llm_enabled=False)
    ux_checks = prog._check_ux(repo)
    assert all(item["ok"] for item in ux_checks), ux_checks

    # Polish requirements
    _mk_file(repo / "app" / "loading.tsx", "Loading\n")
    _mk_file(repo / "components" / "ui" / "empty-state.tsx", "EmptyState\n")
    _mk_file(repo / "components" / "ui" / "skeleton.tsx", "Skeleton\n")
    _mk_file(repo / "components" / "ui" / "toast.tsx", "Toast\n")
    _mk_file(repo / "components" / "ui" / "toaster.tsx", "Toaster\n")
    _mk_file(repo / "app" / "globals.css", ".shadow-soft {}\n.shadow-card {}\n")
    _mk_file(repo / "app" / "app" / "settings" / "page.tsx", "useToast\nWorkspace name is required\n")

    polish_checks = prog._check_polish(repo)
    assert all(item["ok"] for item in polish_checks), polish_checks
