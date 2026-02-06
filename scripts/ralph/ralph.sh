#!/usr/bin/env bash
set -euo pipefail

MAX_ITER="${1:-5}"
TESTS="${2:-pytest -q}"
APPROVE_MODE="${APPROVE_MODE:-auto}"
PRD_PATH="${PRD_PATH:-prd.json}"
PROGRESS_PATH="${PROGRESS_PATH:-progress.txt}"
TAIL_LINES="${TAIL_LINES:-60}"

python -m app.cli ralph-loop \
  --max-iter "$MAX_ITER" \
  --tests "$TESTS" \
  --approve-mode "$APPROVE_MODE" \
  --prd-path "$PRD_PATH" \
  --progress-path "$PROGRESS_PATH" \
  --tail-lines "$TAIL_LINES"
