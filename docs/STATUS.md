---
last_updated: 2026-05-19T14:04:00+07:00
session: 10
current_batch: plan004-batch1-tooling (DONE)
current_actor: chat (drafting Batch 2 dispatch); code (standby)
blocked_on: nothing
next_action: PLAN-004 Phase A Batch 2 retro-migration (~50 handoff files to schema; working-tree only + thin docs/logs/ summary per Lesson #5 §4)
head_commit: 7f5035f
recent_commits: [9afde79, 1ddd9b6, 3b86257, 5cdd6a1, 9a6aa98, b81817b, 96bf51b, 8d570b4]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

**Session 10 — PLAN-004 Phase A Batch 1 in flight; Batch 2 retro-migration queued next.**

Recent activity (post lesson-cleanup-v3 close 2026-05-18):

- **Lesson cleanup batch v3** (`96bf51b`, 2026-05-18) — 5-file batch
  closing the three-dispatch cycle (Lesson #3 amendment, Lesson #5
  §2/§3 amendment, Lesson #6 new, STATUS Q4 spec, chat_tab_instructions
  anchor protocol). Codified dual-layer prevention (durable +
  operational) for schema-fidelity discipline.
- **STATUS Q4 head_commit semantics** (additive in `96bf51b`) — defined
  newest substantive commit (excluding `^docs(status):` housekeeping);
  reader/writer recipes using `git log --invert-grep`.
- **PLAN-004 Phase A Batch 1 dispatched** (this batch, v2 re-dispatch
  after v1 Code midflight pause + Cray ratification of §10 Option B) —
  schema doc + tools (`tools/handoffs/{_schema,validate_handoff,handoff_status}.py`) +
  tests (≥14) + runbook cross-link + CLAUDE.md §10 widening
  (`docs/` → `docs/ + tools/`).

Next: PLAN-004 Phase A Batch 2 (retro-migrate ~50 handoff files to schema,
working-tree only + thin `docs/logs/` tracked summary per Lesson #5 §4).

## Recent Decisions (last 5)

| Date | Decision | Reference |
|------|----------|-----------|
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
- **Batch 4 (PLAN-003):** Ontology Engine implementation steps — first vertical `energy_v0.yaml` + code generator. Forthcoming.
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (see PLAN-001 line 9 forward-reference); ADR-005 has since been reused for the strategic pivot. The Postgres image ADR needs a fresh number (earliest available: ADR-009, post Batch 3's ADR-007/008).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [x] **ADR-007** — OCT engine contracts (DataAdapter, RecommendedAction, three-layer wiring) *(Session 10 Batch 3)*
- [x] **ADR-008** — YAML ontology specification (5 base types, JSON Schema validation) *(Session 10 Batch 3)*
- [x] **`.gitignore` extension** — add `docs/research/private/` (Cowork closeout flag #1) *(Session 10 Batch 3-prep)*
- [ ] **PLAN-003** — Ontology Engine implementation: `verticals/energy/ontology/energy_v0.yaml` (5 entities) + code generator — *the moat* *(Batch 4)*
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
- [ ] Lesson cleanup batch — Lesson #3 amendment (`.venv` incident findings 1-3 + environment observation), Lesson #5 §3 amendment (dispatch line-mapping gap), Lesson #6 new (Code-surface→Chat-redispatch pattern). Source: closeout `2026-05-16-1204` §6 + Code midflight `2026-05-18-1049` §4 item 2.
- [ ] PLAN-004 Phase A kickoff — gated on Cray Open Questions #2 (actor enum: include `cray`?) and #4 (status enum granularity 3 vs 5). Should fold `transcript` suffix + restart-bridge lifecycle taxonomy into Phase A spec.
- [ ] Adopt Q1(b) closeout-template line "STATUS.md updated: yes/no/N/A" — minor convention addition (no constitutional cost). Closeout drafters add the line; honor-system audit.
- [ ] Adopt Q3(b/c) dedicated `docs(status): …` housekeeping commit at batch close (this batch is the first instance; pattern locked).

## Next Steps

1. **Session 10 next batch — Lesson cleanup** (Lesson #3 amendment + Lesson #5 §3 amendment + Lesson #6 new — 3-file batch from `.venv` incident findings + dispatch line-mapping gap + Code-surface→Chat-redispatch pattern).
2. **Session 10 then — PLAN-004 Phase A kickoff** (handoff-frontmatter validator + schema + backfill — gated on Cray OQs #2 and #4).
3. **Adjacent** — Mint new ADR number for the parked Postgres image decision (≥ ADR-009).
4. **Ongoing** — Continue exercising file-based handoff mechanism (Chat ↔ Code, Project Knowledge transport) across batches; capture new traps as Lesson amendments or new lessons (Lesson cleanup batch is the next instance).

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
