# Story page (PLAN-0126 v1) — the reviewed plan and its open decisions

**Date:** 2026-09-19 · **Session:** 312 · **Event type:** rehome (preservation of an untracked artifact)
**Amended:** 2026-09-20 · **Session:** 313 · **Event type:** records the five D-decisions Cray ruled, and corrects two claims this file carried
**Author:** Claude Code (Tier 2)
**Commit:** the commit this file lands in
**Source, gitignored:** `.claude/handoffs/session-306/2026-09-17-1601-code-session306-CLOSE-registry-advisory-MERGED-codegen-planA-READY.md` §Appendix A (lines 179–277)
**Second source, gitignored:** `.claude/handoffs/session-309/2026-09-18-0238-code-session309-CLOSE-story-v2a-SHIPPED-plan0128-DRAFT.md` §5.3

---

## Why this file exists

`PLAN-0126` is closed and archived at `docs/plans/done/0126-fleet-story-mode-explainer.md`.
Its residue — five content decisions, four gates, a sole-source case, and a set of verified
findings about what the page may and may not claim — was written **only into a gitignored
handoff**, and `docs/STATUS.md` recorded that fact as a standing 🔴:

> 🔴 The plan exists only in the gitignored s306 CLOSE handoff (Appendix A) — no tracked home.

`.claude/handoffs/` is gitignored working notes. A single `rm`, a cleared worktree, or a
session that fails to carry the baton forward loses every decision below. Five sessions
(s306 → s311) have re-copied the *names* of these items between handoffs without the
content travelling with them; s312 measured that `.tag-synth` had already fallen out of
`docs/STATUS.md` entirely (0 occurrences) while still being carried as an open item.

This file is that tracked home. **It preserves; it does not decide.** Every ruling below is
Cray's, unchanged, and every "Code recommendation" is the recommendation as written at s306,
not a new one.

⚠️ **Amended at s313 (2026-09-20) — the sentence above still holds, and here is why.** This
file now carries Cray's **typed rulings on D-A…D-E** (Step 2) rather than only the open
questions. That is still preservation: the rulings are Cray's words, recorded on the day they
were typed, into the file that was already their home. Code decided nothing. Two things in the
file were also **corrected against the tree**, each marked in place rather than rewritten —
Step 4's "Cray runs the ship script", and Step 2's bundling clause. The s306 recommendation
column is kept beside the rulings on purpose: what was recommended, and whether the ruling
followed it, is part of the record.

### What this file is NOT

It is **not** a PLAN and must not be read as one. `CLAUDE.md` §6 routes a new PLAN through
Cowork under the G2 gate; `docs/logs/` is not a gated path, and this entry reaches it as a
**records action** — a faithful transcription of an artifact that already existed and had been
reviewed — not as governance authoring. **Whether this content should be promoted into a real
`docs/plans/NNNN-*.md` is Cray's call and is deliberately left open.** If it is promoted, the
promotion goes through Cowork like any other new PLAN.

It is also thicker than `docs/logs/README.md`'s "thin summary" model, because the detail it
preserves has no other tracked home. That tension is recorded here rather than papered over.

---

## Status of the story stream at the time of rehoming (measured, 2026-09-19, `main` = `d7b4db1e`)

| Step | State |
|---|---|
| Step 0a — STATUS reconcile | ✅ done (#1527, s311) |
| Step 0b — book the live-structuring discussion | ⏳ Cray picks the time; Code prepares inputs |
| Step 1 — story v2a (fixes only) | ✅ **shipped** (#1517, #1518) — on `main`, **not deployed** |
| Step 2 — content decisions D-A…D-E → v2b | ✅ **ALL FIVE RULED s313 (typed 2026-09-20)** — see Step 2 below; the build is not started |
| Step 3 — sole-source 4th case (G1) | ⏳ **blocked on Cray** (types the L5 amendment + the case's position) |
| Step 4 — deploy | ⏳ per-phase typed go (`CLAUDE.md` §8). ⚠️ **"Cray runs the ship script" is CORRECTED at s313** — it describes one refusal, not a rule. See the note under Step 4 |
| Step 5 — story v3 (primer, exec cut; G2–G5) | ⏳ waits on the live-structuring discussion |
| Last — G7 (rehome R9) | ✅ **RULED s312 — DONE**; R9 rehomed to `docs/strategy/public/intro-video-production-rulings.md` §2.2 + §7 |
| `.tag-synth` clean-mode position | ✅ **RULED s312** — move it up under `body.clean`; shipped in PR #1529 |

Separately closed and **not** to be reopened: the story `?v=` CI gap, closed by #1521 (s310) —
`tools/ci/cache_bust_diff_check.py` now discovers every `index.html` under
`services/api/static/` and locks the scope against a committed expectation.

⚠️ **Cross-stream interaction, measured s312 against the tracked PLAN** (`docs/plans/0128-probe-battery-claim-tags-and-generator-retirement.md` `:206`, `:210`, `:161`):
PLAN-0128 Step 3 migrates the three PLAN-0126 story batteries onto author-declared claim tags,
adds tag lines to `tests/api/test_story_page.py` / `test_story_drift.py` / `test_story_scenario.py`,
and deletes `tests/batteries/plan_0126_story_generator.py`, `tests/api/test_story_battery_generator.py`
and `tests/batteries/s309-story-battery-generator.json` in one commit. Its **AC-10 pins expected
values against today's page: page `43`, drift `14`, scenario `11`.** Step 2 (D-B) and Step 3 (G1)
below each **add probes**, so executing story content work and PLAN-0128 Step 3 in the wrong order
invalidates one of them. Sequencing is Cray's call; it is recorded here so it is not rediscovered.

---

## A1. Cray's typed items (2026-09-17)

| # | Item | Status |
|---|---|---|
| 1 | Scene 2's "จากโครงสร้างเดียว" is unclear; expand it, or explain it to Cray so Cray can narrate | request |
| 2 | "We agree to change the Act 5 overlapping labels, and it needs a redeploy" | **typed agreement**; deploy still needs per-phase go |
| 3 | Explain the 7 generated things ELI-30 | answered in chat |
| 4 | Add a NEW scene BEFORE Act 0: how an LLM works (human memory/language analogy), where it errs without context → why vero-lite | request; deferred to v3 |
| 5 | Can the `sole_source_justified` case be added to Act 4? | question; amends **L5** → gate G1 |
| 6 | Research tangible money KPIs from data along the flow | done (research) |
| 7 | Gloss the monospace secondary lines so a CFO isn't lost | request |
| 8 | **Act 1b stays** (CTO realism with existing data); **live structuring is NOT ready — top-priority discussion; never depict it** | **typed ruling** |

## A2. Verified findings (each checked against files at s306)

- **Live-page defect.** `services/api/static/story/story.js:487` sub-line read
  `fulfill · autonomy: gated · llm_assist: advisory`. In
  `verticals/fleet_maintenance/procedures.yaml` the **approve** step (≈388) carries
  `llm_assist: "draft the repair justification …"` and the **fulfill** step (≈405) has
  `llm_assist: null`. A hand-typed literal that no test pinned.
  *(Fixed in v2a / #1517, with the new drift test `test_llm_assist_steps_equal_the_loaded_procedure` + probes P4m/P4n.)*

- **Money captions that must NOT be used as first proposed:**
  - **"คำตอบอยู่ในแถวเดียว"** relies on the CSV export.
    `deploy/published/oct-fleet-maintenance/cloudflared/config.yml` (≈254–261): "THE COVER ONLY.
    The sibling `.csv` route is deliberately absent: Cray declined a UI button … at s192."
    **Not demonstrable on the published demo.**
  - **"ทุกบาทตอบได้"** implies 100%; the product reports a %. Use instead:
    "สิ้นเดือน แต่ละบาทถูกถามว่า ใครอนุมัติ · ซื้อจากใคร · ทำไม — และรายงานบอกว่าบาทไหนตอบไม่ได้".
  - **C7 emergency waiver "…ไม่งั้นขึ้นรายงาน"** is wrong: every waiver row is on the exception
    report, and an unsigned one past 7 days is labelled overdue. Also "7 days",
    `relaxes: three_bid` and `escalate_to` are **unpinned** — `waiver|ratification|window_days`
    has 0 hits in `story-data.js` and the story tests. Needs a drift pin, or no mechanism names
    or numbers.

- **Emitters.** Fleet's 7 generated outputs are gitignored reference files; no module imports
  them. Runtime reads the YAML directly (`nl_query.py:1328-1329`; `db_objects.py:64-73`), and a
  lockstep guard holds the hand-written DB tables to the YAML.
  🔴 **Forbidden claims:** "fleet runs on generated code", "the model calls MCP tools",
  "UI typed by types.ts", "the model reads the context pack".

- **Sole-source case.**
  - Feasible only as `illustrative: true`; the drift oracle calls the real `compute_three_quote`
    with `has_sole_source_justification`.
  - It **cannot** be the Pak Chong resolution: seed `synthetic.py:286-295` has เมย์ collecting
    three quotes, "honestly earned".
  - It is **not** the emergency waiver.
  - Runtime ≈1:56 → ≈2:05 (k ≈ 0.906 under `ACT4_MAX = 45`). The battery P8-count must be
    retargeted.

- **Act 5 overlap: root cause and fix.**
  - Cause: persona labels use a fixed pixel offset `dy: -28` (`story.js:375`) while the zone
    label sits at world `HY + 1.7` (`:381`), so they collide on the final dolly
    (camera ≈52 units out).
  - Fix: move the zone label in world space and/or `far ≤ 42` (the reviewer's figure; `far`
    62→50 still leaves op ≈ 0.33, visible).
  - Pre-committed read: `visible := visibility==='visible' && opacity >= 0.5`, selected by the
    five label texts; `pre >= 1` on v1, `post = 0`.
  *(Fixed in v2a / #1517.)*

- **Other findings:**
  - `test_story_page.py:256` `ai_tokens <= 1`: R3 is enforced by a test.
  - Placement conflict: rulings §2.3 prose says the explainer "opens the video", but the
    storyboard's beat-1 rules require the founder's face first, with no title.
  - R9 — see G7 below.

## A3. The reworked plan (after the REWORK review)

### Step 0 — no new decision needed, but unconfirmed

- **0a** `docs/*` STATUS reconcile. ✅ *done — #1527, s311.*
- **0b** Book the live-structuring discussion. Code prepares inputs (private
  `2026-08-28-workshop-instrument-v1.md`, `2026-08-28-fde-readiness-program.md`,
  `2026-05-14-llm-driven-vertical-creation.md`, ADR-0032 D1) and open questions for
  Cowork/Chat; **Cray picks the time.**

### Step 1 — `fix/*` "story v2a": fixes only, no new content ✅ SHIPPED (#1517, #1518)

- Act 5 overlap, using the read in A2.
- "ทุกการใช้เงิน" → "ทุกก้อนที่เกินเพดาน" (repairs under the per-truck ceiling never enter the
  chain; `procedures.yaml:224-237`). *Shipped as "ทุกก้อนที่ถึงหรือเกินเพดาน" — `judge` counts a
  quote **at or above** the ceiling as a breach (`procedures.yaml:227-231`).*
- Fix the `fulfill`/`approve` sub-line (A2).
- Tamper-evident gloss: "ถ้ามีใครแก้ย้อนหลัง ตรวจจับได้".
- **Cray decided at review:** the Act-0 synthetic label, in the storyboard's ruled wording
  "ข้อมูลสาธิต (synthetic) — กลไกจริง". It changes the first filmed frame.
  *Shipped in #1518 as a new `.tag-synth` element in the stage, not the chrome.*
- Mechanics: bump `story.js?v=` only; regenerate the batteries that embed it (page P2d,
  scenario P8b) and P5a/d/e if the tamper-evident sub changes; no timing change.

### Step 2 — Cray content decisions → `feat/*` "story v2b" ✅ ALL FIVE RULED s313

**Ruled by Cray, typed, 2026-09-20 (session 313), one decision at a time.** Each premise the
s306 recommendation rested on was **re-measured against the live tree first** (`CLAUDE.md` §6:
an inherited premise a decision rests on is a claim, not context). All five premises held;
two turned out **stronger** than s306 recorded, and one measurement changed a recommendation.
The s306 column is kept because a recommendation that was followed is still evidence about how
the thinking went.

| Decision | Cray's ruling (typed s313) | Code recommendation (s306) | What s313 measured |
|---|---|---|---|
| **D-A** money captions | ✅ **BOTH** the corrected "แต่ละบาท…" **and** "฿48,000 ยังไม่มีใครอนุมัติให้จ่าย จนกว่าจะเทียบราคาครบสามเจ้า". **"แถวเดียว" and "ทุกบาทตอบได้" are dropped** | first two; drop "แถวเดียว" | ✅ **confirmed — prior intact, and stronger.** `cloudflared/config.yml:257` still states the `.csv` route is deliberately absent (control: the `/story/` routes are present at `:62`), so "แถวเดียว" is undemonstrable on the published demo. And `services/api/static/assets/view-export.js:148-160` renders the KPI as `pct(traceable)` with the literal empty-state string `'no spend filed to this month — not 100%'` — **the product's own copy already refuses the 100 % claim**, which s306 argued from the product's behaviour rather than from this string |
| **D-B** emergency-waiver line | ✅ **include, with the drift pin.** The wording *"…ไม่งั้นขึ้นรายงาน"* is **rewritten** — it is factually wrong | include with the pin | ✅ **confirmed — prior intact, exactly.** The mechanism is real and complete at `verticals/fleet_maintenance/procedures.yaml:375-379` (`relaxes: [three_bid]`, `escalate_to: "เจ้าของกิจการ"`, `ratification_window_days: 7`), while the story side pins **none** of it: `story-data.js` = 0 hits and `test_story_{page,drift,scenario}.py` = 0/0/0 for `waiver\|ratification\|window_days` |
| **D-C** Scene 2 (item 1) | ✅ **expand the 35 s caption slightly** (not a new caption) **AND make `cap-sub` clickable in every act**, opening that act's Sources drawer | short + narrate | ⚠️ **the recommendation's framing was re-aimed.** The page does **not** currently overclaim: the 35 s caption says the system *generates* seven things, and `story.js:106`'s drawer note already reads *"ของ fleet ทั้ง 7 เป็นไฟล์อ้างอิง (gitignored) — commit เฉพาะของ energy/core"*. So item 1 is a **legibility** problem, not an honesty one. Cost, measured: `.caption` is `pointer-events:none` (`story.css:70`) and captions render via `textContent` (`story.js:851-852`), so a clickable **caption** would change the render model — `cap-sub` was chosen because it already carries the source pointer and generalises to all acts for one listener |
| **D-D** gloss "ดูได้ในระบบ:" (item 7) | ✅ **derive + pin + gloss, combined** — derive the drawer's numbers from `DATA`, **pin the result across the seam** against `procedures.yaml` / the ontology (witnessed RED by mutating the vertical), then write the CFO gloss. **Includes `ASSIST_SUB`** | pin first | 🔴 **s313 found a live specimen that changes the answer.** `tests/api/test_story_drift.py:39` reads **`story-data.js` only** — nothing reads `story.js`'s drawer prose, so `:85` ("object type 10 ชนิด · link type 7 เส้น · ref อีก 4 เส้น"), `:94` ("3 ตาราง"), `:105` ("emitter ทั้ง 7") and `:125` (the six step names) are a **second, unpinned copy of numbers that ARE pinned on the block side**. And the repo's one derive example is only ⅔ derived: `story.js:58` interpolates `ASSIST_STEP` and `autonomy` from `DATA` but leaves **`llm_assist: advisory` hand-typed** — the very field whose wrong value was the v1 defect. `advisory` appears **nowhere** in `story-data.js` and is pinned by **no** test. ⇒ derive and pin are **not redundant**: derive kills drift, pin kills wrong-field selection and leftover literals |
| **D-E** say "คู่ค้าต้นแบบ" on screen | ✅ **no — and locked as a ruling** (`intro-video-production-rulings.md` L7 + §3), so the question stops returning | no | ✅ **not previously decided** — `git grep` over the rulings file and this one returned only the D-E row itself. `index.html:14` already discloses `ข้อมูลสาธิต (synthetic) — กลไกจริง`, which covers **data** honesty; "คู่ค้าต้นแบบ" is a **commercial-status** disclosure, a different claim. The deciding argument is R9's shape: a fact stated on camera that **expires** is a reshoot, and "ยังไม่มีลูกค้าจริง" expires on the day it is least convenient |

**What the five rulings changed about the work itself — record this before planning:**

- 🔴 **v2b is no longer "a few caption edits".** D-C and D-D together are a genuine build:
  a new affordance on `cap-sub` (CSS + one listener), four derive sites in `story.js`, a
  cross-seam test that does not exist yet, its probes, and a mutation to witness each
  assertion RED. **The line below about bundling was written when v2b looked like text
  edits, and no longer describes the trade.**
- 🔴 **D-B and D-D each add probes**, so PLAN-0128's AC-10 pins (page `43`, drift `14`,
  scenario `11`) will move. Editing those values in an **`Accepted`** PLAN is **G1-gated**.
  The sequencing question at the head of this file is therefore sharper, not softer.
- **D-C and D-D interact and were ruled in that order deliberately:** making `cap-sub` a
  door into the Sources drawer raises how often the drawer is read, which raises the cost
  of the unpinned copies D-D then removes.

- ⚠️ Adding Act 5 captions **extends Act 5** (`start: 95, end: 105`; final camera key at 105):
  list the `end`, camera-key and act-nav changes explicitly, and design the overlap fix against
  the new timeline. *(Re-measured s313: `story.js:130` still reads `start: 95, end: 105`.)*
- ~~Bundle v2a + v2b into one deploy if decided within the week; otherwise v2a goes first.~~
  ⚠️ **SUPERSEDED BY NEW INFO at s313, not an error.** The clause assumed a small v2b. With
  D-C + D-D ruled as above, bundling holds the deploy — including the `.tag-synth` fix, which
  changes the **first filmed frame** and is already on `main`. **Bundle-or-split is now an open
  call for Cray**, alongside the ordering against PLAN-0128 Step 3.

### Step 3 — sole-source 4th case (G1) ⏳ OPEN

- **Cray types the L5 amendment and the case's position.**
- Record it FIRST (`docs/*`: rulings §2.3 dated note + §7 row), then `feat/*` P2.
- `test_story_drift.py` and `test_story_scenario.py` floors `>= 3` → `>= 4`, **one probe each**.
- Chip "มีเหตุผลเขียนไว้". Drawer: "ภาพประกอบกฎ — ไม่ใช่ run ใน seed และไม่ใช่วิธีที่เคสปากช่องถูกแก้ · ไม่ใช่ emergency_waiver".

### Step 4 — deploy A + Artifact + STATUS ⏳ OPEN

- Follow `deploy/published/oct-fleet-maintenance/DEPLOY.md`, adding what the reviewer found
  missing:
  - §2 `docker compose ls` stop condition + `docker image inspect` of the live tag;
  - §4 boot-log read + sibling containers;
  - record `:prev`;
  - edge pre/post reads on the **versioned** URL, with `cf-cache-status` recorded.
- Story-only change → no host `git pull` or connector recreate. **Establish this by the §2 diff,
  not by assumption.** ✅ **Established at s313, locally, before any host contact:** from the sha
  the host record says is live (`ea6944fa`) to `main` (`6e9bd2fe`) the diff is **7 files the image
  carries** — the four `story/` files plus `cli.py`, `code_generator.py`, `data_adapter.py` — and
  **0 files under `deploy/published/oct-fleet-maintenance/`**, so `cloudflared/config.yml` is
  unchanged ⇒ **no host `git pull`, no `--force-recreate cloudflared`**; only `app` is recreated.
  `merge-base --is-ancestor` = 0, so a fast-forward is available. (79 commits sit between the two
  shas; only these 7 files reach the image.)
- **Per-phase typed go** — `CLAUDE.md` §8 host-state rule. This is the standing requirement and it
  is unchanged.
- ⚠️ **CORRECTED at s313 — "Cray runs the ship script" was a workaround transcribed as a rule.**
  It is kept here rather than deleted, because the correction is the useful part:
  - **No governance source requires it.** `CLAUDE.md` §8 and `DEPLOY.md` §0 both require a typed
    **go**; neither names who may **run** the command. No repository hook denies `ssh` — the
    `PreToolUse`/`Bash` hooks in `.claude/settings.json` are `pretooluse_git_deny`,
    `pretooluse_loop_detect` and `pretooluse_ci_wait_deny` only. The project's own classifier row
    **C5** states the opposite of a ban: *"An explicit Cray go for the action IN THIS EXCERPT
    means the row does not fire."*
  - **Code has demonstrably run `ssh ms-s1` itself.** `docs/logs/2026-08-26-s256-ms-s1-readonly-deploy-census.md`
    records *"one `.ps1` piped over `ssh -o BatchMode=yes ms-s1`"* running `git` and `docker` on
    the host.
  - **Exactly one refusal is on record** — the 2026-09-16 deploy, where the **harness** auto-mode
    permission classifier (not a repo gate) refused both the §3 ship script **and the first
    read-only host read**, the same class of read Code had run at s256. Something in the harness
    tightened between 2026-08-26 and 2026-09-16.
  - ⚠️ **Not established:** who ran §3 at s239 / s246 / s256. Those records name no operator; only
    the 2026-09-16 record does, which is consistent with it being the exception — but that is an
    inference, not a measurement, and it is marked as one here.
  - **Cheapest way to settle it:** give the go for **§2 (read-only) alone**, which the deploy needs
    first regardless. If Code's host read runs, §3 very likely runs too; if it is refused, Cray runs
    §3 as before, at zero cost. 🔴 **Not probed at s313** — `DEPLOY.md` §0 gates read-only commands
    too, and testing the classifier means sending a command to the host.
- 🔴 **What genuinely needs Cray either way:** the per-phase typed go, and the **Cloudflare Access
  PIN** for the edge pre/post reads — `DEPLOY.md` §7 states no automated step can satisfy it.
- Artifact: republish to the same private URL (read it first; the URL is in Tier-0 memory
  `project_story_visualizer_rulings.md`). Record the new tree id.
- Reconcile STATUS afterwards.

### Step 5 — story v3, after the live-structuring discussion ⏳ WAITS ON 0b

- Primer version (i): 0 × "AI", 1 × "โมเดล", analogy
  "ผู้ช่วยที่อ่านข้อความมามหาศาล แต่เพิ่งมาถึงบริษัทคุณวันนี้", honesty-audited, 14-s short form
  possible. Version (ii) needs an R3 amendment plus a test change.
- An executive mode as an in-page toggle.
- Close line Z1: "ของจะถึงโคราชทันหรือไม่ อยู่ที่อู่กับถนน — …ทุกบาทของเคสนี้ตอบได้ว่า เทียบกับใคร ใครอนุมัติ ด้วยอำนาจอะไร".
  🔴 **Never promise arrival time.**
- Gates:
  - **G4** placement — recommend between beats 3 and 4.
  - **G3** primer in the video — recommend no (beat 2.5 covers it).
  - **G2** version — recommend (i).
  - **G5** exec cut as an in-page toggle.
- ⚠️ A pre-Act-0 scene re-times ≈25 absolute timestamps plus the `[0-6]` keys (`story.js:805`)
  and the `index.html:30` hint.

### Last — G7 (rehome R9) ✅ RULED s312 — DONE

A **reopening** of s247's "Cray ruled it acceptable". New info: the tracked rulings file reasons
from the void 140 s bound, and a tracked PLAN needs a citable R9.

✅ **Cray ruled (typed, s312, 2026-09-19): rehome it.** R9 now lives at
`docs/strategy/public/intro-video-production-rulings.md` §2.2, with its provenance in §7.

**What R9 actually says** — and it is more than the one-line summary this plan carried. Cray,
typed 2026-08-20 (s241), reason given as *"the content has to fit before the clock does"*:

1. the clip is **no longer bound to a runtime** — ~140 s is not a target, and the storyboard's
   per-beat times are **descriptive pacing estimates**;
2. 🔴 **nothing on camera may state a runtime.** This half is an **active filming constraint**,
   not a relaxation — a stated duration is a reshoot — and it was the part at risk of being
   lost entirely.

**What the gap had already cost, measured s312.** R9 was tracked in **no** repository file
between s241 and s312, so the rulings file went on reasoning from a bound Cray had voided, in
three places — §4.1's "buys back runtime R2 is short of", §5 item 1's slack argument, and §5
item 5, which said the explainer-vs-runtime conflict *"have to be reconciled by a later
ruling"* when **that ruling already existed and predated the entry by twenty-six days**. All
three are now corrected in place with markers, per that file's own amendment convention; no
ruling text was rewritten. The inventory line and the L-series disambiguation, which both
counted "R1–R8", are corrected too.

⚠️ R9 remains **gitignored at its origin** (the storyboard, 11 sites). The rehome copies the
ruling into a tracked file; it does not move the storyboard.

---

## The `.tag-synth` clean-mode position

*Transcribed from the s309 CLOSE handoff §5.3, which recorded it as "ONLY here, because no
tracked file carries the question". Verified against the code at s312.*

`.tag-synth` — the act-0 synthetic disclosure shipped in #1518 — sits at `top: 64px`
(`services/api/static/story/story.css:49`), which is the gap the page chrome occupies. In
ถ่ายทำ / clean mode the chrome is hidden, so the tag reads as inset from the top edge rather
than sitting at it. The clean toggle is real and reachable two ways:
`story.js:810` (`btn-clean`) and `story.js:818` (keyboard `h`).

✅ **RULED by Cray (typed, s312, 2026-09-19): move it up under `body.clean`.** Shipped in PR #1529
as `body.clean .tag-synth{top:var(--gutter)}` — one scoped rule, normal mode untouched.

⚠️ **"A one-line CSS change" was true of the CSS and false of the change.** Bumping
`story.css?v=c2 → c3` rots two *committed* battery anchors that quote the link tag verbatim —
`P6b` in `plan-0126-story-page.json` and `P8-set` in `plan-0126-story-scenario.json` — the s309
anchor-rot class exactly. The real change is five files: the CSS, the `?v=` bump, two spec-table
literals in `plan_0126_story_generator.py`, and the two regenerated batteries. **Never hand-edit
the JSON; regenerate.** Measured either side: lint `BROKEN (2 of 52)` naming exactly those two
probes, then `OK (52 batteries, 648 probes)` — counts unchanged, so nothing was lost or invented.

Verified in the browser, because no test pins a layout rule and a test reading `story.css` back to
itself would be vacuous: `body.clean` absent → computed `top: 64px`; present → `16px`; delta 48px;
`.chrome` `flex` → `none`; no inline `top` at any point. Exercised through both entry points and
reversed cleanly.

*Sequencing, as recorded before the ruling:* this affects the **first filmed frame**, so ruling it
before the Step 4 deploy cost nothing, where ruling it after would have meant a second deploy run —
the one step Code cannot perform.

---

## Reference

- Archived PLAN: `docs/plans/done/0126-fleet-story-mode-explainer.md` (Accepted; all seven SDs ruled)
- Deploy procedure: `deploy/published/oct-fleet-maintenance/DEPLOY.md`
- Prior deploy record, same system: `docs/logs/2026-09-16-plan0126-fleet-story-deploy.md`
- Cross-stream: `docs/plans/0128-probe-battery-claim-tags-and-generator-retirement.md` Step 3 / AC-10
- Operator-grade detail (gitignored): the s306, s309 and s311 CLOSE handoffs under
  `.claude/handoffs/session-306/`, `session-309/`, `session-311/`
- Story surface: `services/api/static/story/` · tests `tests/api/test_story_{page,drift,scenario}.py`
