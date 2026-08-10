# PLAN-0103 Step 8b — the portal-side assembly request, DELIVERED and PARKED

**Date:** 2026-08-10 (session 221)
**Event type:** outward request produced as a gitignored handoff; no repo-tracked artifact other than this summary, **by design**
**Commit:** the commit this summary lands in
**Operator-grade detail:** `.claude/handoffs/session-221/2026-08-10-2030-code-plan0103-step8b-portal-assembly-request.md` (gitignored)

## Summary

Step 8b is the one request vero-lite sends *outward* about the multi-vertical
demo portal. Step 8a committed each system's card copy **inside that system's
profile**; Step 8b specifies everything that is **about more than one system** —
card order, the arrival narrative, the relocated "Build a Vertical" story, the
bilingual policy, and the CTA — because a vero-lite file naming the roster would
be a shadow ingress map (ADR-0036 D2), and a guard already forbids one.

**It is parked rather than sent, on the PLAN's own branch for that case.**
Step 1 asked whether the portal repo exists and the answer had never been
recorded in three sessions of work built on top of it. Session 221 resolved it:
no such repo exists under the account (52 repos enumerated, no organisations),
every prior session that mentioned it said the same, and **Cray confirmed
(typed, s221) that no portal repo will be created** — the landing surface, DNS
routes and Access policies stay configured in the Cloudflare dashboard, each
published system on its own `oct-<vertical-id>` subdomain label. The PLAN's
"does not exist" branch says the request is "drafted and parked, addressed to
the future bootstrap — content is not blocked on the repo existing", which is
exactly what was produced.

## What the request carries

Card order (fleet leftmost per LOCKED-2) with the **three-axis separation**
stated explicitly — card order, ADR-0036 D4's system number, and SD-2's
deployment order are independent and must not be derived from one another; the
arrival arc (PIN email → pick a persona → be refused → be granted → the ask),
with the note that only fleet has personas at all, so a landing narrative
promising "pick who you are" would be wrong on two of three cards; the relocated
Tab E narrative whose load-bearing beat is that **generation happens only when a
human clicks Confirm** (LOCKED-3 moves the story, SD-6 keeps the surface in the
dev console); the bilingual policy scoped to cards and disclosures only, with
SD-7's adopted English role renderings; and the CTA in Cray's exact typed
wording, already committed verbatim in all three `card-copy.md` files.

It also states what the portal must **not** do — fetch a roster from vero-lite
(there is none, by design and by guard), name an apex domain in any vero-lite
artifact, add a connector to a system's Docker network, link a dev-console
surface, or render a live-looking card for a system that is not reachable yet.

## One correction the request carries forward

ADR-0036 D2 prices a new system at exactly **two portal-side artifacts** — one
ingress entry, one Access policy — and both ADRs describe those as *portal-repo
files*. With no portal repo, they are in practice **Cloudflare dashboard
configuration**. `oct-energy` has been live that way since session 213 and has
never needed a checkout, so "the portal-side artifacts exist" is a check against
the dashboard, not against a repo. The two-artifact **price** is unchanged and
still worth checking per system — ADR-0035's acceptance shape reopens the
arrangement if a system ever costs more.

Relatedly: ADR-0035's **OQ-4** (the domain) still reads "deliberately open,
triggered when the portal repo is stood up". That trigger will now never fire,
while the operational answer was given by Cray in sessions 206/212 and has been
live in DNS since session 213. The ADR is not wrong — Cray's answer was explicitly
provisional ("revisit the name after a full life cycle") — but it is waiting on an
event that has been ruled out, and that is worth folding in.

## Key metrics

- Handoff: 1 file, schema-validated (`tools/handoffs/precommit_handoffs.py`, exit 0).
- Repo-tracked artifacts produced: **1** — this summary. No landing page, no
  roster, no portal file, per the PLAN's hard boundary.
- Inputs verified on disk against `main` `8bb8a90`: all three `card-copy.md`
  files; `app.js`'s view registry (Tab E = "Build a Vertical"); `intake-view.js`'s
  header for the confirm-gate beat; `test_published_profiles.py` for the
  no-roster guard.

## Reference

- PLAN: `docs/plans/0103-portal-landing-and-per-system-published-profiles.md`
  §Step 8 (8b), AC-9's second clause, Step 1's branch, SD-2 / SD-6 / SD-7 / SD-8,
  LOCKED-2/3/4.
- ADRs: ADR-0036 D1/D2/D4/D6 (portal boundary, vertical-as-system, the
  two-artifact price); ADR-0035 D1(3)/D4/L5 + OQ-4 (domain and portal-repo
  ownership); ADR-0032 D1 (the demo→pilot wedge the CTA asks for).
- Companion record from the same session:
  `docs/logs/2026-08-10-oct-energy-migration-phase2-and-step9-headroom.md`.

AI-assisted (Claude Code, session 221); no `Co-Authored-By` per CLAUDE.md §7.
