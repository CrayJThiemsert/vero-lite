# Lesson #14: argv-vs-stdin contract drift between impl + test stub silently disables Telegram fail-safe

> **Status:** Codified 2026-05-26 (Session 15, PR [#45](https://github.com/CrayJThiemsert/vero-lite/pull/45) — Path C step 3).
> **Source:** Direct observation 2026-05-26 ~23:30 +07 in Session 15b. The L1 loop-detect hook fired live in Session 14 Phase 2 (real triggering of the autonomy fail-safe) but Cray received no Telegram alert. Diagnosis traced through three layers: token rotation (Path E, closed in 15a), Claude Desktop process-env cache (NEW finding — candidate Lesson #13), and finally the hook-level invocation bug + matching test stub (this lesson).
> **Severity:** High (silent disablement of the AFK autonomy fail-safe; ran for ~2 weeks across PLAN-0008 Step 4 → PLAN-0009 Step 5c-1 → PLAN-0010 Phase 4 with green CI throughout).
> **Cross-references:** Lesson #4 (sibling — WSL `bash -c` variable-expansion trap; different mechanism, same class of "shell layer drops your content"). Lesson #11 (sibling — `gh pr` body-file hygiene; same class of "wrong delivery channel for the payload"). [[feedback-coding-careful-pre-ship-checklist]] (auto-memory derived from this lesson).

## 1. The finding

When a Python hook invokes a POSIX shell script via `subprocess.run`, the **invocation contract** (argv vs stdin, platform routing, env forwarding) MUST match the script's actual interface. When the test stub mirrors the **impl** rather than the **real script**, both the impl AND the test pin the same wrong contract — CI is green while production silently drops every payload.

Two independent bugs reached silent swallow in three vero-lite hooks:

| Bug | Hooks (broken) | Hooks (correct, for comparison) |
|---|---|---|
| `["bash", str(script)]` on Windows host → Git-for-Windows bash, not WSL bash. Different CA bundle, no WSL env, can fail to find script paths under `\\wsl.localhost\...` | `pretooluse_loop_detect.py`, `posttooluse_progress_observer.py`, `stop_continuation.py` | `notification_telegram.py`, `subagentstop_notify.py` (detect `sys.platform == "win32"` → `wsl.exe --exec bash <wsl-path>` + `TELEGRAM_*` via `WSLENV`) |
| `subprocess.run(..., input=payload)` sends JSON via stdin. `tools/notify/telegram.sh:74-79` requires the message as `$1` argv and exits 2 with usage error if `$#` < 1; nothing reads stdin | Same three | Same two |

Both bugs were absorbed silently by `capture_output=True` + `check=False` + bare `except (TimeoutExpired, OSError): pass` — the documented "best-effort, never block" discipline. That discipline is correct in principle (an AFK channel outage must not block the deny gate) but it became silent-swallow because there was no log-on-failure backstop.

## 2. The mechanism — why CI stayed green

The fix-eating stub:

```python
# tests/handoffs/test_pretooluse_loop_detect.py — pre-fix
STUB_TELEGRAM = """#!/usr/bin/env bash
# Stub that writes its stdin to $TELEGRAM_STUB_CAPTURE.
cat > "$TELEGRAM_STUB_CAPTURE"
"""
```

The test then asserted:

```python
capture = Path(stub_env["TELEGRAM_STUB_CAPTURE"])
assert capture.exists(), "stub telegram script was not invoked"
payload = json.loads(capture.read_text(encoding="utf-8"))
assert payload["loop_type"] == "L1"
assert payload["target"] == "docs/STATUS.md"
```

The stub read stdin. The impl wrote stdin. The capture file existed. The JSON parsed. The assertions passed. The test verified that **impl and stub agreed with each other** — not that either one matched the real `telegram.sh` contract (which reads `$1` argv and ignores stdin entirely).

Same pattern across all three broken hooks' test files and the cross-hook integration test (`test_phase2_integration.py`). All seven tests across four files were green.

The bug shipped through PLAN-0008 Step 2 (PreToolUse gate), PLAN-0008 Step 3 (PostToolUse observer), PLAN-0008 Step 4 (Stop continuation), and PLAN-0009 Step 1b (SubagentStop wiring touched the same hooks at the boundary). Every review of those plans + every test run after every change reinforced the false signal that the AFK fail-safe was wired.

## 3. Reproduction

Trip the trap in <2 minutes:

```bash
# Setup a stub that mirrors a broken impl
mkdir -p /tmp/repro-lesson14
cat > /tmp/repro-lesson14/fake-notify.sh <<'EOF'
#!/usr/bin/env bash
cat > /tmp/repro-lesson14/capture.txt
EOF
chmod +x /tmp/repro-lesson14/fake-notify.sh

# Invocation that "works" — capture file populated, exit 0
bash /tmp/repro-lesson14/fake-notify.sh <<< '{"loop_type":"L1","target":"x"}'
cat /tmp/repro-lesson14/capture.txt   # {"loop_type":"L1","target":"x"}

# Now replace the stub with the REAL telegram.sh contract
cat > /tmp/repro-lesson14/real-notify.sh <<'EOF'
#!/usr/bin/env bash
set -eu
if [ "$#" -lt 1 ]; then
    echo "usage: $0 <message>" >&2
    exit 2
fi
echo "$1" > /tmp/repro-lesson14/capture.txt
EOF
chmod +x /tmp/repro-lesson14/real-notify.sh
rm /tmp/repro-lesson14/capture.txt

# Same invocation — silently fails
bash /tmp/repro-lesson14/real-notify.sh <<< '{"loop_type":"L1","target":"x"}' 2>&1
# stderr: usage: /tmp/repro-lesson14/real-notify.sh <message>
# exit code: 2
ls /tmp/repro-lesson14/capture.txt 2>&1
# ls: cannot access '/tmp/repro-lesson14/capture.txt': No such file or directory
```

Now wrap that invocation in `subprocess.run(..., capture_output=True, check=False, input=payload)` and a bare `except`, and the calling code sees nothing — exit 2, stderr captured, no exception raised. Same observable behavior as success.

## 4. The fix

Three hooks ported to the working pattern (`notification_telegram._invoke_telegram` style — first established in PLAN-0007 Step 3):

1. **Platform routing.** `sys.platform == "win32"` + `shutil.which("wsl.exe")` → `["wsl.exe", "--exec", "bash", _wsl_path(script), message]`. Linux fallback → `["bash", str(script), message]`. Both branches deliver message as argv.
2. **WSLENV forwarding.** Build `WSLENV` such that `TELEGRAM_BOT_TOKEN/u` and `TELEGRAM_CHAT_ID/u` are appended (the `/u` modifier flags the var as "unix-only", needed so WSL sees the value).
3. **Argv message.** Build a human-readable text body (`_format_message` / `_format_cap_message`) instead of raw JSON. Lock-screen-readable; sent as a single `$1` argv.

Test stubs ported to mirror the **real** `telegram.sh` contract:

```bash
STUB_TELEGRAM = """#!/usr/bin/env bash
# Stub that writes $1 (argv message) to $TELEGRAM_STUB_CAPTURE.
# Matches real telegram.sh contract — message via argv, never stdin.
set -eu
printf '%s' "$1" > "$TELEGRAM_STUB_CAPTURE"
"""
```

Assertions changed from "parse JSON, check keys" to "read text, check fragments" — the test now verifies the body Cray would actually receive.

Verification:

- `uv run --extra dev pytest` → 588 passed, 6 skipped (no regressions)
- `uv run --extra dev ruff check .claude/hooks/ tests/handoffs/` → all checks passed
- `uv run --extra dev mypy .claude/hooks/` → success, no issues
- Direct Telegram bridge: `wsl bash -lc 'bash tools/notify/telegram.sh "session-15b post-restart verify ..."'` → Cray received the message

PR [#45](https://github.com/CrayJThiemsert/vero-lite/pull/45) merged to `main` at `1a5fd68`.

## 5. Prevention checklist (for future hooks)

Before declaring a hook / subprocess-invoking module done, walk this checklist (also codified as [[feedback-coding-careful-pre-ship-checklist]]):

1. **Cross-platform routing.** If invoking `bash` / `sh` / any POSIX-only binary AND the project runs on Windows Claude Code → `sys.platform == "win32"` branch + `wsl.exe --exec bash <wsl-path>` + env via `WSLENV`. Plain `["bash", ...]` is wrong on Windows.
2. **Test the contract, not the impl.** Stubs must reflect the **real** script's argv/stdin/env interface. Ask: "If I delete the impl and re-derive it from the real script's docstring, do my tests still verify the right thing?" If no, the test pins both sides to the same potentially-wrong contract.
3. **Make best-effort visible.** `capture_output=True` + `check=False` + bare `except: pass` is silent-swallow by construction. For best-effort paths (notifiers, telemetry, AFK channels) log at least one line to stderr on non-success — silent failure of a fail-safe is worse than loud failure of the work itself.
4. **Copy the full pattern.** When duplicating a pattern from sibling code, copy the full pattern — platform branch + env forwarding + error logging + argv/stdin contract. Partial copies are the most common source of silent regressions. On the third instance, ask whether to extract a shared helper (rule of three).
5. **End-to-end smoke before merge.** For any change touching a notification / fail-safe path, run the real binary end-to-end (not just the stubbed test). For Telegram: `wsl bash -lc 'bash tools/notify/telegram.sh "smoke <ts>"'` and confirm receipt on the actual destination.

## 6. Why this isn't fixed by "just refactor to a shared helper"

After the fix, five hooks duplicate `_wsl_path`, `_forwarded_env`, and the platform branch. The natural reaction is "extract `.claude/hooks/_telegram_bridge.py`." That was rejected for the bug-fix PR per CLAUDE.md ("a bug fix doesn't need surrounding cleanup") and tracked as a follow-up.

But — a shared helper wouldn't have prevented bug #2 (argv vs stdin contract drift). That bug lives at the **boundary between the helper and the real script**, not inside the helper. Even with `_telegram_bridge.py` extracted, the test stub could still be written to mirror a broken `_invoke_telegram` instead of the real `telegram.sh`.

The durable prevention is the **contract test discipline** in checklist item #2 above — applied at every layer that crosses a boundary between Python and shell, between Windows and WSL, between in-process call and IPC. The shared helper is an optimization; the discipline is the safety property.

## 7. Adjacent observations (deferred)

- **Lesson #12 (deferred — session 14 closeout):** Loop-detect bonus L1 trigger recurrence pattern. Worth promoting if it recurs in closeout work. See `docs/research/private/step6-live-ac/scenarioL1-bonus-loop-detect-live-trigger.md`.
- **Lesson #13 (deferred — session 15a):** Claude Desktop process-env-cache + secret rotation. After rotating any Windows User-scope env var (e.g., `TELEGRAM_BOT_TOKEN`), Claude Desktop must be restarted; WSLENV forwards the stale process-env value otherwise. See session-15a → 15b post-restart handoff §3.

Both are real durable findings; both are flagged for opportunistic promotion in a future session. Numbering gap (no 0012 / 0013 yet) is intentional and tolerated.
