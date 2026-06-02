# Runbook — Arm PLAN-0014 (MS-S1-unreachable Telegram ping) on the demo box

> **Goal.** Move the PLAN-0014 notify feature from its safe **dormant** default
> to **armed** on the demo box, so that when MS-S1 (the local LLM) is powered off
> and an operator runs an NL query, the operator gets a Telegram ping with a
> tap-to-`/warm` link. This is the only remaining Cray-action before taking the
> 2-vertical demo to design partners.
>
> **Scope of this runbook.** Tailored to the demo box = **this machine
> (Cray-Legion5Pro, WSL2 Ubuntu)** running the OCT API as **bare uvicorn** with a
> local `.env` (per `README.md:62`). docker-compose only runs postgres + redis;
> the API is not containerized.
>
> **Who does what.** A human (Cray) performs every step here — it changes host
> state (`.env` secrets + a running process) outside any repo worktree. Claude
> Code does not edit `.env` (it holds secrets) or restart the demo process.

---

## 0. What "arm" means

The feature is shipped + tested but **off by default** (`telegram_notify_enabled`
defaults to `False` — "default off so dev sessions get no pings",
`services/api/config.py:161`). "Arming" flips the switch and supplies credentials
so the gate opens. The notifier fires **only** when all four conditions hold
(`services/notify/telegram.py:_gates_open`):

```
telegram_notify_enabled == True      ← env TELEGRAM_NOTIFY_ENABLED
AND llm_backend == "local"           ← env LLM_BACKEND (demo default = local)
AND telegram_bot_token != ""         ← env TELEGRAM_BOT_TOKEN
AND telegram_chat_id  != ""          ← env TELEGRAM_CHAT_ID
```

Miss any one → the feature **no-ops silently** (no ping, no error). All four →
**armed**.

---

## 1. Preconditions

- [ ] `llm_backend` is `local` (the demo uses MS-S1). The arming check in §4.1
      confirms this.
- [ ] The existing harness Telegram **bot token** + **chat id** are on hand
      (PLAN-0014 reuses the harness bot per ADR-013 D5 — no new bot).
- [ ] MS-S1 is reachable at `http://192.168.1.133:11434` for the `/warm` checks
      (IP, not hostname — see memory `project_ms_s1_ollama_reachability`). The
      *ping* path is verified with MS-S1 simulated-down in §4.5.
- [ ] You know the **actual port** uvicorn binds. `README.md:63` shows `:8000`;
      the session-30 handoff mentioned `:8096`. Confirm before setting
      `OCT_PUBLIC_BASE_URL` (wrong port → dead tap-link). Confirm with:
      ```bash
      ss -ltnp | grep uvicorn      # shows the listen address:port
      ```

---

## 2. Determine the public base URL (the phone-reachable address)

The Telegram ping appends a tap-link `{OCT_PUBLIC_BASE_URL}/warm`. It must be
reachable **from your phone on the LAN** — so it is the **Windows LAN IP**, never
`localhost` and never the WSL `172.x` address.

1. Windows LAN IP (run in **PowerShell**):
   ```powershell
   ipconfig    # IPv4 Address of the active Wi-Fi/Ethernet adapter, e.g. 192.168.1.50
   ```
2. WSL IP (run in **WSL**, only needed for the port-proxy path in §6):
   ```bash
   ip addr show eth0 | grep 'inet '
   ```

`OCT_PUBLIC_BASE_URL` = `http://<windows-lan-ip>:<port>` (e.g.
`http://192.168.1.50:8000`).

> WSL networking is the one real wrinkle here. A phone cannot reach a WSL
> service via the Windows IP by default. Fix it once via **§6** (mirrored
> networking — simplest on Win11, or a `netsh` port-proxy). Do §6 before relying
> on the tap-link.

---

## 3. Set the env vars

Append to `~/work/vero-lite/.env` (gitignored — the only place secrets live;
`.env.example` is the only committed `.env*`). **Do not commit the token.**

```dotenv
# --- PLAN-0014: MS-S1-unreachable Telegram ping ---
TELEGRAM_BOT_TOKEN=<harness bot token>
TELEGRAM_CHAT_ID=<your chat id>
TELEGRAM_NOTIFY_ENABLED=true
OCT_PUBLIC_BASE_URL=http://<windows-lan-ip>:<port>
# Optional (defaults shown):
# TELEGRAM_NOTIFY_COOLDOWN_S=600    # min seconds between pings (debounce UI polling)
# OLLAMA_KEEP_ALIVE=30m             # how long /warm keeps the model resident
# LLM_BACKEND=local                 # must be local for the gate to open
```

Field reference: `services/api/config.py:150-189`. `env` overrides `.env` if a
var is also exported, so a stray `export TELEGRAM_NOTIFY_ENABLED=false` in the
shell would win — prefer `.env` and keep the shell clean.

---

## 4. Restart uvicorn + verify (the confidence ladder)

Restart under **tmux** so the process survives closing the terminal, and **drop
`--reload`** for a demo (a file-watch reload can hiccup mid-demo). Bind
`0.0.0.0` so the LAN/port-proxy can reach it (default `127.0.0.1` is
WSL-internal only).

```bash
tmux new -s oct        # or: tmux attach -t oct
cd ~/work/vero-lite
uv run uvicorn services.api.main:app --host 0.0.0.0 --port 8000
# detach without stopping: Ctrl-b then d
# to restart later: tmux attach -t oct, Ctrl-c, re-run the uvicorn line
```

### 4.1 Gate check — is it armed?

```bash
cd ~/work/vero-lite
uv run python -c "from services.notify.telegram import _gates_open; print('ARMED' if _gates_open() else 'NOT ARMED')"
```
Expect `ARMED`. `NOT ARMED` → one of the four gate conditions (§0) is unset.

### 4.2 Credential test — de-risk token + chat_id independently of the app

Confirms the bot token + chat id are valid and your phone receives messages,
without needing MS-S1 down. (Terminal command — token is not written to any
file.)
```bash
curl -s "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d chat_id=<CHAT_ID> -d text="vero-lite PLAN-0014 arm test"
```
Expect `{"ok":true,...}` and the message on your phone.

### 4.3 `/warm` reachable locally

```bash
curl -s http://localhost:8000/warm | head -c 400
```
Expect HTTP 200 JSON with `"loaded":true` (MS-S1 up) — or HTTP 503 with
`"reachable":false` (MS-S1 down). Either proves the route works
(`services/api/routers/admin.py:53`).

### 4.4 Tap-link reachable from the phone

On a phone on the **same Wi-Fi**, open `http://<windows-lan-ip>:<port>/warm` in
the browser. It should load the same JSON. If it times out → do **§6** (WSL
networking).

### 4.5 End-to-end ping (optional, gold-standard)

Proves the real wired path: NL query while MS-S1 is unreachable → ping. Instead
of powering off MS-S1, point the host at a dead port.

1. In `.env` temporarily set `OLLAMA_HOST=http://192.168.1.133:1`, then restart
   uvicorn (§4).
2. Trigger an NL query:
   ```bash
   curl -s -X POST http://localhost:8000/query \
     -H 'content-type: application/json' \
     -d '{"question":"how many assets?"}' | head -c 300
   ```
   Expect an ungrounded answer ("couldn't translate…") **and** a Telegram ping
   arrives within a few seconds.
3. **Revert** `OLLAMA_HOST` and restart uvicorn.

> Cooldown: after one successful ping the notifier stays quiet for
> `TELEGRAM_NOTIFY_COOLDOWN_S` (default 600 s). The anchor is process-local —
> **restarting uvicorn resets it**, so restart between repeat tests.

---

## 5. Disarm / rollback

Set `TELEGRAM_NOTIFY_ENABLED=false` in `.env` (or remove the PLAN-0014 block)
and restart uvicorn. The gate closes and the feature no-ops — nothing else to
undo.

---

## 6. WSL2 networking — make the tap-link reachable from a phone

Pick one (do it once). uvicorn must bind `0.0.0.0` (§4) for either to work.

**Option A — mirrored networking (Win11, simplest, survives WSL restart).**
In `C:\Users\<you>\.wslconfig`:
```ini
[wsl2]
networkingMode=mirrored
```
Then in PowerShell: `wsl --shutdown`, reopen WSL, restart uvicorn. Now the
Windows LAN IP maps straight to the WSL service.

**Option B — `netsh` port-proxy (any Windows; re-run after each WSL restart).**
In an **elevated** PowerShell (`<WSL-IP>` from §2, `<port>` e.g. 8000):
```powershell
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=<port> connectaddress=<WSL-IP> connectport=<port>
New-NetFirewallRule -DisplayName "OCT <port>" -Direction Inbound -LocalPort <port> -Protocol TCP -Action Allow
```
The WSL IP changes on every WSL restart, so re-run the `portproxy` line after a
restart (Option A avoids this).

---

## 7. Safety notes

- **No PII in the ping.** The body is a fixed advisory + a warm one-liner +
  (optionally) the `/warm` link — never the operator question, record data, or
  partner identifiers (`services/notify/telegram.py:build_message`; CLAUDE.md §8
  / PDPA).
- **Secrets stay in `.env`.** Token + chat id are env-only; `.env` is gitignored.
  Never paste the token into a committed file (incl. this runbook or a PR body).
- **Best-effort.** `notify_llm_unreachable` never raises into the request path —
  a notify failure is swallowed + logged, so arming cannot break a live demo.

---

## References

- Plan: `docs/plans/done/0014-llm-unreachable-telegram-notify.md`
- Notifier: `services/notify/telegram.py`
- `/warm` + `/sleep` routes: `services/api/routers/admin.py`
- Config fields: `services/api/config.py:145-189`
- NL-query route (ping trigger): `services/api/routers/query.py` (`POST /query`)
- MS-S1 reachability: memory `project_ms_s1_ollama_reachability` (IP `192.168.1.133`, not hostname)
- Harness-bot reuse rationale: ADR-013 D5
