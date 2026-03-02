import argparse
import os
import subprocess
import sys
from collections.abc import Sequence

LINT_TARGETS = ["app/core", "app/tools", "app/loop", "app/mvp", "scripts", "tests"]
SYNTAX_TARGETS = ["app/core", "app/tools", "app/loop", "scripts", "tests"]


def _run(cmd: Sequence[str], env: dict | None = None) -> int:
    print("Running:", " ".join(cmd))
    return subprocess.call(list(cmd), env=env)


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified quality gate: lint + tests + smoke MVP.")
    parser.add_argument(
        "--mode",
        choices=["full", "quick"],
        default="full",
        help="quick skips heavy/full suite and keeps lint + core + smoke.",
    )
    parser.add_argument(
        "--strict-progressive",
        action="store_true",
        help="Fail when the progressive Ruff pass still reports issues.",
    )
    parser.add_argument(
        "--progressive-select",
        default="F401,F841,E722,E711,E712,E721,UP,SIM,B",
        help="Comma-separated Ruff rule groups for progressive debt reduction.",
    )
    args = parser.parse_args()

    # Keep lint blocking but pragmatic: fail on critical correctness classes first.
    # (Repo still contains legacy style/unused-import debt outside current scope.)
    if _run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            *LINT_TARGETS,
            "--select",
            "E9,F63,F7,F82",
            "--extend-ignore",
            "F821,F823",
        ]
    ) != 0:
        return 1

    # Progressive pass: broader checks without blocking by default.
    # In local runs (non-CI), apply safe autofixes to chip away at debt.
    progressive_cmd = [
        sys.executable,
        "-m",
        "ruff",
        "check",
        ".",
        "--select",
        args.progressive_select,
    ]
    if os.getenv("CI", "").lower() not in {"1", "true", "yes"}:
        progressive_cmd.append("--fix")
    progressive_rc = _run(progressive_cmd)
    if progressive_rc != 0 and args.strict_progressive:
        return 1
    if progressive_rc != 0:
        print("Progressive Ruff pass found remaining issues (non-blocking).")

    if _run([sys.executable, "scripts/check_syntax.py", "--paths", *SYNTAX_TARGETS]) != 0:
        return 1

    if args.mode == "quick":
        pytest_quick_base = [sys.executable, "-m", "pytest", "-q", "--no-cov"]
        core_tests = [
            "tests/test_scoring.py",
            "tests/test_signal_engine.py",
            "tests/test_generators.py",
            "tests/test_self_healing.py",
            "tests/test_onboarding_templates.py",
        ]
        if _run([*pytest_quick_base, *core_tests]) != 0:
            return 1
    else:
        if _run([sys.executable, "-m", "pytest", "-q"]) != 0:
            return 1

    smoke_tests = [
        "tests/test_generators.py::test_landing_generator_creates_html_files",
        "tests/test_generators.py::test_content_generator_creates_pack_files",
        "tests/test_project_build.py::test_project_builder_creates_documents_and_app",
    ]
    env = os.environ.copy()
    env.setdefault("FAST_MODE", "true")
    env.setdefault("MAX_SOURCES", "2")
    env.setdefault("MIN_PAGES", "1")
    env.setdefault("MIN_PAINS", "1")
    env.setdefault("MIN_COMPETITORS", "0")
    env.setdefault("MARKET_SIGNAL_THRESHOLD", "0")
    env.setdefault("SIGNAL_QUALITY_THRESHOLD", "0")
    smoke_cmd = [sys.executable, "-m", "pytest", "-q", *smoke_tests]
    if args.mode == "quick":
        smoke_cmd.insert(4, "--no-cov")
    if _run(smoke_cmd, env=env) != 0:
        return 1

    print("Quality gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

