"""🔴 s275 — every `uv run` in pre-commit must carry `--no-sync`.

A bare ``uv run`` re-syncs the project environment **without** the dev extra and
**uninstalls pytest / ruff / mypy / pre-commit** from the shared ``.venv`` to match
the base dependency set. That is not a theory: two other surfaces in this repo
already defend against it by name —

* ``.github/workflows/ci.yml`` (the comment above the ruff step, and every step
  since, uses ``uv run --no-sync``), and
* ``.claude/skills/ms-s1-ollama/run_detached.sh``, whose comment records that a
  bare ``uv run`` "uninstalls pytest/ruff/mypy/pre-commit out from under a
  concurrent session".

Pre-commit was the third surface and the only one left undefended — while firing
far more often than either, and at the exact moment a developer is most likely to
have a suite running in the background. ``git commit`` could strip that suite's
own site-packages mid-run.

The failure this guards is *silent and misattributed*: the suite does not report
"your venv was emptied", it reports an unrelated ``ImportError`` in whichever test
next imports a lazily-loaded plugin.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / ".pre-commit-config.yaml"

#: An `entry:` line that shells out to `uv run`. Matched as text rather than via a
#: YAML load on purpose: the defect is in the command STRING, and a structural read
#: would have to reassemble it anyway.
_UV_ENTRY = re.compile(r"^\s*entry:\s*(uv run\b.*)$", re.M)


def _uv_entries() -> list[str]:
    return [m.group(1).strip() for m in _UV_ENTRY.finditer(CONFIG.read_text(encoding="utf-8"))]


def test_the_config_actually_contains_uv_entries() -> None:
    """Positive control. The assertion below is 'every entry has --no-sync', which an
    empty list satisfies perfectly — a renamed config, a restructured `entry:`, or a
    broken regex would all turn this module green while checking nothing.
    """
    entries = _uv_entries()
    assert entries, (
        f"no `entry: uv run …` lines found in {CONFIG.name} — the check below would pass "
        "vacuously, so this is RED rather than 'nothing to check'"
    )


def test_every_uv_run_entry_carries_no_sync() -> None:
    """The guard. Prints the offending commands, not a bare count."""
    entries = _uv_entries()
    offenders = [e for e in entries if "--no-sync" not in e]
    assert not offenders, (
        f"{len(offenders)} of {len(entries)} `uv run` pre-commit entries lack `--no-sync`, "
        f"so committing can uninstall pytest/ruff/mypy from the shared .venv mid-run:\n  "
        + "\n  ".join(offenders)
    )
