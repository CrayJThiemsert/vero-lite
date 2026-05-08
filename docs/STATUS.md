---
last_updated: 2026-05-07
session: 7
state: stable
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

**Phase 1, Month 1, Session 7** — Chat Project Knowledge upload + Lesson #11 capture (post-commit-3 housekeeping).

Active priorities:
1. Find 2–3 vet clinic design partners by month 3
2. Build YAML ontology + code generator (the moat) — PLAN-003 not yet started
3. Demo 5: 30-second onboarding (drop CSV → schema detected → answers in <30s)

## Recent Decisions (last 5)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-05-07 | Lesson #11 documented (`uv run pre-commit` pattern) | `docs/lessons/0001-precommit-environment.md`, commit `1972b77` |
| 2026-05-07 | 5 stable files uploaded to Chat Project Knowledge (CLAUDE.md, STATUS.md, ADR-001/002/003) | Session 7 Task 1 |
| 2026-05-07 | `for_llm/` reframed as Tier 2.5 derived snippets (not canonical) | `docs/for_llm/README.md` |
| 2026-05-07 | Memory architecture: Hybrid (Auto Memory + Repository), Tier 0-3 model | `docs/runbooks/memory-architecture.md` |
| 2026-05-07 | CLAUDE.md slim refactor (Option C, ~7-8KB), extract conventions | Session 5 commit 3 (`1789a86`) |

## In-Flight Discussions

- **ADR-004 (canonical email):** Currently using GitHub `users.noreply.github.com` alias. Decision deferred to Session 8.
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted.
- **Convention extraction:** `git.md` and `hardware.md` may be extracted in future commit (currently in CLAUDE.md).
- **Computer-use → WSL:** After Cowork + Claude Code setup, replace heredoc paste pattern with direct file writes via those tools. **Claude Code is Session 8 priority.**

## Active TODOs

- [ ] **ADR-004** — Decide canonical author email for `pyproject.toml` (currently using `users.noreply.github.com` alias)
- [ ] **PLAN-002** — Database setup with extensions (custom Postgres image)
- [ ] **ADR-005** — Custom Postgres image with pgvector + AGE + pg_trgm
- [ ] **PLAN-003** — Ontology Engine (`vet_clinic_v0.yaml` + code generator) — *the moat*
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (future commit)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (future commit)
- [ ] Cowork Project setup pointing to `~/work/vero-lite/` (deferred from Session 6)
- [ ] Setup Claude Code on Windows (Session 8+ priority — enables direct file ops, replaces manual paste workflow)
- [x] **PLAN-001** — Starter pack scaffold *(Session 4, completed)*
- [x] **ADR-003** — Service port strategy *(Session 4)*
- [x] **Memory architecture implementation** *(Session 5, commit 3 `1789a86`)*
- [x] **Chat Project Knowledge upload** *(Session 7 Task 1, 5 files: CLAUDE.md + STATUS.md + ADR-001/002/003)*
- [x] **Lesson #11** — `uv run pre-commit` PATH trap *(Session 7 Task 1.5, commit `1972b77`)*

## Next Steps

1. (Session 8) Setup Claude Code on Windows — enables direct repo edits, replaces 3-patch manual paste pattern
2. (Session 8) ADR-004 canonical email decision (deferred from Session 6+7)
3. (Session 8 or 9) PLAN-002 draft — Database setup with pgvector + AGE + pg_trgm
4. (Session 9+) Begin PLAN-003 — Ontology Engine (the moat)

## Update Workflow

This file is updated when:
- A commit changes project state significantly
- A new ADR/PLAN is minted or completed
- Active priorities shift
- A session closes (sync `last_updated` + `session` front-matter)

Manually edited at session boundaries. Not auto-generated.
