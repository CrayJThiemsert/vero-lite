---
name: ms-s1-ollama
description: Reach, warm, and run a live LLM on the MS-S1 MAX Ollama server (192.168.1.133) for host-state work — benchmarks, structured `format` smokes, latency runs. Encodes the gotchas that otherwise waste tokens on trial-and-error: reach by IP not hostname, list/verify models with jq (never a nested-quote python one-liner), warm via /api/generate, cold-load times, and the "verify the right model" discipline. Use whenever warming or running any model on MS-S1, listing its Ollama tags, or about to run the procedure-baseline benchmark. The helper script `warm.sh` does reachability + tag-verify + warm in one robust command.
---

# MS-S1 MAX — Ollama host-state operations

The LLM server (ADR-0002): **AMD Ryzen AI Max+ 395, 128 GB unified, gfx1151**,
Ollama over ROCm. This skill is the **how-to** for reaching/warming/running it so
the agent doesn't rediscover the incantations (and burn tokens) each session.

## ⚠️ Host-state gate (binding rule lives elsewhere — do NOT rely on this skill to carry it)

Warming or running a model on MS-S1 is a **host-state change**. The **binding
rule** is *ASK Cray before warming / running* — it lives in the active PLAN /
handoff (e.g. PLAN-0020 §5/Phase 2), **not** here (a skill that fails to trigger
must never silently drop a binding rule — CLAUDE.md §4 bright line). This skill
only encodes the *mechanics* once you have the go-ahead.

## Reach by IP, not hostname

```
http://192.168.1.133:11434
```

`ms-s1-max` has **no WSL DNS entry** — `http://ms-s1-max:11434` fails to resolve
from WSL. Always use the IP. Override with `OLLAMA_HOST` if the box moves.

## The pinned model

**`gpt-oss:20b`** (ADR-0001) — the structured-output / `format` path. The G-3
sweep confirmed the pin is best on **both** accuracy and latency (~3.5× faster
than the 12 B–35 B alternatives); *smaller did NOT mean faster* (it is a MoE /
MXFP4 build). The procedure-baseline benchmark and any structured `format` smoke
use this model. `qwen3.x` historically = NOT_JSON for the structured path (one
build of `qwen3.6:35b` does emit JSON, but it is ~3.6× slower and not the pin).

## Warm first — use the helper

```bash
bash .claude/skills/ms-s1-ollama/warm.sh                 # defaults: gpt-oss:20b, keep_alive 15m
bash .claude/skills/ms-s1-ollama/warm.sh gemma4:12b 10m  # explicit model + keep_alive
```

`warm.sh` does three things and **fails closed**:
1. reachability check (GET `/api/tags`);
2. lists every model present **and verifies the requested one is there BEFORE
   warming** — never warm/smoke a model that isn't loaded (the session-37 trap:
   a green smoke against the *wrong* model is false confidence);
3. warms via `/api/generate` with `keep_alive`, printing the cold-load time.

Run it with **`bash script`**, never `./script` — the WSL UNC mount strips POSIX
exec bits (repo sets `core.fileMode false`).

### Cold-load expectations

- `gpt-oss:20b` — **~20–25 s** cold; near-instant once resident.
- `qwen3.x` (35 B) — **>150 s** cold; warm it first and be patient, or it trips
  per-call timeouts mid-run.

Once warm, `keep_alive` (default 15 m) holds it in VRAM; an active run keeps
resetting the timer, so it stays warm for the whole benchmark.

## Listing tags by hand (if not using warm.sh)

Use **jq** — a python one-liner with nested shell quotes is the exact
token-wasting trap this skill exists to avoid:

```bash
curl -s --max-time 10 http://192.168.1.133:11434/api/tags | jq -r '.models[].name'
```

Read the **full** list (never `head -c`-truncated) and confirm your model is in
it before running anything (session-37 lesson).

## Running the procedure-baseline benchmark

After `warm.sh` reports OK (and Cray's go):

```bash
PYTHONUNBUFFERED=1 uv run python -m benchmarks.procedure_baseline.run_benchmark \
  --ollama-host http://192.168.1.133:11434 --warm \
  --reasoning-mode full --dump-json .claude/benchmark-results/<run>.jsonl \
  > .claude/benchmark-results/<run>.log 2>&1
```

- `PYTHONUNBUFFERED=1` — a SIGKILL on a buffered run loses stdout (process-check
  lesson). Run long sweeps in the **background** and read the log/dump after.
- **Long runs need a HELD wsl.exe — `setsid`/`nohup` detach does NOT survive
  here.** A ~50-min sweep must keep a wsl.exe attached for its whole duration:
  launch it via the harness `run_in_background` (which holds one). A
  `setsid nohup … &` started from a foreground call is killed the instant that
  call's wsl.exe exits — empirically the detached children never even wrote their
  first log line. **Instrument every long run**: embed a heartbeat (timestamp +
  items-done + free-MB) and `[wrap] START` / `[wrap] EXIT=<rc>` markers + a signal
  trap, so a death yields the exact time, the memory trend, and any catchable
  signal. The benchmark has **no resume** and writes `--dump-json` + the latency
  summary only at the END — a mid-run kill loses both (per-item PASS/FAIL is in
  the log, so β is salvageable per vertical; latency + dump are not). **No
  systematic ~30-min reap (resolved):** one full run died ~30 min in (no `EXIT`
  marker, memory flat → not OOM, host not asleep), but the very next run — same
  `run_in_background` + the instrumentation above — completed cleanly at ~48 min,
  sailing past the 30-min mark. So that death was a **one-off** (most likely a
  transient WSL / concurrent-session event), not a TTL. Keep long runs
  instrumented anyway so any future one-off is diagnosable, and if you do hit a
  kill, just relaunch (the dump/latency are END-only, so a fresh full run is the
  recovery — there is no resume).
- **Carrier death ≠ benchmark death (observed 2026-06-12).** A one-off reap can
  kill only the **carrier** (the held wsl.exe + wrapper bash): the heartbeat
  subshell dies on SIGPIPE at its next echo and `[wrap] EXIT` never gets
  written — but the python benchmark, whose stdout is redirected to a **file**,
  survives as an orphan and finishes normally. Consequences: **no harness
  completion notification fires**, and the background-task chip can show
  **"running" stale** though nothing is running. Truth test is
  **content-based, never task-status-based**: (1) the log's final
  `DUMP: wrote N item records` + NOTE block are `_main()`'s LAST statements —
  their presence proves every prior item/summary completed; (2) the
  `--dump-json` record count matches; (3) `pgrep -af run_benchmark` is empty;
  (4) `TaskStop <id>` returning "No task found" confirms the harness handle is
  already gone (the chip is display-only at that point). After diagnosing a
  carrier death, verify/clear the harness task state immediately — don't leave
  a stale "running" chip for Cray to find.
- `--reasoning-mode {full,think_off,skip}` — PLAN-0020 think-trim lever.
- `--judgment-latency-threshold` defaults **30 s** (SD-2 per-judgment acceptance
  bar); `--latency-threshold` (per-call) is a lever diagnostic only.
- **VERIFY every score from `--dump-json`** with the Read tool (not piped
  `cat`/`wc`) — confirm a number is a real model verdict, not a grader artifact
  (session-46). Each record carries the per-check detail + the raw judgment.
- **Serialize** runs — one model on MS-S1 at a time, otherwise concurrent
  generations pollute each other's latency. Do not warm/generate against MS-S1
  while another measured run is in flight.

## Snapshot — models on MS-S1 (2026-06-11; verify with warm.sh, don't trust this list)

`gpt-oss:20b` (pin), `gemma4:12b`, `gemma4:26b`, `qwen3.6:35b`, `qwen3.5:35b`,
`qwen2.5-coder:32b`, `groomflow-unified:latest`.

---

*Tier 2.6 skill (ADR-0017). Mechanics only — the host-state ASK-Cray gate is a
binding rule in the active PLAN/handoff, not here. Sources: ADR-0001 (pin),
ADR-0002 (MS-S1), Lessons on MS-S1 reachability / verify-pin-before-override /
process-check.*
