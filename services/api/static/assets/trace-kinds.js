/* ============================================================
   OCT — the trace-kind label registry (PLAN-0080 Subject A).

   ONE source of truth for the reasoning-trace attribution channel, read by
   BOTH the browser (window.OCT_TRACE_KINDS, consumed by components.js
   traceKind()) and CI (tests/api/test_trace_kind_labels.py extracts the JSON
   block between the delimiter comments below and json.loads it).

   THE RULE: an engine-emitted trace kind MUST have an entry here. Adding a
   `"kind": "..."` (raw dict) or `ReasoningStep(kind="...")` emission without
   adding a row turns test_trace_kind_labels RED — the vocabulary cannot rot
   silently the way the substring sniff this file replaces did (14 of 16
   procedure-engine kinds rendered as an unattributed neutral badge, and 2
   matched the WRONG colour by accident).

   TWO AXES, TWO CHANNELS (PLAN-0080 L-4, Cray-ratified):
     - `cls`   = MECHANISM/severity — the existing theme.css semantics.
                 The demo's current look does not shift.
     - `actor` = WHO/WHAT produced the step — carried by a small glyph, never
                 by colour. Closed set: "human" | "llm" | "engine".

   An unmapped kind renders its raw token in the `.badge.unmapped` style with
   NO glyph and data-actor="unknown" — an unknown kind has no known actor, and
   defaulting to a machine glyph would assert an attribution we do not have.

   NOT the same field as definition-side `Step.kind` (services/engine/
   procedures/spec.py:54-61), which IS hashed into the governance/config pin.
   Trace-entry `kind` feeds no hash. Do not conflate them.
   ============================================================ */
(function () {
  'use strict';

  const TRACE_KINDS =
  /* TRACE_KINDS_JSON_BEGIN */
  {
    "gate_principal_recorded": { "label": "Human resolved the gate", "cls": "s-warn", "actor": "human" },
    "action_executed": { "label": "Human-approved — action executed", "cls": "s-ok", "actor": "human" },
    "action_rejected": { "label": "Human rejected the action", "cls": "s-neutral", "actor": "human" },
    "action_proposed": { "label": "Action proposed — awaiting human", "cls": "s-neutral", "actor": "engine" },
    "llm_inference": { "label": "LLM inference", "cls": "s-info", "actor": "llm" },
    "ontology_query": { "label": "Ontology query (deterministic)", "cls": "s-ok", "actor": "engine" },
    "read_provenance": { "label": "Read from ontology (deterministic)", "cls": "s-ok", "actor": "engine" },
    "read_passthrough": { "label": "Read — passthrough (deterministic)", "cls": "s-ok", "actor": "engine" },
    "query": { "label": "Intake — seeded read (deterministic)", "cls": "s-ok", "actor": "engine" },
    "join_pipeline": { "label": "Join pipeline (deterministic)", "cls": "s-ok", "actor": "engine" },
    "entity_resolution": { "label": "Entity resolution (deterministic)", "cls": "s-ok", "actor": "engine" },
    "rule_check": { "label": "Rule check (deterministic)", "cls": "s-warn", "actor": "engine" },
    "rule_gate_evaluated": { "label": "Rule gate evaluated (deterministic)", "cls": "s-warn", "actor": "engine" },
    "scored_rule_selected": { "label": "Scored rule selected (deterministic)", "cls": "s-warn", "actor": "engine" },
    "tier_authority": { "label": "Authority-tier check (deterministic)", "cls": "s-warn", "actor": "engine" },
    "doa_tier_resolved": { "label": "DOA tier resolved (deterministic)", "cls": "s-warn", "actor": "engine" },
    "severity_tier_resolved": { "label": "Severity tier resolved (deterministic)", "cls": "s-warn", "actor": "engine" },
    "verdict_computed": { "label": "Verdict computed (deterministic)", "cls": "s-warn", "actor": "engine" },
    "transform_provenance": { "label": "Deterministic transform", "cls": "s-neutral", "actor": "engine" },
    "economic_impact": { "label": "Economic-impact estimate (deterministic)", "cls": "s-neutral", "actor": "engine" },
    "action_verification": { "label": "Action verification (deterministic)", "cls": "s-warn", "actor": "engine" },
    "advisory_recommendation": { "label": "Advisory recommendation (shown, never routes)", "cls": "s-info", "actor": "llm" },
    "read_refused": { "label": "Read refused (governance)", "cls": "s-crit", "actor": "engine" },
    "error": { "label": "Step error", "cls": "s-crit", "actor": "engine" }
  }
  /* TRACE_KINDS_JSON_END */
  ;

  /* actor -> glyph name in components.js ICONS. Mutually distinct by
     requirement (PLAN-0080 Step 1); `person` is an in-repo SVG path, not an
     icon dependency. */
  const ACTOR_GLYPH = { human: 'person', llm: 'spark', engine: 'cpu' };

  window.OCT_TRACE_KINDS = TRACE_KINDS;
  window.OCT_TRACE_ACTOR_GLYPH = ACTOR_GLYPH;
})();
