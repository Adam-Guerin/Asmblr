from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import Tuple


class LoopVerifier:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def run(self, command: str) -> Tuple[bool, str]:
        if not command:
            return True, 'Tests skipped (no command provided).'
        splitter = shlex.split(command, posix=(os.name != 'nt'))
        try:
            proc = subprocess.run(
                splitter,
                capture_output=True,
                text=True,
                cwd=self.repo_root,
                timeout=300,
            )
            output = proc.stdout + proc.stderr
            return proc.returncode == 0, output
        except subprocess.TimeoutExpired as exc:
            return False, f'Tests timed out: {exc}'.strip()
        except FileNotFoundError as exc:
            return False, f'Command not found: {exc}'
