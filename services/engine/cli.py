"""vero-lite ontology engine CLI (Typer).

``validate`` is wired against ``ontology_validator.main`` here
(commit 3); ``generate`` lands in commit 6. The Typer ``app`` object
is the entry point declared in ``pyproject.toml`` ``[project.scripts]
vero-lite`` (commit 7).
"""

from __future__ import annotations

import typer

from services.engine import ontology_validator

app = typer.Typer(help="vero-lite ontology engine CLI", no_args_is_help=True)


def _yaml_path(vertical: str) -> str:
    return f"verticals/{vertical}/ontology/{vertical}_v0.yaml"


@app.command()
def validate(vertical: str) -> None:
    """Validate ``verticals/<vertical>/ontology/<vertical>_v0.yaml`` (L1 + L2)."""
    code = ontology_validator.main([_yaml_path(vertical)])
    raise typer.Exit(code=code)


@app.command()
def generate(vertical: str) -> None:
    """Emit the five codegen artifacts under ``verticals/<vertical>/generated/``."""
    raise NotImplementedError("vero-lite generate is wired in PLAN-003 commit 6")
