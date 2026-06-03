"""Contract: the suite can never send a real Telegram message.

Guards the autouse ``_no_real_telegram`` fixture (tests/conftest.py). Without
it, a dev box with PLAN-0014 armed (real ``TELEGRAM_*`` in the env / ``.env``)
made tests fire real pings — the dispatcher's ``same_fs`` abort test shelled out
to the real ``telegram.sh`` and delivered an alert. This locks both notify paths
shut for every test.
"""

from __future__ import annotations

import os

from services.api.config import settings


def test_suite_neutralizes_both_telegram_paths() -> None:
    # dispatcher path: telegram.sh reads the OS env and no-ops when these are unset
    assert os.environ.get("TELEGRAM_BOT_TOKEN") is None
    assert os.environ.get("TELEGRAM_CHAT_ID") is None
    # in-app path: notify_llm_unreachable's gate is closed
    assert settings.telegram_notify_enabled is False
