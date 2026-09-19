# Story page (PLAN-0126 v1) — the reviewed plan and its open decisions

**Date:** 2026-09-19 · **Session:** 312 · **Event type:** rehome (preservation of an untracked artifact)
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
| Step 2 — content decisions D-A…D-E → v2b | ⏳ **blocked on Cray** |
| Step 3 — sole-source 4th case (G1) | ⏳ **blocked on Cray** (types the L5 amendment + the case's position) |
| Step 4 — deploy | ⏳ **Cray runs the ship script**, per-phase typed go |
| Step 5 — story v3 (primer, exec cut; G2–G5) | ⏳ waits on the live-structuring discussion |
| Last — G7 (rehome R9) | ⏳ Cray's call; blocks nothing |
| `.tag-synth` clean-mode position | ⏳ Cray has seen the screenshot, has not ruled |

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

### Step 2 — Cray content decisions → `feat/*` "story v2b" ⏳ OPEN

| Decision | Options | Code recommendation (s306) |
|---|---|---|
| **D-A** money captions | corrected "แต่ละบาท…" (A2) / "฿48,000 ยังไม่มีใครอนุมัติให้จ่าย จนกว่าจะเทียบราคาครบสามเจ้า" / none | first two; **drop "แถวเดียว"** |
| **D-B** emergency-waiver line | include + drift pin (new `rules.emergency_waiver` block key + test + probe) / defer to v3 / no | **include with the pin** |
| **D-C** Scene 2 (item 1) | short caption + Cray narrates / longer caption | **short + narrate.** Honest framing: "ระบบอ่านกติกาจากไฟล์นี้ตอนทำงานจริง + guard กันโค้ด DB เบี่ยง"; **do not** claim the 7 are consumed for fleet (option (B) was not opened, so they stay reference files) |
| **D-D** gloss "ดูได้ในระบบ:" (item 7) | pin every receipt literal first (test vs procedures/code), then gloss / gloss only | **pin first** (the `fulfill` defect proves why) |
| **D-E** say "คู่ค้าต้นแบบ" on screen | yes / no | **no** |

- ⚠️ Adding Act 5 captions **extends Act 5** (`start: 95, end: 105`; final camera key at 105):
  list the `end`, camera-key and act-nav changes explicitly, and design the overlap fix against
  the new timeline.
- Bundle v2a + v2b into one deploy if decided within the week; otherwise v2a goes first.

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
  not by assumption.**
- 🔴 **Cray runs the ship script** (the auto-mode classifier refuses Code's `ssh ms-s1`).
  **Per-phase typed go** — `CLAUDE.md` §8 host-state rule.
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

### Last — G7 (rehome R9) ⏳ OPEN

A **reopening** of s247's "Cray ruled it acceptable". New info: the tracked rulings file reasons
from the void 140 s bound, and a tracked PLAN needs a citable R9. **Cray's call; it blocks
nothing on the page.**

---

## The `.tag-synth` clean-mode position

*Transcribed from the s309 CLOSE handoff §5.3, which recorded it as "ONLY here, because no
tracked file carries the question". Verified against the code at s312.*

`.tag-synth` — the act-0 synthetic disclosure shipped in #1518 — sits at `top: 64px`
(`services/api/static/story/story.css:49`), which is the gap the page chrome occupies. In
ถ่ายทำ / clean mode the chrome is hidden, so the tag reads as inset from the top edge rather
than sitting at it. The clean toggle is real and reachable two ways:
`story.js:810` (`btn-clean`) and `story.js:818` (keyboard `h`).

Moving the tag up under `body.clean` is a **one-line CSS change**. Cray has seen the screenshot
and **has not ruled**.

⚠️ **Sequencing:** this affects the **first filmed frame**. Ruling it *before* the Step 4 deploy
costs nothing; ruling it after means a second deploy run, which is the one step Code cannot
perform.

---

## Reference

- Archived PLAN: `docs/plans/done/0126-fleet-story-mode-explainer.md` (Accepted; all seven SDs ruled)
- Deploy procedure: `deploy/published/oct-fleet-maintenance/DEPLOY.md`
- Prior deploy record, same system: `docs/logs/2026-09-16-plan0126-fleet-story-deploy.md`
- Cross-stream: `docs/plans/0128-probe-battery-claim-tags-and-generator-retirement.md` Step 3 / AC-10
- Operator-grade detail (gitignored): the s306, s309 and s311 CLOSE handoffs under
  `.claude/handoffs/session-306/`, `session-309/`, `session-311/`
- Story surface: `services/api/static/story/` · tests `tests/api/test_story_{page,drift,scenario}.py`
