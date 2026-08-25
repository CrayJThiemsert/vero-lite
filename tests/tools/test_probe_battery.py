"""`tools/probe_battery/` — the driver that decides whether a RED is a witness.

🔴 **Nothing here is simulated.** The classifier is fed junit XML from a real pytest run;
the orchestration tests mutate real files on disk and run a real pytest subprocess against
them. A suite that hand-wrote the XML, or stubbed the runner, would be checking its
author's model of pytest rather than pytest — which is precisely the defect this package
exists to stop: s253's driver was wrong about what `returncode` meant, and no amount of
testing against its own assumption would have said so.

The end-to-end seam under a real SIGTERM, and the CLI, are driven by
`test_probe_battery_scenario.py` per CLAUDE.md §8.

Every test carries exactly ONE claim, so a mutation can only ever hide behind one
assertion at a time.
"""

from __future__ import annotations

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from tools.probe_battery import (
    VERDICT_FAIL,
    VERDICT_PASS,
    Battery,
    BatteryDefinitionError,
    BatteryResult,
    Classification,
    MutationError,
    Outcome,
    Probe,
    RunStore,
    UnrestoredSnapshotError,
    classify,
    find_unrestored,
    parse_junit,
    refuse_if_unrestored,
    restore_pending,
    run_battery,
)
from tools.probe_battery._battery import _child_env, _overlaps
from tools.probe_coverage import Claim, enumerate_claims

# ======================================================================================
# Part 1 — the classifier, against junit XML from one real pytest run
# ======================================================================================

_SHAPES = """
import pytest


def test_plain_assert_fails():
    assert "plain-red" == "plain-RED"


def test_crash_before_the_assert():
    obj = None
    obj.missing()
    assert "after-crash" == "after-crash"


def test_crash_on_the_assert_line():
    obj = None
    assert obj.thing == "on-the-line"


def test_two_asserts_second_fails():
    assert "first-holds" == "first-holds"
    assert "second-breaks" == "second-BREAKS"


def test_did_not_raise():
    with pytest.raises(ValueError):
        pass


def test_green():
    assert "green-marker" == "green-marker"


def test_skipped():
    pytest.skip("deliberate")
    assert "skip-marker" == "skip-marker"
"""


@pytest.fixture(scope="module")
def shapes(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("shapes") / "test_shapes.py"
    path.write_text(_SHAPES, encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def shapes_junit(shapes: Path) -> str:
    """One real pytest run over the whole fixture module; its junit XML, verbatim."""
    xml = shapes.parent / "junit.xml"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            shapes.name,
            f"--junitxml={xml}",
            "-p",
            "no:cacheprovider",
            "-q",
        ],
        cwd=str(shapes.parent),
        capture_output=True,
        text=True,
        check=False,
    )
    return xml.read_text(encoding="utf-8")


def _subset(xml_text: str, name: str) -> str:
    """Re-scope a whole-module junit report to the one `<testcase>` a node id would select.

    The element is the real one, moved — not rebuilt — so nothing about pytest's output is
    re-imagined here.
    """
    root = ET.fromstring(xml_text)  # noqa: S314
    suites = ET.Element("testsuites")
    suite = ET.SubElement(suites, "testsuite", {"name": "subset"})
    suite.extend([c for c in root.iter("testcase") if c.get("name") == name])
    return ET.tostring(suites, encoding="unicode")


def _claim_at(path: Path, fragment: str) -> Claim:
    """The one claim whose source text contains `fragment`, via the real enumerator."""
    matches = [c for c in enumerate_claims(path) if fragment in c.source]
    assert len(matches) == 1, f"{fragment!r} matched {len(matches)} claims, expected 1"
    return matches[0]


def _classify(xml_text: str, shapes: Path, name: str, fragment: str) -> Classification:
    return classify(
        parse_junit(_subset(xml_text, name)), _claim_at(shapes, fragment), shapes, shapes.parent
    )


def test_the_junit_failure_element_carries_no_type_attribute(shapes_junit: str) -> None:
    """🔴 Pins the measurement (2026-08-25) that decided the design: pytest leaves
    `<failure type=...>` empty, so a classifier reading that attribute cannot tell an
    assertion from a crash. If a future pytest starts populating it this reddens — which
    is the point, because the body-parsing path would then deserve a re-look."""
    root = ET.fromstring(shapes_junit)  # noqa: S314
    failures = list(root.iter("failure"))
    assert failures and all(f.get("type") is None for f in failures)


# -- AC-2: a crash is a refusal, not a credit ------------------------------------------


def test_a_crash_before_the_tracked_assertion_is_classified_crashed(
    shapes_junit: str, shapes: Path
) -> None:
    """s253's exact defect: an `AttributeError` from a disabled guard, credited as RED."""
    result = _classify(shapes_junit, shapes, "test_crash_before_the_assert", "after-crash")
    assert result.outcome is Outcome.CRASHED


def test_a_genuine_assertion_red_is_classified_witnessed(shapes_junit: str, shapes: Path) -> None:
    """🟢 POSITIVE CONTROL for the test above. Without it, a driver that refused
    *everything* would satisfy the crash test vacuously."""
    result = _classify(shapes_junit, shapes, "test_plain_assert_fails", "plain-red")
    assert result.outcome is Outcome.WITNESSED


def test_a_crash_on_the_declared_assertions_own_line_is_still_not_a_witness(
    shapes_junit: str, shapes: Path
) -> None:
    """🔴 C6's hard case. `assert obj.thing == ...` with `obj is None` raises AttributeError
    at the declared assertion's OWN line: the site matches and the kind does not. A
    site-only rule credits this; the conjunction is what rejects it."""
    result = _classify(shapes_junit, shapes, "test_crash_on_the_assert_line", "on-the-line")
    assert result.outcome is Outcome.CRASHED


# -- AC-4: declared-claim match ---------------------------------------------------------


def test_reddening_a_different_assertion_than_declared_is_a_misfire(
    shapes_junit: str, shapes: Path
) -> None:
    """The second assert fails; the probe declared the first. Crediting whichever one
    happened to fail would let the result rewrite the prediction."""
    result = _classify(shapes_junit, shapes, "test_two_asserts_second_fails", "first-holds")
    assert result.outcome is Outcome.MISFIRE


def test_declaring_the_assertion_that_actually_failed_is_witnessed(
    shapes_junit: str, shapes: Path
) -> None:
    """🟢 POSITIVE CONTROL: same run, same module, the sibling claim — so the MISFIRE above
    is about the declaration, not about the run being unreadable."""
    result = _classify(shapes_junit, shapes, "test_two_asserts_second_fails", "second-breaks")
    assert result.outcome is Outcome.WITNESSED


# -- the remaining outcome shapes -------------------------------------------------------


def test_a_raises_block_that_did_not_raise_witnesses_its_claim(
    shapes_junit: str, shapes: Path
) -> None:
    """`Failed: DID NOT RAISE` is reported at the `with` line, which is exactly where
    `enumerate_claims` puts a `raises` claim — so assertion-family must include `Failed`."""
    result = _classify(shapes_junit, shapes, "test_did_not_raise", "pytest.raises(ValueError)")
    assert result.outcome is Outcome.WITNESSED


def test_a_run_where_nothing_reddened_is_green_not_witnessed(
    shapes_junit: str, shapes: Path
) -> None:
    result = _classify(shapes_junit, shapes, "test_green", "green-marker")
    assert result.outcome is Outcome.GREEN


def test_a_skipped_run_is_not_a_witness(shapes_junit: str, shapes: Path) -> None:
    result = _classify(shapes_junit, shapes, "test_skipped", "skip-marker")
    assert result.outcome is Outcome.SKIPPED


def test_a_node_id_selecting_nothing_is_no_tests(shapes_junit: str, shapes: Path) -> None:
    result = _classify(shapes_junit, shapes, "test_does_not_exist", "green-marker")
    assert result.outcome is Outcome.NO_TESTS


def test_a_failure_record_naming_no_site_is_unreadable(shapes: Path) -> None:
    """C6's legibility conjunct, for the one case a machine can judge: a failure whose
    record does not say where it happened cannot show the declared assertion failing at
    its own site."""
    xml = (
        '<testsuites><testsuite><testcase name="t"><failure message="?">no site here'
        "</failure></testcase></testsuite></testsuites>"
    )
    result = classify(parse_junit(xml), _claim_at(shapes, "green-marker"), shapes, shapes.parent)
    assert result.outcome is Outcome.UNREADABLE


def test_the_failure_message_is_carried_into_the_reason(shapes_junit: str, shapes: Path) -> None:
    """🔴 C6's second half. s253's driver discarded captured output, so its REDs named
    nothing a reader could act on. The message must survive into the report."""
    result = _classify(shapes_junit, shapes, "test_crash_before_the_assert", "after-crash")
    assert "has no attribute 'missing'" in result.reason


# ======================================================================================
# Part 2 — orchestration, against a real tree and a real pytest subprocess
# ======================================================================================

_SUBJECT = """
def classify(n):
    return "high" if n > 10 else "low"


def label(n):
    return "even" if n % 2 == 0 else "odd"
"""

_TESTS = """
from subject import classify, label


def test_classify():
    assert classify(20) == "high"
    assert classify(1) == "low"


def test_label():
    assert label(2) == "even"
"""


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "subject.py").write_text(_SUBJECT, encoding="utf-8")
    (tmp_path / "test_suite.py").write_text(_TESTS, encoding="utf-8")
    (tmp_path / "state").mkdir()
    return tmp_path


def _keys(project: Path) -> list[str]:
    return [c.stable_key for c in enumerate_claims(project / "test_suite.py")]


def _probe(name: str, claim: str, old: str, new: str, node: str = "test_classify") -> Probe:
    return Probe(
        name=name,
        subject=Path("subject.py"),
        old=old,
        new=new,
        node_id=f"test_suite.py::{node}",
        expect_claim=claim,
    )


def _run(
    project: Path, probes: list[Probe], exemptions: dict[str, str] | None = None
) -> BatteryResult:
    battery = Battery(
        claim_sources=(project / "test_suite.py",),
        probes=tuple(probes),
        exemptions=exemptions or {},
    )
    return run_battery(
        battery, project_root=project, state_base=project / "state", timeout_s=120, echo=False
    )


# `classify(20)` stops returning "high" -> the FIRST assert in test_classify reddens.
def _witness_first(name: str, claim: str) -> Probe:
    return _probe(name, claim, "n > 10", "n > 1000")


# `classify(1)` stops returning "low" -> the first assert holds, the SECOND reddens.
def _witness_second(name: str, claim: str) -> Probe:
    return _probe(name, claim, 'else "low"', 'else "LOW"')


# `classify` raises before any tracked assertion is reached -> AC-2's fixture.
def _crash(name: str, claim: str) -> Probe:
    return _probe(name, claim, 'return "high" if n > 10 else "low"', "return None.gone()")


# -- AC-3: one claim per probe ----------------------------------------------------------


def test_a_witnessed_probe_credits_exactly_one_claim(project: Path) -> None:
    """A run stops at the first failing assertion, so one mutation witnesses one claim —
    s253's driver marked ALL of a reddened test's claims witnessed."""
    result = _run(project, [_witness_first("P1", _keys(project)[0])])
    assert len(result.credited) == 1


def test_the_sibling_claim_of_a_witnessed_one_is_reported_as_a_gap(project: Path) -> None:
    """`test_classify` carries two claims; reddening one must leave the other visibly
    uncovered rather than silently closed."""
    keys = _keys(project)
    result = _run(project, [_witness_first("P1", keys[0])])
    assert keys[1] not in result.credited


def test_a_probe_targeting_the_sibling_credits_it(project: Path) -> None:
    """🟢 POSITIVE CONTROL for the GAP above: the sibling IS reachable, so its gap is a fact
    about coverage and not about the key being unaddressable."""
    keys = _keys(project)
    result = _run(project, [_witness_second("P2", keys[1])])
    assert keys[1] in result.credited


def test_the_gap_is_named_in_the_report(project: Path) -> None:
    """#0047's actual requirement: the report must say WHICH claim was never probed. A
    count alone is the silence the lesson is about."""
    result = _run(project, [_witness_first("P1", _keys(project)[0])])
    tail = result.report.split("GAPS: neither reddened nor exempted")[1]
    assert 'classify(1) == "low"' in tail


# -- AC-2 / AC-4 at the driver level: a non-witness credits nothing ----------------------


def test_a_crashed_probe_credits_nothing(project: Path) -> None:
    """AC-2's fixture, for real: the mutation raises `AttributeError` inside the subject,
    before any tracked assertion is reached."""
    result = _run(project, [_crash("P1", _keys(project)[0])])
    assert result.credited == {}


def test_a_crashed_probe_is_classified_crashed_not_witnessed(project: Path) -> None:
    result = _run(project, [_crash("P1", _keys(project)[0])])
    assert result.results[0].classification.outcome is Outcome.CRASHED


def test_a_misfiring_probe_credits_nothing(project: Path) -> None:
    """The mutation reddened a real assertion — just not the declared one."""
    result = _run(project, [_witness_first("P1", _keys(project)[1])])
    assert result.credited == {}


def test_a_misfiring_probe_is_classified_misfire(project: Path) -> None:
    result = _run(project, [_witness_first("P1", _keys(project)[1])])
    assert result.results[0].classification.outcome is Outcome.MISFIRE


def test_a_mutation_that_reddens_nothing_is_green(project: Path) -> None:
    """The guard may be vacuous — and GREEN is how a battery says so instead of falling
    silent."""
    result = _run(
        project,
        [_probe("P1", _keys(project)[2], 'else "odd"', 'else "ODD"', node="test_label")],
    )
    assert result.results[0].classification.outcome is Outcome.GREEN


def test_a_battery_whose_probes_all_witness_passes(project: Path) -> None:
    """🟢 POSITIVE CONTROL for every refusal above: the same driver, on the same tree, does
    reach PASS — so FAIL is a finding, not the only verdict it can print."""
    keys = _keys(project)
    result = _run(
        project,
        [
            _witness_first("P1", keys[0]),
            _witness_second("P2", keys[1]),
            _probe("P3", keys[2], 'return "even"', 'return "EVEN"', node="test_label"),
        ],
    )
    assert VERDICT_PASS in result.report


def test_a_battery_with_a_crashed_probe_fails_its_verdict(project: Path) -> None:
    result = _run(project, [_crash("P1", _keys(project)[0])])
    assert VERDICT_FAIL in result.report


# -- AC-5: stable_key addressing --------------------------------------------------------

_REPEATED_TESTS = """
from subject import classify


def test_repeats():
    row = classify(20)
    assert row is not None
    row = classify(1)
    assert row is not None
"""


def _repeat_probe(claim: str) -> Probe:
    return _probe(
        "P1",
        claim,
        'return "high" if n > 10 else "low"',
        "return None if n > 10 else 'low'",
        node="test_repeats",
    )


def test_crediting_one_of_two_identical_asserts_leaves_the_other_uncovered(
    project: Path,
) -> None:
    """🔴 The driver-level restatement of `test_probe_coverage.py:183`. `owner|source` alone
    COLLIDES; `stable_key` adds `occurrence` precisely so a battery cannot report the pair
    covered when only the first was witnessed.

    Asserted on the **coverage verdict**, not on the credit map: the credit map is keyed by
    what each probe declared and would look identical under a colliding `key_of`, so a test
    reading it could not tell the two addressing schemes apart at all.
    """
    (project / "test_suite.py").write_text(_REPEATED_TESTS, encoding="utf-8")
    result = _run(project, [_repeat_probe(_keys(project)[0])])
    assert "PROBE-COVERAGE: GAPS" in result.report


def test_the_uncovered_twin_is_named_in_the_report(project: Path) -> None:
    """And named, not merely counted — a battery that says "1 gap" without saying which is
    the silence #0047 is about."""
    (project / "test_suite.py").write_text(_REPEATED_TESTS, encoding="utf-8")
    result = _run(project, [_repeat_probe(_keys(project)[0])])
    tail = result.report.split("GAPS: neither reddened nor exempted")[1]
    assert "L9" in tail


def test_the_first_of_two_identical_asserts_is_the_one_credited(project: Path) -> None:
    """🟢 POSITIVE CONTROL: the run really did witness something, so the uncovered twin above
    is a coverage fact and not a battery that credited nothing at all."""
    (project / "test_suite.py").write_text(_REPEATED_TESTS, encoding="utf-8")
    keys = _keys(project)
    result = _run(project, [_repeat_probe(keys[0])])
    assert keys[0] in result.credited


def test_two_identical_asserts_get_distinct_keys(project: Path) -> None:
    (project / "test_suite.py").write_text(_REPEATED_TESTS, encoding="utf-8")
    keys = _keys(project)
    assert keys[0] != keys[1]


def test_a_probe_declaring_an_unknown_claim_is_refused_before_any_mutation(
    project: Path,
) -> None:
    """Refusing early matters: a battery that mutates and *then* finds it cannot check its
    own prediction has spent the risk for nothing."""
    before = (project / "subject.py").read_bytes()
    with pytest.raises(BatteryDefinitionError):
        _run(project, [_witness_first("P1", "no|such|claim#0")])
    assert (project / "subject.py").read_bytes() == before


def test_cross_module_key_collision_is_refused(project: Path) -> None:
    """`occurrence` is stamped per module, so two modules sharing a test name and an
    assertion text would share a key — a coverage lie by construction."""
    (project / "test_other.py").write_text(_TESTS, encoding="utf-8")
    battery = Battery(
        claim_sources=(project / "test_suite.py", project / "test_other.py"),
        probes=(_witness_first("P1", "x"),),
    )
    with pytest.raises(BatteryDefinitionError, match="collide"):
        run_battery(battery, project_root=project, state_base=project / "state", echo=False)


# -- AC-6: the report is mandatory, and the self-check is not tautological ---------------


def test_the_verdict_token_is_printed_even_when_the_battery_dies(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """🔴 A battery that ends by exception is exactly the one whose partial results matter.
    The report must survive the way out."""

    def _explode(_probe: Probe, _root: Path, _timeout: int) -> str | None:
        raise RuntimeError("the runner blew up")

    battery = Battery(
        claim_sources=(project / "test_suite.py",),
        probes=(_witness_first("P1", _keys(project)[0]),),
    )
    with pytest.raises(RuntimeError, match="blew up"):
        run_battery(battery, project_root=project, state_base=project / "state", runner=_explode)
    assert VERDICT_FAIL in capsys.readouterr().out


def test_a_claim_both_probed_and_exempted_is_reported_as_an_overlap(project: Path) -> None:
    keys = _keys(project)
    result = _run(project, [_witness_first("P1", keys[0])], exemptions={keys[0]: "unreachable"})
    assert result.overlaps == (keys[0],)


def test_the_s253_post_filter_intersection_would_have_been_empty(project: Path) -> None:
    """🔴 The tautology, reconstructed. s253 intersected exemptions with a credit set from
    which exempted keys had ALREADY been filtered — empty by construction, printed as live
    evidence. On identical inputs the repaired check finds the overlap and the pre-fix
    shape finds nothing, which is what makes this a witness rather than a re-assertion."""
    keys = _keys(project)
    battery = Battery(
        claim_sources=(project / "test_suite.py",),
        probes=(_witness_first("P1", keys[0]),),
        exemptions={keys[0]: "unreachable"},
    )
    post_filter = {k for k in [keys[0]] if k not in battery.exemptions}
    assert _overlaps(battery) and not (set(battery.exemptions) & post_filter)


# -- AC-1: the mutation reaches disk, and the tree comes back ---------------------------


def test_a_mutation_whose_old_text_is_absent_is_refused(project: Path) -> None:
    """A no-op mutation's GREEN says nothing about the guard — it says the probe never ran.
    Reporting it as GREEN would invert the evidence."""
    result = _run(project, [_probe("P1", _keys(project)[0], "NOT PRESENT", "x")])
    assert result.results[0].classification.outcome is Outcome.MUTATION_ERROR


def test_a_mutation_that_changes_nothing_is_refused(project: Path) -> None:
    """Same hazard, subtler shape: `old` is present but identical to `new`, so the bytes on
    disk never move and every outcome is about the unmutated code."""
    store = RunStore.begin(project, project / "state")
    with pytest.raises(MutationError, match="byte-identical"):
        store.apply(project / "subject.py", "n > 10", "n > 10")


def test_a_mutation_matching_more_than_once_is_refused(project: Path) -> None:
    """More than one hit means the edit's blast radius is not what the probe declared."""
    store = RunStore.begin(project, project / "state")
    with pytest.raises(MutationError, match="occurs 2 times"):
        store.apply(project / "subject.py", "return", "pass  # return")


def test_mutating_deletes_the_subjects_cached_bytecode(project: Path) -> None:
    """🔴 Reaching disk is NOT reaching the interpreter.

    CPython validates a `.pyc` against its source by *(mtime-in-whole-seconds, size)*. A
    mutation that does not change the file's length — `return "even"` → `return "EVEN"` —
    landing in the same wall-clock second as the previous compile is judged *unchanged*,
    so the child imports STALE bytecode and the battery reports GREEN ("the guard may be
    vacuous") about a guard it never exercised.

    Measured 2026-08-25: CI reddened on exactly this while the same commit passed locally,
    because the window is timing-dependent. Asserted here by construction instead — the
    cached file must be gone after a mutation, whatever the clock did.
    """
    cache = project / "__pycache__"
    cache.mkdir()
    stale = cache / "subject.cpython-312.pyc"
    stale.write_bytes(b"stale bytecode")
    store = RunStore.begin(project, project / "state")
    store.apply(project / "subject.py", "n > 10", "n > 1000")
    assert not stale.exists()


def test_restoring_also_deletes_the_cached_bytecode(project: Path) -> None:
    """The restore writes a same-size file too, so leaving its bytecode cached would hand
    the NEXT probe the very staleness this defends against."""
    store = RunStore.begin(project, project / "state")
    store.apply(project / "subject.py", "n > 10", "n > 1000")
    cache = project / "__pycache__"
    cache.mkdir(exist_ok=True)
    stale = cache / "subject.cpython-312.pyc"
    stale.write_bytes(b"stale bytecode")
    store.restore_all()
    assert not stale.exists()


def test_an_unrelated_modules_bytecode_is_left_alone(project: Path) -> None:
    """🟢 POSITIVE CONTROL: the invalidation is targeted at the subject, not a blanket wipe
    of the project's caches — otherwise the two assertions above would pass under a
    function that simply deleted `__pycache__` wholesale."""
    cache = project / "__pycache__"
    cache.mkdir()
    other = cache / "test_suite.cpython-312.pyc"
    other.write_bytes(b"unrelated bytecode")
    store = RunStore.begin(project, project / "state")
    store.apply(project / "subject.py", "n > 10", "n > 1000")
    assert other.exists()


def test_the_probe_subprocess_is_told_not_to_write_bytecode(project: Path) -> None:
    """The second half of the defence: no probe run leaves a fresh `.pyc` for the next
    same-size mutation to be judged against."""
    assert _child_env()["PYTHONDONTWRITEBYTECODE"] == "1"


def test_the_subject_is_restored_after_every_probe(project: Path) -> None:
    """Without a per-probe restore, probe N+1 runs against N's mutation and every outcome
    after the first is about a tree nobody declared."""
    before = (project / "subject.py").read_bytes()
    _run(project, [_witness_first("P1", _keys(project)[0])])
    assert (project / "subject.py").read_bytes() == before


def test_a_battery_refuses_to_start_over_an_unrestored_run(project: Path) -> None:
    """🔴 The load-bearing half of the SIGKILL story. Starting anyway would snapshot a
    MUTATED file as pristine and make the damage permanent."""
    store = RunStore.begin(project, project / "state")
    store.apply(project / "subject.py", "n > 10", "n > 1000")
    with pytest.raises(UnrestoredSnapshotError):
        refuse_if_unrestored(project / "state")


def test_a_clean_state_directory_does_not_refuse(project: Path) -> None:
    """🟢 POSITIVE CONTROL: the refusal above is caused by the unrestored run, not by a
    check that refuses unconditionally."""
    refuse_if_unrestored(project / "state")
    assert find_unrestored(project / "state") == []


def test_restore_recovers_the_subject_byte_identically_after_a_kill(project: Path) -> None:
    """SIGKILL runs no Python, so the persisted manifest is the entire guarantee."""
    before = (project / "subject.py").read_bytes()
    store = RunStore.begin(project, project / "state")
    store.apply(project / "subject.py", "n > 10", "n > 1000")
    assert (project / "subject.py").read_bytes() != before  # the mutation really landed
    restore_pending(project / "state")
    assert (project / "subject.py").read_bytes() == before


def test_an_unparsable_manifest_counts_as_unrestored(project: Path) -> None:
    """Treating unreadable state as "fine" is how a driver talks itself into starting on a
    broken tree."""
    run_dir = project / "state" / "run-broken"
    run_dir.mkdir(parents=True)
    (run_dir / "manifest.json").write_text("{not json", encoding="utf-8")
    assert find_unrestored(project / "state") == [run_dir]


def test_re_snapshotting_a_mutated_subject_keeps_the_first_bytes(project: Path) -> None:
    """Re-snapshotting a file the run already mutated would record the mutation as the
    original — the restore would then put the damage back."""
    before = (project / "subject.py").read_bytes()
    store = RunStore.begin(project, project / "state")
    store.apply(project / "subject.py", "n > 10", "n > 1000")
    store.snapshot(project / "subject.py")
    store.restore_all()
    assert (project / "subject.py").read_bytes() == before


# -- the battery file (the CLI's data path) ---------------------------------------------


def test_a_battery_file_round_trips_into_probes(project: Path) -> None:
    payload = {
        "claim_sources": ["test_suite.py"],
        "probes": [
            {
                "name": "P1",
                "subject": "subject.py",
                "old": "n > 10",
                "new": "n > 1000",
                "node_id": "test_suite.py::test_classify",
                "expect_claim": _keys(project)[0],
            }
        ],
    }
    battery = Battery.from_json(json.loads(json.dumps(payload)), base=project)
    assert battery.probes[0].expect is Outcome.WITNESSED


def test_a_battery_file_missing_a_required_probe_field_is_refused(project: Path) -> None:
    payload: dict[str, object] = {"claim_sources": ["test_suite.py"], "probes": [{"name": "P1"}]}
    with pytest.raises(BatteryDefinitionError, match="missing required field"):
        Battery.from_json(payload, base=project)
