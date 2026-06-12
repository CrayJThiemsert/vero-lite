#!/usr/bin/env bash
# Carrier-proof launcher for long MS-S1 benchmark runs (probe-verified 2026-06-12).
#
# Runs the procedure-baseline benchmark under `systemd-run --user` so the job
# survives the death of the launching wsl.exe — the "carrier death" gotcha:
# a one-off reap of the held wsl.exe used to kill the run (or silently eat its
# completion signal) ~30-60 min in. A systemd user unit is parented to the
# user manager, not the carrier, and was probe-verified to keep running and
# complete after its launcher's wsl.exe exited.
#
# Artifacts (all under .claude/benchmark-results/):
#   <run-name>.log    full runner stdout/stderr (content-based truth source)
#   <run-name>.jsonl  --dump-json per-item records
#   <run-name>.wrap   [wrap] START / EXIT=<rc> / PING markers
#   <run-name>.done   SENTINEL: "<rc> <ISO-timestamp>" — written as the job's
#                     LAST act. Its existence is the ONLY authoritative
#                     completion signal; never trust harness task status.
#
# Usage (after Cray's host-state go + warm.sh):
#   bash .claude/skills/ms-s1-ollama/run_detached.sh <run-name> [extra run_benchmark args...]
#   e.g. bash .claude/skills/ms-s1-ollama/run_detached.sh 2026-06-15-scored-run --reasoning-mode full
# Watch / verify:
#   systemctl --user status bench-<run-name>
#   test -f .claude/benchmark-results/<run-name>.done && cat it -> "rc timestamp"
# Caveat: user lingering is OFF (loginctl Linger=no) — the user manager (and
# the job) survives only while ANY crayj WSL session exists. In practice the
# harness's constant wsl usage holds this; enabling linger is a host-state
# change that needs Cray approval.
set -eu
REPO="$HOME/work/vero-lite"
RUN_NAME=${1:?usage: run_detached.sh <run-name> [extra run_benchmark args...]}
shift || true
OUT_REL=".claude/benchmark-results/$RUN_NAME"
UNIT="bench-$RUN_NAME"

cd "$REPO"
if systemctl --user is-active --quiet "$UNIT"; then
  echo "ERROR: unit $UNIT is already active — serialize MS-S1 runs (skill rule)" >&2
  exit 1
fi
rm -f "$OUT_REL.done"

systemd-run --user --collect --unit="$UNIT" \
  bash "$REPO/.claude/skills/ms-s1-ollama/_run_detached_body.sh" "$OUT_REL" "$@"

echo "launched unit: $UNIT (carrier-proof; probe-verified 2026-06-12)"
echo "watch:   systemctl --user status $UNIT   |   tail .claude/benchmark-results/$RUN_NAME.log"
echo "done iff: $OUT_REL.done exists (contains: rc + ISO timestamp)"
