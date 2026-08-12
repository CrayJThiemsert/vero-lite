# MS-S1 secrets ACL — the exposure closed, and the runbook's remedy replaced

**Date:** 2026-08-12 (session 223)
**Event type:** host-state change on MS-S1, under two explicit typed §8 gos
**Operator-grade detail:** this file. No gitignored companion — everything below is safe
to commit (no secret material, no apex domain).

Closes the exposure carried open by session 222's handoff §5.5 and by
`docs/logs/2026-08-11-plan0103-step10-procurement-bring-up.md` §"Residual". That record
states the remedy in `docs/runbooks/published-demo-bring-up.md` §8 does not work; it was
right, and this session replaced it with a form that does.

## The gos

**Cray, typed, 2026-08-12 (session 223), two of them:**

1. **Ladder A → C**, each rung tightening `C:\vero-secrets` and canary-verifying with a
   force-recreate of **procurement only** — energy explicitly not to be touched.
2. After both rungs passed, a **second go to restart energy for real**, chosen over a
   non-invasive mount probe, to close the last unproven gap end-to-end.

The second go was asked for rather than assumed: the first go named energy as
out of scope, and a still-running container proves nothing about a file it opened
38 hours before the ACL changed.

## Baseline — what was actually there

Every ACE **inherited** from the drive root (`AreAccessRulesProtected=False`), on the
directory and on both credentials files:

```
BUILTIN\Administrators:(I)(F)
NT AUTHORITY\SYSTEM:(I)(F)
BUILTIN\Users:(I)(RX)
NT AUTHORITY\Authenticated Users:(I)(M)
```

Every local account could read both tunnel secrets; every authenticated one could
replace them.

## What changed, and the evidence for each rung

| | Rung A | Rung C |
|---|---|---|
| Change | drop `Authenticated Users` | also drop `BUILTIN\Users`, grant the account SID `(RX)` |
| `oct-procurement-cloudflared` | `e04267502e92` → **`2cb360d9d6e3`** | → **`87713924a147`** |
| `Access is denied` | none | none |
| Tunnel actually back | 4× `Registered tunnel connection` | 4× `Registered tunnel connection` |
| Co-tenant | energy `76049f41de22` / `6e66a8546884` untouched, Up 38 h | unchanged |

Then, under the second go:

| | Energy proof |
|---|---|
| `oct-energy-cloudflared` | `76049f41de22` (Up 38 h) → **`3f3ce9c5d6a2`** |
| `oct-energy-app` | `6e66a8546884`, **never recreated**, Up 38 h (healthy) — only the connector was recreated |
| Result | `compose config` gate rc=0, `up` rc=0, 4× `Registered tunnel connection` |

**Final state, identical on the directory and both credentials files:**

```
CRAY-MS-S1-MAX\Jirachai Thiemsert:(OI)(CI)(RX)
BUILTIN\Administrators:(OI)(CI)(F)
NT AUTHORITY\SYSTEM:(OI)(CI)(F)
```

### The check was seen RED before it was trusted GREEN

A standalone verifier asserted two things at once — that the remote read *succeeded*
(3/3 targets returned `Successfully processed 1 files`) and that no `Authenticated Users`
ACE remained. It was run **before** any change and reported `authenticated_users_aces=4`,
`VERDICT: FAIL`; the same command after rung A reported `0` / `PASS`. The positive anchor
is load-bearing: without it an ssh failure would produce zero matches and pass silently —
the exact `|| echo`-shaped false pass this repo has been bitten by before.

## Why the old form failed — the part worth carrying forward

The session-222 command kept `BUILTIN\Administrators:(OI)(CI)F` **and the signed-in
account is an Administrator**, yet Docker still got `Access is denied`.

The only explanation consistent with that: Docker Desktop's backend runs under a
**filtered (non-elevated) token**, in which the `Administrators` group is marked
*deny-only* and grants nothing. The mount had been working on `BUILTIN\Users:(RX)` all
along. Granting the **account SID** directly is what makes full closure possible — a user
SID is always present and enabled in a filtered token.

A second, structural error in the old form: the wide ACEs were **inherited**, and an
inherited ACE cannot be edited in place. `/grant:r` alone adds an explicit ACE that
*unions* with the inherited one, so a "tightening" written that way changes nothing while
appearing to succeed. `/inheritance:d` must come first.

Removing an inheritable ACE on the directory propagated to both existing files
automatically — they still report `(I)`. `/t` was not needed and would have been wrong.

## The `icacls /save` backup — resolved, and it taught one more thing

`icacls /save` wrote `C:\vero-secrets-acl-backup-s223.txt` before rung A. It holds no
secret material, only ACL descriptors — but it sat **outside** the directory being
tightened, so it kept the wide inherited ACL (`BUILTIN\Users:(RX)` +
`Authenticated Users:(M)`) while everything it described had been locked down.

**Cray ruled: move it into the tightened directory rather than delete it** — the record of
the prior ACL is worth keeping, just not readable by every local account. It now lives at
`C:\vero-secrets\acl-backup-s223.txt`.

🔴 **A same-volume move does NOT re-inherit the destination's ACL — measured, not assumed.**
On Windows a move within one volume is a rename: the file carries its existing ACEs
across. The capture shows the wide set **still on the file after it had landed inside the
tightened directory**; only `icacls <file> /reset` made it pick up the parent's ACEs. A
move done without that step produces a file that looks protected because of where it sits
and is not — the worst of both, since nothing about its location suggests checking.

Verified after the fact across **all 8 paths** under the directory (`icacls C:/vero-secrets
/t`): `icacls_processed=8 failed=0`, zero `Authenticated Users` or `BUILTIN\Users` ACEs,
and the old `C:\` root path reporting *the system cannot find the file specified*.

### Also worth recording: the enumeration was wider than the evidence

The first four captures read back only the directory and the two credentials files. The
directory also holds `rollback-s220\` with its own `.env`, `config.yml` and
`docker-compose.yml` — three paths, one of them a plausible secret carrier, that were
**inside the blast radius but outside the evidence**. Inheritance had in fact propagated to
all of them, so nothing was wrong; but that was known by theory and not by measurement
until a reviewer asked. `icacls <dir> /t` reads the whole tree in one call and costs
nothing extra.

## Not a defect

`cloudflared` logs `ERR Cannot determine default origin certificate path … cert.pem` at
every start. It is expected for a credentials-file tunnel and was present on both systems
before and after; all four connections register immediately after it.
