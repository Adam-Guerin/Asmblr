from __future__ import annotations


from app.loop.schemas import IterationVerdict


class LoopJudge:
    def __init__(self, max_total_diff_lines: int, max_patch_lines: int) -> None:
        self.max_total = max_total_diff_lines
        self.max_patch = max_patch_lines

    def evaluate(
        self,
        iteration: int,
        patch_lines: int,
        total_lines: int,
        tests_pass: bool,
        apply_success: bool,
        dry_run: bool,
    ) -> IterationVerdict:
        reasons: list[str] = []
        status = 'continue'
        if not apply_success and not dry_run:
            reasons.append('Patch failed to apply.')
            status = 'aborted'
        if patch_lines > self.max_patch:
            reasons.append(f'Iteration patch ({patch_lines}) exceeds per-step limit ({self.max_patch}).')
            status = 'aborted'
        if total_lines > self.max_total:
            reasons.append(f'Total diff ({total_lines}) exceeds global cap ({self.max_total}).')
            status = 'aborted'
        if not tests_pass and not dry_run:
            reasons.append('Tests failed.')
            status = 'aborted'
        metrics: dict[str, int | bool] = {
            'iteration': iteration,
            'patch_lines': patch_lines,
            'total_patch_lines': total_lines,
            'tests_pass': tests_pass,
            'apply_success': apply_success,
        }
        return IterationVerdict(status=status, reasons=reasons, metrics=metrics)
