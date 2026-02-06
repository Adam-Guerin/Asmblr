from __future__ import annotations

import py_compile
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [repo_root / "app"]
    failures: list[str] = []
    for root in targets:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
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
