#!/usr/bin/env python3
"""``status_digest`` loop handler — PLAN-0010 deferred Step-4 use-case (a).

**Detect-and-nudge (v1 scope, Cray-ratified 2026-06-02).** When the consumer
processes a ``status_digest`` message it computes ``docs/STATUS.md`` freshness
and, *only when drift is detected*, sends a no-PII Telegram nudge so the operator
remembers to reconcile. It does **not** edit STATUS, commit, or open a PR — the
*detection* is the toil Cray forgets; the *authoring* stays human-quality
(auto-draft is a deferred v2).

Design invariants:

* **Single source of truth for freshness.** Reuses
  :func:`tools.vero_bridge._status_lint.compute_status_freshness` — the same
  logic behind the ``lint_status`` bridge tool — rather than reimplementing the
  ``head_commit`` parse + ``git log`` drift query. (Two consumers today; if a
  third appears, graduate that function to a shared ``tools/`` module per the
  Rule of Three.)
* **The message body is a trigger only — never read.** The digest content comes
  entirely from git/STATUS (trusted), so a producer cannot inject text into the
  nudge (no injection surface). The producer's job is "*when*"; the consumer's
  is "*what*".
* **No PII.** The nudge carries only public git metadata (commit SHAs +
  subjects + the STATUS head SHA) — never operator/record/partner data
  (CLAUDE.md §8 / PDPA).
* **Best-effort — never raises into the dispatcher.** A digest failure must not
  poison the loop (mirrors the PLAN-0014 notify fail-safe). Every error is
  swallowed + logged.
* **argv Telegram contract.** ``tools/notify/telegram.sh`` takes the message as
  ``argv[1]`` (NOT stdin) — see Lesson #0014 (argv-vs-stdin contract drift).
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tools.loop._schema import LoopMessage
from tools.vero_bridge._status_lint import (
    _STATUS_COMMIT_GREP,
    BASELINE_REF,
    REPO_ROOT,
    compute_status_freshness,
)

LOGGER = logging.getLogger("tools.loop.status_digest")

#: Resolved ``git`` executable (absolute path; avoids a partial-path argv).
_GIT: str = shutil.which("git") or "git"

#: Default Telegram notifier script (same one the dispatcher's alert path uses).
DEFAULT_TELEGRAM_SCRIPT = Path("tools/notify/telegram.sh")
TELEGRAM_TIMEOUT_SEC = 5

#: Cap how many commits the nudge body lists (keep the message short).
_MAX_LISTED = 10


def _drift_subjects(repo_root: Path, head: str) -> list[str]:
    """Best-effort ``<sha> <subject>`` lines for the drift commits.

    Same exclusions/range as the freshness check (non-merge,
    non-``docs(status):``, ``<head>..<baseline>``) so the listing matches the
    drift count. Returns ``[]`` on any git failure — display-only, never fatal.
    """
    cmd = [
        _GIT,
        "log",
        "--no-merges",
        "--invert-grep",
        f"--grep={_STATUS_COMMIT_GREP}",
        "--format=%h %s",
        f"{head}..{BASELINE_REF}",
    ]
    try:
        # S603: fixed argv, no shell; the only interpolated value is a git
        # revision range from a STATUS-sourced short SHA + a constant ref.
        result = subprocess.run(  # noqa: S603
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def build_digest_body(freshness: dict[str, Any], subjects: list[str]) -> str | None:
    """Build the no-PII nudge body, or ``None`` when no nudge should be sent.

    Returns ``None`` when STATUS is fresh (nothing to nudge) **and** when the
    freshness check is fail-closed/indeterminate (``fresh=False`` but no drift
    commits — e.g. unreadable STATUS or a git failure): a "0 commits" nudge
    would be noise, so the handler logs that case instead.

    The body contains only commit SHAs + subjects + the STATUS head SHA — all
    public git metadata (no PII; CLAUDE.md §8 / PDPA).
    """
    drift = freshness.get("drift_commits") or []
    if freshness.get("fresh", False) or not drift:
        return None
    head = freshness.get("status_head_commit") or "(unknown)"
    count = len(drift)
    lines = [
        f"\U0001f4cb vero-lite STATUS drift: {count} substantive commit(s) "
        f"since {head} — reconcile due."
    ]
    listed = subjects[:_MAX_LISTED] if subjects else list(drift[:_MAX_LISTED])
    lines.extend(f"• {item}" for item in listed)
    if count > _MAX_LISTED:
        lines.append(f"…and {count - _MAX_LISTED} more")
    return "\n".join(lines)


def _send_telegram(script_path: Path, message: str) -> bool:
    """Send ``message`` via ``tools/notify/telegram.sh`` (``argv[1]`` contract).

    Best-effort: returns ``False`` on any failure and never raises.
    ``telegram.sh`` itself no-ops (exit 0) when ``TELEGRAM_BOT_TOKEN`` /
    ``TELEGRAM_CHAT_ID`` are unset, so a dev box without the env set is fine.
    The message is passed as ``argv[1]`` — NOT on stdin (Lesson #0014).
    """
    if not script_path.exists():
        return False
    try:
        # S603: fixed argv, no shell. S607: "bash" via PATH (same idiom as the
        # dispatcher alert path + pretooluse_loop_detect.py).
        result = subprocess.run(  # noqa: S603
            ["bash", str(script_path), message],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
            timeout=TELEGRAM_TIMEOUT_SEC,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def make_status_digest_handler(
    *,
    repo_root: Path | None = None,
    telegram_script: Path = DEFAULT_TELEGRAM_SCRIPT,
) -> Callable[[LoopMessage], None]:
    """Build the ``status_digest`` handler (closes over repo root + notifier).

    The returned handler matches the dispatcher's ``Handler`` signature
    (``(LoopMessage) -> None``). It never raises — a digest failure is logged,
    not propagated, so it cannot poison the loop.
    """
    root = (repo_root if repo_root is not None else REPO_ROOT).resolve()

    def handler(message: LoopMessage) -> None:
        # message is a trigger only — its body is intentionally NOT read.
        try:
            freshness = compute_status_freshness(root)
            head = freshness.get("status_head_commit")
            drift = freshness.get("drift_commits") or []
            subjects = _drift_subjects(root, str(head)) if drift else []
            body = build_digest_body(freshness, subjects)
            if body is None:
                # No nudge: either STATUS is fresh, or the check is fail-closed
                # (fresh=False + no drift — unreadable STATUS / git failure).
                if freshness.get("fresh", False):
                    LOGGER.info("status_digest: STATUS fresh (head=%s) — no nudge", head)
                else:
                    LOGGER.warning(
                        "status_digest: could not determine STATUS freshness "
                        "(head=%s) — no nudge sent",
                        head,
                    )
                return
            sent = _send_telegram(telegram_script, body)
            LOGGER.info(
                "status_digest: drift=%d head=%s telegram_sent=%s",
                len(drift),
                head,
                sent,
            )
        except Exception as exc:  # best-effort — must never poison the loop
            LOGGER.warning("status_digest handler failed (non-fatal): %s", exc)

    return handler
