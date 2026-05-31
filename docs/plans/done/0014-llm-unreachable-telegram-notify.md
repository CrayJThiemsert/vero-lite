# PLAN-0014: LLM-unreachable Telegram notification

**Status:** Complete (2026-05-31) — all ACs met; executed + archived under `docs/plans/done/`.
**Owner:** Claude Code
**Created:** 2026-05-31
**Completed:** 2026-05-31 (session 28). Executed: config fields +
`OllamaUnreachableError` + `services/notify/telegram.py` +
`OllamaClient.warm()/unload()/ps()` + `GET /warm` + `GET /sleep` +
recommender/nl_query notify wiring + tests (offline suite 1003 passed / 2
skipped, ruff + mypy clean) + a live smoke against MS-S1. Cray-directed;
plan-drafter-authored, Code-reviewed, Cray-ratified at PR #100 merge; `/sleep`
added per Cray (session 28).
**Related ADRs:** ADR-010 (LLM reasoning hook + rule fail-safe — IN-4), ADR-013 D5 (harness Telegram notifier — prior art)

> **Author≠reviewer disclosure (ADR-012 D4.3 / ADR-013 OQ-1).** This PLAN is
> **Code-directed**: the outline originated with the main Code agent (Tier 2)
> under ADR-013 D1 phased authority and was **drafted by the in-harness
> `plan-drafter` subagent**. The independent check is the **main Code agent's
> review + Cray's ratification** at PR merge. Separation: **INTACT** — drafter
> (`plan-drafter`) ≠ reviewer (Code agent + Cray).

## Goal

When an OCT page triggers a local-LLM call — the recommender behind View B
(`recommend()` in `services/engine/recommender.py`) or the natural-language
query behind View C (`answer_question()` in `services/engine/nl_query.py`) —
while the MS-S1 MAX box (ADR-002) is **powered off / unreachable**, the engine
today degrades **silently**: the recommender falls back to the deterministic
rule path (`_rule_recommend`, ADR-010 IN-4) and `answer_question()` returns an
ungrounded "assistant unavailable" answer. During the development phase MS-S1
is **not on 24/7** — it is powered on/off on a schedule. This PLAN adds a
**best-effort, non-blocking Telegram notification** that fires (with a cooldown)
when a local-LLM call fails specifically because the box is unreachable, so the
founder (Cray) gets a ping to power MS-S1 on and warm the model. The message
carries a copy-pasteable warm one-liner. This is a **demo-supporting
reliability/notification feature** for the PLAN-0013 OCT demo (energy +
supply_chain verticals, just shipped) — **not** a new product surface.

## Context & strategic frame

**Why now.** PLAN-0013 closed (PR #99) shipping the demo-ready OCT on two
verticals. The demo depends on MS-S1 being up + warm when a stakeholder clicks
View B / View C. Because the box is on a power schedule during development, a
silent degrade looks like a broken demo. A targeted ping lets Cray recover in
seconds without polling the box manually.

**What already exists (verified prior art — reuse the contract, do NOT call it).**
- `tools/notify/telegram.sh` (PLAN-0007 Step 2 / ADR-013 D5) — an env-driven
  `curl` to `https://api.telegram.org/bot<token>/sendMessage`, reading
  `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`, graceful no-op when either is
  unset. This proves the bot + chat_id **already exist and work**.
- `.claude/hooks/notification_telegram.py` (PLAN-0007 Step 3 / ADR-013 D5) —
  the harness hook that forwards `permission_prompt|idle_prompt` events into
  `telegram.sh`. Best-effort, never raises into the event loop.

**Decision (ratified by Cray, session 28 — baked in, NOT re-opened as OQs):**
1. **Mechanism = a native async notifier inside the FastAPI app.** A small
   module under `services/` does an `httpx` async POST to `sendMessage`,
   reading the **same** `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` the harness
   notifier uses. **Reuse the existing bot + chat_id — no new BotFather bot.**
   We do **not** shell out to `tools/notify/telegram.sh` (that sync shell
   script is for harness hooks). A native async notifier is cleaner for async
   request handlers and is unit-testable via `httpx.MockTransport`, mirroring
   `OllamaClient`'s transport-injection seam
   (`services/engine/llm/client.py` line 66, `transport: httpx.AsyncBaseTransport | None`).
2. **Enablement = an explicit flag `TELEGRAM_NOTIFY_ENABLED` (default `False`).**
   The notifier fires **only** when the flag is `True` **and**
   `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` are set **and** the backend is
   local (`settings.llm_backend == "local"`). Default-off so dev sessions get
   no surprise pings; turned on for the stakeholder demo box.

**Verified engine facts the design hangs on.**
- `OllamaClient.chat()` wraps **all** transport failures in one handler
  (`services/engine/llm/client.py` lines 123–124):
  `except httpx.HTTPError as exc: raise OllamaError(f"Ollama chat call failed: {exc}") from exc`.
  When MS-S1 is off, `httpx` raises `ConnectError` / `ConnectTimeout`
  (subclasses of `httpx.HTTPError`) → currently surfaces as a generic
  `OllamaError` with `__cause__` set. Today nothing distinguishes "box is
  down/unreachable" from "box is up but returned bad JSON / timed out
  mid-generation". The existing test
  `test_chat_raises_ollama_error_on_transport_error`
  (`tests/services/engine/llm/test_client.py` lines 113–120) raises
  `httpx.ConnectError` through a `MockTransport` and asserts `OllamaError` —
  the seam this PLAN narrows.
- `recommend()` (`services/engine/recommender.py` lines 150–177) has a broad
  `except Exception` (line 170) that logs + falls back to `_rule_recommend`
  (ADR-010 IN-4 fail-safe — "**never raises into the runtime loop**"). This is
  the **View-B notify hook point**. Notify must be **additive** and **preserve**
  the fail-safe (still fall back; never raise).
- `answer_question()` (`services/engine/nl_query.py` lines 434–502) catches
  `(QueryTranslationError, OllamaError, NotImplementedError)` on translate
  (line 460) and `_phrase` catches `Exception` (line 410) — both degrade
  gracefully. The translate-catch is the **View-C notify hook point**.
- `Settings` (`services/api/config.py` lines 27–157) is pydantic-settings,
  env/`.env`-driven, with `llm_backend` (default `"local"`) already present
  (lines 69–76).

**Why Cray's adjudication matters now.** The ratified decisions remove the big
design forks, but a handful of mechanical choices (where the notifier module
lives, exactly which error class triggers it, cooldown default, message
wording) have multiple defensible answers and are surfaced as SD-1..SD-4 below.
There is also a **citation correction** the dispatch payload should be aware of
(see Open Questions OQ-1) before this PLAN is treated as ground truth.

## Acceptance Criteria

Each AC is verifiable by **named, offline (mocked) evidence**, plus one
**gated live smoke** (AC-live). All offline ACs run in the default `pytest`
suite with **no network** (Lesson #7 §3 in-process-assertion discipline:
inject a fake LLM client + an `httpx.MockTransport` that captures the
`sendMessage` request).

- [x] **AC-trigger** — local LLM unreachable + flag on → **exactly one**
  Telegram POST is issued. Verify with an injected fake chat client that
  raises `OllamaUnreachableError`, plus an `httpx.MockTransport` on the
  notifier that captures one `POST` to `…/sendMessage` carrying the configured
  `chat_id`.
- [x] **AC-no-false-positive** — bad-JSON / mid-generation timeout / hosted
  seam-only stub (`NotImplementedError`) / normal sub-threshold no-action →
  **no** notify. (These raise a non-`Unreachable` `OllamaError`,
  `NotImplementedError`, or return `None` without ever reaching the notify
  hook.)
- [x] **AC-debounce** — N unreachable calls within the cooldown window → **at
  most one** message. Drive N calls through the hook with a stubbed/controlled
  clock; assert exactly one captured POST.
- [x] **AC-nonblocking-failsafe** — notifier error **or** env-unset **or**
  flag-off **or** non-local backend → the notify is a silent no-op and
  **never raises**; `recommend()` still returns the **rule-path** record and
  `answer_question()` still degrades exactly as before. This is a
  **regression-guard**: the existing recommender fail-safe tests and nl_query
  degrade tests must still pass unchanged with the notify wired in.
- [x] **AC-no-pii** — the formatted message body contains **no** operator
  question text, **no** object/record data, and **no** partner identifiers —
  only a fixed advisory line + the warm one-liner. Assert on the exact
  formatted string (PDPA / CLAUDE.md §8 forward-looking).
- [x] **AC-secret-hygiene** — no token appears in the diff; `.env.example`
  carries placeholders only (`TELEGRAM_BOT_TOKEN=`, `TELEGRAM_CHAT_ID=`,
  `TELEGRAM_NOTIFY_ENABLED=false`, `TELEGRAM_NOTIFY_COOLDOWN_S=600`);
  `detect-secrets` against `.secrets.baseline` still passes (pre-commit clean).
- [x] **AC-live** *(gated — env/marker-skipped, NOT in the default suite)* —
  with MS-S1 **actually off**, the flag on, and Cray's **real** bot/chat_id in
  env, a real Telegram message arrives. Gated behind an env flag +
  `pytest.mark.skipif` (mirrors the `telegram.sh --self-test` env-gated
  precedent); the default offline suite never sends a real message.
- [x] **AC-warm** — `GET /warm` (browser/phone-hittable) triggers a load of the
  configured model on MS-S1 and reports its status. Verify offline with an
  `httpx.MockTransport` capturing one `POST /api/generate` to
  `settings.ollama_host` carrying `model = settings.recommender_model` + a
  `keep_alive`, returning JSON `{model, reachable, loaded, load_seconds, ps}`.
  When the box is unreachable, `/warm` returns `reachable: false` (HTTP 503) and
  **never raises**, and it does **not** itself fire the Telegram notify (the
  operator is already hands-on). When `OCT_PUBLIC_BASE_URL` is set, the Telegram
  body (Step 3) links to this endpoint, closing the recovery loop **notify →
  tap link → warmed**. *(Empirically grounded, session 28: a no-prompt
  `POST /api/generate {model, keep_alive:"30m"}` against MS-S1 returned
  `done_reason:"load"` in ~11 s cold and `/api/ps` then showed the model
  resident; the GET `/api/tags` + `/api/ps` only list, they do not load.)*
- [x] **AC-sleep** — `GET /sleep` (browser/phone-hittable) unloads the
  configured model from MS-S1 VRAM (the symmetric companion to `/warm`,
  Cray-approved session 28). Verify offline with an `httpx.MockTransport`
  capturing one `POST /api/generate` with `keep_alive: 0` → JSON
  `{model, reachable, unloaded, ps}`; unreachable → HTTP 503 `reachable: false`,
  never raises. *(Empirically grounded, session 28: a `keep_alive:0` generate
  returned `done_reason:"unload"` and `/api/ps` then reported the model evicted.)*

## Out of Scope

- ❌ Auto-powering-on MS-S1 (Cray powers it manually).
- ❌ A background poller that auto-warms the model (the message carries the
  warm one-liner instead).
- ❌ Notifications for non-LLM failures, or for the energy/supply_chain rule
  path itself (the rule fail-safe is healthy behaviour, not an outage).
- ❌ Rich Telegram formatting / inline buttons / bot command handling.
- ❌ Any rate-limiting beyond the simple process-local cooldown.
- ❌ Replacing or refactoring the existing harness `tools/notify/telegram.sh`
  hook (PLAN-0007 / ADR-013 D5) — it stays as-is.
- ❌ Persisting notify state across process restarts (cooldown is process-local
  in-memory only).

## Steps

### Step 1: Config additions (`services/api/config.py`)

Add four env-driven fields to `Settings` (mirroring the existing field style,
each with a `Field(description=...)`):

- `telegram_bot_token: str = ""` → env `TELEGRAM_BOT_TOKEN`
- `telegram_chat_id: str = ""` → env `TELEGRAM_CHAT_ID`
- `telegram_notify_enabled: bool = False` → env `TELEGRAM_NOTIFY_ENABLED`
- `telegram_notify_cooldown_s: float = 600.0` → env `TELEGRAM_NOTIFY_COOLDOWN_S`
  (`gt=0.0`)

These are read-only consumers of env; no `.env` is committed (CLAUDE.md §8).

### Step 2: `OllamaUnreachableError` subclass + raise it in the client

In `services/engine/llm/client.py`, add a dedicated subclass:

```python
class OllamaUnreachableError(OllamaError):
    """The Ollama host could not be reached (connection refused / connect
    timeout) — distinct from a reachable host returning bad JSON / a
    mid-generation timeout. Used to drive the MS-S1-down notification
    (PLAN-0014) while preserving the recommender fail-safe (ADR-010 IN-4)."""
```

Narrow the existing transport handler (currently lines 123–124) so that
`httpx.ConnectError` / `httpx.ConnectTimeout` raise `OllamaUnreachableError`,
while every **other** `httpx.HTTPError` (HTTP status errors, read timeouts mid
generation, etc.) continues to raise the base `OllamaError`. Because
`OllamaUnreachableError` **is an** `OllamaError`, every existing
`except OllamaError` site (the nl_query translate-catch line 460, the broad
recommender catch) keeps working unchanged — this change is **purely additive
to the type hierarchy**. The existing test
`test_chat_raises_ollama_error_on_transport_error` still passes
(`OllamaUnreachableError` is an `OllamaError`); add a sibling test asserting
the **narrower** type for `ConnectError`/`ConnectTimeout`.

### Step 3: Native async notifier module (`services/notify/` — see SD-1)

A small module exposing one fire-and-forget async function, e.g.
`notify_llm_unreachable() -> None`. Design invariants (binding):

- **No-op gates (checked first, in order):** return immediately and silently if
  `not settings.telegram_notify_enabled`, or `settings.llm_backend != "local"`,
  or `not (settings.telegram_bot_token and settings.telegram_chat_id)`.
- **Cooldown guard:** a **process-local** module-level timestamp of the last
  send. If `now - last_send < settings.telegram_notify_cooldown_s`, no-op. App
  code may read **real wall-clock time**; tests inject/monkeypatch the clock.
- **Best-effort POST:** `httpx` async `POST` to
  `https://api.telegram.org/bot{token}/sendMessage` with
  `{"chat_id": ..., "text": ...}`, a **short timeout (~5s)**, and an injected
  `transport` seam (default `None`, `httpx.MockTransport` in tests) mirroring
  `OllamaClient.__init__`.
- **Never raises:** wrap the POST in `try/except Exception` → log a `warning`
  and return (mirrors `telegram.sh`'s graceful-no-op posture and ADR-010 IN-4).
  Only mark the cooldown timestamp on a **successful** send (so a transient
  failure does not suppress the next attempt — see SD-4).
- **Message body (no PII — AC-no-pii):** a fixed advisory line with a UTC
  timestamp plus a copy-pasteable warm one-liner. Example shape (final wording
  is SD-3):

  ```
  ⚠️ vero-lite OCT: an LLM request reached MS-S1 at <UTC ISO8601> but it is
  unreachable. Power it on + warm the model:
  curl http://192.168.1.133:11434/api/chat -d '{"model":"gpt-oss:20b","messages":[{"role":"user","content":"warm"}],"keep_alive":"30m"}'
  ```

  The body must **never** include the operator question, object/record data,
  or partner identifiers (PDPA / CLAUDE.md §8). Note the warm one-liner uses
  the MS-S1 **IP** `192.168.1.133:11434`, not the `ms-s1-max` hostname, because
  the hostname has no WSL/Telegram-side DNS entry (project memory
  `project_ms_s1_ollama_reachability`).

### Step 4: Wire the notify into the recommender + nl_query unreachable paths

Both wirings are **additive** and must preserve the existing fail-safe.

- **Recommender (View B):** in `recommend()`'s broad `except Exception` block
  (`services/engine/recommender.py` line 170), **before** returning
  `_rule_recommend(...)`, check `if isinstance(exc, OllamaUnreachableError):`
  and `await notify_llm_unreachable()` (best-effort; its own try/except means
  it can never break the fail-safe). The fall-back-to-rule-path return is
  unchanged. Notify fires **only** for `OllamaUnreachableError`, not other
  exceptions caught by the broad guard.
- **NL query (View C):** in the translate-catch
  (`services/engine/nl_query.py` line 460,
  `except (QueryTranslationError, OllamaError, NotImplementedError) as exc`),
  add the same `isinstance(exc, OllamaUnreachableError)` guarded
  `await notify_llm_unreachable()` before returning the ungrounded answer. Do
  **not** add notify to the `_phrase` `except Exception` (line 410): a phrasing
  failure on a reachable box is not an MS-S1-down signal, and a phrase failure
  has already produced a usable grounded answer.

Import the notifier lazily/at module top per house style; keep the engine's
dependency on `services/notify/` one-directional.

### Step 5: Tests (contract + offline via MockTransport + fail-safe regression)

Under `tests/` mirroring the existing layout
(`tests/services/engine/llm/`, `tests/services/notify/` new):

- **Client (Step 2):** `ConnectError`/`ConnectTimeout` → `OllamaUnreachableError`;
  HTTP 500 + bad-JSON + missing-message → base `OllamaError` (narrower type
  **not** raised). Existing `test_chat_*` tests stay green.
- **Notifier (Step 3):** flag-on + env-set + local backend → one captured
  `sendMessage` POST (MockTransport); flag-off / env-unset / non-local backend
  → zero POSTs; cooldown → at most one POST across N calls with a controlled
  clock; POST raising → swallowed, no exception escapes; message body asserts
  the fixed advisory + warm one-liner and asserts **absence** of any
  question/record/partner string (AC-no-pii).
- **Recommender wiring (Step 4):** injected fake client raising
  `OllamaUnreachableError` → `recommend()` returns the **rule-path** record
  **and** the notifier is invoked once (assert via a spy/MockTransport);
  fake client raising a non-`Unreachable` `OllamaError` → rule-path record,
  notifier **not** invoked (AC-no-false-positive); regression: existing
  recommender fail-safe tests pass unchanged.
- **NL-query wiring (Step 4):** unreachable on translate → ungrounded answer +
  notifier invoked once; `NotImplementedError` (hosted stub) / non-unreachable
  `OllamaError` → ungrounded answer, notifier **not** invoked; regression:
  existing nl_query degrade tests pass unchanged.

### Step 6: `.env.example` + runbook/STATUS note

- Append a `# Telegram notify (PLAN-0014)` block to `.env.example` with
  **placeholders only**: `TELEGRAM_BOT_TOKEN=`, `TELEGRAM_CHAT_ID=`,
  `TELEGRAM_NOTIFY_ENABLED=false`, `TELEGRAM_NOTIFY_COOLDOWN_S=600`, with a
  one-line comment that the values reuse the existing harness bot (ADR-013 D5)
  and default-off so dev sessions get no pings.
- Add a short note (runbook stub or `docs/STATUS.md` line) describing how to
  arm the notify for the demo box and how to run the gated live smoke.

### Step 7: Gated live smoke (AC-live)

A skipped-by-default test (env flag + `pytest.mark.skipif`) and/or a one-line
manual procedure: with MS-S1 **off**, the flag on, and real bot/chat_id in env,
trigger a View-B/View-C call and confirm one real Telegram message arrives.
Mirrors the `telegram.sh --self-test` env-gated precedent; never part of the
default suite (it sends a real message + depends on MS-S1 being off).

### Step 8: Companion — browser/phone-tappable `GET /warm` (Cray-approved, session 28)

A small endpoint so that, **after** a ping, Cray can warm the model from a
browser or phone with one tap — closing the recovery loop **notify → tap →
warmed**. Empirically verified (session 28, against MS-S1): a no-prompt
`POST /api/generate {"model": <model>, "keep_alive": "30m"}` loads the model
(`done_reason: "load"`, ~11 s cold) and `/api/ps` then shows it resident.
Ollama's GET endpoints (`/api/tags`, `/api/ps`) only *list* — they never load —
so a browser address bar cannot warm directly; `/warm` is the GET→POST bridge.

**Augments Step 1 config** — add two fields to `Settings`:
- `ollama_keep_alive: str = "30m"` → env `OLLAMA_KEEP_ALIVE` (how long a warmed
  model stays resident; also used by the warm one-liner in the message).
- `oct_public_base_url: str = ""` → env `OCT_PUBLIC_BASE_URL` (the externally
  reachable base URL of the demo box, e.g. `http://192.168.1.x:8096`). When set,
  the Telegram body (Step 3) appends a tap-link `"{base}/warm"`; when blank, the
  message keeps only the curl one-liner.

**Client (`services/engine/llm/client.py`)** — add `OllamaClient.warm()`: a
`POST /api/generate` with `{"model": self._model, "keep_alive": <keep_alive>}`
and **no prompt**, parsing `{done_reason, total_duration}`. Reuses the same
transport-injection seam (`MockTransport` in tests). A transport failure raises
`OllamaUnreachableError` (Step 2), so `/warm` can report `reachable: false`.

**Route (`GET /warm`)** — a new route on the FastAPI app returning JSON
`{model, ollama_host, reachable, loaded, load_seconds, ps}`:
- Default **blocking**: awaits `OllamaClient(model=settings.recommender_model,
  base_url=settings.ollama_host, ...).warm()` (instant if already resident,
  ~11 s cold) and reports `load_seconds`.
- Optional `?wait=false`: fire-and-forget (schedule the warm, return
  `{"warming": true}` immediately) for a snappy tap when Cray needn't watch the
  load finish.
- On `OllamaUnreachableError`: return HTTP 503 + `{reachable: false}`; **never
  raise**. Does **not** fire the notify (operator is hands-on).
- Phase-2 demo endpoint: **no auth** (LAN/localhost demo box), consistent with
  the other unauthenticated demo routes; flagged here for transparency.

**Message integration (augments Step 3)** — when `oct_public_base_url` is set,
the Telegram body appends `"Or tap to warm: {base}/warm"`; the curl one-liner
stays as the always-present fallback. No PII added (only the host URL).

**Tests** — `OllamaClient.warm()` (MockTransport: one `POST /api/generate` with
the model + keep_alive, parses the load result; `ConnectError` →
`OllamaUnreachableError`); `GET /warm` (MockTransport): reachable → JSON with
`load_seconds`; `?wait=false` → immediate `{"warming": true}`; unreachable → 503
`{reachable: false}` with no exception escaping.

**SD-5 — `/warm` shape (resolved at Code review, session 28).** Blocking `GET`
(default) + `?wait=false`; warming via a new `OllamaClient.warm()`; no auth
(Phase-2 demo). Accepted: `GET` is intentional (browser/phone address-bar use is
the whole point) despite the mild GET-side-effect REST smell — warming is
effectively idempotent (a re-load just resets `keep_alive`). Cray may override
the route name / auth posture / blocking default at ratification.

## Verification

- `pytest` (full offline suite, no network) green, including the new client,
  notifier, recommender-wiring, and nl_query-wiring tests **and** the unchanged
  pre-existing fail-safe/degrade regression tests (AC-trigger,
  AC-no-false-positive, AC-debounce, AC-nonblocking-failsafe, AC-no-pii).
- `pre-commit` clean: `ruff` + `mypy` + `detect-secrets` against
  `.secrets.baseline` all pass; `git diff` shows no token literal and only
  placeholder keys in `.env.example` (AC-secret-hygiene).
- Manual / gated: arm the flag with real env on the demo box, power MS-S1 off,
  click View B (or View C), confirm exactly one Telegram message with the warm
  one-liner arrives and that a second click within the cooldown sends nothing
  (AC-live + AC-debounce live confirmation).
- **Executed + live-verified (session 28).** Offline suite: **1003 passed, 2
  skipped** (ruff + mypy clean). Live smoke against MS-S1 (model cold):
  `GET /warm` → `loaded:true, done_reason:"load", load_seconds≈7` with `/api/ps`
  confirming the model resident; `GET /sleep` → `unloaded:true,
  done_reason:"unload"`; `GET /warm?wait=false` → `{warming:true}` immediately.
  The notify path is exercised by the offline `MockTransport` tests; the gated
  real-send smoke (AC-live) remains opt-in.

## Open Questions

- **OQ-1 (citation correction — flagged to Code/Cray).** The dispatch payload
  cites **"Lesson #15"** as the gated-live-smoke precedent. **Verified
  against the repo, this is wrong:** `docs/lessons/0015-*.md` is
  *classifier-payload-starvation-stop-events*, unrelated to live smokes. There
  is **no** lesson dedicated to gated live smokes. This PLAN therefore grounds
  AC-live in the **verifiable** precedent instead: the env-gated
  `telegram.sh --self-test` path (PLAN-0007) + `pytest.mark.skipif`, and
  Lesson #7's in-process-assertion discipline cited in
  `tests/services/engine/llm/test_client.py`. Code/Cray to confirm the
  substitution (or supply the intended lesson number if one exists).
- **OQ-1 substitution — ACCEPTED (Code review, session 28).** The "Lesson #15"
  miscitation is confirmed; AC-live is grounded in the verifiable
  `telegram.sh --self-test` env-gated precedent (PLAN-0007) + `pytest.mark.skipif`
  + Lesson #7's in-process discipline, as drafted. (Side note for Code/Cray: the
  now-merged PLAN-0013 carries the same stale "Lesson #15 = live-vs-mock"
  citation — a pre-existing doc-lag, not fixed here.)
- **OQ-2 — RESOLVED (Code review, session 28).** The four mechanical choices
  (SD-1..SD-4) were adjudicated by the main Code agent during review; the
  resolutions are recorded below and baked into Steps 2–4. **Cray may override
  any at ratification** — they are documented, not silently chosen.

### Decisions resolved at Code review (session 28)

- **SD-1 — notifier module location → `services/notify/telegram.py`.** Accepted
  the recommendation: a new `services/notify/` package, engine → notify
  dependency one-directional, parallel to the harness `tools/notify/`.
- **SD-2 — trigger boundary → both `ConnectError` AND `ConnectTimeout`.**
  Accepted. *Code-review note:* a **warming** box (powered on, model cold)
  accepts the TCP connection and is slow on the **read**, surfacing as a
  read/per-request timeout — **not** a connect error/timeout — so treating both
  connect failures as "unreachable" does **not** false-fire on a warming box.
  Only a genuinely off/unreachable box trips `OllamaUnreachableError`.
- **SD-3 — message → fixed advisory + warm one-liner; model name templated from
  `settings.recommender_model`.** Accepted with one refinement: the warm curl
  interpolates `settings.recommender_model` (not a hard-coded `gpt-oss:20b`) so
  the ping stays correct if the pinned model changes; the active `oct_vertical`
  is **excluded** from the body (keep it minimal / no-PII). Exact phrasing stays
  trivially Cray-tunable (it is a string constant).
- **SD-4 — cooldown → stamp on successful send, process-local in-memory.**
  Accepted: a failed POST does not suppress the next attempt (prioritises alert
  delivery); cooldown resets on app restart (no cross-restart persistence, per
  Out of Scope).

## References

- **ADRs:** ADR-002 (MS-S1 MAX LLM server); ADR-010
  (`docs/adr/0010-llm-reasoning-hook-surface.md`) — LLM brain-swap + rule
  fail-safe, **IN-4** (lines 402–403: "never raise into the runtime loop");
  ADR-012 D4.3 (author≠reviewer disclosure); ADR-013 D5
  (`docs/adr/0013-autonomy-axis-relocation.md`) — harness Telegram notify
  prior art; CLAUDE.md §8 (public-repo secret hygiene + PDPA forward-looking).
- **Plans:** PLAN-0006 (LLM reasoning hook); PLAN-0007
  (`docs/plans/done/0007-harness-autonomy-layer-phase-1.md`) — `telegram.sh`
  notifier (done); PLAN-0013 (OCT demo this supports — done, PR #99).
- **Source (verified):** `services/engine/llm/client.py` (lines 31–38
  `OllamaError`; 60–77 transport-injection seam; 114–126 transport/JSON catch);
  `services/engine/recommender.py` (lines 150–177 `recommend()`; broad
  `except Exception` at line 170; `_rule_recommend` 180–240);
  `services/engine/nl_query.py` (lines 434–502 `answer_question()`;
  translate-catch line 460; `_phrase` `except Exception` line 410);
  `services/api/config.py` (lines 27–157 `Settings`; `llm_backend` 69–76);
  `services/api/routers/actions.py` (`/recommendations` → `recommend()`,
  lines 55–91); `services/api/routers/query.py` (`/query` → `answer_question()`,
  lines 32–35).
- **Prior art (reuse env-var contract only — do NOT call):**
  `tools/notify/telegram.sh`; `.claude/hooks/notification_telegram.py`.
- **Tests (pattern to mirror):** `tests/services/engine/llm/test_client.py`
  (`httpx.MockTransport` seam, `_client(handler)`, `ConnectError` →
  `OllamaError` at lines 113–120).
- **Project memory:** `project_ms_s1_ollama_reachability` (reach MS-S1 at
  `192.168.1.133:11434`, not the `ms-s1-max` hostname).
