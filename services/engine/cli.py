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

from services.engine import code_generator, ontology_validator

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
