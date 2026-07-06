# Runbook — Run the OCT stakeholder demo (energy · supply_chain · aquaculture · build your own, live)

> **Goal.** Bring up the Operational Control Tower (OCT) demo locally and drive
> all three OCT features on **either vertical** — `energy` or `supply_chain` —
> from a single command, so you can rehearse it, screenshot it, or show it to a
> design partner. The demo is one FastAPI process serving the UI + API at one
> URL; **the vertical is a config swap** (`OCT_VERTICAL`), the same UI + engine
> re-skinned by the ontology (the moat — ADR-006 vertical plugin architecture).
>
> **Scope.** Tailored to the dev/demo box = **this machine (Cray-Legion5Pro,
> WSL2 Ubuntu)** running the OCT API as **bare uvicorn** with a local `.env`.
> `docker compose` runs postgres only; the API is not containerized.
>
> **Provenance.** Every command + every expected value below was run live on
> `main` `508aa90` (session 31, 2026-06-02) with **MS-S1 powered off**, except
> the NL-query *grounded* path (§5) — that requires MS-S1 and its known-good
> evidence is from PLAN-0013 session 28 (`docs/plans/done/0013-oct-stakeholder-demo.md`).
>
> **Since then (PLAN-0015 fast-follow, #144, session 34, `cba80dc`):** the
> synthetic `occurred_at`s on **both** verticals were re-timed so the breach is
> the timeline's **tail beat** (see the tail-beat note in §9). This moved **only
> timestamps** — measured values, asset/shipment ids, units, severities, and
> counts are unchanged — so every **expected value** below (counts, `measured_value`,
> confidence) still holds; only the relative *ordering* of events on the timeline
> changed.
>
> **Verticals since (lineage).** The **aquaculture** vertical (§3a) was scaffolded
> by `vero-lite new-vertical` — the demo generator's own output (PLAN-0016, session
> 37) — not hand-built; the **"Build a Vertical" live co-creation face** (§5b)
> shipped in PLAN-0017 (#170–#173, session 39). Both ride the same engine + UI,
> driven only by ontology/config — no per-vertical UI code.

---

## 0. The one thing to know first — the demo has two modes

OCT feature 2 (NL query) translates plain language → an ontology query **using
the local LLM** (Ollama on MS-S1, ADR-010 D1). Features 1 (map) and 3
(anomaly→decision) do **not** need the LLM — feature 3 keeps a deterministic
**rule fail-safe** so the killer moment works offline (AC-safety).

| Feature | MS-S1 **off** | MS-S1 **on + warmed** |
|---|---|---|
| **A — Operational map** (`/objects` + `/meta`) | ✅ works | ✅ works |
| **B — Anomaly → decision + Approve/Execute** | ✅ rule fail-safe, confidence **0.8** | ✅ LLM reasoning trace, richer, confidence ~0.92 |
| **C — NL query** (`POST /query`) | ❌ returns *"I couldn't translate that question…"* (ungrounded) | ✅ grounded answer + source-object ids |
| **D — Data→Decision flow** | ✅ works | ✅ works |

**Decision:** a quick map + killer-moment demo needs **nothing** (postgres is the
only dependency). A **full three-feature** demo needs **MS-S1 powered on +
warmed** first — see §5.

---

## 1. Preconditions (verify once)

```bash
cd ~/work/vero-lite

# Postgres up on the host (ADR-003: host port 5442, not the vendor default 5432)
docker ps --format '{{.Names}}\t{{.Ports}}\t{{.Status}}' | grep vero-postgres
#   vero-postgres   0.0.0.0:5442->5432/tcp   Up ... (healthy)

# .env present (gitignored; the only place DATABASE_URL etc. live)
test -f .env && echo ".env OK"

# DB migrated (the Approve→Execute round-trip persists to Postgres)
uv run alembic current     # expect: 0001 (head)
```

If postgres is down: `docker compose up -d` (brings up postgres). If migrations
are behind: `uv run alembic upgrade head`.

---

## 2. Run the **energy** vertical

`OCT_VERTICAL` defaults to `energy`, so no extra env is needed.

```bash
cd ~/work/vero-lite
# OCT_DEMO_TIME_ANCHOR=true is the PLAN-0015 live-time loop (breach ≈ now,
# Approve→Execute resolves the incident on Screen A). Off by default; see §9.
OCT_VERTICAL=energy OCT_DEMO_TIME_ANCHOR=true uv run uvicorn services.api.main:app --port 8000
```

Then open **http://localhost:8000** (see §4 for why localhost works from
Windows).

**Known-good baseline (verified offline this session):**

- `GET /objects/Site` → **2** sites with lat/lng: `North Substation` (13.75,
  100.5), `Riverside Microgrid` (13.81, 100.56) → both plot on the map.
- `GET /objects/Asset` → **4** assets (Battery Bank A/B, Inverter Unit A, Feeder
  Meter A).
- `GET /recommendations` → **1** action — the killer moment:
  `Investigate over-temperature on asset-battery-01`, confidence **0.8**, status
  `proposed`, handler `echo`, **2-step reasoning trace**
  (`measured_value 96.5 celsius >= threshold 90.0` → derived over-temp alert),
  affected entity `Asset / asset-battery-01`.
- Approve → Execute round-trips to `status: executed` with an `echo` handler
  receipt (persisted to Postgres).

---

## 3. Run the **supply_chain** vertical (config swap, no code change)

Swap the vertical + its recommender policy via env. Use a **different port** so
you can run both at once and lay the two browsers side by side — the strongest
"same UI, your domain" pitch.

```bash
cd ~/work/vero-lite
OCT_VERTICAL=supply_chain \
OCT_RECOMMEND_THRESHOLD=8 \
OCT_RECOMMEND_ENTITY_TYPE=Shipment \
OCT_RECOMMEND_ENTITY_ID_FIELD=shipment_id \
OCT_RECOMMEND_LABEL="cold-chain temperature breach" \
OCT_DEMO_TIME_ANCHOR=true \
OCT_RECOVERY_VALUE=4.2 \
OCT_RECOVERY_DESCRIPTION="Vaccine Lot VX-1188 temperature back within the 2-8 °C range." \
uv run uvicorn services.api.main:app --port 8098
```

> The last three lines are the PLAN-0015 live-time loop (§9): the anchor flag +
> the cold-chain recovery override (the recovery reading is energy-worded by
> default — `OCT_RECOVERY_VALUE`/`OCT_RECOVERY_DESCRIPTION` re-skin it per
> vertical, the same config-swap pattern as `OCT_RECOMMEND_*`).

Then open **http://localhost:8098**.

**Known-good baseline (verified offline this session):**

- `GET /objects/Facility` → **2** facilities with lat/lng: `Central Cold Hub`
  (13.69, 100.75), `Northern Distribution Center` (13.92, 100.52).
- `GET /objects/Shipment` → **4** shipments (pharma / produce / frozen /
  biologic).
- `GET /recommendations` → **1** action:
  `Investigate cold-chain temperature breach on shipment-pharma-01`, confidence
  **0.8**, handler `echo`, 2-step trace (`measured_value 14.6 celsius >= threshold
  8.0`), affected entity `Shipment / shipment-pharma-01`.
- Approve → Execute → `status: executed` + receipt.

> **Alternative — edit `.env` instead of inline env.** `.env` has a commented
> `supply_chain` block (uncomment it, comment the energy line). Inline env (above)
> wins over `.env` and needs no file edit — preferred for ad-hoc switching.
> Field reference: `services/api/config.py` (`oct_vertical`, `oct_recommend_*`).

---

## 3a. Run the **aquaculture** vertical — the first *below*-threshold breach

The third vertical (ADR-0015 D4 pick) was **scaffolded by `vero-lite new-vertical`**
(PLAN-0016 — the demo generator's own output), not hand-built. It is the first
vertical whose breach is a **crash**: a dissolved-oxygen reading *falls below* the
safe threshold (3.2 < 4 mg/L), so it runs with `OCT_RECOMMEND_DIRECTION=below`
(PLAN-0016 Step 0). Use a third port to lay it beside the others.

```bash
cd ~/work/vero-lite
OCT_VERTICAL=aquaculture \
OCT_RECOMMEND_THRESHOLD=4 \
OCT_RECOMMEND_DIRECTION=below \
OCT_RECOMMEND_ENTITY_TYPE=Pond \
OCT_RECOMMEND_ENTITY_ID_FIELD=pond_id \
OCT_RECOMMEND_LABEL="dissolved-oxygen crash" \
OCT_DEMO_TIME_ANCHOR=true \
OCT_RECOVERY_VALUE=5.5 \
OCT_RECOVERY_DESCRIPTION="Pond POND-07 DO recovered above the 4 mg/L safe threshold after emergency aeration." \
uv run uvicorn services.api.main:app --port 8099
```

Then open **http://localhost:8099**.

**Known-good baseline (verified live this session, session 37, via the HTTP API):**

- `GET /objects/Farm` → **2** farms with lat/lng: `Bayfront Shrimp Farm` (13.52,
  100.27), `Riverside Tilapia Farm` (14.21, 100.58).
- `GET /objects/Pond` → **4** ponds (3 `active`, 1 `fallow` — pond-05).
- `GET /recommendations` → **1** action:
  `Investigate dissolved-oxygen crash on pond-07`, confidence **0.8**, handler
  `echo`, 2-step **below-direction** trace
  (`measured_value 3.2 mg/L <= threshold 4.0`, `direction: below`), affected
  entity `Pond / pond-07`.
- Approve → Execute → `status: executed` + receipt; the recovery reading lands at
  DO **5.5 mg/L** (back above the 4 mg/L safe line).

> **The env block is the command's own output.** `vero-lite new-vertical
> aquaculture …` prints exactly this `OCT_*` block in its run checklist — the
> generator hands you the run recipe. The `--direction below` knob is what makes a
> *crash* (not an overrun) fire the recommender; an above-direction vertical
> (energy/supply_chain) omits it (default `above`).

---

## 3b. Run the procurement OPERATE demo (Control-leg v1, View H — PLAN-0054)

Unlike §2/§3/§3a (which drive the map + anomaly→decision on **read-only** data), this
demo drives the **OCT Monitor (View H)** from **watch → OPERATE**: a named,
authenticated operator **approves/rejects** a `waiting_human` procedure gate and
**cancels** a parked run — from the UI, with **SoD** (requester ≠ approver) + a
tamper-evident audit actor. It runs the **procurement** vertical (5 authored SoD
principals, tiered DOA) with **auth ON**.

> **DB required.** Unlike the read-only demos, this one **persists** runs — bring up
> Postgres + migrate (§1) first. The seed is **deterministic + MS-S1-independent**
> (the advisory stub — no LLM/host-state), so it needs nothing warmed.

**One command (self-seeding).** The `oct-demo-procurement` launch config
(`.claude/launch.json`, port **8101**) sets `OCT_VERTICAL=procurement`,
`API_AUTH_ENABLED=true`, `OCT_DEMO_SEED_OPERATE=true`, and an `API_KEYS` operator key
for **`appr-pm`** (ผจก.จัดซื้อ). On boot it registers the deterministic procurement
executor factory (PLAN-0054 Step 6b) and **auto-seeds ONE `waiting_human`
`emergency_sourcing_round` run** — idempotent (a fixed `run-operate-demo` id) +
fail-soft (a seed error logs, never blocks boot).

Manual run (equivalent to the launch config):

```bash
cd ~/work/vero-lite && source .venv/bin/activate
# Provision ONE operator key for the appr-pm approver (RAW key stays out of git — §8):
python -c "import secrets,hashlib; k=secrets.token_urlsafe(24); print('key:',k); print('sha256:',hashlib.sha256(k.encode()).hexdigest())"
OCT_VERTICAL=procurement \
API_AUTH_ENABLED=true \
OCT_DEMO_SEED_OPERATE=true \
API_KEYS='{"<sha256-hex>": "appr-pm"}' \
exec uvicorn services.api.main:app --port 8101
```

Then open **http://localhost:8101** and go to the **Monitor** tab (**View H** — click
the tab, `location.hash` does not route OCT views). The seeded `waiting_human` run is
listed, suspended at its `approve` gate; a **login bar** sits at the top of the view.

**The governed round-trip (the operate UI — PLAN-0054 Steps 2–5, shipped):** in the login
bar enter the RAW key + a display identity (`appr-pm`) → **Operating as appr-pm**; select
the run → per-proposal **Approve / Reject** appear → **Submit decisions** POSTs the gate
(`Authorization: Bearer <key>`) → SoD passes (requester `req-planner` ≠ approver `appr-pm`)
→ the run resumes to the `issue_po` gate → approve again → **completed**. A **logged-out**
submit or a **self-approval** fails closed (**403**, surfaced inline); a concurrent change
is a **409** "reload and retry"; a **Cancel run** on a `waiting_human` run → `cancelled`.
The seed's **฿288,000** amount lands in the **ผจก.จัดซื้อ** DOA tier, so `appr-pm` is the
tier-matched approver (a หน.จัดซื้อ would be under-tier).

> **Security (pilot-grade, PLAN-0047 SD-A).** The operator's key is a **bearer credential**
> held in `sessionStorage` (per-tab) and sent ONLY on operate POSTs — reads stay
> header-less. The typed identity is a cosmetic display; the REAL approver is the key the
> backend resolves to a `person_id` and SoD-checks (a buyer's key cannot approve as a
> director, whatever is typed). A real pilot deployment MUST be served over **TLS only**
> (the localhost demo is fine). Full user/password login is the named **v2** sequel, built
> behind the same frontend `authHeader()` seam + the backend `get_current_principal`
> dependency.

> **Reseed (test / demo loop).** Each approve/cancel consumes the run, and the `audit_log` is
> **append-only** (a tamper-evidence trigger, PLAN-0047) so a run can't be reset in place — you
> seed a NEW one with the one-command helper (**dev/demo only — never run in production**):
> `python scripts/seed_operate_demo.py` (or `python scripts/seed_operate_demo.py my-run-id` for a
> chosen id), then reload the Monitor. A **full** reset = a clean demo DB (drop +
> `alembic upgrade head`) + restart (self-seeds `run-operate-demo`). Field reference:
> `services/api/config.py` (`oct_demo_seed_operate`); seed seam:
> `verticals/procurement/hero_demo/run.py` (`seed_operate_waiting_human_run`); the manual helper:
> `scripts/seed_operate_demo.py`; the executor factory: `register_procurement_procedure_executors`.

> **Security note — Content-Security-Policy (defense-in-depth, PLAN-0054 operate-UI
> review follow-up).** The operate UI holds the operator's pilot API key in
> `sessionStorage` (SD-A login-form). The PLAN-0054 security review verdict was
> **secure-for-pilot** with a *single* defense-in-depth gap: **no CSP**. The static
> server now stamps a strict **`Content-Security-Policy`** on every served UI response
> (`services/api/main.py` — `_OCT_CSP` + the `_StaticFilesWithCSP` mount):
> `default-src 'self'` with only the relaxations the bundle actually needs —
> `style-src 'unsafe-inline'` (the runtime `<style>` injection + inline `style=` attrs),
> `img-src 'self' data:`, and `script-src` / `connect-src` / `font-src` all `'self'`,
> plus `object-src 'none'` / `base-uri 'self'` / `frame-ancestors 'none'`. It is the
> safety net that would **contain** a future `html:`/`innerHTML` XSS regression: script
> execution and network egress are pinned to same-origin, so the `sessionStorage`
> credential cannot be exfiltrated to an attacker origin (a "credential exfiltration" bug
> becomes a contained one). It is **scoped to the static mount** (a `StaticFiles`
> subclass, not global middleware), so FastAPI's `/docs` + `/redoc` (which load Swagger/
> ReDoc from a CDN + inline scripts) are untouched. When rehearsing, confirm **zero CSP
> violations** in the browser console across every view (A–H + Story mode + the Map).

---

## 4. Open it in a browser

uvicorn binds `127.0.0.1` by default. **WSL2 forwards `localhost` to Windows**,
so a Windows browser reaches the WSL service at `http://localhost:<port>` with no
extra setup. The UI is served at `/`; it fetches the relative API paths
(`/meta`, `/objects`, `/recommendations`, `/query`) same-origin (no CORS).

- energy → http://localhost:8000
- supply_chain → http://localhost:8098
- aquaculture → http://localhost:8099

> Only need the **Windows LAN IP** / `--host 0.0.0.0` when a **phone** must reach
> it (e.g. the PLAN-0014 tap-link). For desktop browsing, `localhost` is enough.
> Phone reachability is covered in `docs/runbooks/arm-plan-0014-telegram.md` §6.

---

## 5. Enable NL query (feature C) — power on MS-S1 first

NL query needs the local LLM. With MS-S1 off it returns the ungrounded
"couldn't translate…" answer (by design — `services/engine/nl_query.py`
`answer_question` catches the unreachable error and degrades safely).

1. **Power on MS-S1 MAX** (Ollama at `http://192.168.1.133:11434` — IP, not
   hostname; see memory `project_ms_s1_ollama_reachability`). Confirm:
   ```bash
   curl -s -m3 http://192.168.1.133:11434/api/tags >/dev/null && echo REACHABLE || echo DOWN
   ```
2. **Warm the model** — open **http://localhost:8000/warm** in the browser (or
   `curl`). Blocks ~11–13 s cold, instant if already resident; returns
   `"loaded": true`. (`GET /warm` is intentional so a phone/address-bar tap can
   trigger it — `services/api/routers/admin.py`.)
3. **Ask questions in Screen C.** Known-good (PLAN-0013 session 28): *"How many
   shipments are there?"* → grounded → `COUNT Shipment` → **4**, with
   source-object-id chips. Also ask a **no-data** question to show it returns
   "no data," **never an invented fact** (the anti-hallucination credibility
   point).
4. **Free the VRAM when done:** open **http://localhost:8000/sleep**.

> If MS-S1 is off and you want a ping-to-warm reminder wired up, that is the
> separate PLAN-0014 arming step — `docs/runbooks/arm-plan-0014-telegram.md`.

### 5a. In-UI MS-S1 control — the demo-shell affordance (PLAN-0018)

Steps 1–4 are the address-bar path. The demo shell also carries an **in-header
MS-S1 control** (top-right, beside Refresh) so the operator manages the LLM
without leaving the demo — the **pre-demo warm checklist**:

1. **Watch the `MS-S1` indicator.** It polls `GET /llm/status` every 5 s
   (read-only — the poll **never** warms the model) and shows the residency of
   the pinned recommender (`gpt-oss:20b`):
   - **RESIDENT** (green) — loaded; hover for the keep_alive remaining-time.
   - **COLD** (amber) — host reachable, model not loaded → click **Warm**.
   - **OFFLINE** (red) — MS-S1 unreachable (power it on — step 1 above).
   - **ERROR** (red) — reachable but erroring (never shown as a false COLD).
   - **—** (grey) — the demo backend itself isn't answering `/llm/status`.
2. **Click `Warm`** — fires `GET /warm?wait=false` and shows a pulsing
   **WARMING…** state (non-blocking — no ~11 s page freeze), flipping to
   **RESIDENT** when the model lands (~13 s from cold).
3. **Confirm RESIDENT before the stakeholder types** — NL query (§5) and the
   PLAN-0017 live co-creation extraction both need the model resident.
4. **`Sleep`** frees the VRAM — **guarded**: one click arms (`Confirm?`), a
   second within 4 s executes (a stray single click can't unload mid-demo).

> This affordance is the **PLAN-0017 seam**: the live co-creation flow (§5b)
> reuses this same status poll + warm control to confirm MS-S1 is resident
> before the stakeholder describes their operation.

### 5b. Live co-creation — build vertical #4 from a stakeholder's description (PLAN-0017)

The headline moment: after showing a pre-built vertical (e.g. aquaculture #3, §3a),
ask the stakeholder *"…and what's **your** operation?"* and build a runnable Mirror
demo of **their** domain on the spot — via the **"Build a Vertical" (E)** tab in the
demo shell. The face is a *caller*: a local LLM drafts a partner-input package, a
**mandatory human review/edit gate** lets the operator correct it, and it invokes
`vero-lite new-vertical` **unchanged** (the same engine as §3a).

**Prereq:** MS-S1 resident (§5 / §5a) for the live extraction. If it is cold or
unreachable the flow degrades gracefully (see *Fallbacks* below) — the demo never
depends on extraction succeeding.

1. Open any running demo (e.g. energy on 8000) and click the **E · Build a Vertical**
   tab. The capture screen shows an **MS-S1 hint** — confirm it reads
   *"resident — extraction ready"* (else warm it via §5a, or use a fallback).
2. Type the stakeholder's domain in plain language — assets + where they sit, what
   breaks and why it hurts, what reading crosses what threshold (a **crash** = value
   falling, or an **overrun** = value rising), and the corrective action. Click
   **Extract draft (MS-S1)**.
3. **Review the gate** (the one non-negotiable). Every slot is editable — namespace,
   the metric + threshold + **breach direction**, the Asset/Site roles and their
   properties/enums, the action vocabulary, and the **recovery value** (set it on the
   *safe* side of the threshold so Execute visibly recovers the incident — e.g. for a
   `below` crash at 4, a recovery above 4). The **source badge** always shows which
   dataset is in play: `MS-S1 EXTRACTION` / `PREBAKED STARTER` / `MANUAL ENTRY`.
4. Click **Confirm & build vertical #4** — the only path to generation (there is no
   auto-confirm). The face assembles the OCT ontology, invokes the engine, and shows
   the result: the **env block**, the scaffold written, and the boot checklist.
5. **Boot #4 on a separate port** so the showcase vertical stays up beside it — the
   same pattern as §3/§3a. Paste the result's env block into a uvicorn run on a fresh
   port. Worked example (verified live, session 39 — a district-heating *below*-crash
   built from free text):
   ```bash
   cd ~/work/vero-lite
   OCT_VERTICAL=district_heating \
   OCT_RECOMMEND_THRESHOLD=4 \
   OCT_RECOMMEND_DIRECTION=below \
   OCT_RECOMMEND_ENTITY_TYPE=BoilerPlant \
   OCT_RECOMMEND_ENTITY_ID_FIELD=boiler_plant_id \
   OCT_RECOMMEND_LABEL="steam_pressure" \
   OCT_RECOVERY_VALUE=6 \
   OCT_RECOVERY_DESCRIPTION="Boiler steam pressure restored above the 4 bar safe minimum." \
   OCT_DEMO_TIME_ANCHOR=true \
   uv run uvicorn services.api.main:app --port 8100
   ```

   > **Port choice — avoid a collision.** Use a *free* port for #4 (`8100` here).
   > `8099` is the §3a aquaculture showcase, so reusing it collides with the very
   > vertical you keep up *beside* #4. (The session-39 live run used 8099 only
   > because no other demo was up then.)

   Open the new port → vertical #4 runs all three OCT features: the map renders from
   the Site-role geo, NL query answers (MS-S1), and the breach fires
   breach → recommend → approve → execute. (Session-39 live: `BoilerPlant 01` +
   `Neighborhood 01`, 1 recommendation `proposed` from the 3.2 < 4 bar crash with an
   `ontology_query → llm_inference → rule_check` trace, NL query *"There is one boiler
   plant: BoilerPlant 01"* grounded, Approve → Execute → `executed`.)

**Fallbacks (AC-4 — the demo never stalls).** If MS-S1 is cold/unreachable or the
extraction looks wrong:
- **Use a starter** — pick a prebaked, source-tagged package (`solar_farm` overrun /
  `water_utility` crash) and edit from there.
- **Enter manually** — a blank gate you fill in directly (the pure-form path).
Both land in the *same* editable gate; the source badge flips to `PREBAKED STARTER` /
`MANUAL ENTRY` so it is always clear the package is not a live extraction.

**Cleanup (ephemeral #4).** Generation writes `verticals/<ns>/` and code-mods
`services/api/main.py` (one registrar row; `verticals/<ns>/generated/` is gitignored).
The built vertical is a **demo output**, not a committed artifact (PLAN-0017
Out-of-Scope: no intake history store) — to discard it after the demo:
```bash
git checkout -- services/api/main.py && rm -rf verticals/<ns>
```
(Stop the #4 uvicorn first — Ctrl-C, or `pkill -f "uvicorn services.api.main:app --port 8100"`.)

---

## 6. What each screen shows — the design-partner narrative

- **Screen A (map).** The legend / status enums render from `/meta`, **not**
  hard-coded labels. Pitch: *"the map already understands your domain — you just
  give us the ontology."*
- **Screen B (anomaly → decision).** The reasoning-trace steps + the
  Approve/Reject/Execute gate = **governance + human-in-the-loop** (north-star
  Pillars 5 + 9). Pitch: *"every automated decision is explainable and gated —
  not a black box."*
- **Screen C (NL query).** The source-object chips under each answer =
  **anti-hallucination** — answers are drawn from real records, and "no data"
  beats a confident lie. (Needs MS-S1 — §5.)
- **Screen D (flow).** Ingest → Condition → Process → Result as one visible
  pipeline. Pitch: *"the data you already have → a governed decision, end to
  end."*
- **Screen E (Build a Vertical).** Not a view of the running vertical — the
  **live co-creation** tab: the stakeholder describes a *new* operation in plain
  language and a Mirror demo of it is generated on the spot (engine + the human
  review/edit gate + boot). Pitch: *"…and that's **your** operation — let's build
  it right now."* Full mechanics: §5b · narrative + show-sequence: §6b.

Running **the ports side by side** (§2 + §3 + §3a) makes the core thesis
concrete: identical UI build, different operations, zero per-vertical UI code.

> **How to actually narrate it.** §6 above is the per-screen reference; the
> story to *tell a stakeholder* — scene → screens → the number — lives in
> **§6a (per-vertical scripts, ไทย/EN)** and **§6b (the Screen-E co-creation
> moment)**.

---

## 6a. Per-vertical narratives — the story to tell (ไทย / EN)

> **Tell the pain before the feature.** Every pre-built vertical follows the same
> 4-beat arc — **the scene → Screen A (map) → Screen B (the killer moment) →
> Screens C/D → the number** — only the domain changes. Open with the 2-a.m.
> failure, *then* let the screens be the answer. Don't open with "this is our
> ontology engine." Below is a script per vertical, grounded in the exact
> on-screen values (§2 / §3 / §3a), in **English** and **ไทย**. The fourth
> "vertical" — the one you build live — is **§6b**.
>
> เล่า **"ความเจ็บปวด" ก่อน "ฟีเจอร์"** เสมอ — ทุก vertical ใช้โครงเดียวกัน:
> **ฉาก → Screen A → Screen B (จุดพีค) → Screen C/D → ตัวเลข** เปลี่ยนแค่ domain.

### 1 · Energy — regional energy operator (§2)

**English**
- **Scene —** a battery-storage fleet across substations and microgrids. A
  battery bank starts overheating at night; left unchecked, thermal runaway means
  fire and a forced outage. Operators watch SCADA and tribal know-how — no single
  live map, no auditable record of who acted and why.
- **On screen** (verified §2): two sites — *North Substation*, *Riverside
  Microgrid* — and four assets. The flagged action is **over-temperature on
  `asset-battery-01`**, reasoning trace `measured_value 96.5 °C ≥ threshold 90.0`
  (an **above** breach), confidence 0.8; the inverter alarm was the precursor.
  Approve → Execute resolves it.
- **Say:** *"The map already understands your grid — you just gave us the
  ontology. Every automated call is explainable and gated: the operator approves,
  the system acts, and it's all on the record."*

**ไทย**
- **ฉาก —** ฟลีตแบตเตอรี่กักเก็บพลังงานกระจายตามสถานีไฟฟ้าย่อย/ไมโครกริด คืนหนึ่ง
  แบงก์แบตเตอรี่เริ่มร้อนเกิน ถ้าปล่อยไว้ thermal runaway = ไฟไหม้ + ไฟดับทั้งโซน
  วันนี้คนคุมดู SCADA กับความเก๋า ไม่มีแผนที่รวมสักจอ ไม่มีบันทึกว่าใครทำอะไรเพราะอะไร
- **บนจอ** (verified §2): 2 ไซต์ — *North Substation*, *Riverside Microgrid* — กับ
  4 asset เหตุที่ถูกชูคือ **over-temperature ที่ `asset-battery-01`** trace
  `วัดได้ 96.5 °C ≥ เกณฑ์ 90.0` (breach แบบ **above** ค่าพุ่งเกิน) confidence 0.8;
  มี inverter alarm เป็นสัญญาณนำ กด Approve → Execute เพื่อปิดเหตุ
- **พูดว่า:** *"แผนที่เข้าใจกริดของคุณอยู่แล้ว คุณแค่ให้ ontology มา ทุกการตัดสินใจ
  อธิบายได้และมีด่านมนุษย์กั้น — operator อนุมัติ ระบบลงมือ และทุกอย่างถูกบันทึกไว้"*

### 2 · Supply chain — industrial cold-chain operator (§3)

**English**
- **Scene —** refrigerated shipments (vaccines, produce, frozen, biologics)
  moving between cold hubs. A reefer door is left ajar; cargo temperature climbs
  past the safe 2–8 °C band; a vaccine load worth a fortune spoils in transit,
  with regulatory fallout. Today: spreadsheets and phone calls — found out too
  late.
- **On screen** (verified §3): two facilities — *Central Cold Hub*, *Northern
  Distribution Center* — and four shipments. The flagged action is **cold-chain
  temperature breach on `shipment-pharma-01`**, trace `measured_value 14.6 °C ≥
  threshold 8.0` (an **above** breach), confidence 0.8; the door-open alarm was
  the precursor. Execute lands the recovery reading at **4.2 °C** (back inside
  2–8 °C).
- **Say:** *"Same console, a completely different operation — a shipment instead
  of a battery, zero UI code changed. Catch the excursion in transit, reroute or
  hold before the cargo is lost, and keep an audit trail the regulator accepts."*

**ไทย**
- **ฉาก —** ตู้แช่เย็นขนส่ง (วัคซีน/ผัก/ของแช่แข็ง/ชีววัตถุ) วิ่งระหว่างฮับความเย็น
  ประตู reefer ถูกเปิดค้าง อุณหภูมิสินค้าไต่เกินช่วงปลอดภัย 2–8 °C วัคซีนล็อตเป็นล้าน
  เสียกลางทาง พ่วงปัญหา compliance วันนี้ใช้ spreadsheet กับโทรศัพท์ รู้ตอนสายไปแล้ว
- **บนจอ** (verified §3): 2 facility — *Central Cold Hub*, *Northern Distribution
  Center* — กับ 4 shipment เหตุที่ถูกชูคือ **cold-chain temperature breach ที่
  `shipment-pharma-01`** trace `วัดได้ 14.6 °C ≥ เกณฑ์ 8.0` (breach แบบ **above**)
  confidence 0.8; มี door-open alarm เป็นสัญญาณนำ กด Execute แล้วค่า recovery ลงมาที่
  **4.2 °C** (กลับเข้าช่วง 2–8 °C)
- **พูดว่า:** *"คอนโซลเดียวกัน แต่คนละการดำเนินงาน — เป็น shipment แทนแบตเตอรี่ โดยไม่
  แตะ UI code เลย จับ excursion ได้กลางทาง รีบ reroute หรือ hold ก่อนของเสีย แล้วมี
  audit trail ที่ผู้คุมกฎยอมรับ"*

### 3 · Aquaculture — SE-Asian shrimp/finfish farm (§3a) · the headline #3

**English**
- **Scene —** a mid-market shrimp farm, dozens of ponds. Dissolved oxygen swings
  hardest at night and after feeding; an aerator fails unnoticed at 2 a.m. and an
  entire pond's crop dies within 1–2 hours — a five-figure loss per pond per
  cycle. Today: manual DO meters and night-watch instinct.
- **On screen** (verified §3a): two farms — *Bayfront Shrimp*, *Riverside
  Tilapia* — and four ponds (3 active, *pond-05* fallow). The flagged action is
  **dissolved-oxygen crash on `pond-07`**, trace `measured_value 3.2 mg/L ≤
  threshold 4.0 · direction: below` — the **first below-threshold breach** (a
  *crash*: the value falls, not an overrun). Execute lands recovery at **5.5
  mg/L** (back above the 4 mg/L line). The real-world action it represents: start
  the emergency aerator (dispatch a technician if the aerator itself failed).
- **Why this one leads (2026):** after the eFishery collapse (founder sentenced;
  ~US$600M inflated revenue) the sector's trust is shattered — a
  reasoning-trace-first, auditable, mid-market product is the *anti-eFishery*, and
  the founder is in-region (SE Asia / Thailand) to sanity-check it.
- **Say:** *"A living operational map, a plain-language 'which ponds are low on DO
  right now?', and an AI recommendation you can see the reasoning behind — not
  hype, an audit trail."*

**ไทย**
- **ฉาก —** ฟาร์มกุ้ง mid-market บ่อเป็นสิบ DO แกว่งแรงสุดตอนกลางคืน + หลังให้อาหาร
  aerator พังตอนตี 2 โดยไม่มีใครรู้ ทั้งบ่อตายใน 1–2 ชม. = เสียหลักหมื่น–แสนต่อบ่อ
  ต่อรอบ วันนี้ใช้เครื่องวัด DO มือถือ + สัญชาตญาณคนเฝ้ายาม
- **บนจอ** (verified §3a): 2 ฟาร์ม — *Bayfront Shrimp*, *Riverside Tilapia* — กับ
  4 บ่อ (3 active, *pond-05* fallow) เหตุที่ถูกชูคือ **dissolved-oxygen crash ที่
  `pond-07`** trace `วัดได้ 3.2 mg/L ≤ เกณฑ์ 4.0 · direction: below` —
  **breach แบบต่ำกว่าเกณฑ์ตัวแรก** (เป็น crash ค่าตก ไม่ใช่ค่าพุ่ง) กด Execute แล้ว
  recovery ขึ้นมา **5.5 mg/L** (เหนือเส้น 4) การแก้ที่มันแทน: เปิด emergency aerator
  (ส่งช่างถ้า aerator เองพัง)
- **ทำไมตัวนี้นำ (2026):** หลัง eFishery ล่ม (ผู้ก่อตั้งโดนตัดสิน รายได้ปลอม ~600
  ล้าน$) วงการขาดความเชื่อใจ — product ที่ reasoning-trace-first + auditable +
  ขนาดพอดี mid-market คือ "ตรงข้าม eFishery" และผู้ก่อตั้งอยู่ในภูมิภาค (อาเซียน/ไทย)
  sanity-check ได้
- **พูดว่า:** *"แผนที่ปฏิบัติการที่มีชีวิต ถามเป็นภาษาคนว่า 'บ่อไหน DO ต่ำตอนนี้?'
  และคำแนะนำ AI ที่เห็น reasoning เบื้องหลัง — ไม่ใช่การปั่น แต่เป็น audit trail"*

> **Why aquaculture is the *below*-breach showcase.** Energy + supply_chain both
> breach **above** (something gets too hot). Aquaculture breaches **below**
> (oxygen crashes) — showing it proves the engine handles *both* alert directions
> from config alone (`OCT_RECOMMEND_DIRECTION`), the cleanest "your domain, not
> ours" proof before you hand the stakeholder Screen E.

---

## 6b. Screen E · Build a Vertical — the live co-creation moment (the closer)

> Screens A–D show a vertical **you** pre-built. **Screen E builds the
> stakeholder's *own* vertical, live.** It is the demo's closer — it converts
> "nice product" into "that's **my** operation." The mechanics (warm, extract,
> gate, confirm, boot, clean up) are in **§5b**; this section is the **narrative +
> where it sits in the show**.
>
> Screen A–D โชว์ vertical ที่ **คุณ** build ไว้ก่อน **Screen E สร้าง vertical ของ
> stakeholder เองสดๆ** — เป็นไม้ปิดของ demo เปลี่ยนจาก "product ดีนะ" เป็น "นี่มัน
> งานของฉันนี่" กลไกอยู่ใน **§5b** ตรงนี้คือ **เรื่องเล่า + ตำแหน่งในการโชว์**

### The show sequence — where Screen E fits in the #3 demo

**English**
1. Run the headline vertical #3 (aquaculture, §3a) and walk Screens **A → B → C →
   D** — the full §6a story. Land the killer moment (the `pond-07` crash,
   Approve → Execute → recovery 5.5 mg/L).
2. **Pause and pivot — the golden question:** *"That's a shrimp farm… and what's
   **your** operation? What value, when it crosses a line, costs you money?"* Let
   them answer out loud.
3. **Switch to the `E · Build a Vertical` tab** (top of the demo shell). Confirm
   the MS-S1 hint reads *"resident — extraction ready"* (warm it first via §5a —
   this is the pre-demo checklist; if cold, use a fallback, step 6).
4. Type *their* domain in plain language — assets + where they sit, what breaks
   and why it hurts, the metric + threshold + **direction** (crash = value
   falling / overrun = value rising), the corrective action. Click **Extract
   draft (MS-S1)**.
5. **Narrate the review/edit gate out loud — it's a feature, not a delay:** *"the
   AI proposed this ontology; nothing generates until you confirm it, and you can
   correct any slot."* Point at the source badge (`MS-S1 EXTRACTION`). This is the
   mandatory human gate (AC-2) — the anti-"black box" promise made literal.
6. Click **Confirm & build vertical #4** → show the result (env block, scaffold
   written, boot checklist). *Fallback if MS-S1 is cold or the draft looks wrong:*
   **Use a starter** (`solar_farm` / `water_utility`) or **Enter manually** — both
   land in the same gate; the demo never stalls (§5b Fallbacks).
7. **Boot #4 on a free port (8100)** and open it beside #3 — now *their*
   operation runs the same **A → B → C → D**. *"You described it sixty seconds
   ago; here it is, live — same engine, your assets."*
8. After the demo, revert the ephemeral #4 (§5b cleanup).

**ไทย**
1. รัน vertical #3 (aquaculture, §3a) แล้วเดิน Screen **A → B → C → D** ครบตาม
   เรื่อง §6a ปิดด้วยจุดพีค (crash ที่ `pond-07`, Approve → Execute → recovery
   5.5 mg/L)
2. **หยุดแล้วหันมา — ประโยคทอง:** *"นี่คือฟาร์มกุ้ง… แล้ว **'งานของคุณ'** คืออะไร
   ล่ะครับ? ค่าอะไรที่พอข้ามเส้นแล้วทำให้คุณเสียเงิน?"* ให้เขาตอบออกมาดังๆ
3. **สลับไปแท็บ `E · Build a Vertical`** (บนสุดของ demo shell) เช็คว่า hint MS-S1
   ขึ้น *"resident — extraction ready"* (warm ก่อนตาม §5a — เป็น checklist ก่อน
   demo; ถ้า cold ใช้ fallback ข้อ 6)
4. พิมพ์ domain ของ *เขา* เป็นภาษาคน — asset + อยู่ที่ไหน, อะไรพังและเจ็บยังไง,
   metric + threshold + **direction** (crash = ค่าตก / overrun = ค่าพุ่ง), และ
   action ที่ใช้แก้ กด **Extract draft (MS-S1)**
5. **เล่า review/edit gate ออกมาดังๆ — นี่คือฟีเจอร์ ไม่ใช่ความช้า:** *"AI เสนอ
   ontology นี้ ระบบจะยังไม่สร้างจนกว่าคุณจะยืนยัน และคุณแก้ได้ทุกช่อง"* ชี้ที่
   source badge (`MS-S1 EXTRACTION`) นี่คือด่านมนุษย์บังคับ (AC-2) — คำมั่น
   "ไม่ใช่กล่องดำ" ที่จับต้องได้
6. กด **Confirm & build vertical #4** → โชว์ผลลัพธ์ (env block, scaffold, boot
   checklist) *Fallback ถ้า MS-S1 cold หรือ draft ผิด:* **Use a starter**
   (`solar_farm` / `water_utility`) หรือ **Enter manually** — ลงที่ gate เดียวกัน
   demo ไม่มีวันค้าง (§5b Fallbacks)
7. **Boot #4 ที่ port ว่าง (8100)** เปิดวางข้าง #3 — ตอนนี้งานของ *เขา* รันครบ
   **A → B → C → D** *"คุณเพิ่งพูดเมื่อหกสิบวินาทีที่แล้ว นี่ไงครับ — engine เดียวกัน
   สินทรัพย์ของคุณ"*
8. หลัง demo ค่อย revert #4 ที่เป็น ephemeral (§5b cleanup)

### The closing line

- **EN:** *"Every other vendor shows you their demo. We just built **yours** — in
  the room, in a minute, with you correcting the AI as it went."*
- **ไทย:** *"เจ้าอื่นโชว์ demo ของเขา เราเพิ่งสร้าง demo ของ **คุณ** — ในห้องนี้
  ในหนึ่งนาที โดยคุณเป็นคนแก้ AI ไปด้วยกัน"*

> **One-line how-to (cross-ref §5b):** warm MS-S1 (§5a) → `E` tab → describe →
> **Extract** → review/edit gate → **Confirm & build** → boot on **8100** → §5b
> cleanup. Never skip the gate; never reuse port 8099 (that's the §3a showcase).

---

## 6c. Story mode — the guided 7-scene arc (hotkey **S**, PLAN-0033 Phase C)

> §6a/§6b drive the **console** (Views A–E) by hand. **Story mode** is a separate,
> narration-paced **7-scene overlay** (`view-story.js`, PLAN-0033 Phase C) that tells
> the whole pitch as one arc — pain → governance → pipeline → live intake → the honest
> number → breadth → "how it works." It is an **additive overlay** (it never replaces
> the console — **Esc** returns you to whatever view was open), runs on synthetic
> Tier-1 mirror data, and is **offline** (no MS-S1 dependency; see the honesty note).

**Pre-demo checklist (same as §5a).** Pre-warm MS-S1 (header **Warm**, or §5) and confirm
the indicator reads **RESIDENT** before you start. Story mode runs fine cold, but scene 4's
readiness pill reads the real `GET /llm/status` — **green ("resident") looks best on stage**.

**Launch.** Press **S** anywhere in the demo (or click the header **Story** button). The
`S` hotkey is app-lifetime and ignores typing into inputs, so it never collides with the
A–E view keys.

**Drive it** (narration-paced — click/keyboard, never a timer that desyncs live Q&A):

| Key | Action |
|---|---|
| **→** | next step within the scene |
| **Space** | play / pause auto-advance (~1.1 s/step) |
| **]** / **[** | next / previous scene |
| **R** | restart the current scene |
| **Esc** | exit story mode (returns to the console) |

The arc (**Story · Aquaculture**): **1 Hook** (2 a.m. DO crash, ฿/biomass at stake) →
**2 Govern** (decision card + the 🌟 fail-safe self-catch — toggle *"What if the AI is
unsure?"*) → **3 Pipeline** (the branching DAG + Proposed→Approved→Executed control
surface; toggle **"Simulate LLM fault"** to show the LLM → deterministic rule fail-safe
reroute that *still* needs your signature) → **4 Live intake** (dual-path: "Use cached
draft" / "Go live") → **5 Before/After** (the one honest number) → **6 Breadth** (swap
across verticals + "Compare all" matrix + real-YAML) → **7 Appendix** (how the YAML
generates the whole stack).

> **Honesty (don't over-claim on stage).** Scene 4's **"Go live"** button is a *scripted*
> resilience beat — it shows a hard-timeout → cached-draft fallback; it does **not** make
> a real MS-S1 extraction call (real wiring is deferred). The readiness pill *does* do a
> real safe `GET /llm/status` read. Scene 5's "**0 of 40**" is the in-repo B-γ finding
> (`benchmarks/procedure_baseline/REPORT.md` §B-3), framed as *robustness*, not a
> leaderboard %.

**Editing the demo assets — the `?v=` cache-bust convention (operator gotcha).** The
browser **caches** the static JS/CSS, so after you edit any file under
`services/api/static/assets/`, a normal reload serves the **stale** asset (it looks like
"my change didn't land"). Bump the shared `?v=` token in `services/api/static/index.html`
(e.g. `?v=c8` → `?v=c9`) on **every** asset edit so the browser refetches; verify with a
cache-busted `fetch` + a runtime probe (`window.OCT.ViewStory._probe()` returns
`{open, scene, step, motion}`), never "reload = fresh."

---

## 6d. Procurement story — the 5 operator surfaces (PLAN-0036 Stage 1)

> The **4th vertical** is a **procurement** scene group appended to the same story
> overlay (scenes 8–12 of the 12). It is **not** a re-skin of the aquaculture arc —
> it is a procurement operator's **round-trip** (worklist → approve → monitor), the
> concrete proof that the same engine runs a governed sourcing workflow. Pitch
> target: **Fastenal Thailand** (auto-parts manufacturing, EEC); the UI is **Thai-
> localized** and all data is **abstract** (no partner brand). Runs offline on
> synthetic Tier-1 data, same as the aquaculture arc.

**Reach it.** Press **S**, then **]** to page past the 7 aquaculture scenes to the
procurement group (or click the scene dots 8–12). The header eyebrow flips to
**"Story mode · Procurement (Fastenal TH)."**

**The hero:** a critical CNC machining center fails, line down, spare out of stock
→ governed emergency sourcing. The arc (**scenes 8–12**):

| # | Surface | What to show |
|---|---------|--------------|
| 8 | **Worklist / inbox** | the operator's home — urgency-sorted queue; the CNC emergency (red) on top, the calm reorder below |
| 9 | **Process timeline** | the 7-step pipeline; rule gates auto-resolve (gray, 🔒), and it **stops at "⏸ รอการตัดสินใจของคุณ"** at `approve` — the bottleneck is a human gate, by design |
| 10 | **Approval "money screen"** | the one screen where it all converges: AI exec-summary (editable) · per-criterion compliance (incl the cert-blocked quote) · DOA ladder (฿2.15M → **ผอ.**) · emergency-waiver banner · supplier/RFQ compare · SoD · approve/reject |
| 11 | **Graduation moment** | step through it: an **"AI draft"** justification (blue) → a human edit → **approve** → the card **flips to solid green "human-approved · ผอ. · time"**. This *is* governed ≠ generated, made visible |
| 12 | **Monitoring dashboard** | real KPIs (req-to-PO cycle · rush-freight avoided · stockout · maverick · %on-contract — each value + trend + target) · emergency-waivers-used (watched) · the **AI-assist throughput** panel: *"AI drafted N · 0 supplier-selections · 0 approvals"* |

**The three visual registers (look for them on every surface).** **AI-assist** =
blue, "AI draft" (advisory, editable) · **rule-decided** = gray + 🔒 (deterministic,
names the rule) · **human-approved** = green + name·role·time (accountable). The line
to land: *the AI drafts and summarises; the rules and the human decide.*

> Same `?v=` cache-bust + `_probe()` teardown conventions as §6c apply (the
> procurement scenes are in the same `view-story.js`).

---

## 7. Stop / clean up

- Stop a server: **Ctrl-C** in its terminal.
- The Approve→Execute round-trips append rows to the demo Postgres DB
  (`recommended_action`, `alert`). This is expected and harmless — `/objects` is
  served from the synthetic adapter, so the demo content is unchanged on the next
  start, and `/recommendations` regenerates the action fresh **per process
  start**.
- With `OCT_DEMO_TIME_ANCHOR=true` (§9), the anchored timestamps and the
  execute-time recovery reading are **per-process** too: a **restart resets** the
  incident to unresolved and re-anchors it to the new start. So to re-rehearse
  the loop from the top, just restart uvicorn (no DB cleanup needed).

---

## 8. Troubleshooting

- **`/recommendations` is slow.** With MS-S1 **on**, the first call warms +
  generates (LLM path) and can take ~10–60 s; subsequent calls are fast while the
  model stays resident (`OLLAMA_KEEP_ALIVE`, default 30m). With MS-S1 **off**, the
  unreachable connection fails fast and the rule fail-safe answers immediately.
- **NL query always says "couldn't translate…".** MS-S1 is unreachable or not
  warmed — do §5. (Forcing `LLM_BACKEND=hosted` does **not** help — it is a
  seam-only stub; the demo path is `local`.)
- **Port already in use.** Pick another `--port`; check with
  `ss -ltnp | grep :8000`.
- **`OCT_VERTICAL=... is not a registered vertical`.** `energy`, `supply_chain`,
  and `aquaculture` are registered (`services/api/main.py` `_VERTICAL_REGISTRARS`);
  `vero-lite new-vertical` code-mods that dict to add more.
- **Live co-creation (§5b): `POST /intake/generate` returns 409.** The namespace
  already exists on disk — you built this domain in an earlier rehearsal and did
  not clean it up. Pick a new namespace, or discard the previous build first (the
  §5b cleanup block: `git checkout -- services/api/main.py && rm -rf verticals/<ns>`).
  `force=true` overwrites but is deliberately **not** the demo default (it would
  clobber an existing vertical silently — AC-5).
- **DB errors on Execute.** Run `uv run alembic upgrade head` (§1). The test suite
  uses a disposable `<db>_test` DB and never touches the demo DB (memory
  `project_test_suite_drops_demo_db`).

---

## 9. The live-time decision loop (PLAN-0015)

`OCT_DEMO_TIME_ANCHOR=true` turns the static incident into a **live** one so the
demo plays as *incident → human decision → resolution* in real time. Off by
default (so `synthetic.py` stays deterministic for tests); the demo box runs it
**on**. `.claude/launch.json` already sets it for every demo config.

**What changes with the flag on:**

1. **Anchored to now.** Each `uvicorn` run shifts the `OperationalEvent`
   timestamps so the **breach ≈ server start** (relative spacing preserved). The
   timeline reads as "this is happening now," not a fixed May date. Re-anchors
   every run.
   > **Tail-beat note (PLAN-0015 fast-follow, #144).** The breach is deliberately
   > the **final** beat in each synthetic timeline — earlier events (e.g. the
   > energy inverter alarm, the supply_chain reefer door-open alarm) read as
   > *precursors* leading up to it. Anchoring the breach to "now" therefore leaves
   > **0 events in the future** on either vertical. Before #144 both datasets had
   > events *after* the breach, which anchored into the future and showed up as
   > future HH:MM labels on the all-sites Operational Timeline; that artifact is
   > now gone.
2. **The loop closes on Screen A.** Approve then Execute the recommendation in
   **Screen B**; return to **Screen A** and the Operational Timeline now shows:
   - the breach marker turned **green / ✓** (the red pulse stops) + a **Resolved**
     chip in the timeline head;
   - **approve / execute** markers at their real click-times on the rail;
   - a **recovery reading** (the safe-range value) that lands as the *visible
     effect of Execute* — it isn't pre-baked, it appears only after you act;
   - the map node's anomaly ring goes **static green**, and the detail panel
     banner resolves with the recorded Approved / Executed times.
   Approve alone is the **intermediate** state (still unresolved); **Execute** is
   what resolves.

**Clean capture tip.** For a screenshot/recording, run with **MS-S1 off** (rule
fail-safe path, confidence 0.8) so the first `GET /recommendations` answers
instantly — with MS-S1 on, that first call warms the LLM and the map's first
render waits on it (memory: *MS-S1-on blocks the map's first render*). The
anchor + resolution behaviour is identical on both paths.

**Per-vertical recovery wording.** The injected recovery reading is energy-worded
by default; `OCT_RECOVERY_VALUE` + `OCT_RECOVERY_DESCRIPTION` re-skin it for a
second vertical (see the supply_chain command in §3) — config swap, no code.

**Determinism.** With the flag **off**, timestamps are the fixed synthetic values
and no recovery is injected until an Execute — so the full test suite is
unaffected. Field reference: `services/api/config.py`
(`oct_demo_time_anchor`, `oct_recovery_value`, `oct_recovery_description`);
mechanism: `services/engine/demo_events.py`.

---

## References

- Plan (shipped, archived): `docs/plans/done/0013-oct-stakeholder-demo.md` (the
  7-AC demo spec + live verification evidence for both verticals).
- Entry point + vertical registry: `services/api/main.py`.
- Config / env fields: `services/api/config.py` (`oct_vertical`, `oct_recommend_*`,
  `ollama_host`, `llm_backend`).
- Routes: `services/api/routers/{actions,query,admin,intake}.py`
  (`/recommendations` + approve/execute, `POST /query`, `GET /warm` + `/sleep`;
  the live co-creation face = `POST /intake/extract`, `GET /intake/defaults`,
  `POST /intake/generate` — PLAN-0017).
- Recommender + fail-safe: `services/engine/recommender.py` (`_rule_recommend`,
  `RULE_CONFIDENCE = 0.8`).
- NL query engine: `services/engine/nl_query.py` (`answer_question`).
- Ontologies + synthetic scenarios:
  `verticals/{energy,supply_chain,aquaculture}/ontology/*.yaml` +
  `verticals/{energy,supply_chain,aquaculture}/data_adapter/synthetic.py`.
- Scaffolding the next vertical: `vero-lite new-vertical <ns>` (PLAN-0016,
  `services/engine/scaffold.py`); aquaculture is its end-to-end instance.
- MS-S1 reachability: memory `project_ms_s1_ollama_reachability` (IP
  `192.168.1.133`, not hostname).
- Arming the MS-S1-unreachable Telegram ping + phone tap-link / WSL networking:
  `docs/runbooks/arm-plan-0014-telegram.md`.
- ADRs: ADR-005 (OCT pivot), ADR-006 (vertical plugin / template-first), ADR-007
  (RecommendedAction + action loop), ADR-010 (LLM brain-swap + rule fail-safe).
