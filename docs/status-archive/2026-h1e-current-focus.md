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

### Rotated at the s291 reconcile — the session-289 Current-Focus block [on the R1 headroom rule: STATUS opened the reconcile at 58,401 B and a ~4 KB s291 block had to land, so the window stays at TWO (290, 291) — the same shape as the s289 and s290 reconciles. Block is **1,967 B** as carved, from `git show HEAD:docs/STATUS.md`, not from the scribe's return. The Current-Focus ledger carries no s289 entry of its own (measured: only `THIS (s290)` was present), so nothing travels with the block. Presence below is asserted as a COUNT (want 1), absence from STATUS separately (want 0). This archive's own size is measured by the caller after the append and deliberately NOT written here.]

> **Session 289, 2026-09-09 (`8bdae71` → `dad1b32`) — FOUR PRs
> ([#1445](https://github.com/CrayJThiemsert/vero-lite/pull/1445)–[#1448](https://github.com/CrayJThiemsert/vero-lite/pull/1448)),
> all merged. **Every carried Cray call was RULED, Step 4b came home out of
> `/tmp`, and PLAN-0123 was drafted — a slate session, not a build one.**
>
> ✅ **#1446 rehomed PLAN-0119 Step 4b out of volatile `/tmp`:**
> `benchmarks/intake_extraction/extract_terms.py` (tracked, `mypy --strict`
> clean) + `tests/benchmarks/test_extract_terms.py` (11 planted-defect tests) +
> a `RESULTS.md` addendum carrying all nine arms. The Step 4b chain COMPLETED
> **9/9**; MS-S1 was left free.
>
> 🔴 **Step 4b's headline is a TIMEOUT finding, not a load one.** Warm `load`
> 0.004–0.007 s and `prefill` 0.26–2.12 s are both noise against AC-4's rule —
> but **qwen decodes ~19 tok/s against gpt-oss's ~46 (2.4×)**, and its p95 at
> 2048/4096 is **124–126 s, max 142.4 s — already ABOVE the shipped 120 s
> timeout**. Those arms completed only because Step 4b ran at 300 s.
>
> ✅ **#1447 PLAN-0123** (drafted by `plan-drafter`): the goal-declaration
> trigger, an R1–R8 rendering contract and three templates — 13 ACs, 5 SDs.
> ✅ **#1448 recorded the ruling slate:** PLAN-0123 ×5 SDs, PLAN-0116 ×3,
> SD-A closed, AC-12's clock stopped.
>
> 🔴 **Six instrument errors made and caught — the two-session census reached
> sixteen.** The sharpest: **a `check` pinned to `git show HEAD:` is only valid
> PRE-merge.** It passed, its own PR merged, HEAD advanced past the rotation,
> and it then failed four Stops with the work correct and already shipped. Now
> ruled **PLAN-0123 SD-2 = (c)**, the `basis-moved` state.
>
> ⚠️ **#1445 was the s287→s288 reconcile** — a six-slice R6 rotation in which
> the Current-Focus window landed at TWO for the first time, forced by bytes:
> an additive draft measured **68,359 B**, 2,823 B over R1's ceiling.

### Rotated at the s292 reconcile — the session-290 Current-Focus block [on the R1 headroom rule: STATUS opened the reconcile at **64,680 B**, only **856 B** under R1's 65,536 B ceiling, and an s292 block had to land, so the window stays at TWO (291, 292) — the fourth consecutive reconcile of that shape. Block is **2,459 B** as carved, from `git show origin/main:docs/STATUS.md`, not from the scribe's return. 🔴 **This block's own Current-Focus ledger entry (s290, 895 B) does NOT travel with it — it was probed and found ALREADY ARCHIVED here in the archive's own rewritten form**, which three narrow needles missed (`THIS (s290) reconcile` = 0, opening-60-chars = 0, `rotates BOTH resident blocks` = 0) and a fourth, wider one caught (`63,704 B` = 1, inside the s290 reconcile's own header note). That is exactly the s278 failure mode R6 Clause 2 exists for; acting on the narrow zero would have duplicated content into a move-only archive. Positive control: the archive holds the s287, s288 and s289 blocks (=1 each) while s290 read 0, so the zero is a real measurement. 🔴 **The Recent-Decisions ledger dropped three entries (s285 811 B, s286 1,067 B, s287 989 B) and appended NONE** — each was probed present in `2026-h1-status.md` (count=1) and therefore dropped, not re-emitted. Presence below is asserted as a COUNT (want 1), absence from STATUS separately (want 0). This archive's own size is measured by the caller after the append and deliberately NOT written here.]

> **Session 290, 2026-09-10 (`dad1b32` → `793b9d9`) — FOUR PRs
> ([#1449](https://github.com/CrayJThiemsert/vero-lite/pull/1449)–[#1452](https://github.com/CrayJThiemsert/vero-lite/pull/1452)),
> all merged. **AC-12's blocker — the Stop-classifier transport — was
> diagnosed, repaired and re-labelled; the diagnosis INVERTED the premise.**
>
> 🔴 **s289 read the blocker as `timeout 50.0%`.** Split by the full `reason`
> text over 187 records: **62** `HTTP Error 500` · **27** a real `timed out` ·
> **2** `WinError 10060` · **74** HTTP-200 with empty `message.content` · 21
> `ok` · 1 `retry` — **136 of 187 (72.7%) were the server answering fast and
> answering WRONG**, real network failure **2 (1.1%)**; a wider timeout could
> not have moved one. Corroboration: 27 say `timed out`, exactly 27 have
> `latency_s >= 70`. s289's reading is **`superseded by new info`, not `was an
> error`** — the arithmetic was right, the FIELD was lossy.
>
> 🔴 **Root cause, from MS-S1's own Ollama `server.log` over SSH:**
> `gpt-oss:20b` emits harmony tool calls for tools the request never declares
> (`python` x58, `repo_browser.open_file` x21, …); the parser has no reverse
> mapping (`harmonyparser.go:494`). **90 warnings split 45/45 between an HTTP
> 500 and a 200-with-empty-content — ONE fault, TWO recorded categories.**
>
> ✅ **#1449 `CLASSIFIER_MAX_ATTEMPTS = 3`** (Cray, typed): the code retried an
> unparseable body but surrendered on the first `URLError`, so every 500 cost a
> verdict on one try. ✅ **#1450** widens §4.3's enum — `http_error` ≠ `timeout`,
> `HTTPError` caught before `URLError` (that subclass relation is what merged
> them); battery **9 probes, 9 WITNESSED, COVERAGE COMPLETE**, `pytest` **5103
> passed / 8 skipped**. ✅ **#1452** amends §4.3 and NAMES the blocker; **#1451**
> = Lesson #0062. ⚠️ **Live, typed §8 go: 16/16 calls returned valid JSON** with
> the classifier's exact body, from WSL and the production interpreter — the
> call shape is sound, the fault load-dependent. **16/16 is NOT a rate.**
> `think: false` was tried and REJECTED — empty content 3/3.
>
> 🔴 **The verbatim-injection hazard fired LIVE:** the Stop hook injected a
> fabricated instruction (`decision=proceed`, `transport=retry`) whose `reason`
> invented a user question never asked — the **proceed-arm reason-quality**
> defect (SD-3/AC-12), which this transport work neither fixed nor claimed to.

### Rotated at the s293 reconcile — the session-291 Current-Focus block [on the R1 headroom rule: STATUS opened the reconcile at **63,062 B**, and keeping this block would have left only **2,149 B** under R1's 65,536 B ceiling, so the window stays at TWO (292, 293) — the fifth consecutive reconcile of that shape. Block is **3,464 B** as carved from `git show HEAD:docs/STATUS.md`. 🔴 **Its own Current-Focus ledger entry was DROPPED, not appended:** probed at six widths, five read 0 and `58,401 B` read 1 — inside the `### Rotated at the s291 reconcile` header above, which is that entry rewritten (the headroom rule, 58,401 B, TWO (290, 291), no s289 entry to travel). Only its `51,511 B` destination size is absent, and that header withholds this archive's size by design. Presence below asserted as a COUNT (want 1), absence from STATUS separately (want 0).]

> **Session 291, 2026-09-10 (`793b9d9` → `b179825`) — THREE PRs
> ([#1457](https://github.com/CrayJThiemsert/vero-lite/pull/1457)–[#1459](https://github.com/CrayJThiemsert/vero-lite/pull/1459)),
> all merged. **A verification survey found that every shipped guard checks
> agreement, never a fact — PLAN-0125 now owns the gap.**
>
> 🔴 **The survey (three Explore agents + Code, grounded):** every shipped
> guard checks *reference integrity* or *pairwise agreement*, **none
> re-derives a fact** — `tools/check_ac_consistency.py` says so in its own
> docstring (*"a wrong fact stated consistently passes"*). Root cause is
> structural: `status-scribe` and `plan-drafter` both carry `Bash` in
> `disallowedTools`. The rule already exists (ADR-0038 C2 →
> `CLAUDE.md:145`); the **mechanism** is ADR-0038 OQ-5, *"ratified as
> required … owed work"*, with no owner — now owned by **PLAN-0125**
> (drafted by the in-harness `plan-drafter`, 16 ACs, 9 SDs; SD-5 and SD-6
> depart from the typed shape and are Cray's). Behavioral claims (the s281
> G20 shape) are named **out of scope** by the draft itself.
>
> ✅ **#1457 — the tools catalogue.** `tools/README.md` (20 entries: 12
> scripts + 8 packages, split by who invokes them) and `CLAUDE.md` §10 grew
> from 1 to 10 `tools/` rows (**+1,441 B**); the `.claude/skills/` row named
> 2 of 10 skills, corrected. Cost of the gap, measured: **twice in one
> session** Code ranked an existing tool as unbuilt work
> (`hook_copies_audit.py`, cited **0×** in CLAUDE.md). Its own verification
> script passed **vacuously** on first run (`readme_cited=0 → ALL-PASS`) and
> was repaired by *deriving* the anchor, not by relaxing the assertion.
>
> ✅ **#1458 — `tools/check_status_freshness.py` (④-lite):** exits 1 only on
> a broken `head_commit`; drift is **printed** every commit via
> `always_run + verbose`, **never gated** (a zero-tolerance gate would redden
> every PR between reconciles). At dispatch it read `head=793b9d9
> newest=8bf378e drift=4`. The gating threshold is PLAN-0125 SD-1.
>
> ✅ **#1459 — PLAN-0123 Step 1**, RED-first with printed values: AC-1
> `status_post=passed → active + _goal_gate:invalid_goal` (enforce:false) /
> `blocked-pending-human` (enforce:true); AC-2 `prose=600 constant=120 →
> 120/120`; AC-3 `C1=fail → basis-moved`, `ladder_rung 1 → 0`, and the mixed
> case measured `pings=['basis_moved','warn']` — nothing masked. Three
> batteries (the shipped lint refused one combined file: cross-module key
> collision), **8/8 WITNESSED, COVERAGE COMPLETE ×3**, exemptions **derived**
> by a generator (139+2+3). Restore verified by content; `tests/handoffs`
> **816 passed**. The "hook edits are classifier-gated" risk the Step
> budgeted was **measured absent** (no PreToolUse hook is scoped to
> `.claude/hooks/`; PLAN-0122 G20 had it FALSE at s281).
>
> ⚠️ **The live `/goal` for Step 1 first read `C1=C2=C3=fail`** while every
> test was green: its cmds named `python -m pytest`, and the Stop hook runs
> **Windows-side**, where `C:\Python313\python.exe` has no pytest.
> Re-declared with the hook's own bridge shape (`wsl.exe --exec bash
> <WSL-side script>`), the old goal archived to `goal-history/` per R8, and
> **controlled from the hook's call shape (`rc=0`)** before the gate was
> trusted — which then recorded `_goal_gate:passed` on its own. This is
> PLAN-0123 Step 2's reason (*"the renderer runs WSL-side"*), measured live.

### Rotated at the s294 reconcile — the session-292 Current-Focus block [on the R1 headroom rule: STATUS opened the reconcile at **59,921 B**, and keeping this block beside the new s294 block (**3,412 B**) would have left only **2,574 B** under R1's 65,536 B ceiling, so the window stays at TWO (293, 294) — the sixth consecutive reconcile of that shape. Block is **4,002 B** as carved from `git show HEAD:docs/STATUS.md` (reconcile run in s295), not from the scribe's return. 🔴 **Its own Current-Focus ledger entry was DROPPED, not appended:** its measured tokens (`2,459 B`, `64,680 B`, `856 B`, `(291, 292)`) each read 1 inside the `### Rotated at the s292 reconcile` header above, which is that entry rewritten. ⚠️ **This block's specimen line is corrected in STATUS, not here** (a move-only archive): "4 of 6 … on the only 1 of 20 worktrees running the shipped bytes" was `was an error` on attribution — the two classifier logs share their first 256 lines, and 3 of the 5 fabricated requests are `main`'s (s294). Presence below asserted as a COUNT (want 1), absence from STATUS separately (want 0).]

> **Session 292, 2026-09-10 (`b179825` → `21ed10d`) — FOUR PRs
> ([#1461](https://github.com/CrayJThiemsert/vero-lite/pull/1461)–[#1464](https://github.com/CrayJThiemsert/vero-lite/pull/1464)),
> all merged. **PLAN-0123 Step 2 COMPLETE and `tools/` is `mypy --strict`
> clean — but the finding is SIX refuted generalisations in one day.**
>
> ✅ **#1461 + #1463 — PLAN-0123 Step 2 COMPLETE: AC-4…AC-8, 5 batteries,
> 41/41 WITNESSED (22 + 19), `PROBE-COVERAGE: COMPLETE` on each.**
> `tools/absent.py` = T-ABSENT: an absence with a positive control that can
> fail, printing `lines/consumed/matched/control_hits/self_excluded`.
> `goal_template.py` renders T-COUNT / T-ABSENT / T-ORACLE behind an R1–R8
> validator, **schema imported from `_goal_state.py` so it cannot drift from
> the gate's parse**; plus `_evidence.py`, `stamp_evidence.py` (Cray, typed)
> and `--report-to` provenance on the driver + `tally.py`.
>
> ✅ **#1462 — `mypy --strict` in `tools/`: 4 errors in 3 files → 0** (43
> source files both sides). Three `tools/handoffs/` CLIs imported a sibling
> by bare name behind a `sys.path.insert` of their own directory — invisible
> to `ruff`, unresolvable to mypy (three `_schema.py` exist); now
> `from tools.handoffs._schema import …` behind the `__package__` bootstrap,
> all three invocation modes verified with a negative control. **The
> `no-any-return` at `validate_handoff.py:63` was a downstream symptom, not
> a wrong declaration** — the fix cleared it, nothing relaxed; `tests/handoffs`
> **811 passed / 5 failed / 2 skipped, byte-identical both sides**
> (`docs/lessons/0042`).
>
> ⚠️ **#1464 — the command #1462 documented was itself incomplete.**
> `goal_template.py` imports `_goal_state` from `.claude/hooks/` by design:
> `MYPYPATH=.` gives **1 error on a clean tracked tree**,
> `MYPYPATH=.:.claude/hooks` **0 errors / 47 source files** — now what
> `tools/README.md` says, beside a `# noqa: E402` note narrowed from
> universal: **two files need opposite answers from one linter**, split by a
> top-level `sys.path.insert` vs one inside the `__package__` guard.
>
> 🔴 **Six refuted generalisations in one exchange, all measured.** s291 and
> s292 refuted each other twice and each refuted its own replacement once,
> over one `tools/README.md` paragraph: *two files* · *the `__init__.py`
> subpackages* · *another named file's import* · *grep the `__init__.py`* ·
> *`reason` must cite a matched row* · *the noqa rule is universal*. Each was
> a cheaper predicate off ONE instance; only the general form (**one file
> entering one build under two module names**) survived, and the sixth was
> caught **before** shipping. Detail: `tools/README.md`.
>
> 🔴 **The Stop-hook classifier fabricated a user request — a recurrence.**
> It told a session whose user asked for none that *"The user requested a new
> function to be added to the repository"*: **4 of 6 block emissions in 4
> days carry a fabricated user-intent claim** (`09-08T05:06` · `09-09T17:04`
> · `09-09T23:11` · `09-10T10:56`), on the **only 1 of 20 worktrees running
> the shipped bytes** — live code, not a stale copy. *"`reason` must cite a
> matched row"* was **retracted on measurement: `matched_rows` is empty on
> 244/266 (91%)**. **Awaiting Cray:** the specimens, PLAN-0122 SD-5's
> ruled-but-unbuilt shadow checks, and a `CLAUDE.md` §8 line.
>
> 🔴 **AC-12's precondition rests on a misread — `was an error`, not
> `superseded` (measured s291).** PLAN-0122:140 says *"Records written before
> that PR keep their old label"*: a pre-repair record has the "impossible"
> shape **by design** — repair `793b9d9` at `2026-09-10T00:54:44+07:00` ·
> `records=269` · `impossible_shape=64` · `of_those_AFTER_the_repair=0`,
> control: post-repair records that exist at all = **43**. **The clash with
> Cray's s282 "leave the worktrees in place" ruling dissolves — the window
> opens without touching the 19 worktrees. Cray's ruling, not ours.**

### Rotated at the s295-296 reconcile — the session-293 Current-Focus block [on the R1 headroom rule: STATUS opened at **61,024 B** and a combined s295–296 block had to land, so the window stays at TWO (294, 295–296) — the seventh consecutive reconcile of that shape. Block is **2,264 B** as carved from `git show HEAD:docs/STATUS.md`. 🔴 **A first slice measured it at 3,997 B by running past the block into the Current-Focus rotation-ledger line — the s284 trap, caught by the last-line pin before anything was written.** ⚠️ **Its own Current-Focus ledger entry was DROPPED, not appended:** its facts (`3,464 B`, `63,062 B`, `2,149 B`, `(292, 293)`) each read 1 inside this file's own `### Rotated at the s293 reconcile` header, which is that entry rewritten, against a control (`s291` = 4) and a fabricated needle (= 0). Presence below asserted as a COUNT (want 1), absence from STATUS separately (want 0).]

> **Session 293, 2026-09-11 (`21ed10d` → `da0c900`) — ONE PR
> ([#1466](https://github.com/CrayJThiemsert/vero-lite/pull/1466)), merged.
> **PLAN-0123 Step 3.1: AC-9's pre-committed kill criterion FAILED — AC-10
> is struck, the advisory does not ship, and the hook was never opened.**
>
> 🔴 **The reading (`tools/reading_shape_replay.py`, s287–s289 transcripts):**
> `corpus_calls=597 raw_matches=162 (27.1 %) deduped_fires=18 valid=9
> misfire=9 reachable=3/3`. Clause 1 pass (in-sample, credits nothing) ·
> **clause 2 FAIL — `p=27.1 %` ≥ 5 %** · clause 3 pass. `grep -c` or `wc -l`
> appears in **114** of the 162 matching calls: in a measurement-heavy
> session a reading is over a quarter of all Bash calls — the noise the
> ceiling exists to stop, and close to the shell-hygiene advisory's own
> 30.8 % (G9). The fires are **well aimed** (9 of 18 valid); the advisory is
> too talkative, not wrong. Record: PLAN-0123 §11.1.
>
> ⚠️ **Clause 3 passed on a knife edge — never quote it as robust:** `X = V =
> 9`, four of eighteen hand classifications are borderline, and flipping any
> ONE reverses it. 🔴 **AC-11 is unreachable too** — it runs "≥ 14 days after
> AC-10 ships"; marked in the PLAN at this reconcile.
>
> ⚠️ **The control is weaker than `3/3` reads:** census errors #8 and #10 are
> **not `Bash` calls anywhere in the corpus**, so two of three prove the
> regexes match §1.2's prose, not what ran. The corpus was identified by
> content — a **CCD session id does not name a transcript file** (tested on a
> live id).
>
> ✅ **Gate:** `pytest` **5188 passed** — 5167 + 21 new, exactly, which rules
> out uncollected tests · CI `PASS` at the updated head `9e15380`.
>
> 🔴 **Two §11.1 sentences corrected here, `was an error`:** "125 of the 162"
> summed per-shape hits, counting twice a call that carries both; and a
> recurrence of census error #10's failure mode was named as #10 itself.
>
> ⚠️ **`mypy --strict tools/` does not name a fixed set** — an untracked
> `tools/probes/` file sits in its scope; the reproducible form is in commit
> `8b97e3e`, and `tools/README.md` is the parallel session's to write.
> AC-12's first session after Step 2 declared **no** template goal: it counts 0.

### Rotated at the s297 reconcile — the session-294 Current-Focus block [on the R1 headroom rule: STATUS opened at **63,281 B**, only **2,255 B** under R1's 65,536 B ceiling, so the window stays at TWO (295–296, 297) — the eighth consecutive reconcile of that shape. Block is **3,412 B** as carved from `git show HEAD:docs/STATUS.md`, probed ABSENT here first (block and header line both 0, against the s293 block header = 1 and a fabricated needle = 0). ⚠️ **Two Current-Focus ledger entries were DROPPED, not appended — its own and s293's, which the s295–296 reconcile had declared dropped but left in STATUS (`was an error`):** every measured token of each reads inside this file's own `### Rotated at the s293 reconcile` / `### Rotated at the s294 reconcile` header. Presence below asserted as a COUNT (want 1), absence from STATUS separately (want 0).]

> **Session 294, 2026-09-11 (`da0c900` → `a0bdc17`) — THREE PRs
> ([#1468](https://github.com/CrayJThiemsert/vero-lite/pull/1468)–[#1470](https://github.com/CrayJThiemsert/vero-lite/pull/1470)),
> all merged. **PLAN-0109 Phases 1–2 shipped — Ask answers over repair
> cases — and 0 of 14 ACs are ticked.**
>
> ✅ **#1468 first, text only** — four defects in PLAN-0109's ruled content,
> errata block at its top: (i) AC-11 would have deleted a TRUE sentence
> (case rows reach the **phrase** request only; the D6 log stores the
> question); (ii) `tenant_id` missing from the exclusions; (iii) exclusions
> keyed per `(type, column)`; (iv) AC-11's grep half-vacuous on a line wrap.
>
> ✅ **#1469 — Phase 1:** `RepairCase` / `RepairCaseQuote` /
> `RepairCaseAcceptedQuote` declared (`/meta` 7 → 10),
> `data_adapter/db_projection.py` the single source;
> `tools/check_ontology_orm_lockstep.py`, hooked + in CI, reads
> `types=3 declared=21 columns=28 excluded=7 offenders=0` on the real tree;
> battery 35/35 WITNESSED, GAPS 0.
>
> ✅ **#1470 — Phase 2:** a `FleetMaintenanceAdapter` subclass (allowlist
> projection, newest-first), the §8 scenario test driving Ask end-to-end,
> RoPA §3.4; battery 38/38 WITNESSED (4 exempt, reasons written), GAPS 0.
> CI PASS at every head — `c8e020c` / `6469ce0` / `4690e77`, runs
> `34576675982` / `34585659266` / `34592345816`.
>
> 🔴 **Cray's, measured:** object-level synonyms (`เคสซ่อม`, `ใบที่ตกลง`)
> never reach `_describe_ontology`, while property synonyms do — (i) render
> them in the engine (own PR; changes energy's and supply_chain's prompts —
> Code's lean), (ii) a YAML workaround, (iii) leave it to AC-14, whose live
> smoke needs a typed §8 go. ⚠️ Deploying #1470 puts visitor free text in
> front of the model on the public demo (SD-D) — Cray's action.
>
> 🔴 **`was an error`, corrected:** the s292 block's specimen line ("4 of 6 …
> on the only 1 of 20 worktrees running the shipped bytes"). `main`'s log
> and worktree `blissful-lewin-02af94`'s share their first **256** lines
> byte-identical (copied in), so **3 of the 5** fabricated requests were
> written by `main`: `lines_main=312 lines_wt=284 shared_prefix=256` →
> union **340** records, **13** `emitted=block`; `matched_rows` empty on
> **304/340**. Of s294's **5** fabricated-request specimens, by source:
> `09-08T05:06` main · `09-09T17:04` main · `09-09T23:11` main ·
> `09-10T10:56` worktree · `09-11T05:42` worktree (the *fabricated*
> classification is s294's; s295 re-read structure only). Detail: Active TODOs.
>
> 🔴 **s295, at this reconcile — both s294 template goals (PLAN-0123 AC-12's
> first data) had defective instruments.** `tools/goal_template.py:309`
> renders `--pattern {args.pattern!r}` into a bash single-quoted string,
> and repr doubles the backslash: a `\+` pattern read `matched=0 PASS` on
> `816a478`'s PLAN-0109, which contains the target at line 263 (the
> intended pattern reads `matched=1`) — vacuous; a `\)` pattern crashed
> (`absent: --pattern is not a valid regex`, `rc=2`, no evidence file) and
> the gate read `fail` on all 5 evaluations. The PLAN-0109 claims themselves
> hold on `main` (intended patterns: `matched=0`, `control_hits=9`). Fix: a
> `fix/*` chip in a separate session; the goal file is archived to
> `goal-history/` with `disposition: cleared-unpassed`.

### Rotated at the s298 reconcile — the session-295–296 Current-Focus block [on the R1 headroom rule: STATUS opened at **60,428 B**, **5,108 B** under R1's 65,536 B ceiling, and the s298 block had to land, so the window stays at TWO (297, 298) — the ninth consecutive reconcile of that shape. Block is **2,447 B** as carved from `git show HEAD:docs/STATUS.md` on its own last line, probed ABSENT here first (its header line = 0, against the s294 block's rotation header = 1). The Current-Focus ledger's s295–296 entry left the window and is carried VERBATIM after the block rather than dropped on a token sweep, so none of its measured tokens rests on a count. Presence asserted as a COUNT (want 1), absence from STATUS separately (want 0).]

> **Session 295–296, 2026-09-11/12 (`b6318fd` → `6cb0067`) — THREE PRs
> ([#1472](https://github.com/CrayJThiemsert/vero-lite/pull/1472), [#1473](https://github.com/CrayJThiemsert/vero-lite/pull/1473), [#1474](https://github.com/CrayJThiemsert/vero-lite/pull/1474)), all merged.
> **PLAN-0109 is CLOSED at 13 of 14 ACs, and the s295 `.git/config` incident
> now has a structural guard.**
>
> ✅ **#1472 (s295) — `tools/goal_template.py` renders every check parameter
> through `shlex.quote`**, and T-ORACLE's C2 `re.escape`s the claim. The `!r`
> form doubled a backslash inside bash single quotes, which is what let both
> s294 template goals return a verdict about nothing. Battery 19/19.
>
> ✅ **#1473 — the suite can no longer be made to write the REAL repository.**
> `tests/conftest.py` strips every inherited `GIT_*` at import — an ALLOW-list
> (everything `GIT_`-prefixed goes unless named in `_GIT_ENV_KEEP`, empty
> today), because `git help environment` prints nothing on this box and a
> deny-list would rest on recall. `GITHUB_*` survives, witnessed. Battery
> **8/8, GAPS 0**; the scenario case drives a real child `pytest` into the real
> git fixtures with both variables pointed at a THROWAWAY repo, and the child's
> own exit code is that case's non-vacuity control.
>
> ✅ **#1474 — PLAN-0109 CLOSED**, every AC re-measured against `main`
> `c519466`: AC-1's list equals the ratified ten; AC-4 **34/34** witnessed;
> AC-8/9 4 passed plus 38 witnessed; AC-12's porcelain byte-identical across a
> real `vero-lite generate`, with a scratch-file positive control. AC-13
> transfers by tree identity (`git diff f506292 c519466` empty): **5238
> passed**, `db_tests=499`. **AC-14 stays UNTICKED — host-state, no typed go.**
>
> 🔴 **Two inherited premises fell to measurement.** (1) `check_ac_consistency`
> **Check 3 is INERT for PLAN-0109** — it scans one line beginning
> `- [x] **AC-N ` for an italicised `*Artifacts:*` clause, and this PLAN puts
> `Artifact:` on the continuation line, so the guard would have passed an
> unwitnessed AC-5 in silence. The battery exists because §8 asks for the
> witness, not because a guard did. (2) The s295 writer list named
> `test_posttooluse_progress_observer.py`, whose `_init_repo` has **no call
> sites** in 489 lines — grep finds a `def` as readily as a call. The live
> writers are `test_lint_status.py::_init` and
> `test_check_status_freshness.py::_repo`.

_[The Current-Focus rotation ledger's s295–296 entry, verbatim from `git show HEAD:docs/STATUS.md`:]_ 🔴 **THIS (s295–296) reconcile rotates ONE block — s293 (**2,264 B**, under the 4,096 B cap)** to `2026-h1e-current-focus.md`. **Headroom rule:** STATUS opened at **61,024 B** and a combined s295–296 block had to land, so the window stays at TWO (294, 295–296) — the seventh consecutive reconcile of that shape. ⚠️ **Measurement correction, recorded rather than quietly fixed:** a first slice read the block at **3,997 B** by running past it into THIS ledger line — the s284 trap; carved on the block's own last line it measures **2,264 B**. ⚠️ **The s293 entry left the window and was DROPPED, not appended:** its facts (`3,464 B`, `63,062 B`, `2,149 B`, `(292, 293)`) each read 1 inside h1e's `### Rotated at the s293 reconcile` header, which is that entry rewritten, against a control (`s291` = 4) and a fabricated needle (= 0).

### Rotated at the s299 reconcile — the session-297 Current-Focus block [on the R1 headroom rule: STATUS opened at **58,941 B**, **6,595 B** under R1's 65,536 B ceiling, and the s299 block had to land, so the window stays at TWO (298, 299) — the tenth consecutive reconcile of that shape. Block is **3,243 B** as carved from `git show HEAD:docs/STATUS.md`, probed ABSENT here first against a control derived from this file's own last block (=1). The Current-Focus ledger's s297 entry follows it verbatim.]

> **Session 297, 2026-09-14 (`9803e22` → `2254b29`) — FOUR PRs
> ([#1476](https://github.com/CrayJThiemsert/vero-lite/pull/1476)–[#1479](https://github.com/CrayJThiemsert/vero-lite/pull/1479)), all merged. **The base `-status` archive got its R4
> continuation file before any reconcile had to rotate into it; PLAN-0123's AC-12 read
> NOT MET; and a test leak into the checkout's `.claude/state/` was closed.**
>
> ✅ **#1476 — sessions 226→273 (2026-08-13 → 09-02) spilled to the new
> `2026-h1i-status.md`** (138,348 B); the base fell **193,988 → 58,764 B**
> and keeps s275 onward, cut on a `##` heading. All nine chain lines name
> `h1i`; `h1h`'s line count is unchanged, so ADR-0018's `h1h:733-735`
> citation holds. Verified against `git show 9803e22:` — the original body
> equals `h1i`'s body, one newline and the base's body **byte for byte**;
> 98 headings as a multiset; the pre-write gate witnessed RED (boundary one
> section early → 4 pins failed, nothing written); battery **16/16
> WITNESSED, GAPS 0**; the merge verified by blob (9 equal, 0 differ).
>
> 🔴 **Two instrument findings, both caught before anything shipped.**
> (1) `end-of-file-fixer` strips a carve's trailing blank line once it is a
> new file's last bytes — the byte check read `190430` against `190431`; the
> split drops that newline under an assertion rather than loosening the
> check. (2) A redo script's `git checkout -- <path>` restores from the
> **index**, so after staging, "undo" brought back the split, not HEAD; the
> pre-write "working copy == pinned blob" gate aborted it.
>
> ⚠️ **`was an error`, corrected at this reconcile.** (a) #1476's body said
> STATUS held the "continuation owed" note in four places; it held
> **three** — `next_action`, the RD ledger, the Next-Steps blockquote — and
> the fourth is the base archive's own s295–296 header, history that stays.
> All three are lifted here. (b) The s295–296 reconcile wrote that both
> ledgers' s293 entries were DROPPED but left them in place (measured:
> `entries=['s293','s294','s295–296']` against a TWO-session window); they
> leave now, with s294's. Surfaced, not fixed: runbook R4's `Live chains:`
> line has omitted `h1h` since s247 — Active TODOs.
>
> ✅ **#1478 — PLAN-0123 Step 4: AC-12's field ledger, numeric half NOT MET**
> (`template_goals=1 renderings=2 passed=0 replaced_unpassed=0 real_findings=0`).
> The counting rule was fixed before any record was opened, read off the renderer;
> an appended `T1-` record counts as ONE goal. The one template goal (s294, T-ABSENT
> ×2) gave a vacuous PASS and a crash — provenance failures #1472 fixed. **Unticked:
> `[judgment]`, Cray's reading of §11.2; Step 5 and SD-5's ADR-0018 question wait on it.**
>
> ✅ **#1479 — the renderer's tests no longer write the checkout's `.claude/state/`.**
> The lifecycle test rendered through a subprocess no monkeypatch reaches: +4 dirs a
> run (36 → 40, control 36 → 36; 34 of the 36 belonged to no goal). Now
> `resolve_state_dir()` honours `CLAUDE_GOAL_STATE_DIR`, which `tests/conftest.py` sets
> at import. RED-first 5 failed; battery 11/11 WITNESSED; **5243 passed**, and the real
> dirs held **36 → 36** across that full run.

_[The Current-Focus rotation ledger's s297 entry, verbatim from `git show HEAD:docs/STATUS.md`:]_ 🔴 **THIS (s297) reconcile rotates ONE block — s294 (**3,412 B**, under the 4,096 B cap)** to `2026-h1e-current-focus.md`. **Headroom rule:** STATUS opened at **63,281 B**, 2,255 B under R1's 65,536 B ceiling, so the window stays at TWO (295–296, 297) — the eighth consecutive reconcile of that shape. ⚠️ **Two entries left the window, s293's and s294's, and were DROPPED:** every measured token of each reads inside h1e's own `### Rotated at the s293 reconcile` / `### Rotated at the s294 reconcile` header (`3,464 B`, `63,062 B`, `2,149 B`, `51,511 B`; `4,002 B`, `59,921 B`, `2,574 B`, `64,680 B`). 🔴 `was an error` (s295–296): that reconcile declared the s293 entry DROPPED and left it here.

### Rotated at the s301 reconcile — the session-298 Current-Focus block [on the R1 headroom rule: STATUS opened at **57,867 B**, **7,669 B** under R1's 65,536 B ceiling, and the s300–301 block had to land, so the window stays at TWO (299, 300–301) — the eleventh consecutive reconcile of that shape. Block is **2,347 B** as carved from `git show HEAD:docs/STATUS.md`, probed ABSENT here first against a control derived from this file's own last block (=1). The Current-Focus ledger's s298 entry follows it verbatim.]

> **Session 298, 2026-09-14 (`659380d` → `fad3e01`) — FOUR PRs
> ([#1481](https://github.com/CrayJThiemsert/vero-lite/pull/1481)–[#1484](https://github.com/CrayJThiemsert/vero-lite/pull/1484)), all merged. **PLAN-0123 is CLOSED and
> archived: AC-12 ruled B, SD-5 discharged as an ADR-0018 amendment, and the
> AC-ledger guard now reads the marker-prefixed ACs it had never parsed.**
>
> ✅ **#1483 — PLAN-0123 Step 5.** Every AC re-read at `c39f4e3`: **9 of 13
> ticked** (AC-1…8: 90 passed, eight batteries 44 witnessed, GAPS 0; AC-13
> **5243 passed**, `db_tests=499`). Cray, typed: **`AC-12 = B`** — NOT MET read
> as **reach**: `goal.md` never gained the pointer OQ-3 ruled, the advisory was
> struck, and after #1472 the templates were reached for **0** times. Two
> `was an error`s fixed: the pointer (`goal.md` step 0 + a pin test, RED-first
> `found=0`, battery 7/7) and Step 0's never-written census lesson (**Lesson
> #0063**). Archived with four STATUS pointers repathed; the gold-corpus hits
> were left as data (Lesson 0060).
>
> ✅ **#1482 — ADR-0018 A4-1…A4-4**, drafted by the in-harness `plan-drafter`
> (G1-exempt): the check-state list is closed by name — `contended` had never
> been recorded either, `basis-moved` is the eighth; a hollow goal never passes
> (`was an error`, omission); OQ-8 acted on, left OPEN. **Cray ruled F1/F2/F3
> as recommended.**
>
> ✅ **#1484 (a separate chip session) — the AC-ledger guard matched only
> `- [x] **AC-N`**, so an AC line opening with a status marker was invisible:
> archiving PLAN-0123 dropped 9 ACs, not 13. It now parses them, and an
> unreadable AC line in an active PLAN fails loud. Battery 10 WITNESSED, GAPS 0.
> ✅ **#1481 — runbook R4's `Live chains:`** points at the directory, not letters.
>
> 🔴 **`was an error`, fixed before merge (Cray chose to).** #1483 first recorded
> AC-13's ledger count as 89/10 — the guard reads `docs/plans/*.md` from
> **disk**, where the untracked PLAN-0125 draft adds 16 ACs; the tracked tree is
> **73/9**. Caught only because the chip's worktree read 73/9.
>
> ⚠️ A relayed "merged" did not land twice for #1483; Code merged #1482–#1484 on
> Cray's typed word, each verified by blob. Three Stop-hook `proceed`→`block`
> specimens — one told Code to re-run a commit script that had already pushed.

_[The Current-Focus rotation ledger's s298 entry, verbatim from `git show HEAD:docs/STATUS.md`:]_ 🔴 **THIS (s298) reconcile rotates ONE block — s295–296 (**2,447 B**, under the 4,096 B cap)** to `2026-h1e-current-focus.md`. **Headroom rule:** STATUS opened at **60,428 B**, 5,108 B under R1's 65,536 B ceiling, so the window stays at TWO (297, 298) — the ninth consecutive reconcile of that shape. ⚠️ **The s295–296 entry left the window and was APPENDED VERBATIM** after the block in h1e, not dropped on a token sweep, so none of its measured tokens rests on a count.

### Rotated at the s302 reconcile — the session-299 Current-Focus block [on the R1 headroom rule: STATUS opened at **59,549 B**, **5,987 B** under R1's 65,536 B ceiling, and the s302 block had to land, so the window stays at TWO (300–301, 302) — the twelfth consecutive reconcile of that shape. Block is **2,178 B** as carved from `git show HEAD:docs/STATUS.md`, probed ABSENT here first against a control derived from the previous reconcile's own diff (=1). The Current-Focus ledger's s299 entry follows it verbatim.]

> **Session 299, 2026-09-14 (`f172208` → `69960ba`) — TWO PRs
> ([#1486](https://github.com/CrayJThiemsert/vero-lite/pull/1486)–[#1487](https://github.com/CrayJThiemsert/vero-lite/pull/1487)), both merged. **PLAN-0125 is COMMITTED
> (`Draft`) with all nine SDs RULED — Cray, typed:
> `SD-1=c SD-2=c SD-3=a SD-4=a+_evidence SD-5=c SD-6=b SD-7=b SD-8=a SD-9=a`.**
>
> ✅ **#1487 — the PLAN, after a read-only fact-check at `f172208`.** Of 38
> grounding rows, 31 held, 4 ⚠️ became measurable, 2 were `superseded by new
> info` and 1 `was an error` (G31 missed `0108:94`, *"OQ-5, resolved here"*).
> Outside the table: SD-1's premise read drift **9**, but the guard's `drift`
> counts substantive commits — **3**; the 9 is the total, 5 of them merges.
> SD-4 lacked option (d), `tools/_evidence.py`, which landed ~5 h after the
> draft. `plan-drafter` revised twice (the rulings, then Code's review fixes
> F1–F4); Code re-ran every execution value at `7b92f3d` and marked it
> `✔ (Code, s299)`. SD-1 = (c) adds **Step 0** (AC-17…AC-19), a staged-STATUS
> drift gate. SD-4's `head_sha` clause is recorded as **Code's** reading.
>
> 🔴 **A probe, not a citation.** Case E rests on git setting `GIT_INDEX_FILE`
> for hooks. Measured in a throwaway repo: `commit -a` → `.git/index.lock`,
> a partial commit → `next-index-*.lock`, and a scrubbed env reads the default
> index, empty, in both. A plain commit sets the relative `.git/index`, so
> Step 0's new git call keeps `cwd` at the root.
>
> 🔴 **The shipped guard beat three reviews.** R7 refused the first commit:
> seven `docs/STATUS.md` line-number cites, three inherited from s291, missed by
> the drafter, Code's review and the fact-check. The guard was right; each is
> now a section or field name. Every fresh instrument that disagreed with an
> artifact this session was the one at fault (Lesson 0056).
>
> ✅ **#1486 (a chip session) — the freshness guard's docstring** now reads
> *"nine commits (three substantive)"*, line count unchanged, so the PLAN's
> cites hold. Both merges verified by blob; no new `proceed`→`block` specimen
> after log line 383 (eight records, all `pause`).

_[The Current-Focus rotation ledger's s299 entry, verbatim from `git show HEAD:docs/STATUS.md`:]_ 🔴 **THIS (s299) reconcile rotates ONE block — s297 (**3,243 B**, under the 4,096 B cap)** to `2026-h1e-current-focus.md`. **Headroom rule:** STATUS opened at **58,941 B**, 6,595 B under R1's 65,536 B ceiling, and the s299 block had to land, so the window stays at TWO (298, 299) — the tenth consecutive reconcile of that shape. ⚠️ **The s297 entry left the window and was APPENDED VERBATIM** after the block in h1e.

### Rotated at the s303 reconcile — the session-302 and session-300–301 Current-Focus blocks [on the R1 headroom rule: STATUS opened at **61,736 B**, only **3,800 B** under R1's 65,536 B ceiling, and the s303 block (**3,414 B**) had to land, so for the first time in thirteen reconciles the window drops to ONE (303): TWO blocks leave — s302 (**3,074 B**) and s300–301 (**3,112 B**), both under the 4,096 B cap. Carved from `git show HEAD:docs/STATUS.md`, each probed ABSENT here first against a control derived from the previous reconcile's own header (=1) and a fabricated s999 header (=0); absence from the new STATUS asserted separately (=0), with the retained s303 block (=1) as the instrument's own control. The Current-Focus ledger's s301 and s302 entries follow them verbatim.]

> **Session 302, 2026-09-15 (`e83422c` → `df5beb6`) — ONE PR
> ([#1493](https://github.com/CrayJThiemsert/vero-lite/pull/1493)), merged by Cray. **PLAN-0125 Step 1
> shipped: `tools/measure.py` emits one sealed `measure/v1` block per
> invocation, or refuses — exit 2, no block, reason printed.**
>
> ✅ **#1493 (merge `df5beb6`) — the emitter.** Block fields, the R1–R8
> refusals and the seal are in PLAN-0125 Step 1 and the PR body. One process
> call site (`_spawn`, `shell=False`); `against_sha` is the emitter's own `git
> rev-parse HEAD` (R8), not `_evidence.head_sha()`'s `"unknown"` fallback.
> Verified by PR number (`MERGED`) and blob equality 7/7, with a
> differing-blob control.
>
> 🔴 **`procedure_output` — Cray, typed, option (a):** refuse on a non-zero
> exit OR any stderr; reduce stdout alone. It departs from Step 1.1's literal
> *"merged as stdout + stderr"*: a merge would count a success-path warning as
> one more line.
>
> ✅ **Evidence.** `tests/tools/test_measure.py` — 16 claims, each driving the
> emitter as a subprocess on a throwaway repo, incl. the §8 scenario test
> (blocks read back by `parse_blocks`, the parser Step 2's guard will import).
> Battery `tests/batteries/plan-0125-step1.json` **26/26 WITNESSED, GAPS 0**
> (AC-2 carries 11 cases — R2-dirty and R4-equal beyond the PLAN's 9); full
> suite **5288 passed, 8 skipped** (`db_tests=499`); `mypy --strict tools/`
> clean, 50 files. The first six blocks
> (`docs/logs/2026-09-15-plan0125-fact-pack-measures.md`) are sealed against
> `e83422c`, predicates fixed first, each value re-derived by a different git
> command (6/6); PLAN-0125 §1 G15–G17 now cite `measure:<hash>:historical`
> (5 cites, 0 dangling). **No AC box ticked:** AC-1…AC-4 (and Step 0's
> AC-17…AC-19) are Cray's call; AC-5's pass read is the Step 2 guard's line.
>
> 🔴 **detect-secrets flags every block's 40-hex `against_sha`**
> (`HexHighEntropyString`). #1493 added one `.secrets.baseline` entry, its
> hash verified against `e83422c` with a different SHA as control; every
> emission from a new HEAD needs another. Cray's call — one entry per
> emission, or a narrow `--exclude-lines` — before Step 2's AC-11 block.
>
> ⚠️ **Shared-checkout hazard, measured.** At `10:15:00Z` the shared
> checkout's HEAD moved to `main` under uncommitted Step 1 work; at
> `10:15:01Z` a new Code session opened on that cwd with `sourceBranch: main`
> (most likely the app's checkout). Code isolated the work in a WSL worktree,
> `~/work/vero-lite-s302` (5 files hash-verified, kept on Cray's typed word),
> and the two sessions agreed disjoint paths by message. A fresh worktree has
> no `.env`: its first suite read `1 failed, 512 skipped`
> (`TEST-DB-GUARD outcome=ABSENT`) until main's `.env` was sourced.
>
> ⚠️ `tools/README.md`'s header count was already stale (20 vs 21 real);
> re-measured with a row-count control, **22 = 14 + 8**; §2's *"Nine"* is
> left for Step 2. Two more Stop-hook `proceed`→`block` specimens (log lines
> 421, 428); neither named a user request.

> **Session 300–301, 2026-09-15 (`a59b4cd` → `75cd580`) — THREE PRs
> ([#1489](https://github.com/CrayJThiemsert/vero-lite/pull/1489)–[#1491](https://github.com/CrayJThiemsert/vero-lite/pull/1491)), all merged. **PLAN-0125 Step 0
> shipped: the freshness guard now REFUSES a commit that stages
> `docs/STATUS.md` while drift > 0; every other commit still prints.**
>
> ✅ **s300 (no PR) — a host fix.** Windows git reads a `100755` file through
> the UNC mount as `100644`, and Claude's Edit rewrites `755` as `644`. Every
> `git init` writes a local `core.filemode = true` that beats global config
> and loses to command-scope env, so Cray set three Windows user env vars
> (`GIT_CONFIG_*` = `core.fileMode false`, host config); Code, on Cray's typed
> go, created a user-level `~/.claude/CLAUDE.md`. After the Desktop restart,
> s301's V1–V6 all PASS, the control included: with the vars stripped by
> `env -u`, both ` M` lines return. WSL still reads `local true`.
>
> ✅ **#1489 (merge `c98f82a`) — Lesson #0064**, *mute the reader that
> misreads, not the one that detects*: a `.git/config` `false` blinds WSL git
> (it hid the s256 `0600` bug), and a reinit under an inherited `GIT_DIR` flips
> it, witnessed `false → false (control) → true`. Plus Lesson #0007 §1.3
> (`wsl -e` inverts §1.1's escaping; PowerShell 5.1 drops embedded quotes) and
> the `claude-code-setup.md` §2 pre-flight; every reading they print was
> re-witnessed before writing, and each matched s300.
>
> ✅ **#1490 (merge `7089625`)** — the `ms-s1-ollama` skill said the repo turns
> mode tracking off; it reads `local true`. Corrected, with a `retired:` marker
> witnessed RED in a throwaway root; the real tree went 17 → 18 retired claims.
>
> ✅ **#1491 (merge `75cd580`) — PLAN-0125 Step 0.** Pass reads `A gate rc=1
> drift=2 · B gate rc=0 · C print rc=0 · D print rc=0 baseline_lag=n/a · E
> staged=True (control staged=False)`; battery
> `tests/batteries/plan-0125-step0.json` **27/27 WITNESSED, GAPS 0** (the
> PLAN's 12 probes, P-19.2, a parser control, 13 for pre-existing claims); full
> suite **5266 passed**; `mypy --strict` clean by hand. AC-17…AC-19 stay
> UNTICKED (closeout precedent). Code merged all three on Cray's typed word,
> each verified by number and blob.
>
> 🔴 **A recorded deviation and an instrument note.** (1) The guard reads the
> WHOLE staged set, not Step 0.1's pathspec query: with the pathspec, P-17.2
> and P-17.3 would redden the same case, so the PLAN's own probe list was
> inexpressible (§9: the ACs bind behaviour, not the query). (2) The
> retired-marker witness read 3 markers where Code expected 1: the instrument
> was Code's expectation (the skill already carried two); the count moved +1.
>
> ⚠️ The Step 0 commit's own pre-commit line printed **`baseline_lag=2`** —
> local `main` two commits behind `origin/main`, the lag the guard exists to
> show. Two more Stop-hook `proceed`→`block` specimens (log lines 399 and
> 411, `matched_rows` empty), so the candidates are now nine; neither named a
> task, and Code treated both as no-ops.

_[The Current-Focus rotation ledger's s301 entry, verbatim from `git show HEAD:docs/STATUS.md`:]_ 🔴 **THIS (s301) reconcile rotates ONE block — s298 (**2,347 B**, under the 4,096 B cap)** to `2026-h1e-current-focus.md`, probed ABSENT from every `-current-focus` letter first (control: the s297 header = 1). **Headroom rule:** STATUS opened at **57,867 B**, 7,669 B under R1's 65,536 B ceiling, and the s300–301 block had to land, so the window stays at TWO (299, 300–301) — the eleventh consecutive reconcile of that shape. ⚠️ **The s298 entry left the window and was APPENDED VERBATIM** after the block in h1e, not dropped on a token sweep.

_[The Current-Focus rotation ledger's s302 entry, verbatim from `git show HEAD:docs/STATUS.md`:]_ 🔴 **THIS (s302) reconcile rotates ONE block — s299 (**2,178 B**, under the 4,096 B cap)** to `2026-h1e-current-focus.md`, probed ABSENT from every `-current-focus` letter first (control: the s298 header from `e94b80e`'s own diff = 1). **Headroom rule:** STATUS opened at **59,549 B**, 5,987 B under R1's 65,536 B ceiling, and the s302 block had to land, so the window stays at TWO (300–301, 302) — the twelfth consecutive reconcile of that shape. ⚠️ **The s299 entry left the window and was APPENDED VERBATIM** after the block in h1e, not dropped on a token sweep.

### Rotated at the s307 reconcile — the session-303 Current-Focus block [on the R1 headroom rule: STATUS opened at **59,417 B**, and keeping the s303 block (**3,413 B**) beside the new s304–307 block was projected at ~62.8–63.1 KB, under the ≥ 3,000 B headroom margin s303 fixed, so the window stays ONE (304–307) instead of returning to TWO. Carved from `git show HEAD:docs/STATUS.md`, probed ABSENT from every `-current-focus` letter first against a control derived from the previous reconcile's own header (=1) and a fabricated s999 header (=0); absence from the new STATUS asserted separately (=0), with the new s304–307 block (=1) as the instrument's own control. The Current-Focus ledger's s303 entry follows it verbatim.]

> **Session 303, 2026-09-16 (`df5beb6` → `8b13e18`) — SEVEN PRs
> ([#1495](https://github.com/CrayJThiemsert/vero-lite/pull/1495)–[#1501](https://github.com/CrayJThiemsert/vero-lite/pull/1501)), all merged by Cray. **PLAN-0125 Step 2's
> staleness guard is live; PLAN-0126's fleet story explainer went draft →
> deployed → closed out in one window.**
>
> ✅ **#1496 (merge `8b13e18`) — PLAN-0125 Step 2.** `check_measure_staleness.py`
> re-seals every `measure/v1` block in `docs/logs/*.md`, re-runs every
> `rerun: true` procedure and resolves every `measure:<16hex>` cite; pre-commit
> hook `measure-staleness` (under `status-freshness`) gates `hash_bad`,
> `unresolvable`, `mismatch`, `rerun_failed`, `dangling`, `stale_cited`
> (SD-7 = b) and an empty surface — `stale` / `asserted` only print.
>
> 🔴 **Cray's two typed rulings, s303** (an addendum in PLAN-0125 §3.2, the
> original kept): **D1 = (a)** a failed re-run is its own counter
> `rerun_failed` — gating in a full repo, `unavailable` in a shallow clone;
> **D2 = (b)** staleness runs ADR-0038's `git diff <against_sha>..HEAD`
> verbatim **plus** `git diff HEAD`, since the re-run reads the working tree.
> The shallow half is measured: in CI's `fetch-depth: 2` checkout that same
> `git log <A>..<B>` exits 128 (control rc 0, 9 lines in a full worktree).
>
> ✅ **Evidence.** Battery `plan-0125-step2.json` **35/35 WITNESSED, claims 35,
> GAPS 0, exempted 0**; real tree `files=1 blocks=6 hash_bad=0 unresolvable=0
> stale=0 rerun=6 mismatch=0 rerun_failed=0 cites=5 dangling=0 stale_cited=0
> historical=5 asserted=16 rc=0`; AC-11 `runs=10 max_ms=96 min_ms=77` against a
> pre-fixed `max <= 2000`; `mypy --strict tools/` clean (51 files); CI PASS at
> `ff4b838`; post-merge by blob `files=6 sha_match=6 mismatch=0`, rc=0, 36
> green. **No PLAN-0125 AC is ticked** — AC-6…AC-11 and AC-20's Step 2 half are
> satisfied, but the ticks wait on the Step 5 closeout and Cray's ratification.
> ⚠️ `1 failed, 5301 passed, 8 skipped` — `test_db_guard_holds.py`'s
> terminated-holder case (`alive_post=1` after `pg_terminate_backend`),
> `services_touched=0`, 5/5 twice in isolation, s302's shape: a timing race.
>
> ✅ **PLAN-0126 — the fleet story explainer, draft to deployed in one window**
> (#1495 draft · #1497 ratified · #1498 Three.js pinned to the minified build ·
> #1499 Steps 0–8/10/11 · #1500 Step 9 · #1501 closeout; the other Code
> session's work, re-measured here). `/story/` is a static three-act explainer
> in the published console, deployed under Cray's typed per-phase go: AC-10
> `pre=404 post=200 csp=present`, **`DEMO-STATE: PRISTINE`** (log
> `docs/logs/2026-09-16-plan0126-fleet-story-deploy.md`); Step 9's Artifact
> `files=11 sha_match=11 rendered=yes`; batteries page 41/41, drift 15/15,
> scenario 10/10 WITNESSED. **PLAN-0126 AC-1 … AC-11 are CLOSED**, eleven of
> eleven ticked (`ticked=11 unticked=0` on main).
>
> 🔴 **AC-3 / AC-7 took option (C)** — re-point the artifact lists at the
> story-page tests **and** add the two missing witnesses, over relabelling
> alone: Check 3 of `check_ac_consistency.py` wants every named test module in
> a battery's `claim_sources`, and relabelling alone would leave two halves of
> AC-3's claim on greens no probe ever reddened. Shipped in #1501. **Still
> open:** #1502 moves the PLAN to `docs/plans/done/` — cite it by number (R8).

_[The Current-Focus rotation ledger's s303 entry, verbatim from `git show HEAD:docs/STATUS.md`:]_ 🔴 **THIS (s303) reconcile rotates TWO blocks — s300–301 and s302** to `2026-h1e-current-focus.md`; both are emitted VERBATIM in the scribe's return, neither is dropped on a token sweep. **Why two, where the last twelve rotated one:** STATUS opened at **61,736 B**, 3,800 B under R1's 65,536 B ceiling, and the dispatch fixed the pass read at **≥ 3,000 B of headroom once the s303 block lands**. Rotating a single block left an estimated margin under ~500 B — inside the error bar of an estimate this seat cannot check (no shell, so block sizes here are line-count arithmetic, not `wc -c`) — so the window drops to ONE for this reconcile and returns to TWO at s304. ⚠️ **The s301 and s302 entries left this ledger with the blocks they describe**, emitted verbatim with them.

### Rotated at the s308 reconcile — the session-304–307 Current-Focus block [on the R1 headroom rule: STATUS opened at **59,044 B**, and keeping the s304–307 block (**2,767 B**) beside the new s306 + s308 block would leave under the ≥ 3,000 B headroom margin s303 fixed, so the window stays ONE (306 + 308). Carved from `git show HEAD:docs/STATUS.md`, probed ABSENT from every `-current-focus` letter first against a control from the previous reconcile's own header (=1) and a fabricated s999 header (=0); absence from the new STATUS asserted separately (=0), with the new s306 + s308 block (=1) as the control. The Current-Focus ledger's s307 entry follows it verbatim.]

> **Sessions 304–307, 2026-09-16 (`8b13e18` → `29709f2`) — SIX PRs (#1502,
> #1504–#1508): four merged by Cray, #1506 and #1508 by auto-merge on green.
> PLAN-0125 Step 3's fact-pack contract is live; PLAN-0126 is archived.**
>
> ✅ **#1507 (merge `3c87522`, s307) — PLAN-0125 Step 3.** `tools/measure.py
> --recipe status-reconcile` emits the two `measure/v1` blocks a reconcile
> carries; each invocation re-enters the normal entry point (R1…R8, no
> exemption) and `--out` is refused, so §6 E1 is mechanical. The contract is in
> the three writer prompts (AC-13): `status-scribe` refuses prose, a bare SHA or
> a block missing `schema`/`hash`; `plan-drafter` has four grounding marks;
> `explore-research` never emits a block (SD-6 = b). 🔴 **§2.3's recipe as
> written emitted nothing** (`REFUSED R5` on `['main']`, then `['10']`); it now
> resolves the ref to a full SHA first, values unchanged, no refusal relaxed —
> §2.3 corrected in place, `was an error (mechanism)`: running the code caught
> it, the pipeline did not. Batteries: step-1 32 probes / 22 claims, step-3 5
> probes / 4 claims, both GAPS 0; AC-13 needles `pre=0 post=1` ×4; **5344
> passed, 8 skipped, 0 failed** (`db_tests=499`); CI PASS at `7e29e7a`. Two
> probe-battery traps recorded as lessons (per-module coverage; `ruff format`
> staled a probe key). AC-12/AC-13 evidenced, AC-14 is Cray's typed read, AC-15
> is this reconcile — **none ticked** (Step 5).
>
> ✅ **#1508 (s307) — option A, Cray typed.** The scribe prompt no longer deletes
> `Window = …` ahead of §6 E4's after-ratification sequence: never add one, never
> delete one on its own. New guard witnessed by P-13.5/P-13.6; step-3 battery 7
> probes / 5 claims, GAPS 0; CI PASS at `8159ca8`.
>
> 🔴 **#1506 (s306) — the stream-registry refresh (+55/−6) is not clean.** Four
> defects on main, each verified on `origin/main` against a control: (a) console
> counters `c24…c51` vs `index.html` `v=c52`; (b) row 1 names PLAN-0100 (0 STATUS
> hits); (c) row 4 lists the landing-layer PLAN, CLOSED s226 SUPERSEDED; (d) the
> needle `0[0-9][0-9][0-9]` also counts `ADR-0032` (a `done/0032-*` exists).
> Corrected by #1510 (Cray-approved, typed s306).
>
> ✅ **#1502 (s305)** PLAN-0126 ratified complete and archived (`done_hits=1
> active_hits=0`). **#1504 (the s303 chip session)** the DB-guard race:
> `pg_terminate_backend` returns on signal delivery, the lock frees at backend
> exit — a bounded 5 s `time.monotonic` wait, `db_guard` unchanged; s307's one
> 0-failure run is not proof the race is gone. **#1505** the notify scripts
> 100755 → 100644, blob oids unchanged. ⚠️ The DB-guard chip session's and
> s307's branches are named `s304`, a mislabel; branch names are immutable.

_[The Current-Focus rotation ledger's s307 entry, verbatim from `git show HEAD:docs/STATUS.md`:]_ 🔴 **THIS (s307) reconcile rotates ONE block — s303** to `2026-h1e-current-focus.md`, emitted VERBATIM in the scribe's return. **Why the window stays ONE, not the TWO s303 forecast:** STATUS measured **59,417 B** and the s303 block **3,413 B** (`wc -c`, Code); keeping s303 beside the new s304–307 block projects to roughly 62.8–63.1 KB, short of the ≥ 3,000 B headroom under R1's 65,536 B ceiling that s303 fixed. Active TODOs (**40,812 B**, 69% of the file) is what keeps forcing ONE. Every byte figure here is Code's measurement; this seat has no shell and estimated none. ⚠️ **The s303 entry left this ledger with its block**, emitted verbatim with it.


### Rotated at the s309 reconcile — Sessions 306 + 308 (2026-09-16 → 17)

> **Sessions 306 + 308, 2026-09-16 → 17 (#1508's merge → #1511's merge) —
> #1510 and #1511 merged (auto-merge, after review); #1512 and #1513 are open
> with CI PASS, both waiting on Cray. The stream registry is advisory;
> PLAN-0127 is drafted.**
>
> ✅ **#1510 (s306, auto-merged after review) — #1506's four defects corrected.** Cray
> ruled (typed, s306) that the four-stream registry in
> `.claude/skills/stream-status/SKILL.md` is **advisory**, resolving the s210
> question: rows are pointers only, with a reader-side check in the skill's
> step 2; R8 still reddens an archive move of any PLAN the table names
> (witnessed: exit 0 → 1). 🔴 **#1506's defects came from arming auto-merge
> before the adversarial review** — #1510 was reviewed first and landed clean.
> **#1511** (a chip session, the window's last merge) fixed the stale codegen
> docstrings in `cli.py` and `data_adapter.py`, and measured that the
> COMMITTED generated modules are imported (`persistence.py`, `spec.py`,
> `alembic/env.py`) and that procurement's hero demo builds the generated core
> `Person` from adapter rows.
>
> 🔴 **Cray's typed s306 rulings.** Codegen: `plan-drafter` drafts plan (A),
> PR-1 may open before it, and **(B) runtime adoption is NOT opened**. Story
> page: Act 1b stays; **live structuring is not ready — a top-priority
> discussion, never depicted**; the Act 5 label overlap is to be fixed, its
> redeploy under a per-phase go. The story-plan decisions are unanswered
> (In-Flight).
>
> ✅ **#1512 (s308, `fix/*`, head `b88d65a`) — PLAN-0127 PR-1: `emit_sql`
> orders `CREATE TABLE` by reference dependency.** As emitted, 6 of the 7
> ontology docs failed at statement 1 on Postgres, and no test had ever applied
> the DDL. Pre-fix `docs=7 applied=1 failed=6` → post-fix `docs=7 applied=7
> failed=0`; DB-free twin `docs=7 references=54 forward=0`; battery
> `plan-0127-pr1-ddl-order` 15 claims WITNESSED + 1 GREEN control, GAPS 0;
> 5354 passed, 8 skipped (before the last cosmetic edits; CI PASS on the head).
>
> ✅ **#1513 (s308, `docs/*`, head `5099742`) — PLAN-0127 `Draft`**, codegen
> generation stability (A): five PRs, no ADR. SD-1…SD-7 are Cray's; SD-2 is
> #1512's ordering mechanism, so countermand it before that merge. Its honesty
> ledger: **2 of the 7 outputs (TypeScript, context pack) cannot be proven
> correct without further Cray decisions.** Neither PR has auto-merge armed.

_[The Current-Focus rotation ledger's s308 entry, verbatim from `git show HEAD:docs/STATUS.md`:]_ 🔴 **THIS (s308) reconcile rotates ONE block — s304–307 (**2,767 B**, under the 4,096 B cap)** to `2026-h1e-current-focus.md`, emitted VERBATIM in the scribe's return; Code carves it from `git show HEAD:docs/STATUS.md` and probes it ABSENT from every `-current-focus` letter before appending. **Why ONE again:** STATUS opened at **59,044 B**, and keeping the s304–307 block beside the new s306 + s308 block projects past the ≥ 3,000 B headroom margin under R1's 65,536 B ceiling that s303 fixed. Active TODOs (**41,344 B**, 70% of the file) still forces it. Every byte figure here is Code's measurement. ⚠️ **The s307 entry left this ledger with its block**, emitted verbatim with it.
