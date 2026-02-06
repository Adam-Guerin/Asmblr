import os
import subprocess
import sys
from typing import List

import httpx


def _ollama_ready(base_url: str, models: List[str]) -> bool:
    try:
        timeout = httpx.Timeout(5.0, connect=3.0, read=5.0, write=5.0, pool=3.0)
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(f"{base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return False

    available = {m.get("name") for m in data.get("models", []) if isinstance(m, dict)}
    missing = [m for m in models if m and m not in available]
    return not missing


def main() -> int:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    models = [os.getenv("GENERAL_MODEL", ""), os.getenv("CODE_MODEL", "")]
    if not _ollama_ready(base_url, models):
        print("Ollama not ready or missing models. Skipping E2E run.")
        return 0

    cmd = [sys.executable, "-m", "app", "run", "--topic", "CI smoke test", "--fast"]
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
