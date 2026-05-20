"""vero-lite ontology engine CLI (Typer).

Commit 1 ships command stubs that raise ``NotImplementedError``;
commit 3 wires ``validate`` against ``ontology_validator.main`` and
commit 6 wires ``generate`` against ``code_generator.generate_all``.
The Typer ``app`` object is the entry point declared in
``pyproject.toml`` ``[project.scripts] vero-lite``.
"""

from __future__ import annotations

import typer

app = typer.Typer(help="vero-lite ontology engine CLI", no_args_is_help=True)


@app.command()
def validate(vertical: str) -> None:
    """Validate ``verticals/<vertical>/ontology/<vertical>_v0.yaml`` (L1 + L2)."""
    raise NotImplementedError("vero-lite validate is wired in PLAN-003 commit 3")


@app.command()
def generate(vertical: str) -> None:
    """Emit the five codegen artifacts under ``verticals/<vertical>/generated/``."""
    raise NotImplementedError("vero-lite generate is wired in PLAN-003 commit 6")
