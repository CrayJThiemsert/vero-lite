"""PLAN-0128 — claim tags reaching the DRIVER and the LINT, through the existing refusals.

The whole H2 argument is that a tag key and a text key are two derivations of one key, not
two lookup paths. So everything here exercises the tag form through `_index_claims`,
`_validate`, `_overlaps`, `render_report` and `lint_battery_file` **unchanged** — if any of
them needed a tag-shaped branch, that argument would be false.

🔴 **Its own module, for the denominator.** See `test_probe_coverage_claim_tags.py`; the
same reasoning applies twice as hard here, because `test_check_battery_definitions.py` is
scoped EXACTLY by `s288-battery-definition-lint.json` (19 claims, 19 addressed) and adding
claims to it would have opened six gaps in a battery this PR has nothing to do with.

NOTE — no comment here spells the tag marker out; see the sibling module's note.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.probe_battery import Battery, BatteryDefinitionError, Probe
from tools.probe_battery._battery import _index_claims, _overlaps, _validate
from tools.probe_battery._lint import lint_battery_file
from tools.probe_coverage import enumerate_claims, render_report

#: A minimal but REAL project: a subject with distinguishable branches, a test module, a
#: battery. Copied rather than imported so this module's fixtures cannot drift with the
#: lint suite's.
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

CLAIM = 'test_shape_is_plain_for_positive|shape(1) == "plain"|#0'


def _tree(tmp_path: Path) -> tuple[Path, Path]:
    (tmp_path / "svc").mkdir()
    subject = tmp_path / "svc" / "shape.py"
    subject.write_text(SUBJECT, encoding="utf-8")
    (tmp_path / "t").mkdir()
    module = tmp_path / "t" / "test_shape.py"
    module.write_text(TEST_MODULE, encoding="utf-8")
    return subject, module


def _battery(tmp_path: Path, **overrides: object) -> Path:
    probe: dict[str, object] = {
        "name": "P1",
        "subject": "svc/shape.py",
        "old": '        return "plain"',
        "new": '        return "reasoning"',
        "node_id": "t/test_shape.py::test_shape_is_plain_for_positive",
        "expect_claim": CLAIM,
    }
    probe.update(overrides.pop("probe", {}))  # type: ignore[arg-type]
    data: dict[str, object] = {"claim_sources": ["t/test_shape.py"], "probes": [probe]}
    data.update(overrides)
    path = tmp_path / "battery.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _details(tmp_path: Path, **overrides: object) -> str:
    report = lint_battery_file(_battery(tmp_path, **overrides), tmp_path)
    return " ".join(f.detail for f in report.findings)


_TAG_PROBE: dict[str, object] = {
    "name": "P1",
    "subject": "subject.py",
    "old": "a",
    "new": "b",
    "node_id": "test_suite.py::test_x",
    "expect_claim": "@E1",
}


@pytest.mark.parametrize("field", ["prefix", "ref", "claim_ref", "owner", "source"])
def test_a_probe_carrying_a_reference_field_is_refused(field: str) -> None:
    """🔴 The one way a second address form could get back in.

    `expect_claim` is the only address field and the claim index the only lookup, so the
    refusals cover tags and text keys alike. A probe carrying `{owner, prefix}` — or any
    pointer beside the key — would be a resolver, and a resolver is what has no
    structural answer to a deleted claim. Until now an unknown field was silently
    IGNORED, so such a battery read as if it worked.
    """
    with pytest.raises(BatteryDefinitionError, match=r"# claim:"):  # claim: pr1/ref-field-refused
        Probe.from_json(_TAG_PROBE | {field: "whatever"})

    # Positive control: the same dict without the field loads, and the address is read
    # verbatim — so the refusal is about the extra field, not about the tag form.
    assert Probe.from_json(_TAG_PROBE).expect_claim == "@E1"  # claim: pr1/ref-field-control


def test_a_deleted_tagged_assert_is_refused_even_when_a_same_prefix_sibling_remains(
    tmp_path: Path,
) -> None:
    """🔴 H1, witnessed — and the retired rule replayed on the same fixture as the oracle.

    The module has two asserts in one owner sharing a prefix; the first is tagged. Delete
    the tagged assert **and its tag line** and `@E1` resolves to nothing, so `_validate`
    refuses before the first mutation. The four-line reconstruction below is the
    closed-incident oracle (the PLAN-0115 AC-6 pattern): applied to the SAME post-deletion
    tree, the retired `(owner, prefix)` rule resolves to exactly one claim — the survivor
    — which is what it would have credited.
    """
    module = tmp_path / "test_suite.py"
    module.write_text(
        "def test_x():\n"
        '    assert result.error == "missing"  # claim: E1\n'
        '    assert result.error == "missing" or retry\n',
        encoding="utf-8",
    )
    battery = Battery(claim_sources=(module,), probes=(Probe.from_json(_TAG_PROBE),))

    # (i) fixture premise: before the deletion the address resolves and validation passes.
    _validate(battery, _index_claims(battery))

    module.write_text('def test_x():\n    assert result.error == "missing" or retry\n', "utf-8")
    with pytest.raises(
        BatteryDefinitionError, match=r"@E1"
    ):  # claim: pr1/dead-tag-refused-before-mutation
        _validate(battery, _index_claims(battery))

    # (iii) the closed-incident oracle, on the post-deletion tree.
    survivors = enumerate_claims(module)
    prefix = 'result.error == "missing"'
    would_have_matched = [c for c in survivors if c.source.startswith(prefix)]
    assert len(would_have_matched) == 1  # claim: pr1/h1-oracle


def test_an_exemption_keyed_by_tag_is_honoured_and_reported(tmp_path: Path) -> None:
    """H3: exemption keys are `stable_key`s, so the tag form needed no new code.

    The reason must reach the reader, not a count — an exemption nobody reads is how a
    coverage check rots into agreement with itself (#0047 §3).
    """
    module = tmp_path / "test_suite.py"
    module.write_text(
        "def test_x():\n    assert a == 1  # claim: E1\n    assert b == 2\n", encoding="utf-8"
    )
    claims = enumerate_claims(module)
    reason = "no mutation can reach it without rewriting the fixture"
    report, _ = render_report(claims, {}, {"@E1": reason}, key_of=lambda c: c.stable_key)

    assert "exempted: 1" in report  # claim: pr1/tag-exemption-counted
    assert reason in report  # claim: pr1/tag-exemption-reason-printed


def test_a_battery_that_both_probes_and_exempts_one_tag_is_an_overlap(tmp_path: Path) -> None:
    """`_overlaps` is the driver's own self-check, computed from PRE-filter inputs. A tag
    key flows through it with no new code, which is the H2 claim at a fourth surface."""
    module = tmp_path / "test_suite.py"
    module.write_text("def test_x():\n    assert a == 1  # claim: E1\n", encoding="utf-8")
    battery = Battery(
        claim_sources=(module,),
        probes=(Probe.from_json(_TAG_PROBE),),
        exemptions={"@E1": "also exempted, which is a contradiction"},
    )
    assert _overlaps(battery) == ("@E1",)  # claim: pr1/tag-overlap-reported


#: The H1 shape. Two asserts in one owner whose texts share the prefix the retired
#: `(owner, prefix)` rule resolved on; the first is tagged. Deleting the tagged assert
#: leaves a sibling that the prefix rule WOULD have accepted.
TAGGED_MODULE = """from pathlib import Path


def test_shape_is_plain_for_positive() -> None:
    assert shape(1) == "plain"  # claim: E1
    assert shape(1) == "plain" or retry()
"""

#: The same module after the one edit that rebuilt H1 under the rejected line-above
#: form: the tagged assert AND its tag are gone, the sibling remains.
TAGGED_MODULE_AFTER_DELETION = """from pathlib import Path


def test_shape_is_plain_for_positive() -> None:
    assert shape(1) == "plain" or retry()
"""

#: The survivor's text key, so a probe can address it without a tag.
SIBLING_CLAIM = 'test_shape_is_plain_for_positive|shape(1) == "plain" or retry()|#0'


def _tagged_tree(tmp_path: Path, *, deleted: bool = False) -> Path:
    """`_tree`, with the test module replaced by the tag fixture."""
    _tree(tmp_path)
    module = tmp_path / "t" / "test_shape.py"
    body = TAGGED_MODULE_AFTER_DELETION if deleted else TAGGED_MODULE
    module.write_text(body, encoding="utf-8")
    return module


def test_the_lint_refuses_a_deleted_tagged_claim_with_a_same_prefix_sibling(
    tmp_path: Path,
) -> None:
    """🔴 The centre of PLAN-0128, at the surface that actually runs every commit.

    Under the retired `(owner, prefix)` rule this exact edit was silent: the prefix
    `shape(1) == "plain"` still resolved — to the SURVIVOR — and the battery went on
    crediting a claim nobody declared. A tag cannot do that, because `@E1` is not derived
    from any text still in the file. It resolves to nothing, and nothing is loud.
    """
    module = _tagged_tree(tmp_path, deleted=True)
    detail = _details(tmp_path, probe={"expect_claim": "@E1"})
    assert "@E1" in detail  # claim: pr1/lint-names-the-dead-tag

    # Positive control: the SAME battery over the pre-deletion module is clean. Only the
    # module's bytes change between the two reads, so the finding above is about the
    # deletion and not about tags being unsupported here.
    module.write_text(TAGGED_MODULE, encoding="utf-8")
    assert _details(tmp_path, probe={"expect_claim": "@E1"}) == ""  # claim: pr1/lint-live-tag


def test_the_lint_reports_a_tag_error_as_a_finding(tmp_path: Path) -> None:
    """A refused tag must arrive as a Finding, never as a traceback.

    Same shape as the `expect: "witnessed"` dogfooding failure above, one exception class
    later: this hook is `always_run`, so a raise here would take the lint down for every
    OTHER battery in the same commit, and the commit that stranded the tag would learn
    nothing while 50-odd healthy batteries were reported as a tool crash.
    """
    _tree(tmp_path)
    module = tmp_path / "t" / "test_shape.py"
    module.write_text(TEST_MODULE + "    # claim: stranded\n", encoding="utf-8")

    report = lint_battery_file(_battery(tmp_path), tmp_path)
    details = " ".join(f.detail for f in report.findings)
    assert "claim tag:" in details  # claim: pr1/tag-error-is-a-finding
    assert "unattached" in details  # claim: pr1/tag-finding-says-which-refusal


def test_an_orphaned_tag_exemption_is_a_finding(tmp_path: Path) -> None:
    """Exemption keys are `stable_key`s, so a tag exemption rots exactly as a text one
    does — and the orphan check needed no new code to see it, which is the H2 argument
    holding at a third surface.

    An exemption is a written promise that a specific claim cannot be reached. When the
    claim is gone the promise still READS as deliberate coverage while covering nothing.
    """
    _tagged_tree(tmp_path, deleted=True)
    detail = _details(
        tmp_path,
        probe={"expect_claim": SIBLING_CLAIM},
        exemptions={"@E1": "unreachable from any mutation"},
    )
    assert "@E1" in detail  # claim: pr1/orphan-tag-exemption-found
    assert "exemption(s) name a claim that no longer exists" in detail  # claim: pr1/orphan-wording
