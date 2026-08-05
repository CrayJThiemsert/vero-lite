"""Append-only prompt log for the published demo (PLAN-0100 Step 7; ADR-0035 D6).

What a visitor typed is the one thing the published demo retains, and D6 fixes
both halves of that bargain: the operator can read what was asked (so a demo can
be improved and a misuse can be seen), and **nothing identifies who asked it**.

The field set is therefore a CLOSED set, not a minimum — see :data:`FIELDS`. No
IP, no headers, no gate identity, no session (OQ-2, ratified). AC-8 asserts
set-equality rather than presence for exactly this reason: a test that checked
"the required keys are present" would stay green on the day someone adds a
``client_ip``, and that day is the whole risk.

Default-OFF. Dev and CI never write a byte unless ``PROMPT_LOG_ENABLED`` is set,
so this module changes nothing about existing flows.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from services.api.config import settings

#: The complete set of keys a prompt-log row may carry (D6). CLOSED, not minimal.
FIELDS = frozenset({"ts_utc", "route", "vertical", "text", "model", "outcome", "arm"})

#: Rolling retention (D6, ratified OQ-2). Files older than this are deleted on
#: the write path — there is no cron on the published box, and a retention policy
#: whose enforcement depends on a scheduler nobody installed is a promise, not a
#: control.
RETENTION_DAYS = 90

_FILE_PREFIX = "prompt-"
_FILE_SUFFIX = ".jsonl"


def _day_file(directory: Path, when: datetime) -> Path:
    return directory / f"{_FILE_PREFIX}{when.date().isoformat()}{_FILE_SUFFIX}"


def _file_date(path: Path) -> datetime | None:
    """The day a log file covers, from its NAME — never its mtime.

    Deliberately not ``stat().st_mtime``: a copy, a restore, or a volume remount
    rewrites mtimes and would silently resurrect expired rows past their
    retention. The name is written once and never changes.
    """
    stem = path.name
    if not (stem.startswith(_FILE_PREFIX) and stem.endswith(_FILE_SUFFIX)):
        return None
    raw = stem[len(_FILE_PREFIX) : -len(_FILE_SUFFIX)]
    try:
        return datetime.fromisoformat(raw).replace(tzinfo=UTC)
    except ValueError:
        return None


def rotate(directory: Path, *, now: datetime) -> list[Path]:
    """Delete day files older than :data:`RETENTION_DAYS`. Returns what was deleted.

    Never raises: retention failing must not take a demo query down with it. A
    file that cannot be removed stays and is retried on the next write.
    """
    cutoff = now - timedelta(days=RETENTION_DAYS)
    deleted: list[Path] = []
    if not directory.is_dir():
        return deleted
    for path in sorted(directory.glob(f"{_FILE_PREFIX}*{_FILE_SUFFIX}")):
        day = _file_date(path)
        if day is None or day >= cutoff:
            continue
        try:
            path.unlink()
        except OSError:
            continue
        deleted.append(path)
    return deleted


def record(
    *,
    route: str,
    vertical: str,
    text: str,
    model: str,
    outcome: str,
    arm: str,
    now: datetime | None = None,
) -> Path | None:
    """Append one row and rotate. Returns the file written, or ``None`` if disabled.

    ``text`` is the visitor's input **verbatim** — not normalised, not truncated.
    A log of what someone meant to type is not evidence of what they typed, and
    the operator reading this is trying to answer questions about the latter.

    Never raises. A logging failure must not fail the query it describes: the
    visitor asked a question, and losing their answer to a full disk would turn a
    housekeeping problem into a product outage.
    """
    if not settings.prompt_log_enabled:
        return None
    stamp = now or datetime.now(UTC)
    row = {
        "ts_utc": stamp.isoformat(),
        "route": route,
        "vertical": vertical,
        "text": text,
        "model": model,
        "outcome": outcome,
        "arm": arm,
    }
    assert set(row) == FIELDS, "prompt-log row drifted from the D6 closed field set"
    directory = Path(settings.prompt_log_dir)
    try:
        directory.mkdir(parents=True, exist_ok=True)
        target = _day_file(directory, stamp)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        return None
    rotate(directory, now=stamp)
    return target
