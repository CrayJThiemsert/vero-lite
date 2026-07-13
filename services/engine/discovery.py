"""Registry auto-discovery — import-scan over ``verticals/*`` (ADR-0023 / PLAN-0032, B2).

The ADR-006 D3 **L1 → L2** plugin-maturity move: a vertical that lives under
``verticals/<ns>/`` and exposes the conventional registration entry functions
(``register_<ns>_adapter`` in ``data_adapter``, ``register_<ns>_handlers`` in
``handlers``) is discovered + registered at runtime **without a hand edit to
``services/api/main.py``**. Mechanism = import-scan (ADR-0023 D2 / SD-C; Python
entry-points are the L3 future seam).

Properties (ADR-0023 D3/D4):

* **Additive** — the explicit ``registry.register_adapter`` / ``register_handler``
  API stays valid; discovery just invokes the same conventional entry functions.
* **Idempotent** — a vertical already in the registry is skipped (no duplicate
  ``RegistryError``), so discovery + an explicit register of the same vertical coexist.
* **Failure-isolated** — a broken / non-conforming vertical package is skipped + logged,
  never aborting discovery of the others.
* **Test-resettable** — discovery is a callable (no import-time-only side effect that
  survives ``registry.reset()``), so the ``_reset_registry`` fixture (PLAN-0005 R5) can
  wipe + re-discover deterministically.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil

from services.engine.registry import registry

logger = logging.getLogger(__name__)

_VERTICALS_PACKAGE = "verticals"
_SKIP = frozenset({"_template"})


def discover_and_register() -> list[str]:
    """Discover + register every conforming vertical under ``verticals/*``.

    Returns the names of the verticals **newly** registered by this call (sorted,
    deterministic). A vertical already present in the registry is skipped (idempotent);
    one whose import or entry-function call raises is skipped + logged (failure-isolated)
    and does not abort the rest.
    """
    package = importlib.import_module(_VERTICALS_PACKAGE)
    search_path = list(getattr(package, "__path__", []))
    already = set(registry.verticals())
    registered: list[str] = []
    for module_info in sorted(pkgutil.iter_modules(search_path), key=lambda m: m.name):
        ns = module_info.name
        if not module_info.ispkg or ns in _SKIP or ns in already:
            continue
        try:
            _register_vertical(ns)
        except Exception as exc:  # failure-isolation (AC-3) — one bad vertical ≠ all
            logger.warning("registry discovery skipped vertical %r: %s", ns, exc)
            continue
        registered.append(ns)
    return registered


def _register_vertical(ns: str) -> None:
    """Import a vertical's ``data_adapter`` + ``handlers`` and invoke its conventional
    ``register_<ns>_adapter`` / ``register_<ns>_handlers`` entry functions against the
    process-global registry. The optional ``economic_impact`` producer (ADR-0030 /
    PLAN-0071) registers here too when the module is present."""
    adapter_mod = importlib.import_module(f"{_VERTICALS_PACKAGE}.{ns}.data_adapter")
    handlers_mod = importlib.import_module(f"{_VERTICALS_PACKAGE}.{ns}.handlers")
    register_adapter = getattr(adapter_mod, f"register_{ns}_adapter")
    register_handlers = getattr(handlers_mod, f"register_{ns}_handlers")
    register_adapter()
    register_handlers()
    _register_economic_producer(ns)


def _register_economic_producer(ns: str) -> None:
    """Invoke a vertical's optional ``register_<ns>_economic_impact`` entry (ADR-0030 /
    PLAN-0071) if the vertical ships an ``economic_impact`` module.

    Guarded: an **absent** producer module is fine — the ฿ facet is opt-in per
    vertical, so a vertical without one is simply ฿-blind. But a producer module that
    exists yet fails on a **broken transitive import** must still surface (it is a real
    bug, not an opt-out), so the ``ModuleNotFoundError`` guard checks ``exc.name`` — only
    the producer module itself being missing is swallowed (drafter finding vii)."""
    econ_qualname = f"{_VERTICALS_PACKAGE}.{ns}.economic_impact"
    try:
        econ_mod = importlib.import_module(econ_qualname)
    except ModuleNotFoundError as exc:
        if exc.name == econ_qualname:
            return  # no producer module for this vertical — ฿-blind by design
        raise  # a broken transitive import inside an existing producer module — surface it
    getattr(econ_mod, f"register_{ns}_economic_impact")()
