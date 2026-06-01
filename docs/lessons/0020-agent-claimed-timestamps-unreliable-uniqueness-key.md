# Lesson #20: Agent-claimed timestamps are an unreliable uniqueness key — LLM producers can't self-clock, guess round values, and collide

> **Status:** Codified 2026-06-01 (session 29). Surfaced by the live producer↔consumer smoke of the PLAN-0010 autonomy loop (the two Desktop routines `phase35-smoke-cowork-heartbeat` + `loop-dispatcher`), which reproduced — in production — the exact collision documented the same session in `tests/loop/test_loop_roundtrip.py`.
> **Severity:** Low for the current smoke (heartbeats are interchangeable, so a deduped fire loses nothing). Medium–high for real PLAN-0010 Step-5 payloads, where two distinct messages under one guessed name = **silent data loss**. Also a standing **observability** defect: a loop that mostly dedups can look healthy while no fresh work flows.
> **Cross-references:** PLAN-0010 AC-2 (collision-resistance "must not depend on the producer's drifting clock" — this lesson is its empirical proof); `tests/loop/test_loop_roundtrip.py` (`test_nonce_collision_drops_second_body_silently` + `test_rand_suffix_prevents_collision`); `tools/loop/dispatcher.py` (`_process_one` keys idempotency on the **filename**, before parsing); `docs/runbooks/loop-dispatcher-scheduled-task.md` (§"Producer drift"); STATUS session-29 ledger. [[lesson-0017-mcp-cross-tab-visibility-empirical-probe]] (the "probe before infer" sibling — both say: trust observed system state, not an agent's self-report).

## 1. The finding

The PLAN-0010 producer (`phase35-smoke-cowork-heartbeat`, a Haiku-tier Cowork routine) builds its message filename as `cowork-smoke-heartbeat-<NONCE>.msg.md`, where `<NONCE>` is the current UTC time formatted `YYYYMMDDTHHMMSSZ`. The consumer (`loop-dispatcher`) keys idempotency on the **filename**: if `processed/<name>` already exists, the inbox copy is unlinked and the message is **not** re-processed (`skipped_idempotent`).

In the session-29 live smoke the producer fired and — by its own visible reasoning — **could not determine the real time**:

> *"No specific time is given... I'll assume it fired at ~07:00 UTC."*

It wrote `cowork-smoke-heartbeat-20260601T070000Z.msg.md`. That NONCE **already existed in `processed/`** (a 00:04 run that morning had archived the same guessed value). The consumer saw the name, deduped it (`skipped_idempotent=1`), and the producer's fresh heartbeat was dropped — the archived copy kept its original `00:04` mtime. The data-loss path was not hypothetical; it triggered on the very first manual test fire.

## 2. Why it happens

- **A sandboxed LLM producer has no reliable clock.** The Cowork tab cannot run `bash` on the UNC-mounted repo (K-1), and the harness injects only the *date*, not a granular time. So the producer **guesses**, and LLMs guess *round, plausible* values — `07:00`, `12:00`, `00:00` — which recur and collide across fires.
- **`claimed_time` is explicitly audit-only.** The schema sets `time_authority: mtime`; ordering uses filesystem mtime, and the claimed timestamp is decorative. But the **filename NONCE is derived from that same unreliable clock**, so the *one* field that drives collision-resistance inherits the unreliability.
- **Idempotency is name-based and runs before parse.** This is correct and deliberate (crash-safe re-processing), but it means a duplicate *name* silently discards a duplicate-named message regardless of body.

## 3. The convention

**Never use an agent-claimed timestamp as a uniqueness/collision key. Collision-resistance must come from a source independent of the producer's clock.**

- **LLM / best-effort producers:** append a freshly-generated `-<rand>` suffix (4 chars base32-lowercase `[a-z2-7]`) to every filename — `<producer-id>-<NONCE>-<rand>.msg.md`. The schema already permits the optional `-<rand>` group; the consumer needs no change. Even weak LLM randomness over `32^4 ≈ 10^6` combinations makes a same-fire collision negligible.
- **Deterministic / code producers (real Step-5):** use a real monotonic or content-addressed key (counter, uuid, content hash), not a wall-clock string.
- **The NONCE stays for human/archeology readability**, but it is *not* the uniqueness guarantee.

## 4. Observability corollary

Without unique names, a producer that keeps guessing the same few round hours has **most of its fires deduped**. The loop drains cleanly (`inbox → 0`) and *looks* healthy, but the consumer's `ok` count no longer tracks producer liveness — it is mostly `skipped_idempotent`. Unique names restore the invariant "one fresh producer fire ⇒ one `ok`," which is what makes the heartbeat a meaningful liveness signal.

## 5. The fix (applied session 29)

The producer routine's "Construct the filename" instruction was amended to emit `cowork-smoke-heartbeat-<NONCE>-<RAND>.msg.md` with a fresh 4-char `[a-z2-7]` suffix per fire (Cray, Desktop UI — no consumer-side code change). `tests/loop/test_loop_roundtrip.py::test_rand_suffix_prevents_collision` pins the behavior: same NONCE + distinct `-<rand>` ⇒ both messages process, no loss.
