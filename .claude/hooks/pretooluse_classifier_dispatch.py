#!/usr/bin/env python3
"""PreToolUse classifier dispatch hook — gate on G1/G2 governance rows
(PLAN-0009 Step 5c-2; PLAN-0008 carry-over).

Closes the PLAN-0008 deferred work: the Phase-2 classifier shipped the
``Stop``-side dispatch only; non-G5 rows that can be classified pre-tool
(G1 ADR mutation via ``Edit``, G2 number consumption via filename
creation) were marked "deferred to PLAN-0009 (subagent topology)" in
``.claude/autonomy-triggers.md`` "How the classifier reads this file" §.
This hook is the PreToolUse arm.

**Cheap pre-filter, then classifier.** The classifier is a ~5s API call;
firing it on every ``Write``/``Edit`` would be wasteful. So a cheap
deterministic pre-filter detects the *signature* of a G1/G2 candidate
first:

* **G1 (Edit accepted ADR)** = ``Edit`` + path matches
  ``docs/(adr|plans)/NNNN-*.md`` + file exists + first N lines contain
  ``Status: Accepted``
* **G2 (number consumption)** = ``Write`` + path matches
  ``docs/(adr|plans)/NNNN-*.md`` + file does NOT yet exist
  (the write would create a fresh-NNNN artifact)

Pre-filter miss → exit 0 (allow). Pre-filter hit → invoke classifier
with an augmented payload (``pretool_signature`` field flags the row
hit so the classifier knows the context).

**Decision mapping (3-decision contract from Step 5c-1):**

* ``proceed`` → exit 0 (allow). The classifier overruled the pre-filter
  (legitimate context — e.g., a chore PR fixing a typo in an accepted
  ADR; the registry G1 row is advisory + classifier judges OK).
* ``pause`` → ``deny`` with citation. The agent must surface to Cray
  before retrying. Matches the "always-pause" semantics of G1/G2.
* ``dispatch`` → ``deny`` with a *spawn-redirect* reason. Tells the
  agent NOT to retry inline; instead, spawn ``plan-drafter`` via the
  Step 4 §1 R4 routing. The Stop-side dispatch arm (5c-1) handles the
  same redirect at turn-end; this arm catches it before the action.

**Fail-closed:** ``_sonnet_classifier.classify`` already fails closed
to ``pause`` on any infrastructure failure (network, missing key,
malformed JSON). This hook treats ``pause`` as ``deny`` — strictly
safer than allow. A malformed ``dispatch`` verdict reaching this hook
(classifier-helper regression) is demoted to ``pause``-style deny too.

**Bypass-immunity:** PreToolUse ``deny`` decisions fire regardless of
``permissionMode`` per Anthropic hooks docs (ADR-013 D2 precedent).
The pre-filter reads file content from disk (not from ``tool_input``),
so a spoofed in-payload "I am editing a Draft ADR" cannot defeat the
G1 detection — we read the real on-disk file.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from _loop_counter import normalize_file_path  # noqa: E402  — sys.path above

# Pattern: docs/(adr|plans)/NNNN-name.md where NNNN is exactly 4 digits.
# Anchors enforce no false-positive on docs/adr/template.md, README.md, etc.
_GOVERNANCE_PATH_RE = re.compile(r"^docs/(?:adr|plans)/\d{4}-[\w\-]+\.md$")

# How many lines from top of an ADR to scan for the Status field. ADRs
# in this repo put Status: in the first 5-10 lines; 20 is comfortable.
_STATUS_SCAN_LINES = 20

# Match the ADR/PLAN status line in any of the three common markdown forms:
#   `Status: Accepted`         (plain)
#   `**Status:** Accepted`     (bold-key with colon inside bold — repo norm)
#   `**Status**: Accepted`     (bold-key with colon outside bold)
# Case-insensitive; tolerates extra whitespace and trailing punctuation
# ("Accepted.", "Accepted — amended 2026-...").
_STATUS_ACCEPTED_RE = re.compile(
    r"^\s*\*{0,2}\s*Status\s*\*{0,2}\s*:\s*\*{0,2}\s*Accepted\b",
    re.IGNORECASE | re.MULTILINE,
)


def _is_governance_path(file_path: str) -> bool:
    """True iff the path matches docs/(adr|plans)/NNNN-*.md.

    Handles three input shapes:

    * Repo-relative POSIX (``docs/adr/0009-foo.md``) — normalize is a no-op.
    * Absolute path inside the repo (UNC or POSIX) — ``normalize_file_path``
      finds the ``/vero-lite/`` marker and strips it.
    * Absolute path outside the repo (test fixtures in ``/tmp/...``,
      symlinks) — fall back to a suffix match for the
      ``docs/(adr|plans)/NNNN-*.md`` portion anywhere in the path.
    """
    normalized = normalize_file_path(file_path)
    if _GOVERNANCE_PATH_RE.match(normalized):
        return True
    # Suffix fallback for absolute paths that fall through normalization
    # (e.g., tmp_path fixtures, or files outside REPO_ROOT entirely).
    slashed = file_path.replace("\\", "/")
    if "/docs/adr/" in slashed or "/docs/plans/" in slashed:
        idx = slashed.rfind("/docs/")
        suffix = slashed[idx + 1 :]
        return bool(_GOVERNANCE_PATH_RE.match(suffix))
    return False


def _resolve_for_disk(file_path: str) -> Path:
    """Resolve to an absolute path for disk reads.

    Hook stdin's ``tool_input.file_path`` may be absolute or relative
    depending on harness behavior. We resolve against REPO_ROOT when
    relative so the existence check + content read are stable.
    """
    p = Path(file_path)
    if p.is_absolute():
        return p
    # Normalize via the L1 helper first, then resolve against REPO_ROOT.
    return REPO_ROOT / normalize_file_path(file_path)


def _has_status_accepted(disk_path: Path) -> bool:
    """Read first N lines; True if 'Status: Accepted' is present."""
    try:
        with disk_path.open("r", encoding="utf-8") as f:
            content = "".join(f.readline() for _ in range(_STATUS_SCAN_LINES))
    except (OSError, UnicodeDecodeError):
        return False
    return bool(_STATUS_ACCEPTED_RE.search(content))


def _detect_signature(tool_name: str, file_path: str) -> str | None:
    """Return the matched row ID (``"G1"`` or ``"G2"``) or ``None``.

    G1 = Edit + existing accepted ADR-or-PLAN
    G2 = Write + new (not-yet-existing) NNNN-*.md under docs/{adr,plans}/
    """
    if not _is_governance_path(file_path):
        return None

    disk_path = _resolve_for_disk(file_path)
    exists = disk_path.exists()

    if tool_name == "Edit":
        # G1 only applies when the file exists + carries Status: Accepted.
        # Edit on a Draft/Proposed ADR is fine (classifier will skip).
        # Edit on a not-yet-existing file is a weird payload (the Edit tool
        # would itself fail) — let the harness handle that path, we skip.
        if not exists:
            return None
        if _has_status_accepted(disk_path):
            return "G1"
        return None

    if tool_name == "Write":
        # G2 = consuming a fresh NNNN. Writing to an existing file is not
        # G2 (it might still be G1 if the file is accepted — but the Edit
        # tool, not Write, is the conventional path for that; if a Write
        # overwrites an accepted ADR, we still want to gate it as G1, so
        # check Status too).
        if not exists:
            return "G2"
        if _has_status_accepted(disk_path):
            return "G1"  # Write overwriting an accepted ADR → still G1
        return None

    return None


def _classify(payload: dict[str, Any]) -> dict[str, Any]:
    """Dispatch to the Sonnet classifier with a final fail-closed safety net.

    The classifier helper already converts every error path to a pause; this
    wrapper adds a defensive catch-all so a future helper regression cannot
    raise into the hook flow (which would default-allow the Pre tool call —
    the opposite of what we want).
    """
    try:
        from _sonnet_classifier import classify  # local: tolerant to absence
    except ImportError as exc:
        return {
            "decision": "pause",
            "matched_rows": [],
            "reason": f"classifier helper unavailable: {exc}",
        }
    try:
        return classify(payload)
    except Exception as exc:
        return {
            "decision": "pause",
            "matched_rows": [],
            "reason": f"classifier raised unexpectedly: {exc}",
        }


def _emit_deny(reason: str) -> int:
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


def _build_pause_deny_reason(
    signature: str,
    classifier_reason: str,
    matched_rows: list[str],
) -> str:
    cited = ", ".join(matched_rows) if matched_rows else signature
    return (
        f"PLAN-0009 Step 5c-2 PreToolUse classifier matched {cited}: "
        f"{classifier_reason}\n\n"
        f"This action is on the always-pause list per "
        f".claude/autonomy-triggers.md row {signature}. Surface the change "
        f"to Cray (handoff or chat) before retrying. The override path is "
        f"a chore PR with rationale — direct retry of this Write/Edit will "
        f"be denied again."
    )


def _build_dispatch_deny_reason(
    signature: str,
    dispatch_meta: dict[str, str],
    classifier_reason: str,
) -> str:
    artifact_kind = dispatch_meta.get("artifact_kind", "?")
    task_summary = dispatch_meta.get("task_summary", "")
    subagent = dispatch_meta.get("subagent", "plan-drafter")
    artifact_dir = "docs/adr" if artifact_kind == "adr" else "docs/plans"
    return (
        f"PLAN-0009 Step 5c-2 AUTO-HANDOFF DISPATCH (PreToolUse arm). "
        f"The classifier matched {signature} and recommends spawning "
        f"`{subagent}` instead of writing this inline:\n"
        f'  "{classifier_reason}"\n\n'
        f"Per Step 4 §1 R4 routing, do NOT proceed with this inline "
        f"Write/Edit. Instead:\n"
        f"  1. Enumerate `{artifact_dir}/` to pick the next free NNNN; "
        f"pass as target_number (you enumerate, subagent does not).\n"
        f"  2. Spawn `{subagent}` via the Agent tool with "
        f"artifact_kind={artifact_kind} and task_summary: {task_summary}\n"
        f"  3. The subagent writes the draft under {artifact_dir}/NNNN-*.md "
        f"and returns the path; you commit via PR per CLAUDE.md §7.\n\n"
        f"Override clause: if you believe the classifier misrouted this "
        f"(the action is not actually governance-drafting), surface the "
        f"misroute in a short reply so Cray can review the trigger — do "
        f"NOT retry the same Write/Edit. The PreToolUse arm will deny it "
        f"again."
    )


def _is_plan_drafter_subagent(payload: dict[str, Any]) -> bool:
    """True iff this PreToolUse call comes from the sanctioned ``plan-drafter``
    subagent (PLAN-0034 prong 2 / SD-1 (a)).

    Reuses the **same signal G5 keys on**
    (``pretooluse_git_deny._is_subagent_call``): ``agent_id`` is present +
    non-empty *only* when the hook fires inside a subagent call (PLAN-0009
    Step 1a Q3, empirically re-confirmed by the PLAN-0034 Step-3 spike — the
    live Claude Code harness populates both ``agent_id`` and ``agent_type`` on
    subagent PreToolUse payloads, though the public hooks docs currently omit
    them). We additionally require ``agent_type == "plan-drafter"`` so the
    exemption is scoped to the one sanctioned governance drafter (the codebase
    already name-couples to it: ``settings.json`` SubagentStop matcher,
    ``_sonnet_classifier.DISPATCH_ALLOWED_SUBAGENTS``).

    Version-dependent + fail-closed toward MORE gating: if a future Claude Code
    version stops populating these fields this returns ``False`` and the gate
    falls back to its prior (deny-prone) behaviour — never the reverse.
    """
    agent_id = payload.get("agent_id")
    if not isinstance(agent_id, str) or not agent_id.strip():
        return False
    agent_type = payload.get("agent_type")
    return isinstance(agent_type, str) and agent_type.strip() == "plan-drafter"


# ``main`` is a linear guard-clause dispatcher (parse -> validate -> prong-2
# exempt -> detect signature -> classify -> map verdict); the prong-2 exemption
# (PLAN-0034) adds the 11th branch. Decomposing would scatter the single
# PreToolUse contract across helpers without reducing real complexity.
def main() -> int:  # noqa: C901
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # fail-open on malformed input (protocol expects valid JSON)

    if not isinstance(payload, dict):
        return 0

    # PLAN-0034 prong 2 (SD-1 (a)): the sanctioned `plan-drafter` subagent's
    # draft-write is governed by the H2 allowlist
    # (`pretooluse_plan_subagent_write_deny.py`), NOT by this project-level
    # classifier gate. Without this exemption the gate fires on the drafter's
    # own `docs/(adr|plans)/NNNN-*.md` write (G2 signature) and denies it — the
    # mutual deadlock the dispatch creates. Short-circuit BEFORE the classifier
    # (no network; AC-7c). The main agent carries no `agent_id`, so its inline
    # new-artifact write is still gated (G2 preserved; AC-7b). G5 still denies
    # the subagent's git ops (separate hook, untouched; AC-7d).
    if _is_plan_drafter_subagent(payload):
        return 0

    tool_name = payload.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    file_path = tool_input.get("file_path", "")
    if not isinstance(file_path, str) or not file_path:
        return 0

    signature = _detect_signature(tool_name, file_path)
    if signature is None:
        return 0  # pre-filter miss — allow

    # Pre-filter hit → invoke classifier with augmented context.
    augmented_payload = dict(payload)
    augmented_payload["pretool_signature"] = {
        "matched_row": signature,
        "file_path": file_path,
        "hook_source": "pretooluse_classifier_dispatch",
    }
    decision = _classify(augmented_payload)
    verdict = decision.get("decision")
    classifier_reason = str(decision.get("reason", ""))
    matched_rows_raw = decision.get("matched_rows") or []
    matched_rows = [str(r) for r in matched_rows_raw] if isinstance(matched_rows_raw, list) else []

    if verdict == "proceed":
        # Classifier overruled the pre-filter — legitimate context.
        return 0

    if verdict == "dispatch":
        dispatch_meta = decision.get("dispatch")
        if not isinstance(dispatch_meta, dict):
            # Defensive: malformed dispatch metadata → demote to pause-style deny.
            return _emit_deny(_build_pause_deny_reason(signature, classifier_reason, matched_rows))
        return _emit_deny(_build_dispatch_deny_reason(signature, dispatch_meta, classifier_reason))

    # "pause" (or any unrecognized verdict — fail-closed) → deny.
    return _emit_deny(_build_pause_deny_reason(signature, classifier_reason, matched_rows))


if __name__ == "__main__":
    raise SystemExit(main())
