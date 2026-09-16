"""``tools/measure.py`` — the emitter's contract, witnessed RED (PLAN-0125 Step 1).

Every behaviour below is read from the emitter run as a **subprocess** against a
throwaway git repository built per test with realistic content: a copy of STATUS's
frontmatter (Thai text included, so the UTF-8 reducers meet real bytes), a PLAN
grounding table, two ``docs/logs/`` files and a gitignored run log. Nothing mocks the
emitter or git. The one in-process import is the scenario test's *consumer* —
``parse_blocks`` / ``verify_hash``, the parser the staleness guard (Step 2) will import.

Each test prints the values it measured in its assertion message, so a failure names
what broke instead of starting a hunt (Lesson #0043). The probes that witness each
assertion RED live in ``tests/batteries/plan-0125-step1.json``.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from tools.measure import parse_blocks, verify_hash

REPO_ROOT = Path(__file__).resolve().parents[2]
EMITTER = REPO_ROOT / "tools" / "measure.py"
CATALOGUE = REPO_ROOT / "tools" / "README.md"
TOKEN = "MEASURE:"
MARKER = "<!-- measure:v1 -->"

_GIT_IDENTITY = ["-c", "user.name=t", "-c", "user.email=t@example.invalid"]

_STATUS = """---
session: 301
head_commit: 75cd580
recent_commits: [e83422c, e94b80e, 75cd580, f30cf47, 7089625]
last_updated: "2026-09-15T15:30:00+07:00"
current_batch: "s300-301 (#1489-#1491), all merged"
next_action: "Code: PLAN-0125 Step 1 (tools/measure.py, AC-1…AC-5)."
---

# vero-lite — STATUS

## Current Focus

> ✅ **#1491 (merge `75cd580`) — PLAN-0125 Step 0.** Pass reads `A gate rc=1 drift=2`.
> สถานะ: gate ทำงานแล้ว — reconcile จาก main ที่ fresh เท่านั้น
"""

_PLAN = """# PLAN-0999: fixture PLAN

## 1. Grounding

| # | Claim | Source | Mark |
|---|---|---|---|
| G15 | the range `793b9d9..f65f7ea` holds 9 commits | dispatch §2 | ⚠️ asserted-not-verified |
| G17 | `docs/STATUS.md` = 58,401 B at `f65f7ea` | dispatch §2 | ⚠️ asserted-not-verified |
"""

_LOG_A = """# PLAN-0999 Step 0 closeout

**Date:** 2026-09-14
**Event type:** other

## Key metrics

battery 27/27 WITNESSED, GAPS 0
"""

_LOG_B = """# PLAN-0999 fact-pack measures

**Date:** 2026-09-15
**Event type:** measurement

## Blocks
"""

_REALISTIC = {
    "docs/STATUS.md": _STATUS,
    "docs/plans/0999-fixture.md": _PLAN,
    "docs/logs/2026-09-14-plan0999-step0-closeout.md": _LOG_A,
    "docs/logs/2026-09-15-plan0999-fact-pack-measures.md": _LOG_B,
    ".gitignore": "*.log\n",
}


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *_GIT_IDENTITY, *args],  # noqa: S607  ("git" via PATH — the house idiom)
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _commit(root: Path, subject: str, name: str) -> None:
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    before = target.read_text(encoding="utf-8") if target.exists() else ""
    target.write_text(before + subject + "\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", subject)


def _repo(tmp_path: Path) -> tuple[Path, str]:
    """The realistic tree, one commit on ``main``; returns ``(root, full sha)``."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "checkout", "-q", "-b", "main")
    for rel, text in _REALISTIC.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    (root / "state.log").write_text("gitignored run log — never a measure subject\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "feat: realistic fixture tree")
    return root, _git(root, "rev-parse", "HEAD")


def _history_repo(tmp_path: Path) -> tuple[Path, str, str]:
    """``A..B`` holds four commits and **2** substantive ones (the Step 0 shape).

    After ``A``: a ``docs(status):`` reconcile, a side-branch commit, a ``main`` commit,
    and the merge bringing the side branch in.
    """
    root, first = _repo(tmp_path)
    _commit(root, "docs(status): reconcile at the first commit", "docs/STATUS.md")
    _git(root, "checkout", "-q", "-b", "side")
    _commit(root, "feat: second", "side.txt")
    _git(root, "checkout", "-q", "main")
    _commit(root, "fix: third", "f.txt")
    _git(root, "merge", "-q", "--no-ff", "-m", "Merge branch 'side'", "side")
    return root, first, _git(root, "rev-parse", "HEAD")


def _emit(cwd: Path, *args: str, env: dict[str, str] | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(EMITTER), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    return proc.returncode, proc.stdout + proc.stderr


# --- the instruments every reading below goes through -------------------------------------


def _values(out: str) -> dict[str, str]:
    """The ``key=value`` fields of the first ``MEASURE:`` values line (never a refusal line)."""
    for line in out.splitlines():
        if line.startswith(TOKEN + " metric="):
            return dict(tok.split("=", 1) for tok in line[len(TOKEN) :].split() if "=" in tok)
    return {}


def _refused_rule(out: str) -> str | None:
    match = re.search(r"^MEASURE: REFUSED (\S+) —", out, flags=re.M)
    return match.group(1) if match else None


def _blocks(out: str) -> list[str]:
    return re.findall(r"^<!-- measure:v1 -->\n```json\n(.*?)\n```$", out, flags=re.M | re.S)


def _independent_seal(block: dict[str, object]) -> str:
    """PLAN-0125 §2.2's seal, re-implemented here on purpose: an oracle the emitter can't share."""
    body = {key: value for key, value in block.items() if key != "hash"}
    digest = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode())
    return "sha256:" + digest.hexdigest()[:16]


_KNOWN_OUTPUT = (
    "MEASURE: metric=m value=3 units=commits against=" + "a" * 40 + " paths=history "
    "pass=True control=0 hash=0123456789abcdef\n"
    f'{MARKER}\n```json\n{{\n  "value": "3"\n}}\n```\n'
    "VERDICT: PASS exit=0\n"
)
_KNOWN_REFUSAL = "MEASURE: REFUSED R5 — history endpoint(s) ['main'] are not SHAs\n"


def test_the_output_parsers_read_a_known_output() -> None:
    """Instrument control (Lesson #0056): every reading below passes through these parsers."""
    got = (
        _values(_KNOWN_OUTPUT).get("value"),
        _refused_rule(_KNOWN_REFUSAL),
        _blocks(_KNOWN_OUTPUT),
    )
    assert got == ("3", "R5", ['{\n  "value": "3"\n}']), f"got={got!r}"


# --- AC-1: a block re-verifies, and a tampered one does not -------------------------------


def _sized_text(size: int) -> bytes:
    body = "".join(f"line {n:04d} of a fixed-size fixture\n" for n in range(size))
    return body.encode("ascii")[:size]


def test_a_block_reverifies_and_a_tampered_one_does_not(tmp_path: Path) -> None:
    root, _ = _repo(tmp_path)
    rel = "docs/logs/2026-09-15-bytes-fixture.md"
    (root / rel).write_bytes(_sized_text(1234))
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "docs(logs): a 1234-byte fixture")
    rc, out = _emit(
        root,
        *("--metric", "fixture_bytes", "--units", "bytes", "--who", "test-ac1"),
        *("--predicate", "value == 1234", "--paths", rel, "--file", rel, "--reduce", "bytes"),
        *("--control-file", "docs/STATUS.md", "--control-reduce", "bytes"),
    )
    texts = _blocks(out)
    block = json.loads(texts[0]) if len(texts) == 1 else {}
    recomputed = _independent_seal(block)
    assert (len(texts), block.get("hash") == recomputed) == (1, True), (
        f"AC-1: emitted={len(texts)} hash={block.get('hash')} recomputed={recomputed} "
        f"rc={rc} out={out!r}"
    )
    tampered = json.loads(
        texts[0].replace(f'"value": "{block["value"]}"', f'"value": "{block["value"]}0"')
    )
    tampered_verified = tampered.get("hash") == _independent_seal(tampered)
    assert tampered_verified is False, (
        f"AC-1: tampered_verified={tampered_verified} "
        f"value pre={block.get('value')} post={tampered.get('value')}"
    )
    assert block.get("value") == "1234", f"AC-1: value={block.get('value')} (pre=1234) rc={rc}"


# --- AC-2: the refusals refuse, and a clean call does not ---------------------------------

_BASE = ("--metric", "m", "--units", "u", "--who", "test-ac2", "--predicate", "value >= 0")
_CONTROL_EMPTY_RANGE = (
    "--control-argv",
    "git log --format=%h {A}..{A}",
    "--control-reduce",
    "lines",
)
_LOG_A_B = ("--", "git", "log", "--format=%h", "{A}..{B}")
_MISSING = "0" * 40

#: ``(id, the rule that must fire, the argv template)``. Each case is built so that with its
#: own refusal disabled it would run to a block (or another rule) — so a probe that removes
#: that refusal reddens this case and no other.
REFUSAL_CASES: list[tuple[str, str, tuple[str, ...]]] = [
    ("R1", "R1", (*_BASE, *_CONTROL_EMPTY_RANGE, "--reduce", "lines", *_LOG_A_B)),
    (
        "R2-gitignored",
        "R2",
        (
            *_BASE,
            "--paths",
            "state.log",
            "--file",
            "state.log",
            "--reduce",
            "bytes",
            "--control-file",
            "docs/STATUS.md",
            "--control-reduce",
            "bytes",
        ),
    ),
    (
        "R2-dirty",
        "R2",
        (
            *_BASE,
            "--paths",
            "docs/STATUS.md",
            "--file",
            "docs/STATUS.md",
            "--reduce",
            "bytes",
            "--control-file",
            "docs/plans/0999-fixture.md",
            "--control-reduce",
            "bytes",
        ),
    ),
    (
        "R3",
        "R3",
        (
            "--metric",
            "m",
            "--units",
            "u",
            "--who",
            "test-ac2",
            "--history",
            *_CONTROL_EMPTY_RANGE,
            "--reduce",
            "lines",
            *_LOG_A_B,
        ),
    ),
    ("R4-absent", "R4", (*_BASE, "--history", "--reduce", "lines", *_LOG_A_B)),
    (
        "R4-equal",
        "R4",
        (
            *_BASE,
            "--history",
            "--control-argv",
            "git log --format=%h {A}..{B}",
            "--control-reduce",
            "lines",
            "--reduce",
            "lines",
            *_LOG_A_B,
        ),
    ),
    (
        "R5",
        "R5",
        (
            *_BASE,
            "--history",
            *_CONTROL_EMPTY_RANGE,
            "--reduce",
            "lines",
            "--",
            "git",
            "log",
            "--format=%h",
            f"{_MISSING}..{{B}}",
        ),
    ),
    (
        "R6-wrap",
        "R6",
        (
            *_BASE,
            "--paths",
            "docs/STATUS.md",
            *_CONTROL_EMPTY_RANGE,
            "--reduce",
            "lines",
            "--",
            "env",
            "bash",
            "-c",
            "echo x",
        ),
    ),
    (
        "R6-paste",
        "R6",
        (
            *_BASE,
            "--paths",
            "docs/STATUS.md",
            *_CONTROL_EMPTY_RANGE,
            "--reduce",
            "lines",
            "--",
            "git log --oneline",
        ),
    ),
    (
        "R7",
        "R7",
        (
            *_BASE,
            "--paths",
            "docs/STATUS.md",
            "--rerun",
            *_CONTROL_EMPTY_RANGE,
            "--reduce",
            "lines",
            "--",
            "git",
            "grep",
            "-c",
            "head_commit",
            "--",
            "docs/STATUS.md",
        ),
    ),
    (
        "R8",
        "R8",
        (
            *_BASE,
            "--paths",
            "notes.md",
            "--file",
            "notes.md",
            "--reduce",
            "bytes",
            "--control-file",
            "notes.md",
            "--control-reduce",
            "lines",
        ),
    ),
]


@pytest.mark.parametrize(
    ("case", "rule", "template"), REFUSAL_CASES, ids=[case for case, _, _ in REFUSAL_CASES]
)
def test_each_refusal_refuses_and_writes_no_block(
    tmp_path: Path, case: str, rule: str, template: tuple[str, ...]
) -> None:
    root, first, tip = _history_repo(tmp_path)
    cwd, env = root, None
    if case == "R2-dirty":
        (root / "docs" / "STATUS.md").write_text(
            _STATUS + "an uncommitted edit\n", encoding="utf-8"
        )
    if case == "R8":
        cwd = tmp_path / "not-a-repo"
        cwd.mkdir()
        (cwd / "notes.md").write_text("no repository around this file\n")
        env = {**os.environ, "GIT_CEILING_DIRECTORIES": str(tmp_path)}
    out_file = tmp_path / "out" / "measures.md"
    args = [part.replace("{A}", first).replace("{B}", tip) for part in template]
    rc, out = _emit(cwd, "--out", str(out_file), *args, env=env)
    written = out_file.exists() or MARKER in out
    assert (rc, _refused_rule(out), written) == (2, rule, False), (
        f"AC-2 {case}: rc={rc} rule={_refused_rule(out)} (expected {rule}) "
        f"block_written={written} out={out!r}"
    )


def test_a_clean_call_with_git_c_and_a_regex_is_not_refused(tmp_path: Path) -> None:
    """The control that the refusals are not "everything exits 2" (AC-2)."""
    root, first, tip = _history_repo(tmp_path)
    rc, out = _emit(
        root,
        *("--metric", "status_head_drift", "--units", "commits", "--who", "test-ac2"),
        *("--history", "--rerun", "--predicate", "value == 2"),
        *("--control-argv", f"git log --format=%h {first}..{first}", "--control-reduce", "lines"),
        *("--reduce", "lines", "--", "git", "-c", "core.quotepath=false", "log", "--no-merges"),
        *("--invert-grep", "--grep=^docs(status):", "--format=%h", f"{first}..{tip}"),
    )
    got = (rc, _refused_rule(out), len(_blocks(out)), _values(out).get("value"))
    assert got == (0, None, 1, "2"), f"AC-2 clean: (rc, rule, blocks, value)={got!r} out={out!r}"


# --- AC-3: reducers agree with a hand-computed value, and no shell runs -------------------

#: Five ``needle`` occurrences on FOUR lines, and no upper-case ``NEEDLE`` anywhere: a
#: reducer counting lines reads 4, and a case-blind one finds the absent needle.
_NEEDLES = "needle one\nneedle needle two\n\nthree needle\nfour needle\n"


def test_reducers_agree_with_hand_computed_values(tmp_path: Path) -> None:
    root, first = _repo(tmp_path)
    (root / "needles.txt").write_text(_NEEDLES, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "test: plant five needles")
    _commit(root, "feat: two", "f.txt")
    _commit(root, "feat: three", "f.txt")
    tip = _git(root, "rev-parse", "HEAD")
    base = ("--metric", "m", "--units", "u", "--who", "test-ac3")
    _, lines_out = _emit(
        root,
        *base,
        "--history",
        "--predicate",
        "value == 3",
        "--control-argv",
        f"git log --format=%h {first}..{first}",
        "--reduce",
        "lines",
        "--",
        "git",
        "log",
        "--format=%h",
        f"{first}..{tip}",
    )
    needles = ("--paths", "needles.txt", "--file", "needles.txt", "--control-file", "needles.txt")
    _, count_out = _emit(
        root,
        *base,
        *needles,
        "--predicate",
        "value == 5",
        "--reduce",
        "count:needle",
        "--control-reduce",
        "count:two",
    )
    _, absent_out = _emit(
        root,
        *base,
        *needles,
        "--predicate",
        "value == 0",
        "--reduce",
        "count:NEEDLE",
        "--control-reduce",
        "count:two",
    )
    lines, count, absent = (_values(o).get("value") for o in (lines_out, count_out, absent_out))
    assert lines == "3", f"AC-3: lines pre=3 got={lines} out={lines_out!r}"
    assert (
        count == "5"
    ), f"AC-3: count pre=5 got={count} (lines-with-needle would read 4) out={count_out!r}"
    assert absent == "0", f"AC-3: absent pre=0 got={absent} (case-sensitive) out={absent_out!r}"


def test_a_symbolic_history_endpoint_is_refused(tmp_path: Path) -> None:
    root, first, _tip = _history_repo(tmp_path)
    rc, out = _emit(
        root,
        *_BASE,
        "--history",
        "--control-argv",
        f"git log --format=%h {first}..{first}",
        "--control-reduce",
        "lines",
        "--reduce",
        "lines",
        "--",
        "git",
        "log",
        "--format=%h",
        f"{first}..main",
    )
    assert (rc, _refused_rule(out)) == (
        2,
        "R5",
    ), f"AC-3: symbolic_ref rc={rc} rule={_refused_rule(out)} out={out!r}"


def test_the_one_process_call_site_never_runs_a_shell() -> None:
    """AC-3's source-text half: every process start in the emitter, by owner and shell flag."""
    tree = ast.parse(EMITTER.read_text(encoding="utf-8"))
    sites: list[tuple[str, str, bool]] = []
    for function in ast.walk(tree):
        if not isinstance(function, ast.FunctionDef):
            continue
        for node in ast.walk(function):
            if not isinstance(node, ast.Call):
                continue
            callee = ast.unparse(node.func)
            if callee.startswith(("subprocess.", "os.system", "os.popen", "os.exec", "os.spawn")):
                shell = next((kw.value for kw in node.keywords if kw.arg == "shell"), None)
                literal_false = isinstance(shell, ast.Constant) and shell.value is False
                sites.append((function.name, callee, literal_false))
    assert sites == [
        ("_spawn", "subprocess.run", True)
    ], f"AC-3: process call sites (owner, callee, shell=False literal) = {sites!r}"


# --- AC-4: the predicate is a parser, not eval --------------------------------------------

_NINE = "abc\n" + "".join(f"row {n}\n" for n in range(2, 10))


def _predicate_repo(tmp_path: Path) -> Path:
    root, _ = _repo(tmp_path)
    (root / "nine.txt").write_text(_NINE, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "test: a nine-line file whose first line is abc")
    return root


def _predicate_run(root: Path, predicate: str, reducer: str) -> tuple[int, str]:
    return _emit(
        root,
        "--metric",
        "m",
        "--units",
        "u",
        "--who",
        "test-ac4",
        "--predicate",
        predicate,
        "--paths",
        "nine.txt",
        "--file",
        "nine.txt",
        "--reduce",
        reducer,
        "--control-file",
        "docs/STATUS.md",
        "--control-reduce",
        "bytes",
    )


def test_predicates_in_the_grammar_are_evaluated(tmp_path: Path) -> None:
    root = _predicate_repo(tmp_path)
    cases = [
        ("value == 9", "lines"),
        ("value <= 65536", "bytes"),
        ("3 <= value <= 5", "lines"),
        ('value == "abc"', "first"),
    ]
    got = []
    for predicate, reducer in cases:
        rc, out = _predicate_run(root, predicate, reducer)
        got.append((rc, _values(out).get("pass")))
    expected = [(0, "True"), (0, "True"), (1, "False"), (0, "True")]
    assert got == expected, f"AC-4 accepted: got={got!r} expected={expected!r}"


def test_injection_shaped_predicates_are_refused(tmp_path: Path) -> None:
    root = _predicate_repo(tmp_path)
    got = []
    for predicate in ("__import__('os')", "value == 9 or True"):
        rc, out = _predicate_run(root, predicate, "lines")
        got.append((rc, _refused_rule(out)))
    assert got == [(2, "R3"), (2, "R3")], f"AC-4 rejected: got={got!r}"


# --- Lesson #0007: a failed procedure never becomes a number ------------------------------


def test_a_failing_procedure_is_refused_never_reduced(tmp_path: Path) -> None:
    """``git log <bad-ref>`` exits 128 with one stderr line; that line must not become value=1."""
    root, _ = _repo(tmp_path)
    rc, out = _emit(
        root,
        *_BASE,
        "--paths",
        "docs/STATUS.md",
        "--control-file",
        "docs/STATUS.md",
        "--control-reduce",
        "bytes",
        "--reduce",
        "lines",
        "--",
        "git",
        "log",
        "--format=%h",
        "no-such-ref",
    )
    got = (rc, _refused_rule(out), MARKER in out)
    assert got == (
        2,
        "procedure",
        False,
    ), f"procedure failure: (rc, rule, block)={got!r} out={out!r}"


# --- CLAUDE.md §8 scenario: the real emitter into the real consumer ----------------------


def test_scenario_appended_blocks_parse_back_through_the_guard_parser(tmp_path: Path) -> None:
    """Two blocks appended to a real ``docs/logs`` file, read back by the Step 2 guard's parser."""
    root, first, tip = _history_repo(tmp_path)
    log = root / "docs" / "logs" / "2026-09-15-plan0999-fact-pack-measures.md"
    drift = len(
        _git(
            root,
            "log",
            "--no-merges",
            "--invert-grep",
            "--grep=^docs(status):",
            "--format=%h",
            f"{first}..{tip}",
        ).split()
    )
    size = len((root / "docs" / "STATUS.md").read_bytes())
    rc_history, out_history = _emit(
        root,
        "--out",
        str(log),
        "--metric",
        "status_head_drift",
        "--units",
        "commits",
        "--who",
        "test-scenario",
        "--history",
        "--rerun",
        "--predicate",
        f"value == {drift}",
        "--control-argv",
        f"git log --format=%h {first}..{first}",
        "--control-reduce",
        "lines",
        "--reduce",
        "lines",
        "--",
        "git",
        "log",
        "--no-merges",
        "--invert-grep",
        "--grep=^docs(status):",
        "--format=%h",
        f"{first}..{tip}",
    )
    rc_path, out_path = _emit(
        root,
        "--out",
        str(log),
        "--metric",
        "status_bytes",
        "--units",
        "bytes",
        "--who",
        "test-scenario",
        "--paths",
        "docs/STATUS.md",
        "--file",
        "docs/STATUS.md",
        "--reduce",
        "bytes",
        "--predicate",
        "value <= 65536",
        "--rerun",
        "--control-file",
        "docs/plans/0999-fixture.md",
        "--control-reduce",
        "bytes",
    )
    parsed = parse_blocks(log.read_text(encoding="utf-8"))
    readings = [(block.data or {}).get("value") for block in parsed]
    sealed = [block.data is not None and verify_hash(block.data) for block in parsed]
    got = (rc_history, rc_path, readings, sealed)
    assert got == (0, 0, [str(drift), str(size)], [True, True]), (
        f"scenario: (rc_history, rc_path, readings, sealed)={got!r} expected drift={drift} "
        f"size={size} out_history={out_history!r} out_path={out_path!r}"
    )


# --- AC-20 (Step 1 half): the catalogue names the emitter ---------------------------------


def test_the_catalogue_names_the_emitter() -> None:
    text = CATALOGUE.read_text(encoding="utf-8")
    row, control = text.count("| **`measure.py`** |"), text.count("no-such-tool.py")
    assert (row, control) == (1, 0), f"AC-20: measure.py row post={row} (pre=0) control={control}"


# --- AC-12 (Step 3): the status-reconcile recipe, real producer into real consumer ---------
#
# The scenario CLAUDE.md §8 asks for: the real emitter drives the real parser the staleness
# guard imports, over a real git repository. Nothing is stubbed on either side of the seam.
# One assertion per test, because one mutation witnesses only one assertion — the probes are
# P-12.1 … P-12.3 in tests/batteries/plan-0125-step3.json.

_PROSE_PAYLOAD = """The scribe's payload, with the two facts typed as prose instead:

head_commit: abc1234
recent_commits: [abc1234, def5678, 0123abc]
"""


def _recipe_blocks(root: Path) -> tuple[int, str, list[dict[str, object]]]:
    """Run the recipe; return its status, its whole output, and every block it emitted.

    The **raw list**, deliberately: an earlier draft indexed by ``metric`` first, and a
    recipe that emitted the same block twice would have collapsed to two keys and slipped
    past the count assertion. The count claim is about blocks, so it is read off blocks.
    """
    code, out = _emit(root, "--recipe", "status-reconcile", "--who", "test-scenario")
    return code, out, [json.loads(text) for text in _blocks(out)]


def _by_metric(blocks: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(block["metric"]): block for block in blocks}


def test_the_recipe_emits_two_sealed_blocks(tmp_path: Path) -> None:
    """AC-12 — two blocks from one invocation, each sealed (the seal itself is AC-1's claim)."""
    root, _first, _tip = _history_repo(tmp_path)
    code, out, blocks = _recipe_blocks(root)
    sealed = sorted(str(block["metric"]) for block in blocks if verify_hash(block))
    got = (code, len(blocks), sealed)
    assert got == (
        0,
        2,
        ["status_head_commit", "status_recent_commits"],
    ), f"AC-12: (rc, blocks, sealed)={got!r} — expected (0, 2, both metrics sealed). out={out!r}"


def test_the_recipes_head_value_equals_an_independent_computation(tmp_path: Path) -> None:
    """AC-12 — the value the scribe would transcribe, against the test's own git call."""
    root, _first, _tip = _history_repo(tmp_path)
    _code, out, blocks = _recipe_blocks(root)
    expected = _git(root, "rev-parse", "--short=7", "main")
    got = _by_metric(blocks).get("status_head_commit", {}).get("value")
    assert (
        got == expected
    ), f"AC-12 head_match: block value={got!r} independent={expected!r}. out={out!r}"


def test_the_recipes_recent_value_equals_an_independent_computation(tmp_path: Path) -> None:
    """AC-12 — the same, for the ten-commit list. The PLAN's ``-n 10`` is the test's form."""
    root, _first, _tip = _history_repo(tmp_path)
    _code, out, blocks = _recipe_blocks(root)
    expected = _git(root, "log", "--format=%h", "-n", "10", "main")
    got = _by_metric(blocks).get("status_recent_commits", {}).get("value")
    assert (
        got == expected
    ), f"AC-12 recent_match: block value={got!r} independent={expected!r}. out={out!r}"


def test_prose_where_a_block_belongs_is_not_a_block(tmp_path: Path) -> None:
    """AC-12's control — and it carries its own positive control.

    ``prose_rejected`` is a negative reading ("this text holds no block"), which an
    always-empty parser would satisfy for free (CLAUDE.md §8). So the same parser, in the
    same assertion, must still find the two real blocks: the positive half is what makes
    the negative half mean something.
    """
    root, _first, _tip = _history_repo(tmp_path)
    _code, out, _blocks_seen = _recipe_blocks(root)
    prose = [block for block in parse_blocks(_PROSE_PAYLOAD) if block.data is not None]
    real = [block for block in parse_blocks(out) if block.data is not None]
    got = (len(prose), len(real))
    assert got == (0, 2), (
        f"AC-12: (prose_blocks, real_blocks)={got!r} — expected (0, 2). A parser that "
        f"read 0 real blocks makes the prose reading vacuous. out={out!r}"
    )


def test_the_recipe_refuses_to_persist_its_blocks(tmp_path: Path) -> None:
    """PLAN-0125 §6 E1 — a recipe block is payload provenance and is never written down."""
    root, _first, _tip = _history_repo(tmp_path)
    target = root / "docs" / "logs" / "never-written.md"
    code, out = _emit(
        root, "--recipe", "status-reconcile", "--who", "test-scenario", "--out", str(target)
    )
    got = (code, _refused_rule(out), target.exists())
    assert got == (2, "recipe", False), f"E1: (rc, rule, file_exists)={got!r} out={out!r}"


def test_an_unknown_recipe_is_refused_by_name(tmp_path: Path) -> None:
    """The recipe set is closed: an unknown name refuses rather than emitting nothing quietly."""
    root, _first, _tip = _history_repo(tmp_path)
    code, out = _emit(root, "--recipe", "no-such-recipe", "--who", "test-scenario")
    got = (code, _refused_rule(out), _blocks(out))
    assert got == (2, "recipe", []), f"unknown recipe: (rc, rule, blocks)={got!r} out={out!r}"
