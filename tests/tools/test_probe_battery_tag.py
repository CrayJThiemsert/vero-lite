"""AC-9 — the ``tag`` subcommand (PLAN-0128 Step 2).

Nothing here is mocked. Each case builds a real module and a real text-keyed battery in
``tmp_path``, drives the **real** subcommand through ``main([...])``, and reads the
result back off disk with the shipped enumerator. A test that stubbed either side of
this seam would prove the contract its author imagined rather than the one the tool
produces (CLAUDE.md §8) — and the seam under test here *is* the write/read boundary
between the tool and the enumerator.

Every refusal case asserts on **sha256 of each file the tool would have touched**, not
on the absence of an error message: "it printed a refusal" and "it wrote nothing" are
two different claims, and only the second is what "refuse before writing" means.

⚠️ Tag prose in this module lives in docstrings, never in a ``#`` comment. A comment
that spells the marker is read by the enumerator as a real tag and takes down the whole
module's enumeration — measured three times in s313, including on the first draft of a
test module, which refused itself.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools.probe_battery.__main__ import main
from tools.probe_coverage import enumerate_claims

MARKER = "# claim:"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_project(root: Path, line_length: int = 100) -> None:
    (root / "pyproject.toml").write_text(
        f"[tool.ruff]\nline-length = {line_length}\n", encoding="utf-8"
    )


def _module_source() -> str:
    """A module with four claims, one of them multi-line.

    ``test_multi``'s assert spans four physical lines, so its anchor is the ``) == 3``
    line — the case that separates a correct writer from one appending to a statement's
    first line.
    """
    return (
        "def total(*values):\n"
        "    return sum(values)\n"
        "\n"
        "\n"
        "def test_one():\n"
        "    assert total(1, 2) == 3\n"
        "\n"
        "\n"
        "def test_two():\n"
        "    assert total(2, 2) == 4\n"
        "\n"
        "\n"
        "def test_multi():\n"
        "    assert total(\n"
        "        1,\n"
        "        2,\n"
        "    ) == 3\n"
        "\n"
        "\n"
        "def test_untouched():\n"
        "    assert total(5) == 5\n"
    )


def _keys(module: Path) -> dict[str, int]:
    return {c.stable_key: c.lineno for c in enumerate_claims(module)}


def _battery(
    root: Path, module: Path, probes: list[dict[str, str]], exemptions: dict[str, str]
) -> Path:
    path = root / "pr2-tag-tool.json"
    path.write_text(
        json.dumps(
            {
                "name": "pr2-tag-tool",
                "claim_sources": [str(module.relative_to(root))],
                "probes": probes,
                "exemptions": exemptions,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def _probe(
    name: str,
    module: Path,
    root: Path,
    key: str,
    old: str,
    new: str,
    owner: str = "test_one",
) -> dict[str, str]:
    """A probe whose ``old`` anchor really occurs once in ``module``.

    The anchor must be real: ``lint_battery_file`` refuses an anchor occurring zero
    times (*"a no-op whose GREEN proves nothing"*), and the ``tag`` tool runs that lint
    over its own result — so a placeholder anchor makes every case fail for a reason
    that has nothing to do with tagging. It did, on the first run of this module.
    """
    return {
        "name": name,
        "subject": str(module.relative_to(root)),
        "old": old,
        "new": new,
        "node_id": f"{module.name}::{owner}",
        "expect_claim": key,
    }


#: The two anchors the fixture module offers, each occurring exactly once.
#: ``ONE_OLD`` survives tagging because a tag is APPENDED — the anchor stays a prefix
#: of the tagged line — which is itself part of what makes append-not-insert safe.
ONE_OLD = "assert total(1, 2) == 3"
ONE_NEW = "assert total(1, 2) == 4"
#: Leading spaces matter: bare ``) == 3`` also occurs inside ``total(1, 2) == 3``.
MULTI_OLD = "    ) == 3"
MULTI_NEW = "    ) == 4"


@pytest.fixture
def project(tmp_path: Path) -> tuple[Path, Path]:
    _write_project(tmp_path)
    module = tmp_path / "test_subject.py"
    module.write_text(_module_source(), encoding="utf-8")
    return tmp_path, module


def test_tag_appends_to_anchor_lines_rewrites_the_battery_and_prints_its_equivalence(
    project: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """(i)…(v): anchors tagged, untouched claims left alone, battery rewritten, proof printed."""
    root, module = project
    keys = _keys(module)
    one = next(k for k in keys if "total(1, 2) == 3" in k)
    two = next(k for k in keys if "total(2, 2) == 4" in k)
    multi = next(k for k in keys if "total( 1, 2, ) == 3" in k)

    original_lines = module.read_text(encoding="utf-8").split("\n")
    battery = _battery(
        root,
        module,
        [
            _probe("p-one", module, root, one, ONE_OLD, ONE_NEW),
            _probe("p-one-again", module, root, one, ONE_OLD, ONE_NEW),
            _probe("p-multi", module, root, multi, MULTI_OLD, MULTI_NEW, owner="test_multi"),
        ],
        {two: "no probe can reach this one"},
    )

    assert main(["--project-root", str(root), "tag", str(battery)]) == 0
    printed = capsys.readouterr().out

    tagged_lines = module.read_text(encoding="utf-8").split("\n")

    # (i) every addressed claim's ANCHOR line now carries a tag — for the multi-line
    # claim that is its closing line, not its first.
    anchor_rows = sorted(i for i, line in enumerate(tagged_lines) if MARKER in line)
    assert len(anchor_rows) == 3
    assert tagged_lines[anchor_rows[2]].strip().startswith(") == 3")

    # ... and every other line is byte-identical, with the line count unchanged.
    assert len(tagged_lines) == len(original_lines)
    for i, (before, after) in enumerate(zip(original_lines, tagged_lines, strict=True)):
        if i not in anchor_rows:
            assert before == after, f"line {i + 1} changed and should not have"
    # positive control for that absence: the anchor lines DID change.
    for i in anchor_rows:
        assert original_lines[i] != tagged_lines[i]

    # (ii) the unaddressed claim is untagged.
    live = {c.stable_key: c for c in enumerate_claims(module)}
    untouched = [c for c in live.values() if c.owner == "test_untouched"]
    assert [c.tag for c in untouched] == [None]

    # (iii) every addressed key in the JSON is now a tag key.
    data = json.loads(battery.read_text(encoding="utf-8"))
    assert [p["expect_claim"] for p in data["probes"]] == [
        "@pr2-tag-tool/p-one",
        "@pr2-tag-tool/p-one",
        "@pr2-tag-tool/p-multi",
    ]
    assert list(data["exemptions"]) == ["@pr2-tag-tool/exempt-1"]

    # (iv) the proof line, exact.
    assert (
        "battery=pr2-tag-tool.json addressed=3 tagged=3 adopted=0 "
        "resolved_same=3 resolved_differ=0" in printed
    )


def test_tag_refuses_when_a_key_is_unaddressable_and_writes_nothing(
    project: tuple[Path, Path],
) -> None:
    root, module = project
    battery = _battery(
        root,
        module,
        [_probe("p-ghost", module, root, "test_one|nothing like this|#0", ONE_OLD, ONE_NEW)],
        {},
    )
    before = {module: _sha(module), battery: _sha(battery)}

    assert main(["--project-root", str(root), "tag", str(battery)]) == 2

    assert {p: _sha(p) for p in before} == before


def test_tag_adopts_an_existing_tag_instead_of_appending_a_second(
    project: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    root, module = project
    source = module.read_text(encoding="utf-8").replace(
        "    assert total(1, 2) == 3\n",
        f"    assert total(1, 2) == 3  {MARKER} already-mine\n",
    )
    module.write_text(source, encoding="utf-8")
    anchor_before = next(line for line in source.split("\n") if MARKER in line)

    battery = _battery(
        root,
        module,
        [_probe("p-one", module, root, "@already-mine", ONE_OLD, ONE_NEW)],
        {},
    )
    assert main(["--project-root", str(root), "tag", str(battery)]) == 0
    printed = capsys.readouterr().out

    assert "adopted=1" in printed
    anchor_after = [
        line for line in module.read_text(encoding="utf-8").split("\n") if MARKER in line
    ]
    assert anchor_after == [anchor_before]
    assert anchor_after[0].count(MARKER) == 1


def test_tag_appends_after_an_existing_trailing_comment(project: tuple[Path, Path]) -> None:
    """The existing comment keeps its bytes and its position; the tag goes last.

    Each pragma parser reads rightwards from its own marker, so appending after
    ``# noqa: E501`` leaves every such reader seeing exactly what it saw before.
    """
    root, module = project
    source = module.read_text(encoding="utf-8").replace(
        "    assert total(1, 2) == 3\n",
        "    assert total(1, 2) == 3  # noqa: E501\n",
    )
    module.write_text(source, encoding="utf-8")

    key = next(k for k in _keys(module) if "total(1, 2) == 3" in k)
    battery = _battery(root, module, [_probe("p-one", module, root, key, ONE_OLD, ONE_NEW)], {})
    assert main(["--project-root", str(root), "tag", str(battery)]) == 0

    line = next(line for line in module.read_text(encoding="utf-8").split("\n") if MARKER in line)
    assert line.endswith("# noqa: E501  " + MARKER + " pr2-tag-tool/p-one")
    # ...and the claim still resolves to the tag, which is the separate claim.
    assert "@pr2-tag-tool/p-one" in _keys(module)


def test_tag_refuses_an_append_that_would_exceed_line_length_and_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path
    _write_project(root, line_length=60)
    module = root / "test_wide.py"
    # 41 columns, chosen so the append lands at exactly 70: 41 + 11 for the tag prefix
    # + 18 for the id `pr2-tag-tool/p-one`. The first draft of this fixture used a
    # 27-column assert, which reached only 56 and so never overran at all — the test
    # then failed for an unrelated reason and said nothing about the width check.
    # (This comment once spelled the tag prefix literally, which made the enumerator
    # read it as a real tag and refuse the whole module. Prose about the marker goes
    # in a docstring; see this module's own.)
    wide = "    assert total(1, 2, 3, 4, 5, 60) == 71"
    assert len(wide) == 41, "fixture drifted — the width arithmetic below depends on it"
    module.write_text(
        "def total(*values):\n    return sum(values)\n\n\ndef test_one():\n" + wide + "\n",
        encoding="utf-8",
    )
    key = next(iter(_keys(module)))
    battery = _battery(
        root,
        module,
        [_probe("p-one", module, root, key, "assert total(1, 2, 3", "assert total(9, 9, 9")],
        {},
    )
    before = {module: _sha(module), battery: _sha(battery)}

    assert main(["--project-root", str(root), "tag", str(battery)]) == 2
    printed = capsys.readouterr().err

    assert "overlong:" in printed
    assert "width=70 limit=60" in printed
    assert {p: _sha(p) for p in before} == before

    # Positive control: the SAME project at line-length 100 succeeds, so the refusal
    # above is about the width and nothing else in the fixture.
    _write_project(root, line_length=100)
    assert main(["--project-root", str(root), "tag", str(battery)]) == 0
    assert "@pr2-tag-tool/p-one" in _keys(module)


def test_dry_run_prints_the_sd_e_measurement_and_writes_nothing(
    project: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """SD-e's binding measurement is a printed value, and it prints even at zero.

    A missing line and a ``overlong=0`` line read the same to anyone grepping for the
    figure, and only one of them is true.
    """
    root, module = project
    key = next(k for k in _keys(module) if "total(1, 2) == 3" in k)
    battery = _battery(root, module, [_probe("p-one", module, root, key, ONE_OLD, ONE_NEW)], {})
    before = {module: _sha(module), battery: _sha(battery)}

    assert main(["--project-root", str(root), "tag", str(battery), "--dry-run"]) == 0
    printed = capsys.readouterr().out

    assert "overlong=0 of addressed=1" in printed
    assert {p: _sha(p) for p in before} == before
