# Session 239 — the Cray.J brand mark deployed, and DEPLOY.md's first real use

**Date:** 2026-08-19 (session 239, continued)
**Event type:** host-state change on MS-S1, under an explicit typed §8 go
**Operator-grade detail:** this file. No gitignored companion — everything below is safe to commit.

## The go and the intent

**Cray, typed:** *"merge 1222 แล้ว deploy fleet ขึ้น MS-S1 เลย"*, after *"เราอยากให้ทดสอบ
deploy fleet โดยทำการเปลี่ยน icon"*.

The icon was the payload; **exercising the procedure was the point.** This is the first
run of `deploy/published/oct-fleet-maintenance/DEPLOY.md`, written hours earlier in the
same session precisely because this system's sequence had lived only as prose in
`docs/logs/`. If the document turned out to be insufficient, the rule agreed in advance
was to fix the document rather than work around it. It was insufficient in one place, and
the fix ships in the same PR as this record.

## 🔴 What the first real use found

**§2 told the operator to diff `<last-deployed-sha>..HEAD` without saying where that sha
comes from.** It is the **host checkout's** HEAD — the host reads `docker-compose.yml` and
`cloudflared/config.yml` from its own working copy, not from the image — and that is *not*
the sha the running image was built from. The two can differ, and here they did: the host
checkout sat at `205ba4b3` while the image had been built from `907a842`.

Reading the wrong one produces a confident wrong answer in both directions: a needless
pull, or a skipped pull that leaves compose reading a stale file. Nothing about the
mistake announces itself.

A second, smaller correction rode along: the documented diff scoped the whole profile
directory, which reports documentation compose never opens. Measured here — three `.md`
files differed and none of them mattered. Both fixes are in this PR.

## Pre-flight — read-only, captured before any host-state action

| Read | Result |
|---|---|
| reachability | `CRAY-MS-S1-MAX` |
| container baseline | `app` `9984c71e47f6` `Up 11 hours` · `cloudflared` `535f6d17a159` `Up 3 days` · `postgres` `3e1daa1bebd1` `Up 3 days` · four sibling containers `Up 7–8 days` |
| stop condition (§0b) | clear — no `vero-published`; the fleet project **was** present, so the read is not vacuous |
| live image | `sha256:e4afeb8f…101b8ee0` — **exactly what this session deployed earlier today**, so the host had not drifted |
| demo state | `DEMO-STATE: PRISTINE` — nobody had played the beat since |
| host pull needed? | **No.** `docker-compose.yml` and `cloudflared/` identical between the host checkout `205ba4b3` and local `b1701b4` |

`PRISTINE` removed the reset branch before any command ran. **`--execute` appears nowhere
in what was executed**; no row was deleted anywhere in this deploy.

## Evidence, step by step — every pass/fail read fixed BEFORE the run

Built on the dev box from `main` at **`b1701b4`**, tree clean. New image
**`sha256:63c5ec37…8877a471`**.

| # | Action | Pre-committed pass | Result |
|---|---|---|---|
| — | build, then read both shipped assets **inside the image** | PNG and narrative sha256 match source; `?v=c51`; the old glyph gone | PNG `b9cfe368…`, narrative `47e3fd20…`, `app.js?v=c51`, `icon('grid'` count **0** |
| 3.1 | tag `:prev` | resolves to the OLD id | `e4afeb8f…101b8ee0` |
| 3.2 | `docker save` → `ssh … docker load` over stdin | a `Loaded image` line | present |
| 3.3 | `docker image inspect` on the host | **id IDENTICAL to the dev box** | `63c5ec37…8877a471` on both |
| 3.4 | `compose config --quiet` | **zero bytes** | 0 |
| 3.5 | `compose up -d` | **only `app` Recreated** | `postgres Running`, `cloudflared Running`, `app Recreated → Healthy` |
| 4.1 | `docker inspect` the app container | `.Image` == the loaded id | matches; container `9984c71e47f6` → **`b23992b244c8`** |
| 4.2 | `sha256sum` the brand mark **inside the running container** | `b9cfe368…` | matched |
| 4.3 | `sha256sum` the narrative, same container | `47e3fd20…` | matched |
| 4.4 | boot log | the seed **skips** | `run 'run-fleet-operate-demo' already present — skip` |
| 4.5 | demo state after | still `PRISTINE` | `PRISTINE` |
| 4.6 | do-no-harm vs the baseline | this system's other two containers and both siblings untouched | see below |

**4.3 is not boilerplate and it is worth keeping in the procedure.** Shipping a new asset
while silently dropping an existing one is a failure nobody checks for, because the thing
you just added is the thing you look at. Both assets were read out of the same running
container, by content.

### Do-no-harm, verified rather than assumed

`oct-fleet-maintenance-cloudflared` kept container id `535f6d17a159` and its `Up 3 days`;
`oct-fleet-maintenance-postgres` kept `3e1daa1bebd1` and its `Up 3 days`. The tunnel never
re-registered and `pgdata` was never at risk. Both sibling systems' four containers were
untouched at `Up 7–8 days`. Only `oct-fleet-maintenance-app` changed.

## What was NOT verified here

- **The mark as it renders through the edge.** Cloudflare Access needs an interactive PIN
  no automated step can satisfy. Verified in the local browser under the **published**
  profile with the served asset versions confirmed: the `<img>` resolves, natural size
  374×262, not broken, no SVG left in the tile, `object-fit: contain`. Opening the live
  system is Cray's check, as it was for the narrative panel earlier today.
- **That the mark is legible at 28 px.** It is not, and that is recorded rather than
  discovered later: the artwork paints at 7% of source scale, so the "Cray.J" wordmark
  inside it renders about 16×4.6 px — below the cap height anything reads at. Cray chose
  this form knowingly (option (a) of three offered). The available fix is cropping the
  artwork to the bunny alone; it needs no code change beyond a new file.

## The procedure's own verdict

Eleven pre-committed reads, eleven passes, one documentation gap found and closed. The
sequence itself needed no improvisation — which is the difference between following a
procedure and reconstructing one from two logs, and the reason the file exists.

## Reference

- Feature: [#1222](https://github.com/CrayJThiemsert/vero-lite/pull/1222), merged at `b1701b4`.
- Procedure: `deploy/published/oct-fleet-maintenance/DEPLOY.md` (corrected in this PR).
- Prior host-state record for this system: [`2026-08-18-s239-fleet-origin-narrative-deploy.md`](2026-08-18-s239-fleet-origin-narrative-deploy.md).
