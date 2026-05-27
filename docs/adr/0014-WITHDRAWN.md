# ADR-0014: WITHDRAWN — Cross-Tab MCP Transport (rolled back to PLAN-0012)

**Status:** Withdrawn
**Date withdrawn:** 2026-05-27
**Deciders:** Jirachai Thiemsert (founder)
**Resolution:** Work continues as **PLAN-0012 `vero-bridge`** under already-Accepted [ADR-013 D1](0013-autonomy-axis-relocation.md), per [PLAN-0009 OQ-3](../plans/done/0009-subagent-topology.md) precedent ("*no new ADR; mint ADR only if a genuinely architecture-level choice surfaces*").

## Why this slot is tombstoned

This slot held a Proposed-state ADR draft (`0014-cross-tab-mcp-transport.md`, take 3, 837 lines) for cross-tab MCP transport between Code, Cowork, and Chat tabs. The draft went through a full author≠reviewer pipeline:

| Step | Artifact | Reference |
|---|---|---|
| Take 1 | 685 lines, recovered from JSONL after a contaminated-session loss | (working-tree only, not committed) |
| Cowork advisory round 1 | C1 stale Phase-3 premise, C2 Cowork-client locus, C3 slot inventory, C4 commit attribution, 3 missing OQs | [`.claude/handoffs/session-16/2026-05-27-1145-cowork-adr0014-advisory-pass.md`](../../.claude/handoffs/session-16/2026-05-27-1145-cowork-adr0014-advisory-pass.md) |
| Take 2 | 727 lines, uncommitted | (working-tree only, not committed) |
| Cowork advisory round 2 | Focus-1 (C1–C4) PASS; Focus-3 N1/N2 docs lag (fixed in [PR #56](https://github.com/CrayJThiemsert/vero-lite/pull/56)); Focus-2 OQ A/B/C dimension refinements; Focus-4 attribution refinement | [`.claude/handoffs/session-16/2026-05-27-1330-cowork-adr0014-take2-verification.md`](../../.claude/handoffs/session-16/2026-05-27-1330-cowork-adr0014-take2-verification.md) |
| Take 3 | 837 lines, opened as [PR #57](https://github.com/CrayJThiemsert/vero-lite/pull/57) | PR closed without merge as part of this withdrawal |

Cray resolved the take-3 blocking **OQ-A** (the load-bearing "ADR-014 vs PLAN-0012-under-ADR-013" question) in favor of **PLAN-0012-under-ADR-013** on 2026-05-27. Reasoning recorded in PR #57 closure comment.

## Why the slot is reserved (not reused)

`docs/adr/` numbering is monotonic and used as archeology. A future reader scanning `ls docs/adr/` should see `0013 → 0014-WITHDRAWN → 0015` and not a confusing gap that conceals the take-1/2/3 author-pipeline work. Same pattern as ADR slot `0011` (reserved for the action-approval / audit framework; see [ADR-013 §Context](0013-autonomy-axis-relocation.md)).

The full take-3 draft is preserved in git history on branch `chore/adr-0014-cross-tab-mcp-transport` at commit `2fde9eb`; the closure comment on PR #57 cites that SHA so deep archeology stays reachable.

## What replaces this ADR

- **PLAN-0012 `vero-bridge`** — to be minted under ADR-013 D1 (transport implementation). The `vero-bridge` name is honored from [PLAN-0009 §Out-of-Scope](../plans/done/0009-subagent-topology.md) Phase-4 earmark (re-anchored from PLAN-0010 to PLAN-0012 in the same commit as this tombstone).
- **OQ-C empirical experiment** (Cowork MCP-client execution locus — desktop-proxy vs sandbox-VM) — to be run by Cray + Cowork (~10 min) **before** PLAN-0012 commits any v1 wiring, so the Cowork-client section can be specified concretely rather than contingently. Outcome captured in a runbook or research note so future-surface OQs (e.g. ADR-014 take-3 §OQ-5 Chat-client) can cite it.

## References

- [ADR-013 — Autonomy Axis Relocation](0013-autonomy-axis-relocation.md) (D1 is what PLAN-0012 will operationalize)
- [PLAN-0009 — Subagent Topology (DONE)](../plans/done/0009-subagent-topology.md) (§Out-of-Scope `vero-bridge` Phase-4 earmark; OQ-3 "no new ADR" precedent)
- [Lesson #8 — Cowork K-1/K-2 sandbox facts](../lessons/0008-cowork-tier1-k1-k2-workflow.md) (basis for OQ-C)
- [Lesson #15 — Classifier payload starvation](../lessons/0015-classifier-payload-starvation-stop-events.md) (§7: bug does not invalidate ADR-013 D1; live-evidence dependency rolls into PLAN-0012 sequencing)
- [PR #53](https://github.com/CrayJThiemsert/vero-lite/pull/53) — Lesson #15 fix shipped (PLAN-0011)
- [PR #56](https://github.com/CrayJThiemsert/vero-lite/pull/56) — docs reconcile that unblocked take-3 citations
- [PR #57](https://github.com/CrayJThiemsert/vero-lite/pull/57) — take-3 draft (closed without merge as part of this withdrawal)
