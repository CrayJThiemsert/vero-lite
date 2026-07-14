/* ============================================================
   OCT — API layer + app state + ontology helpers.
   Tries the REAL relative endpoint first; on network failure
   (backend offline / mid-call) falls back to the embedded mock
   and flips the connection strip to "degraded".
   ============================================================ */
(function () {
  'use strict';

  const State = {
    meta: null,
    objects: {},        // { TypeName: { count, objects:[] } }
    recommendations: [],
    connection: 'live', // live | degraded | down
    usingMock: false,
    view: 'A'
  };

  const listeners = [];
  function onConnection(fn) { listeners.push(fn); }
  function setConnection(c) {
    if (State.connection === c) return;
    State.connection = c;
    listeners.forEach(fn => fn(c));
  }

  /* ---- core request: real fetch, fall back to mock ---- */
  async function request(method, path, body) {
    const opts = { method, headers: {} };
    if (body !== undefined) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
    try {
      const res = await fetch(path, opts);
      const ct = res.headers.get('content-type') || '';
      // A live backend serves these routes as JSON with 200. Anything else
      // (404 because the endpoint isn't wired, a 5xx, or an HTML error page)
      // means the real API isn't answering here — fall back to the mock.
      if (!res.ok || !ct.includes('json')) {
        return fallback(method, path, body, 'endpoint-unavailable');
      }
      State.usingMock = false;
      setConnection('live');
      return res.json();
    } catch (err) {
      // network failure (offline / blocked) → mock
      return fallback(method, path, body, 'network');
    }
  }

  function fallback(method, path, body) {
    if (window.OCT_MOCK) {
      State.usingMock = true;
      setConnection('degraded');
      return window.OCT_MOCK.handle(method, path, body);
    }
    setConnection('down');
    return Promise.reject(new Error('Backend unreachable and no embedded data available.'));
  }

  const API = {
    meta: () => request('GET', '/meta'),
    objects: (type) => request('GET', '/objects/' + encodeURIComponent(type)),
    recommendations: () => request('GET', '/recommendations'),
    approve: (id) => request('POST', '/recommendations/' + encodeURIComponent(id) + '/approve'),
    execute: (id) => request('POST', '/recommendations/' + encodeURIComponent(id) + '/execute'),
    query: (question) => request('POST', '/query', { question }),
    // PLAN-0039 (read-only procedure viewer): a DIRECT fetch with NO mock
    // fallback. A mocked copy would drift from the live verticals/*/procedures.yaml
    // the viewer is meant to render faithfully, so an honest "backend required"
    // empty state offline is correct (the view shows errorState on failure).
    procedures: () => fetchProcedures()
  };

  async function fetchProcedures() {
    const res = await fetch('/procedures');
    const ct = res.headers.get('content-type') || '';
    if (!res.ok || !ct.includes('json')) {
      throw new Error('GET /procedures unavailable (' + res.status + ')');
    }
    return res.json();
  }

  /* ---- hero-demo read-only views (PLAN-0045): the governance-moment audit + the
     ฿-impact ledger. DIRECT fetch, NO mock fallback — the render binds to the shipped
     A1b engine shapes / the derived ledger, so a mocked copy would drift; an honest
     "backend required" error offline is correct (the view shows errorState). */
  async function fetchDemoHero(path, init) {
    const res = await fetch(path, init);
    const ct = res.headers.get('content-type') || '';
    if (!res.ok || !ct.includes('json')) {
      const verb = (init && init.method) || 'GET';
      throw new Error(verb + ' ' + path + ' unavailable (' + res.status + ')');
    }
    return res.json();
  }
  const Hero = {
    governance: (live) => fetchDemoHero('/demo/hero/governance' + (live ? '?live=true' : '')),
    impact: () => fetchDemoHero('/demo/hero/impact'),
    // PLAN-0057: the event-triggered opener — a POST (persists a governed run via the bridge).
    event: () => fetchDemoHero('/demo/hero/event', { method: 'POST' }),
    // PLAN-0072 (beat 3): read the parked run's proposals (read-only) + resolve the DOA gate
    // through the REAL production route (authenticated operate POST). resolve() throws an error
    // carrying .status + .detail so the Act panel renders an honest 401 / 403-with-verdict / 409.
    runDetail: (runId) => fetchDemoHero('/runs/' + encodeURIComponent(runId)),
    resolve: async (runId, stepId, decisions) => {
      const res = await fetch('/runs/' + encodeURIComponent(runId) + '/gate/resolve', {
        method: 'POST',
        headers: Object.assign({ 'Content-Type': 'application/json' },
          (window.OCT && window.OCT.Auth ? window.OCT.Auth.authHeader() : {})),
        body: JSON.stringify({ step_id: stepId, decisions: decisions })
      });
      let data = null;
      try { data = await res.json(); } catch (e) { /* empty / non-JSON body */ }
      if (!res.ok) {
        const d = data && data.detail;
        const err = new Error((d && (typeof d === 'string' ? d : d.error)) || ('HTTP ' + res.status));
        err.status = res.status; err.detail = d;
        throw err;
      }
      return data;
    }
  };

  /* ---- LLM control (PLAN-0018): MS-S1 status + warm/sleep ----
     These talk to the REAL backend only — NO mock fallback. A mocked
     "resident" would lie about MS-S1, and GET /llm/status already returns a
     truthful unreachable/cold/resident/error body (HTTP 200) of its own, so we
     never want request()'s mock path here. Returns {ok, status, body}. */
  async function llmCall(method, path) {
    try {
      const res = await fetch(path, { method });
      const ct = res.headers.get('content-type') || '';
      const body = ct.includes('json') ? await res.json().catch(() => null) : null;
      return { ok: res.ok, status: res.status, body: body };
    } catch (err) {
      // demo backend itself unreachable (network) — distinct from MS-S1 down
      return { ok: false, status: 0, body: null, networkError: true };
    }
  }
  const Llm = {
    status: () => llmCall('GET', '/llm/status'),     // read-only; never warms (INV-1)
    warm: () => llmCall('GET', '/warm?wait=false'),  // non-blocking warm (AC-8)
    sleep: () => llmCall('GET', '/sleep')
  };

  /* ---- intake face (PLAN-0017): live co-creation -> vertical #4 ----
     REAL backend only — NO mock fallback (a mocked extraction/generate would
     lie about what was built). extract is MS-S1-local; generate ALWAYS sends
     confirmed:true because the ONLY caller is the operator's explicit gate
     Confirm click (the UI has no auto-confirm path — AC-2). Returns
     {ok, status, body}. */
  async function intakeCall(method, path, body) {
    try {
      const opts = { method, headers: {} };
      if (body !== undefined) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
      const res = await fetch(path, opts);
      const ct = res.headers.get('content-type') || '';
      const parsed = ct.includes('json') ? await res.json().catch(() => null) : null;
      return { ok: res.ok, status: res.status, body: parsed };
    } catch (err) {
      return { ok: false, status: 0, body: null, networkError: true };
    }
  }
  const Intake = {
    extract: (description, namespaceHint) =>
      intakeCall('POST', '/intake/extract', { description, namespace_hint: namespaceHint || null }),
    defaults: () => intakeCall('GET', '/intake/defaults'),
    // confirmed is hard-true: only the explicit gate Confirm button calls this.
    generate: (pkg, force) =>
      intakeCall('POST', '/intake/generate', { package: pkg, confirmed: true, force: !!force })
  };

  /* ---- procedure-draft intake (PLAN-0040 AC-B5): narrative -> governed skeleton ----
     REAL backend only (reuses intakeCall — NO mock fallback; a mocked classify/build
     would lie about the moat). `build` ALWAYS sends confirmed:true: the ONLY caller is
     the operator's explicit gate Confirm click (no auto-confirm path, LOCKED-5).
     `instantiate` is the zero-LLM manual-pick fallback (works when MS-S1 is cold, D9).
     Each returns {ok, status, body}; the body carries state=match|abstain|degraded|ok. */
  const Draft = {
    classify: (narrative, vertical) =>
      intakeCall('POST', '/procedures/draft/classify', { narrative, vertical }),
    build: (narrative, vertical, archetypeId, bandSource) =>
      intakeCall('POST', '/procedures/draft/build', {
        narrative, vertical, archetype_id: archetypeId,
        confirmed: true, band_source: bandSource || 'in_file'
      }),
    instantiate: (archetypeId, vertical, title) =>
      intakeCall('POST', '/procedures/draft/instantiate', {
        archetype_id: archetypeId, vertical, title: title || ''
      })
  };

  /* ---- ontology helpers (everything domain-specific comes from here) ---- */
  const Onto = {
    typeDef(name) { return State.meta ? State.meta.object_types.find(t => t.name === name) : null; },
    pk(type) { const t = Onto.typeDef(type); return t ? (t.primary_key || (t.properties[0] && t.properties[0].name)) : null; },
    titleKey(type) { const t = Onto.typeDef(type); return t ? t.title_key : null; },
    // display label of a record: value of title_key, fall back to primary_key
    label(type, obj) {
      if (!obj) return '';
      const tk = Onto.titleKey(type);
      if (tk && obj[tk] != null) return obj[tk];
      const pk = Onto.pk(type);
      return pk && obj[pk] != null ? obj[pk] : '';
    },
    prop(type, name) { const t = Onto.typeDef(type); return t ? t.properties.find(p => p.name === name) : null; },
    // ref properties pointing out of this type
    refs(type) { const t = Onto.typeDef(type); return t ? t.properties.filter(p => p.type === 'ref') : []; },
    enumProps(type) { const t = Onto.typeDef(type); return t ? t.properties.filter(p => p.type === 'enum') : []; },
    // the "status-like" enum used for a record's primary badge:
    // prefer a prop literally named status / severity, else first enum prop
    statusProp(type) {
      const t = Onto.typeDef(type); if (!t) return null;
      return t.properties.find(p => p.type === 'enum' && /status|severity|state/i.test(p.name))
          || t.properties.find(p => p.type === 'enum') || null;
    },
    // find lat/lng-bearing props for the map (by name heuristics over /meta)
    geoProps(type) {
      const t = Onto.typeDef(type); if (!t) return null;
      const lat = t.properties.find(p => /^(lat|latitude)$/i.test(p.name));
      const lng = t.properties.find(p => /^(lng|lon|long|longitude)$/i.test(p.name));
      return (lat && lng) ? { lat: lat.name, lng: lng.name } : null;
    },
    // which object types carry geo coords
    geoTypes() { return State.meta ? State.meta.object_types.filter(t => Onto.geoProps(t.name)) : []; },
    // resolve a ref value to its target object (from loaded store)
    resolveRef(fromType, propName, obj) {
      const p = Onto.prop(fromType, propName);
      if (!p || p.type !== 'ref' || !p.target) return null;
      const target = p.target;
      const val = obj[propName];
      const store = State.objects[target];
      if (!store) return { target, id: val, obj: null };
      const tpk = Onto.pk(target);
      return { target, id: val, obj: store.objects.find(o => o[tpk] === val) || null };
    },
    // map an enum value to a semantic status class (shared by severities + statuses)
    statusClass(value) {
      const v = String(value || '').toLowerCase();
      if (/(critical|error|fault|alarm|offline|failed|fail|rejected|breach|excursion)/.test(v)) return 's-crit';
      if (/(warn|maintenance|pending|degraded|proposed|caution|delayed|held|hold|open)/.test(v)) return 's-warn';
      if (/(active|ok|online|nominal|healthy|live|executed|approved\b|delivered|resolved|closed|completed)/.test(v)) return 's-ok';
      if (/(info|approved|reading|transition|paired|transit|acknowledged|scheduled|staged|at_facility)/.test(v)) return 's-info';
      if (/(retired|inactive|disabled|archived|unknown|n\/a)/.test(v)) return 's-neutral';
      return 's-neutral';
    }
  };

  /* ---- load core data ---- */
  async function loadMeta() { State.meta = await API.meta(); return State.meta; }
  async function loadObjects(type) {
    const r = await API.objects(type);
    State.objects[type] = r;
    return r;
  }
  async function loadAllObjects() {
    if (!State.meta) await loadMeta();
    await Promise.all(State.meta.object_types.map(t => loadObjects(t.name).catch(() => { State.objects[t.name] = { object_type: t.name, count: 0, objects: [] }; })));
    return State.objects;
  }
  async function loadRecommendations() {
    const r = await API.recommendations();
    State.recommendations = r.recommendations || [];
    return State.recommendations;
  }

  window.OCT = window.OCT || {};
  Object.assign(window.OCT, {
    State, API, Llm, Intake, Draft, Hero, Onto, onConnection, setConnection,
    loadMeta, loadObjects, loadAllObjects, loadRecommendations
  });
})();
