# Ralph Loop Prompt

You are running a single Ralph iteration. Treat this as fresh context.

Inputs:
- `prd.json`
- `progress.txt`

Rules:
- Implement ONLY the next story that has `passes: false`.
- Do not update `prd.json` or `progress.txt` yourself; the orchestrator will.
- Keep changes minimal and aligned to acceptance criteria.
- Run the provided test command and fix failures.
- Commit with a concise message if tests pass.

Output:
- A working change set that satisfies the story acceptance criteria.
