from __future__ import annotations

import json
import subprocess
import shutil
from pathlib import Path
from collections.abc import Iterable


class MVPVerifier:
    def __init__(
        self,
        repo_dir: Path,
        install_timeout: int = 600,
        build_timeout: int = 300,
        test_timeout: int = 300,
        shell: bool = False,
    ) -> None:
        self.repo_dir = repo_dir
        self.install_timeout = install_timeout
        self.build_timeout = build_timeout
        self.test_timeout = test_timeout
        self.shell = shell
        self._installed = False
        self._npm_path = shutil.which("npm")
        self._npm_available = self._npm_path is not None
        self._scripts = self._load_scripts()

    def run_install(self) -> tuple[bool, str]:
        if not self._npm_available:
            return False, "npm install failed: npm not found on PATH."
        if self._installed:
            return True, "npm install already executed."
        success, log = self._run_command(
            [self._npm_path or "npm", "install"],
            label="install",
            timeout=self.install_timeout,
        )
        if success:
            self._installed = True
        return success, log

    def run_build(self, attempt: int | None = None) -> tuple[bool, str]:
        if not self._npm_available:
            return False, "npm run build failed: npm not found on PATH."
        install_ok, install_log = self.run_install()
        if not install_ok:
            return False, f"Install prerequisite failed:\n{install_log}"
        return self._run_command(
            [self._npm_path or "npm", "run", "build"],
            label="build",
            timeout=self.build_timeout,
            attempt=attempt,
        )

    def run_test(self, attempt: int | None = None) -> tuple[bool, str]:
        if not self._npm_available:
            return False, "npm test failed: npm not found on PATH."
        if "test" not in self._scripts:
            return False, "npm test failed: test script missing in package.json."
        return self._run_command(
            [self._npm_path or "npm", "test"],
            label="test",
            timeout=self.test_timeout,
            attempt=attempt,
        )

    def _load_scripts(self) -> dict[str, str]:
        package_path = self.repo_dir / "package.json"
        if not package_path.exists():
            return {}
        try:
            payload = json.loads(package_path.read_text(encoding="utf-8"))
            scripts = payload.get("scripts", {})
            if isinstance(scripts, dict):
                return {str(key): str(value) for key, value in scripts.items()}
        except json.JSONDecodeError:
            pass
        return {}

    def _run_command(
        self,
        command: Iterable[str],
        label: str,
        timeout: int,
        attempt: int | None = None,
    ) -> tuple[bool, str]:
        name = " ".join(command)
        attempt_hint = f" (attempt {attempt})" if attempt else ""
        header = f"{label.title()}{attempt_hint}"
        try:
            proc = subprocess.run(
                list(command),
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout,
                shell=self.shell,
            )
        except subprocess.TimeoutExpired as exc:
            return False, f"{header} timed out after {timeout} seconds: {exc}"
        except Exception as exc:
            return False, f"{header} failed to start: {exc}"
        lines = [
            header,
            f"Command: {name}",
            f"Return code: {proc.returncode}",
        ]
        if proc.stdout:
            lines.append(f"stdout:\n{proc.stdout.strip()}")
        if proc.stderr:
            lines.append(f"stderr:\n{proc.stderr.strip()}")
        return proc.returncode == 0, "\n".join(lines)
