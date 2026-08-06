"""Which arm a published route may run — the OI-1 pin, stated as a principle.

PLAN-0100 OI-1 (Cray's typed ruling, 2026-08-06 — option **(b)**, in PRINCIPLE
form):

    On the published profile, an LLM call the visitor did not ask for is not
    made. Any route whose LLM invocation is INVOLUNTARY — fired by page load,
    by boot, by a background sweep, or by any path the visitor did not
    initiate — runs the deterministic arm instead.

Why a principle rather than a one-route patch: ``GET /recommendations`` was
found (s207-R2, corrected s209) to fan out unauthenticated inference from
**Tab A, the default landing view** — before a visitor clicks anything. The
same shape can reappear on any future route, so the discriminator is stated
once, here, and consulted rather than re-derived per route.

What the principle does **not** bar: deterministic work of any richness. The
ADR-0030 economic (฿) facet is deterministic and never-raises, so it rides the
pinned path unchanged (Cray, same ruling). The pin is about the *LLM arm*, not
about how thin the record is.

Voluntary LLM routes are unaffected — ``POST /query``, the wedge's NL query,
stays ``assisted``: the visitor typed the input, so ADR-0035 D6's prompt-log
regime applies to it naturally and the rate cap bounds it. That is exactly the
asymmetry that made (b) cheaper than (a): D6's ``text`` field is defined as the
visitor's typed input verbatim, which an involuntary route has none of.
"""

from __future__ import annotations

from services.api.config import settings


def deterministic_arm_pinned(*, visitor_initiated: bool) -> bool:
    """True when this call must take the deterministic arm rather than the LLM.

    ``visitor_initiated`` is the caller's assertion that a visitor asked for
    this specific inference. It is keyword-only, and callers default it to
    ``False`` (see ``recommender.recommend``) so that a new caller which never
    thought about the question is **pinned** — the fail-closed direction.

    Reads ``settings.ui_profile`` (``dev`` | ``published``), which already ships
    and is already load-bearing (``main.py`` index rewrite, ``/meta``); no new
    settings seam is introduced.
    """
    return settings.ui_profile == "published" and not visitor_initiated
