/* ============================================================
   Story-mode explainer — the ONE pinned data block (PLAN-0126 §3.2)

   Read by BOTH the browser (window.STORY_DATA, consumed by story.js) and CI
   (tests/api/test_story_drift.py extracts the JSON between the delimiter
   comments below and json.loads it) — the trace-kinds.js pattern
   (docs/conventions/ui.md §4).

   `expected.*` is PINNED, not authored: the drift test checks every value
   against the repo's real producers — the fleet ontology YAML, the
   governed_repair_approval procedure, sourcing.compute_three_quote, the
   DOA ladder and the seed. Edit a case, run the test, and it prints the
   value the real rule produces. The page evaluates no business rule.

   Strict JSON between the delimiters: double quotes, no comments, no
   trailing commas.
   ============================================================ */
(function () {
  'use strict';

  const STORY_DATA =
  /* STORY_DATA_JSON_BEGIN */
  {
    "ontology": {
      "object_types": ["Truck", "Vendor", "Depot", "OperationalEvent", "Alert", "RecommendedAction",
                       "AlertEventLink", "RepairCase", "RepairCaseQuote", "RepairCaseAcceptedQuote"],
      "link_types": [
        ["truck_at_depot", "Truck", "Depot"],
        ["event_for_truck", "OperationalEvent", "Truck"],
        ["event_at_depot", "OperationalEvent", "Depot"],
        ["action_addresses_alert", "RecommendedAction", "Alert"],
        ["action_target_truck", "RecommendedAction", "Truck"],
        ["alert_event_link_to_alert", "AlertEventLink", "Alert"],
        ["alert_event_link_to_event", "AlertEventLink", "OperationalEvent"]
      ],
      "undeclared_refs": [
        ["RepairCase", "Truck"],
        ["RepairCaseQuote", "RepairCase"],
        ["RepairCaseAcceptedQuote", "RepairCase"],
        ["RepairCaseAcceptedQuote", "RepairCaseQuote"]
      ]
    },
    "emitters": {
      "pydantic": "Pydantic",
      "orm": "ORM",
      "sql": "SQL DDL",
      "jsonschema": "JSON Schema",
      "mcp": "MCP tools",
      "typescript": "TypeScript",
      "context_pack": "context pack"
    },
    "procedure": {
      "id": "governed_repair_approval",
      "event_kind": "repair_quote_accepted",
      "steps": [
        {"id": "intake", "th": "อ่านใบเสนอราคาล่าสุด"},
        {"id": "judge", "th": "เทียบเพดานซ่อมของคันนี้"},
        {"id": "reshape", "th": "แปลงเป็นยอดใช้จ่าย"},
        {"id": "quote_gate", "th": "ด่านเทียบราคา"},
        {"id": "approve", "th": "ด่านอนุมัติตามวงเงิน"},
        {"id": "fulfill", "th": "ลงมือ"}
      ],
      "gates": {
        "quote_gate": {"kind": "rule_gate", "criterion": "three_quote"},
        "approve": {"kind": "doa_tier", "autonomy": "gated"}
      },
      "sod": {"distinct_steps": ["intake", "approve"]},
      "llm_assist_steps": ["approve"]
    },
    "rules": {
      "three_quote_threshold_thb": 30000,
      "min_distinct_vendors": 3,
      "minor_repair_ceiling_thb": 5001,
      "tiers": [
        {"min_amount": 0, "role": "ช่างใหญ่"},
        {"min_amount": 5001, "role": "ผจก.เดินรถ"},
        {"min_amount": 30001, "role": "เจ้าของกิจการ"}
      ]
    },
    "cases": [
      {"truck": "truck-01", "what": "เพลาขาด", "amount_thb": 48000, "distinct_vendors": 1, "sole_source": false,
       "illustrative": true,
       "expected": {"breach": true, "sourcing_pass": false, "basis": "quotes_required", "tier_role": "เจ้าของกิจการ", "outcome": "fail"}},
      {"truck": "truck-01", "what": "เพลาขาด", "amount_thb": 48000, "distinct_vendors": 3, "sole_source": false,
       "illustrative": false,
       "expected": {"breach": true, "sourcing_pass": true, "basis": "three_quotes", "tier_role": "เจ้าของกิจการ", "outcome": "approved"}},
      {"truck": "truck-03", "what": "เกียร์เสียงดัง", "amount_thb": 15000, "distinct_vendors": 1, "sole_source": false,
       "illustrative": false,
       "expected": {"breach": true, "sourcing_pass": true, "basis": "under_threshold", "tier_role": "ผจก.เดินรถ", "outcome": "approved"}}
    ]
  }
  /* STORY_DATA_JSON_END */
  ;

  window.STORY_DATA = STORY_DATA;
})();
