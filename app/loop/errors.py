class LoopException(RuntimeError):
    """Base exception for loop failures."""


class LoopAbort(LoopException):
    """Used when the loop must stop and record an abort."""
