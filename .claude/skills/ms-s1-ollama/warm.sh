#!/usr/bin/env bash
# Warm an Ollama model on the MS-S1 MAX server (reachability + verify + warm).
#
# Usage:  bash warm.sh [model] [keep_alive]
#   model       default gpt-oss:20b  (ADR-0001 pin; the structured/`format` path)
#   keep_alive  default 15m
#   env OLLAMA_HOST overrides the default IP endpoint
#
# Fails closed: aborts if MS-S1 is unreachable OR the requested model is not in
# the tag list (session-37: never warm/smoke the WRONG model). Reaches MS-S1 by
# IP — `ms-s1-max` has no WSL DNS entry. Run with `bash warm.sh`, not `./warm.sh`
# (the WSL UNC mount strips exec bits). Requires `jq`.
set -euo pipefail

HOST="${OLLAMA_HOST:-http://192.168.1.133:11434}"
MODEL="${1:-gpt-oss:20b}"
KEEP="${2:-15m}"

echo "MS-S1: $HOST | model: $MODEL | keep_alive: $KEEP"

# 1. reachability + full tag list
if ! TAGS="$(curl -s --max-time 10 "$HOST/api/tags")" || [ -z "$TAGS" ]; then
  echo "ABORT: MS-S1 unreachable at $HOST (check the box is up / on the LAN / IP)."
  exit 1
fi
echo "Models present:"
echo "$TAGS" | jq -r '.models[].name' | sed 's/^/  - /'

# 2. verify the requested model is present BEFORE warming (fail closed)
if ! echo "$TAGS" | jq -e --arg m "$MODEL" '[.models[].name] | any(. == $m)' >/dev/null; then
  echo "ABORT: '$MODEL' is not in the tag list above — refusing to warm a model"
  echo "       that isn't loaded (a green smoke vs the wrong model is false confidence)."
  echo "       Pass an exact name from the list, or 'ollama pull' it on MS-S1 first."
  exit 2
fi

# 3. warm via /api/generate (loads into VRAM; keep_alive holds it)
echo "Warming '$MODEL' (cold load: gpt-oss:20b ~20-25s; qwen3.x can exceed 150s)..."
REQ="$(jq -n --arg m "$MODEL" --arg k "$KEEP" \
  '{model:$m, prompt:"reply with ok", stream:false, keep_alive:$k}')"
if ! RESP="$(curl -s --max-time 240 "$HOST/api/generate" -d "$REQ")" || [ -z "$RESP" ]; then
  echo "ABORT: warm request failed (timeout? cold load > 240s? model crashed?)."
  exit 3
fi
echo "$RESP" | jq -r '"load_s=\(.load_duration/1e9 | floor)  total_s=\(.total_duration/1e9 | floor)  done=\(.done)  response=\(.response[0:40])"'

echo "WARM OK — '$MODEL' resident for $KEEP."
