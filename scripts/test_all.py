import argparse
import os
import subprocess
import sys
from typing import Sequence


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
    args = parser.parse_args()

    # Keep lint blocking but pragmatic: fail on critical correctness classes first.
    # (Repo still contains legacy style/unused-import debt outside current scope.)
    if _run([sys.executable, "-m", "ruff", "check", ".", "--select", "E9,F63,F7,F82"]) != 0:
        return 1

    if _run([sys.executable, "scripts/check_syntax.py"]) != 0:
        return 1

    if args.mode == "quick":
        core_tests = [
            "tests/test_scoring.py",
            "tests/test_signal_engine.py",
            "tests/test_generators.py",
            "tests/test_self_healing.py",
            "tests/test_onboarding_templates.py",
        ]
        if _run([sys.executable, "-m", "pytest", "-q", *core_tests]) != 0:
            return 1
    else:
        if _run([sys.executable, "-m", "pytest", "-q"]) != 0:
            return 1

    smoke_tests = [
        "tests/test_smoke_doctor_and_run.py::test_smoke_doctor_and_run",
        "tests/test_build_mvp.py::test_smoke_build_mvp_repo",
    ]
    env = os.environ.copy()
    env.setdefault("FAST_MODE", "true")
    env.setdefault("MAX_SOURCES", "2")
    env.setdefault("MIN_PAGES", "1")
    env.setdefault("MIN_PAINS", "1")
    env.setdefault("MIN_COMPETITORS", "0")
    env.setdefault("MARKET_SIGNAL_THRESHOLD", "0")
    env.setdefault("SIGNAL_QUALITY_THRESHOLD", "0")
    if _run([sys.executable, "-m", "pytest", "-q", *smoke_tests], env=env) != 0:
        return 1

    print("Quality gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
