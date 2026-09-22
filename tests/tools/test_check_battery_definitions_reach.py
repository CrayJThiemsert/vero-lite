"""The definition lint must REACH every committed battery, not only the ones in its home.

🔴 **The defect this exists for (measured s317).** ``check_battery_definitions`` globbed
``tests/batteries/*.json`` and nothing else. Two tracked batteries sat beside their subject
in ``benchmarks/intake_extraction/``, the lint never opened them, and one was DEAD: probe
S3 named a one-line ``self.attempts.append(AttemptRecord(...))`` that 2a112187 had turned
into a multi-line constructor. Its anchor occurred 0 times, so its green proved nothing,
and the guard printed ``BATTERY-DEFINITIONS: OK`` the whole time.

The guard now selects batteries by CONTENT over ``git ls-files``. Each case below pins one
half of that selection rule. Each negative case carries its own positive control, because
"absent from the list" is also satisfied by an empty list.

This is its own module, not a section of ``test_check_battery_definitions.py``. That module
is the whole ``claim_sources`` of ``s288-battery-definition-lint.json``, and claims added
there would open gaps in a battery this change has no reason to edit
(``tools/probe_battery/README.md``, "Give a tagged module its own test file").
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tools.check_battery_definitions import find_batteries, main

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tools" / "check_battery_definitions.py"

#: The smallest file the selection rule recognises. The lint would refuse it (no probes, no
#: sources), but these cases test SELECTION, which never parses what it selects.
MINIMAL = '{"claim_sources": [], "probes": []}'


def _write(root: Path, rel: str, text: str) -> Path:
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def _healthy_home_battery(root: Path) -> Path:
    """A home battery that lints clean: a real subject and a real claim source."""
    _write(
        root,
        "svc/shape.py",
        'def shape(value: int) -> str:\n    if value > 0:\n        return "plain"\n'
        '    return "zero"\n',
    )
    _write(
        root,
        "t/test_shape.py",
        'def test_shape_is_plain_for_positive() -> None:\n    assert shape(1) == "plain"\n',
    )
    battery = {
        "claim_sources": ["t/test_shape.py"],
        "probes": [
            {
                "name": "P1",
                "subject": "svc/shape.py",
                "old": '        return "plain"',
                "new": '        return "zero"',
                "node_id": "t/test_shape.py::test_shape_is_plain_for_positive",
                "expect_claim": 'test_shape_is_plain_for_positive|shape(1) == "plain"|#0',
            }
        ],
    }
    return _write(root, "tests/batteries/healthy.json", json.dumps(battery, indent=2))


# --- selection: which files the guard reaches ----------------------------------------


def test_a_tracked_battery_outside_the_home_is_found(tmp_path: Path) -> None:
    """The s317 shape: a battery beside its subject, tracked, and never read before now."""
    rel = "benchmarks/intake_extraction/probe_battery.json"
    stray = _write(tmp_path, rel, MINIMAL)
    found = find_batteries(tmp_path, [Path(rel)])
    assert stray in found  # claim: battery-reach/U1


def test_a_home_battery_named_by_both_sources_is_listed_once(tmp_path: Path) -> None:
    """A tracked home battery is named by the home glob AND by the tracked scan.

    Counted twice, it would be linted twice and would inflate every printed count. A reach
    that covers the home and the rest of the tree must still count each file once.
    """
    home = _write(tmp_path, "tests/batteries/a.json", MINIMAL)
    found = find_batteries(tmp_path, [Path("tests/batteries/a.json")])
    assert found.count(home) == 1  # claim: battery-reach/U2


def test_an_untracked_copy_is_not_found(tmp_path: Path) -> None:
    """Only COMMITTED batteries are in scope.

    ``.claude/worktrees/`` holds full copies of this repo, batteries included, and this repo
    tracks none of them. A filesystem walk would lint every copy; ``git ls-files`` never
    lists them. The first assertion is the positive control: the same file, tracked, IS
    found, so the second cannot pass by finding nothing.
    """
    tracked = _write(tmp_path, "benchmarks/x/battery.json", MINIMAL)
    copy = _write(tmp_path, ".claude/worktrees/wt/benchmarks/x/battery.json", MINIMAL)
    found = find_batteries(tmp_path, [Path("benchmarks/x/battery.json")])
    assert tracked in found  # claim: battery-reach/U3-control
    assert copy not in found  # claim: battery-reach/U3


def test_a_tracked_json_without_the_marker_is_not_found(tmp_path: Path) -> None:
    """The over-refusal control: most tracked JSON is not a battery and must not be linted.

    The first assertion is the positive control, for the same reason as above.
    """
    battery = _write(tmp_path, "benchmarks/x/battery.json", MINIMAL)
    other = _write(tmp_path, "ui/package.json", '{"name": "oct-ui", "private": true}')
    found = find_batteries(tmp_path, [Path("benchmarks/x/battery.json"), Path("ui/package.json")])
    assert battery in found  # claim: battery-reach/U4-control
    assert other not in found  # claim: battery-reach/U4


def test_a_battery_whose_json_is_broken_is_still_found(tmp_path: Path) -> None:
    """Why the marker is matched on TEXT: a parsed check would silently drop this file.

    Once found, it reaches the lint, which reports it unreadable. Dropped, nothing reports it.
    """
    broken = _write(tmp_path, "benchmarks/x/battery.json", '{"claim_sources": [')
    found = find_batteries(tmp_path, [Path("benchmarks/x/battery.json")])
    assert broken in found  # claim: battery-reach/U5


def test_a_tree_git_cannot_enumerate_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``tmp_path`` is not a repository, so ``git ls-files`` fails there.

    The ceiling stops git from discovering a repository above ``tmp_path``. The home holds a
    battery that lints clean, so a guard that swallowed the failure into an empty list would
    exit 0 here. Only exit 2 says "did not look".
    """
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    _healthy_home_battery(tmp_path)
    assert main([str(tmp_path)]) == 2  # claim: battery-reach/U6


# --- scenario: the real CLI over a real git index, with the s317 rot reproduced ------

#: The recorder's success path in its CURRENT shape (run_benchmark.py): the multi-line
#: constructor 2a112187 introduced. The transport-failure append kept its one-line form.
RUN_BENCHMARK = """class RecordingChatClient:
    def __init__(self, inner: ChatClient) -> None:
        self._inner = inner
        self.attempts: list[AttemptRecord] = []

    async def chat(self, messages: list[dict[str, str]]) -> ChatResult:
        index = len(self.attempts) + 1
        try:
            result = await self._inner.chat(messages)
        except Exception as exc:
            detail = f"{type(exc).__name__}: {exc}"
            self.attempts.append(AttemptRecord(index=index, content=None, model=None, error=detail))
            raise
        metrics = call_metrics(result, role="structuring")
        self.attempts.append(
            AttemptRecord(
                index=index,
                content=result.content,
                model=result.model,
                done_reason=metrics.done_reason,
            )
        )
        return result
"""

#: The claim S3 addresses, in its claim source's own shape.
SCENARIO_MODULE = """async def test_the_artifact_carries_every_raw_attempt(boiler_case) -> None:
    client = RecordingChatClient(CannedTransport(["{not json", _matching_body(boiler_case)]))
    outcome = await run_case(boiler_case, client)
    record = case_artifact(boiler_case, outcome)

    assert record["attempt_count"] == 2
"""

#: Probe S3 exactly as it stood in benchmarks/intake_extraction/probe_battery.json on main
#: before this change. Its anchor still names the one-line append.
S3_ROTTED = {
    "claim_sources": ["tests/benchmark/test_intake_extraction_scenario.py"],
    "probes": [
        {
            "name": "S3-raw-attempt-capture-cut",
            "subject": "benchmarks/intake_extraction/run_benchmark.py",
            "old": (
                "        self.attempts.append(AttemptRecord(index=index, "
                "content=result.content, model=result.model))\n"
            ),
            "new": "        pass  # probe: raw-attempt capture cut\n",
            "node_id": (
                "tests/benchmark/test_intake_extraction_scenario.py"
                "::test_the_artifact_carries_every_raw_attempt"
            ),
            "expect_claim": (
                'test_the_artifact_carries_every_raw_attempt|record["attempt_count"] == 2|#0'
            ),
        }
    ],
}

DEAD_LINE = "🔴 DEAD benchmarks/intake_extraction/probe_battery.json"
S3_FINDING = "S3-raw-attempt-capture-cut: anchor occurs 0 times"
COUNTS = "batteries: 2 (outside tests/batteries/: 1)"


def test_scenario_a_dead_battery_beside_its_subject_fails_the_guard(tmp_path: Path) -> None:
    """Drives the guard the way pre-commit does: as a subprocess over a real git index.

    Before this change, the same tree printed ``BATTERY-DEFINITIONS: OK`` and exited 0.
    """
    _healthy_home_battery(tmp_path)
    _write(tmp_path, "benchmarks/intake_extraction/run_benchmark.py", RUN_BENCHMARK)
    _write(tmp_path, "tests/benchmark/test_intake_extraction_scenario.py", SCENARIO_MODULE)
    _write(
        tmp_path,
        "benchmarks/intake_extraction/probe_battery.json",
        json.dumps(S3_ROTTED, indent=2),
    )
    env = {
        **os.environ,
        "GIT_CEILING_DIRECTORIES": str(tmp_path.parent),
        "PYTHONIOENCODING": "utf-8",
    }
    for argv in (["git", "init", "-q"], ["git", "add", "-A"]):
        subprocess.run(argv, cwd=tmp_path, env=env, check=True, capture_output=True)

    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    out = proc.stdout

    assert proc.returncode == 1, out + proc.stderr  # claim: battery-reach/S-rc
    assert DEAD_LINE in out  # claim: battery-reach/S-named
    assert S3_FINDING in out  # claim: battery-reach/S-finding
    assert COUNTS in out  # claim: battery-reach/S-count
