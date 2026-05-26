# PLAN-0010 Step 1 — Message schema + lifecycle

**Status:** Ready for execution (this is the design artifact; Step 2/3/4/5/6 consume the contract defined here)
**Owner:** Claude Code (Tier 2 — loop on-disk contract is Code-exclusive per ADR-013 D1)
**Created:** 2026-05-26
**Parent plan:** [PLAN-0010 §Step 1](0010-phase3-5-scheduled-task-autonomy-loop.md)
**Related ADRs:** ADR-013 (autonomy axis relocation — D1 phased relocation), ADR-009 (D2 only-Code-commits boundary), PLAN-0008 (loop-detect L1–L4 reused in consumer)
**Related lessons:** Lesson #8 (Cowork K-1/K-2 — binds producer write-only contract), Lesson #9 (Auto-mode Sonnet+ floor for consumer), Lesson #10 (classifier-blocks-direct-push — informs consumer commit gate)
**Related smoke findings:** `docs/research/private/phase3.5-smoke/findings.md` (F1–F10; gitignored, local-durable)

> **SD-3 resolution recap.** PLAN-0010 §Surfaced-decisions SD-3 was ratified 2026-05-26 as "Code picks at execution." This document is that execution-time pick. The chosen path is **`loop/` at repo top** (rationale §1).

> **Sequencing.** Step 1 unblocks PLAN-0010 Steps 2/3/4/5/6 (execution arc). Step 2 (Cowork-side producer) consumes the filename pattern + frontmatter schema. Step 3 (Code-side consumer) consumes the lifecycle + idempotency rules + retention policy. Step 5 (PLAN-0007 L1–L4 integration in consumer) consumes the failure-handling contract.

## Goal

Define the **machine-checkable on-disk contract** for the scheduled-task autonomy loop introduced by PLAN-0010 (the Cowork producer ↔ Code consumer pattern) — concrete filename grammar, YAML frontmatter shape, payload body structure, lifecycle states, idempotency mechanism, and retention policy. Step 1 is **design + directory skeleton only**; the parser, validator, producer prompt, and consumer poller are downstream deliverables in Steps 2–3.

The load-bearing safety property — *no commits via the loop unless the composed G5 gate allows it* — is preserved by Step 3 + the composed identity gate shared with PLAN-0009 Step 1b §1. Step 1 does not by itself enforce commit boundaries; it defines the on-disk shape the gate operates on.

## §1 — Directory layout (SD-3 resolution)

**Decision: `loop/` at repo top.** (Cray-delegated to Code at execution time per SD-3 ratification.)

### Layout

```
loop/
├── inbox/
│   └── .gitkeep          ← git-tracked sentinel; messages NOT tracked
└── processed/
    └── .gitkeep          ← git-tracked sentinel; archived messages NOT tracked
```

### `.gitignore` additions (binding for this PR)

```
# PLAN-0010 loop — messages are uncommitted by design (producer has no git
# per K-1; consumer processes in place then archives to processed/).
loop/inbox/*
loop/processed/*
!loop/inbox/.gitkeep
!loop/processed/.gitkeep
```

### Why `loop/` at repo top (not `tools/loop/`)

| Aspect | `loop/` at repo top (chosen) | `tools/loop/` alternative |
|---|---|---|
| Pattern fit | Mirrors how `.claude/handoffs/` (data) is distinct from `tools/handoffs/` (code) — data and code live in separate trees | Would mix data with the code-only `tools/handoffs/` + `tools/notify/` siblings |
| Discoverability | Top-level dir signals "core mechanism," not auxiliary tooling | Buried under `tools/`; reader must know the convention |
| Top-level cost | +1 top-level dir | 0 |
| Future code home | Code (parser, dispatcher, validator) will live at `tools/loop/` per the existing `tools/handoffs/` precedent | Same `tools/loop/` for code regardless |

The +1 top-level dir is the only cost; everything else favors the split.

### K-2 + worktree constraints (binding regardless of path choice)

Both apply to `loop/` exactly as PLAN-0010 §Step 1 requires:

1. **K-2 (Cowork cannot Write under `.claude/`)** — `loop/` is outside `.claude/`, so the Cowork producer can Write into `loop/inbox/` (Step 2 contract).
2. **Consumer reads from main checkout** — `loop/` is in the working tree. The consumer must run from the **main checkout** (not a worktree), because a worktree-bound consumer is blind to gitignored files per the 2026-05-25 STATUS reconciliation finding. Step 3 enforces this via the consumer's launch documentation.

### Code home (deferred to Step 2/3 execution)

Forward-looking note (not in this PR): Step 2 (producer) and Step 3 (consumer) introduce code under `tools/loop/`:

```
tools/loop/
├── _schema.py           ← Step 3 — stdlib YAML subset parser + validator (mirrors tools/handoffs/_schema.py)
├── dispatcher.py        ← Step 3 — consumer poller (reads inbox/, processes, archives)
└── (producer prompt is text-only, lives in the scheduled task definition, not in tools/loop/)
```

## §2 — Filename pattern

### Grammar (binding)

```
<producer-id>-<mtime-nonce>[-<rand>].msg.md
```

| Part | Type | Example | Rule |
|---|---|---|---|
| `<producer-id>` | kebab-case ASCII | `cowork-smoke-heartbeat`, `code-smoke-reader` | `^[a-z][a-z0-9-]{2,63}$` — matches the producer task name in the scheduled-task definition |
| `<mtime-nonce>` | UTC ISO-8601 basic | `20260526T085945Z` | Derived from filesystem `mtime` at write time. UTC. Basic (no separators) for filename safety. Second-resolution. |
| `<rand>` | base32 lowercase, 4 chars | `x7k2` | **Omitted** by default. Added **only** when a same-second collision would otherwise overwrite an existing file. Producer prompt encodes this fallback. |
| `.msg.md` | literal suffix | — | Two-segment suffix lets `glob("loop/inbox/*.msg.md")` filter sentinels (e.g. `.gitkeep`) cleanly |

### Why mtime, not claimed time

Phase 3.5 smoke (gitignored findings F2–F4): observed agent-claimed timestamps drifted from filesystem `mtime` by −3h34m to +5h17m across 7 fires. Filenames keyed on claimed time caused collisions that made the inbox count of 7 under-represent ~11 successful fires. **Filesystem `mtime` is the only authoritative ordering signal.** The body's `claimed_time` field is informational — the parser MUST NOT use it for ordering or idempotency.

### Why a `.msg.md` double-suffix (not just `.md`)

- `loop/inbox/*.msg.md` glob excludes the `.gitkeep` sentinel without an explicit skip
- A future reader of `loop/inbox/` immediately recognizes these are not ordinary markdown docs
- Keeps `.md` so editor tooling (syntax highlighting, preview) still works for inspection

## §3 — YAML frontmatter schema

### Required fields

| Field | Type | Example | Constraint |
|---|---|---|---|
| `producer_id` | string (kebab-case) | `cowork-smoke-heartbeat` | Matches the `<producer-id>` segment of the filename exactly |
| `schema_version` | integer | `1` | Start at 1; bump on breaking schema changes; consumer rejects unknown versions (fail-closed) |
| `message_type` | string (enum) | `smoke_heartbeat` | One of the enum values listed in §3.1 below |
| `claimed_time` | string (RFC 3339 UTC) | `2026-05-26T08:59:45Z` | Agent's claimed write time — informational only; **never authoritative** |
| `time_authority` | literal string | `mtime` | Explicit caveat — must equal `"mtime"`. Encodes the §2 ordering rule into every message so a future reader cannot misread `claimed_time` as authoritative |

### Optional fields

| Field | Type | Example | Use |
|---|---|---|---|
| `correlation_id` | string | `smoke-2026-05-26-batch-3` | Group related messages (e.g. producer's heartbeat + consumer's processed-receipt) |
| `expires_after` | string (RFC 3339 UTC) | `2026-05-27T00:00:00Z` | Consumer skips (still archives to `processed/`) if `now > expires_after`. Prevents stale heartbeat-class messages from being processed days late |
| `references` | list[string] | `["docs/STATUS.md", "https://example.com/dash"]` | Repo paths or URLs the consumer may want to consult; informational |

### §3.1 — `message_type` enum (Phase 3.5 vocabulary)

Initial vocabulary (Step 4 (b) smoke regression is the only one shipping in Phase 3.5; the rest are reserved for future Step 4 use cases (a)/(c)/(d) when they unblock):

| Value | Purpose | Phase 3.5 ship status |
|---|---|---|
| `smoke_heartbeat` | Producer's periodic liveness ping | ✅ ships (b) |
| `smoke_receipt` | Consumer's "processed N inbox messages" rollup | ✅ ships (b) |
| `status_digest` | Hourly STATUS rollup | deferred (Step 4 (a)) |
| `governance_reminder` | Poke unmerged ADRs/PLANs older than N days | deferred (Step 4 (c)) |
| `deferred_oq_rotation` | Surface one open question from `docs/plans/done/` | deferred (Step 4 (d)) |

Consumer rejects unknown `message_type` values (fail-closed; archive to `processed/` with a logged warning so the message is not retried indefinitely).

### Schema-version compatibility rule

- Consumer **rejects** any message where `schema_version != 1` in this Phase. Fail-closed, archive with warning.
- The bump path (v1 → v2) is: ship v2-parser in a consumer release that handles both v1 and v2; only then bump producers to emit v2.
- The reverse (producer ahead of consumer) is what fail-closed protects against.

## §4 — Payload body schema

The body is markdown beneath the frontmatter. Use H2 sections; consumers parse by section heading.

**Section ordering is insensitive** (amended 2026-05-26, session 14 Step 6 Phase 1.5 spec-drift fix). The parser uses a `{heading: content}` dict keyed on the section header (`tests/loop/test_schema.py::test_section_ordering_insensitive`), which is strictly more robust than the earlier draft's `split("\n## ").zip` approach. Producers should still emit sections in the canonical order below for human readability + diff stability, but the consumer does not enforce order at parse time.

*Earlier draft text (preserved for archeology):* "Required section ordering matters — consumers can `split('\n## ')` and zip to keys."

### Required sections

```markdown
## Subject

<one-line plain-text subject; ≤ 120 chars; mirrors an email subject>

## Body

<≤ 2k tokens of structured prose or bullet lists; the substantive payload>

## Action requested

<exactly one of: `none`, `acknowledge`, `process-then-archive`, or a free-form
imperative if message_type allows it per §3.1 future vocabulary>
```

### Optional sections

```markdown
## Citations

- `path/to/file:42` — <quote or paraphrase>
- <url> — <one-line excerpt>

## Residual gaps

<list any facts the producer could not resolve; mirrors the
explore-research / plan-drafter discipline>
```

### Rationale for markdown-section payload (not all-YAML)

- The frontmatter handles small, structured metadata cleanly
- The payload is variable-length prose — YAML strings with multi-line content are awkward (literal vs folded, indentation traps)
- Markdown sections give a consumer + a human reader the same parse path
- Mirrors the handoff schema's discipline (`tools/handoffs/_schema.py` — frontmatter for structure, body for prose)

## §5 — Lifecycle + idempotency

### State machine

```
[producer Write] → loop/inbox/<filename>.msg.md
                       ↓ (consumer scans inbox/ in mtime order)
                  [consumer parse + dispatch]
                       ↓ (on success)
                  loop/processed/<filename>.msg.md
```

### Consumer scan order (binding)

1. `os.scandir("loop/inbox/")` → filter `*.msg.md`
2. Sort ascending by **filesystem `mtime`** (the §2 authoritative key) — `st_mtime_ns` preferred over `st_mtime` for resolution
3. Process each in order; do not parallelize within a single consumer run (parallelism is a future optimization; Phase 3.5 ships serial)

### Idempotency mechanism

Per-message idempotency is **filename-keyed**, not content-keyed. The consumer rule:

1. Before processing `loop/inbox/<name>.msg.md`, check whether `loop/processed/<name>.msg.md` already exists
2. If yes → skip (the message was already processed in a prior consumer run that crashed before the `mv` completed; the no-op is the recovery path)
3. If no → process, then `mv` to `processed/` atomically

The atomic `mv` is the commit boundary. Either `inbox/<name>` exists or `processed/<name>` exists, never both, never neither (assuming the FS provides atomic rename, which POSIX guarantees on same filesystem).

### Failure handling (consumer-side; binding for Step 3 integration)

- **Parse failure** (malformed YAML, missing required field, unknown `message_type`, `schema_version != 1`) → archive to `processed/` immediately with a `loop/processed/<name>.parse-error.log` sibling containing the error reason. Do NOT retry — the message will not parse differently on retry.
- **Dispatch failure** (downstream handler raises) → leave message in `inbox/`; integrate PLAN-0008 L1–L4 loop-detect so repeated dispatch failure on the same message trips the loop fail-safe and pauses + Telegram-alerts rather than thrashing.
- **Expired message** (`now > expires_after`) → archive to `processed/` with a `loop/processed/<name>.expired.log` marker; do not dispatch.

### Cross-process consumer safety (binding assumption)

*Documented 2026-05-26, session 14 Step 6 Phase 1.5; mitigates §8 residual risks #6 + #7.*

Phase 3.5 ships with **single-consumer-process topology** — only one `python -m tools.loop.dispatcher` runs at a time (Cray invokes manually; the Code Desktop scheduled-task wiring is deferred to Phase 4). The lifecycle invariant ("message exists in inbox/ OR processed/, never both, never neither") rests on POSIX `rename(2)` atomicity within a single filesystem (verified by the same-fs check at consumer startup).

**If two consumers ever run concurrently** (anticipated when Phase 4 wires the scheduled task and Cray simultaneously runs a manual dispatch):

1. POSIX `rename(2)` guarantees exactly one process wins the move; the loser's `Path.replace()` raises `FileNotFoundError`. The current dispatcher (`tools/loop/dispatcher.py`) does **NOT** catch this exception, so the losing process exits with a traceback (non-zero return code). Filesystem invariant remains intact (loser does not create a duplicate); only the process-level exit code is dirty.
2. Phase 4 unblock criteria for scheduled-task wiring: **add `FileNotFoundError` recovery to `_archive` call sites** so the loser returns `SKIPPED_IDEMPOTENT` cleanly instead of crashing. This is a focused dispatcher PR (~5 LOC + 1 unit test using `multiprocessing.Process`) that should land *before* the scheduled task fires for the first time.
3. Step 6 Phase 2 (session 14, this session) live-AC verification will exercise the race manually with two terminals; observed behavior feeds into the Phase 4 unblock PR.

**Why deferred (not fixed in Phase 3.5):** YAGNI — the feature requiring concurrent consumers (scheduled-task wiring) is itself Phase 4. Fixing now would add untested code for a hypothetical scenario; fixing alongside the feature ensures the fix is exercised by the same PR that makes it load-bearing. (Originally evaluated at session-14 Step 6 Phase 1.5 with a 30-min cost estimate; actual cost ~90 min including dispatcher code change + multiprocessing test infrastructure — recommendation revised to defer.)

## §6 — Retention policy

### `loop/processed/` retention (binding for Step 3)

- **Age threshold:** archive entries older than **30 days** are eligible for prune
- **Size threshold (secondary):** if `loop/processed/` exceeds **100 MB** total, prune oldest entries (by `mtime`) until under threshold regardless of age
- **Prune frequency:** consumer runs prune at the **end of each scan cycle** — bounded, predictable, no separate cron
- **Prune order:** oldest first; preserve the most recent N=200 entries even if older than 30 days (cheap forensics floor)
- **Logged:** each prune cycle writes a one-line summary to consumer stdout (`pruned 14 messages, oldest=2026-04-26, freed 2.1MB`); the summary is captured by the scheduled task's transcript

### `loop/inbox/` retention

No automatic prune — inbox entries are processed or surfaced as failures (§5). A persistent inbox file that the consumer cannot process is a **signal**, not noise; surfacing it via L1–L4 loop-detect is the right behavior.

## §7 — Surfaced decisions for Cray

Per ADR-009 D1 + the surfaced-decisions discipline (Cowork rule #8 adopted for Code's own design docs): decisions with multiple defensible answers must be surfaced for Cray rather than silently chosen. Below: 4 SDs where I picked a reasonable default but the alternative is also defensible. PR review is the adjudication moment.

### SD-Step1-1 — Filename nonce format

**Decision (Code-picked):** UTC ISO-8601 basic — `20260526T085945Z` (no separators).
**Alternative considered:** Epoch decimal `1748204385`.
**Why ISO over epoch:** human-readable at a glance, sortable lexicographically (so an `ls`/`scandir` ordering is the same as `mtime` ordering even without a sort call — defense-in-depth against a buggy sort), and unambiguous about timezone (the `Z` suffix is explicit).
**Why Cray might prefer epoch:** more compact (10 chars vs 16), and ordering correctness does not depend on a fixed-width string.
**Recommendation:** keep ISO; flip to epoch only if the +6 chars/filename matters at scale (it does not at heartbeat cadence — ~24 files/day worst case).

### SD-Step1-2 — `expires_after` default behavior

**Decision (Code-picked):** Optional field. If absent, the message never expires (consumer always dispatches regardless of age).
**Alternative considered:** Mandatory with a sane default (e.g. 24h from `claimed_time`).
**Why optional:** heartbeat-class messages have inherent freshness; a stale heartbeat is its own signal (consumer fell over). Forcing an expiry default would mask that signal.
**Why Cray might prefer mandatory:** prevents accidental "process a 30-day-old message because the consumer was down for a month" pathology.
**Recommendation:** keep optional for Phase 3.5; reconsider when (c) governance-reminder use case ships (the only future type where mandatory-expiry is clearly correct).

### SD-Step1-3 — `loop/processed/` retention defaults

**Decision (Code-picked):** 30 days OR 100 MB OR floor-of-N=200 (most-permissive wins).
**Alternatives considered:** 7 days / 10 MB (aggressive); 90 days / 1 GB (lax).
**Why 30/100/200:** heartbeat cadence is ~24 msgs/day → 30 days = ~720 messages × ~2 KB each = ~1.4 MB. The 100 MB ceiling is mostly defensive against accidental verbose payloads. The N=200 floor preserves forensic visibility for at least a week even if the size ceiling triggers.
**Why Cray might prefer 7/10/200:** keeps the directory truly small; forces verbose payloads to be diagnosed.
**Recommendation:** keep 30/100/200; tighten only if observability needs to see something we are not currently logging.

### SD-Step1-4 — Per-message parse-error sibling files

**Decision (Code-picked):** On parse failure, write `loop/processed/<name>.parse-error.log` (sibling to the archived bad message) with the error reason.
**Alternative considered:** Log to consumer stdout only; do not write per-message sibling.
**Why sibling:** the bad message is preserved verbatim in `processed/<name>.msg.md`, and the sibling `.parse-error.log` makes "why did this fail?" answerable from `ls -la loop/processed/` without correlating to a scheduled-task transcript.
**Why Cray might prefer stdout-only:** halves the file count in `processed/`; sibling files are an extra retention/prune surface.
**Recommendation:** keep sibling; the parse-error.log files are short (~200 bytes), age out with their `.msg.md` partner, and the forensics win is worth the file count.

## §8 — Verification matrix (case-coverage per Cray verification-rigor directive)

Mirrors PLAN-0009 Step 1b §8 + PLAN-0010 §Verification. Per the binding directive: each AC ships rows covering **happy / boundary / fail-closed / adversarial / concurrency**, with a test mapped to **every** row; uncovered cases named as residual risk; sign-off states confidence explicitly. Bar = "we are confident it does what we intend," not "tests pass."

### Per-AC matrix (Step 3 fills the test column for consumer-side; Step 2 for producer-side)

| AC | Happy | Boundary | Fail-closed | Adversarial | Concurrency |
|----|-------|----------|-------------|-------------|-------------|
| **AC-Step1-1 schema parse** | Well-formed message parses → struct returned | Optional fields all-absent + all-present | Missing required field → reject; `schema_version != 1` → reject; unknown `message_type` → reject | Frontmatter with extra unknown keys → tolerate (forward-compat); body section ordering swapped → reject (consumers split-zip) | N/A (parser is pure function) |
| **AC-Step1-2 lifecycle** | inbox/<msg> → processed/<msg> in single consumer run | Empty inbox → no-op; single-message inbox → process exactly once | Crashed consumer mid-mv → next run skips (idempotency); processed/<msg> pre-exists → skip | Producer rewrites same filename twice (same-second collision) → §2 rand suffix prevents overwrite | Two consumers run on same inbox → second sees no work (first claims via atomic mv) — Step 3 must include this case |
| **AC-Step1-3 mtime ordering** | 3 messages with mtimes 1s/2s/3s → processed in 1→2→3 order | Two messages with identical mtime_ns → tiebreak by filename lexicographic | Filesystem with no mtime support (FAT) → consumer refuses to start (Step 3 mount-check) | Producer fakes mtime (touch -t) → §2 still authoritative (mtime is filesystem-owned) | Producer writes during consumer scan → next scan picks it up (no missed-message hazard) |
| **AC-Step1-4 retention** | 30-day-old entries pruned; <30-day kept | Exactly-30-day entries pruned (boundary inclusive); N=200 floor preserved | Disk full mid-prune → consumer recovers next run; bad mtime stat → skip (don't crash) | Symlink in processed/ → resolved, not followed (Step 3 implementation detail) | Prune during inbox processing → no race (different directories) |

### §8.1 — Test mapping (Step 6 Phase 1, session 14)

For each (AC, case) coordinate the matrix above defines, this section maps to the
existing unit test(s) that cover it. Legend:

- **`tests/...`** — concrete unit test path (one or more `pytest` IDs)
- **(L)** — verifiable only via Phase 2 live AC (live producer fire across a clock-cycle, real cross-process consumer race); primitive is not unit-testable
- **(RR)** — uncovered cell, flagged as residual risk for sign-off

#### AC-Step1-1 schema parse
- **Happy** — well-formed parses cleanly: [`tests/loop/test_schema.py`](../../tests/loop/test_schema.py) — `test_minimal_well_formed_parses`, `test_all_message_types_parse`, `test_all_canonical_actions_parse`
- **Boundary** — optional fields all-absent + all-present: `test_minimal_well_formed_parses` (absent), `test_all_optional_fields_present` (present), `test_subject_exactly_120_chars_clean`, `test_action_requested_with_backticks_stripped`
- **Fail-closed** — missing required / `schema_version != 1` / unknown enum / missing body section / malformed time:
  - Required-field rejection: `test_missing_producer_id_rejected`, `test_time_authority_missing_rejected`, `test_missing_body_subject_rejected`, `test_missing_body_action_rejected`, `test_missing_frontmatter_block_rejected`
  - Schema-version rejection (Step 1 §3 binding fail-closed): `test_schema_version_zero_rejected`, `test_schema_version_two_rejected`
  - Enum rejection: `test_unknown_message_type_rejected`, `test_time_authority_wrong_literal_rejected`
  - Time-format rejection: `test_claimed_time_without_timezone_rejected`, `test_claimed_time_malformed_rejected`, `test_expires_after_without_timezone_rejected`
  - Cross-check: `test_producer_id_mismatch_with_filename_rejected` (defends against post-write filename forgery)
- **Adversarial** — extra unknown keys / oversized subject / free-form action / section ordering / `.gitkeep`-shadow:
  - Forward-compat: `test_extra_frontmatter_keys_warn_only`
  - Lenient: `test_oversized_subject_warns_not_errors`, `test_action_requested_free_form_accepted`
  - Section ordering: `test_section_ordering_insensitive` — **NOTE spec drift** (see residual risk #5 below)
  - Filename grammar (`.gitkeep` shadow defense, residual #4 from current §): `test_filename_gitkeep_does_not_parse_as_message`, `test_filename_gitkeep_with_msg_md_suffix_does_not_parse`, `test_filename_short_producer_id_rejected`, `test_filename_uppercase_producer_rejected`, `test_filename_underscore_in_producer_rejected`, `test_filename_malformed_nonce_rejected`, `test_filename_wrong_extension_rejected`, `test_filename_rand_wrong_charset_rejected`, `test_filename_rand_wrong_length_rejected`
- **Concurrency** — N/A per spec (parser is a pure function); no test required

#### AC-Step1-2 lifecycle
- **Happy** — `inbox/<msg>` → `processed/<msg>` in a single consumer run: [`tests/loop/test_dispatcher.py::test_happy_message_archived`](../../tests/loop/test_dispatcher.py)
- **Boundary** — empty inbox → no-op; single-message → process exactly once; recover-after-flake clears state: `test_empty_inbox_noop`, `test_happy_message_archived`, `test_recover_after_partial_failures_clears_state`
- **Fail-closed** — crash mid-mv (idempotent skip), pre-existing processed copy, parse failure, expired, dispatch failure, poison threshold:
  - Idempotency: `test_idempotent_skips_when_processed_exists`
  - Parse-failure sibling log: `test_parse_failure_archives_with_sibling_log`
  - Expired sibling log: `test_expired_message_archives_with_sibling_log` (plus `test_not_yet_expired_dispatches_normally` as negative)
  - Dispatch failure left in inbox: `test_dispatch_failure_leaves_in_inbox_first_time`
  - Poison-threshold archive + alert (PLAN-0008 L1–L4 spirit): `test_poison_threshold_archives_and_alerts`
  - Same-fs invariant: `test_run_once_aborts_when_same_fs_check_fails`, `test_cli_aborts_when_same_fs_check_fails`, `test_same_filesystem_true_when_both_under_tmp`, `test_same_filesystem_false_when_inbox_missing`
  - Failure-state persistence: `test_failure_state_load_missing_returns_empty`, `test_failure_state_load_corrupt_returns_empty`, `test_failure_state_roundtrip`, `test_failure_state_clear`
- **Adversarial** — producer rewrites same filename twice (§2 rand suffix collision avoidance) → **(RR)** producer-side concern; consumer trusts filename uniqueness. Mitigated by producer prompt, not consumer code. Residual risk #2 below already names this.
- **Concurrency** — two consumers on same inbox, atomic-mv wins → **(RR-documented)** see §5 "Cross-process consumer safety" subsection (added Step 6 Phase 1.5, session 14). Phase 3.5 ships single-consumer topology; cross-process scenario is Phase 4 territory with explicit unblock criteria. Single-process atomic-mv invariant verified by tests above; cross-process documented as binding assumption, not unit-tested.

#### AC-Step1-3 mtime ordering
- **Happy** — 3 messages mtime 1s/2s/3s → processed in order: [`tests/loop/test_dispatcher.py::test_mtime_order_three_messages`](../../tests/loop/test_dispatcher.py)
- **Boundary** — identical mtime, tiebreak by filename lex: `test_mtime_tiebreak_by_filename_lex`; plus inbox scanner skips non-`*.msg.md`: `test_scan_inbox_skips_non_msg_md`, `test_scan_inbox_missing_dir_returns_empty`, `test_iter_inbox_filenames_helper`
- **Fail-closed** — FS without mtime support → consumer refuses to start: the *spec* says mount-support check; the *implementation* enforces **same-filesystem** check (stronger). Same-fs tests already cited under AC-Step1-2 fail-closed. Pure mtime-FS check **(RR)** — no FAT-mount unit test (rare in dev/prod environments).
- **Adversarial** — producer fakes mtime via `touch -t`: **(RR)** mtime is filesystem-owned per spec §2; the consumer trusts FS-reported mtime regardless of producer fakery. No unit test exercises this (it would require post-hoc `os.utime` after consumer scan window — which the mtime-ordering tests do exercise, indirectly establishing trust in `os.utime`-set mtimes).
- **Concurrency** — producer writes during consumer scan → next scan picks it up: **(RR)** partial coverage via `test_scan_inbox_skips_non_msg_md` (sentinel handling). Full cross-process race is **(L)** in Phase 2; cheap to verify with a live producer fire mid-`run_once`.

#### AC-Step1-4 retention
- **Happy** — 30-day-old pruned; <30-day kept: [`tests/loop/test_dispatcher.py`](../../tests/loop/test_dispatcher.py) — `test_retention_no_op_when_all_fresh`, `test_retention_prunes_old_entries_by_age`
- **Boundary** — N=200 floor preserved even when over-age; integrated into `run_once`: `test_retention_floor_preserves_recent`, `test_retention_integrated_into_run_once`; constants surface: `test_defaults_are_sensible`; size-driven prune: `test_retention_size_threshold_prunes_oldest`
- **Fail-closed** — disk full mid-prune → recover next run; bad mtime stat → skip; missing dir → no-op: `test_retention_missing_dir_no_op` covers missing-dir; disk-full and bad-stat **(RR)** — not unit-tested (would require fault injection); the implementation uses defensive `try/except` per Step 1 §6.
- **Adversarial** — symlink in `processed/` → resolved, not followed: **(RR)** implementation detail per Step 1 §8 — not unit-tested; rare/improbable in practice (producer doesn't create symlinks).
- **Concurrency** — prune during inbox processing: `test_retention_integrated_into_run_once` (single-process integration); cross-process **(L)** in Phase 2

#### Auxiliary tests (regression guards, not AC-row-mapped)
- DispatchResult enum surface: `test_dispatch_result_string_values`
- Scan-cycle summary line: `test_scan_cycle_summary_log_line`, `test_scan_cycle_summary_no_prune_omits_freed`
- Stderr alert JSON envelope: `test_stderr_alert_emits_json`
- CLI smoke: `test_cli_with_empty_inbox_exits_zero`
- ValidationError surface: `test_validation_error_render`, `test_validation_error_warning_severity`
- parse_message_file roundtrip: `test_parse_message_file_missing_file_returns_error`, `test_parse_message_file_roundtrip`

### Residual risks (named for sign-off)

1. **Atomic-mv assumption** — POSIX guarantees atomic `rename(2)` only within the same filesystem. If `loop/inbox/` and `loop/processed/` ever land on different mounts, the lifecycle invariant breaks. Step 3 must include a same-fs check at consumer startup; failure to verify aborts.
2. **Filename-keyed idempotency** — content changes that re-use a filename (producer bug) would be silently skipped by the `processed/<name>` check. Mitigated by §2 `mtime-nonce` (collisions across same-second require explicit `<rand>` suffix). Residual: a producer with a genuinely buggy filename generator could still mask updates.
3. **Schema-version rejection is fail-closed** — a v2 producer ahead of a v1 consumer drops messages silently into `processed/` with a warning. Operator must monitor consumer logs to notice. Mitigation: Step 3 emits a `loop_drop_count` metric per scan; observability dashboard (future) alerts on non-zero.
4. **`.gitkeep` sentinel collision** — a future producer accidentally writing `loop/inbox/.gitkeep.msg.md` would shadow the sentinel. Mitigated by the `^[a-z]` producer-id constraint (`.` is not lowercase letter), but worth a Step 3 unit test that names `.gitkeep` does NOT parse as a valid filename. **Verified by `test_filename_gitkeep_does_not_parse_as_message` + `test_filename_gitkeep_with_msg_md_suffix_does_not_parse` (Step 6 Phase 1, session 14).**
5. **~~Spec drift — body section ordering~~** (raised in Step 6 Phase 1; **closed in Step 6 Phase 1.5, session 14**) — §4 amended to declare the parser order-insensitive and preserve the earlier draft text for archeology. Cray's PR review ratifies the direction (order-insensitive is strictly more robust than the original split-zip approach; `test_section_ordering_insensitive` confirms).
6. **Producer-side filename-collision race not unit-testable from consumer side** (new in Step 6 Phase 1) — AC-Step1-2 Adversarial cell ("producer rewrites same filename twice"). The consumer trusts filename uniqueness; the §2 `mtime-nonce` + `<rand>` suffix discipline is the producer prompt's responsibility. No consumer unit test verifies producer-side collision avoidance. Sign-off must name this division of responsibility explicitly.
7. **Cross-process race coverage** (raised in Step 6 Phase 1; **mitigation documented in Step 6 Phase 1.5, session 14** — see §5 "Cross-process consumer safety") — AC-Step1-2/3/4 Concurrency cells rely on single-process atomic-`rename(2)` + same-fs invariant. Phase 3.5 ships single-consumer-process topology (manual dispatch only); the concurrent-consumer scenario is **Phase 4 territory** (when the Code Desktop scheduled task wires). §5 documents the binding assumption and the Phase 4 unblock criterion: add `FileNotFoundError` recovery to `_archive` call sites + a `multiprocessing.Process` unit test before the scheduled task fires for the first time. Phase 2 live AC verification (session 14) will exercise the race manually with 2 terminals; observed behavior feeds the Phase 4 unblock PR.

## §9 — Deferred to Step 2/3 execution

Out of scope for Step 1. Step-by-step execution plan (Phase 3.5 §Steps 2–6 in `docs/plans/0010-phase3-5-scheduled-task-autonomy-loop.md`):

| PLAN-0010 Step | Step 1 deliverable consumed | New work |
|---|---|---|
| **Step 2** — Cowork-side producer | §2 filename pattern + §3 frontmatter + §4 body schema | Author the Cowork scheduled-task prompt; verify K-1/K-2 compliance; smoke-test the producer→inbox path |
| **Step 3** — Code-side consumer | §1 layout + §2 mtime ordering + §5 lifecycle + §6 retention | Implement `tools/loop/_schema.py` (parser) + `tools/loop/dispatcher.py` (poller); integrate PLAN-0008 L1–L4 loop-detect; unit-test the AC matrix; live-verify against the resumed smoke scheduled tasks |
| **Step 4** — Composed identity gate integration | (none directly — Step 3 + PLAN-0009 Step 5 do the gate work) | Document the gate's interaction with the consumer's commit handling (mirror PLAN-0009 Step 1b §1 composed check) |
| **Step 5** — Smoke regression workload (Cray-ratified SD-1) | §3.1 vocabulary (`smoke_heartbeat`, `smoke_receipt`) | Cowork producer emits `smoke_heartbeat`; Code consumer rolls up daily into `smoke_receipt`; alert on reliability drift |
| **Step 6** — Tests + live AC + closeout | §8 matrix template | Fill the test column for every row; live-verify the matrix; sign off residual risks |

## Implementation Notes

Drafted by Code (Tier 2, Claude Code Opus 4.7) in session 12 (2026-05-26). Per ADR-013 D1 phased authority, the `plan-drafter` subagent (PLAN-0009 Step 3, shipped earlier this session — [PR #30](https://github.com/CrayJThiemsert/vero-lite/pull/30)) is now available but **was not used for this doc** because:

1. Author≠reviewer separation under ADR-013 OQ-1 — `plan-drafter` shares the main harness's framing, so an in-harness draft has no independent-deliberation check beyond Cray's PR review
2. The dispatch protocol (Step 4 of PLAN-0009) is not yet finalized — there is no formal in-harness dispatch path to invoke `plan-drafter` with bounded scope yet
3. This doc is a *companion design* to a Cowork-drafted parent plan, so Code drafting in-harness preserves the same independent-check shape that PLAN-0009 Step 1b used (Cowork drafted PLAN-0010 → Code drafts PLAN-0010 Step 1, Cray reviews both at PR merge)

The author≠reviewer separation for *this* artifact is held by **Cray's review at PR merge**, not by drafter/reviewer tier distinction. Disclosure: **INTACT** — Cray reviews; AI drafts; outline derives from the Cowork-drafted parent PLAN-0010 + this session's Code-side execution-time decision (SD-3 ratification + 4 sub-decisions surfaced in §7).

AI assistance: drafted by Code (Claude Code, Opus 4.7). AI-assistance noted in commit body per CLAUDE.md §7; never `Co-Authored-By`.
