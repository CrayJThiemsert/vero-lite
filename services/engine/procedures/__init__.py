"""Governed Procedure engine (ADR-016; PLAN-0019).

The generic, vertical-agnostic engine that runs a vertical's *normal* operating
workflow as a governed, human-gated, multi-step Procedure — expanding the OCT
action layer from reactive-only ``anomaly→action`` to
``anomaly AND normally→action``.

Per-vertical CONFIG (``procedures.yaml`` + Agent defs) lives under
``verticals/<name>/``; this package is the ENGINE (ADR-016 D6 engine-vs-config
boundary; SD-A2 home ``services/engine/procedures/``).

Phase-1 surface (PLAN-0019 Part A): ``spec`` — the Procedure/Step/Agent spec
models + loader; ``runs`` — the durable PipelineRun/StepResult run records.
"""
