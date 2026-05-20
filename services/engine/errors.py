"""Structured error records for the ontology engine.

Mirrors the ``tools/handoffs/_schema.py:ValidationError`` shape (frozen
dataclass; immutable, hashable) so handoff tooling and engine tooling
share a single diagnostic vocabulary (PLAN-003 §7 cross-tool
consistency rule).

The classes are data containers, not exceptions. The validator and
emitter pipelines collect them into lists and emit them to stderr; the
process boundary is the ``main(argv) -> int`` contract (Lesson #7 §3.1).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OntologyError:
    """Base record for any ontology engine violation.

    Fields are normalised across L1 (schema), L2 (semantic), and codegen
    emitter failures so a single render helper can format all three.
    """

    file: str
    object_type: str
    property: str
    yaml_line: int
    yaml_col: int
    message: str

    def render(self) -> str:
        """Format ``<file>:<line>:<col>: <ctx>: <message>`` for stderr."""
        location = f"{self.file}:{self.yaml_line}:{self.yaml_col}"
        if self.object_type and self.property:
            context = f"{self.object_type}.{self.property}"
        elif self.object_type:
            context = self.object_type
        else:
            context = ""
        if context:
            return f"{location}: {context}: {self.message}"
        return f"{location}: {self.message}"


@dataclass(frozen=True)
class SchemaValidationError(OntologyError):
    """L1 violation: input YAML does not conform to ADR-008 D2 grammar."""


@dataclass(frozen=True)
class SemanticValidationError(OntologyError):
    """L2 violation: cross-reference integrity failure within the YAML."""


@dataclass(frozen=True)
class EmitError(OntologyError):
    """Code generation failure for one of the five emitter outputs."""
