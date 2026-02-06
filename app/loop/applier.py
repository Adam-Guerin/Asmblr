from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Tuple

from app.loop.errors import LoopException


class LoopApplier:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self.git = shutil.which('git')
        if not self.git:
            raise LoopException('git is required for the loop runner.')

    def apply_patch(self, patch_text: str, dry_run: bool) -> Tuple[str, bool]:
        cmd = [self.git, 'apply', '--whitespace=nowarn']
        if dry_run:
            cmd.append('--check')
        else:
            cmd.append('--index')
        result = subprocess.run(cmd, input=patch_text.encode('utf-8'), cwd=self.repo_root, capture_output=True)
        stdout = result.stdout.decode('utf-8', errors='ignore')
        stderr = result.stderr.decode('utf-8', errors='ignore')
        log = stdout + stderr
        if result.returncode != 0:
            raise LoopException(f'git apply failed ({result.returncode}): {log}')
        return log, True
