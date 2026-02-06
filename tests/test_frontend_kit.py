from pathlib import Path
import json
import re

from app.core.config import Settings
from app.mvp.frontend_kit.scaffold import write_frontend_scaffold
from app.mvp.ui_lint import count_components, count_pages, run_ui_lint
from app.mvp_cycles import MVPProgression


def test_frontend_scaffold_generates_required_files(tmp_path: Path) -> None:
    repo_dir = tmp_path / "mvp_repo"
    write_frontend_scaffold(
        repo_dir,
        "Atlas",
        brief="Atlas helps operators launch faster with clear pricing and proof.",
        audience="early-stage operators",
        style="startup_clean",
    )

    assert (repo_dir / "app" / "page.tsx").exists()
    assert (repo_dir / "app" / "app" / "page.tsx").exists()
    assert (repo_dir / "app" / "app" / "marketplace" / "page.tsx").exists()
    assert (repo_dir / "app" / "app" / "settings" / "page.tsx").exists()
    assert (repo_dir / "components" / "layout" / "app-shell.tsx").exists()
    assert (repo_dir / "components" / "ui" / "button.tsx").exists()
    assert (repo_dir / "components" / "ui" / "toast.tsx").exists()
    assert (repo_dir / "app" / "global-error.tsx").exists()
    assert (repo_dir / "app" / "loading.tsx").exists()

    assert count_pages(repo_dir) >= 3
    assert count_components(repo_dir) >= 5


def test_frontend_kit_lockfile_required_files_exist(tmp_path: Path) -> None:
    repo_dir = tmp_path / "mvp_repo"
    write_frontend_scaffold(
        repo_dir,
        "Atlas",
        brief="Atlas helps operators launch faster with clear pricing and proof.",
        audience="early-stage operators",
        style="startup_clean",
    )

    kit_lock = Path(__file__).resolve().parents[1] / "app" / "mvp" / "frontend_kit" / "lockfile.json"
    assert kit_lock.exists()
    lock_payload = json.loads(kit_lock.read_text(encoding="utf-8"))
    required = lock_payload.get("required_files", [])
    assert required

    for rel_path in required:
        assert (repo_dir / rel_path).exists(), rel_path

    assert (repo_dir / "frontend_kit.lock.json").exists()


def test_ui_lint_flags_banned_copy_and_contrast(tmp_path: Path) -> None:
    repo_dir = tmp_path / "mvp_repo"
    (repo_dir / "app").mkdir(parents=True, exist_ok=True)
    (repo_dir / "components").mkdir(parents=True, exist_ok=True)
    (repo_dir / "app" / "layout.tsx").write_text(
        "import { ToastProvider } from '@/components/ui/use-toast';\n"
        "import { Toaster } from '@/components/ui/toaster';\n"
        "export default function RootLayout({ children }) { return (<ToastProvider>{children}<Toaster /></ToastProvider>); }\n",
        encoding="utf-8",
    )
    (repo_dir / "app" / "page.tsx").write_text(
        "const sectionOrder = ['Hero','Features','HowItWorks','SocialProof','Pricing','FAQ','CTA','Footer'] as const;\n"
        "<p className=\"text-slate-300\">Lorem ipsum copy.</p>",
        encoding="utf-8",
    )
    (repo_dir / "components" / "ui").mkdir(parents=True, exist_ok=True)
    (repo_dir / "components" / "ui" / "empty-state.tsx").write_text("export const X=()=>null;", encoding="utf-8")
    (repo_dir / "app" / "loading.tsx").write_text("loading", encoding="utf-8")
    (repo_dir / "app" / "error.tsx").write_text("error", encoding="utf-8")
    (repo_dir / "app" / "not-found.tsx").write_text("notfound", encoding="utf-8")
    (repo_dir / "app" / "global-error.tsx").write_text("global", encoding="utf-8")

    cycle_dir = tmp_path / "cycle"
    result = run_ui_lint(repo_dir, cycle_dir)
    assert result["ok"] is False
    rules = {item["rule"] for item in result["errors"]}
    assert "contrast" in rules
    assert "banned_copy" in rules


def test_ui_lint_passes_on_scaffold(tmp_path: Path) -> None:
    repo_dir = tmp_path / "mvp_repo"
    write_frontend_scaffold(
        repo_dir,
        "Signalroom",
        brief="Signalroom helps founders present a crisp launch narrative.",
        audience="founders and product leads",
        style="startup_clean",
    )
    cycle_dir = tmp_path / "cycle"
    result = run_ui_lint(repo_dir, cycle_dir)
    assert result["ok"] is True


def test_landing_snapshot_sections_and_copy_lengths(tmp_path: Path) -> None:
    repo_dir = tmp_path / "mvp_repo"
    brief = "Signalroom helps founders present a crisp launch narrative."
    audience = "founders and product leads"
    write_frontend_scaffold(
        repo_dir,
        "Signalroom",
        brief=brief,
        audience=audience,
        style="startup_clean",
    )

    page = (repo_dir / "app" / "page.tsx").read_text(encoding="utf-8")
    sections: list[str] = []
    for match in re.finditer(r"data-section=['\"]([A-Za-z]+)['\"]", page):
        label = match.group(1)
        if label not in sections:
            sections.append(label)

    def _count_in_block(block_name: str, field_pattern: str) -> int:
        match = re.search(rf"{block_name}:\s*\[(.*?)\]", page, re.S)
        if not match:
            return 0
        return len(re.findall(field_pattern, match.group(1)))

    snapshot = "\n".join(
        [
            f"sections: {' > '.join(sections)}",
            f"features: {_count_in_block('features', r'title:')}",
            f"steps: {_count_in_block('steps', r'title:')}",
            f"testimonials: {_count_in_block('testimonials', r'quote:')}",
            f"pricing: {_count_in_block('pricing', r'name:')}",
            f"faqs: {_count_in_block('faqs', r'q:')}",
            "headline_max: 60",
            "subhead_max: 120",
            "support_max: 120",
        ]
    )
    snapshot_path = Path(__file__).resolve().parent / "fixtures" / "landing_snapshot.txt"
    assert snapshot_path.exists()
    assert snapshot == snapshot_path.read_text(encoding="utf-8").strip()

    assert "trimCopy(`Launch a story ${audienceTrimmed} trust.`" in page
    assert "trimCopy(tagLine, 120)" in page
    assert len(brief) <= 120

    literals = re.findall(r"'([^\\n']+)'", page)
    long_literals = [text for text in literals if len(text) > 120]
    assert long_literals == []


def test_ui_lint_flags_missing_sections_states_toaster(tmp_path: Path) -> None:
    repo_dir = tmp_path / "mvp_repo"
    (repo_dir / "app").mkdir(parents=True, exist_ok=True)
    (repo_dir / "components").mkdir(parents=True, exist_ok=True)
    (repo_dir / "app" / "page.tsx").write_text("<main>Landing</main>", encoding="utf-8")
    (repo_dir / "app" / "layout.tsx").write_text(
        "<html><body>No toaster</body></html>", encoding="utf-8"
    )

    cycle_dir = tmp_path / "cycle"
    result = run_ui_lint(repo_dir, cycle_dir)
    assert result["ok"] is False
    rules = {item["rule"] for item in result["errors"]}
    assert "landing_sections" in rules
    assert "required_states" in rules
    assert "toaster_usage" in rules


def test_ui_lint_flags_microcopy_rubric(tmp_path: Path) -> None:
    repo_dir = tmp_path / "mvp_repo"
    (repo_dir / "app").mkdir(parents=True, exist_ok=True)
    (repo_dir / "components").mkdir(parents=True, exist_ok=True)
    (repo_dir / "app" / "layout.tsx").write_text(
        "import { ToastProvider } from '@/components/ui/use-toast';\n"
        "import { Toaster } from '@/components/ui/toaster';\n"
        "export default function RootLayout({ children }) { return (<ToastProvider>{children}<Toaster /></ToastProvider>); }\n",
        encoding="utf-8",
    )
    (repo_dir / "app" / "page.tsx").write_text(
        "import { Button } from '@/components/ui/button';\n"
        "const sectionOrder = ['Hero','Features','HowItWorks','SocialProof','Pricing','FAQ','CTA','Footer'] as const;\n"
        "export default function Page(){return (<main><Button>Explore the platform now</Button><p>We deliver synergy.</p></main>)}\n",
        encoding="utf-8",
    )
    (repo_dir / "components" / "ui" / "empty-state.tsx").write_text("export const X=()=>null;", encoding="utf-8")
    (repo_dir / "app" / "loading.tsx").write_text("loading", encoding="utf-8")
    (repo_dir / "app" / "error.tsx").write_text("error", encoding="utf-8")
    (repo_dir / "app" / "not-found.tsx").write_text("notfound", encoding="utf-8")
    (repo_dir / "app" / "global-error.tsx").write_text("global", encoding="utf-8")

    result = run_ui_lint(repo_dir, tmp_path / "cycle")
    assert result["ok"] is False
    rules = {item["rule"] for item in result["errors"]}
    assert "microcopy_rubric" in rules


def test_progressive_cycles_write_ui_lint_and_verdict(tmp_path: Path) -> None:
    settings = Settings()
    settings.runs_dir = tmp_path
    settings.mvp_build_command = ""
    settings.mvp_test_command = ""
    settings.mvp_install_command = ""
    run_dir = tmp_path / "run-cycles"

    progression = MVPProgression(
        run_id="run-cycles",
        run_dir=run_dir,
        settings=settings,
        llm_enabled=False,
        cycle_keys=["ux"],
    )
    progression.run()

    cycle_dir = run_dir / "mvp_cycles" / "cycle_1_ux"
    assert (cycle_dir / "ui_lint.json").exists()
    verdict = cycle_dir / "verdict.json"
    assert verdict.exists()
    payload = verdict.read_text(encoding="utf-8")
    assert "ui_lint_ok" in payload
    assert "pages_count" in payload
    alias_dir = run_dir / "mvp_cycles" / "ux"
    assert (alias_dir / "ui_lint.json").exists()
    assert (alias_dir / "verdict.json").exists()
