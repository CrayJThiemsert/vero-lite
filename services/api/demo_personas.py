"""The published persona picker's offer set (PLAN-0103 Step 6).

ONE resolver, called from two places that must never disagree: ``main.py``'s
lifespan (so a misprovisioned deployment fails in the operator's terminal) and
the ``/meta`` route (so the browser is handed exactly what boot validated). A
second implementation on either side would be a two-carrier drift risk of the
kind this PLAN has already been bitten by three times.

It resolves through :func:`services.api.auth._principal_index` — the same
function ``get_current_principal`` uses to decide whether a ``person_id`` is a
member of the active vertical. Reusing it rather than re-reading the YAML is
load-bearing: it makes "the picker offers a persona that auth would refuse"
structurally impossible instead of merely tested-for.

Scope note: this module resolves and validates. It does NOT decide whether the
personas are served — that is the route's published-profile branch.
"""

from __future__ import annotations

from collections.abc import Mapping

from services.api.auth import _principal_index
from services.engine.ontology_meta import DemoPersonaMeta


class DemoPersonaError(RuntimeError):
    """A persona picker that could not be honoured as configured.

    A ``RuntimeError`` subclass so a boot caller can let it propagate and stop
    the process, which is the intended handling — the alternative is a published
    demo that serves a picker whose logins fail, on the one system whose entire
    story is the approve beat.
    """


def resolve_demo_personas(
    vertical: str,
    persona_keys: Mapping[str, str],
) -> list[DemoPersonaMeta]:
    """Project configured persona keys onto the vertical's AUTHORED principals.

    Returns the personas in **authored order** — the order they appear in the
    vertical's ``procedures.yaml`` — rather than the order they happen to occupy
    in the env JSON. For fleet that is the authority ladder read bottom-up
    (mechanic → manager → owner), which is the thing the three cards exist to
    show; an operator reordering a JSON object should not reorder the ladder a
    visitor sees.

    Empty ``persona_keys`` returns an empty list rather than raising: that is the
    correct configuration for every system except fleet, not an error.

    Raises:
        DemoPersonaError: personas are configured but the vertical authors no
            principals, or a configured ``person_id`` is not among them.
    """
    if not persona_keys:
        return []

    index = _principal_index(vertical)
    if not index:
        raise DemoPersonaError(
            f"UI_DEMO_PERSONA_KEYS is provisioned but the {vertical!r} vertical "
            "authors no principals, so every persona offered would resolve to "
            "nobody. The picker is a projection of an authored ladder — it "
            "cannot invent one."
        )

    unknown = sorted(set(persona_keys) - set(index))
    if unknown:
        raise DemoPersonaError(
            f"UI_DEMO_PERSONA_KEYS names person_ids the {vertical!r} vertical "
            f"does not author: {unknown}. Authored principals are "
            f"{sorted(index)}. A persona the ladder does not contain would be "
            "refused by the same membership check that guards every gate "
            "(auth.py's 403), so offering it as a card is offering a dead "
            "control on a public surface."
        )

    # Authored order, not env order: `index` is built from `procedures.principals`
    # in file order and dicts preserve insertion order.
    return [
        DemoPersonaMeta(
            person_id=person_id,
            name=index[person_id].name,
            # `Person.roles` is a frozenset — unordered. Sorted here so the wire
            # shape is deterministic across processes; an unsorted set would make
            # the response differ run to run and the tests flaky for a reason
            # that has nothing to do with the behaviour under test.
            roles=sorted(index[person_id].roles),
            key=persona_keys[person_id],
        )
        for person_id in index
        if person_id in persona_keys
    ]
