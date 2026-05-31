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
    query: (question) => request('POST', '/query', { question })
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
    State, API, Onto, onConnection, setConnection,
    loadMeta, loadObjects, loadAllObjects, loadRecommendations
  });
})();
