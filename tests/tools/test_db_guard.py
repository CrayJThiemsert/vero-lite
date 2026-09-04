"""Unit half of PLAN-0120 Step 1 — the guard's pure functions, no database.

Every test carries exactly ONE claim, so a mutation can only ever hide behind one
assertion at a time (the `test_probe_battery.py` doctrine applied here).
"""

from __future__ import annotations

import pytest

from tests import db_guard

#: The name this checkout actually resolves to, used so the key tests are about a real
#: input rather than a shape invented for the test.
SAMPLE_DB = "vero_lite_test_bb36873b"
#: The credential below is the throwaway local dev one, identical to the value already in
#: docker-compose.yml and ci.yml — hence the allowlist pragma rather than a fake string,
#: which would make the URL tests about a shape this project never actually uses.
SAMPLE_URL = (
    "postgresql+asyncpg://vero:vero@localhost:5442/"  # pragma: allowlist secret
    "vero_lite_test_bb36873b"
)


def test_the_contended_exit_code_cannot_be_mistaken_for_a_pytest_verdict() -> None:
    """pytest owns 0-5; 128+ is signal death. 75 must sit strictly between them.

    Without this, a future "let's use 1" would make every contended session read as an
    ordinary test failure — which is the fabricated-defect class ADR-0018 D8 exists to
    close, re-made one layer down.
    """
    assert 5 < db_guard.CONTENDED_EXIT < 128, f"rc={db_guard.CONTENDED_EXIT}"


def test_the_advisory_key_is_deterministic_for_one_database_name() -> None:
    """Two processes must derive the SAME key from the same name or they never collide."""
    assert db_guard.advisory_key(SAMPLE_DB) == db_guard.advisory_key(SAMPLE_DB)


def test_two_database_names_do_not_share_a_key() -> None:
    """🟢 The control for the test above. A key function returning a constant would
    satisfy determinism perfectly and give every database on the cluster one lock."""
    assert db_guard.advisory_key(SAMPLE_DB) != db_guard.advisory_key(SAMPLE_DB + "_gate")


def test_the_key_fits_a_signed_bigint() -> None:
    """``pg_try_advisory_lock(bigint)`` rejects anything outside the signed 64-bit range,
    and the failure would arrive as a Postgres error at acquisition, not here."""
    key = db_guard.advisory_key(SAMPLE_DB)
    assert -(2**63) <= key < 2**63, f"key={key}"


def test_the_lock_halves_reconstruct_the_key() -> None:
    """The classid/objid split must be lossless, or the CONTENDED path looks for a holder
    under the wrong address and reports ``holder_pid=-`` on a real collision — a reading
    indistinguishable from a clean run."""
    key = db_guard.advisory_key(SAMPLE_DB)
    classid, objid = db_guard.lock_halves(key)
    rebuilt = (classid << 32) | objid
    assert rebuilt == (key & 0xFFFFFFFFFFFFFFFF), f"key={key} classid={classid} objid={objid}"


def test_the_lock_halves_are_each_inside_the_oid_range() -> None:
    """``pg_locks.classid``/``objid`` are 32-bit ``oid`` columns; an out-of-range value
    would be a query that silently matches nothing."""
    classid, objid = db_guard.lock_halves(db_guard.advisory_key(SAMPLE_DB))
    assert 0 <= classid <= 0xFFFFFFFF and 0 <= objid <= 0xFFFFFFFF, f"{classid=} {objid=}"


def test_a_role_suffixes_the_database_name_and_nothing_else() -> None:
    """The role composes with whatever name resolved (SD-1) — it must not disturb the
    host, port or credentials, which is why the full URL is asserted rather than the
    database segment alone."""
    out = db_guard.role_suffixed(SAMPLE_URL, "gate")
    assert out == SAMPLE_URL + "_gate", out


def test_the_suffixed_url_keeps_the_password_readable() -> None:
    """🟢 The control that matters in practice: ``str(URL)`` masks the password as
    ``***``, so a naive implementation produces a URL that parses and cannot connect."""
    assert "***" not in db_guard.role_suffixed(SAMPLE_URL, "gate")


def test_the_suffixed_name_stays_inside_postgres_identifier_limit() -> None:
    """63 characters is the hard limit; the role regex caps at 16 so the longest possible
    suffixed name has to fit. Asserted rather than reasoned about."""
    longest = db_guard.role_suffixed(SAMPLE_URL, "a" * 16)
    name = longest.rsplit("/", 1)[-1]
    assert len(name) <= 63, f"len={len(name)} name={name}"


@pytest.mark.parametrize("bad", ["Gate", "a-b", "with space", "x" * 17, "role!", "../etc"])
def test_a_malformed_role_raises_instead_of_meaning_no_isolation(bad: str) -> None:
    """🔴 The load-bearing refusal. A rejected role must be LOUD: silently falling back
    to the unsuffixed name would leave the gate sharing the session's database, which is
    the single outcome the marker exists to prevent."""
    with pytest.raises(RuntimeError, match="not a valid role"):
        db_guard.validated_role(bad)


@pytest.mark.parametrize("ok", ["gate", "t12345", "a", "a" * 16, "role_2"])
def test_a_well_formed_role_is_accepted(ok: str) -> None:
    """🟢 The control: a validator that rejected everything would satisfy the test above
    perfectly and make the isolation lever unusable."""
    assert db_guard.validated_role(ok) == ok


def test_an_unset_role_is_none_not_an_error() -> None:
    """Unset is the DEFAULT everywhere — this is what keeps behaviour identical to
    before the guard shipped."""
    assert db_guard.validated_role(None) is None


def test_an_empty_role_is_treated_as_unset() -> None:
    """``VERO_TEST_DB_ROLE=`` in an env file is "unset", not a zero-length role that
    would produce a database name ending in a bare underscore."""
    assert db_guard.validated_role("") is None


def test_the_token_carries_every_measured_field() -> None:
    """🔴 CLAUDE.md §8 at the instrument's own output: the line reports what it measured,
    never a bare PASS/FAIL. A reader who cannot see the values cannot tell a working
    guard from one that only prints reassuring words."""
    guard = db_guard.TestDbGuard(SAMPLE_URL, "gate")
    token = guard.token(db_tests=7)
    for field in (
        "db=vero_lite_test_bb36873b",
        "role=gate",
        f"key={db_guard.advisory_key('vero_lite_test_bb36873b')}",
        "outcome=NOT-NEEDED",
        "holder_pid=-",
        "foreign_backends=0",
        "create_race=0",
        "release=-",
        "db_tests=7",
    ):
        assert field in token, f"missing {field!r} in {token!r}"


def test_the_guard_names_the_maintenance_database_not_the_target() -> None:
    """SD-2: the lock is taken on ``postgres`` so it PRECEDES ``CREATE DATABASE`` and
    never sits on a database a cleanup may want to drop. Asserted on the DSN because a
    guard that locked the target would still pass every other test in this file."""
    guard = db_guard.TestDbGuard(SAMPLE_URL, None)
    assert guard._admin_dsn.endswith("/postgres"), guard._admin_dsn


def test_the_holder_application_name_identifies_the_process() -> None:
    """A contention report names ``holder_app``; if the application_name were generic,
    the report would name a pid without saying what it belongs to."""
    guard = db_guard.TestDbGuard(SAMPLE_URL, "gate")
    app = guard.application_name()
    assert app.startswith("vero-pytest-guard pid=") and "role=gate" in app, app
