#!/usr/bin/env bash

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
RUNS="${RUNS:-3}"
MAX_WORKERS="${MAX_WORKERS:-4}"
PROTOCOLS="${PROTOCOLS:-multiturn structured}"
CACHE_ROOT="${CACHE_ROOT:-result}"
OUTPUT_BASE="${OUTPUT_BASE:-result}"
DATA_DIR="${DATA_DIR:-data}"
DRY_RUN="${DRY_RUN:-0}"
FAILED_TASKS=0
STOP_REQUESTED=0
TOTAL_PROTOCOLS=0
for _protocol in $PROTOCOLS; do
  TOTAL_PROTOCOLS=$((TOTAL_PROTOCOLS + 1))
done
TOTAL_TASKS=$((RUNS * TOTAL_PROTOCOLS))
TASK_INDEX=0

on_interrupt() {
  STOP_REQUESTED=1
  printf 'interrupt received, will stop after current task\n'
}

trap on_interrupt INT

for run in $(seq 1 "$RUNS"); do
  for protocol in $PROTOCOLS; do
    if [[ "$STOP_REQUESTED" -eq 1 ]]; then
      break 2
    fi
    TASK_INDEX=$((TASK_INDEX + 1))
    cmd=(
      "$PYTHON_BIN"
      "$ROOT_DIR/acc_test/run_benchmark.py"
      --protocol "$protocol"
      --data-dir "$DATA_DIR"
      --max-workers "$MAX_WORKERS"
      --cache-root "$CACHE_ROOT"
      --output-root "$OUTPUT_BASE/run$run"
      "$@"
    )

    printf '[%d/%d] run=%d protocol=%s output=%s/run%d\n' \
      "$TASK_INDEX" \
      "$TOTAL_TASKS" \
      "$run" \
      "$protocol" \
      "$OUTPUT_BASE" \
      "$run"

    if [[ "$DRY_RUN" == "1" ]]; then
      printf '%q ' "${cmd[@]}"
      printf '\n'
    else
      if "${cmd[@]}"; then
        printf '[%d/%d] done run=%d protocol=%s\n' \
          "$TASK_INDEX" \
          "$TOTAL_TASKS" \
          "$run" \
          "$protocol"
      else
        FAILED_TASKS=$((FAILED_TASKS + 1))
        printf '[%d/%d] failed run=%d protocol=%s\n' \
          "$TASK_INDEX" \
          "$TOTAL_TASKS" \
          "$run" \
          "$protocol"
      fi
    fi
  done
done

if [[ "$DRY_RUN" != "1" && "$FAILED_TASKS" -gt 0 ]]; then
  printf 'completed with %d failed task(s)\n' "$FAILED_TASKS"
  exit 1
fi

if [[ "$DRY_RUN" != "1" && "$STOP_REQUESTED" -eq 1 ]]; then
  printf 'stopped by interrupt\n'
  exit 130
fi
