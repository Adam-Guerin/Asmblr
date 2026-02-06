from pathlib import Path

from app.core.config import Settings
from app.loop.errors import LoopException
from app.loop.git_ops import GitOps


def run_loop_rollback(
    settings: Settings, run_id: str, to_iter: int, repo_root: Path | None = None
) -> str:
    loop_dir = settings.runs_dir / run_id / 'loop'
    target = loop_dir / f'iter_{to_iter:02d}' / 'commit.txt'
    if not target.exists():
        raise LoopException(f'Iteration {to_iter} does not exist for run {run_id}.')
    commit_hash = target.read_text(encoding='utf-8').strip()
    if not commit_hash:
        raise LoopException('No commit recorded for that iteration.')
    git_ops = GitOps(repo_root or Path.cwd())
    git_ops.reset_to(commit_hash)
    return commit_hash
