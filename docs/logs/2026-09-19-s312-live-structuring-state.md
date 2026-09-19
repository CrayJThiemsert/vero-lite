# Live structuring — what it is, what is decided, and what is not

**Date:** 2026-09-19 · **Session:** 312 · **Event type:** rehome + state capture
**Author:** Claude Code (Tier 2) · **Tree:** `main` `9a7186cd`
**Why this file exists:** the term was **defined in no repository file**. Measured s312: ~16
mentions across STATUS, the archives and the handoffs, and **every one is governance wrapper**
("Cray's top-priority discussion", "NOT ready", "never depict it", "not booked") — not one says
what it *is*. This file is the tracked home, written before the stream is parked.

---

## 1. What it is

*Reconstructed by Code from the three named inputs, then **confirmed by Cray (typed, s312)**:
"ใช่ ประกอบถูก".*

Today the workshop is **paper and offline**. `2026-08-28-workshop-instrument-v1.md` is a 3-hour,
8-section interview you print and carry (*"พิมพ์เอกสารนี้ไป 1 ชุด + กระดาษ guess 1 แผ่น"*), and
the FDE program's phase-2 pass criterion is *"workshop notes → demo รันได้ใน **≤ 5 วัน**"* — the
system is built **afterwards**.

**Live structuring is that ≤5-day gap compressed to zero:** the customer's corrections land in
the ontology while they watch, and the vertical takes shape in the room.

It is not a new capability bolted on. The instrument is already built for it — Appendix A maps
every note field to a build artifact (object names + คำเรียก → `object_types` + `synonyms`;
the ก–ง authority levels → `llm_assist` / `action` + `autonomy: gated|auto`) — and
`2026-05-14-llm-driven-vertical-creation.md` calls the missing half **Layer 2**: requirements
conversation → LLM drafts YAML → engine validates and compiles.

## 2. Why Cray ruled it NOT READY (typed, s306) — and the tension is real

ADR-0032 **D1 element 3** binds the wedge to *"Run the deterministic offline arm. **No live-model
or network dependency in the room** — a hiccup cannot collapse the demo."*

A demo whose centrepiece is an LLM authoring YAML live contradicts that directly. And Layer 2 is
scheduled *"Phase 2 (months 4-6)"* with its own guard: *"NOT a justification for shipping Layer 2
in Phase 1."*

### The reframing that dissolves the tension (s312, Code — not yet ruled)

🔴 **Recorded here because it exists nowhere else.** ADR-0032 D1 already describes a re-runnable
live-structuring demo without anyone noticing:

> *"pre-build a **guessed** governed hero in the partner's own shape and ask them only to
> **correct** it"*

Put D1's own wedge together with element 3 and the live part is **the correction, not the
generation**:

1. pre-build the vertical from the ช่วง-0 guess sheet — committed, permanent
2. in the room the stakeholder says what is wrong (ช่วง 1's script: *"ผิดตรงไหนชี้เลย"*)
3. the corrections edit the ontology YAML
4. regenerate deterministically — the system changes in front of them
5. reset = `git checkout` the YAML + regenerate + `reset_demo_runs`

**No live model in the room. Re-runnable without limit.** And `verticals/building_materials/` is
already a guess-and-react vertical of exactly this kind — its ontology header reads
*">>> EVERY NUMERIC VALUE HERE IS A GUESS — เดา, รอแก้ <<< … the partner's 'correct me'
surface"*. The mechanism has a working precedent; it is not a new idea to prove.

### Replay, never delete — and what it depends on

`vero-lite new-vertical` *"requires the ontology at `verticals/<ns>/ontology/<ns>_v0.yaml` to
**exist first**"* (`cli.py:97`). The YAML is the only hand-authored input; everything downstream
is generated. So a re-demo **replays the derivation** instead of deleting the vertical — the
artifact stays (Cray: *"ไหนๆ ก็ทำแล้ว มันจะได้ของไว้ทำอะไรได้อีก"*) and the reset is a regeneration.

| what a re-demo must reset | exists? |
|---|---|
| run / case / audit state | ✅ `demo_run_reset.py::reset_demo_runs` (scoped by `OCT_VERTICAL`), `delete_case`, `demo_events.reset(vertical)` |
| the vertical itself | ❌ no teardown seam — **and none is needed if you replay** |

⚠️ **The replay mechanism rests on codegen determinism, which is being proven right now.**
PLAN-0127 **AC-5 / AC-11 / AC-12 are ticked** (#1512); **AC-1** (*"cross-process determinism,
every doc … all seven outputs byte-identical"*) and **AC-2** are **not**. If regeneration is not
byte-stable, the reset is not a reset. PLAN-0127 PR-2 therefore unlocks the demo, not just codegen.

## 3. What IS decided — do not re-decide

| Decided | Where | When |
|---|---|---|
| Four candidate cases, all fit-filter **4/4** | FDE program §4 | s259, 2026-08-28 |
| The dry-run pair and its order: **เคส 1 (เกตปล่อยงบยิงแอด) → เคส 4 (คอมเพลน→ชดเชย)** | FDE §4 | s259 — reason recorded: *"สองเคสรวมครอบตำแหน่ง LLM ทั้ง 3"* |
| Live structuring is **NOT ready**; never depict it on the story page or in a demo | A1 item 8 | s306, typed |
| The conversation fixture form: **transcript + filled notes, as a pair** | this session | s312, typed |

## 4. What exists on disk now

| Artifact | Path | Tracked? |
|---|---|---|
| Case-1 conversation fixture (transcript + filled 8-section notes + tier cases) | `docs/strategy/private/2026-09-19-dryrun-case1-adspend-conversation.md` | gitignored |
| The probe vertical built from it | `docs/strategy/private/adspend-probe/{adspend_v0.yaml,procedures.yaml}` | gitignored — **deliberately NOT under `verticals/`**, see the probe log |
| What the probe measured | `docs/logs/2026-09-19-s312-adspend-load-probe.md` | ✅ tracked (#1531) |

## 5. Open, and whose

| # | Open question | Whose |
|---|---|---|
| 1 | A time for the discussion itself (never booked since s306) | **Cray** |
| 2 | Should `docs/strategy/private/adspend-probe/` ever become a real `verticals/adspend/`? It would move the AT-2 signature census and turn CI RED **by design** — a governance act, not a build one (see the probe log) | **Cray** |
| 3 | Instrument **v2**: the five note-fields the fixture found missing (§6 below) | **Cray** — the instrument is his |
| 4 | Build the re-demo mechanism (replay + reset + the AC-1 dependency) | **PLAN-shaped → G2-gated → Cowork drafts** |
| 5 | เคส 4's fixture (different LLM position: classification on a closed enum; and it has real SoD) | Code, when asked |

## 6. The five gaps the fixture found in the instrument — the highest-value output so far

Full detail and the v2 wording proposal are in the fixture's §7. The sharpest:

🔴 **`watch_margin` has no note field at all.** ช่วง 2 asks for the normal band and the value at
the time of the incident — it never asks *"ก้ำกึ่งแค่ไหนถึงเริ่มไม่สบายใจ"*. But the entire tier
model rests on the watch band: `grader.classify_disposition` uses it to separate a deterministic
breach (auto-eligible) from an ambiguous `watch` (LLM proposes, human decides), and the fixture
contract is explicit that *"the ambiguity trigger is the engine's deterministic `watch` band,
**never** the LLM's `confidence`"*. Not asking it in the room means **we pick the margin ourselves
and it enters the system looking like the customer's number.** The fixture marks its 15% as
Code's proposal for exactly that reason.

The other four: no field for *why* a number moves (the customer volunteered "competitors bid up
the price"); a rolling-window definition would be mis-filed as a `rule_gate` instead of as the
measure's own definition; the form measures "seen → decided" but the ROI lives in "happened →
seen"; and the DOA base field is never pinned (here it is daily spend, **not** the monitored CPA).

## 7. What is NOT established

- **No model has ever done the conversation→YAML step.** The s312 probe authored the YAML by
  hand, from the fixture. It shows the target is reachable and where the tripwires are — it does
  not show a model can reach it.
- **The probe was never run** — no seeding, no DB, no `waiting_human`.
- **One case only.** เคส 4 is untouched.
- **The reframing in §2 is Code's, not ruled.** Cray has not typed on it.

## Reference

- `docs/strategy/private/2026-08-28-fde-readiness-program.md` (§2 phases, §4 the four cases, §5 architecture rules)
- `docs/strategy/private/2026-08-28-workshop-instrument-v1.md` (the 8 sections + Appendix A's field→artifact map)
- `docs/strategy/private/2026-05-14-llm-driven-vertical-creation.md` (Layer 2)
- `docs/adr/0032-...md` D1 (the wedge), D6 (the fit filter)
- `docs/logs/2026-09-19-s312-adspend-load-probe.md` (what the engine accepted and what governance refused)
