---
last_updated: 2026-05-09
session: 9
state: stable
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

**Phase 1, Month 1, Session 9** — Phase G complete (PR #1 merged), Lesson #13 captured, file-based Code↔Chat handoff mechanism live.

Active priorities:
1. Find 2–3 vet clinic design partners by month 3
2. Build YAML ontology + code generator (the moat)
3. Demo 5: 30-second onboarding (drop CSV → schema detected → answers in <30s)

## Recent Decisions (last 5)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-05-09 | Lesson #13 — Code Tab worktree lifecycle traps (3 families, 7 traps) | `docs/lessons/0003-code-tab-worktree-lifecycle-traps.md` |
| 2026-05-09 | File-based Code↔Chat handoff mechanism (`.claude/handoffs/`) | `docs/runbooks/claude-code-chat-handoff.md` |
| 2026-05-09 | Lesson #12 amendment — Misdiagnosis section (2-store gitconfig, UNC binding) | `docs/lessons/0002-claude-code-desktop-wsl-ownership.md` |
| 2026-05-09 | PR workflow standardised (merge commit + delete branch for future-proofing) | PR #1, commit `e69e31a` |
| 2026-05-08 | Claude Code in Desktop adopted, runbook + Lesson #12 captured | `docs/runbooks/claude-code-setup.md` |

## In-Flight Discussions

- **ADR-004 (canonical email):** Deferred 4 times across Sessions 6/7/8/9. **Must close in Session 10 — no more deferrals.**
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted.
- **ADR-005:** Custom Postgres image decision. Pairs with PLAN-002.
- **Hook portability across environments:** Lesson #13 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [ ] **ADR-004** — Decide canonical author email (Session 10 hard deadline)
- [ ] **ADR-005 + PLAN-002** — Custom Postgres image with extensions
- [ ] **PLAN-003** — Ontology Engine (`vet_clinic_v0.yaml` + code generator) — *the moat*
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (low priority)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)
- [ ] Filesystem cleanup: `wsl -u root -- rm -rf .claude/worktrees/sad-northcutt-6a48ff/` (cosmetic, no rush)
- [x] **Phase G** — commit + PR + merge + cleanup *(Session 9)*
- [x] **Lesson #12 amendment** — Misdiagnosis section *(Session 9)*
- [x] **Lesson #13** — Code Tab worktree lifecycle traps *(Session 9, drafted; commit pending Step 4)*
- [x] **File-based handoff mechanism** — `.claude/handoffs/` live *(Session 9)*
- [x] **Setup Claude Code on Windows** *(Session 8)*
- [x] **Cowork Project setup** *(Session 8)*
- [x] **PLAN-001** — Starter pack scaffold *(Session 4)*
- [x] **ADR-003** — Service port strategy *(Session 4)*
- [x] **Memory architecture implementation** *(Session 5)*

## Next Steps

1. **Session 10** — ADR-004 decisive close (no more deferrals)
2. **Session 10** — Begin ADR-005 + PLAN-002 (Postgres + extensions)
3. **Session 10** — Validate file-based handoff mechanism end-to-end (Code↔Chat across full task lifecycle)
4. **Session 10+** — Begin PLAN-003 (Ontology Engine = the moat)

## Update Workflow

This file is updated when:
- A commit changes project state significantly
- A new ADR/PLAN is minted or completed
- Active priorities shift
- A session closes (sync `last_updated` + `session` front-matter)

Manually edited at session boundaries. Not auto-generated.
