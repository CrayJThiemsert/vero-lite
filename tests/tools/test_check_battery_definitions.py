"""The battery-definition lint must FAIL on each rot class — and only on those.

Its sibling ``test_guards_hold_on_the_real_tree`` proves this guard accepts a healthy
tree, which ``return 0`` also does. This module is the other half: one case per finding
class, each built as a real battery over a real subject in ``tmp_path``, plus the
over-refusal controls that stop the guard from being "strict" by being wrong.

🔴 **The regression pin is ``test_a_new_text_already_present_elsewhere_is_not_a_finding``.**
The first draft of this lint treated a mutation's ``new`` text appearing anywhere in the
subject as proof the mutation was a no-op. That is false — replacing ``return "plain"``
with ``return "reasoning"`` in a file that already has a legitimate ``return "reasoning"``
branch changes the file exactly as intended — and the wrong version reported **8 of 21**
batteries dead when the true number was **2**. Six healthy batteries were accused. That
case is pinned here so the mistake cannot come back as a "stricter" check.
"""

from __future__ import annotations

import json
from pathlib import Path

from tools.probe_battery._lint import lint_battery_file

#: Both returns sit at the SAME indent on purpose: the regression pin needs the probe's
#: `new` text to appear elsewhere in the subject BYTE-FOR-BYTE, and an indent mismatch
#: would make that case silently untested. (It did, on the first run — the premise
#: assertion in that test is what caught it.)
SUBJECT = '''"""A subject with three distinguishable branches."""


def shape(value: int) -> str:
    if value > 0:
        return "plain"
    if value < 0:
        return "reasoning"
    return "zero"
'''

TEST_MODULE = """from pathlib import Path


def test_shape_is_plain_for_positive() -> None:
    assert shape(1) == "plain"
"""

#: `stable_key` is owner|source|#occurrence — line-independent by construction.
CLAIM = 'test_shape_is_plain_for_positive|shape(1) == "plain"|#0'


def _tree(tmp_path: Path) -> tuple[Path, Path]:
    """A minimal but REAL project root: a subject, a test module, a batteries dir."""
    (tmp_path / "svc").mkdir()
    subject = tmp_path / "svc" / "shape.py"
    subject.write_text(SUBJECT, encoding="utf-8")
    (tmp_path / "t").mkdir()
    module = tmp_path / "t" / "test_shape.py"
    module.write_text(TEST_MODULE, encoding="utf-8")
    return subject, module


def _battery(tmp_path: Path, **overrides: object) -> Path:
    """A HEALTHY battery by default; each test perturbs exactly one field."""
    probe: dict[str, object] = {
        "name": "P1",
        "subject": "svc/shape.py",
        "old": '        return "plain"',
        "new": '        return "reasoning"',
        "node_id": "t/test_shape.py::test_shape_is_plain_for_positive",
        "expect_claim": CLAIM,
    }
    probe.update(overrides.pop("probe", {}))  # type: ignore[arg-type]
    data: dict[str, object] = {
        "claim_sources": ["t/test_shape.py"],
        "probes": [probe],
    }
    data.update(overrides)
    path = tmp_path / "battery.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _details(tmp_path: Path, **overrides: object) -> str:
    report = lint_battery_file(_battery(tmp_path, **overrides), tmp_path)
    return " ".join(f.detail for f in report.findings)


# --- over-refusal controls: these must produce NO findings --------------------


def test_a_healthy_battery_produces_no_findings(tmp_path: Path) -> None:
    """Non-vacuity for every case below: a guard that flags everything passes them all."""
    _tree(tmp_path)
    report = lint_battery_file(_battery(tmp_path), tmp_path)
    assert report.findings == (), f"a healthy battery was accused: {report.findings}"
    assert report.probes == 1
    assert report.claim_sources == 1


def test_a_new_text_already_present_elsewhere_is_not_a_finding(tmp_path: Path) -> None:
    """🔴 The regression pin. `new` on disk elsewhere does not make a mutation a no-op.

    The default probe rewrites ``return "plain"`` to ``return "reasoning"`` in a subject
    that ALREADY contains ``return "reasoning"`` — the exact shape the first draft called
    dead. The substitution still changes the file, so there is nothing to report.
    """
    subject, _ = _tree(tmp_path)
    text = subject.read_text(encoding="utf-8")
    # The premise this test rests on, asserted rather than assumed.
    assert text.count('        return "reasoning"') == 1
    assert text.count('        return "plain"') == 1

    report = lint_battery_file(_battery(tmp_path), tmp_path)
    assert report.findings == (), (
        "a mutation whose `new` text also appears elsewhere is a normal mutation, not a "
        f"no-op — this is the s288 over-refusal, back: {report.findings}"
    )


# --- one case per rot class: each must produce a finding ----------------------


def test_an_anchor_that_no_longer_resolves_is_found(tmp_path: Path) -> None:
    """The s287 R17 death: the code moved, the battery did not."""
    _tree(tmp_path)
    details = _details(tmp_path, probe={"old": '        return "renamed_away"'})
    assert "occurs 0 times" in details


def test_an_anchor_matching_twice_is_found(tmp_path: Path) -> None:
    """The other half of 'exactly once': a mutation whose blast radius is undeclared."""
    subject, _ = _tree(tmp_path)
    subject.write_text(SUBJECT + '\n\ndef other() -> str:\n    return "plain"\n', encoding="utf-8")
    details = _details(tmp_path, probe={"old": 'return "plain"'})
    assert "occurs 2 times" in details


def test_a_byte_identical_mutation_is_found(tmp_path: Path) -> None:
    """The only offline-decidable no-op: substituting a string by itself."""
    _tree(tmp_path)
    details = _details(tmp_path, probe={"new": '        return "plain"'})
    assert "byte-identical" in details


def test_a_claim_key_that_addresses_nothing_is_found(tmp_path: Path) -> None:
    """The s287 AC-1 / AC-2 death: a reflowed or renamed assertion."""
    _tree(tmp_path)
    details = _details(tmp_path, probe={"expect_claim": "test_gone|no such assertion|#0"})
    assert "does not exist in the claim sources" in details


def test_an_exemption_naming_a_vanished_claim_is_found(tmp_path: Path) -> None:
    """The third address that rots — and the one the driver only reports mid-run."""
    _tree(tmp_path)
    details = _details(tmp_path, exemptions={"test_gone|no such assertion|#0": "why"})
    assert "no longer exists" in details


def test_a_node_id_naming_a_missing_module_is_found(tmp_path: Path) -> None:
    """A probe pointing at a test module that was moved or deleted."""
    _tree(tmp_path)
    details = _details(tmp_path, probe={"node_id": "t/gone.py::test_x"})
    assert "node_id names a module that does not exist" in details


def test_a_missing_claim_source_is_found(tmp_path: Path) -> None:
    """Reported alone: every later check derives from an index that cannot be built."""
    _tree(tmp_path)
    report = lint_battery_file(_battery(tmp_path, claim_sources=["t/gone.py"]), tmp_path)
    assert len(report.findings) == 1
    assert "claim_sources missing from disk" in report.findings[0].detail


def test_unparseable_json_is_found_and_does_not_raise(tmp_path: Path) -> None:
    """A broken battery must be a FINDING, not a crash that takes the whole run down."""
    _tree(tmp_path)
    path = tmp_path / "battery.json"
    path.write_text("{not json", encoding="utf-8")
    report = lint_battery_file(path, tmp_path)
    assert len(report.findings) == 1
    assert "unreadable" in report.findings[0].detail
