"""AC-3 — the ordering tripwire for the cross-run substrate (PLAN-0088 Step 1).

Same doctrine as ``test_load_run_ordering_guard.py``: this box's wall clock steps
BACKWARDS, so ``services/db/run_analytics.py`` must never ``ORDER BY`` a raw
wall-clock column (``started_at`` / ``created_at`` / ``updated_at``). Ordering a
``date_trunc`` bucket label — or a non-wall-clock grouping column, or in Python —
is allowed; ordering the raw column is a static error here.

The guard also asserts the module documents its own ±1 s skew tolerance +
day-or-coarser bucketing rule, and pins that it fires on the pattern it forbids.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MODULE = _REPO_ROOT / "services" / "db" / "run_analytics.py"

_WALL_CLOCK = frozenset({"started_at", "created_at", "updated_at"})
_ORDER_WRAPPERS = {"desc", "asc", "nullsfirst", "nullslast"}

#: The vocabulary the ``services/``-wide scan uses (PLAN-0099 D4). The three names
#: above were correct for the substrate this guard was born in; the tables built
#: afterwards stamp differently-named columns, and every one of the picks PLAN-0099
#: fixes was invisible to the original set. That is the precise sense in which the
#: old enumeration was superseded by new information rather than wrong when written.
#:
#: **The limit is stated because the scan cannot hide it.** These are nine
#: hand-picked names. A timestamp column named anything else is invisible here, so
#: the completeness this guard backs is scoped to the vocabulary — a future stamp
#: column either joins this set or joins the blind spot.
_WALL_CLOCK_WIDE = _WALL_CLOCK | {
    "entered_at",
    "accepted_at",
    "opened_at",
    "linked_at",
    "occurred_at",
    "fired_at",
}


def _unwrap(node: ast.expr) -> ast.expr:
    """Strip ``.desc()`` / ``.asc()`` / ``.nulls*()`` wrappers to the core sort key."""
    while (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in _ORDER_WRAPPERS
    ):
        node = node.func.value
    return node


def _wall_clock_sort_key(arg: ast.expr, vocabulary: frozenset[str] = _WALL_CLOCK) -> str | None:
    """The wall-clock column this ``order_by`` argument sorts on, or None.

    ``PipelineRun.started_at`` / ``…started_at.desc()`` → ``"started_at"`` (the raw
    value is the sort key). ``func.date_trunc('day', started_at)`` → None (the wall
    clock is an *argument* to a bucketing function, not the sort key). ``sa.text('…
    started_at …')`` → ``"started_at"`` (raw column named in raw SQL).

    Returns the NAME rather than a bool so the widened scan can build an allowlist
    keyed on (file, column) — line numbers move on every edit and would turn the
    ledger into a maintenance tax that nobody keeps honest.
    """
    core = _unwrap(arg)
    if isinstance(core, ast.Attribute) and core.attr in vocabulary:
        return core.attr
    if isinstance(core, ast.Name) and core.id in vocabulary:
        return core.id
    if isinstance(core, ast.Call):
        for a in core.args:
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                for word in sorted(vocabulary):
                    if word in a.value:
                        return word
    return None


def _orders_by_wall_clock(arg: ast.expr, vocabulary: frozenset[str] = _WALL_CLOCK) -> bool:
    """True if this ``order_by`` argument sorts on a RAW wall-clock column."""
    return _wall_clock_sort_key(arg, vocabulary) is not None


def offending_lines(tree: ast.Module, vocabulary: frozenset[str] = _WALL_CLOCK) -> set[int]:
    """Lines with an ``order_by(...)`` sorting on a raw wall-clock column."""
    return {line for line, _column in offending_sites(tree, vocabulary)}


def offending_sites(
    tree: ast.Module, vocabulary: frozenset[str] = _WALL_CLOCK
) -> set[tuple[int, str]]:
    """``(line, column)`` for every ``order_by(...)`` sorting on a raw wall-clock column."""
    sites: set[tuple[int, str]] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "order_by"
        ):
            for arg in node.args:
                column = _wall_clock_sort_key(arg, vocabulary)
                if column is not None:
                    sites.add((node.lineno, column))
                    break
    return sites


def cross_row_timestamp_comparisons(
    tree: ast.Module, vocabulary: frozenset[str] = _WALL_CLOCK_WIDE
) -> set[int]:
    """Lines comparing one stored wall-clock column against ANOTHER.

    The second disease shape, and the one no existing guard could see: a comparison
    has no "position" and no ``order_by`` call to scan for. The concrete shape being
    pinned is ``q.entered_at <= accepted.accepted_at`` — two stamps written by
    separate requests in separate transactions, compared as though they were
    commensurable.

    **BOTH sides must be wall-clock attributes.** That is what separates the disease
    from the legitimate use: comparing a stored stamp against a caller-supplied bound
    is how ``as_of`` views and month-bounded exports work
    (``AuditLog.occurred_at >= start``), and those are correct. Only a column-against-
    column comparison is asking the clock to order two independent writes.

    General wall-clock-comparison detection is deliberately NOT attempted. It is a
    much harder AST problem, and a guard that matches everything gets suppressed
    while a guard that matches nothing is worse than none.
    """
    lines: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        operands = [node.left, *node.comparators]
        stamps = [
            operand
            for operand in operands
            if isinstance(operand, ast.Attribute) and operand.attr in vocabulary
        ]
        if len(stamps) >= 2:
            lines.add(node.lineno)
    return lines


def test_run_analytics_never_orders_by_a_wall_clock() -> None:
    tree = ast.parse(_MODULE.read_text(encoding="utf-8"), filename=str(_MODULE))
    offenders = sorted(offending_lines(tree))
    assert not offenders, (
        "services/db/run_analytics.py orders by a raw wall-clock column at lines "
        + ", ".join(map(str, offenders))
        + " — this box's wall clock steps backwards. Order by a date_trunc bucket label, "
        "a non-wall-clock column, or in Python (AC-3 / S4)."
    )


def test_module_documents_the_skew_and_bucketing_rule() -> None:
    doc = ast.get_docstring(ast.parse(_MODULE.read_text(encoding="utf-8"))) or ""
    assert "±1 s" in doc, "AC-3: the ±1 s skew tolerance must be documented in the module docstring"
    assert (
        "day or coarser" in doc
    ), "AC-3: the day-or-coarser bucketing rule must be documented in the module docstring"


def test_the_guard_fires_on_the_pattern_it_forbids() -> None:
    """A guard that matches nothing is worse than none — pin what it does and does not catch."""
    forbidden_plain = ast.parse("q = select(X).order_by(PipelineRun.started_at)\n")
    assert offending_lines(forbidden_plain) == {1}

    forbidden_desc = ast.parse("q = select(X).order_by(PipelineRun.started_at.desc())\n")
    assert offending_lines(forbidden_desc) == {1}

    forbidden_text = ast.parse("q = select(X).order_by(sa.text('started_at DESC'))\n")
    assert offending_lines(forbidden_text) == {1}

    allowed_bucket = ast.parse(
        "q = select(X).order_by(func.date_trunc('day', PipelineRun.started_at))\n"
    )
    assert offending_lines(allowed_bucket) == set(), "ordering a date_trunc bucket label is allowed"

    allowed_label = ast.parse("q = select(X).order_by(PipelineRun.status)\n")
    assert offending_lines(allowed_label) == set(), "ordering a non-wall-clock column is allowed"


# --------------------------------------------------------------------------- #
# PLAN-0099 Step 4 (AC-7) — the SAME machinery, widened to all of services/
#
# Not new AST machinery, deliberately: the two things this scan has to get right —
# unwrapping `.desc()` off a sort key, and exempting a wall clock that appears as an
# ARGUMENT to a bucketing function rather than as the key itself — are already solved
# above and already pinned by their own fires-on-what-it-forbids test. Widening scope
# and vocabulary reuses that; reimplementing it would mean re-earning both exemptions.
#
# The single-module test above is untouched and stays STRICTER: run_analytics.py gets
# a zero-hit rule with no allowlist at all. This widened scan is allowlist-backed,
# because a display list ordered newest-first is a legitimate thing for an endpoint to
# do and a guard that forbade it would be turned off within a week.
# --------------------------------------------------------------------------- #

_SERVICES = _REPO_ROOT / "services"

#: **Measured, not recalled.** The widened scan run against `services/` extracted from
#: the Step 1 boundary commit `2252ac9` — i.e. the tree BEFORE Step 3 re-keyed
#: anything. Nine names, twelve hits, matching PLAN-0099's §Coverage ledger site for
#: site. The same scan with the guard's ORIGINAL three-name vocabulary yields exactly
#: two — `runs.py` and `persistence.py`, precisely the pair the load_run guard's
#: docstring enumerated. That is the measurement behind "superseded by new info": the
#: old enumeration was right for its vocabulary, and the tables built afterwards stamp
#: differently-named columns on correctness paths.
#:
#: This constant exists as AC-7's NARROWING TRIPWIRE. A future edit that quietly drops
#: a name from the vocabulary, or narrows the scan's scope, makes the arithmetic below
#: stop adding up — which is the fake-done shape this AC names as rejection-grade
#: rather than a pass.
_PRE_FIX_LEDGER: dict[tuple[str, str], int] = {
    ("services/api/routers/cases.py", "opened_at"): 1,
    ("services/api/routers/cases.py", "entered_at"): 3,
    ("services/api/routers/runs.py", "started_at"): 1,
    ("services/db/case_events.py", "opened_at"): 1,
    ("services/db/evidence_pack.py", "entered_at"): 2,
    ("services/db/evidence_pack.py", "accepted_at"): 1,
    ("services/db/repair_case_closeout.py", "entered_at"): 1,
    ("services/db/repair_spend_export.py", "linked_at"): 1,
    ("services/engine/procedures/persistence.py", "created_at"): 1,
}

#: The survivors, each reason CONFIRMED against the surrounding code rather than
#: inherited from the PLAN's prose. Two of these sit on correctness paths, and saying
#: "display" about them would have been the exact mistake this ledger is supposed to
#: prevent — so they are described by what is actually consumed: the SET, not the
#: ORDER.
_ALLOWLIST: dict[tuple[str, str], tuple[int, str]] = {
    ("services/api/routers/cases.py", "opened_at"): (
        1,
        "GET /api/cases — newest-first display list. It carries a truncating `limit`, "
        "so a backward step could in principle push a boundary case off the first "
        "page; that is a paging artefact on a screen a human is reading, and no "
        "correctness consumer reads this order.",
    ),
    ("services/api/routers/cases.py", "entered_at"): (
        3,
        "Three quote/justification list reads. Two render full lists into response "
        "tuples (no positional pick anywhere). The third is `_case_quotes`, which DOES "
        "feed a correctness path — the 422 not-the-cheapest rule and the figure the "
        "acceptance stores — but what those consume is `min(...)` over the whole list "
        "and a lookup by `quote_id`. Both are order-insensitive; the SET is load "
        "bearing and the ORDER is not.",
    ),
    ("services/api/routers/runs.py", "started_at"): (
        1,
        "GET /runs — newest-first rows a human reads. PLAN-0099 records this as a "
        "decision rather than an oversight: a backward step can transiently reorder "
        "adjacent rows in a display list, and no correctness consumer exists.",
    ),
    ("services/db/case_events.py", "opened_at"): (
        1,
        "`governed_case_facts` iterates EVERY open case, so the order changes the "
        "sequence of the returned list and never which facts are in it. It exists for "
        "projection-fingerprint stability and carries a deterministic `case_id` "
        "tiebreak, so identical data fingerprints identically.",
    ),
    ("services/db/evidence_pack.py", "entered_at"): (
        1,
        "The quotes read feeding the pack. Everything computed from it is "
        "order-insensitive — `min()`, `sum()`, a set for the distinct-vendor count, "
        "and a lookup by `quote_id`; only the `vendors` tuple carries the order, and "
        "that is a display field.",
    ),
}

#: The five PLAN-0099 silenced, and what silenced each. Kept as data rather than prose
#: so that a regression names itself instead of leaving the next reader to diff a
#: ledger against a scan by eye.
_SILENCED: dict[tuple[str, str], tuple[int, str]] = {
    ("services/engine/procedures/persistence.py", "created_at"): (
        1,
        "load_run, re-keyed (seq, step_result_id) — D3, the original deferral",
    ),
    ("services/db/evidence_pack.py", "accepted_at"): (
        1,
        "latest_accepted_quote, now seq.desc() alone — D2, the DOA gate's input",
    ),
    ("services/db/repair_case_closeout.py", "entered_at"): (
        1,
        "latest_closeout, now seq.desc() — SD-3(a), the month-end THB figure",
    ),
    ("services/db/evidence_pack.py", "entered_at"): (
        1,
        "the justifications ordering behind the [-1] pick, now seq — SD-3(b)",
    ),
    ("services/db/repair_spend_export.py", "linked_at"): (
        1,
        "the export's governed_by_case last-write-wins, now seq — SD-3(c)",
    ),
}


def _scan_services(vocabulary: frozenset[str] = _WALL_CLOCK_WIDE) -> dict[tuple[str, str], int]:
    """``{(relative path, column): count}`` for every wall-clock ``order_by`` in services/.

    Keyed on the column NAME rather than the line number on purpose: a ledger keyed on
    lines is invalidated by every unrelated edit above it, and a ledger nobody can
    afford to keep accurate is a ledger that gets rubber-stamped. The COUNT is what
    keeps the key precise — a second `entered_at` ordering appearing in a file that
    already allowlists one is still a new hit.
    """
    counts: dict[tuple[str, str], int] = {}
    for path in sorted(_SERVICES.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for _line, column in offending_sites(tree, vocabulary):
            key = (path.relative_to(_REPO_ROOT).as_posix(), column)
            counts[key] = counts.get(key, 0) + 1
    return counts


def _scan_services_for_comparisons() -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in sorted(_SERVICES.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        found = cross_row_timestamp_comparisons(tree)
        if found:
            counts[path.relative_to(_REPO_ROOT).as_posix()] = len(found)
    return counts


def test_the_widened_vocabulary_is_not_quietly_narrowed() -> None:
    """AC-7's narrowing tripwire, at its cheapest: the vocabulary itself.

    The easiest way to make a scan pass is to stop looking for things. This pins both
    the size and the containment, so dropping `accepted_at` to silence a new hit is a
    test failure rather than a green run.
    """
    assert len(_WALL_CLOCK_WIDE) == 9
    assert _WALL_CLOCK < _WALL_CLOCK_WIDE, "the widened set must still contain the original three"


def test_the_ledger_accounts_for_every_pre_fix_site() -> None:
    """12 = 7 allowlisted + 5 fixed. Stated as arithmetic, not as a claim in prose."""
    combined: dict[tuple[str, str], int] = {}
    for key, (count, _why) in _ALLOWLIST.items():
        combined[key] = combined.get(key, 0) + count
    for key, (count, _why) in _SILENCED.items():
        combined[key] = combined.get(key, 0) + count

    assert combined == _PRE_FIX_LEDGER, (
        "the allowlist plus the fixed sites no longer reconstruct the pre-fix "
        "measurement — either a site was dropped from the ledger without being fixed, "
        "or one was declared fixed that the scan never saw"
    )
    assert sum(_PRE_FIX_LEDGER.values()) == 12
    assert sum(count for count, _ in _ALLOWLIST.values()) == 7
    assert sum(count for count, _ in _SILENCED.values()) == 5


def test_every_wall_clock_ordering_in_services_is_allowlisted_with_a_reason() -> None:
    """The live scan must equal the allowlist EXACTLY — both directions matter.

    A new hit means a wall-clock ordering landed without anyone deciding it was
    display-only. A stale entry means the ledger is describing code that no longer
    exists, which is how an audited allowlist decays into a list nobody rereads.
    """
    live = _scan_services()
    expected = {key: count for key, (count, _why) in _ALLOWLIST.items()}
    assert live == expected
    assert all(reason.strip() for _count, reason in _ALLOWLIST.values()), (
        "every allowlist entry carries a reason — an entry without one is a "
        "suppression, not a decision"
    )


def test_the_sites_plan_0099_fixed_do_not_come_back() -> None:
    """Named individually so a regression says WHICH pick reverted, not just 'a diff'."""
    live = _scan_services()
    for key, (_count, why) in _SILENCED.items():
        allowed = _ALLOWLIST.get(key, (0, ""))[0]
        assert live.get(key, 0) == allowed, f"{key[0]} orders by {key[1]} again — {why}"


def test_no_cross_row_timestamp_comparison_survives_in_services() -> None:
    """The second disease shape, gone: two stored stamps compared against each other.

    Measured at the Step 1 boundary, this scan found exactly two — `evidence_pack.py`
    and its duplicate in `cases.py`, the pair PLAN-0099 D1 deleted rather than patched.
    There is no allowlist here on purpose: a legitimate comparison has a
    caller-supplied bound on one side, which this check already exempts, so anything it
    catches is the disease.
    """
    assert _scan_services_for_comparisons() == {}


# The frozen pre-fix shapes. Transcribed from `services/db/evidence_pack.py` as it
# stood at `2252ac9`, so the guard is pinned against the code it was built to catch
# rather than against a paraphrase of it.
_FROZEN_PRE_FIX_PICK = """
q = (
    select(RepairCaseAcceptedQuote)
    .where(RepairCaseAcceptedQuote.case_id == case_id)
    .order_by(
        RepairCaseAcceptedQuote.accepted_at.desc(),
        RepairCaseAcceptedQuote.accepted_id.desc(),
    )
    .limit(1)
)
"""

_FROZEN_PRE_FIX_COMPARISON = """
lowest = min(
    (q.amount_thb for q in quotes if q.entered_at <= accepted.accepted_at),
    default=None,
)
"""


def test_the_widened_scan_fires_on_the_frozen_pre_fix_pick() -> None:
    """A guard that matches nothing is worse than none — so pin what it catches.

    Line 3, not the line ``.order_by(`` sits on: the reported line is where the query
    CHAIN begins, because that is the ``Call`` node's own position. PLAN-0099's ledger
    documents the same offset, which is why its numbers sit a couple of lines above
    the argument lines cited elsewhere in that PLAN — same sites, not different ones.
    """
    assert offending_sites(ast.parse(_FROZEN_PRE_FIX_PICK), _WALL_CLOCK_WIDE) == {
        (3, "accepted_at")
    }
    # ...and the ORIGINAL vocabulary is blind to it, which is the whole reason for the
    # widening and the measurement behind "superseded by new info".
    assert offending_sites(ast.parse(_FROZEN_PRE_FIX_PICK), _WALL_CLOCK) == set()


def test_the_widened_scan_is_silent_on_the_seq_keyed_pick() -> None:
    """The shape that replaced it must NOT fire, or the guard forbids its own fix."""
    fixed = ast.parse("q = select(X).where(X.case_id == case_id).order_by(X.seq.desc()).limit(1)\n")
    assert offending_sites(fixed, _WALL_CLOCK_WIDE) == set()


def test_the_comparison_check_fires_on_the_frozen_pre_fix_comparison() -> None:
    assert cross_row_timestamp_comparisons(ast.parse(_FROZEN_PRE_FIX_COMPARISON)) == {3}


def test_the_comparison_check_is_silent_on_the_shapes_that_replaced_it() -> None:
    """Three negatives, each a real shape this codebase relies on.

    A stored-field read is what D1 replaced the comparison WITH. The `as_of` shape is a
    legitimate view-as-of feature (`GET /cases/{id}/tasks`), and the month-bounded
    export filter is the same family: one side is a caller-supplied instant, so the
    clock is being used as a QUESTION rather than as an ordering between two writes.
    """
    stored = ast.parse("lowest = accepted.lowest_amount_at_acceptance_thb\n")
    assert cross_row_timestamp_comparisons(stored) == set()

    as_of = ast.parse("late = [e for e in events if e.occurred_at <= moment]\n")
    assert cross_row_timestamp_comparisons(as_of) == set(), (
        "comparing a stored stamp against a caller-supplied instant is the as_of "
        "feature, not the defect"
    )

    bounded = ast.parse("q = select(X).where(AuditLog.occurred_at >= start)\n")
    assert cross_row_timestamp_comparisons(bounded) == set()
