"""``tools/check_measure_staleness.py`` — the staleness guard, witnessed RED (PLAN-0125 Step 2).

Every reading below comes from the guard run as a **subprocess** over a throwaway git
repository. Its blocks were emitted by the real ``tools/measure.py`` (the producer), and
each broken shape is made the way a session would make it: commit an edit to a declared
path, change one byte of a block, re-seal a value by hand, cite a hash nobody emitted.
Nothing mocks git, the emitter or the guard (CLAUDE.md §8 — the scenario rule).

Each assertion prints the values it measured, so a failure names what broke (Lesson
#0043). The probes that witness each assertion RED live in
``tests/batteries/plan-0125-step2.json``.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
GUARD = REPO_ROOT / "tools" / "check_measure_staleness.py"
EMITTER = REPO_ROOT / "tools" / "measure.py"
CATALOGUE = REPO_ROOT / "tools" / "README.md"
PRECOMMIT = REPO_ROOT / ".pre-commit-config.yaml"
PREFIX = "MEASURE-STALENESS:"
MARKER = "<!-- measure:v1 -->"
WHO = "test-s303"

STATUS = "docs/STATUS.md"
TEMPLATE = "docs/plans/0000-template.md"
PLAN = "docs/plans/0999-fixture.md"
LOG = "docs/logs/2026-09-15-plan0999-fact-pack-measures.md"
NO_SUCH_SHA = "0123456789abcdef0123456789abcdef01234567"  # pragma: allowlist secret
NO_SUCH_HASH = "0123456789abcdef"  # pragma: allowlist secret

_GIT_IDENTITY = ["-c", "user.name=t", "-c", "user.email=t@example.invalid"]

_STATUS = """---
session: 302
head_commit: df5beb6
recent_commits: [df5beb6, 39fdf7f, e83422c, e94b80e, 75cd580]
last_updated: "2026-09-15T20:25:00+07:00"
current_batch: "s302 (#1493-#1494), both merged"
next_action: "Code: PLAN-0125 Step 2 (tools/check_measure_staleness.py, AC-6…AC-11)."
---

# vero-lite — STATUS

## Current Focus

> ✅ **#1493 (merge `df5beb6`) — PLAN-0125 Step 1.** battery 26/26 WITNESSED, GAPS 0.
> สถานะ: emitter ใช้งานได้แล้ว — guard ยังไม่มี
"""

_TEMPLATE = """# PLAN-NNNN: <title>

**Status:** Draft
**Owner:** Claude Code

## Goal

## Acceptance Criteria

## Out of Scope

## Steps
"""

_PLAN = """# PLAN-0999: fixture PLAN

## 1. Grounding

| # | Claim | Source | Mark |
|---|---|---|---|
| G15 | the range holds 2 commits | Step 1 fixture | ⚠️ asserted-not-verified |
| G17 | `docs/STATUS.md` fits R1 | Step 1 fixture | ⚠️ asserted-not-verified |
"""

_LOG_CLOSEOUT = """# PLAN-0999 Step 1 closeout

**Date:** 2026-09-15
**Event type:** other

## Key metrics

battery 26/26 WITNESSED, GAPS 0
"""

_LOG_MEASURES = """# PLAN-0999 fact-pack measures

**Date:** 2026-09-15
**Event type:** measurement

## Blocks
"""

_REALISTIC = {
    STATUS: _STATUS,
    TEMPLATE: _TEMPLATE,
    PLAN: _PLAN,
    "docs/logs/2026-09-15-plan0999-step1-closeout.md": _LOG_CLOSEOUT,
    LOG: _LOG_MEASURES,
}


# --- the throwaway repository ------------------------------------------------------------


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *_GIT_IDENTITY, *args],  # noqa: S607  ("git" via PATH — the house idiom)
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _commit_all(root: Path, subject: str) -> str:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", subject)
    return _git(root, "rev-parse", "HEAD")


def _append(root: Path, rel: str, text: str) -> None:
    target = root / rel
    target.write_text(target.read_text(encoding="utf-8") + text, encoding="utf-8")


def _repo(tmp_path: Path) -> tuple[Path, str, str]:
    """The realistic tree and two more commits on ``main``: ``(root, first, tip)``.

    ``first..tip`` holds exactly **2** commits — the range the history blocks measure.
    """
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "checkout", "-q", "-b", "main")
    for rel, text in _REALISTIC.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    first = _commit_all(root, "feat: realistic fixture tree")
    (root / "services").mkdir()
    (root / "services" / "engine.py").write_text("RUNS = 1\n", encoding="utf-8")
    _commit_all(root, "feat(engine): the first runtime module")
    _append(root, "services/engine.py", "RUNS = 2\n")
    tip = _commit_all(root, "fix(engine): count the second run")
    return root, first, tip


def _emit(root: Path, *args: str) -> str:
    """Append one block to ``LOG`` with the real emitter; its 16-hex hash.

    A fixture that did not emit raises — it is a precondition, not a claim about the guard.
    """
    proc = subprocess.run(
        [sys.executable, str(EMITTER), "--out", LOG, "--who", WHO, *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    found = re.search(r"^MEASURE: appended sha256:([0-9a-f]{16}) to ", proc.stdout, flags=re.M)
    if proc.returncode != 0 or found is None:
        raise RuntimeError(
            f"fixture emission failed rc={proc.returncode}: {proc.stdout}{proc.stderr}"
        )
    return found.group(1)


def _emit_template_tokens(root: Path) -> str:
    """A path block over the template, re-runnable: ``count:measure`` = 0, control ``Goal`` = 1."""
    return _emit(
        root,
        *("--metric", "template_measure_tokens", "--units", "occurrences"),
        *("--paths", TEMPLATE, "--file", TEMPLATE, "--reduce", "count:measure", "--rerun"),
        *(
            "--predicate",
            "value == 0",
            "--control-file",
            TEMPLATE,
            "--control-reduce",
            "count:Goal",
        ),
    )


def _emit_status_bytes(root: Path) -> str:
    """A path block over STATUS, NOT re-runnable — so only staleness can ever catch it."""
    return _emit(
        root,
        *("--metric", "status_bytes", "--units", "bytes"),
        *("--paths", STATUS, "--file", STATUS, "--reduce", "bytes"),
        *("--predicate", "value <= 65536", "--control-file", TEMPLATE, "--control-reduce", "bytes"),
    )


def _emit_range(root: Path, metric: str, first: str, tip: str) -> str:
    """A re-runnable history block: ``git log first..tip`` = 2 lines, the empty range as control."""
    return _emit(
        root,
        *("--metric", metric, "--units", "commits", "--history", "--rerun"),
        *("--predicate", "value == 2", "--reduce", "lines"),
        *("--control-argv", f"git log --format=%h {first}..{first}", "--control-reduce", "lines"),
        *("--", "git", "log", "--format=%h", f"{first}..{tip}"),
    )


def _independent_seal(block: dict[str, Any]) -> str:
    """PLAN-0125 §2.2's seal, re-implemented on purpose: an oracle the guard cannot share."""
    body = {key: value for key, value in block.items() if key != "hash"}
    digest = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode())
    return "sha256:" + digest.hexdigest()[:16]


def _fences(text: str) -> list[str]:
    return re.findall(r"^<!-- measure:v1 -->\n```json\n(.*?)\n```$", text, flags=re.M | re.S)


def _rewrite(root: Path, digest: str, change: Callable[[dict[str, Any]], None]) -> None:
    """Change the block sealed ``digest`` in ``LOG`` and re-seal it — a hand edit with a shell."""
    log = root / LOG
    text = log.read_text(encoding="utf-8")
    fence = next(f for f in _fences(text) if f'"hash": "sha256:{digest}"' in f)
    block = json.loads(fence)
    change(block)
    block["hash"] = _independent_seal(block)
    log.write_text(text.replace(fence, json.dumps(block, indent=2, ensure_ascii=False)), "utf-8")


def _tamper(root: Path, digest: str) -> None:
    """Change one byte of the block sealed ``digest`` — the ``who`` — and do NOT re-seal."""
    log = root / LOG
    text = log.read_text(encoding="utf-8")
    fence = next(f for f in _fences(text) if f'"hash": "sha256:{digest}"' in f)
    edited = fence.replace(f'"who": "{WHO}"', f'"who": "{WHO[:-1]}4"')
    log.write_text(text.replace(fence, edited), encoding="utf-8")


# --- the instrument every reading goes through --------------------------------------------


def _guard(root: Path, *extra: str) -> tuple[int, dict[str, str], str]:
    proc = subprocess.run(
        [sys.executable, str(GUARD), str(root), *extra],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    out = proc.stdout + proc.stderr
    return proc.returncode, _values(out), out


def _values(out: str) -> dict[str, str]:
    """The ``key=value`` fields of the values line — never a finding line."""
    for line in out.splitlines():
        if line.startswith(PREFIX + " files="):
            return dict(tok.split("=", 1) for tok in line[len(PREFIX) :].split() if "=" in tok)
    return {}


_KNOWN = (
    f"{PREFIX} files=1 blocks=4 hash_bad=1 unresolvable=0 unavailable=0 stale=1 rerun=2 "
    "mismatch=1 rerun_failed=0 cites=2 dangling=1 stale_cited=0 historical=0 asserted=2 "
    "elapsed_ms=41\n"
    f"{PREFIX} dangling docs/plans/0999-fixture.md:9 — no block is sealed measure:{NO_SUCH_HASH}\n"
    "VERDICT: FAIL exit=1\n"
)


def test_the_values_parser_reads_a_known_output() -> None:
    """Instrument control (Lesson #0056): every counter below is read through ``_values``."""
    got = _values(_KNOWN)
    picked = (got.get("blocks"), got.get("dangling"), got.get("elapsed_ms"), len(got))
    assert picked == ("4", "1", "41", 15), f"parsed={got!r}"


# --- AC-6 + the §8 scenario: five shapes, each by its own positive control ----------------


def test_scenario_the_five_shapes_from_the_real_emitter_are_classified(tmp_path: Path) -> None:
    """One fresh, one stale, one tampered, one re-sealed-wrong block, and one dangling cite.

    Each counter is 1 by construction, and each broken block is built so that disabling
    any one classifier leaves it looking fresh to every other one: the stale block is not
    re-runnable, the tampered byte is ``who`` (the re-run still agrees), and the re-sealed
    block is a history block (no paths to go stale).
    """
    root, first, tip = _repo(tmp_path)
    fresh = _emit_template_tokens(root)
    _emit_status_bytes(root)
    tampered = _emit_range(root, "status_head_range_commits", first, tip)
    resealed = _emit_range(root, "engine_commits", first, tip)
    _commit_all(root, "docs(logs): the fixture blocks")
    _append(root, STATUS, "> ✅ **#1494** — reconciled.\n")
    _commit_all(root, "docs(status): a reconcile moves a declared path")
    _tamper(root, tampered)
    _rewrite(root, resealed, lambda block: block.update(value="3"))
    _append(root, PLAN, f"\n✔ measure:{fresh}\n✔ measure:{NO_SUCH_HASH}\n")
    _commit_all(root, "docs(plans): cite one block that exists and one that does not")

    rc, values, out = _guard(root)
    counted = [int(values.get(key, "0")) for key in ("blocks", "hash_bad", "stale", "mismatch")]
    fresh_left = counted[0] - sum(counted[1:])  # derived, printed: no shape double-counted
    seen = f"values={values!r} fresh_left={fresh_left} rc={rc}\n{out}"
    assert values.get("blocks") == "4", f"AC-6 blocks: {seen}"
    assert values.get("hash_bad") == "1", f"AC-6 hash_bad: {seen}"
    assert values.get("stale") == "1", f"AC-6 stale: {seen}"
    assert values.get("mismatch") == "1", f"AC-6 mismatch: {seen}"
    assert values.get("cites") == "2", f"AC-6 cites: {seen}"
    assert values.get("dangling") == "1", f"AC-6 dangling: {seen}"
    assert rc == 1, f"AC-6 rc: {seen}"


# --- AC-7: the real tree is accepted, and an empty surface is refused ---------------------


def test_the_guard_accepts_the_real_tree() -> None:
    """The over-refusal control on the repository itself (AC-7, AC-8's real half).

    In CI's depth-2 checkout every block reads ``unavailable`` — a visible skip, still rc=0;
    the counters asserted here hold in both clones.
    """
    rc, values, out = _guard(REPO_ROOT)
    seen = f"values={values!r} rc={rc}\n{out[-2000:]}"
    assert int(values.get("blocks", "0")) >= 5, f"AC-7 blocks: {seen}"
    assert int(values.get("cites", "0")) >= 2, f"AC-8 real cites: {seen}"
    gated = tuple(
        values.get(key)
        for key in ("hash_bad", "unresolvable", "mismatch", "rerun_failed", "dangling")
    )
    assert (gated, rc) == (("0", "0", "0", "0", "0"), 0), f"AC-7 real tree: {seen}"


def test_an_empty_surface_is_refused_never_passed(tmp_path: Path) -> None:
    """The null-glob control (PLAN-0108:104-109): no blocks is a red, not a silent green."""
    root, _, _ = _repo(tmp_path)
    rc, values, out = _guard(root)
    seen = f"values={values!r} rc={rc}\n{out}"
    assert "blocks=0 — EMPTY SURFACE, NOT a pass" in out, f"AC-7 empty text: {seen}"
    assert rc == 1, f"AC-7 empty rc: {seen}"


# --- AC-8: a :historical citation never gates; a live one on a stale block does ----------


def _cited_stale_block(tmp_path: Path, token_suffix: str) -> tuple[int, dict[str, str], str]:
    root, _, _ = _repo(tmp_path)
    digest = _emit_status_bytes(root)
    _commit_all(root, "docs(logs): one block over STATUS")
    _append(root, STATUS, "> ✅ **#1494** — reconciled.\n")
    _append(root, PLAN, f"\n| G17 | STATUS size | ✔ measure:{digest}{token_suffix} |\n")
    _commit_all(root, "docs(status): STATUS moves; the PLAN cites the block")
    return _guard(root)


def test_a_historical_citation_of_a_stale_block_does_not_gate(tmp_path: Path) -> None:
    rc, values, out = _cited_stale_block(tmp_path, ":historical")
    seen = f"values={values!r} rc={rc}\n{out}"
    assert values.get("stale") == "1", f"AC-8 historical, stale: {seen}"
    assert values.get("historical") == "1", f"AC-8 historical count: {seen}"
    assert (values.get("stale_cited"), rc) == ("0", 0), f"AC-8 historical never gates: {seen}"


def test_a_live_citation_of_a_stale_block_gates(tmp_path: Path) -> None:
    """SD-7 = (b)'s positive control: without it, ``stale_cited=0`` above proves nothing."""
    rc, values, out = _cited_stale_block(tmp_path, "")
    seen = f"values={values!r} rc={rc}\n{out}"
    assert values.get("stale_cited") == "1", f"AC-8 live cite of a stale block: {seen}"
    assert rc == 1, f"AC-8 live stale cite gates: {seen}"


# --- AC-9 + D1's shallow half: a shallow clone is a visible skip --------------------------


def test_a_shallow_clone_is_a_visible_skip(tmp_path: Path) -> None:
    """Two blocks the clone cannot check, for the two different reasons.

    ``X`` names an ``against_sha`` older than the clone; ``Y`` names one inside it, but its
    procedure's range is not. The clone is taken with ``file://`` — measured s303, a plain
    path makes git ignore ``--depth`` and hand back a full clone, which would make this
    test a second full-clone test that could never see the shallow branch.
    """
    root, first, tip = _repo(tmp_path)
    _emit_template_tokens(root)
    _commit_all(root, "docs(logs): block X")
    _emit_range(root, "engine_commits", first, tip)
    _commit_all(root, "docs(logs): block Y")
    clone = tmp_path / "shallow"
    _git(tmp_path, "clone", "-q", "--depth", "2", root.as_uri(), str(clone))
    shallow = _git(clone, "rev-parse", "--is-shallow-repository")
    assert shallow == "true", f"instrument: the clone is not shallow (read {shallow!r})"

    rc, values, out = _guard(clone)
    seen = f"values={values!r} rc={rc}\n{out}"
    assert values.get("rerun_failed") == "0", f"AC-9 shallow re-run is not a failure: {seen}"
    assert values.get("unavailable") == "2", f"AC-9 shallow unavailable: {seen}"
    assert "NOT checked in this shallow clone, NOT a pass" in out, f"AC-9 skip text: {seen}"
    assert rc == 0, f"AC-9 shallow rc: {seen}"


def test_a_fabricated_against_sha_in_a_full_clone_gates(tmp_path: Path) -> None:
    """The control that ``unavailable`` is not swallowing broken pointers."""
    root, _, _ = _repo(tmp_path)
    digest = _emit_template_tokens(root)
    _rewrite(root, digest, lambda block: block.update(against_sha=NO_SUCH_SHA))
    _commit_all(root, "docs(logs): a block pointing at a commit that never existed")
    rc, values, out = _guard(root)
    seen = f"values={values!r} rc={rc}\n{out}"
    assert values.get("unresolvable") == "1", f"AC-9 full clone unresolvable: {seen}"
    assert rc == 1, f"AC-9 full clone rc: {seen}"


# --- D1 = a: a re-run that fails is its own finding, and it gates -------------------------


def test_a_rerun_that_fails_in_a_full_clone_gates_as_rerun_failed(tmp_path: Path) -> None:
    root, first, tip = _repo(tmp_path)
    digest = _emit_range(root, "engine_commits", first, tip)

    def break_endpoint(block: dict[str, Any]) -> None:
        block["procedure"]["argv"][-1] = f"{NO_SUCH_SHA}..{tip}"

    _rewrite(root, digest, break_endpoint)
    _commit_all(root, "docs(logs): a history block whose range no longer resolves")
    rc, values, out = _guard(root)
    seen = f"values={values!r} rc={rc}\n{out}"
    got = (values.get("rerun_failed"), values.get("mismatch"))
    assert got == ("1", "0"), f"D1 a failed re-run is rerun_failed, not mismatch: {seen}"
    assert rc == 1, f"D1 rerun_failed gates: {seen}"


def test_a_block_outside_the_rerun_allowlist_is_never_executed(tmp_path: Path) -> None:
    """A re-sealed block can name any argv; the guard must not run what R7 would refuse."""
    control = tmp_path / "control"
    control.mkdir()
    subprocess.run(
        ["git", "init", "-q", "pwned-by-rerun"],  # noqa: S607
        cwd=control,
        capture_output=True,
        check=False,
    )
    assert (control / "pwned-by-rerun" / ".git").is_dir(), "instrument: the argv writes nothing"

    root, first, tip = _repo(tmp_path)
    digest = _emit_range(root, "engine_commits", first, tip)

    def name_a_writing_subcommand(block: dict[str, Any]) -> None:
        block["procedure"]["argv"] = ["git", "init", "pwned-by-rerun"]

    _rewrite(root, digest, name_a_writing_subcommand)
    _commit_all(root, "docs(logs): a re-sealed block naming a writing git subcommand")
    rc, values, out = _guard(root)
    seen = f"values={values!r} rc={rc}\n{out}"
    assert not (root / "pwned-by-rerun").exists(), f"D1 the argv was executed: {seen}"
    assert values.get("rerun_failed") == "1", f"D1 allowlist refusal counted: {seen}"


# --- D2 = b: an uncommitted edit to a declared path is stale, not a mismatch --------------


def test_a_staged_edit_to_a_declared_path_is_stale_not_mismatch(tmp_path: Path) -> None:
    """The pre-commit shape: the edit is in the index, not yet in ``HEAD``."""
    root, _, _ = _repo(tmp_path)
    _emit_template_tokens(root)
    _commit_all(root, "docs(logs): one block over the template")
    _append(root, TEMPLATE, "\n## A measure section\n")
    _git(root, "add", TEMPLATE)
    staged = _git(root, "diff", "--cached", "--name-only")
    assert staged == TEMPLATE, f"instrument: staged set is {staged!r}"

    rc, values, out = _guard(root)
    seen = f"values={values!r} rc={rc}\n{out}"
    got = (values.get("stale"), values.get("mismatch"))
    assert got == ("1", "0"), f"D2 a staged edit reads stale, never mismatch: {seen}"
    assert rc == 0, f"D2 an uncited stale block does not gate: {seen}"


# --- AC-10 + AC-20 (Step 2 half): the hook is wired and catalogued ------------------------


def test_the_hook_is_wired_and_catalogued() -> None:
    hook = PRECOMMIT.read_text(encoding="utf-8")
    catalogue = CATALOGUE.read_text(encoding="utf-8")
    wired = (hook.count("- id: measure-staleness\n"), hook.count("- id: no-such-hook"))
    assert wired == (1, 0), f"AC-10: hook_id_count post={wired[0]} (pre=0) control={wired[1]}"
    row = catalogue.count("| `measure-staleness` | `check_measure_staleness.py` |")
    control = catalogue.count("no-such-tool.py")
    assert (row, control) == (1, 0), f"AC-20: guard row post={row} (pre=0) control={control}"
