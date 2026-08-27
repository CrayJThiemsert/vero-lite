"""Shared pytest fixtures."""

import os
import socket
from collections.abc import Iterator
from typing import Any

import pytest

from services.api.config import settings
from services.engine import demo_events
from services.engine.economic_impact import clear_economic_producers
from services.engine.registry import registry
from tests import db_support

# PLAN-0047 Step 1: the legacy suites exercise business logic with authn OFF;
# auth behavior is covered explicitly in tests/api/test_api_auth.py (which
# monkeypatches it back on per-test). Attribute-level (not env) so dev (.env
# present) and CI (no .env) collect identically.
settings.api_auth_enabled = False


@pytest.fixture(autouse=True)
def _reset_registry() -> Iterator[None]:
    """Reset the process-wide vertical registry around every test (PLAN-0005 R5).

    autouse so no test that registers an adapter or handler can leak
    state into another (PLAN-0005 C-4). Also clears the module-global
    economic-impact producer registry (ADR-0030 / PLAN-0071) so a
    discovery-registered ฿ producer cannot leak an ``economic_impact`` trace
    step into another test's action.
    """
    registry.reset()
    clear_economic_producers()
    yield
    registry.reset()
    clear_economic_producers()


@pytest.fixture(autouse=True)
def _arm_schema_reset() -> Iterator[None]:
    """Arm the once-per-test ``public`` schema reset in ``tests.db_support``.

    The reset itself happens lazily, inside the first ``create_test_engine()``
    call of the test, so a non-DB test never pays for a connection. autouse so
    no DB test can inherit tables or rows from the test before it — or from an
    aborted ``pytest`` process (``create_all`` is ``checkfirst=True`` and would
    silently adopt the residue).
    """
    db_support.arm_schema_reset()
    yield


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


class OutboundNetworkBlocked(BaseException):
    """Raised when the offline suite tries to open a socket off this box.

    A ``BaseException``, deliberately: the application layer catches
    ``RuntimeError`` (translate) and bare ``Exception`` (phrase) in order to
    DEGRADE gracefully when a model is unavailable, and ``httpx`` wraps ``OSError``
    into its own connect errors. If this guard raised any of those, an accidental
    live call would be silently absorbed by exactly the code paths designed to
    tolerate an outage — blocked, but with nobody learning it had been attempted.
    Bypassing all of them makes it loud.

    A test that wants to exercise graceful degradation should install its own stub
    raising ``OllamaError``. That tests the contract; this guards the network.
    """


#: Loopback only. The suite legitimately talks to the disposable Postgres on
#: localhost; everything else is off-box and therefore not "offline".
_LOOPBACK = frozenset({"127.0.0.1", "::1", "localhost", "0.0.0.0", ""})  # noqa: S104


@pytest.fixture(autouse=True)
def _no_outbound_network(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Guarantee no test reaches off this box (test isolation).

    The same shape as ``_no_real_telegram`` above, one layer out, and added for the
    same reason: a dev box whose ``.env`` points at a REACHABLE MS-S1 lets the
    "offline" suite run a live model. That is not hypothetical. Wiring the AC-9b
    translate seam turned ``tests/api/test_insights_query.py``'s
    deliberately-unstubbed case into a live call, and it ran ``gpt-oss:20b`` on
    MS-S1 twice before anyone noticed — a host-state action, which CLAUDE.md §8
    requires explicit Cray approval for. Care was not enough; the suite has to be
    structurally incapable of it.

    **The guard sits at the socket, not at the client.** The first version patched
    ``OllamaClient``'s methods and broke 38 tests that exercise the client itself
    against a mocked transport — they never touch the network, so blocking them
    protected nothing and cost coverage. What actually needs forbidding is the
    *connection*: a mocked ``httpx`` transport opens no socket, so those tests are
    untouched, while a real call to MS-S1 (or any remote API) is refused whatever
    library makes it.

    Note what the guard does NOT rely on: it does not check the model name, the
    configured host, or reachability. Any of those would make the protection
    contingent on configuration, and configuration is precisely what varies between
    CI (no ``.env``) and a dev box (``.env`` pointing at a live host).

    Opt out with ``@pytest.mark.host_state``, which also makes a live run visible in
    the test id so it can never be mistaken for an offline one.
    """
    if request.node.get_closest_marker("host_state"):
        return

    real_connect = socket.socket.connect

    def _guarded_connect(sock: socket.socket, address: Any, *args: Any, **kwargs: Any) -> Any:
        # AF_UNIX addresses are plain strings/bytes — on-box by definition.
        host = str(address[0]) if isinstance(address, tuple) and address else None
        if host is not None and host not in _LOOPBACK:
            raise OutboundNetworkBlocked(
                f"the offline suite tried to connect to {host} — off this box. Stub the "
                "client in this test, or mark it @pytest.mark.host_state if it is a "
                "deliberate live run (CLAUDE.md §8 — needs explicit Cray go)."
            )
        return real_connect(sock, address, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", _guarded_connect)


# --- PLAN-0107 AC-12: a floor under the executed DB-test count -----------------
#
# The gap: `tests/db_support.py` turns an unreachable Postgres into
# `pytest.skip(_UNREACHABLE)` (`:249`, `:256`) with no floor anywhere. The CI job
# PROVIDES a postgres service, but if it were unreachable the whole DB layer would
# drop silently and `pytest -q` would still exit 0 — 475 tests' worth of coverage
# gone, reported as a pass.
#
#: Measured baseline: **475** executed DB-backed tests (session 257, full suite,
#: `CI=1`, real Postgres, 4477 collected). The floor sits deliberately far below it.
_DB_TEST_BASELINE = 475
#: ~16% of margin. The floor exists to catch a COLLAPSE (the layer vanished), not
#: drift — a tight floor would redden on ordinary test churn and get raised until it
#: meant nothing. FAILURE MODE, stated so it is never mistaken for the other one:
#: **RED on shrink, loud** — it can fail a green run, and it can NEVER turn a failing
#: run into a passing one.
_DB_TEST_FLOOR = 400

#: Measured, not assumed: both `pytest -q` (no path — pytest fills this from
#: `testpaths`) and `pytest tests -q` report exactly this. A narrower run carries its
#: own paths here, which is how a partial run is recognised and left alone — without
#: this, `pytest one_module.py` under CI would trip the floor every time (measured:
#: one module = 7 executed DB tests).
_FULL_SUITE_ARGS = ["tests"]


def db_floor_verdict(executed: int, ci: str | None, args: list[str]) -> str | None:
    """The floor decision, pure so the unit suite can drive it (AC-12).

    Returns the failure message, or ``None`` when the run passes the floor — which
    includes every run the floor does not govern (local, or a partial selection).
    """
    if not ci:
        return None
    if list(args) != _FULL_SUITE_ARGS:
        return None
    if executed >= _DB_TEST_FLOOR:
        return None
    return (
        f"DB-TEST FLOOR: only {executed} DB-backed test(s) executed, floor is "
        f"{_DB_TEST_FLOOR} (baseline {_DB_TEST_BASELINE}). The database layer did not "
        "run. A mass skip reads as a pass on the summary line, so this fails the run "
        "instead — check that the postgres service is reachable and TEST_DATABASE_URL "
        "points at it."
    )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Fail a CI full-suite run whose DB layer silently vanished (AC-12)."""
    message = db_floor_verdict(
        len(db_support.EXECUTED_DB_TESTS),
        os.environ.get("CI"),
        list(session.config.args),
    )
    if message is None:
        return
    print(f"\n{message}")
    session.exitstatus = 1
