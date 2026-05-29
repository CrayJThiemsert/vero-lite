"""Bridge ↔ handoff-schema adapter for the ``validate_handoff_frontmatter`` tool.

PLAN-0012 Step 2b. Closes the Lesson #8 K-1 forcing fact for Cowork: Cowork
cannot run ``tools/handoffs/validate_handoff.py`` locally (UNC abort on
``mcp__workspace__bash``; §1/§3), so it has had no way to validate the
handoffs it authors. Exposing the committed handoff-frontmatter schema over
the bridge lets Cowork validate a handoff body **in-process** — no Code
broker, no filesystem write.

This module is a thin adapter: it calls
:func:`tools.handoffs._schema.parse_frontmatter_text` (the content-based
entry point, same validation logic the ``validate_handoff.py`` CLI uses) and
maps its typed findings onto the bridge wire shape. Validation is pure — no
state mutation, no I/O.

Surfaced-findings note (mirrors ``parse_frontmatter`` exactly): warnings are
included only when the block *also* has a blocking error; a block whose only
issue is advisory (e.g. an unknown field) parses cleanly and reports
``valid=True`` with no findings. ``valid`` reflects the presence of any
*error*-severity finding (``ValidationError.is_error()``), never a warning.
"""

from __future__ import annotations

from tools.handoffs._schema import parse_frontmatter_text


def validate_frontmatter_content(content: str) -> tuple[bool, list[dict[str, str]]]:
    """Validate a handoff frontmatter body.

    Returns ``(valid, findings)`` where ``valid`` is ``True`` iff there is no
    error-severity finding, and ``findings`` is the wire-shaped list of
    ``{"field", "value", "message", "severity"}`` dicts (empty when the block
    parsed cleanly).
    """
    result = parse_frontmatter_text(content)
    findings = result if isinstance(result, list) else []
    wire_findings = [
        {
            "field": f.field,
            "value": f.value,
            "message": f.message,
            "severity": f.severity.value,
        }
        for f in findings
    ]
    valid = not any(f.is_error() for f in findings)
    return valid, wire_findings
