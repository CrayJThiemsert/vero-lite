"""Tests for the DataAdapter Protocol (ADR-007 D1, PLAN-0005 §6.1 / §7.1).

Lesson #7 §3 reliable methods: in-process ``isinstance`` probes against
the ``runtime_checkable`` Protocol and a behavioral assertion on the
``health_check`` return value. No harness exit codes.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from services.engine.data_adapter import DataAdapter


class _ConformingAdapter:
    """Minimal structurally-conforming DataAdapter implementation."""

    vertical_name = "test_vertical"

    async def fetch_objects(
        self,
        object_type: str,
        filter_expr: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        return [{"object_type": object_type}]

    async def fetch_links(
        self,
        link_type: str,
        from_pk: str | None = None,
        to_pk: str | None = None,
    ) -> list[dict[str, Any]]:
        return []

    async def stream_events(
        self,
        event_type: str,
        since: datetime | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        yield {"event_type": event_type}

    async def health_check(self) -> dict[str, Any]:
        return {"status": "ok", "vertical": self.vertical_name}


class _MissingHealthCheck:
    """Deliberately non-conforming: lacks the ``health_check`` method."""

    vertical_name = "broken_vertical"

    async def fetch_objects(
        self,
        object_type: str,
        filter_expr: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        return []

    async def fetch_links(
        self,
        link_type: str,
        from_pk: str | None = None,
        to_pk: str | None = None,
    ) -> list[dict[str, Any]]:
        return []

    async def stream_events(
        self,
        event_type: str,
        since: datetime | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        yield {}


def test_conforming_adapter_satisfies_protocol() -> None:
    """A class with every member passes the runtime_checkable check."""
    assert isinstance(_ConformingAdapter(), DataAdapter)


def test_adapter_missing_method_fails_protocol() -> None:
    """A class missing one method fails the same isinstance check."""
    assert not isinstance(_MissingHealthCheck(), DataAdapter)


async def test_health_check_returns_status_dict() -> None:
    """``health_check`` returns a dict carrying a status key."""
    adapter = _ConformingAdapter()
    result = await adapter.health_check()
    assert isinstance(result, dict)
    assert "status" in result
