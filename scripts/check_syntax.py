from __future__ import annotations

import argparse
import py_compile
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Compile selected Python paths to catch syntax errors.")
    parser.add_argument(
        "--paths",
        nargs="+",
        default=["app"],
        help="Repository-relative directories/files to syntax-check.",
    )
    args = parser.parse_args()

    targets = [repo_root / path for path in args.paths]
    failures: list[str] = []
    for root in targets:
        if not root.exists():
            continue
        candidates = [root] if root.is_file() else root.rglob("*.py")
        for path in candidates:
            if path.suffix != ".py":
                continue
            try:
                py_compile.compile(str(path), doraise=True)
            except py_compile.PyCompileError as exc:
                failures.append(f"{path}: {exc.msg}")
    if failures:
        print("Syntax check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Syntax check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
