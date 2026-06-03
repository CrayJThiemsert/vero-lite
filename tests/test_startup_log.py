"""The app logs the PLAN-0014 Telegram arm state once at startup.

A boot diagnostic that makes a silent mis-arm visible: when the notifier is
DISARMED (e.g. the enable flag left off), per-call no-ops are silent, so the
only place a mis-arm shows up is this one-shot startup line.
"""

from __future__ import annotations

import logging

import pytest
from fastapi.testclient import TestClient

from services.api.config import settings
from services.api.main import app


def test_startup_logs_plan0014_arm_state(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    # Force a known disarmed state so the assertion is independent of the local
    # .env (the dev box may have armed it). describe_arm_state() reads settings
    # live during the lifespan, which TestClient's context manager triggers.
    monkeypatch.setattr(settings, "telegram_notify_enabled", False)
    with caplog.at_level(logging.INFO, logger="uvicorn.error"), TestClient(app):
        pass
    arm = [r.getMessage() for r in caplog.records if "PLAN-0014 Telegram notify:" in r.getMessage()]
    assert arm, "no PLAN-0014 arm-state line logged at startup"
    assert "DISARMED" in arm[0]
    assert "TELEGRAM_NOTIFY_ENABLED=false" in arm[0]
