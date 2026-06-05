"""Prebaked default partner-input packages (PLAN-0017 AC-4 fallback).

When MS-S1 is cold/unreachable at demo time, the operator can pick one of these
**static, source-tagged** starter packages in the gate to keep the live
"build #4" flow moving — instead of typing every slot by hand. Crucially these
are vero-lite's OWN example fixtures (no partner data, nothing leaves the box),
so this fallback does NOT cross the CLAUDE.md §8 / AC-4 boundary that forbids
sending the stakeholder's live description to a hosted model. The gate surfaces
``source='prebaked_default'`` prominently so the operator always knows a starter
(not their live extraction) is in play — the AC-4 non-silent-state requirement.

Each ``*.json`` in this directory is one :class:`IntakePackage`. Adding a
starter = drop in a new validated JSON file (no code change).
"""

from __future__ import annotations

import json
from pathlib import Path

from services.engine.intake_assembler import IntakePackage

_DEFAULTS_DIR = Path(__file__).parent


def load_default_packages() -> list[IntakePackage]:
    """Load + validate every prebaked default package, sorted by namespace.

    Each file must validate as an :class:`IntakePackage`; a malformed fixture
    raises at load time (caught early by the Step-1 test) rather than degrading
    silently at demo time.
    """
    packages: list[IntakePackage] = []
    for path in sorted(_DEFAULTS_DIR.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        packages.append(IntakePackage.model_validate(raw))
    return sorted(packages, key=lambda p: p.namespace)
