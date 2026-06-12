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
# Sentinel: its existence == the run is over; its content == rc + when.
# (Still the authoritative completion signal — the ping below is post-sentinel
# best-effort and can never delay or block it.)
echo "$rc $(date -Iseconds)" > "$OUT.done"
# Unit-side completion ping (2026-06-12 lesson: a harness-side watcher is a
# wsl.exe carrier — it false-alarms and dies silently; the unit sends its own
# signal instead). systemd user env lacks TELEGRAM_*; source the gitignored
# .env in a subshell (CLAUDE.md §8: tokens live in env / untracked .env only).
(
  [ -z "${TELEGRAM_BOT_TOKEN:-}" ] && [ -f .env ] && . ./.env
  if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
    echo "[wrap] PING skipped (env unset) $(date -Iseconds)" >> "$OUT.wrap"
  elif bash tools/notify/telegram.sh \
      "[vero-lite/bench] $(basename "$OUT") done rc=$rc $(date -Iseconds)" \
      >/dev/null 2>&1; then
    echo "[wrap] PING ok $(date -Iseconds)" >> "$OUT.wrap"
  else
    echo "[wrap] PING failed $(date -Iseconds)" >> "$OUT.wrap"
  fi
) || true
exit "$rc"
