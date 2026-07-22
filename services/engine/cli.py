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
from typing import cast

import typer

from services.engine import code_generator, ontology_validator, scaffold

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
