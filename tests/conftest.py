"""Shared pytest fixtures."""

from collections.abc import Iterator

import pytest

from services.engine.registry import registry


@pytest.fixture(autouse=True)
def _reset_registry() -> Iterator[None]:
    """Reset the process-wide vertical registry around every test (PLAN-0005 R5).

    autouse so no test that registers an adapter or handler can leak
    state into another (PLAN-0005 C-4).
    """
    registry.reset()
    yield
    registry.reset()
