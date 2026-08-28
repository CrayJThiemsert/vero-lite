"""Authoring guards that hold for EVERY vertical — present and future.

Both rules here exist because a defect survived in a shipped dataset for six
weeks while every count-based check stayed green, and because the vertical that
will actually carry the pilot does not exist yet. A guard that names four
verticals is a roster; these are rules.

**The goal/parameter rule.** ``generate_judgment`` threads the running
procedure's ``goal`` into the *trusted* system instruction of every call, while
the dataset supplies the event the model judges. Nothing checked that the two
describe the same physical quantity. Measured 2026-08-28: ``energy.yaml``
supplies ``temperature`` in celsius while ``substation_health_sweep``'s goal —
re-themed by PLAN-0070 on 2026-07-13 and never propagated to the fixture —
instructs the model to read *feeder current* against ``rated_current_a``. The
challenger model detected the contradiction and refused the pinned action; the
gold set scored that refusal as the error. **A model reading its directive
carefully was penalised for it, and the resulting numbers measured a fixture,
not a capability.**

The matcher is deliberately loose, because the alternative is a guard that
forces authors to contort goal prose into fixture vocabulary. Measured against
all four shipped datasets: an exact-substring rule on the raw parameter flags
three of four, and **two of those three are false** — ``dissolved_oxygen``
against a goal that writes "dissolved-oxygen", and ``repair_quote_thb`` against
one that writes "quoted repair". Splitting on ``_`` and keeping tokens of
:data:`_MIN_TOKEN` characters or more flags exactly one, and it is the real one.
The length floor is what drops unit and currency codes (``thb``, ``mg``) without
a hand-maintained stop-list that would itself go stale.
"""

from __future__ import annotations

from dataclasses import dataclass

_MIN_TOKEN = 4
"""Shortest parameter token the rule will look for.

Four characters is not a round number chosen for tidiness: it is the smallest
floor that drops every unit/currency code in the shipped datasets (``thb``) while
keeping every domain word (``quote``, ``oxygen``, ``repair``). A stop-list would
need editing for each new vertical's units — exactly the roster this module
exists to avoid.
"""


@dataclass(frozen=True)
class GoalCoverage:
    """Whether a dataset's measured quantity is named in the goal it threads.

    Carries the tokens and the matches rather than a bare bool so a failing guard
    can say WHICH words it looked for and did not find. A red that names nothing
    is a red the next person deletes.
    """

    parameter: str
    tokens: tuple[str, ...]
    matched: tuple[str, ...]

    @property
    def covered(self) -> bool:
        return bool(self.matched)

    def describe(self) -> str:
        """A one-line explanation fit for an assertion message."""
        if not self.tokens:
            return (
                f"reading_parameter {self.parameter!r} yielded no token of "
                f"{_MIN_TOKEN}+ characters to look for"
            )
        if self.covered:
            return f"goal names {list(self.matched)} from reading_parameter {self.parameter!r}"
        return (
            f"goal names NONE of {list(self.tokens)} (from reading_parameter "
            f"{self.parameter!r}) — the directive and the event describe different quantities"
        )


def parameter_tokens(parameter: str) -> tuple[str, ...]:
    """The significant words of a ``reading_parameter``, normalised for matching."""
    parts = parameter.replace("-", "_").lower().split("_")
    return tuple(part for part in parts if len(part) >= _MIN_TOKEN)


def goal_coverage(parameter: str, goal: str | None) -> GoalCoverage:
    """Does ``goal`` name the quantity ``parameter`` measures?

    Substring matching absorbs ordinary inflection for free (``quote`` inside
    ``quoted``), and ``-``/``_`` are folded together so a hyphenated goal phrase
    matches an underscored parameter.
    """
    tokens = parameter_tokens(parameter)
    haystack = (goal or "").replace("-", "_").lower()
    matched = tuple(token for token in tokens if token in haystack)
    return GoalCoverage(parameter=parameter, tokens=tokens, matched=matched)


def missing_handler_verticals(verticals: list[str], registered: dict[str, list[str]]) -> list[str]:
    """Which of ``verticals`` have an EMPTY registered-handler list.

    The α probe and the whole ``suggested_handler`` enum constraint are built from
    the registry. A vertical that fails to register does not error — it yields an
    empty enum, which silently removes the schema constraint and lets the model
    emit any string at all with nothing to catch it. Registry auto-discovery is
    deliberately *failure-isolated* (it logs and skips a broken vertical rather
    than aborting the others), so discovery alone cannot close this: the caller
    has to assert the outcome. A negative check with no positive control is
    satisfied by an empty list, which is precisely the failure being guarded.
    """
    return sorted(vertical for vertical in verticals if not registered.get(vertical))
