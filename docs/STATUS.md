---
last_updated: 2026-05-08
session: 8
state: stable
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

**Phase 1, Month 1, Session 8** — Adopt Claude Code in Desktop (Code tab) for vero-lite; capture setup runbook and WSL ownership lesson.

Active priorities:
1. Find 2–3 vet clinic design partners by month 3
2. Build YAML ontology + code generator (the moat) — PLAN-003 not yet started
3. Demo 5: 30-second onboarding (drop CSV → schema detected → answers in <30s)

## Recent Decisions (last 5)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-05-08 | Adopted Claude Code in Desktop (Code tab) over CLI; documented setup runbook | `docs/runbooks/claude-code-setup.md` |
| 2026-05-08 | Lesson #12: Claude Code Desktop + WSL ownership trap (`safe.directory '*'` fix) | `docs/lessons/0002-claude-code-desktop-wsl-ownership.md` |
| 2026-05-07 | Lesson #11 documented (`uv run pre-commit` pattern) | `docs/lessons/0001-precommit-environment.md`, commit `1972b77` |
| 2026-05-07 | 5 stable files uploaded to Chat Project Knowledge (CLAUDE.md, STATUS.md, ADR-001/002/003) | Session 7 Task 1 |
| 2026-05-07 | `for_llm/` reframed as Tier 2.5 derived snippets (not canonical) | `docs/for_llm/README.md` |

## In-Flight Discussions

- **ADR-004 (canonical email):** Currently using GitHub `users.noreply.github.com` alias. Decision deferred to Session 9.
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted.
- **Convention extraction:** `git.md` and `hardware.md` may be extracted in future commit (currently in CLAUDE.md).
- **Direct file writes via Claude Code in Desktop:** Adopted in Session 8 — replaces the earlier heredoc paste pattern. Cowork was skipped (Code tab covers the in-repo workflow).

## Active TODOs

- [ ] **ADR-004** — Decide canonical author email for `pyproject.toml` (currently using `users.noreply.github.com` alias) *(deferred to Session 9)*
- [ ] **PLAN-002** — Database setup with extensions (custom Postgres image)
- [ ] **ADR-005** — Custom Postgres image with pgvector + AGE + pg_trgm
- [ ] **PLAN-003** — Ontology Engine (`vet_clinic_v0.yaml` + code generator) — *the moat*
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (future commit)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (future commit)
- [x] **PLAN-001** — Starter pack scaffold *(Session 4, completed)*
- [x] **ADR-003** — Service port strategy *(Session 4)*
- [x] **Memory architecture implementation** *(Session 5, commit 3 `1789a86`)*
- [x] **Chat Project Knowledge upload** *(Session 7 Task 1, 5 files: CLAUDE.md + STATUS.md + ADR-001/002/003)*
- [x] **Lesson #11** — `uv run pre-commit` PATH trap *(Session 7 Task 1.5, commit `1972b77`)*
- [x] **Setup Claude Code on Windows** *(Session 8, runbook `docs/runbooks/claude-code-setup.md`)*
- [x] **Cowork Project setup** — *not adopted; Code tab covers the in-repo workflow (Session 8 decision)*
- [x] **Lesson #12** — Claude Code Desktop + WSL ownership trap *(Session 8, `docs/lessons/0002-...`)*

## Next Steps

1. (Session 8 wrap-up) Phase F+G of Task 1 — review draft, commit, push runbook + Lesson #12 + STATUS update
2. (Session 9) ADR-004 canonical email decision (deferred from Session 6, 7, 8)
3. (Session 9) PLAN-002 draft + ADR-005 — Custom Postgres image with pgvector + AGE + pg_trgm
4. (Session 10+) Begin PLAN-003 — Ontology Engine (the moat)

## Update Workflow

This file is updated when:
- A commit changes project state significantly
- A new ADR/PLAN is minted or completed
- Active priorities shift
- A session closes (sync `last_updated` + `session` front-matter)

Manually edited at session boundaries. Not auto-generated.
