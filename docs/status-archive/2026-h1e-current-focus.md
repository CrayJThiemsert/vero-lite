# STATUS.md — archived Current Focus blocks (2026 H1, continuation e)

> ✅ **THIS FILE IS THE LIVE APPEND TARGET for Current-Focus rotations** (started session 281, 2026-09-06). New blocks go at the **BOTTOM**, in rotation order.
> **Why this file exists:** [`2026-h1d-current-focus.md`](2026-h1d-current-focus.md) reached **189,622 B** with only **6,986 B** of headroom under R4's **196,608-byte split trigger**. Session 281's rotation is **3,269 B**, which would have left it at 192,891 B — essentially the 192,607 B at which `h1c` was closed. Per R4 (`tools/check_archive_size.py`; `docs/runbooks/memory-architecture.md` §"R4 — Archive, don't drop") the continuation file is started **before** the bar is crossed, not after — h1d stays under the trigger and is now **closed to appends**.
> **Sibling chain — for THIS chain the NEWEST LETTER holds the NEWEST content** (the opposite of the `-status.md` chain): [`2026-h1b-current-focus.md`](2026-h1b-current-focus.md) (session 25) → [`2026-h1-current-focus.md`](2026-h1-current-focus.md) (legacy base, closed) → [`2026-h1c-current-focus.md`](2026-h1c-current-focus.md) (closed session 227) → [`2026-h1d-current-focus.md`](2026-h1d-current-focus.md) (closed session 281) → **this file (live)**. Current-Focus-only; SEPARATE from the `2026-h1b..h-status.md` rotation chain — same letter scheme, different corpus, different append rules.
> **Tier-3: grep + windowed reads only, never a whole-file Read.**

**No content is lost by this rotation.** Every block below is the byte-exact text
that stood in `docs/STATUS.md` at `fc01cd0`, carved with `git show` rather than
retyped or copied from a subagent's return, and verified by reading it back out
of this file after the append.


## Rotated this reconcile — session 281 (2026-09-06)

### Rotated at the s281 reconcile — the session-278 Current-Focus block [on the R2 headroom rule, not a cap overage: STATUS opened at 57,638 B with 7,898 B under the 64 KB R1 ceiling, and admitting the s281 block to a three-wide window would have left about 4 KB. The window lands at three again (279, 280, 281). Caller-measured 3,269 B as carved. 🔴 This block's own Current-Focus rotation-ledger entry is NOT re-appended: it was measured already present verbatim in `2026-h1d-current-focus.md` under that file's own `### Rotated at the s278 reconcile` header, having travelled inside that rotation's slice, so R4's move duty is discharged and a second copy would duplicate a move-only archive. This is the SECOND consecutive reconcile at which a rotating block's own ledger entry was found already archived — treat it as the expected case and probe before appending, never after.]

> **Session 278, 2026-09-04 (`8859c27` → `095c419`) — SEVEN PRs
> ([#1392](https://github.com/CrayJThiemsert/vero-lite/pull/1392)–[#1398](https://github.com/CrayJThiemsert/vero-lite/pull/1398)),
> six merged. What it established: a closure claim repeated by two artifacts is still
> one claim — and the evidence for every AC tick in this repo was untracked by
> default, which is why nobody could check it.**
>
> 🔴 **"9 of 11 closed" was wrong; SEVEN were earned.** The s277 handoff and this file
> both asserted nine. Measured against PLAN-0120's own bar — *no AC box is ticked
> before its probe(s) report WITNESSED* — **AC-1**'s shipped test read the env var
> directly, witnessing the marker **arriving**, never its second conjunct that it
> **changes the database**; its declared **probe 1b had never run**. **AC-2**'s claim
> was an **exemption**, not a witness. ✅ **Cray ruled route (ก), typed:** write the
> tests the ACs specify rather than relax the ACs. #1394 did — probes 1b/1c/2 all
> WITNESSED. 🔴 **Probe 2 refuted the PLAN's own prediction** (it reddens the
> inequality, not the equality); that equality is a **co-moving agreement claim** and
> is exempted with that reason.
>
> 🔴 **The battery definitions were in `/tmp`, tracked nowhere.** PLAN-0120 Step 5
> demanded they travel with the report *citing PLAN-0117 for skipping it* — then it
> was skipped again. The s278 audit worked only because four `/tmp` files survived.
> **Four independent specialist reviews of an unrelated question each escalated this
> unprompted, ahead of what they were asked.** #1395 commits seven definitions to
> `tests/batteries/` with the convention, and PLAN-0120 gains a machine-addressable
> `**Batteries:**` line.
>
> 🔴 **Committing them exposed a gap in THIS session's own ticks.** #1396: AC-7's
> artifact (a) and AC-8's cross-file pin sat in **no** battery's `claim_sources`, and
> declared **probe 8c had never run** — so `PROBE-COVERAGE: COMPLETE` was computed over
> a denominator excluding them, and both were ticked on that reading hours earlier.
> Closed by two new batteries rather than by unticking, route (ก) again. **Ledger 0 → 8
> of 11**, now evidenced.
>
> ✅ **The join is mechanised (#1397).** `check_ac_consistency` **Check 3** fails a
> ticked AC whose artifact module is in no battery, fails a PLAN that binds ticks to
> probes and names none, and treats an empty `**Batteries:**` glob as an **error, never
> a skip**. Module-level by measurement: a probe-id join recovers **37%** and would
> raise 12 false alarms of 19. Two of its own false positives were measured and fixed
> before shipping, and are now regression tests. Witnessed by six probes on its own
> tests — including the **over-fire** direction, since a guard that accuses correct
> work gets silenced too.
>
> ✅ **#1398 homed what had no home:** R6 gains where a rotation payload comes from
> (`git show HEAD:`, not a subagent's paste) and a pre-append present-once check with a
> positive control — the second a **precedence correction**, since the derived skill
> already carried it and its canonical did not. Lesson **#0047** gains the addendum
> with its ADR-0038 tally. A proposed third finding was **dropped on the evidence**.

## Rotated this reconcile — session 282 (2026-09-06)

### Rotated at the s282 reconcile — the session-279 Current-Focus block [on the R2 headroom rule, NOT a cap overage. STATUS opened at **59,608 B** with only **5,928 B** under the 64 KB R1 ceiling, and admitting the s282 block to a four-wide window would have left roughly 2 KB — which the next reconcile would breach. The window lands at **THREE** again (280, 281, 282); this is the **fourth consecutive** reconcile to land there on the headroom rule. 🔴 **Caller-measured, and it CORRECTS the drafting estimate:** the block is **3,815 B** as carved from `git show HEAD:docs/STATUS.md` — **UNDER** the 4,096 B per-block cap, not over it as the scribe's line-count estimate suggested. It rotated on headroom alone. Carved from git rather than from the subagent's return, per this file's own rule and because that return arrived **HTML-escaped**, which would have corrupted the archive silently. ✅ STATUS **59,608 → 61,595 B** (3,941 B of headroom left — the next reconcile must rotate again).]

> **Session 279, 2026-09-05 (`3a9e043` → `af0eca0`) — FOUR PRs
> ([#1399](https://github.com/CrayJThiemsert/vero-lite/pull/1399)–[#1402](https://github.com/CrayJThiemsert/vero-lite/pull/1402)),
> all merged, 0 open, tree clean, MS-S1 never contacted. What it established: a
> probe pair can report green for a mutation that reached disk and changed
> behaviour — six PLAN premises fell here, every one to a measurement or a
> guard, none to review.**
>
> ✅ **PLAN-0121 executed end to end (Steps 0–5): a cut-off pytest child is no
> longer published as `GREEN`.** Before, `body=GREEN` / `fixture=NO-TESTS` with a
> reason **byte-identical to a real green**; after, `body=ABORTED` /
> `fixture=ABORTED`, carrying `rc=75`, the child's own last line, and **which of
> two defence layers decided**. Two committed batteries —
> `plan-0121-abort-legibility.json` (28 claims, 14 probes, 14 exemptions,
> `GAPS: 0`, 26 s) and `plan-0121-scenario-cli.json` (20 claims, 2 probes, 18
> exemptions, `GAPS: 0`, 4 s) — **16 probes WITNESSED, ledger 0 → 8 of 8**, every
> box carrying the probe that earned it. Suite **4876 → 4901**, reconciled
> exactly (+21 contention, +3 scenario, +1 a rebuilt control), no new skip.
>
> ✅ **The four PRs are the layers:** #1399 made the classifier read a no-verdict
> exit as an infrastructure event (Steps 0–1); **#1400 made the runner return a
> `RunRecord`**, so an abort's cause survives the call that produced it (Step 2);
> #1401 built the out-of-band oracle a cut-off child needs (Steps 3–4); #1402
> pinned the probes (Step 5). PLAN-0121's ledger is **8 of 8**, its `Status:`
> still `Draft` — the closeout `git mv` has not run.
>
> 🔴 **AC-1's own probe P1 COULD NOT REDDEN.** Both defence layers fire on the
> same body shape, so disabling one left the other returning the identical
> `ABORTED` — P1 would have published a green for a mutation that reached disk.
> Fixed on both sides: each layer now leads its reason with a distinct clause,
> AC-1's read became a **conjunction**, and AC-5 gained probe **P9**.
>
> 🔴 **Five more premises refuted by measurement:** the s277 green control was
> **not** in the preserved copy (recovered from `/tmp` in time); one fixture
> stdout is **reconstructed**, not raw; the pytest runtime is **9.0.3**, not the
> 8.3 pin; a nonexistent node id gives **`rc=4`**, not `rc=5`; and
> `expect: ABORTED` does **not** reach `PROBE-BATTERY: PASS`, because coverage
> still reports a gap.
>
> 🔴 **Two more caught by RUNNING, not reading.** Probe **P11 reported
> `CRASHED`** — an `IndexError` in the test's own diagnostic print, raised before
> the assertion could run. And **`check_ac_consistency` Check 3 refused an AC
> tick twice**: first correctly (the positive control lived in a module no
> battery's `claim_sources` covers, so the coverage report excluded its own
> control), then again on the correction note, which still named the old module
> inside the segment the guard scans. AC-7's gate at true CI scope: **seven
> zeros**; `node --check` recorded **NOT-RUN** (node absent from this image),
> never counted as a pass.
>
> ✅ **Cray ruled, typed 2026-09-05:** `CLAUDE.md` §7 wins over the harness's
> `Co-Authored-By` instruction — no trailer; AI assistance is noted in the
> commit body.
>
> ⚠️ **One unexplained artifact, recorded not absorbed:** the first
> `detect-secrets --all-files` returned `rc=1 "files were modified"` while
> `.secrets.baseline` stayed byte-identical to HEAD (`git hash-object` 6b2779b
> both times); two re-runs returned 0. Not reproduced; the committed state is
> clean. ⚠️ `end-of-file-fixer` rewrote three committed junit captures on their
> first commit — the repo's own tooling editing a closed-incident pin. Now
> excluded via `^tests/.*/fixtures/`.

🔴 **THIS (s279) reconcile rotates the session-274-275 block** on **BOTH** rules — a fourth block entered a three-wide window **and** it measured **7,577 B, 85% over** the 4,096 B per-block cap (caller-measured); the new block was written under the cap at **~3.9 KB**. 🔴 **This ledger's own s269-273 and s274-275 entries rotate with it**, probed against the archive with a positive control: the **s269-273** entry is **present verbatim** (it travelled inside the s275 slice) and is **not** re-appended; the **s274-275** entry is **absent** — only the archive's `## Rotated at the session-275 reconcile` header records it — so it travels to the caller. ⚠️ **No byte delta measured — no shell; the caller owes `wc -c` + append + verify-by-DELTA.**

## Rotated this reconcile — sessions 283 + 284 (2026-09-07)

### Rotated at the s284 reconcile — the session-280 Current-Focus block [on the R2 headroom rule, NOT a cap overage: the block is **3,690 B** as carved, under the 4,096 B per-block cap. STATUS opened at **63,219 B** — only **2,317 B** under the 64 KB R1 ceiling — and admitting the new s283-284 block to a four-wide window would have breached it. The window lands at **THREE** again (281, 282, 283-284); the **fifth consecutive** reconcile to land there on headroom. 🔴 **This block's own Current-Focus rotation-ledger entry IS appended here — it was probed and found ABSENT from all five CF archives**, against a positive control that found a known entry (`reconcile rotates the session-274-275`, count 1) and a fabricated needle that found none. That **BREAKS the run of three** consecutive reconciles (s280, s281, s282) whose rotating entry was already archived — the prior is informative, never a substitute for the probe. ⚠️ **Two instrument traps caught by controls at s284**, recorded so the next rotation avoids them: the CF slice does **not** run to the section end — the rotation-ledger line sits between the last block and `## Prior focus` and must STAY, and taking the slice to the section end measured **7,668 B** against the correct **3,691 B**; and a ledger-entry probe carrying the `🔴 **THIS (sNNN) ` prefix returned 0 **including on its positive control**, which is what exposed the needle rather than the archive as wrong. ✅ Caller-measured: STATUS **63,219 → 61,764 B** (3,772 B of headroom left — the next reconcile must rotate again). Carved from `git show HEAD:docs/STATUS.md`, never from the subagent's return.]

> **Session 280, 2026-09-05..06 (`af0eca0` → `7138cc0`) — FOUR PRs
> ([#1404](https://github.com/CrayJThiemsert/vero-lite/pull/1404)–[#1407](https://github.com/CrayJThiemsert/vero-lite/pull/1407)),
> all merged, 0 open, tree clean. What it established: the Stop hook's proceed
> arm is **~57% defective over 47 days** — counted, not felt — and the harness
> grading its replacement was broken two ways, both flattering the incumbent.**
>
> ✅ **PLAN-0122 drafted (#1404), ratified (#1405), Steps 0+1 merged
> (#1406/#1407)** — 12 ACs, 7 SDs, six typed by Cray at merge. Step 0 froze the
> evidence into `benchmarks/stop_classifier/s280/` (13 files) before it expired;
> the raw 294-envelope jsonl stays gitignored, sha256 recorded. The ledger — 117
> proceed-arm fires, ~57% defective — was trusted only after its instrument
> passed controls (strict 150 < loose 156; a positive control found all 28
> goal-gate directives).
>
> 🔴 **Two harness defects confirmed WITH controls, not asserted.** **D-1, label
> leak:** the harness put `{case_id}.jsonl` in the prompt, grading the incumbent
> on a leaked label — AC-1 prints `cases=79 leak_pre=79 leak_post=0`, `leak_pre`
> being the control proving the detector can see a leak. **D-2, transport
> divergence:** the harness sent a body production never sends, penalising the
> challengers — AC-2 prints `prod_options={'temperature': 0}`, `pre=75 post=3`,
> `prod_t=1.02 harness_t=1.00`.
>
> ✅ **Same model, before → after the repair, nothing else changed: 16/49 (33%),
> 0/18 proceed, 10 calls lost → 42/49 (86%), 0 unsafe, 49/49 delivered**, from a
> six-arm A/B over 294 live MS-S1 calls; both degenerate bots lose (AC-3
> `slim5=42/49 unsafe=0 | always_pause=22/49 unsafe=0 | always_proceed=22/49
> unsafe=27`), and a bigger model, a raised `num_predict` and an output
> word-filter were ruled OUT **on measurement**. ⚠️ **The 86% is IN-SAMPLE and
> never travels without that:** one pass at temperature 0, no variance estimate,
> SLIM→SLIM5 tuned on the same 49 cases (PLAN-0122 §9).
>
> 🔴 **Three corrections to the session's OWN figures — the load-bearing part.**
> (i) The scorer counted timeouts and unparseable replies as `delivered`,
> inflating FULL and SLIM4 by one case each — caught only because Step 1.4 makes
> the frozen file meet the already-reported figures, which is its purpose.
> (ii) `SLIM3 unsafe` was reported as 2 all session; the repaired scorer says
> **4** and was right — it counts *proceed on a dispatch-gold case* as a hard
> fail, documented since s56; corrected visibly in the PR body, and it changes
> no ruling (SD-3 was decided on SLIM5). (iii) Two probes (P2b, P2c) MISFIRED on
> first declaration — the mutation reddened a neighbouring line, not the
> declared claim; the driver refused to credit them and **the prediction was
> fixed, never the assertion**.
>
> **Evidence, not restated** — read the PR bodies and the frozen dir: battery
> `tests/batteries/plan-0122-step1-harness.json` claims 48, RED 8, exempted 40,
> **GAPS 0**, `PROBE-BATTERY: PASS`; `ruff` + `ruff format --check` (725 files)
> + `check_ac_consistency` (86 ACs / 10 PLANs) clean; CI `success` on both heads.
>
> 🔴 **PLAN-0122 is NOT done — Step 2 has not started because SD-1 is RESOLVED
> BY ENTAILMENT, NOT TYPED.** It follows from SD-2 + SD-3 as *(a) ship SLIM5
> byte-identical, Stop-only, sha-pinned, conditioned on AC-7 passing first* —
> but Cray never typed "SD-1", and anything narrower changes Steps 2 **and** 4.
> ⚠️ Step 2.3 must also edit `.claude/hooks/*`, which the auto-mode classifier
> (G20) is expected to **DENY**; the PLAN forbids routing around it.

🔴 **THIS (s280) reconcile rotates the session-276-277 block** (caller-measured **3,660 B**, under the 4,096 B cap) on the **headroom rule**, not a cap overage: STATUS opened at **59,218 B** — **6,318 B** under R1 — and a fourth block would have left ~2.2 KB, the same rule the s279 reconcile rotated on at 4,041 B. The window lands at **THREE** again (278, 279, 280), inside R2's `≤ 4 sessions / ≤ 8 blocks` maximum — **deliberate; no block was lost**; the s280 block was written under the cap from the start. 🔴 **This ledger's own s276-277 entry is NOT re-appended — probed and found ALREADY in the archive verbatim** (count 1, against a positive control), having travelled inside the s278 rotation, so R4's move duty is discharged and a second copy would duplicate a move-only archive. ✅ **Caller-measured:** STATUS **59,218 → 57,638 B**; CF archive **185,073 → 189,622 B (+4,549)**, the block **3,659 B** carved from `git show HEAD:`, present-once verified by **DELTA** (pre=0 post=1) with absence-from-STATUS checked separately. ⚠️ **CF archive headroom is now 6,986 B under R4's 196,608 B split trigger — the next reconcile or two must open `2026-h1e-current-focus.md`.**

## Rotated this reconcile — session 285 (2026-09-08)

### Rotated at the s285 reconcile — the session-281 Current-Focus block [on the R2 headroom rule, not a cap overage: the block is **3,128 B** as carved, under the 4,096 B per-block cap — STATUS's own ledger line says **3,130 B**, which counts the blank separator line the carve strips; same block, two conventions, recorded rather than silently reconciled (the s281 append documents the identical 3,269/3,270 B pair). STATUS opened at **62,509 B**, only **3,027 B** under R1's 65,536 B ceiling, and the CF window had a free slot — the byte ceiling forced the prune, not the block count. The window lands at THREE again (282, 283-284, 285).]

> **Session 281, 2026-09-06 (`7138cc0` → `fc01cd0`) — THREE PRs
> ([#1408](https://github.com/CrayJThiemsert/vero-lite/pull/1408)–[#1410](https://github.com/CrayJThiemsert/vero-lite/pull/1410)),
> all merged, 0 open, tree clean. What it established: SLIM5 — the prompt s280
> measured at 42/49 IN-SAMPLE and shipped — was REFUTED on data it had never
> seen and Cray reverted it. The arm running today is the INCUMBENT full prompt:
> a success of the method, a failure of the candidate.**
>
> ✅ **Step 2 shipped SLIM5 (#1409)** — `STOP_SYSTEM_PROMPT` = the measured
> bytes, sha-pinned; `_build_system_prompt(..., event=None)` returned SLIM5 on
> `Stop`, legacy otherwise. AC-4/5/6 ticked; battery `claims 189 · RED 12 ·
> exempted 177 · GAPS 0 · PASS`.
>
> 🔴 **Step 3 (#1410) measured it OUT-OF-SAMPLE and it lost.** 30 held-out
> `gold.yaml` cases, one pass per arm, `gpt-oss:20b` on MS-S1 under a typed §8
> go, warm call excluded, **neither arm re-run after its score was seen**:
> **FULL 29/30 correct · 0 unsafe · 29/30 delivered** vs **SLIM5 28/30 · 2
> unsafe · 30/30 delivered** (`pause-destructive-db`, `pause-plan-status-flip`);
> controls `always-pause` 19/30 and `always-proceed` 8/30 both reproduced their
> pre-committed values. AC-7's read was fixed BEFORE the run and **two of three
> conjuncts FAILED** — `28 > 19` true, `unsafe == 0` FALSE, `28 >= 29` FALSE.
> **AC-7 is NOT ticked.**
>
> 🔴 **The in-sample result INVERTED.** SLIM5 led **42/49 to 16/49 on the 49
> cases it was TUNED against**; on 30 unseen ones the incumbent is ahead on
> correctness and strictly better on safety, and both SLIM5 misses run the
> dangerous way — `proceed` on a should-pause case, one a destructive DB
> operation. PLAN-0122 §9 named the risk. Not argued away: SLIM5 delivered 30/30
> to FULL's 29/30, but under the PARITY ruling a lost call is a pause, so FULL's
> timeout costs a turn, never safety — and its 29/30 is that arm's FIRST honest
> score, on the repaired harness, not the void `19/20`.
>
> ✅ **The revert (Cray, typed).** `classify()` no longer passes the event; every
> arm gets the legacy prompt. **KEPT:** harness repair, sha-pinned constant,
> AC-5/AC-6 tests, battery, the `event` seam. **ADDED:**
> `test_stop_arm_is_not_slim5_until_ac7_passes` (probe P4d redefined to witness
> it); battery after: `claims 191 · RED 12 · exempted 179 · GAPS 0 · PASS`.
>
> ⚠️ **A trap for whoever is next:** `.claude/autonomy-triggers.md` is fed
> VERBATIM into the legacy prompt, so editing it — even only to annotate the
> void `19/20` it still quotes — changes the FULL prompt and **voids the 29/30
> that justifies today's configuration**. Never documentation-only.
>
> ⚠️ Two doc defects the `goal-evaluator` caught, both fixed in #1410: the typed
> revert lived **in code comments only** while the PLAN still framed it as open,
> and the s280 README still said *"No held-out numbers"* in the directory that
> now holds them. Gate on `fc01cd0` all clean; **pytest 4917 passed, 8 skipped**;
> CI `gate: pass` on both heads. Detail: `docs/plans/0122-*.md` Step 3.

🔴 **THIS (s281) reconcile rotates the session-278 block** (caller-measured **3,270 B**, under the 4,096 B cap) on the **headroom rule**, not a cap overage: STATUS opened at **57,638 B**, **7,898 B** under R1, and a fourth block would have left ~4 KB. The window lands at **THREE** again (279, 280, 281) — deliberate; no block was lost. 🔴 **The chain OPENS A NEW LETTER — the block goes to `2026-h1e-current-focus.md` (NEW FILE)**: `h1d` is CLOSED at 189,622 B, since +3,270 B would reach **192,892 B**, essentially where `h1c` closed (**193,007 B**). 🔴 **This ledger's own s278 entry is NOT re-appended — probed and found ALREADY in `2026-h1d-current-focus.md` verbatim** (count 1, against a positive control run on h1d because an empty new file cannot control anything), having travelled inside the s278 rotation's own slice, so R4's move duty is discharged. **Second consecutive reconcile this shape has fired** — treat a rotating block's ledger entry as PROBABLY already archived and probe before appending, never after. ✅ **Caller-measured:** STATUS **57,638 → 59,342 B**; `h1e` created at **5,968 B** (the block 3,269 B as carved — the 3,270 B above counts the blank separator line — plus its header); `h1d` **CLOSED** at **190,011 B** after its own banner edit, per the s227 precedent that a closing chain file rewrites its own header. Present-once verified by **DELTA** (pre=0 post=1), absence-from-STATUS checked separately.

## Rotated this reconcile — session 286 (2026-09-08)

### Rotated at the s286 reconcile — the session-282 Current-Focus block [on the R2 headroom rule, not a cap overage: the block is **3,733 B** as carved (54 lines), under the 4,096 B per-block cap. STATUS opened at **61,320 B**, only **4,216 B** under R1's 65,536 B ceiling, and the CF window had a free slot — the byte ceiling forced the prune, not the block count. The window lands at THREE again (283-284, 285, 286), the fifth consecutive reconcile of this shape.]

> **Session 282, 2026-09-06 (`fc01cd0` → `22fc98f`) — FIVE PRs
> ([#1412](https://github.com/CrayJThiemsert/vero-lite/pull/1412)–[#1416](https://github.com/CrayJThiemsert/vero-lite/pull/1416)),
> all merged, 0 open, tree clean. What it established: three PLAN-0122 artifacts
> landed (AC-8/9/10) and **not one is ticked**; the first to run in production
> exposed a 40-day blind spot, and an offline audit CLEARED s281's held-out run.**
>
> ✅ **PLAN-0121 archived (#1412).** The closeout `git mv` broke **three**
> pre-archive pointers and **R8 caught all three** — two re-pointed, the third
> deliberately **not** (a gold-corpus line whose text IS the fixture); plus a
> `-2` battery-header error wrong **as committed** since s279. ✅ **Lesson #0060
> + a guard (#1413):** R8 now fails on an **unregistered benchmark corpus**,
> detecting corpora by **CONTENT** (`transcript_turns`), not filename, and
> **failing closed** on zero.
>
> 🔴 **AC-10's audit (#1414), `tools/hook_copies_audit.py`: `worktrees=19
> distinct_classifier_hashes=6 distinct_stop_hook_hashes=8` — not ONE of the 19
> is on main's bytes**, and main's version exists in a single copy. ⚠️ `git
> worktree list` reports only **6 of 19** (UNC gitdirs read `prunable`), so the
> audit enumerates by **filesystem**, never by git.
>
> ✅ **AC-8 + AC-9 (#1415)** — the SD-4 decision log (one line per classifier
> verdict, all five arms) and the AC-9 floor pin `demoted=1/117`; plus an autouse
> **socket guard** in `tests/conftest.py`, after the suite was measured writing
> **25 lines into production state**. 🔴 **#1416 CORRECTED it the same session:**
> the log was built from AC-8's pass read **without reading §4.3**, which
> specifies the artifact in full — wrong path, wrong env var, wrong field names,
> missing `event` / `latency_s` / `prompt_sha8`, and a **boolean** where the spec
> has a four-value `transport` enum. **A pass read is not a spec.**
>
> 🔴 **The log's first production lines showed the Stop classifier failing on
> MS-S1 in THREE shapes** — HTTP 500 (Ollama's harmony parser rejects a `python`
> tool call the model emits), timeout, and **HTTP 200 with an empty body**
> (`malformed`). Read-only server-log inspection measured **286 of 1,756
> `/api/chat` calls returning 500 since 2026-08-28** — pre-existing and
> previously invisible. ✅ **An offline audit of `s281-heldout.jsonl` CLEARED the
> Step 3 measurement:** exactly **1 of 60** live calls was lost and scored
> `invalid`, never silently credited — FULL answered 29 and got **all 29 right**,
> SLIM5 answered 30 and got **2 dangerously wrong**. **The revert stands.**
>
> ✅ **Cray ruled, typed:** (1) the 19 stale worktrees — **record as abandoned,
> leave in place**, no worktree file touched; (2) the MS-S1 classifier failures —
> **change nothing now**, let the log collect **14 days**, then decide; (3) the
> registry repair (the void `19/20` + SD-7's homeless `C6`/`C7`) stays **ONE**
> follow-up PLAN, **ONE** live re-measurement, **after** AC-12's window closes.
>
> 🔴 **AC-8/9/10 all have their artifacts on `main` and NONE is ticked** —
> PLAN-0122 was not edited at all this session (`Accepted`, so the closeout edit
> may be G1-gated; it was not attempted). Same shape as the s274 and s277 rows.
> ⚠️ Open, none blocking: AC-10's closeout record (19 names + Cray's disposition)
> is unwritten, and **`tools/stop_classifier_ledger.py` — AC-12's instrument —
> DOES NOT EXIST**; it must be rebuilt **inside** the 14-day window, not
> discovered missing on day 14. **Proposed, not ruled:** the AC-12 clock starts
> at #1416's merge (`22fc98f`), not #1415 (`ff656a8`) — that is where the file
> AC-12 reads begins.

🔴 **THIS (s282) reconcile rotates the session-279 block** — 59 lines, **est. ~4.4 KB** (no shell; the caller owes `wc -c`), i.e. likely **over** the 4,096 B per-block cap as retained — and on the **headroom rule**: STATUS opened at **59,608 B**, only **5,928 B** under R1, and keeping a fourth block would have left ~2 KB. The window lands at **THREE** again (280, 281, 282) — deliberate, the **fourth consecutive** reconcile of this shape; no block was lost. Destination is the OPEN chain file **`2026-h1e-current-focus.md`** (5,968 B, opened at s281), nowhere near R4's 196,608 B split trigger. 🔴 **This ledger's own s279 entry travels with it — PROBE BEFORE APPENDING**: the s281 and s280 reconciles both found their rotating entry ALREADY archived, so probe with a positive control; a false negative appends a duplicate. ⚠️ **No byte delta measured — no shell; the caller owes `wc -c` + append + verify-by-DELTA.**

### Rotated at the s287 reconcile — the session-283-284 Current-Focus block [on the R2 headroom rule, not a cap overage: the block is **3,041 B** as carved, well under the 4,096 B per-block cap. The scribe was instructed NOT to rotate — the CF window had a free slot and went 3 → 4, exactly R2's window — so this prune is the **caller's**, forced by bytes alone: STATUS closed the reconcile at **65,146 B**, only **390 B** under R1's 65,536 B ceiling, which would have left the next session unable to add anything at all. The window lands at THREE again (285, 286, 287) — the sixth consecutive reconcile of this shape. 🔴 **This block's own Current-Focus rotation-ledger entry (s284) travels with it and was probed ABSENT** from this archive against a positive control that found known archived content (`Session 282` = 1, `THIS (s282)` = 1) and a fabricated needle that found none — a genuine first append. ⚠️ **One instrument bug caught before it mattered:** the neighbour-bleed probe's regex was over-escaped inside a raw string and read **0** block headers in a slice that starts with one; the instrument was wrong, not the slice, and it was repaired rather than the assertion relaxed. Carved from the live tree for the block (unchanged by this reconcile) and from `git show HEAD:docs/STATUS.md` for the RD row (already removed from the tree by the scribe). ✅ **Caller-measured:** STATUS **65,146 → 61,515 B** on the rotation alone, then **62,270 B** after two Active-TODO figure corrections landed in the same commit — **3,266 B** of headroom, up from the 390 B the reconcile would otherwise have shipped. This archive's own size is measured by the caller after the append and deliberately NOT written here: a self-referential byte figure changes the file it describes.]

> **Session 283–284, 2026-09-06..07 (`22fc98f` → `006ffd0`) — FOUR PRs merged
> ([#1418](https://github.com/CrayJThiemsert/vero-lite/pull/1418)–[#1421](https://github.com/CrayJThiemsert/vero-lite/pull/1421))
> plus [#1422](https://github.com/CrayJThiemsert/vero-lite/pull/1422) — **all
> merged**. What it established: PLAN-0122 went **6/12 → 10/12** on evidence, a
> stale line in the PLAN itself was refuted **in code**, and **AC-12's 14-day
> window is running while measuring nothing.****
>
> ✅ **s283 (#1418–#1421).** Banked the Step-4 probe battery s282 had run but
> **never committed** — the artifact, not the memory of it. Fixed a **Check 3
> false positive**: it demanded a *claimless tool* appear in a denominator **of
> claims**, which no claimless tool can satisfy. Ticked **AC-8/AC-9/AC-10** with
> their §11 closeout records. Also landed **Lesson #0061** (an AC is not a spec)
> and the STATUS TODO for the uninstrumented PreToolUse arm.
>
> ✅ **s284 (#1422 — `fff851c` → `55d7ec8`, CI `success`, run 34123293869).**
> Ticked **AC-1/AC-2/AC-3** on a battery re-run — **8/8 WITNESSED,
> `PROBE-COVERAGE COMPLETE`, GAPS 0** — and **AC-11** on a clean gate: `ruff` 0 ·
> `format` 0 · `mypy` 0 · `pytest` 0 with **4948 passed / 8 skipped** ·
> `check_ac_consistency` clean. That clean reading is trustworthy because the run
> carried a **positive control**: with the Step-4 battery hidden, the checker
> printed **exactly the 5 predicted gaps** — an instrument shown able to fail
> before its pass was believed.
>
> 🔴 **A stale Status line in PLAN-0122 contradicted the PLAN's own Step 3.** It
> claimed the live Stop arm runs the unvalidated **SLIM5** prompt and that
> reverting was an open Cray decision. **Both false since s281** — verified in
> code, not recalled: `_sonnet_classifier.py:1009-1010` passes no `event=`, so
> `:397` resolves to the legacy/FULL builder, pinned by
> `tests/handoffs/test_sonnet_classifier.py:407`. It had already misread one
> session's orientation before being caught: a PLAN header line is a **claim**,
> not context.
>
> 🔴 **AC-12's window is collecting nothing to measure — the blocker is DATA, not
> code.** `.claude/state/stop-classifier-log.jsonl` holds **48 lines over ~19
> hours**, `"decision":"proceed"` appears **0 times**, and **39 of 48 are
> transport failures**. AC-12's pass read needs `post=k/n` with `p < 20`, so
> **n = 0**. Two compounding causes: the MS-S1 transport failing, and the
> reverted FULL prompt being pause-heavy by nature so `proceed` rarely fires.
> Structurally the log records only `decision`/`emitted`, so it **cannot** supply
> AC-12's defective-class judgement (INVERSION / PERMISSION-FRAME /
> ROLE-CONFUSION) at all — it is §4.3's durability backstop, **not** a substitute
> input for AC-12, which reads main-session transcripts. So writing
> `tools/stop_classifier_ledger.py` today would build an instrument with nothing
> to read. **Cray's call:** extend the window, change the spec, or stop the clock.

🔴 **THIS (s284) reconcile rotates the session-280 block** (caller-measured **3,691 B**, under the 4,096 B cap) on the **headroom rule**, not a cap overage: STATUS opened at **63,219 B**, only **2,317 B** under R1's 65,536 B, so a fourth block was unaffordable. The window lands at **THREE** again (281, 282, 283-284) — deliberate; no block was lost. Destination `2026-h1e-current-focus.md` (**11,612 B**; R4's split trigger is 196,608 B). 🔴 **This ledger's own s280 entry travels with the block and was probed NOT YET ARCHIVED** — controlled instrument (positive control found a known entry = 1, fabricated needle = 0) — so it is a **genuine first append**, breaking the run of three reconciles that found theirs already archived. ⚠️ **No byte delta measured — no shell; the caller owes `wc -c` + append + verify-by-DELTA.**

### Rotated at the s288 reconcile — the session-285 AND session-286 Current-Focus blocks [on the R2 headroom rule, not a cap overage: **2,810 B** and **2,397 B** as carved, both well under the 4,096 B per-block cap. 🔴 **TWO blocks moved, not one, and the window lands at TWO (287, 288) — a first, forced by bytes alone.** The scribe was told not to rotate, so this prune is the caller's entirely. Rotating only s285 would have closed STATUS at **~64,990 B**, roughly **546 B** under R1's 65,536 B ceiling — and the s287 reconcile's own ledger note warned that shipping that thin “would have left the next session unable to add anything at all”. s288 also adds two PERMANENT Active-TODO rows (the Step-4b `/tmp` rehome and the G2-gated goal-template PLAN) whose only tracked home is STATUS, so the bytes had to come from the Current-Focus window. 🔴 **Both blocks' own Current-Focus rotation-ledger entries travel with them** (s285 **746 B**, s286 **1,149 B**), probed SEPARATELY and found ABSENT from this archive against a positive control that found known archived content (`Session 283–284` = 1) — genuine first appends. ⚠️ **The s286 entry measured 1,149 B, OVER the ~900 B per-entry cap Cray set at s267** — rotating it clears a live cap breach as well as bytes; the breach is recorded here rather than silently carried. ⚠️ **One instrument error caught before it mattered:** a post-write assertion counting `**THIS (s285)` across the whole file read **1** and looked like a failed removal — the *Recent-Decisions* ledger legitimately keeps its own s285 entry and only the *Current-Focus* ledger loses it. The assertion was WRONG-SCOPED, not the slice; it was re-scoped to each ledger line, and it was visible only because the check prints the values it measured rather than a bare PASS/FAIL. All four slices carved from `git show HEAD:docs/STATUS.md`, not from the scribe's return. This archive's own size is measured by the caller after the append and deliberately NOT written here: a self-referential byte figure changes the file it describes.]

> **Session 286, 2026-09-08 (`0cef7ed` → `0bcc2ae`) — SIX PRs
> ([#1429](https://github.com/CrayJThiemsert/vero-lite/pull/1429)–[#1434](https://github.com/CrayJThiemsert/vero-lite/pull/1434)),
> all merged, 0 open, tree clean. **PLAN-0119 ratified `Accepted` (Cray,
> typed); Steps 1–2 complete, Step 3 part 1 landed — and the PLAN's own §3
> inventory was corrected `was an error` mid-session.**
>
> ✅ **Steps 1–2 (#1429, #1430).** The five-class workload taxonomy (G/S/J/N/A),
> a call-site inventory and a 9-question checklist now live in
> `docs/conventions/llm-workload-taxonomy.md`; its guard enumerates `.chat(`
> from the **tree** by AST walk, treating the artifact as the claim. The intake
> benchmark recorder keeps `load_duration_ns`, `prompt_eval_duration_ns` and
> the raw `thinking` string — what makes **OQ-1** answerable — plus
> `--num-predict` / `--think`.
>
> 🔴 **#1432 corrected §3's call-site inventory, `was an error`** (by the
> in-harness `plan-drafter`): it claimed 14 grep-verified `.chat(` sites and an
> AST re-measurement also found 14 — **but not the same 14**, listing
> `action_step.py` (**zero** `.chat(`) and omitting `gate_advisory.py:160`
> (one). ⚠️ **SD-A is Cray's:** §3 now runs to 15 rows under a heading saying 14.
>
> ✅ **Step 3 part 1 (#1433) — the per-workload budget seam.** `Workload` is
> declared **at construction with no default**, the chokepoint derives
> `num_predict` from it, 8 sites migrated. ✅ **Cray ruled, typed,** a case the
> PLAN never anticipated: two sites that **never generate** were split into a
> second client type (`OllamaAdminClient` / `OllamaClient`) rather than a sixth
> class. ✅ **#1434** rehomed the findings — two instrument-failure shapes to
> Lesson #0056, a vacuity shape to #0058, a failing battery to Active TODOs.
>
> ✅ **Evidence:** three batteries — **36 claims, 32 RED, 4 exempted in writing,
> GAPS 0 on all three**; suite 4958 → **4974 passed, 8 skipped**, each delta
> exactly the tests its PR added; Step 3's pre-committed read `pre=8` →
> `post: missing=0, declared=6, admin_split=2`. **MS-S1 was never contacted.**
> 🔴 **AC-1/2/3/8/11 have evidence and NOT ONE is ticked** — a tick is a
> closure claim, so Cray's. 🔴 **Step 3 part 2 is HALF-BLOCKED:** AC-4/AC-5 need
> `load`/`prefill`/`num_ctx` numbers only Step 4b's LIVE §8-gated run can supply.

> **Session 285, 2026-09-07..08 (`006ffd0` → `0cef7ed`) — TWO PRs
> ([#1424](https://github.com/CrayJThiemsert/vero-lite/pull/1424),
> [#1425](https://github.com/CrayJThiemsert/vero-lite/pull/1425)), both merged, 0
> open, tree clean. **PLAN-0120 is 11 of 11 and ARCHIVED** — but two of the ACs it
> closed had to be reconciled to the code first, and Step 7 carried a §8 claim
> that was false when written and nearly fired.**
>
> ✅ **AC-9 closed through the REAL seam** — `tests/tools/test_probe_battery_guard.py`
> plus an eighth battery (`plan-0120-ac9-battery-child.json`): a real parent holds
> a real advisory lock on real Postgres, `_make_pytest_runner` spawns a real child
> on a DB-backed node → `outcome=ABORTED credited=False`, control
> `outcome=WITNESSED`; battery **PASS · 6 claims · 3 witnessed · GAPS 0**.
> PLAN-0121's `test_probe_battery_contention.py` does **not** cover it — that pins
> the classifier against **synthetic** shapes and binds no database. ✅ **AC-1's
> live WSLENV half:** `last_deterministic={"C1": "pass"}`, controlled three ways.
>
> 🔴 **Two AC texts were reconciled to the code, not merely ticked — both
> `superseded by new info`.** AC-9's probes named `tests/db_guard.py`, which holds
> **zero** `pytest.exit(` sites (control found 3 in `db_support.py:361`, so the
> zero is real absence); its `{NO-TESTS, GREEN}` read was overtaken when PLAN-0121
> landed `Outcome.ABORTED`. **AC-10** closed at true CI scope (seven commands, all
> exit `0`; `4951 passed, 8 skipped`) with its stale `4801 passed` baseline
> **corrected, not re-frozen** — that count has moved 4801 → 4948 → 4951, so the
> criterion reconciles on `K`, the skip count (unchanged at **8**), and records `N`.
>
> 🔴 **SD-3 ruled `was an error` (Cray, typed) — and it NEARLY FIRED.** Step 7's
> "(MS-S1 is not involved)" was false **when written**: `git log -S`, against a
> control needle returning zero commits, dates `_sonnet_classifier` into
> `stop_continuation.py` at **2026-05-24** and its MS-S1 backend at **2026-06-12**,
> while the PLAN was drafted **2026-09-03**. Live, `run_goal_gate` returned `None`
> — *fall through to the classifier* — so Step 7 obeyed verbatim would have hit
> MS-S1 with no typed §8 go. **A §8 "not a host-state action" claim must name the
> COMPONENT, never the containing hook.** **MS-S1 was NOT contacted this session.**
> Two deviations sit on their ACs: `node.exe` over WSL interop, and `run_goal_gate`
> driven directly rather than `stop_continuation.main`. ⚠️ Archival repathed three
> tracked references but left `gold_s280.yaml` naming the pre-archive path on
> purpose — rewriting a path inside a gold-set corpus would silently change what
> FULL's held-out 29/30 was scored on. Detail: `docs/plans/done/0120-*.md`.

🔴 **THIS (s286) reconcile rotates the session-282 block** (caller-measured **3,733 B** as carved, 54 lines, under the 4,096 B cap) on the **headroom rule**, not a cap overage: STATUS opened at **61,320 B**, only **4,216 B** under R1's 65,536 B, so a fourth block was unaffordable. The window lands at **THREE** again (283-284, 285, 286) — deliberate, the **fifth consecutive** reconcile of this shape; no block was lost. Destination `2026-h1e-current-focus.md` (**23,531 B**; R4's split trigger is 196,608 B). 🔴 **This ledger's own s282 entry travelled with the block; probed SEPARATELY from the RD ledger's s282 entry and found NOT yet archived — a genuine first append.** ✅ **Caller-measured:** STATUS **61,320 → 60,720 B**; `2026-h1e-current-focus.md` **23,531 → 28,733 B** (+5,202). 🔴 **The first probe's positive control read 0 and condemned the instrument** — it named the s285 block, which is still in STATUS's live window, not the archive; controls were re-derived FROM the archive (`Session 281` ×2, `THIS (s281)` ×1) before any zero was trusted. Present-in-archive (1) and absence-from-STATUS (0) checked SEPARATELY.

🔴 **THIS (s285) reconcile rotates the session-281 block** (caller-measured **3,130 B**, under the 4,096 B cap) on the **headroom rule**, not a cap overage: STATUS opened at **62,509 B**, only **3,027 B** under R1's 65,536 B, so a fourth block would have left ~27 B. The window lands at **THREE** again (282, 283-284, 285) — deliberate; no block was lost. Destination `2026-h1e-current-focus.md` (R4's split trigger is 196,608 B). 🔴 **This ledger's own s281 entry travels with the block — probe it with a positive control and SEPARATELY from the RD ledger's s281 entry** (s281 measured that the two ledgers' entries do not share a fate). ⚠️ **No byte delta measured — no shell; the caller owes `wc -c` + append + verify-by-DELTA.**

### Rotated at the s290 reconcile — the session-287 AND session-288 Current-Focus blocks [on the R2 **headroom** rule, not a cap overage: **2,335 B** and **2,267 B** as carved, both well under the 4,096 B cap. STATUS opened at **63,704 B**, only **1,832 B** under R1's 65,536 B, and TWO sessions had to land (s289 and s290), so neither old block was affordable. The window lands at **TWO** again (289, 290) — the same shape s289 was forced into; no block was lost. Both blocks carved from `git show HEAD:docs/STATUS.md`, not from a scribe's return. 🔴 **Also rotated: the Current-Focus ledger's OWN s287 (**967 B**) and s288 (**888 B**) entries**, which travel with their blocks; probed SEPARATELY from the Recent-Decisions ledger's entries and found ABSENT here against a positive control that found known archived content (`THIS (s286) reconcile` = 1). The Recent-Decisions ledger dropped NOTHING this reconcile — measured, not assumed. 🔴 **The first attempt at this append wrote the s288 entry TWICE and the R6 post battery caught it** (`present in archive: got=2 want=1`): the ledger is a single 2,230 B line, so a carve terminated on `\n\n` ran to end-of-line and the s287 carve swallowed the s288 entry after it — the archive was reverted and re-carved on consecutive `THIS (sNNN)` markers. This is why presence is asserted as a COUNT, never as a boolean. ✅ **Caller-measured:** STATUS **63,704 → 58,204 B**.]

> **Session 288, 2026-09-09 (`ca0407d` → `8bdae71`) — FIVE PRs
> ([#1440](https://github.com/CrayJThiemsert/vero-lite/pull/1440)–[#1444](https://github.com/CrayJThiemsert/vero-lite/pull/1444)),
> all merged, 0 open, tree clean. **The spine was TRUTH — two tracked artifacts
> (a published README, ADR-0032's Context) re-grounded against what they
> describe, then guards built so the class cannot recur silently.**
>
> 🔴 **A tracked artifact can describe a world three weeks gone, and nothing
> catches it.** #1440: the published fleet README named *discharged* gates in
> the present tense, and a cloud dispatch had planned three work items on that
> text. Two mechanism claims corrected `was an error` — **G1 matches
> `docs/adr/` ONLY**; **G2 fires only on a not-yet-existing numbered file**.
>
> 🔴 **A probe battery can be silently DEAD — 2 of 21 were.** #1443's
> `tools/check_battery_definitions.py` runs `always_run` at pre-commit: an
> anchor or claim key that stops resolving now **blocks the commit**. ✅ Every
> `tools/check_*.py` must also prove it still **accepts** a healthy tree — that
> rule accused **6 healthy of 21**, caught only because the number surprised us.
>
> ✅ **`run_query.py`'s two silent aggregate drops are REFUSED at the validator**
> (#1442, `_validate_aggregate_dimensions`) — **(a), RULED, typed**. ✅ **#1444:**
> `tools/tally.py` makes a breakdown account for its own input (`--expect` is a
> falsifier written *before* the reading); every subagent's `model:` is pinned.
>
> 🔴 **TEN instrument errors made and caught — all ten in ad-hoc work, ZERO in
> PLAN-governed work**, and **every catch came from numbers contradicting each
> other** (139≠140; 8≠2), never from reading more carefully. Sharpest: **a
> control must meet the SAME failure the claim does** — a 20-line windowed
> `sed | grep` missed the keys below it, its control passing only because that
> key sat *inside* the window. 🔴 **No `goal.json` was ever created, so the Stop
> gate never fired: §8 already carries these rules — the gap is the TRIGGER.**
>
> ⚠️ **PLAN-0119 Step 4b is RUNNING LIVE on MS-S1** under a typed §8 go — 5 of 9
> arms at handoff. **MS-S1 was contacted deliberately and only for Step 4b.**

> **Session 287, 2026-09-09 (`820e8ea` → `ca0407d`) — THREE PRs
> ([#1436](https://github.com/CrayJThiemsert/vero-lite/pull/1436)–[#1438](https://github.com/CrayJThiemsert/vero-lite/pull/1438)),
> all merged, 0 open, tree clean. **PLAN-0119 Steps 1–4 COMPLETE, 9 of 11 ACs
> ticked (Cray, typed) — and the pre-tick re-run caught two probe batteries
> that had been silently DEAD.**
>
> 🔴 **A battery that could not address the claim it named.** Re-running all
> six on the merged tree before any tick aborted **two** with a *definition
> error* — not a red probe. AC-1's: a `ruff format` reflow of the asserted
> literal (`stable_key` is built from those bytes). AC-2's: the claim key
> **and** probe R17's mutation anchor both still named
> `settings.llm_max_output_tokens`, which #1433 replaced — **the test was
> updated with the code, the battery was not**, so R17 had been a no-op whose
> green proved nothing since s286. **Batteries do not run in CI, and
> `check_ac_consistency` reports clean because it does not run them.** Only
> PLAN-0119's six were checked; **others may be dead now** — see Active TODOs.
>
> ✅ **Two Cray rulings, typed, on cases the PLAN never anticipated — each
> PRICED before it was argued.** (i) Unmeasured capacity terms carry provenance
> in the **type** (`Term[T]`: `value`/`measured`/`source`/`replaced_by`);
> counting them zero could not have closed **AC-4 at all** — the failing case
> it requires (qwen @2048 vs a 120 s timeout) *fits*, 15.0 s to spare, at
> `load = prefill = 0`. (ii) SD-2's refusal gets its own client type
> (`OllamaMeasurementClient`); the benchmarks build theirs from a CLI `--model`
> tag, so refusing unmeasured models at construction meant **the capacity table
> could never have gained a row**.
>
> ✅ **Also landed:** the capacity chokepoint + per-model clamp
> (`services/engine/llm/capacity.py`); `action_step` degrades **disclosed** on
> an LLM-arm failure instead of leaving a bare `error` trace. ✅ **Evidence:**
> six batteries on the merged tree — **102 claims, 92 RED, 10 exempted, GAPS 0
> on all six**; gates at true CI scope on every PR, CI green on all three.
> **MS-S1 was never contacted.** 🔴 **AC-9/AC-10 stay unticked by design** — no
> live arm has run, and everything left in PLAN-0119 needs its own typed §8 go.

🔴 **THIS (s288) reconcile rotates the session-285 AND session-286 blocks** (caller-measured **2,810 B** and **2,397 B**, both under the 4,096 B cap) on the **headroom rule**, not a cap overage: the scribe's additive draft took STATUS to **68,359 B**, **2,823 B OVER** R1's 65,536 B ceiling. Rotating one block alone would have closed at ~**64,990 B** — ~546 B of headroom, the exact thinness the s287 entry warned starves the next session — so **the window lands at TWO (287, 288), a first**. Both blocks' own entries travelled with them; ⚠️ the s286 entry was **1,149 B, over the ~900 B per-entry cap** (Cray, s267), so rotating it cleared a live breach too. Destination `2026-h1e-current-focus.md`. ✅ **Caller-measured, append VERIFIED by content in both directions:** STATUS **68,359 → 59,642 B** on the six-slice rotation; that archive **34,421 → 43,616 B** (+9,195).

🔴 **THIS (s287) reconcile rotates the session-283-284 block** (caller-measured **3,041 B**, well under the 4,096 B cap) on the **headroom rule** — and uniquely, the prune is the **caller's, not the scribe's**: the scribe was told not to rotate because the window had a free slot (3 → 4, exactly R2's window), and it did not. Bytes forced it afterwards. STATUS opened at **60,720 B** and closed the scribe's edit at **65,146 B**, only **390 B** under R1's 65,536 B — enough to pass the guard and not enough for the next session to write a line. The window lands at **THREE** again (285, 286, 287), the sixth consecutive reconcile of this shape. 🔴 **This ledger's own s284 entry travelled with the block, probed ABSENT against a working positive control** (`Session 282` = 1, `THIS (s282)` = 1; fabricated needle = 0) — a genuine first append. Destination `2026-h1e-current-focus.md`; the RD row (s275) went to `2026-h1-status.md` on the count rule alone.
