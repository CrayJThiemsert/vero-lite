#!/usr/bin/env bash
# tools/notify/telegram.sh — env-var-driven Telegram notifier (PLAN-0007 Step 2 / ADR-013 D5).
#
# Usage:
#   tools/notify/telegram.sh "<message>"
#   tools/notify/telegram.sh --self-test
#
# Env vars (REQUIRED for any send; graceful no-op if either is unset):
#   TELEGRAM_BOT_TOKEN   bot API token (see https://core.telegram.org/bots#botfather)
#   TELEGRAM_CHAT_ID     destination chat id
#
# Per CLAUDE.md §8 + ADR-013 D5: tokens MUST come from the environment, never
# from a tracked file. .env is gitignored. A dev session without the vars set
# is supported (exit 0 + one-line stderr note) so the hook does not break
# local workflows that do not need notifications.
#
# Smoke test parity (Cray E.2, 2026-05-23):
#   curl -sS "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
#        -d chat_id="${TELEGRAM_CHAT_ID}" -d text="vero-lite smoke"
#   => {"ok":true,...}

set -eu

readonly _PROG="tools/notify/telegram.sh"

_log() {
    # one-line stderr log; never to stdout (hook stdout is parsed by Claude Code).
    printf '%s: %s\n' "$_PROG" "$*" >&2
}

_send() {
    # $1 = message text
    local message="$1"
    local response http_status
    response=$(
        curl -sS \
            --max-time 10 \
            -o /tmp/telegram_response.$$ \
            -w '%{http_code}' \
            "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
            --data-urlencode "text=${message}" \
            2>&1
    ) || {
        _log "curl failed: $response"
        rm -f /tmp/telegram_response.$$
        return 1
    }
    http_status="$response"
    if [ "$http_status" != "200" ]; then
        _log "non-200 from Telegram API: HTTP $http_status — $(cat /tmp/telegram_response.$$ 2>/dev/null || true)"
        rm -f /tmp/telegram_response.$$
        return 1
    fi
    rm -f /tmp/telegram_response.$$
    return 0
}

main() {
    if [ "${1:-}" = "--self-test" ]; then
        if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
            _log "self-test: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID unset; skipping"
            return 0
        fi
        _send "vero-lite telegram.sh self-test — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        return $?
    fi

    if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
        _log "env unset (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID); skipping"
        return 0
    fi

    if [ "$#" -lt 1 ]; then
        _log "usage: $_PROG \"<message>\"  (or --self-test)"
        return 2
    fi

    _send "$1"
}

main "$@"
