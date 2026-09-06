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
