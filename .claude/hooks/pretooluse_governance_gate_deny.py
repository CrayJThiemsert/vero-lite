#!/usr/bin/env python3
"""PreToolUse hook — deterministic G1 + G2 governance gate (no model call).

Replaces a model judgment with a file read for the two registry rows whose
criteria are pure predicates:

* **G1** — "Mutate any ADR with ``Status: Accepted``". Decided by opening the
  target ADR and reading its ``**Status:**`` line.
* **G2** — "Consume / earmark an ADR or PLAN number". Decided by the target
  path matching ``docs/(adr|plans)/NNNN-*.md`` and **not yet existing**.

Why deterministic (session 201, 2026-08-02 — measured, see
``docs/research/private/2026-08-02-llm-placement-classifier-eval-and-palantir-aip-pattern.md``):

The classifier payload carries the target's *path*, never its *content*, so no
model of any size can evaluate G1's actual criterion — it can only infer from
the path. Measured consequences on ``gpt-oss:20b``: identical input at
``temperature 0`` returned ``proceed`` and ``pause`` on consecutive calls
(self-consistency 0/4 at the live prompt size), blank ``message.content`` on
3/12 runs (each one a fail-closed deny with no verdict behind it), ``G1`` cited
against a routine edit to ``services/api/routers/insights.py``, and ``G1`` cited
against ``0014-WITHDRAWN.md``. Shrinking the prompt fixed every other row and
made G1 *worse* — with less noise the model correctly reasoned "nothing here
says Accepted" and allowed the edit, which is the right inference from the
wrong inputs.

A hook can open the file. That is the whole difference, and it is structural
rather than a matter of model quality: this gate is **better informed** than any
classifier, not merely cheaper. Same shape as the existing deterministic rows
(G5 ``pretooluse_git_deny``, C4 ``pretooluse_research_path_deny``, H1
``posttooluse_validate_handoff``), and the same shape Palantir AIP Logic uses —
five of its six block types never invoke an LLM.

**No override hatch, by design.** CLAUDE.md §6 already routes ADR/PLAN authoring
as "drafter authors (ungated) -> Code commits"; the sanctioned ``plan-drafter``
subagent is exempted below (PLAN-0034 prong 2 — it carries its own fail-closed
write-allowlist). An env-var escape for the main agent would restore exactly the
"retry until it lets you through" property this hook exists to remove.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

ADR_DIR = "docs/adr/"
PLANS_DIR = "docs/plans/"

#: ``docs/adr/0035-name.md`` / ``docs/plans/0100-name.md``. Three-or-four digit
#: to tolerate any legacy 3-digit file; the directory prefix is matched
#: separately so ``docs/plans/done/0042-x.md`` (an archive move, not a number
#: consumption) does not match.
NUMBERED_ARTIFACT = re.compile(r"^docs/(adr|plans)/(\d{3,4})-[^/]+\.md$")

#: The canonical status line. Body may carry emphasis and a trailing clause.
STATUS_LINE = re.compile(r"^\*\*Status:\*\*(.*)$", re.MULTILINE)


def _normalize_to_repo_relative(path_str: str) -> str | None:
    """Return a POSIX path relative to REPO_ROOT, or None if outside the repo.

    Lifted from ``pretooluse_research_path_deny`` — backslashes are folded to
    forward slashes BEFORE any pathlib op so Windows / UNC inputs parse
    correctly. Cray's host launches the CLI on Windows (``file_path`` arrives in
    Windows form) while tests run on Linux.
    """
    if not path_str:
        return None
    normalized = path_str.replace("\\", "/")
    marker = "/vero-lite/"
    idx = normalized.rfind(marker)
    if idx >= 0:
        return normalized[idx + len(marker) :]
    p = Path(normalized)
    if p.is_absolute():
        try:
            return p.resolve().relative_to(REPO_ROOT).as_posix()
        except (ValueError, OSError):
            return None
    return p.as_posix()


def status_is_accepted(text: str) -> bool:
    """True iff the document's ``**Status:**`` line names Accepted.

    Handles every shape measured across the 35 committed ADRs:

    * ``**Status:** Accepted``
    * ``**Status:** **Accepted**`` (ADR-0035 — emphasis around the value)
    * ``**Status:** Accepted — ratified by Cray 2026-07-28 (session 185, ...)``
    * ``**Status:** Accepted *(Cray-ratified 2026-06-11)*``

    and rejects:

    * ``**Status:** Withdrawn`` (ADR-0014)
    * ``**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXXX``
      — ``0000-template.md``'s **menu of choices**, not a status. A naive
      substring test says "Accepted" here and would gate the template forever;
      the pipe is the tell.
    """
    m = STATUS_LINE.search(text)
    if m is None:
        return False
    value = m.group(1)
    if "|" in value:
        return False  # a menu of options (the template), not a decided status
    value = value.replace("*", "").replace("_", "").strip()
    return value.lower().startswith("accepted")


def _is_plan_drafter_subagent(payload: dict[str, object]) -> bool:
    """True iff the caller is the sanctioned ``plan-drafter`` subagent.

    Mirrors ``pretooluse_classifier_dispatch._is_plan_drafter_subagent``:
    ``agent_id`` is present and non-empty only inside a subagent call, and
    ``agent_type`` must additionally name the drafter — so a different subagent
    cannot inherit the exemption. PLAN-0034 prong 2: the drafter is the one
    actor allowed to author under ``docs/adr/`` + ``docs/plans/``, bounded by
    its own fail-closed write-allowlist rather than by this gate.
    """
    agent_id = payload.get("agent_id")
    if not (isinstance(agent_id, str) and agent_id.strip()):
        return False
    agent_type = payload.get("agent_type")
    return isinstance(agent_type, str) and agent_type.strip() == "plan-drafter"


def _deny(reason: str) -> int:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    return 0


def evaluate(payload: dict[str, object], *, repo_root: Path | None = None) -> str | None:
    """Return a deny reason, or None to stay silent. Pure — testable without IO
    on stdin. ``repo_root`` is injectable so tests can build a fixture tree.
    """
    if payload.get("tool_name") not in ("Write", "Edit"):
        return None
    if _is_plan_drafter_subagent(payload):
        return None

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str):
        return None

    rel = _normalize_to_repo_relative(file_path)
    if rel is None:
        return None

    match = NUMBERED_ARTIFACT.match(rel)
    root = repo_root if repo_root is not None else REPO_ROOT
    target = root / rel

    # --- G2: a numbered artifact that does not exist yet = consuming a number.
    if match is not None and not target.exists():
        kind = "ADR" if match.group(1) == "adr" else "PLAN"
        return (
            f"Registry row G2 (always-pause): creating `{rel}` consumes a new "
            f"{kind} number. Deterministic gate — no classifier involved, so "
            f"retrying will not change this answer.\n\n"
            f"Route: CLAUDE.md §6 — the `plan-drafter` subagent authors the "
            f"draft (it is exempt from this gate and bounded by its own "
            f"write-allowlist), then Code reviews and commits it via a PR. "
            f"Spawn `plan-drafter` with the target number you enumerated."
        )

    # --- G1: mutating an ADR whose status is Accepted.
    if rel.startswith(ADR_DIR) and rel.endswith(".md") and target.exists():
        try:
            text = target.read_text(encoding="utf-8")
        except OSError:
            return None  # unreadable — this gate has nothing to say
        if status_is_accepted(text):
            return (
                f"Registry row G1 (always-pause): `{rel}` has "
                f"`Status: Accepted`, read from the file itself. Deterministic "
                f"gate — no classifier involved, so retrying will not change "
                f"this answer.\n\n"
                f"Route: CLAUDE.md §6 — an Accepted ADR's body is amended by "
                f"`plan-drafter` (exempt from this gate), then Code reviews and "
                f"commits via a `docs/*` PR. Cray's approval of the wording "
                f"authorises the amendment; it does not authorise Code to type "
                f"it directly."
            )

    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # malformed input — fail open, the protocol expects valid JSON
    if not isinstance(payload, dict):
        return 0
    reason = evaluate(payload)
    return _deny(reason) if reason else 0


if __name__ == "__main__":
    raise SystemExit(main())
