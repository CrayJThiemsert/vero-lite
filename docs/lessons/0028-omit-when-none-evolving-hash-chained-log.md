# Lesson #0028 — Omit-when-None: evolve an append-only hash-chained log without an epoch boundary

**Date:** 2026-07-07 (session 106; the learning is from session 104)
**Class:** advisory (schema-evolution / tamper-evident-log discipline)
**Trigger:** PLAN-0053 Phase B (ADR-016 S2, session 104, PR
[#596](https://github.com/CrayJThiemsert/vero-lite/pull/596)) added a new nullable
column `actor_service_principal_id` to the append-only, per-row **hash-chained**
audit log (`services/db/audit_log.py`). SD-2 was ratified as **omit-when-None**
(over an epoch boundary) after a code read; proven on-disk that pre-migration rows
recompute byte-identically.

## The lesson

An append-only log with a per-row hash chain —
`row_hash = sha256(canonical(prev_hash + row_fields))`, `verify_chain` walking the
whole thing — carries a hard invariant: **every historical row must recompute to
its stored hash**, or the chain reads as tampered. Naively adding a field to the
hashed payload changes *every* historical row's recomputation, so the whole chain
reports a break, and you are forced into an **epoch boundary** (a hash-format
version with a cutover point) or a **re-hash migration**.

**Omit-when-None avoids both.** Include the new field in the canonical hashed dict
**only when its value is non-None**:

```python
# services/db/audit_log.py::compute_row_hash
canonical_fields = {"prev_hash": prev_hash, "occurred_at": ..., "payload": payload}
if actor_service_principal_id is not None:            # ← the whole trick
    canonical_fields["actor_service_principal_id"] = actor_service_principal_id
```

A historical row (column `NULL`) omits the key → recomputes **byte-identically** to
its stored hash → the tamper-evident chain stays intact with **no epoch boundary**.
A new row with a value includes it. This is the same backward-compat property that
lets **protobuf add an optional field without breaking old bytes** — *absent* is
not the same as *present-with-default*, and the hash sees absence.

## Why (omit-when-None over an epoch boundary)

- **No cutover point to get wrong.** An epoch boundary carries two hash formats; the
  verifier must know exactly where the format changes, and any off-by-one at that
  boundary silently breaks verification. Omit-when-None has no boundary — the
  *presence of the key* is the per-row version signal, so old and new rows are
  verified by one code path.
- **It scales as a convention, not a one-off.** The `compute_row_hash` docstring
  makes it standing: *"Future nullable audit fields SHOULD follow this same
  None⇒omit convention."* Every subsequent nullable audit field inherits the
  backward-compat property for free.
- **The column stays honestly nullable.** The omit lives in the *hash computation*,
  not the schema — historical absence is recorded as absence, not back-filled with a
  fake default that would itself change the hash.

## How to apply

- When you add a field to **any hashed / signed append-only structure** (audit
  chain, Merkle log, signed envelope), make the field's contribution to the hash
  **conditional on presence** (omit-when-None / omit-when-absent) so historical
  records hash identically. Reach for an epoch boundary *only* if the new field must
  be mandatory in old rows (it usually is not — historical absence is truthful).
- **Verify it, do not trust the reasoning.** After the migration, recompute a sample
  of pre-existing rows (run `verify_chain` against a pre-migration fixture) and
  assert byte-identical to the stored hash. This is the "verify a doc's forward
  reference against the code" discipline (CLAUDE.md §6) — the property is only real
  once the on-disk recompute is green (s104: pre-migration rows 7/7 byte-identical).
- Keep the omit in `compute_row_hash`; keep the column `nullable=True`; document the
  convention where the next author will see it (the function docstring did).

## Why a lesson (not just the code docstring)

The mechanism is one `if x is not None` line, but the *reason* it is correct — and
the reason to prefer it over an epoch boundary — is a reusable schema-evolution
principle that applies to any tamper-evident log, not just this column. The
docstring holds the local convention; this lesson holds the transferable one.

Related: CLAUDE.md §8 (build audit trails from day 1); the canonical implementation
+ standing convention in `services/db/audit_log.py::compute_row_hash` /
`verify_chain`; PLAN-0053 (`docs/plans/done/`) SD-2 ratification.
[[0029-verify-full-suite-not-subset]] — sibling verification-hygiene lesson from the
same ADR-016 S2 arc (the regression that the same S2 track later exposed).

*AI-assisted (Claude Code, session 106); no `Co-Authored-By` per CLAUDE.md §7.*
