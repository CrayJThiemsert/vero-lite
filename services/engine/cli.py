"""vero-lite ontology engine CLI (Typer).

``validate`` calls ``ontology_validator.main``; ``generate`` calls
``code_generator.generate_all``. The Typer ``app`` object is the
entry point declared in ``pyproject.toml`` ``[project.scripts]
vero-lite`` (commit 7).
"""

from __future__ import annotations

import asyncio
import importlib
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, cast

import typer

from services.engine import code_generator, ontology_validator, scaffold

if TYPE_CHECKING:  # import-time cost stays off every other command's path
    from services.engine.scaffolder.intake import IntakeRecord

app = typer.Typer(help="vero-lite ontology engine CLI", no_args_is_help=True)


def _yaml_path(vertical: str) -> str:
    return f"verticals/{vertical}/ontology/{vertical}_v0.yaml"


def _output_dir(vertical: str) -> Path:
    return Path(f"verticals/{vertical}/generated")


@app.command()
def validate(vertical: str) -> None:
    """Validate ``verticals/<vertical>/ontology/<vertical>_v0.yaml`` (L1 + L2)."""
    code = ontology_validator.main([_yaml_path(vertical)])
    raise typer.Exit(code=code)


@app.command()
def generate(vertical: str) -> None:
    """Emit the five codegen artifacts under ``verticals/<vertical>/generated/``.

    Validates the YAML first; refuses to emit if validation fails (so
    the operator never sees codegen output derived from a broken
    ontology).
    """
    yaml_path = _yaml_path(vertical)
    code = ontology_validator.main([yaml_path])
    if code != 0:
        raise typer.Exit(code=code)
    outputs = code_generator.generate_all(Path(yaml_path), _output_dir(vertical))
    for name, path in outputs.items():
        sys.stderr.write(f"  {name}: {path}\n")
    sys.stderr.write(f"OK: generated {len(outputs)} artifact(s) for vertical {vertical!r}\n")


@app.command()
def new_vertical(
    namespace: str,
    threshold: float = typer.Option(..., help="OCT_RECOMMEND_THRESHOLD — the breach threshold."),
    label: str = typer.Option(..., help="OCT_RECOMMEND_LABEL — short anomaly label."),
    recovery_value: float = typer.Option(
        ..., help="OCT_RECOVERY_VALUE — safe value after the corrective action."
    ),
    recovery_description: str = typer.Option(
        ..., help="OCT_RECOVERY_DESCRIPTION — the recovery reading's description."
    ),
    direction: str = typer.Option(
        "above", help="Breach direction: 'above' (overrun) or 'below' (crash)."
    ),
    unit: str = typer.Option("", help="Measurement unit for events (e.g. 'mg/L')."),
    problem: str = typer.Option("", help="Problem statement (for the README / future LLM)."),
    decision: str = typer.Option("", help="Corrective action (for the README / future LLM)."),
    force: bool = typer.Option(False, help="Overwrite existing scaffold files."),
    llm: bool = typer.Option(
        False, help="Draft synthetic.py via the MS-S1 LLM (falls back to deterministic)."
    ),
) -> None:
    """Scaffold a Tier-1 Mirror-demo vertical from its ontology (ADR-0015 D2).

    Stitches the BUILD steps around ``validate`` + ``generate``: a deterministic
    draft synthetic adapter, the templated boilerplate, and the registration
    code-mod. Requires the ontology at
    ``verticals/<namespace>/ontology/<namespace>_v0.yaml`` to exist first.
    """
    config = scaffold.RecommendConfig(
        threshold=threshold,
        direction=direction,
        label=label,
        unit=unit,
        recovery_value=recovery_value,
        recovery_description=recovery_description,
        problem=problem,
        decision=decision,
    )
    try:
        result = scaffold.scaffold_vertical(namespace, config, force=force, llm=llm)
    except scaffold.ScaffoldError as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        raise typer.Exit(code=1) from exc

    cwd = Path.cwd()
    for path in result.written:
        sys.stderr.write(f"  wrote: {path.relative_to(cwd)}\n")
    for name, path in result.generated.items():
        sys.stderr.write(f"  generated: {name}: {path}\n")
    discoverable = "yes (auto-registered at startup via import-scan)" if result.registered else "no"
    sys.stderr.write(f"  discoverable: {discoverable}\n")
    sys.stderr.write(
        f"OK: scaffolded vertical {namespace!r} "
        f"(Asset={result.roles.asset_type}, Site={result.roles.site_type}, "
        f"direction={direction})\n\n"
        "Next steps:\n"
        "  1. Review + enrich data_adapter/synthetic.py (draft — ADR-0015 D5).\n"
        "  2. Add the env block below to your local .env, then boot uvicorn:\n\n"
        f"{result.env_block}\n\n"
        "  3. Verify the map, NL query, and the breach -> recommend -> approve "
        "-> execute lifecycle.\n"
    )


def _emit_scaffold(record: IntakeRecord, namespace: str, root: Path) -> None:
    """Emit the vertical: ontology -> package -> procedures -> ceiling check -> wires.

    Split out of the command so the ORDER is readable in one screen, because the order
    is load-bearing rather than incidental: the governance-ceiling check runs after the
    procedures document exists (it needs the signature) but **before** any wire is
    written, so a stop leaves the four shared wire files untouched. A ceiling stop that
    had already code-modded ``services/api/main.py`` would be a stop in name only.

    Every write is uncommitted working-tree output (PLAN-0091: no git operations, ever);
    Code reviews and commits it via PR.
    """
    import tempfile

    from services.engine.scaffolder.ceiling import GovernanceCeilingError, check_ceiling
    from services.engine.scaffolder.ontology import (
        DomainPropertyError,
        OntologyEmissionError,
        emit_ontology,
        write_ontology,
    )
    from services.engine.scaffolder.package import write_package
    from services.engine.scaffolder.spine import emit_procedures, write_procedures
    from services.engine.scaffolder.wire import WireError, write_wires

    try:
        ontology_doc = emit_ontology(record)
    except OntologyEmissionError as exc:
        sys.stderr.write(
            "REFUSING TO EMIT — these judgment slots are unanswered or unconfirmed:\n"
            + "".join(f"  - {slot}\n" for slot in exc.open_slots)
            + "They are customer vocabulary calls; no default is safe, because a wrong "
            "default is indistinguishable from an answer once it is on disk.\n"
        )
        raise typer.Exit(code=3) from exc
    except DomainPropertyError as exc:
        sys.stderr.write(f"REFUSING TO EMIT — a domain column did not parse: {exc}\n")
        raise typer.Exit(code=3) from exc

    procedures_doc = emit_procedures(record, ontology_doc)
    procedure_id = next(iter(procedures_doc["procedures"]))

    # The designed-in ceiling: detect, STOP, and hand a human a pre-built argument.
    # The tool never clears a governance tripwire on its own.
    with tempfile.TemporaryDirectory() as scratch:
        try:
            check_ceiling(namespace, procedures_doc, repo_root=Path.cwd(), scratch=Path(scratch))
        except GovernanceCeilingError as exc:
            sys.stderr.write(exc.report.render() + "\n")
            raise typer.Exit(code=4) from exc

    written: list[Path] = [write_ontology(record, root)]
    written.extend(write_package(record, ontology_doc, root))
    written.append(write_procedures(record, ontology_doc, root))

    try:
        wires = write_wires(namespace, procedure_id, procedures_doc, root)
    except WireError as exc:
        sys.stderr.write(
            f"Package written, but wiring failed: {exc}\n"
            f"The package under verticals/{namespace}/ is intact; re-run the wiring once "
            f"the target files are present.\n"
        )
        raise typer.Exit(code=5) from exc

    sys.stderr.write(f"Wrote {len(written)} package files:\n")
    for path in written:
        sys.stderr.write(f"  {path}\n")
    sys.stderr.write(f"\nWired {len(wires)} shared files:\n")
    for rel in wires:
        sys.stderr.write(f"  {rel}\n")
    sys.stderr.write(
        f"\nAll output is UNCOMMITTED working-tree changes — review the diff before "
        f"committing. Procedure id: {procedure_id!r}\n"
    )


# Registered as `scaffold` but NOT named `scaffold` at module scope: that name is
# already bound to the `services.engine.scaffold` module imported above, which
# `new_vertical` calls into (`scaffold.RecommendConfig`). Shadowing it would break
# that command at runtime, which is why the command name is passed explicitly.
@app.command("scaffold")
def scaffold_from_narrative(
    namespace: str,
    narrative: Annotated[
        Path | None,
        typer.Option(help="Free-text customer narrative to derive the question queue from."),
    ] = None,
    intake: Annotated[
        Path | None,
        typer.Option(help="A typed IntakeRecord JSON (partially or fully answered)."),
    ] = None,
    plan_only: Annotated[
        bool,
        typer.Option(
            "--plan-only", help="Print the open question queue + file manifest; write nothing."
        ),
    ] = False,
) -> None:
    """Scaffold a vertical package from a customer narrative (PLAN-0091).

    Covers the seam ``new-vertical`` declares out of scope: it starts BEFORE the
    ontology exists. ``new-vertical`` stays the ADR-0015 D2 Tier-1 Mirror vehicle
    and is deliberately not overloaded.

    Refuses to touch an existing ``verticals/<namespace>/`` — there is no
    overwrite path in v1, so a mis-typed namespace cannot damage a shipped
    vertical. Performs no git operations, ever.
    """
    from services.engine.scaffolder.intake import (
        IntakeRecord,
        format_queue,
        open_questions,
        required_slots,
        unenforced_register,
    )

    # CWD-relative, like `validate` / `generate` (ADR-0015 D2). Deliberately no
    # --root flag: the emitters take an explicit root, but the COMMAND must resolve
    # the same way the floor it invokes does, and a root that could differ from the
    # CWD would split-brain against `check_ceiling`'s repo_root. Tests chdir into a
    # staged tree, which is the resolution rule the command actually runs under.
    root = Path(".")
    target = root / "verticals" / namespace
    if target.exists():
        sys.stderr.write(
            f"ERROR: {target}/ already exists — scaffold refuses to overwrite an existing "
            f"vertical (no overwrite path in v1). Choose a new namespace.\n"
        )
        raise typer.Exit(code=2)

    if intake is not None:
        record = IntakeRecord.model_validate_json(intake.read_text(encoding="utf-8"))
        # The emitters key every write off `record.namespace`, while the guard above
        # checks the ARGUMENT. Letting the two differ would route the write past the
        # refuse-to-overwrite guard entirely and land on whatever the file names —
        # potentially a shipped vertical. Refuse rather than silently pick a winner.
        if record.namespace != namespace:
            sys.stderr.write(
                f"ERROR: --intake declares namespace {record.namespace!r} but the argument "
                f"says {namespace!r}. They must match: the overwrite guard checks the "
                f"argument and every emitter writes to the record's namespace.\n"
            )
            raise typer.Exit(code=2)
    else:
        narrative_text = narrative.read_text(encoding="utf-8") if narrative is not None else ""
        record = IntakeRecord(namespace=namespace, narrative=narrative_text)

    checklist = required_slots()
    still_open = open_questions(record, checklist)

    sys.stderr.write(f"Scaffold plan for vertical {namespace!r}\n\n")
    sys.stderr.write(f"Open questions ({len(still_open)} of {len(checklist)} slots):\n")
    sys.stderr.write(format_queue(still_open) + "\n\n")

    register = unenforced_register(record, checklist)
    if register:
        sys.stderr.write(
            "Stated but NOT enforced (no schema field — these land in the README register):\n"
        )
        sys.stderr.write(format_queue(register) + "\n\n")

    if plan_only:
        sys.stderr.write("--plan-only: nothing written.\n")
        raise typer.Exit(code=0)

    _emit_scaffold(record, namespace, root)


# Per-vertical procedure-executor factory registration for the scheduler daemon (PLAN-0090 L3).
# MIRRORS ``_PROCEDURE_EXECUTOR_REGISTRARS`` in services/api/main.py rather than importing it:
# ``services/engine/`` must not depend on ``services/api/``, and importing the app would drag
# FastAPI into daemon startup. The two vertical sets are pinned EQUAL by
# ``tests/services/engine/test_cli_registrars.py`` (AC-4), so a 7th vertical wired into one and
# not the other goes RED instead of silently un-fireable. Module paths resolve LAZILY, so booting
# one vertical never imports another's harness — the main.py property this mirrors.
_PROCEDURE_EXECUTOR_REGISTRARS: dict[str, tuple[str, str]] = {
    "aquaculture": (
        "verticals.aquaculture.procedures_factory",
        "register_aquaculture_procedure_executors",
    ),
    "energy": (
        "verticals.energy.procedures_factory",
        "register_energy_procedure_executors",
    ),
    "procurement": (
        "verticals.procurement.hero_demo.run",
        "register_procurement_procedure_executors",
    ),
    "supply_chain": (
        "verticals.supply_chain.procedures_factory",
        "register_supply_chain_procedure_executors",
    ),
    "building_materials": (
        "verticals.building_materials.procedures_factory",
        "register_building_materials_procedure_executors",
    ),
    "fleet_maintenance": (
        "verticals.fleet_maintenance.procedures_factory",
        "register_fleet_maintenance_procedure_executors",
    ),
}


async def _register_executor_factory(vertical: str) -> None:
    """Register the vertical's procedure-executor factory (OQ-6: explicit, not auto-discovered).

    Without it the daemon does not merely fail to fire: :func:`_run_scheduler` asks the registry
    for the factory UNGUARDED, so an unregistered vertical raises ``RegistryError`` at STARTUP,
    before the daemon ever ticks. Until PLAN-0090 this dispatch was hardcoded to procurement,
    which is precisely the shape that failure took for the other five procedure-bearing verticals
    — recorded only by a docstring that had itself gone stale. The AC-4 set-equality test is the
    structural replacement for that docstring.

    Note: the vertical's action *handlers* are registered separately by ``discover_and_register``
    (see :func:`_run_scheduler`) — a fired run's action steps resolve their handlers via the
    registry, so the daemon must register both."""
    entry = _PROCEDURE_EXECUTOR_REGISTRARS.get(vertical)
    if entry is None:
        return
    module_name, attr = entry
    registrar = cast(
        "Callable[[], Awaitable[None]]",
        getattr(importlib.import_module(module_name), attr),
    )
    await registrar()


async def _run_scheduler(vertical: str, interval_seconds: float) -> None:
    from services.db.session import async_session
    from services.engine.discovery import discover_and_register
    from services.engine.procedures.scheduler_daemon import run_scheduler_daemon
    from services.engine.procedures.scheduler_wiring import build_resolver, sync_schedule_states
    from services.engine.procedures.spec import load_procedures
    from services.engine.registry import registry

    # Register adapters + action handlers (OQ-6) BEFORE firing — a fired run's action steps
    # (e.g. `source`/`emergency_source`) resolve their handler via the registry, so a daemon that
    # skipped this fails the run at its first action step (a StructuredOutputError:
    # "…not a registered handler"). Mirrors the API lifespan (services/api/main.py). Surfaced by
    # the PLAN-0055 Step 8 live-daemon smoke — the offline test masked it by registering handlers
    # explicitly.
    discover_and_register()
    spec = load_procedures(vertical)
    await _register_executor_factory(vertical)
    factory = registry.get_procedure_executors(vertical)
    async with async_session() as session:
        rows = await sync_schedule_states(session, spec)
    sys.stderr.write(
        f"OK: scheduler for vertical {vertical!r} — {len(rows)} schedule(s) registered "
        f"from spec; ticking every {interval_seconds:g}s. Ctrl-C / SIGTERM to stop.\n"
    )
    resolver = build_resolver(spec, factory)
    await run_scheduler_daemon(
        session_factory=async_session, resolve=resolver, interval_seconds=interval_seconds
    )


@app.command()
def scheduler(
    vertical: str = typer.Option(..., help="Vertical whose schedule-trigger procedures to run."),
    interval_seconds: float = typer.Option(
        60.0, help="Seconds between fire ticks (the daemon reads the wall clock each tick)."
    ),
) -> None:
    """Run the long-lived ``schedule``-trigger scheduler daemon for a vertical (PLAN-0055 Step 7).

    Loads the vertical spec, registers its procedure-executor factory, syncs the
    ``schedule_states`` table from the spec's ``schedule``-trigger procedures (the registration
    step), then runs the daemon with a graceful SIGTERM/SIGINT shutdown. A pure clock — no MS-S1
    dependency. See ``docs/runbooks/scheduler-daemon.md`` for the deploy posture.
    """
    asyncio.run(_run_scheduler(vertical, interval_seconds))
