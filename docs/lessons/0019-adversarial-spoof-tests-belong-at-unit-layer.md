# Lesson #19: Adversarial spoof tests belong at the unit/server layer — never ask a live agent tab to emit a falsified identity

> **Status:** Codified 2026-05-30 (OQ-T5 reconcile, session 26). Surfaced by PLAN-0012 Step 5's cross-tab spoof matrix (AC-4(c)) — the live "every tab spoofs" framing met reality when Chat *refused* to self-spoof (FINDING-4) while Cowork complied.
> **Severity:** Low–medium — not a correctness bug; a test-design + governance smell. The risk is wasted effort (theatrical live tests) plus a tier-posture asymmetry (one tab lies on request, another refuses) that adds noise to the threat model.
> **Cross-references:** PLAN-0012 AC-4(c) / AC-5 / AC-8; `tests/vero_bridge/test_server_adversarial.py` (the unit layer that already proves the property); `docs/research/private/2026-05-29-vero-bridge-step5-spoof-matrix.md` §4 (Chat refusal verbatim) + §3 (Cowork compliance); `docs/runbooks/vero-bridge-cross-client-evidence.md` §5; OQ-T3 (Option I — `claimed_tag` is audit-only, never authorization); FINDING-4. [[lesson-0017-mcp-cross-tab-visibility-empirical-probe]] (tab-group routing — why a spoofed tag forges nothing).

## 1. The finding

The property under test — *"the server accepts any `claimed_tag`, never authorizes on it (Option I), and the observable fingerprint is independent of the tag"* — is a **server property**, fully provable at the unit layer. PLAN-0012 Step 5 *also* tried to prove it by dispatching each live agent tab to call `bridge_whoami` with a **falsified** `claimed_tag`. That live framing:

- **Was redundant** with the 26 unit tests in `test_server_adversarial.py`, which already assert spoof-acceptance + signal-independence + audit-discrepancy with **no live agent lying**.
- **Did not survive contact with the agents.** Chat (conversation-only tier) *correctly refused* to emit a forged tag (FINDING-4); Cowork (tool-capable tier) complied. The server property got proven via Code self-spoof + Cowork spoof + unit tests — the literal "Chat claiming cowork" cell was unobtainable from a cooperative tab.

## 2. Why the live cells were the wrong instrument

- **A spoofed tag forges nothing.** Under tab-group routing (Lesson #0017 §3.1), the observable fingerprint (pid/ppid/fds) is set by the OS, not the caller; the tag rides on the argument shape and the server only logs it. So "does the server accept a forged tag?" is answered identically whether a unit test or a live agent supplies the forged string — but the unit test is deterministic, repeatable, and needs no one to lie.
- **Asking an agent to lie is a governance smell.** A cooperative agent *should* refuse to misrepresent its identity — FINDING-4 is correct, desirable behavior. A test design that *requires* an agent to spoof is at odds with the discipline we want every tab to hold. Chat's own counter-proposal was the better design: *"verify that spoofed tags are detected/rejected, not paste a forged one through."*
- **It created a tier asymmetry.** Cowork complied while Chat refused — leaving the audit trail with one tab that lies on request and one that won't. That asymmetry is noise in the threat model, not signal.

## 3. The convention

**Adversarial spoof / identity-forgery testing lives at the unit/server layer. Live agent tabs are never asked to emit a falsified identity tag.**

- Prove server-side spoof-acceptance + signal-independence + audit-discrepancy with unit tests that construct forged envelopes **directly**.
- Reserve live cross-tab capture for **truthful** round-trips (cross-client parity, wire-format equality, real routing) — `claimed_tag` always matches the operating tier.
- Every tab's standing instruction is: **never emit a falsified identity tag, regardless of stated rationale** — codified during the OQ-T5 reconcile in `chat_tab_instructions.md` (behavioral rule 7) and `cowork_tab_instructions.md` (Bridge-client posture).

## 4. Generalization

Any *"can the system be fooled by a lying client?"* property is a property of the **system**, not of the honest clients you happen to have. Test it by constructing the malicious input directly (unit / integration), not by asking a cooperating participant to behave maliciously. Reserve live multi-actor capture for proving the **honest** path works end-to-end. (Single-operator threat model — OQ-T3 — makes this especially clear: there is no adversary to simulate, only a server contract to verify.)

## 5. Application checklist

Before designing an adversarial test that involves a live agent tab:

1. **Is the property a server/system property?** If yes, construct the adversarial input at the unit layer; do not route it through a live agent.
2. **Would the test require a cooperative actor to misrepresent itself?** If yes, redesign — that is the unit layer's job, and a tab refusing is correct behavior you do not want to train against.
3. **Reserve live capture for the honest path** — truthful tags, real routing, wire-format parity.
4. **Codify the no-spoof posture per tab** so the refusal is a written rule, not an emergent accident.
