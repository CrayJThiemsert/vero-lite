"""A controllable clock for the forcing tests — PLAN-0099 D5.

The defect this PLAN fixes needs a clock that steps BACKWARDS between two writes.
On the dev box that happens on its own — measured at 20 backward steps per 300 s,
every one >= 400 ms — but only against a 90-166 ms vulnerable window, which is a
~0.9% chance per execution. A test that waits for it is a coin flip that passes
99.1% of the time and proves nothing (PLAN-0099 D5).

So the clock is driven instead of observed.

**Why a settable instant rather than a scripted sequence.** The obvious shape is a
list of instants returned one per ``now()`` call. It is also brittle: it silently
depends on exactly how many times a request handler happens to call ``now()``, so
an unrelated refactor that adds one call shifts every later stamp and the test
fails somewhere far from the change. Here the test sets the instant BETWEEN HTTP
calls and every ``now()`` within one call returns the same value — the property the
fixtures actually care about ("this write is stamped before that one") stated
directly, with no dependence on call counts.

Usage, through the real HTTP path (never a stubbed writer):

    clock = Clock(T0)
    monkeypatch.setattr(cases_router, "datetime", clock.datetime_class())
    await _add_quote(...)                 # stamped T0
    clock.set(T1)
    await _accept(...)                    # stamped T1
    clock.set(T1 - timedelta(milliseconds=5))
    await _add_quote(...)                 # stamped BEFORE the acceptance

``calls`` counts every ``now()`` the patched module made, so a test can assert the
clock was actually consulted — a patch applied to the wrong module reads as a
perfectly green test otherwise, which is the shape of a probe that protects nothing.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, tzinfo


class Clock:
    """A settable instant, exposed as a ``datetime`` subclass for monkeypatching."""

    def __init__(self, start: datetime) -> None:
        if start.tzinfo is None:
            raise ValueError(
                "the forcing clock must start at an AWARE instant — a naive stamp would "
                "compare against the aware column values the writers produce and raise, "
                "which surfaces as an ERROR rather than the assertion mismatch the AC "
                "requires as its RED evidence"
            )
        self._now = start
        self.calls = 0

    def set(self, value: datetime) -> None:
        """Pin the instant every subsequent ``now()`` returns."""
        self._now = value

    def shift(self, **delta: float) -> None:
        """Move the instant. A NEGATIVE delta is the backward step under test."""
        self._now = self._now + timedelta(**delta)

    def back(self, milliseconds: float) -> None:
        """The measured failure mode, named: the wall clock stepping backwards."""
        self.shift(milliseconds=-milliseconds)

    @property
    def now_value(self) -> datetime:
        return self._now

    def datetime_class(self) -> type[datetime]:
        """A ``datetime`` subclass whose ``now()`` reads this clock.

        A subclass rather than a bare function so the patched symbol still satisfies
        every other use of ``datetime`` in the target module — annotations,
        ``datetime.min``, ``isinstance`` checks — and the patch cannot break a code
        path it was not aiming at.
        """
        clock = self

        class _ClockDatetime(datetime):
            @classmethod
            def now(cls, tz: tzinfo | None = None) -> datetime:  # type: ignore[override]
                clock.calls += 1
                value = clock.now_value
                return value if tz is None else value.astimezone(tz)

        return _ClockDatetime


def utc(
    year: int = 2026,
    month: int = 7,
    day: int = 31,
    hour: int = 9,
    minute: int = 0,
    second: int = 0,
    microsecond: int = 0,
) -> datetime:
    """A fixed aware instant. Defaults chosen so a fixture reads as one working day."""
    return datetime(year, month, day, hour, minute, second, microsecond, tzinfo=UTC)
