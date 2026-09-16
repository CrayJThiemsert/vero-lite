# PLAN-0126 Step 13 — deploying the story-mode explainer to the live fleet system

**Date:** 2026-09-16 · **System:** `oct-fleet-maintenance` · **Merged sha shipped:** `ea6944fa` (#1499) ·
**Author:** Claude Code (Tier 2)

> **The go, recorded BEFORE any command reached the host** (`CLAUDE.md` §8;
> `deploy/published/oct-fleet-maintenance/DEPLOY.md` §0). Cray, typed, 2026-09-16:
> **"ทำ Step 9 (Artifact), Step 13 deploy และ closeout ตามลำดับได้เลย"**, and then, when
> the auto-mode classifier refused the first host read, **"(ก) go ได้เลยเมื่อถึงขั้นตอนที่ต้องการ"**.
>
> **Who ran what.** Code ran the §2 read-only pre-flight, the §2a local build, and every
> edge read. The auto-mode classifier refused Code's run of the §3 ship script, and Code
> did not work around the refusal. **Cray ran that script from a terminal on the dev box.**
> Code wrote the script, syntax-checked it with a broken-file control, and verified every
> line of its output file afterwards.
>
> 🔴 The shared `deploy/published/deploy.py` was not used. It targets another profile
> (`DEPLOY.md` §1).

## §2 Pre-flight — the read-only baseline

| Read | Result |
|---|---|
| `hostname` | `CRAY-MS-S1-MAX` |
| fleet **app** | `e6984c248b51`, image `sha256:880307365d7f…`, Up 8 days (healthy) — **the rollback point** |
| fleet **postgres** | `3e1daa1bebd1`, Up 8 days (healthy) |
| fleet **cloudflared** | `b8afbac907e7`, Up 8 days |
| `docker compose ls` | this project `running(3)` ✅; **no `vero-published`** ✅ |
| `:prev` before this deploy | `sha256:0fc679cf0e50…` (overwritten by step 1 below; `:prev` is one deep) |
| demo state (plan mode) | **`DEMO-STATE: PRISTINE`** → no reset |
| host checkout | `dd4228f`, clean, an ancestor of `ea6944fa` (so a fast-forward pull is possible) |

**The pull decision was established by diff, not assumed.** `git diff --name-only dd4228f ea6944fa`
over only the two files the host reads names `cloudflared/config.yml`. One commit touches it
(`456b3b58`), and the diff is exactly the two `/story/` rows plus their basis comment. So a
host `git pull` **and** `--force-recreate cloudflared` were both required.

## §2a Pre-ship — local build, then read what ships

- **Build context: `git archive ea6944fa`** (tracked files, git modes), not the working tree. The working tree adds
  40 gitignored `verticals/*/generated/` files that no runtime code reads (only the CLI and
  scaffold do). It is also where probe batteries leave restored files at mode 0600, the defect
  the s256 deploy caught at this step. The export had `0` files unreadable by others under the
  COPY paths.
- **Local image:** `sha256:0d9578379e1e…`.
- **In-image hashes:** every COPY-carried file changed between `dd4228f` and `ea6944fa`, **33 of 33**,
  hashed inside the image matched the export line for line (`hash_diff_rc=0`,
  `No such file: 0`). The six `story/` files are among them.
- **Local boot** of the built image with the fleet `published.env` and no database (evidence, not the gate):
  - `/story/` 200 with CSP; `story.js`, `story.css`, `story-data.js`, `three.module.min.js` and the
    Plex font all 200 with CSP;
  - `/` carries `content="published"`; `/story/` carries no `ui-profile` meta;
  - `/story` (no slash) → 307 from the app, which the edge does not admit.

⚠️ **This deploy ships all of `main` since `dd4228f`, not only the story.** The 33 files include the
PLAN-0119 LLM capacity/workload changes and the fleet data-adapter changes merged since the
s256 deploy. They are CI-gated on `main` and were hashed above. They are named here so nobody
reads this record as a story-only change.

## AC-10 pre-read — the RED baseline, taken before the ship

Cray completed the Cloudflare Access login in the Code session's browser tab. The reads are
same-origin `fetch`es through the edge:

| Path | Status | CSP |
|---|---|---|
| `/story/` | **404** (0 bytes, the edge catch-all) | absent |
| `/story/story.js` | **404** | absent |
| `/` (control: the reader is authenticated and reaches the app) | 200 | present |
| `/assets/app.js` (control) | 200 | present |

## §3 The sequence — every step passed its pre-fixed read

| # | Step | Result |
|---|---|---|
| 0 | guard: the local image is the one §2a verified | `0d9578379e1e…` ✅ |
| 1 | tag `:prev` | resolves to `sha256:880307365d7f…`, **exactly the §2 baseline** |
| 2 | `docker save │ ssh … docker load` | `Loaded image: oct-fleet-maintenance-app:latest` |
| 3 | id equality across machines | host `:latest` = `sha256:0d9578379e1e…` = local |
| A | host `git pull --ff-only` | `dd4228fd..ea6944fa` fast-forward; host HEAD `ea6944fa`; `status --short` 0 lines; the bind-mounted `config.yml` carries `^/story/$` (L62) and `^/story/[^/]+$` (L64) |
| 4 | `config --quiet` | **0 bytes** |
| 5 | `up -d` | `postgres` Running · **`app` Recreate → Recreated → Healthy** · `cloudflared` Running |
| 5b | `up -d --force-recreate cloudflared` | connector Recreated → Started (required: `config.yml` changed) |

## §4 Verify — against the §2 baseline

| Read | Result |
|---|---|
| app health / `.Image` | `healthy` on `sha256:0d9578379e1e…` at the first poll — **the deploy took effect** |
| fleet app container | `e6984c248b51` → `f2dde43472ae` (expected: recreated) |
| fleet postgres | `3e1daa1bebd1` → `3e1daa1bebd1` **unchanged**; `pgdata` never at risk |
| fleet cloudflared | `b8afbac907e7` → `382a546c18fd` (expected: force-recreated for the new ingress map) |
| the other four containers on the host (sibling systems) | all **unchanged** ids, Up 8 days |
| boot log | `run 'run-fleet-operate-demo' already present — skip` · `fleet live cases loaded: 4 case(s) with an accepted quote reach the gate` — the seeded beat survived |
| demo state, plan mode | **`DEMO-STATE: PRISTINE`**, same as the baseline |
| running-container `sha256sum` of the six story files, `main.py`, `app.js` | **8/8 identical** to the merged export (`diff_rc=0`) |

## AC-10 post-read — live through the edge, under Access

| Path | Status | CSP (equal to the console's) |
|---|---|---|
| `/story/` | **200** | present ✅ |
| `/story/story.js` · `story-data.js` · `story.css` | 200 · 200 · 200 | present ✅ |
| `/story/three.module.min.js` | 200 (670,681 characters, ASCII, so equal to its byte size) | present ✅ |
| `/assets/fonts/IBMPlexSans-Regular.woff2` | 200 | present ✅ |
| `/story` — control: not admitted | **404** | absent |
| `/story/sub/x.js` — control: `[^/]+` admits nothing deeper | **404** | absent |

⇒ **`pre=404 post=200 csp=present`**, `DEMO-STATE: PRISTINE`, under the go quoted at the top.

**The page itself, loaded in the same tab:**
- every story resource the page requested returned 200;
- 7 acts, the canvas draws, the clock runs (`0:12 / 1:56` at the read);
- Plex Sans 400/500 and Mono 400/500 `loaded` (SemiBold is lazy: its one user is the closed Sources drawer).

**The console link is live:** `/` serves `assets/app.js?v=c52` and renders one anchor, "ทำไม",
`href=/story/`, `target=_blank`, `rel=noopener`.

⚠️ **Instrument note.** Some "bytes" figures in the post-read are `body.length` of the decoded
text, meaning UTF-16 characters, not bytes. That is why `/story/` reads 1,741 against its
2,026-byte file (the page is Thai). Only the ASCII `three.module.min.js` count is comparable to a
byte size. The status and CSP columns are the readings this AC rests on.

## An observation, not a regression

The browser console on `/story/` logs one CSP refusal of
`static.cloudflareinsights.com/beacon.min.js`. **The console page `/` carries the same injected
beacon script.** The edge injects it into document responses (not into `fetch` bodies), and
`script-src 'self'` blocks it on both. It predates this deploy and changes nothing the page does.
Recorded so it is not rediscovered as a new failure.

## Rollback

`:prev` = `sha256:880307365d7f…` (built 2026-08-26, the image that ran before this deploy):

```bash
ssh ms-s1 docker tag oct-fleet-maintenance-app:prev oct-fleet-maintenance-app:latest
ssh ms-s1 docker compose -f C:/projects/vero-lite/deploy/published/oct-fleet-maintenance/docker-compose.yml -p oct-fleet-maintenance up -d
```

⚠️ Rolling the image back does not roll back the host checkout (`ea6944fa`) or the connector's
ingress map. The two story rows are harmless with the old image: the paths would 404 from the
app instead of from the edge. A full revert would also need
`git -C C:/projects/vero-lite checkout dd4228f -- deploy/published/oct-fleet-maintenance/cloudflared/`
and a connector recreate.

---

*Host state changed under Cray's typed go, recorded above before the first host command. The
ship script ran from Cray's own terminal; Code verified its output. Ollama received no contact.
AI-assisted (Claude Code).*
