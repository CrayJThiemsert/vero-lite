"""Vertical registry — explicit adapter + handler registration (PLAN-0005 §6.4).

A per-process registry mapping ``vertical_name`` to its DataAdapter and
its named action handlers. Per OQ-6 registration is explicit via
``register_adapter`` / ``register_handler`` — no entry-point packaging,
no import-scan discovery.

A ``Handler`` is an async callable that executes a RecommendedAction and
returns a receipt dict. The module exposes a process-wide ``registry``
singleton; because it is process-global, tests MUST reset it between
cases (PLAN-0005 R5) — the autouse ``_reset_registry`` fixture in
``tests/conftest.py`` does this.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from services.engine.actions import RecommendedAction
from services.engine.data_adapter import DataAdapter

Handler = Callable[[RecommendedAction], Awaitable[dict[str, Any]]]


class RegistryError(Exception):
    """Raised on a missing lookup or a duplicate registration."""


@dataclass
class _VerticalEntry:
    """One vertical's registered adapter and named handlers."""

    adapter: DataAdapter | None = None
    handlers: dict[str, Handler] = field(default_factory=dict)


class VerticalRegistry:
    """Per-process map of ``vertical_name`` to its adapter and handlers.

    OQ-6: registration is explicit; the engine never scans entry points
    or imports for discovery.
    """

    def __init__(self) -> None:
        self._verticals: dict[str, _VerticalEntry] = {}

    def register_adapter(self, adapter: DataAdapter) -> None:
        """Register a vertical's DataAdapter, keyed by ``adapter.vertical_name``."""
        name = adapter.vertical_name
        entry = self._verticals.setdefault(name, _VerticalEntry())
        if entry.adapter is not None:
            raise RegistryError(f"adapter already registered for vertical '{name}'")
        entry.adapter = adapter

    def register_handler(self, vertical: str, name: str, handler: Handler) -> None:
        """Register a named action handler for a vertical."""
        entry = self._verticals.setdefault(vertical, _VerticalEntry())
        if name in entry.handlers:
            raise RegistryError(f"handler '{name}' already registered for vertical '{vertical}'")
        entry.handlers[name] = handler

    def get_adapter(self, vertical: str) -> DataAdapter:
        """Return the adapter registered for ``vertical``."""
        entry = self._verticals.get(vertical)
        if entry is None or entry.adapter is None:
            raise RegistryError(f"no adapter registered for vertical '{vertical}'")
        return entry.adapter

    def get_handler(self, vertical: str, name: str) -> Handler:
        """Return the handler ``name`` registered for ``vertical``."""
        entry = self._verticals.get(vertical)
        if entry is None or name not in entry.handlers:
            raise RegistryError(f"no handler '{name}' registered for vertical '{vertical}'")
        return entry.handlers[name]

    def verticals(self) -> list[str]:
        """Return the sorted names of every registered vertical."""
        return sorted(self._verticals)

    def reset(self) -> None:
        """Drop all registrations — mandatory between tests (PLAN-0005 R5)."""
        self._verticals.clear()


registry = VerticalRegistry()
