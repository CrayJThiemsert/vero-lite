"""Run a battery of probes and report what each one actually witnessed.

**The seam this package draws** (PLAN-0115 R-A). ``tools/probe_coverage.py``'s original
docstring anticipated "a session's battery imports :func:`enumerate_claims` and
:func:`render_report`" — a per-session battery *script*. Session 253 measured the cost of
that boundary: all four of its driver defects lived in the un-shipped half (mutate,
restore, classify, credit), and none of them is visible to the shipped half by
construction, because ``render_report`` sees claim keys and credit maps and never *how*
credit was earned. So the seam moves: the **machinery** ships here, and the **probe
definitions** — which mutation, which declared claim, which expected outcome — stay
per-session *data* fed to it.

**What the driver refuses to do**, each traced to a measured s253 defect:

1. It never credits from an exit code. Outcome comes from the junit failure record
   (:mod:`tools.probe_battery._outcome`), so a crash cannot masquerade as a RED.
2. A witnessed probe credits **exactly one** claim — the one it pre-declared. A run stops
   at the first failing assertion, so one mutation can only ever witness one claim.
3. Claims are addressed **only** by :attr:`~tools.probe_coverage.Claim.stable_key`. There
   is no alternate keying path in this API, because s253 imported the object carrying
   ``stable_key`` and then hand-rolled a colliding key beside it.
4. Every run ends in :func:`~tools.probe_coverage.render_report`, and the one self-check
   the driver prints is computed from **pre-filter** inputs — see :func:`_overlaps`.

**This is an instrument, not a gate** (ADR-0038 D2-C1 refused a mechanical gate). It
automates the mechanics of witnessing; the verdict's authority stays with the review that
reads the report. It is deliberately not wired into CI or pre-commit — batteries mutate
real source files, so they stay agent/human-invoked.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from pathlib import Path
from types import FrameType
from xml.etree.ElementTree import ParseError

from tools.probe_battery._lock import LockHandle, ping_telegram
from tools.probe_battery._outcome import (
    CREDITING_OUTCOMES,
    Classification,
    Outcome,
    classify,
    parse_junit,
)
from tools.probe_battery._snapshot import (
    MutationError,
    RunStore,
    refuse_if_unrestored,
    state_root,
)
from tools.probe_coverage import Claim, enumerate_claims, render_report

#: Printed verbatim when every probe hit its declared outcome, coverage is complete, and
#: no claim is both probed and exempted. Greppable — an echoed exit code is corruptible.
VERDICT_PASS = "PROBE-BATTERY: PASS"  # noqa: S105 — a verdict token, not a credential

#: Printed verbatim otherwise. A battery that prints this has told you something true.
VERDICT_FAIL = "PROBE-BATTERY: FAIL"

DEFAULT_TIMEOUT_S = 600

#: What :func:`signal.signal` accepts back when we reinstate the previous disposition.
_SignalHandler = Callable[[int, FrameType | None], object] | int | signal.Handlers | None


class BatteryDefinitionError(ValueError):
    """The battery is not runnable as written — raised **before** anything is mutated."""


class BatteryInterruptedError(RuntimeError):
    """A termination signal arrived mid-battery.

    Raised *from the signal handler* on purpose: Python's default SIGTERM disposition
    kills the process outright and runs no ``finally``, so a battery interrupted that way
    would leave every mutation on disk. Turning the signal into an exception hands control
    back to the restore path — and, because :func:`subprocess.run` kills its child on any
    exception out of ``communicate()``, it takes the running pytest down with it instead
    of orphaning one.
    """


class _DeferredInterrupts:
    """Holds a termination signal for the length of one spawn, instead of raising it.

    **The window this closes.** :class:`subprocess.Popen` forks *and* execs inside its
    ``__init__``. A SIGTERM handler that raises can therefore fire after the child is
    already running but before the assignment to ``proc`` completes — leaving a live pytest
    that no ``except`` clause can reach, because the name is still unbound. Measured
    2026-08-31 (session 265) under single-CPU contention: 4 of 6 signals landed at
    ``subprocess.py:_execute_child``, and every one of those orphaned a pytest that then ran
    its body to completion. The 2 that landed inside ``communicate`` were handled correctly,
    which is why the hole only ever surfaced as a flaky guard on a loaded runner.

    **Why not :func:`signal.pthread_sigmask`**, which is the textbook answer: a child forked
    while SIGTERM is blocked *inherits the block*. Measured the same day — the child's
    ``/proc/<pid>/status`` reported ``SigBlk: 0x4000``. That would leave every pytest
    subprocess immune to the SIGTERM :func:`reap_child` sends and to the ``pkill`` the
    scenario suite cleans up with. Deferring in Python touches no process mask, so the child
    inherits nothing.

    Single-threaded by construction: CPython runs signal handlers on the main thread, which
    is the thread ``run_battery`` runs on.
    """

    def __init__(self) -> None:
        self._deferring = False
        self._pending: int | None = None

    def defer(self) -> None:
        """Begin holding SIGTERM/SIGINT rather than raising them."""
        self._deferring = True

    def record(self, signum: int) -> bool:
        """Handler hook. Returns whether the signal was held rather than raised."""
        if not self._deferring:
            return False
        if self._pending is None:  # the first arrival is the one reported
            self._pending = signum
        return True

    def stand_down(self) -> int | None:
        """Stop deferring and hand back the held signal, if any, WITHOUT raising.

        The cleanup path needs this: raising out of a ``finally`` would displace whatever
        exception is already unwinding.
        """
        self._deferring = False
        pending, self._pending = self._pending, None
        return pending

    def resume(self) -> None:
        """Stop deferring, and raise the signal that arrived while we were."""
        pending = self.stand_down()
        if pending is not None:
            raise BatteryInterruptedError(
                f"received {signal.Signals(pending).name} during the probe spawn"
            )


@contextmanager
def _terminating_signals() -> Iterator[_DeferredInterrupts]:
    """Make SIGTERM/SIGINT raise, for the duration of the battery **and its restore**.

    Handlers stay installed across the restore deliberately: a second signal arriving
    while the tree is half-restored should raise into the same recovery path, not kill the
    process at the worst possible moment. Best-effort, per the repo's daemon precedent — a
    non-main thread cannot install handlers, and the battery is still correct there
    because ``try/finally`` covers every non-signal exit.
    """
    interrupts = _DeferredInterrupts()
    installed: list[tuple[int, _SignalHandler]] = []

    def _raise(signum: int, _frame: FrameType | None) -> None:
        if interrupts.record(signum):
            return
        raise BatteryInterruptedError(f"received {signal.Signals(signum).name} mid-battery")

    for sig in (signal.SIGTERM, signal.SIGINT):
        with suppress(ValueError, OSError, AttributeError):
            installed.append((sig, signal.signal(sig, _raise)))
    try:
        yield interrupts
    finally:
        for restored_sig, previous in installed:
            with suppress(ValueError, OSError):
                signal.signal(restored_sig, previous)


@dataclass(frozen=True)
class Probe:
    """One mutation, and the single claim it predicts will redden.

    ``expect_claim`` is a pre-committed read: it is checked against what actually failed,
    and a probe that reddens something else credits nothing. Crediting the
    accidentally-hit claim would let the result rewrite the prediction, which is the
    whole failure mode a pre-committed read exists to prevent.
    """

    name: str
    subject: Path
    old: str
    new: str
    node_id: str
    expect_claim: str
    expect: Outcome = Outcome.WITNESSED
    note: str = ""

    @classmethod
    def from_json(cls, data: Mapping[str, object]) -> Probe:
        missing = [
            k for k in ("name", "subject", "old", "new", "node_id", "expect_claim") if k not in data
        ]
        if missing:
            raise BatteryDefinitionError(f"probe is missing required field(s): {missing}")
        return cls(
            name=str(data["name"]),
            subject=Path(str(data["subject"])),
            old=str(data["old"]),
            new=str(data["new"]),
            node_id=str(data["node_id"]),
            expect_claim=str(data["expect_claim"]),
            expect=Outcome(str(data.get("expect", Outcome.WITNESSED.value))),
            note=str(data.get("note", "")),
        )


@dataclass(frozen=True)
class Battery:
    """The per-session data: which modules' claims count, which probes, which exemptions.

    ``exemptions`` maps a ``stable_key`` to the written reason no probe can reach it —
    #0047's rule that an exemption without a reason is how a coverage check rots into
    agreement with itself.
    """

    claim_sources: tuple[Path, ...]
    probes: tuple[Probe, ...]
    exemptions: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: Mapping[str, object], base: Path | None = None) -> Battery:
        raw_sources = data.get("claim_sources")
        if not isinstance(raw_sources, list) or not raw_sources:
            raise BatteryDefinitionError("`claim_sources` must be a non-empty list of paths")
        raw_probes = data.get("probes")
        if not isinstance(raw_probes, list) or not raw_probes:
            raise BatteryDefinitionError("`probes` must be a non-empty list")
        root = base or Path()
        exemptions = data.get("exemptions") or {}
        if not isinstance(exemptions, dict):
            raise BatteryDefinitionError("`exemptions` must be a mapping of key -> reason")
        return cls(
            claim_sources=tuple(root / str(p) for p in raw_sources),
            probes=tuple(Probe.from_json(p) for p in raw_probes if isinstance(p, dict)),
            exemptions={str(k): str(v) for k, v in exemptions.items()},
        )


@dataclass(frozen=True)
class ProbeResult:
    """What one probe did, and whether that is what it said it would do."""

    probe: Probe
    classification: Classification
    credited: str | None

    @property
    def passed(self) -> bool:
        return self.classification.outcome == self.probe.expect


@dataclass(frozen=True)
class BatteryResult:
    results: tuple[ProbeResult, ...]
    report: str
    passed: bool
    overlaps: tuple[str, ...]
    credited: Mapping[str, str]


#: A runner turns a probe into junit XML text (``None`` = pytest produced no report).
Runner = Callable[[Probe, Path, int], str | None]


def _index_claims(battery: Battery) -> dict[str, tuple[Claim, Path]]:
    """Map every claim's ``stable_key`` to the claim and the file it came from.

    Refuses on a cross-module key collision. ``stable_key`` is ``owner|source|#n`` and
    ``occurrence`` is stamped *within* one module, so two modules that share a test name
    and an assertion text would share a key — and a coverage report built on it would
    call both covered when only one was ever witnessed. That is the exact coverage lie
    ``stable_key`` was introduced to prevent, so it fails loudly rather than at review.
    """
    index: dict[str, tuple[Claim, Path]] = {}
    for source in battery.claim_sources:
        for claim in enumerate_claims(source):
            key = claim.stable_key
            if key in index:
                other = index[key][1]
                raise BatteryDefinitionError(
                    f"claim key {key!r} occurs in both {other} and {source}. Cross-module "
                    f"keys collide because `occurrence` is stamped per module — run these "
                    f"modules as separate batteries."
                )
            index[key] = (claim, source)
    return index


def _validate(battery: Battery, index: Mapping[str, tuple[Claim, Path]]) -> None:
    """Everything checkable before the first mutation is checked before the first mutation.

    A battery that mutates the tree and *then* discovers it cannot verify its own
    prediction has already spent the risk for nothing.
    """
    unknown = sorted({p.expect_claim for p in battery.probes} - set(index))
    if unknown:
        raise BatteryDefinitionError(
            f"{len(unknown)} probe(s) declare a claim that does not exist in the claim "
            f"sources: {unknown}. Run `python -m tools.probe_coverage <module>` to list "
            f"the real keys — a battery cannot check a prediction it cannot address."
        )
    duplicates = sorted(
        {p.name for p in battery.probes if [q.name for q in battery.probes].count(p.name) > 1}
    )
    if duplicates:
        raise BatteryDefinitionError(f"probe names must be unique; repeated: {duplicates}")


def _overlaps(battery: Battery) -> tuple[str, ...]:
    """Claims that are both **declared by a probe** and exempted — a contradiction.

    🔴 **This is the s253 tautology, repaired.** That driver intersected the exemption set
    with a credit set *from which exempted keys had already been filtered*: empty by
    construction, printed as live evidence. The repair is the input, not the operator —
    the left side here is what the battery **declared** it would credit, before any
    filtering, so the intersection can actually be non-empty.

    An exemption asserts no probe can reach the claim; a probe asserts it will. Both
    cannot be true, and whichever is wrong, the coverage number is wrong with it.
    """
    declared = {p.expect_claim for p in battery.probes}
    return tuple(sorted(declared & set(battery.exemptions)))


def _child_env() -> dict[str, str]:
    """The probe subprocess's environment, with bytecode writing off.

    The second half of the stale-``.pyc`` defence (the first is
    :func:`~tools.probe_battery._snapshot.invalidate_bytecode`). Deleting the cache handles
    bytecode that already exists; this stops each probe run from leaving a fresh ``.pyc``
    that the *next* same-size mutation could be judged against. Belt and braces on purpose —
    the failure it prevents is a silent false GREEN, which no other check would catch.
    """
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _make_pytest_runner(store: RunStore, interrupts: _DeferredInterrupts) -> Runner:
    """The real runner, bound to the run's manifest so the child pid is recorded.

    Returns ``None`` when pytest produced no report at all — it failed to start, or it was
    killed at the timeout. Both mean "there is no failure record to read", which the
    classifier reports as ``SETUP/COLLECT-ERROR`` with the cause named.

    ``Popen`` rather than :func:`subprocess.run` for two reasons: the pid must be published
    to the manifest **while the child runs** (so a SIGKILLed driver leaves a reapable
    trail), and the kill-on-any-exception path is spelled out rather than inherited — it is
    what stops a SIGTERM to the driver from orphaning a running pytest.
    """

    def _run(probe: Probe, project_root: Path, timeout_s: int) -> str | None:
        with tempfile.TemporaryDirectory() as td:
            xml = Path(td) / "junit.xml"
            argv = [
                sys.executable,
                "-m",
                "pytest",
                probe.node_id,
                f"--junitxml={xml}",
                "-p",
                "no:cacheprovider",
                "-q",
            ]
            proc: subprocess.Popen[bytes] | None = None
            # The spawn runs with signals DEFERRED — see _DeferredInterrupts. `Popen`
            # forks and execs inside `__init__`, so a handler that raises here would
            # abandon a child that `proc` does not yet name.
            interrupts.defer()
            try:
                proc = subprocess.Popen(  # noqa: S603 — fixed argv from the battery
                    argv,
                    cwd=str(project_root),
                    env=_child_env(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                store.set_child(proc.pid, " ".join(argv))
                # Deferral ends HERE, inside the try — the first point at which the
                # handlers below can kill what was just spawned. Ending it any earlier
                # reopens the window by exactly the distance to the `try`.
                interrupts.resume()
                proc.communicate(timeout=timeout_s)
            except subprocess.TimeoutExpired:
                if proc is not None:
                    proc.kill()
                    proc.communicate()
                return None
            except BaseException:
                # Includes BatteryInterruptedError raised out of the SIGTERM handler. The
                # child is holding the mutated tree; leaving it running is the orphan.
                if proc is not None:
                    proc.kill()
                    proc.communicate()
                raise
            finally:
                # Never leave the handler deferring: a spawn that failed for a non-signal
                # reason would otherwise swallow every later signal. Does not raise, so it
                # cannot displace an exception already in flight.
                interrupts.stand_down()
                store.clear_child()
            if not xml.exists():
                return None
            return xml.read_text(encoding="utf-8")

    return _run


def _classify_probe(
    probe: Probe,
    index: Mapping[str, tuple[Claim, Path]],
    project_root: Path,
    xml_text: str | None,
    timeout_s: int,
) -> Classification:
    if xml_text is None:
        return Classification(
            Outcome.SETUP_ERROR,
            f"pytest produced no junit report for {probe.node_id!r} — it failed to start, "
            f"or it was killed at the {timeout_s}s timeout. There is no failure record to "
            f"read, so nothing is witnessed.",
        )
    try:
        cases = parse_junit(xml_text)
    except ParseError as exc:
        return Classification(
            Outcome.SETUP_ERROR, f"the junit report for {probe.node_id!r} is unparsable: {exc}"
        )
    claim, claim_path = _resolve_declared(probe, index)
    return classify(cases, claim, claim_path, project_root)


def _resolve_declared(probe: Probe, index: Mapping[str, tuple[Claim, Path]]) -> tuple[Claim, Path]:
    """Re-read the declared claim's CURRENT line, from the tree as the probe left it.

    🔴 **A probe that mutates the file its own claim lives in shifts that claim's line.**
    Measured 2026-08-25: a mutation replacing three lines with one moved every claim below
    it up by two, so the failure reported at line 101 was matched against a claim indexed
    at 103 and the run was rejected as a MISFIRE — the right refusal on the wrong grounds.
    That case is not exotic: it is exactly what happens when the thing under test is a
    guard living in its own test module.

    The fix was already in the design and merely unused here. ``stable_key`` is
    ``owner|source|#occurrence`` — **line-independent by construction**, precisely so an
    edit above a claim cannot re-point it. Classification runs while the mutation is still
    on disk, so re-enumerating and looking the key up again yields the line the failure
    record will actually name.

    Falls back to the pre-run claim when the key no longer resolves — a mutation that
    rewrote the declared assertion's own text. That is a probe whose prediction can no
    longer be checked, and it will be reported as a MISFIRE rather than silently credited.
    """
    claim, claim_path = index[probe.expect_claim]
    try:
        live = {c.stable_key: c for c in enumerate_claims(claim_path)}
    except (OSError, SyntaxError):
        return claim, claim_path
    return live.get(probe.expect_claim, claim), claim_path


def _run_one(
    probe: Probe,
    index: Mapping[str, tuple[Claim, Path]],
    store: RunStore,
    project_root: Path,
    timeout_s: int,
    runner: Runner,
) -> ProbeResult:
    """Mutate, run, classify, and put the subject back — in that order, always."""
    subject = probe.subject if probe.subject.is_absolute() else project_root / probe.subject
    try:
        store.apply(subject, probe.old, probe.new)
    except (MutationError, OSError) as exc:
        return ProbeResult(probe, Classification(Outcome.MUTATION_ERROR, str(exc)), None)
    try:
        classification = _classify_probe(
            probe, index, project_root, runner(probe, project_root, timeout_s), timeout_s
        )
    finally:
        # Per-probe restore: without it, probe N+1 runs against N's mutation and every
        # outcome after the first is about a tree nobody declared.
        store.restore(subject)
    credited = probe.expect_claim if classification.outcome in CREDITING_OUTCOMES else None
    return ProbeResult(probe, classification, credited)


def run_battery(
    battery: Battery,
    *,
    project_root: Path,
    state_base: Path | None = None,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    runner: Runner | None = None,
    echo: bool = True,
) -> BatteryResult:
    """Run every probe, restore the tree, and render the report — in every exit path.

    ``runner`` is injectable so the driver's own orchestration (crediting, per-probe
    restore, the overlap check) can be exercised without spawning one pytest per case.
    The real seam — driver → real pytest → real junit → real report — is driven by
    ``tests/tools/test_probe_battery_scenario.py`` on a self-contained fixture project,
    per CLAUDE.md §8's scenario rule.
    """
    base = state_base if state_base is not None else state_root(project_root)
    refuse_if_unrestored(base)

    index = _index_claims(battery)
    _validate(battery, index)

    store = RunStore.begin(project_root, base)
    results: list[ProbeResult] = []
    result: BatteryResult
    # Acquired BEFORE the first mutation and released only after the verified restore, so
    # the Axis-B goal gate never sees a half-broken tree (PLAN-0115 Step 2).
    lock = LockHandle.acquire(project_root, store.manifest.run_id, store.manifest.head_sha)
    ping_telegram(
        project_root,
        "lock_acquired",
        f"battery {store.manifest.run_id} started — the Axis-B goal gate will stand down "
        f"while it runs. {len(battery.probes)} probe(s), head={store.manifest.head_sha[:8]}",
    )
    with _terminating_signals() as interrupts:
        run = runner if runner is not None else _make_pytest_runner(store, interrupts)
        try:
            for probe in battery.probes:
                results.append(_run_one(probe, index, store, project_root, timeout_s, run))
                store.heartbeat()
                lock.heartbeat()
        finally:
            # Both halves belong here. The restore is the safety obligation; the report is
            # AC-6 — a battery must not be able to end without one, including the runs
            # that end by exception, which are exactly the runs whose partial results
            # matter most.
            store.restore_all()
            # Released only after restore_all: the gate must stay stood down until the
            # tree is actually back, not merely until the last probe finished.
            deferred = lock.release()
            if deferred:
                ping_telegram(
                    project_root,
                    "lock_released",
                    f"battery {store.manifest.run_id} finished — tree restored, gate live "
                    f"again. It stood down for {deferred} Stop event(s).",
                )
            result = _finalize(battery, index, tuple(results), store.manifest.run_id, echo)
        return result


def _finalize(
    battery: Battery,
    index: Mapping[str, tuple[Claim, Path]],
    results: tuple[ProbeResult, ...],
    run_id: str,
    echo: bool,
) -> BatteryResult:
    credited = {r.probe.expect_claim: r.probe.name for r in results if r.credited is not None}
    overlaps = _overlaps(battery)
    claims = [claim for claim, _ in index.values()]
    coverage, complete = render_report(
        claims, credited, battery.exemptions, key_of=lambda c: c.stable_key
    )
    passed = complete and not overlaps and all(r.passed for r in results)
    report = _render(battery, results, coverage, overlaps, run_id, passed)
    if echo:
        # AC-6: the verdict is *printed*, not merely returned. A battery that dies
        # mid-run propagates its exception — and the caller's `except` is exactly where a
        # returned-but-never-read report goes missing. Printing from the one place that
        # always runs is what makes "a battery cannot end without a report" true.
        print(report)
    return BatteryResult(
        results=results, report=report, passed=passed, overlaps=overlaps, credited=credited
    )


def _render(
    battery: Battery,
    results: tuple[ProbeResult, ...],
    coverage: str,
    overlaps: tuple[str, ...],
    run_id: str,
    passed: bool,
) -> str:
    lines: list[str] = []
    lines.append("=" * 78)
    lines.append("PROBE BATTERY (PLAN-0115 Step 1 · ADR-0038 C6 form (c))")
    lines.append("=" * 78)
    lines.append(
        f"run: {run_id}   probes: {len(results)}/{len(battery.probes)} run   "
        f"claim sources: {len(battery.claim_sources)}"
    )
    lines.append("")
    lines.append(f"-- probe outcomes ({len(results)}) " + "-" * 44)
    for res in results:
        mark = "✅" if res.passed else "🔴"
        expectation = (
            "" if res.probe.expect is Outcome.WITNESSED else f"  (declared {res.probe.expect})"
        )
        lines.append(f"  {mark} {res.probe.name}  {res.classification.outcome}{expectation}")
        lines.append(f"      claim : {res.probe.expect_claim}")
        lines.append(f"      node  : {res.probe.node_id}")
        # The RED's text, carried rather than discarded — C6's legibility conjunct is
        # only satisfiable by a reader who can see what broke.
        lines.append(f"      why   : {res.classification.reason}")
        if res.probe.note:
            lines.append(f"      note  : {res.probe.note}")

    if overlaps:
        lines.append("")
        lines.append(f"-- 🔴 probed AND exempted ({len(overlaps)}) " + "-" * 38)
        lines.append("   An exemption says no probe can reach the claim; a probe says it will.")
        lines.append("   Computed from the PRE-filter declared set, so this can be non-empty.")
        for key in overlaps:
            probes = ", ".join(p.name for p in battery.probes if p.expect_claim == key)
            lines.append(f"  {key}")
            lines.append(f"      probed by: {probes}")
            lines.append(f"      exemption: {battery.exemptions[key]!r}")

    lines.append("")
    lines.append(coverage)
    lines.append("")
    lines.append(VERDICT_PASS if passed else VERDICT_FAIL)
    return "\n".join(lines)
