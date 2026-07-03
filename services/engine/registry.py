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

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from services.engine.actions import RecommendedAction
from services.engine.data_adapter import DataAdapter

if TYPE_CHECKING:  # TYPE_CHECKING-only: keeps registry import-cycle-free at runtime
    from services.engine.procedures.orchestrator import StepExecutor
    from services.engine.procedures.spec import StepKind

Handler = Callable[[RecommendedAction], Awaitable[dict[str, Any]]]

# PLAN-0047 Step 2: a vertical's per-kind procedure-executor wiring, built fresh
# per run/resume request (stateful executors never leak across requests).
ExecutorFactory = Callable[[], "Mapping[StepKind, StepExecutor]"]


class RegistryError(Exception):
    """Raised on a missing lookup or a duplicate registration."""


@dataclass
class _VerticalEntry:
    """One vertical's registered adapter, named handlers, and executor factory."""

    adapter: DataAdapter | None = None
    handlers: dict[str, Handler] = field(default_factory=dict)
    executor_factory: ExecutorFactory | None = None


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

    def register_procedure_executors(self, vertical: str, factory: ExecutorFactory) -> None:
        """Register a vertical's procedure-executor factory (PLAN-0047 Step 2).

        The factory is invoked fresh per run/resume request by the HTTP run
        surface, mirroring the explicit adapter/handler registration pattern
        (OQ-6 — no import-scan discovery).
        """
        entry = self._verticals.setdefault(vertical, _VerticalEntry())
        if entry.executor_factory is not None:
            raise RegistryError(
                f"procedure-executor factory already registered for vertical '{vertical}'"
            )
        entry.executor_factory = factory

    def get_procedure_executors(self, vertical: str) -> ExecutorFactory:
        """Return the procedure-executor factory registered for ``vertical``."""
        entry = self._verticals.get(vertical)
        if entry is None or entry.executor_factory is None:
            raise RegistryError(
                f"no procedure-executor factory registered for vertical '{vertical}'"
            )
        return entry.executor_factory

    def verticals(self) -> list[str]:
        """Return the sorted names of every registered vertical."""
        return sorted(self._verticals)

    def handler_names(self, vertical: str) -> list[str]:
        """Return the sorted names of every handler registered for ``vertical``.

        Empty when the vertical is unknown or has no handlers. Used to
        constrain the LLM ``suggested_handler`` to resolvable handlers
        (PLAN-0006).
        """
        entry = self._verticals.get(vertical)
        if entry is None:
            return []
        return sorted(entry.handlers)

    def all_handler_names(self) -> list[str]:
        """Return the sorted UNION of every handler name across all registered verticals.

        Used by the procedure generator's prose-lint (PLAN-0040): a handler name is a
        human-authored binding regardless of which vertical it belongs to, so a generated
        prose string is scanned against the cross-vertical set, not just one vertical's.
        Empty when nothing is registered (e.g. in a fresh test process).
        """
        return sorted({name for entry in self._verticals.values() for name in entry.handlers})

    def reset(self) -> None:
        """Drop all registrations — mandatory between tests (PLAN-0005 R5)."""
        self._verticals.clear()


registry = VerticalRegistry()
