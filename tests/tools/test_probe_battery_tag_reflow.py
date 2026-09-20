"""AC-9R — ``tag --reflow`` (PLAN-0128 Step 3).

Step 3 measured that a third of the PLAN-0126 story battery's anchors cannot carry a tag
at any id length: their bare lines already sit within 11 columns of the limit, and the
tag marker alone costs 11. The refusal's standing advice — *explode the statement, then
re-run* — is a **dead end**, and this module pins why: exploding rewrites the source text
the battery's key is derived from, so the re-run refuses the claim as unaddressable. The
order has to be tag-first, reflow-second, which is what ``--reflow`` does.

Nothing here is mocked. Each case builds a real module and a real text-keyed battery in
``tmp_path``, drives the **real** subcommand through ``main([...])``, runs the **real**
``ruff format``, and reads the result back with the shipped enumerator.

Every refusal case asserts on **sha256 of each file the tool would have touched**. A
printed refusal and an unwritten file are two different claims, and ``--reflow`` writes
before it formats — so "it restored" is the one that matters here.

⚠️ Tag prose in this module lives in docstrings, never in a ``#`` comment: a comment that
spells the marker is read by the enumerator as a real tag and takes down the whole
module's enumeration.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools.probe_battery.__main__ import main
from tools.probe_coverage import enumerate_claims

MARKER = "# claim:"

#: 41 columns. With ``line-length = 60`` the append lands at 68 (41 + 11 for the marker
#: + 16 for the id ``tag-reflow/p-one``), so the width check really fires. Asserted in
#: every case that depends on it: a fixture that quietly stopped overrunning would make
#: these tests pass while testing nothing.
WIDE = "    assert total(1, 2, 3, 4, 5, 60) == 71"

#: Deliberately excludes the ``assert`` keyword. ``--reflow`` moves the expression onto
#: its own interior line, so an anchor containing ``assert`` would occur zero times
#: afterwards and the tool's own post-write lint would refuse the result.
ANCHOR_OLD = "total(1, 2, 3"
ANCHOR_NEW = "total(9, 9, 9"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_project(root: Path, line_length: int = 60) -> None:
    (root / "pyproject.toml").write_text(
        f"[tool.ruff]\nline-length = {line_length}\n", encoding="utf-8"
    )


def _keys(module: Path) -> dict[str, int]:
    return {c.stable_key: c.lineno for c in enumerate_claims(module)}


def _battery(root: Path, module: Path, key: str, old: str = ANCHOR_OLD) -> Path:
    path = root / "tag-reflow.json"
    path.write_text(
        json.dumps(
            {
                "name": "tag-reflow",
                "claim_sources": [str(module.relative_to(root))],
                "probes": [
                    {
                        "name": "p-one",
                        "subject": str(module.relative_to(root)),
                        "old": old,
                        "new": ANCHOR_NEW,
                        "node_id": f"{module.name}::test_one",
                        "expect_claim": key,
                    }
                ],
                "exemptions": {},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def project(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A format-clean project whose single claim cannot carry a tag without a reflow."""
    assert len(WIDE) == 41, "fixture drifted — the width arithmetic depends on it"
    _write_project(tmp_path)
    module = tmp_path / "test_subject.py"
    module.write_text(
        "def total(*values):\n    return sum(values)\n\n\ndef test_one():\n" + WIDE + "\n",
        encoding="utf-8",
    )
    battery = _battery(tmp_path, module, next(iter(_keys(module))))
    return tmp_path, module, battery


def test_reflow_tags_an_overlong_anchor_and_leaves_every_line_within_the_limit(
    project: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """(i) the tag resolves, (ii) nothing overruns, (iii) equivalence holds, (iv) it says so."""
    root, module, battery = project
    lines_before = len(module.read_text(encoding="utf-8").split("\n"))

    assert main(["--project-root", str(root), "tag", str(battery), "--reflow"]) == 0
    printed = capsys.readouterr().out

    # (i) the claim is addressable by its tag — the whole point of the migration
    assert "@tag-reflow/p-one" in _keys(module)

    # (ii) the tree the tool left behind is lintable
    widest = max(len(line) for line in module.read_text(encoding="utf-8").split("\n"))
    assert widest <= 60, f"a line still overruns at {widest}"

    # (iii) the claim behind the tag is still the claim the text key named
    assert "resolved_differ=0" in printed

    # (iv) the reflow is reported rather than silent
    assert "reflowed=1" in printed

    # Positive control for (ii): the statement really was exploded. Without this a
    # fixture that stopped overrunning would satisfy every assertion above while the
    # reflow path never ran at all.
    lines_after = len(module.read_text(encoding="utf-8").split("\n"))
    assert lines_after > lines_before, "the module was never reflowed"


def test_the_battery_key_is_rewritten_to_the_tag(
    project: tuple[Path, Path, Path],
) -> None:
    """The JSON must follow the source, or the battery addresses a key that is now gone."""
    root, _module, battery = project

    assert main(["--project-root", str(root), "tag", str(battery), "--reflow"]) == 0

    data = json.loads(battery.read_text(encoding="utf-8"))
    assert data["probes"][0]["expect_claim"] == "@tag-reflow/p-one"


def test_without_reflow_the_refusal_warns_against_exploding_by_hand(
    project: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """The dead end is named in the refusal, because following it wastes a whole pass."""
    root, module, battery = project
    before = {module: _sha(module), battery: _sha(battery)}

    assert main(["--project-root", str(root), "tag", str(battery)]) == 2
    printed = capsys.readouterr().err

    assert "--reflow" in printed
    assert "unaddressable key" in printed
    assert {p: _sha(p) for p in before} == before


def test_reflow_refuses_a_module_that_is_not_already_formatted_and_writes_nothing(
    project: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """An unformatted module makes the post-write diff unattributable, so it is refused."""
    root, module, battery = project
    module.write_text(
        module.read_text(encoding="utf-8").replace("def test_one():", "def test_one() :"),
        encoding="utf-8",
    )
    before = {module: _sha(module), battery: _sha(battery)}

    assert main(["--project-root", str(root), "tag", str(battery), "--reflow"]) == 2
    printed = capsys.readouterr().err

    assert "format` clean already" in printed
    assert {p: _sha(p) for p in before} == before


def test_reflow_restores_everything_when_it_strands_a_probe_anchor(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A reflow can move an anchor out of existence; the post-write lint catches it.

    The anchor here deliberately contains ``assert``, which the reflow pushes onto a
    line of its own — so afterwards it occurs zero times and the battery no longer
    lints. The tool must restore rather than commit a battery whose probe is a no-op.
    """
    _write_project(tmp_path)
    module = tmp_path / "test_subject.py"
    module.write_text(
        "def total(*values):\n    return sum(values)\n\n\ndef test_one():\n" + WIDE + "\n",
        encoding="utf-8",
    )
    battery = _battery(tmp_path, module, next(iter(_keys(module))), old="assert total(1, 2, 3")
    before = {module: _sha(module), battery: _sha(battery)}

    assert main(["--project-root", str(tmp_path), "tag", str(battery), "--reflow"]) == 2
    assert {p: _sha(p) for p in before} == before

    # Positive control: the SAME run with an anchor the reflow preserves succeeds, so
    # the refusal above is about the stranded anchor and not about --reflow at large.
    battery = _battery(tmp_path, module, next(iter(_keys(module))))
    capsys.readouterr()
    assert main(["--project-root", str(tmp_path), "tag", str(battery), "--reflow"]) == 0
    assert "@tag-reflow/p-one" in _keys(module)
