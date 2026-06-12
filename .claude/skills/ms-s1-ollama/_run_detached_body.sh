#!/usr/bin/env bash
# Body of a detached benchmark run — executed by systemd via run_detached.sh.
# A separate FILE (not an inline bash -c string) by design: the 3-shell-layer
# quoting trap (PowerShell/git-bash -> wsl bash -lc -> bash -c) mangled inline
# command substitution during the 2026-06-12 probe; a script file has exactly
# one shell layer.
set -u
export PATH="$HOME/.local/bin:$PATH"   # systemd user env lacks the login PATH (uv lives here)
cd "$HOME/work/vero-lite"
OUT=${1:?out prefix (e.g. .claude/benchmark-results/<run-name>)}
shift || true
echo "[wrap] START $(date -Iseconds)" > "$OUT.wrap"
PYTHONUNBUFFERED=1 uv run python -m benchmarks.procedure_baseline.run_benchmark \
  --ollama-host "${OLLAMA_HOST_URL:-http://192.168.1.133:11434}" --warm \
  --dump-json "$OUT.jsonl" "$@" > "$OUT.log" 2>&1
rc=$?
echo "[wrap] EXIT=$rc $(date -Iseconds)" >> "$OUT.wrap"
# Sentinel LAST: its existence == the run is over; its content == rc + when.
echo "$rc $(date -Iseconds)" > "$OUT.done"
exit "$rc"
