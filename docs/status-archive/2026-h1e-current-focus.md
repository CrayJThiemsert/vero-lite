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
