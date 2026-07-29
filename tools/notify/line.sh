#!/usr/bin/env bash
# tools/notify/line.sh — env-var-driven LINE Official Account push (PLAN-0096 Step 7 / AC-8).
#
# The CLI analog of tools/notify/telegram.sh, for the ONE outbound channel of the
# fleet pilot. Useful for a delivery smoke test before wiring the API, and for an
# operator-side "did the OA reach this group?" check that does not need the app.
#
# Usage:
#   tools/notify/line.sh <recipient-id> "<message>"
#   tools/notify/line.sh --self-test <recipient-id>
#
# Env vars (REQUIRED for any send; graceful no-op if unset):
#   LINE_CHANNEL_ACCESS_TOKEN   Messaging API channel access token for the OA
#
# NOTE — LINE Notify was discontinued 2025-03-31. This is the Messaging API push
# endpoint on an Official Account; <recipient-id> is a user id (U…) or a group id
# (C…), and the API accepts either in the same `to` field.
#
# Per CLAUDE.md §8: the token MUST come from the environment, never a tracked file.
# A dev session without it is supported (exit 0 + one-line stderr note).
#
# Outbound only. There is no inbound/webhook counterpart anywhere in this repo, and
# PLAN-0096's Out of Scope keeps it that way.

set -eu

readonly _PROG="tools/notify/line.sh"
readonly _PUSH_URL="https://api.line.me/v2/bot/message/push"

_log() {
    # one-line stderr log; never to stdout (hook stdout is parsed by Claude Code).
    printf '%s: %s\n' "$_PROG" "$*" >&2
}

_send() {
    # $1 = recipient id, $2 = message text
    local to="$1" message="$2"
    local response http_status body_file
    body_file="/tmp/line_payload.$$"
    # Build the JSON with a here-doc through python so a message containing quotes,
    # newlines or Thai text cannot break the payload — the shell-quoting bug class
    # this repo has been bitten by before.
    python3 - "$to" "$message" >"$body_file" <<'PY'
import json, sys
print(json.dumps({"to": sys.argv[1], "messages": [{"type": "text", "text": sys.argv[2][:5000]}]}))
PY
    response=$(
        curl -sS \
            --max-time 10 \
            -o "/tmp/line_response.$$" \
            -w '%{http_code}' \
            -X POST "$_PUSH_URL" \
            -H "Authorization: Bearer ${LINE_CHANNEL_ACCESS_TOKEN}" \
            -H "Content-Type: application/json" \
            --data-binary "@${body_file}" \
            2>&1
    ) || {
        _log "curl failed: $response"
        rm -f "$body_file" "/tmp/line_response.$$"
        return 1
    }
    http_status="$response"
    rm -f "$body_file"
    if [ "$http_status" != "200" ]; then
        _log "non-200 from LINE API: HTTP $http_status — $(cat "/tmp/line_response.$$" 2>/dev/null || true)"
        rm -f "/tmp/line_response.$$"
        return 1
    fi
    rm -f "/tmp/line_response.$$"
    return 0
}

main() {
    if [ -z "${LINE_CHANNEL_ACCESS_TOKEN:-}" ]; then
        _log "env unset (LINE_CHANNEL_ACCESS_TOKEN); skipping"
        return 0
    fi

    if [ "${1:-}" = "--self-test" ]; then
        if [ -z "${2:-}" ]; then
            _log "usage: $_PROG --self-test <recipient-id>"
            return 2
        fi
        _send "$2" "vero-lite line.sh self-test — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        return $?
    fi

    if [ "$#" -lt 2 ]; then
        _log "usage: $_PROG <recipient-id> \"<message>\"  (or --self-test <recipient-id>)"
        return 2
    fi

    _send "$1" "$2"
}

main "$@"
