/* ============================================================
   Gate fixture — a RECORDED generated draft for the edit-mode
   authoring gate (PLAN-0040 Phase C / ADR-0024 D8; OQ-D D1).

   The edit-mode of View F renders a GENERATED procedure DRAFT behind the
   human-review gate. That draft is host-state to produce live (MS-S1 `gpt-oss:20b`,
   CLAUDE.md §8), so v1 renders it OFFLINE from this recorded fixture (OQ-D D1: the
   gate render is exercised against a recorded-fixture draft; the live intake face
   is the deferred host-state surface).

   AUTHENTICITY: this mirrors the real pipeline output —
   `instantiate(AT1)` + `derive_governance_todo` + the GovernanceStub
   reasons/expectations are copied VERBATIM from
   services/engine/procedures/{archetypes/template.py, draft.py, generator/pipeline.py}.
   The prose `description` / facet notes stand in for an LLM draft (the only
   LLM-sourced strings; regeneratable live). Every governance VALUE is ABSENT —
   the schema-correct stub (OQ-C C1) — so this is a `load_procedures`-valid SKELETON
   that FAILS `validate_governance_complete` until a human authors the stubs (D6).

   SHAPE: identical to GET /procedures ({ verticals: [...] }) so view-procedures.js
   reuses its read-mode render path verbatim (LOCKED-8: no second renderer). The
   net-new keys are per-procedure `governance_todo` (the "YOU must author" worklist,
   keyed by step_id) and `governance_options` (the LEGAL authoring domains — the
   allowlist a human picks from, NOT a recommended value: guided authoring that
   never crosses D4).
   ============================================================ */
(function () {
  'use strict';
  window.OCT = window.OCT || {};

  // The legal authoring domains surfaced as guided controls (presentation only).
  // `handler` mirrors the energy vertical's REGISTERED handler vocabulary
  // (verticals/energy: action_handlers + the echo receipt) — the set a human picks
  // from, never a value the generator emits (D4).
  const governance_options = {
    direction: ['above', 'below'],          // spec.ThresholdDirection
    autonomy: ['gated', 'auto', 'manual'],  // spec.Autonomy (gated = the safe default)
    handler: ['restart', 'echo']            // energy registered action handlers
  };

  // One generated AT-1 skeleton (energy: transformer over-temperature → judge → restart).
  // Every H value (threshold / direction / watch_margin / handler / tiers / env_var)
  // is ABSENT — the unfilled stub the gate makes the human author.
  const procedure = {
    procedure_id: 'generated_procedure',
    archetype: 'AT-1',
    title: 'Transformer over-temperature → evaluate → restart',
    goal: '', // OQ-B B2: goal is human-authored in the elevated-scrutiny zone (not generated)
    run_by: 'author_agent',
    trigger: 'manual',
    terminal: 'act',
    steps: [
      {
        step_id: 'read',
        name: 'Read the signal',
        kind: 'query',
        description: 'Pull the latest temperature readings for the transformers under watch.',
        input: null,
        output: null,
        facet: {
          decision_condition: { gate_kind: 'none' },
          llm_assist: null,
          input: 'the transformer set under watch (advisory)',
          output: null,
          governance: null
        }
      },
      {
        step_id: 'judge',
        name: 'Judge against the band',
        kind: 'evaluate',
        description: 'Compare each reading against the transformer safe-operating band.',
        input: { from: 'read' },
        output: null,
        // threshold / direction / watch_margin: ABSENT stubs (H) — see governance_todo
        facet: {
          decision_condition: { gate_kind: 'in_file_band', band_source: 'in_file' },
          llm_assist: null,
          input: null,
          output: null,
          governance: null
        }
      },
      {
        step_id: 'act',
        name: 'Act on the breach set',
        kind: 'action',
        autonomy: 'gated', // the archetype posture — present, but a human CONFIRM obligation (finding #5)
        description: 'Restart the flagged transformer to bring it back within band.',
        input: { from: 'judge', where: { verdict: 'breach' } },
        output: null,
        // handler / tiers: ABSENT stubs (H) — see governance_todo
        facet: {
          decision_condition: { gate_kind: 'none' },
          llm_assist: 'draft the action proposal (advisory)',
          input: null,
          output: null,
          governance: null
        }
      }
    ],
    // the "YOU must author" worklist (GeneratedSkeleton.governance_todo), keyed by
    // step_id — reason + archetype_expectation copied verbatim from generator/pipeline.py.
    governance_todo: {
      judge: [
        {
          field: 'threshold',
          reason: 'the breach floor/ceiling is a deterministic band a human authors (D3)',
          archetype_expectation: 'judge expects an in_file band — author threshold + direction'
        },
        {
          field: 'direction',
          reason: 'the breach direction pairs with the human-authored threshold (D3)',
          archetype_expectation: 'judge expects an in_file band — author threshold + direction'
        }
      ],
      act: [
        {
          field: 'handler',
          reason: 'the action handler is a blast-radius binding a human authors (D3)',
          archetype_expectation: 'action expects a registered handler binding + an autonomy confirm'
        },
        {
          field: 'autonomy',
          reason: "confirm the action's autonomy posture (safe-default gated; D3)",
          archetype_expectation: 'action expects a registered handler binding + an autonomy confirm'
        }
      ]
    }
  };

  // The placeholder agent the human binds: run_by resolves so the skeleton loads,
  // but llm_model / autonomy_ceiling / allowed are unbound stubs (H, agent-side).
  const agent = {
    agent_id: 'author_agent',
    name: '<author: name + bind this agent>',
    llm_model: null,
    autonomy_ceiling: null,
    allowed: { step_kinds: [], action_handlers: [] }
  };

  // GET /procedures-shaped envelope: one vertical, one generated draft.
  window.OCT.GateFixture = {
    verticals: [
      {
        vertical: 'energy',
        namespace: 'energy',
        version: 0,
        agents: [agent],
        procedures: [procedure]
      }
    ],
    governance_options: governance_options
  };
})();
