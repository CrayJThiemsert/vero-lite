---
last_updated: 2026-05-20T18:35:00+07:00
session: 10
current_batch: plan003-phase1-kickoff (engine implementation merged; closeout + trial-protocol §7.3 adjudication pending)
current_actor: code (closed plan003-phase1; trial closeout for Cray)
blocked_on: nothing
next_action: PLAN-003 Phase 1 closeout handoff with trial-protocol §7.3 (a)/(b)/(c) adjudication input
head_commit: 30619b8
recent_commits: [30619b8, 81ea262, f7bbacf, 21308d9, cdde75c, ea5f73e, 08117cf, 0f392ba, 9572b81, a7c68a2]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

**Session 10 — PLAN-003 Phase 1 LANDED (the moat ships; ontology engine + first vertical).**

- **PLAN-003 Phase 1 merged (`30619b8`):** 7 commits on
  `feat/plan003-phase1-ontology-engine`; PR #2 merged to `main`. Lands:
  - `services/engine/` package — `errors.py` (frozen-dataclass error
    hierarchy mirroring `tools/handoffs/_schema.py`),
    `ontology_schema.json` (ADR-008 D2 grammar JSON Schema draft
    2020-12), `ontology_validator.py` (L1+L2 with ruamel.yaml line:col
    diagnostics), `code_generator.py` (5 emitters), `cli.py` (Typer
    `validate` + `generate` commands)
  - First vertical: `verticals/energy/ontology/energy_v0.yaml` —
    6 object_types (5 base + AlertEventLink join object per ADR-008 D4)
    + 7 link_types in ADR-008 D2 grammar
  - L1 commit-time gate: `check-jsonschema` pre-commit hook on
    `verticals/*/ontology/*.yaml`
  - Entry-point: `.venv/bin/vero-lite` shell command
  - 24 engine tests; total suite 58 passed; coverage **94.06%**
    (target ≥70% aspirational — far exceeds)
  - `verticals/*/generated/` gitignored (resolves dispatch R-K4)
- **Cowork-Tier-1 trial test-bed:** Phase 1 dispatch authored by
  Cowork-as-Tier-1 per the trial protocol; Code's R2 pre-execution
  veto-check passed (C1=0); content quality HIGH (Cowork promoted
  F-3 ADR↔plan grammar divergence to binding R-K1 resolution).
  Mid-execution C4 measured 0 (no Lesson #6 firings during commits
  1-7). C3 carries 2 (Cowork-sandbox bash UNC + `.claude/` Write
  block — surfaced pre-execution, not new). C2 = 0 inside execution
  (Code-automated `cp` of Cowork output to canonical did not count
  per protocol §5 amendment). Full trial-criteria adjudication in
  the closeout — Cray decides §7.3 (a) re-trial / (b) accept /
  (c) fallback.
- **Carried-forward J-class observations** (advisory, not blocking):
  J-1 `int → BIGINT` in SQL emitter follows PLAN-003 §6.2 binding
  spec; ADR-008 D3 narrative literally says `INTEGER` — minor
  divergence (BIGINT is the safer Postgres default). J-2 `next()`
  Python builtin tripped PD-5 wording grep as false positive;
  mitigated by rewriting the test to use a dict-by-name lookup.
- **PLAN-004 Phase B/C remains deferred** per Cray Option-1
  (2026-05-20).

Next: Phase 2 starts after Cray adjudicates the trial-protocol §7.3
question. Phase 2 scope (DataAdapter Protocol + RecommendedAction
runtime + three-layer wiring) is laid out in PLAN-003 §3.3.

## Recent Decisions (last 5)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-05-20 | **PLAN-003 Phase 1 merged** (PR #2) — `services/engine/` package + 5 emitters + `verticals/energy/ontology/energy_v0.yaml` (ADR-008 D2 grammar; 6 object_types + 7 link_types) + L1 commit-time gate + `vero-lite` entry-point; 24 engine tests; coverage 94.06%; ADR-008 D2 binding per dispatch R-K1; PLAN-003 §8.6 list-of-dicts illustration is REJECTED at L1 (schema-fidelity guarantee) | `30619b8` |
| 2026-05-20 | PLAN-003 Phase 1 kickoff dispatch authored by Cowork-as-Tier-1 (trial test-bed); Code R2 pre-execution PASS; mid-execution C4=0 (no Lesson #6 firings during commits 1-7); trial-protocol §7.3 adjudication queued for Cray | `.claude/handoffs/session-10/2026-05-20-1530-cowork-plan003-phase1-kickoff-dispatch.md` |
| 2026-05-20 | PLAN-003 plan doc landed — `docs/plans/0003-ontology-engine.md` (427 lines); Phase 1 only (5 emitters: Pydantic+SQL+JSON Schema+MCP+TS-light); Typer CLI + ruamel.yaml parser + jsonschema; Alert↔OperationalEvent via explicit join object type (ADR-008 D4 stays; `many_to_many` deferred); coverage ≥70% aspirational (R-8); 3 J-class surfaces logged in dispatch closeout | `a7c68a2` |
| 2026-05-20 | PLAN-004 Phase A Batch 2 COMPLETE — Step 2a (20 files) + 2b.1 (12 renames + ref-graph, 5-ratification surface→re-dispatch chain) + 2b.2 (post-recovery, single-pass). Handoff-class schema-FAIL = `{}` | `ad81e7e` (2b.2 anchor), `098f8cd` (2b.1), `7f5035f` (2a) |
| 2026-05-20 | Strategic pivot — Option-1: pause PLAN-004 Phase B/C, prioritize PLAN-003 (Ontology Engine = the moat) | Cray decision 2026-05-20 |
| 2026-05-20 | Chat dispatch tooling/schema pre-verification protocol codified (operational layer; durable Lesson #8 mint deferred post-Phase-A per Q3=A) | `be38bce` `docs/conventions/chat_tab_instructions.md` |
| 2026-05-19 | PLAN-004 v2 Phase A Batch 1 landed | Schema doc + tools/handoffs/{_schema,validate_handoff,handoff_status}.py + ≥14 tests + runbook cross-link + CLAUDE.md §10 widening (docs/ → docs/ + tools/, Option B per Code midflight) | `9afde79` |
| 2026-05-17 | §11 Transcript Handoff ratified — Lesson #5 §2 "Cray-direct constitutional codification path" sub-rule + runbook §4 refresh + runbook §2 helper | `8d570b4` |
| 2026-05-16 | CLAUDE.md §11 "Transcript Handoff" constitutional subsection promoted — first instance of Cray-direct codification path (Lesson #5 §2 sub-rule) | `dd65d9b` |
| 2026-05-16 | Transcript tooling + runbook landed — `tools/handoffs/render_transcript.py` (stdlib-only, mypy-strict) + tests + `docs/runbooks/transcript-handoff.md` | `98e5591` |
| 2026-05-16 | Lesson-numbering offset sweep — `Lesson #12/#13/#14` → `#2/#3/#4` across repo (full normalization) | `c85a595` |
| 2026-05-16 | Lesson #5 audit baseline applied — `docs/lessons/0005-tier-system-audit-2026-05-15.md` (10 findings, tier-system audit); in-repo references normalized | `8274a66` |
| 2026-05-15 | Governance mini-batch — CLAUDE.md §1 precedence + §6 4-tier table + §11 Tier 2 ops; `docs/conventions/{chat,cowork}_tab_instructions.md` canonicalized | `ac3baf3` |
| 2026-05-13 | ADR-007 (OCT engine contracts) + ADR-008 (YAML ontology specification) — both Accepted | `docs/adr/0007-oct-engine-contracts.md`, `docs/adr/0008-yaml-ontology-specification.md` |
| 2026-05-13 | Cowork Tier 0 first deliverable — Palantir Foundry ontology reference brief (validates ADR-008's 4-tier model; cited from ADR-008 §Context as influencing reference) | `docs/research/private/2026-05-13-palantir-ontology-reference.md` |
| 2026-05-11 | ADR-006 — Vertical Plugin Architecture (D1–D4 + 5 core patterns; template-first multi-vertical) | `docs/adr/0006-vertical-plugin-architecture.md` |
| 2026-05-11 | ADR-005 — Strategic Pivot from SMB vet clinic to Operational Control Tower (vet clinic parked as Phase 2) | `docs/adr/0005-strategic-pivot-to-oct.md` |
| 2026-05-10 | ADR-004 closed — GitHub noreply alias as canonical author email (provisional) | `docs/adr/0004-canonical-author-email.md` |
| 2026-05-10 | Worktree mode policy codified in CLAUDE.md §6 (per Lesson #3) | `CLAUDE.md` §6 |
| 2026-05-10 | Handoff rotation policy codified in runbook | `docs/runbooks/claude-code-chat-handoff.md` |

## In-Flight Discussions

- **Batch 3 (ADR-007 + ADR-008):** Both **Accepted 2026-05-13** — OCT engine contracts + YAML ontology specification (5 base types, JSON Schema validation). Cowork Tier 0 brief at `docs/research/private/2026-05-13-palantir-ontology-reference.md` cited from ADR-008 §Context; 5 open questions in the brief remain candidates for future ADR amendments.
- **Batch 4 (PLAN-003):** Ontology Engine — **Phase 1 MERGED (`30619b8`, PR #2).** Plan doc: `docs/plans/0003-ontology-engine.md`. Phase 1 shipped: 5 emitters (Pydantic + Postgres DDL + JSON Schema + MCP tool-defs + TypeScript light) + `verticals/energy/ontology/energy_v0.yaml` (6 object_types in ADR-008 D2 grammar) + Typer CLI + 24 engine tests (coverage 94.06%). Phase 2 (DataAdapter + RecommendedAction runtime + three-layer wiring) deferred to a later batch.
- **Cowork-Tier-1 trial:** Phase 1 was the test-bed; trial-criteria scorecard pending Cray §7.3 (a)/(b)/(c) adjudication in the closeout.
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (see PLAN-001 line 9 forward-reference); ADR-005 has since been reused for the strategic pivot. The Postgres image ADR needs a fresh number (earliest available: ADR-009, post Batch 3's ADR-007/008).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [x] **ADR-007** — OCT engine contracts (DataAdapter, RecommendedAction, three-layer wiring) *(Session 10 Batch 3)*
- [x] **ADR-008** — YAML ontology specification (5 base types, JSON Schema validation) *(Session 10 Batch 3)*
- [x] **`.gitignore` extension** — add `docs/research/private/` (Cowork closeout flag #1) *(Session 10 Batch 3-prep)*
- [ ] **Phase-enum amendment** — add `consultation` (or equivalent Q&A-round value) to canonical Phase enum (Q15 of `2026-05-20-0245-code-plan003-pre-draft-consultation-reply.md`); requires touching `tools/handoffs/_schema.py` + `docs/conventions/handoff-frontmatter-schema.md` + validator tests; PLAN-004 Phase B adjacent. *(Deferred per R-9, 2026-05-20)*
- [ ] **Cleanup stale `ontology/README.md`** — 2026-05-05 PLAN-001 artifact; ontology directory canon now lives at `verticals/<name>/ontology/<name>_v0.yaml` per ADR-006 D1 / ADR-008 D5; superseded by PLAN-003. *(Deferred per R-9 cohort, 2026-05-20)*
- [ ] **PLAN-004 Phase B/C — DEFERRED (backlog, post-PLAN-003):** validator-scope exclusion (`README.md` / `_rename-map.md`, manifest §4.2/§6.1) + Cat G `references_*` autofix + Phase C handoff dashboard + OQ-2 systemic candidate (effective-vs-authored `status:` / archival flag so dead handoffs don't surface as actionable in the dashboard)
- [ ] **ADR-NN (TBD, ≥ ADR-009) + PLAN-002** — Custom Postgres image with extensions (renumbered after ADR-005 reused for strategic pivot)
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (low priority)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)
- [ ] Filesystem cleanup: `wsl -u root -- rm -rf .claude/worktrees/sad-northcutt-6a48ff/` (cosmetic, no rush)
- [x] **ADR-006** — Vertical Plugin Architecture *(Session 10 Batch 2)*
- [x] **ADR-005** — Strategic Pivot to OCT (vet clinic parked Phase 2) *(Session 10 Batch 2)*
- [x] **Directory scaffolds** — `verticals/{_template, energy, supply_chain, vet_clinic}/` + `docs/strategy/{public, private}/` *(Session 10 Batch 2)*
- [x] **Parked-note pass** — 6 vet-mentioning docs annotated *(Session 10 Batch 2)*
- [x] **ADR-004** — Canonical author email (GitHub noreply, provisional) *(Session 10)*
- [x] **Worktree mode policy** — codified in CLAUDE.md §6 *(Session 10)*
- [x] **Handoff rotation policy** — codified in runbook *(Session 10)*
- [x] **Phase G** — commit + PR + merge + cleanup *(Session 9)*
- [x] **Lesson #2 amendment** — Misdiagnosis section *(Session 9)*
- [x] **Lesson #3** — Code Tab worktree lifecycle traps *(Session 9)*
- [x] **File-based handoff mechanism** — `.claude/handoffs/` live *(Session 9)*
- [x] **Setup Claude Code on Windows** *(Session 8)*
- [x] **Cowork Project setup** *(Session 8)*
- [x] **PLAN-001** — Starter pack scaffold *(Session 4)*
- [x] **ADR-003** — Service port strategy *(Session 4)*
- [x] **Memory architecture implementation** *(Session 5)*
- [x] Lesson cleanup batch — Lesson #3 amendment + Lesson #5 §2/§3 amendment + Lesson #6 new *(done `96bf51b`, 2026-05-18)*
- [x] **PLAN-004 Phase A** — Batch 1 (schema + tools) + Batch 2 (2a: 20 files / 2b.1: 12 renames + ref-graph / 2b.2: post-recovery) complete *(Session 10, 2026-05-19/20; anchor `ad81e7e`)*
- [x] **PLAN-003 Phase 1** — Ontology engine + 5 emitters + `energy_v0.yaml` + L1 commit-time gate *(Session 10, 2026-05-20; merge `30619b8`, PR #2)*
- [x] Adopt Q1(b) closeout-template line "STATUS.md updated: yes/no/N/A" — adopted (closeouts carry the line)
- [x] Adopt Q3(b/c) dedicated `docs(status): …` housekeeping commit at batch close — adopted (`894a1e5` first instance; this 2b.2 close repeats)

## Next Steps

1. **PLAN-003 Phase 1 closeout + trial-protocol §7.3 adjudication** — Code authors the closeout with trial-criteria scorecard (C1, C2, C3, C4); Cray decides §7.3 (a) re-trial / (b) accept Cowork-as-Tier-1 + execute next batch / (c) fall back to Chat-as-Tier-1.
2. **PLAN-003 Phase 2** — DataAdapter Protocol + RecommendedAction runtime + three-layer wiring + first end-to-end action loop (read → recommend → approve → execute). Scope laid out in PLAN-003 §3.3. Kicks off after Cray adjudicates the trial question.
3. **Deferred (backlog)** — PLAN-004 Phase B (validator-scope exclusion for `README.md`/`_rename-map.md`; Cat G `references_*` autofix) + Phase C (handoff dashboard) + OQ-2 systemic candidate.
4. **Adjacent** — Mint new ADR number for the parked Postgres image decision (≥ ADR-009).
5. **Ongoing** — Continue exercising file-based handoff mechanism (Chat ↔ Code ↔ Cowork) across batches; pre-verification protocol governs all future data-transformation dispatches.

## Update Workflow

This file is updated when:
- A commit changes project state significantly
- A new ADR/PLAN is minted or completed
- Active priorities shift
- A batch closes (sync `last_updated` + `current_batch` + `head_commit` + `recent_commits` frontmatter)
- A session closes (sync all frontmatter fields; archive batch history if needed)

**Update mechanism (locked per STATUS staleness batch 2026-05-18, Hybrid A+B short-term, C long-term):**

- **Per closeout (Option A + Q1(b) discipline):** Closeout drafter includes the line "STATUS.md updated: yes / no / N/A" in their closeout. If `yes`, the closeout's commit batch should include a dedicated `docs(status): …` housekeeping commit (Q3(b/c) pattern) bumping at minimum the `last_updated` and `head_commit` frontmatter fields.
- **Per batch boundary (Option B full body):** Full body refresh (Current Focus + Recent Decisions + Active TODOs + Next Steps) at batch close, alongside the frontmatter bump.
- **Per session boundary:** Full body + frontmatter sync; consider archive of prior session's batch history.
- **Future (Option C, PLAN-004 Phase A):** Validator will flag stale STATUS.md by comparing **frontmatter `last_updated` field** against newest closeout's `created` timestamp (NOT file mtime — mtime is defeated by side-effect commits, e.g. `c85a595` 2026-05-16 normalization sweep that touched STATUS.md body without bumping `last_updated`).

**Q4 `head_commit` semantics (codified 2026-05-18, locked Cray ratification of midflight `2026-05-18-1049` §4 + closeout `2026-05-18-1202` §6.2):**

- `head_commit` = short SHA of the newest **substantive** commit on
  `origin/main` that STATUS.md content reflects.
- **Excluded from `head_commit`:** `docs(status): …` housekeeping
  commits. These commits encode no new repo state — they ARE the
  STATUS.md freshness marker. Including them in `head_commit` creates
  a self-defeat where every housekeeping commit makes STATUS.md appear
  "fresh" to Q4 detection regardless of substantive backlog.
- **Substantive (included in `head_commit`):** everything else —
  `docs(lessons):`, `docs(adr):`, `docs(runbook):`, `feat:`, `fix:`,
  `chore:` (when changing meaningful state), `refactor:`, `test:`, etc.
  Any commit type that changes durable repo content updates
  `head_commit` at the next STATUS.md edit.
- **Reader recipe (returning after a pause):**

  ```bash
  # Newest substantive commit on origin/main (the value head_commit should hold)
  git log -1 --format=%h --invert-grep --grep='^docs(status):' origin/main

  # Compare to STATUS.md head_commit field
  grep -E '^head_commit:' docs/STATUS.md
  ```

  If the two differ → STATUS.md content is stale relative to substantive
  repo state. If they match → STATUS.md is fresh.

- **Writer rule (at each STATUS.md update):** Set `head_commit` to the
  output of `git log -1 --format=%h --invert-grep --grep='^docs(status):' origin/main`
  *after* the substantive commits of the current batch land but *before*
  any `docs(status):` housekeeping commit (or, if the STATUS.md edit
  itself is in a substantive commit like `docs(lessons):`, set
  `head_commit` to that substantive commit's own SHA — which becomes
  knowable only post-commit, so the writer typically updates
  `head_commit` to the *most-recent prior substantive commit* and lets
  the next batch's first edit catch up).
- **Two failure modes this rule closes:**
  1. **mtime trap** (closeout `2026-05-18-1202` §2): side-effect commits
     that touch STATUS.md body without bumping `last_updated` (e.g.
     `c85a595` 2026-05-16 normalization sweep) leave the file mtime-fresh
     but semantically stale. A SHA in `head_commit` cannot drift this way.
  2. **Housekeeping self-defeat** (closeout `2026-05-18-1202` §6.2 +
     midflight `2026-05-18-1049` §4): if `head_commit` = own SHA, every
     `docs(status):` commit makes Q4 say "fresh" regardless of
     substantive backlog. Excluding `^docs(status):` from the comparison
     baseline closes this loophole.

Manually edited until Option C lands.
