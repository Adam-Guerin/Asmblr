from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Sequence

from app.loop.errors import LoopException


class GitOps:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self.active_root = self.repo_root
        self.git = shutil.which('git')
        if not self.git:
            raise LoopException('Git is required for loop operations.')

    def run_git(self, args: Sequence[str], check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        cwd = cwd or self.active_root
        result = subprocess.run(
            [self.git, *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check,
        )
        return result

    def is_git_repo(self) -> bool:
        try:
            self.run_git(['rev-parse', '--is-inside-work-tree'])
            return True
        except subprocess.CalledProcessError:
            return False

    def status_porcelain(self) -> str:
        result = self.run_git(['status', '--porcelain'], check=False)
        return result.stdout.strip()

    def prepare_workspace(self, loop_dir: Path) -> Path:
        if not self.is_git_repo():
            raise LoopException('Loop requires a git repository. Please initialize git before running the loop.')
        status = self.status_porcelain()
        if status:
            worktree_dir = loop_dir / 'worktree'
            if worktree_dir.exists():
                shutil.rmtree(worktree_dir)
            self.run_git(['worktree', 'add', '--detach', str(worktree_dir), 'HEAD'], cwd=self.repo_root)
            self.active_root = worktree_dir.resolve()
        else:
            self.active_root = self.repo_root
        return self.active_root

    def commit(self, message: str) -> str:
        self.run_git(['add', '--all'])
        try:
            self.run_git(['commit', '-m', message])
        except subprocess.CalledProcessError as exc:
            raise LoopException(f'Git commit failed: {exc.stderr}')
        return self.head_commit()

    def head_commit(self) -> str:
        result = self.run_git(['rev-parse', 'HEAD'])
        return result.stdout.strip()

    def reset_to(self, commit: str) -> None:
        self.run_git(['reset', '--hard', commit])
