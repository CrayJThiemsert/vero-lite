---
last_updated: 2026-05-07
session: 5
state: stable
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

**Phase 1, Month 1, Session 5** — Memory architecture implementation + knowledge sync.

Active priorities:
1. Find 2–3 vet clinic design partners by month 3
2. Build YAML ontology + code generator (the moat)
3. Demo 5: 30-second onboarding (drop CSV → schema detected → answers in <30s)

## Recent Decisions (last 5)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-05-07 | `for_llm/` reframed as Tier 2.5 derived snippets (not canonical) | `docs/for_llm/README.md` |
| 2026-05-07 | Memory architecture: Hybrid (Auto Memory + Repository), Tier 0-3 model | `docs/runbooks/memory-architecture.md` |
| 2026-05-07 | CLAUDE.md slim refactor (Option C, ~7-8KB), extract conventions | Session 5 commit 3 |
| 2026-05-05 | Service port strategy: env-overridable with vendor defaults | ADR-003 |
| 2026-05-05 | Network topology + LLM model baseline | ADR-001, ADR-002 |

## In-Flight Discussions

- **ADR-004 (canonical email):** Currently using GitHub `users.noreply.github.com` alias. Decision deferred to Session 6.
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted.
- **Convention extraction:** `git.md` and `hardware.md` may be extracted in future commit (currently in CLAUDE.md).
- **Computer-use → WSL:** After Cowork + Claude Code setup, replace heredoc paste pattern with direct file writes via those tools.

## Active TODOs

- [ ] **ADR-004** — Decide canonical author email for `pyproject.toml` (currently using `users.noreply.github.com` alias)
- [ ] **PLAN-002** — Database setup with extensions (custom Postgres image)
- [ ] **ADR-005** — Custom Postgres image with pgvector + AGE + pg_trgm
- [ ] **PLAN-003** — Ontology Engine (`vet_clinic_v0.yaml` + code generator) — *the moat*
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (future commit)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (future commit)
- [ ] Cowork Project setup pointing to `~/work/vero-lite/` (Session 6 Task 3)
- [ ] Update Chat Project Knowledge upload (5 stable files) (Session 6 Task 1)
- [x] **PLAN-001** — Starter pack scaffold *(Session 4, completed)*
- [x] **ADR-003** — Service port strategy *(Session 4)*
- [x] **Memory architecture implementation** *(Session 5, commit 3)*

## Next Steps

1. (Session 6) Phase D-G — Pre-commit + commit + push for commit 3
2. (Session 6) Task 1 — Update Chat Project Knowledge upload
3. (Session 6) Task 3 — Cowork Project setup
4. (Session 6 Optional) ADR-004 canonical email discussion

## Update Workflow

This file is updated when:
- A commit changes project state significantly
- A new ADR/PLAN is minted or completed
- Active priorities shift
- A session closes (sync `last_updated` + `session` front-matter)

Manually edited at session boundaries. Not auto-generated.
