# Runbook — Run the OCT stakeholder demo (energy + supply_chain)

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
OCT_VERTICAL=energy uv run uvicorn services.api.main:app --port 8000
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
uv run uvicorn services.api.main:app --port 8098
```

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

## 4. Open it in a browser

uvicorn binds `127.0.0.1` by default. **WSL2 forwards `localhost` to Windows**,
so a Windows browser reaches the WSL service at `http://localhost:<port>` with no
extra setup. The UI is served at `/`; it fetches the relative API paths
(`/meta`, `/objects`, `/recommendations`, `/query`) same-origin (no CORS).

- energy → http://localhost:8000
- supply_chain → http://localhost:8098

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

Running **both ports side by side** (§2 + §3) makes the core thesis concrete:
identical UI build, two different operations, zero per-vertical UI code.

---

## 7. Stop / clean up

- Stop a server: **Ctrl-C** in its terminal.
- The Approve→Execute round-trips append rows to the demo Postgres DB
  (`recommended_action`, `alert`). This is expected and harmless — `/objects` is
  served from the synthetic adapter, so the demo content is unchanged on the next
  start, and `/recommendations` regenerates the action fresh **per process
  start**.

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
- **`OCT_VERTICAL=... is not a registered vertical`.** Only `energy` and
  `supply_chain` are registered (`services/api/main.py` `_VERTICAL_REGISTRARS`).
- **DB errors on Execute.** Run `uv run alembic upgrade head` (§1). The test suite
  uses a disposable `<db>_test` DB and never touches the demo DB (memory
  `project_test_suite_drops_demo_db`).

---

## References

- Plan (shipped, archived): `docs/plans/done/0013-oct-stakeholder-demo.md` (the
  7-AC demo spec + live verification evidence for both verticals).
- Entry point + vertical registry: `services/api/main.py`.
- Config / env fields: `services/api/config.py` (`oct_vertical`, `oct_recommend_*`,
  `ollama_host`, `llm_backend`).
- Routes: `services/api/routers/{actions,query,admin}.py`
  (`/recommendations` + approve/execute, `POST /query`, `GET /warm` + `/sleep`).
- Recommender + fail-safe: `services/engine/recommender.py` (`_rule_recommend`,
  `RULE_CONFIDENCE = 0.8`).
- NL query engine: `services/engine/nl_query.py` (`answer_question`).
- Ontologies + synthetic scenarios:
  `verticals/{energy,supply_chain}/ontology/*.yaml` +
  `verticals/{energy,supply_chain}/data_adapter/synthetic.py`.
- MS-S1 reachability: memory `project_ms_s1_ollama_reachability` (IP
  `192.168.1.133`, not hostname).
- Arming the MS-S1-unreachable Telegram ping + phone tap-link / WSL networking:
  `docs/runbooks/arm-plan-0014-telegram.md`.
- ADRs: ADR-005 (OCT pivot), ADR-006 (vertical plugin / template-first), ADR-007
  (RecommendedAction + action loop), ADR-010 (LLM brain-swap + rule fail-safe).
