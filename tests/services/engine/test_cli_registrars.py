"""AC-4 (PLAN-0090) — the scheduler CLI's vertical set must equal the API lifespan's.

``services/engine/cli.py`` MIRRORS ``services/api/main.py``'s registrar map rather than
importing it: ``services/engine/`` must not depend on ``services/api/``, and importing the app
would drag FastAPI into daemon startup. A mirror with no tripwire is exactly how the
pre-PLAN-0090 hardcode survived five verticals — ``_register_executor_factory`` dispatched on
``if vertical == "procurement"``, so ``vero-lite scheduler --vertical <anything-else>`` raised
``RegistryError`` at STARTUP (``_run_scheduler`` asks the registry for the factory unguarded),
and the only thing recording that state was a docstring which had itself gone stale ("Only
procurement ships one today" — false since four verticals ago).

So these tests are the structural replacement for that docstring: prose cannot go stale in a
way CI notices, a set-equality assertion can.
"""

from __future__ import annotations

import importlib

from services.api.main import _PROCEDURE_EXECUTOR_REGISTRARS as API_REGISTRARS
from services.engine.cli import _PROCEDURE_EXECUTOR_REGISTRARS as CLI_REGISTRARS


def test_cli_registrar_set_equals_api_lifespan_set() -> None:
    """A 7th vertical wired into one map but not the other goes RED here.

    Set-equality in BOTH directions on purpose: a vertical present only in the API is
    un-fireable by the daemon (the PLAN-0090 bug), and one present only in the CLI would
    register a factory the HTTP surface never does — a split-brain the run surface would hit
    at gate-resolve instead.
    """
    assert set(CLI_REGISTRARS) == set(API_REGISTRARS)


def test_every_cli_registrar_target_resolves() -> None:
    """Each CLI entry names a real, callable registrar.

    The CLI map addresses its registrars by ``(module_path, attribute)`` strings so the import
    stays lazy — which means a typo cannot fail at import time the way a direct ``from x import
    y`` would. This test buys that safety back deterministically, offline.
    """
    for vertical, (module_name, attr) in sorted(CLI_REGISTRARS.items()):
        module = importlib.import_module(module_name)
        target = getattr(module, attr, None)
        assert callable(target), f"{vertical}: {module_name}.{attr} is not callable"
