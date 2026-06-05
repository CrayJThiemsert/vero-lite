/* ============================================================
   OCT — MS-S1 LLM control (PLAN-0018).
   A header affordance for the demo operator: a read-only residency
   indicator polling GET /llm/status (the poll NEVER warms — INV-1) plus a
   non-blocking Warm and a guarded Sleep.
   ============================================================ */
(function () {
  'use strict';
  const O = window.OCT;
  const { h, icon } = O;

  const POLL_MS = 5000;        // D-1: documented client interval, no server cache
  const WARM_POLL_MS = 1500;   // faster cadence while a warm is in flight
  const WARM_TIMEOUT_MS = 45000;
  const SLEEP_ARM_MS = 4000;   // guarded sleep auto-disarms after this

  // state → indicator visual (status-color vocabulary from theme.css)
  const VIS = {
    resident:    { cls: 's-ok',      text: 'RESIDENT' },
    cold:        { cls: 's-warn',    text: 'COLD' },
    warming:     { cls: 's-info',    text: 'WARMING…' },
    unreachable: { cls: 's-crit',    text: 'OFFLINE' },
    error:       { cls: 's-crit',    text: 'ERROR' },
    unknown:     { cls: 's-neutral', text: '—' }
  };

  let rootEl, indEl, labelEl, warmBtn, sleepBtn;
  let timer = null;
  let warming = false, warmDeadline = 0;
  let sleepArmed = false, sleepArmTimer = null;

  function mount(target) {
    indEl = h('span', { class: 'llm-ind s-neutral' }, [
      icon('cpu', { width: 12, height: 12 }),
      h('span', { class: 'llm-tag' }, 'MS-S1'),
      h('span', { class: 'led' }),
      labelEl = h('span', { class: 'llm-state' }, '—')
    ]);
    warmBtn = h('button', { class: 'iconbtn sm', onClick: onWarm }, [icon('bolt'), 'Warm']);
    sleepBtn = h('button', { class: 'iconbtn sm llm-sleep', onClick: onSleep }, 'Sleep');
    rootEl = h('div', { class: 'llmctl', title: 'MS-S1 local LLM (recommender model)' },
      [indEl, warmBtn, sleepBtn]);
    target.appendChild(rootEl);

    document.addEventListener('visibilitychange', onVisibility);
    tick(); // initial poll + schedule
  }

  function setIndicator(state) {
    const v = VIS[state] || VIS.unknown;
    indEl.className = 'llm-ind ' + v.cls + (state === 'warming' ? ' is-warming' : '');
    labelEl.textContent = v.text;
  }

  function updateButtons(state) {
    const canWarm = !warming && state !== 'resident';
    warmBtn.disabled = !canWarm;
    const canSleep = state === 'resident' || state === 'warming';
    sleepBtn.disabled = !canSleep;
    if (!canSleep && sleepArmed) disarmSleep();
  }

  function setTooltip(state, body) {
    if (state === 'resident' && body && body.seconds_remaining != null) {
      const mins = Math.max(0, Math.round(body.seconds_remaining / 60));
      rootEl.title = 'MS-S1 recommender model resident · ~' + mins + ' min until idle-evict';
    } else if (body && body.detail) {
      rootEl.title = 'MS-S1: ' + body.detail;
    } else if (state === 'unknown') {
      rootEl.title = 'MS-S1 status unavailable (demo backend not answering /llm/status)';
    } else {
      rootEl.title = 'MS-S1 local LLM (recommender model)';
    }
  }

  async function poll() {
    const r = await O.Llm.status();
    const body = r && r.body;
    let state = (r && r.ok && body && body.state) ? body.state : 'unknown';

    // warming overlay: hold a transient WARMING… between a warm click and the
    // flip to resident; drop it on success, a real failure, or timeout (AC-8).
    if (warming) {
      if (state === 'resident' || state === 'unreachable' || state === 'error'
          || Date.now() > warmDeadline) {
        warming = false;
      } else {
        state = 'warming';
      }
    }

    setIndicator(state);
    updateButtons(state);
    setTooltip(state, body);
    return state;
  }

  function schedule(ms) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(tick, ms);
  }

  async function tick() {
    await poll();
    schedule(warming ? WARM_POLL_MS : POLL_MS);
  }

  async function onWarm() {
    if (warmBtn.disabled) return;
    warming = true;
    warmDeadline = Date.now() + WARM_TIMEOUT_MS;
    setIndicator('warming');
    updateButtons('warming');
    await O.Llm.warm();   // GET /warm?wait=false — returns immediately, never blocks
    tick();               // immediate poll, then fast cadence until resident
  }

  /* guarded sleep (AC-7): destructive, so it requires a deliberate two-step —
     first click arms (visually distinct "Confirm?"), a second click within the
     arm window executes; otherwise it auto-disarms. Never a single fat-finger. */
  function onSleep() {
    if (sleepBtn.disabled) return;
    if (!sleepArmed) {
      sleepArmed = true;
      sleepBtn.classList.add('armed');
      sleepBtn.textContent = 'Confirm?';
      clearTimeout(sleepArmTimer);
      sleepArmTimer = setTimeout(disarmSleep, SLEEP_ARM_MS);
      return;
    }
    disarmSleep();
    doSleep();
  }

  function disarmSleep() {
    sleepArmed = false;
    clearTimeout(sleepArmTimer);
    sleepBtn.classList.remove('armed');
    sleepBtn.textContent = 'Sleep';
  }

  async function doSleep() {
    warming = false;
    await O.Llm.sleep();  // GET /sleep
    tick();               // refresh → should flip to cold
  }

  function onVisibility() {
    if (document.hidden) {
      if (timer) { clearTimeout(timer); timer = null; }
    } else {
      tick();
    }
  }

  O.LlmControl = { mount: mount };
})();
