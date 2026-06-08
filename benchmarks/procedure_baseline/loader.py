"""Dataset loader for the procedure-baseline benchmark (PLAN-0019 B-β).

Pure YAML -> validated :class:`Dataset` models. No side effects, no network — the
loader is unit-tested offline. Uses ``ruamel.yaml`` ``typ="safe"`` (matching the
procedure-spec loader in ``services/engine/procedures/spec.py``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from benchmarks.procedure_baseline.schema import Dataset

DATASET_DIR = Path(__file__).parent / "dataset"
"""Default home of the authored ``<vertical>.yaml`` ground-truth files."""


def load_dataset(path: Path) -> Dataset:
    """Load + validate one vertical's dataset YAML into a :class:`Dataset`.

    Raises ``pydantic.ValidationError`` on a malformed item (a precise authoring
    error) and a ``ruamel.yaml`` error on unparseable YAML.
    """
    yaml = YAML(typ="safe")
    with path.open(encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.load(handle)
    return Dataset.model_validate(raw)


def load_all(dataset_dir: Path = DATASET_DIR) -> list[Dataset]:
    """Load every ``*.yaml`` dataset in ``dataset_dir``, sorted by filename.

    Sorted so a run iterates verticals deterministically (aquaculture, energy,
    supply_chain).
    """
    return [load_dataset(path) for path in sorted(dataset_dir.glob("*.yaml"))]
