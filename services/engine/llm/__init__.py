"""LLM reasoning-hook package (PLAN-0006 / ADR-010).

Houses the local-LLM-backed reasoning path that ``recommender.recommend()``
swaps in for the deterministic rule body (the "brain swap", ADR-010 D5):

- ``client``     — async Ollama ``/api/chat`` wrapper (ADR-002, MS-S1 MAX)
- ``prompt``     — system instruction + untrusted-event-text containment (IN-2)
- ``structured`` — constrained generation + validate-and-retry + semantic checks
- reasoning-trace assembly (ADR-010 D3)

The package is consumed by ``services/engine/recommender.py``; the ADR-007
D2 ``RecommendedAction`` envelope, the approval gate, persistence, and the
API router stay unchanged (ADR-010 D5).
"""
