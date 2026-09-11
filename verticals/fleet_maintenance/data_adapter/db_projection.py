"""Which fleet ontology types are served from the database, and which columns never are.

PLAN-0109 AC-10's single source. Three consumers read this module and no other copy of
its content exists anywhere:

* the scaffolder golden oracle (``tests/services/engine/scaffolder/test_golden_e2e.py``)
  exempts exactly these types from its donor set comparison (AC-5) — so adding a
  DB-backed type here and in the YAML is one act, not two lists to keep in step;
* the ontology↔ORM lockstep guard (``tools/check_ontology_orm_lockstep.py``, AC-3)
  compares each type's declared properties to its table's columns minus the
  exclusions below;
* the fleet adapter's projection (AC-6) emits the declared property set — an
  allowlist — so a column added to a table later is excluded by default and reddens
  the guard until someone either declares it or writes its reason here.

**Why the mapping lives outside the YAML.** ``services/engine/ontology_schema.json``
sets ``additionalProperties: false`` on object types, so the ontology cannot carry a
table-mapping key (PLAN-0109 F12).

**Exclusions are keyed by ``(type, column)``, never by column alone.** ``seq`` exists
only on ``repair_case_accepted_quote``, ``photos`` only on ``repair_case``, ``note`` and
``attachment`` only on ``repair_case_quote``. A column-keyed entry would name a column
two of the three tables do not have, and the guard's stale-exclusion check (AC-3 iii)
exists to redden on exactly that (PLAN-0109 Errata iii, s294).

**Every reason carries its provenance**, because a later reader deciding whether an
exclusion may be lifted needs to know whose decision it was:

* ``ruled-out (Cray)`` — a typed ruling (SD-D). Lifting it is a new ruling.
* ``payload-not-text (Code, reversible)`` — Code's exclusion before the question reached
  Cray: a path list and a JSON blob are payload, not text a model answers from. Cray
  may reverse it; the reversal is a YAML declaration plus removal of the entry plus a
  compliance correction in the same PR (PLAN-0109 Out of Scope).
* ``internal`` — an insertion-order key with no meaning to a question.
* ``tenancy-key`` — stamped on every table by ``TenantKeyMixin``. Declaring it would
  make a cross-tenant filter EXPRESSIBLE to the NL-query validator, which draws its
  allowlist from the ontology (``tests/services/engine/test_tenant_key_not_in_nl_query.py``
  records why that absence is structural, not incidental).
"""

from __future__ import annotations

from typing import Final

from services.db.base import Base
from services.db.repair_case import RepairCase
from services.db.repair_case_evidence import RepairCaseAcceptedQuote, RepairCaseQuote

#: SD-B RULED (Cray, typed 2026-08-18): the demo-play spine, and nothing else.
#: Widening this set is a new ruling, not a drift (PLAN-0109 Out of Scope).
DB_BACKED_TYPES: Final[dict[str, type[Base]]] = {
    "RepairCase": RepairCase,
    "RepairCaseQuote": RepairCaseQuote,
    "RepairCaseAcceptedQuote": RepairCaseAcceptedQuote,
}

_PAYLOAD_NOT_TEXT: Final = "payload-not-text (Code, reversible)"
_TENANCY_KEY: Final = "tenancy-key (TenantKeyMixin, ADR-0035 D7; never queryable)"

#: Columns a DB-backed type's table has and its ontology type deliberately does not
#: declare. Authored from the model classes, not from memory (PLAN-0109 Step 1).
EXCLUDED_COLUMNS: Final[dict[tuple[str, str], str]] = {
    ("RepairCase", "photos"): _PAYLOAD_NOT_TEXT,
    ("RepairCase", "tenant_id"): _TENANCY_KEY,
    ("RepairCaseQuote", "note"): "ruled-out (Cray)",
    ("RepairCaseQuote", "attachment"): _PAYLOAD_NOT_TEXT,
    ("RepairCaseQuote", "tenant_id"): _TENANCY_KEY,
    ("RepairCaseAcceptedQuote", "seq"): "internal",
    ("RepairCaseAcceptedQuote", "tenant_id"): _TENANCY_KEY,
}
