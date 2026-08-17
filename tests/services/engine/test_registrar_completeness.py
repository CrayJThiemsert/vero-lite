"""The registrar map is complete against DISK (PLAN-0107 AC-4, Phase A / ① instruments).

``test_cli_registrars.py`` asserts the API map and the CLI map are **set-equal**.
That is the right guard for a mirror, and it is blind to the failure that
actually costs a demo: a **7th vertical wired into neither map**. Two empty
slots are set-equal, so a vertical that ships ``procedures.yaml`` and no
executor registrar is green in both directions today, and only fails at runtime
— a `409` on the first governed run of a brand-new vertical, on a live surface.

This test closes that by comparing the map against the **filesystem** instead of
against its own mirror. Disk is the one party to the comparison that cannot be
kept in sync by forgetting.

Enumeration deliberately reuses ``discovery``'s own package handle and ``_SKIP``
rather than re-deriving a path or re-listing skipped directories: a guard that
restates its subject's constants drifts from it silently — which is exactly the
class of defect PLAN-0107 exists to close.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from services.api.main import _PROCEDURE_EXECUTOR_REGISTRARS as API_REGISTRARS
from services.engine.discovery import _SKIP, _VERTICALS_PACKAGE

#: Verticals that ship a ``procedures.yaml`` and DELIBERATELY register no
#: executor factory. Each entry needs a written reason.
#:
#: Empty today, and measured rather than assumed: all six spec-shipping verticals
#: (aquaculture, building_materials, energy, fleet_maintenance, procurement,
#: supply_chain) register a factory. ``vet_clinic`` ships no ``procedures.yaml``
#: and is therefore never enumerated here at all — it needs no exemption, which
#: is why it is a comment and not an entry.
_NO_REGISTRAR_EXPECTED: dict[str, str] = {}


def _vertical_dirs() -> list[Path]:
    """Every discoverable vertical package directory, exactly as discovery sees it."""
    package = importlib.import_module(_VERTICALS_PACKAGE)
    search_path = list(getattr(package, "__path__", []))
    return [
        Path(info.module_finder.path) / info.name  # type: ignore[union-attr]
        for info in pkgutil.iter_modules(search_path)
        if info.ispkg and info.name not in _SKIP
    ]


def _spec_shipping_verticals() -> set[str]:
    return {d.name for d in _vertical_dirs() if (d / "procedures.yaml").is_file()}


def test_the_enumeration_finds_spec_shipping_verticals() -> None:
    """Anti-vacuity: an enumeration that finds nothing makes the real check pass.

    Every assertion below is a set difference against this enumeration, so an
    empty result would turn them green. This is the positive control that the
    instrument reads the filesystem at all.
    """
    found = _spec_shipping_verticals()
    assert found, (
        "no vertical under verticals/ was found shipping a procedures.yaml — the "
        "enumeration matched nothing, so the completeness check below would be "
        "vacuously true. Either the package layout moved or discovery's _SKIP grew."
    )


def test_every_spec_shipping_vertical_has_an_executor_registrar() -> None:
    """A vertical with a spec and no registrar 409s on its first governed run.

    RED when: a new ``verticals/<ns>/procedures.yaml`` lands without an entry in
    ``_PROCEDURE_EXECUTOR_REGISTRARS``. That is precisely the state
    ``test_cli_registrars.py`` cannot see, because two absent entries are
    set-equal.
    """
    missing = sorted(
        ns
        for ns in _spec_shipping_verticals()
        if ns not in API_REGISTRARS and ns not in _NO_REGISTRAR_EXPECTED
    )
    assert not missing, (
        f"{len(missing)} vertical(s) ship a procedures.yaml but register no executor "
        f"factory: {missing}. Add each to _PROCEDURE_EXECUTOR_REGISTRARS in "
        "services/api/main.py (and to the CLI mirror in services/engine/cli.py), or "
        "add an entry to _NO_REGISTRAR_EXPECTED with the reason it ships specless."
    )


def test_the_exemption_dict_carries_no_stale_entry() -> None:
    """An exemption for a vertical that is gone, or now registered, is a lie."""
    shipping = _spec_shipping_verticals()
    stale = sorted(
        ns for ns in _NO_REGISTRAR_EXPECTED if ns not in shipping or ns in API_REGISTRARS
    )
    assert not stale, (
        f"_NO_REGISTRAR_EXPECTED holds {len(stale)} entry/entries that no longer "
        f"describe a spec-shipping vertical without a registrar: {stale}. Remove them."
    )
