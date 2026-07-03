"""Shared pytest fixtures."""

from collections.abc import Iterator

import pytest

from services.api.config import settings
from services.engine import demo_events
from services.engine.registry import registry

# PLAN-0047 Step 1: the legacy suites exercise business logic with authn OFF;
# auth behavior is covered explicitly in tests/api/test_api_auth.py (which
# monkeypatches it back on per-test). Attribute-level (not env) so dev (.env
# present) and CI (no .env) collect identically.
settings.api_auth_enabled = False


@pytest.fixture(autouse=True)
def _reset_registry() -> Iterator[None]:
    """Reset the process-wide vertical registry around every test (PLAN-0005 R5).

    autouse so no test that registers an adapter or handler can leak
    state into another (PLAN-0005 C-4).
    """
    registry.reset()
    yield
    registry.reset()


@pytest.fixture(autouse=True)
def _reset_demo_events() -> Iterator[None]:
    """Reset the per-process live OperationalEvent view around every test.

    PLAN-0015: the demo_events store holds the anchored event list + any
    execute-time recovery reading per process. autouse so an execute in one test
    cannot leak an injected recovery (or a stale anchor) into another.
    """
    demo_events.reset()
    yield
    demo_events.reset()


@pytest.fixture(autouse=True)
def _no_real_telegram(monkeypatch: pytest.MonkeyPatch) -> None:
    """Guarantee no test ever sends a real Telegram message (test isolation).

    Two independent notify paths exist, and a dev box with PLAN-0014 *armed*
    (real ``TELEGRAM_*`` present) would otherwise let the suite fire real pings:

    * the loop dispatcher shells out to ``tools/notify/telegram.sh``, which reads
      the **OS env** — so unset it and the script no-ops (``telegram.sh`` §main);
    * the in-app notifier POSTs via ``settings`` creds (loaded from ``.env`` at
      import, where ``delenv`` cannot reach them) — so close its enable gate.

    Tests that exercise the armed path re-arm explicitly (they override this).
    Reported live: ``test_cli_aborts_when_same_fs_check_fails`` sent a real
    dispatcher alert once Cray armed the box (the dispatcher assumed an unset
    env, which no longer holds on the demo box).
    """
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setattr(settings, "telegram_notify_enabled", False)
