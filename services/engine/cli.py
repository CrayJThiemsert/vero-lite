"""vero-lite ontology engine CLI (Typer).

``validate`` calls ``ontology_validator.main``; ``generate`` calls
``code_generator.generate_all``. The Typer ``app`` object is the
entry point declared in ``pyproject.toml`` ``[project.scripts]
vero-lite`` (commit 7).
"""

from __future__ import annotations

import sys
from pathlib import Path

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
    sys.stderr.write(f"  registered: {'yes' if result.registered else 'no (main.py absent)'}\n")
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
