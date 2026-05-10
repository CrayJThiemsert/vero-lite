---
last_updated: 2026-05-10
session: 10
state: stable
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

**Phase 1, Month 1, Session 10** — ADR-004 closed, worktree mode policy codified, handoff rotation live.

Active priorities:
1. Find 2–3 vet clinic design partners by month 3
2. Build YAML ontology + code generator (the moat)
3. Demo 5: 30-second onboarding (drop CSV → schema detected → answers in <30s)

## Recent Decisions (last 5)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-05-10 | ADR-004 closed — GitHub noreply alias as canonical author email (provisional) | `docs/adr/0004-canonical-author-email.md` |
| 2026-05-10 | Worktree mode policy codified in CLAUDE.md §6 (per Lesson #13) | `CLAUDE.md` §6 |
| 2026-05-10 | Handoff rotation policy codified in runbook | `docs/runbooks/claude-code-chat-handoff.md` |
| 2026-05-09 | Lesson #13 — Code Tab worktree lifecycle traps (3 families, 7 traps) | `docs/lessons/0003-code-tab-worktree-lifecycle-traps.md` |
| 2026-05-09 | File-based Code↔Chat handoff mechanism (`.claude/handoffs/`) | `docs/runbooks/claude-code-chat-handoff.md` |

## In-Flight Discussions

- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted.
- **ADR-005:** Custom Postgres image decision. Pairs with PLAN-002.
- **Hook portability across environments:** Lesson #13 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [ ] **ADR-005 + PLAN-002** — Custom Postgres image with extensions
- [ ] **PLAN-003** — Ontology Engine (`vet_clinic_v0.yaml` + code generator) — *the moat*
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (low priority)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)
- [ ] Filesystem cleanup: `wsl -u root -- rm -rf .claude/worktrees/sad-northcutt-6a48ff/` (cosmetic, no rush)
- [x] **ADR-004** — Canonical author email (GitHub noreply, provisional) *(Session 10)*
- [x] **Worktree mode policy** — codified in CLAUDE.md §6 *(Session 10)*
- [x] **Handoff rotation policy** — codified in runbook *(Session 10)*
- [x] **Phase G** — commit + PR + merge + cleanup *(Session 9)*
- [x] **Lesson #12 amendment** — Misdiagnosis section *(Session 9)*
- [x] **Lesson #13** — Code Tab worktree lifecycle traps *(Session 9)*
- [x] **File-based handoff mechanism** — `.claude/handoffs/` live *(Session 9)*
- [x] **Setup Claude Code on Windows** *(Session 8)*
- [x] **Cowork Project setup** *(Session 8)*
- [x] **PLAN-001** — Starter pack scaffold *(Session 4)*
- [x] **ADR-003** — Service port strategy *(Session 4)*
- [x] **Memory architecture implementation** *(Session 5)*

## Next Steps

1. **Session 10** — Begin ADR-005 + PLAN-002 (Postgres + extensions)
2. **Session 10+** — Begin PLAN-003 (Ontology Engine = the moat)
3. **Ongoing** — Continue exercising file-based handoff mechanism (Chat ↔ Code) across batches; capture any new traps as Lesson #13 amendments or new lessons.

## Update Workflow

This file is updated when:
- A commit changes project state significantly
- A new ADR/PLAN is minted or completed
- Active priorities shift
- A session closes (sync `last_updated` + `session` front-matter)

Manually edited at session boundaries. Not auto-generated.
