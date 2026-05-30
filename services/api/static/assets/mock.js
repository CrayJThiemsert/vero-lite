/* ============================================================
   OCT — Embedded mock backend.
   The page fetches RELATIVE URLs (/meta, /objects/..., /recommendations,
   /query, .../approve, .../execute) exactly as the real backend serves.
   This module transparently answers those same routes when the real
   backend is unreachable, so the demo renders & the round-trips work.
   It is a faithful in-memory ontology store — swapping META alone
   re-skins the entire UI, proving the "ontology-driven" claim.
   ============================================================ */
(function () {
  'use strict';

  /* ---------- /meta : the ontology ---------- */
  const META = {
    vertical: 'energy',
    namespace: 'grid-ops',
    version: 3,
    object_types: [
      {
        name: 'Site', primary_key: 'site_id', title_key: 'name',
        description: 'A physical location operating grid assets.',
        properties: [
          { name: 'site_id', type: 'string', required: true, enum: null, target: null },
          { name: 'name', type: 'string', required: true, enum: null, target: null },
          { name: 'site_type', type: 'enum', required: true, enum: ['substation', 'microgrid', 'depot'], target: null },
          { name: 'lat', type: 'float', required: true, enum: null, target: null },
          { name: 'lng', type: 'float', required: true, enum: null, target: null },
          { name: 'region', type: 'string', required: false, enum: null, target: null }
        ]
      },
      {
        name: 'Asset', primary_key: 'asset_id', title_key: 'name',
        description: 'A controllable unit of grid equipment.',
        properties: [
          { name: 'asset_id', type: 'string', required: true, enum: null, target: null },
          { name: 'name', type: 'string', required: true, enum: null, target: null },
          { name: 'asset_type', type: 'enum', required: true, enum: ['battery', 'inverter', 'meter', 'transformer'], target: null },
          { name: 'capacity_kw', type: 'float', required: false, enum: null, target: null },
          { name: 'status', type: 'enum', required: true, enum: ['active', 'maintenance', 'retired'], target: null },
          { name: 'install_date', type: 'date', required: false, enum: null, target: null },
          { name: 'site_id', type: 'ref', required: true, enum: null, target: 'Site' }
        ]
      },
      {
        name: 'OperationalEvent', primary_key: 'event_id', title_key: null,
        description: 'A time-stamped reading, transition or alarm from an asset.',
        properties: [
          { name: 'event_id', type: 'string', required: true, enum: null, target: null },
          { name: 'event_type', type: 'enum', required: true, enum: ['reading', 'transition', 'alarm'], target: null },
          { name: 'severity', type: 'enum', required: true, enum: ['info', 'warn', 'error', 'critical'], target: null },
          { name: 'measured_value', type: 'float', required: false, enum: null, target: null },
          { name: 'unit', type: 'string', required: false, enum: null, target: null },
          { name: 'occurred_at', type: 'datetime', required: true, enum: null, target: null },
          { name: 'asset_id', type: 'ref', required: true, enum: null, target: 'Asset' }
        ]
      },
      {
        name: 'RecommendedAction', primary_key: 'action_id', title_key: 'title',
        description: 'A governed action proposed by the engine for human sign-off.',
        properties: [
          { name: 'action_id', type: 'string', required: true, enum: null, target: null },
          { name: 'title', type: 'string', required: true, enum: null, target: null },
          { name: 'status', type: 'enum', required: true, enum: ['proposed', 'approved', 'rejected', 'executed'], target: null },
          { name: 'confidence', type: 'float', required: true, enum: null, target: null },
          { name: 'asset_id', type: 'ref', required: false, enum: null, target: 'Asset' }
        ]
      }
    ],
    link_types: [
      { name: 'asset_at_site', from_type: 'Asset', to_type: 'Site', cardinality: 'many_to_one' },
      { name: 'event_on_asset', from_type: 'OperationalEvent', to_type: 'Asset', cardinality: 'many_to_one' },
      { name: 'action_targets_asset', from_type: 'RecommendedAction', to_type: 'Asset', cardinality: 'many_to_one' }
    ]
  };

  /* ---------- object store ---------- */
  const STORE = {
    Site: [
      { site_id: 'site-substation-01', name: 'North Substation', site_type: 'substation', lat: 13.75, lng: 100.50, region: 'Metro North' },
      { site_id: 'site-microgrid-01', name: 'Riverside Microgrid', site_type: 'microgrid', lat: 13.81, lng: 100.56, region: 'Riverside' }
    ],
    Asset: [
      { asset_id: 'asset-battery-01', name: 'Battery Bank A', asset_type: 'battery', capacity_kw: 250, status: 'active', install_date: '2022-04-11', site_id: 'site-substation-01' },
      { asset_id: 'asset-inverter-01', name: 'Inverter Unit A', asset_type: 'inverter', capacity_kw: 500, status: 'active', install_date: '2022-04-11', site_id: 'site-substation-01' },
      { asset_id: 'asset-battery-02', name: 'Battery Bank B', asset_type: 'battery', capacity_kw: 250, status: 'active', install_date: '2023-01-20', site_id: 'site-microgrid-01' },
      { asset_id: 'asset-meter-01', name: 'Feeder Meter A', asset_type: 'meter', capacity_kw: null, status: 'active', install_date: '2021-09-02', site_id: 'site-microgrid-01' }
    ],
    OperationalEvent: [
      { event_id: 'evt-0007', event_type: 'reading', severity: 'critical', measured_value: 96.5, unit: 'celsius', occurred_at: '2026-05-30T08:14:22Z', asset_id: 'asset-battery-01' },
      { event_id: 'evt-0006', event_type: 'reading', severity: 'warn', measured_value: 84.2, unit: 'celsius', occurred_at: '2026-05-30T08:02:10Z', asset_id: 'asset-battery-01' },
      { event_id: 'evt-0005', event_type: 'reading', severity: 'info', measured_value: 41.0, unit: 'celsius', occurred_at: '2026-05-30T07:58:01Z', asset_id: 'asset-battery-02' },
      { event_id: 'evt-0004', event_type: 'reading', severity: 'info', measured_value: 230.4, unit: 'kw', occurred_at: '2026-05-30T07:55:40Z', asset_id: 'asset-inverter-01' },
      { event_id: 'evt-0003', event_type: 'transition', severity: 'info', measured_value: null, unit: null, occurred_at: '2026-05-30T06:30:00Z', asset_id: 'asset-meter-01' }
    ],
    RecommendedAction: [
      { action_id: 'act-otemp-01', title: 'Investigate over-temperature on asset-battery-01', status: 'proposed', confidence: 0.8, asset_id: 'asset-battery-01' }
    ]
  };

  /* ---------- recommendations (rich form for View B) ---------- */
  const RECS = [
    {
      action_id: 'act-otemp-01',
      title: 'Investigate over-temperature on Battery Bank A',
      description: 'Battery Bank A (asset-battery-01) reported a cell temperature of 96.5 °C, exceeding the 90.0 °C safety threshold. Recommend dispatching an inspection and de-rating the bank until the reading returns below threshold.',
      vertical: 'energy',
      status: 'proposed',
      confidence: 0.8,
      requires_approval: true,
      suggested_handler: 'dispatch.work_order',
      reasoning_trace: [
        {
          step_id: 'r1', kind: 'ontology_query',
          summary: 'Pulled latest reading events for assets of type "battery".',
          detail: { object_type: 'OperationalEvent', filter: 'event_type = reading AND asset.asset_type = battery', returned: 3, latest_event: 'evt-0007' }
        },
        {
          step_id: 'r2', kind: 'rule_check',
          summary: 'measured_value 96.5 celsius ≥ threshold 90.0 celsius — over-temperature.',
          detail: { property: 'measured_value', measured_value: 96.5, unit: 'celsius', operator: '>=', threshold: 90.0, rule: 'battery.thermal.max_cell_temp', breached: true }
        },
        {
          step_id: 'r3', kind: 'llm_inference',
          summary: 'Classified the breach as a thermal-runaway precursor; recommended inspect + de-rate over immediate shutdown.',
          detail: { model: 'oct-reasoner-v2', hypothesis: 'thermal_runaway_precursor', alternatives_considered: ['sensor_fault', 'transient_spike'], rationale: 'Reading is 6.5 °C above threshold and trended up from 84.2 °C 12 min earlier — consistent rise, not a single-sample spike.', recommended_handler: 'dispatch.work_order' }
        },
        {
          step_id: 'r4', kind: 'ontology_query',
          summary: 'Resolved affected asset and its site for the work-order payload.',
          detail: { asset_id: 'asset-battery-01', asset_name: 'Battery Bank A', site_id: 'site-substation-01', site_name: 'North Substation' }
        }
      ],
      affected_entities: [
        { object_type: 'Asset', primary_key: 'asset-battery-01', title: 'Battery Bank A' },
        { object_type: 'Site', primary_key: 'site-substation-01', title: 'North Substation' }
      ]
    }
  ];

  /* ---------- query engine (genuinely evaluates against the store) ---------- */
  function singular(word) { return word.replace(/s$/i, ''); }
  function typeFromText(q) {
    // 1) explicit type-name mention
    for (const t of META.object_types) {
      const n = t.name.toLowerCase();
      if (q.includes(n) || q.includes(n + 's') || q.includes(singular(n))) return t.name;
    }
    // 2) keyword hints
    if (/\breading|temperature|temp|°c|celsius|alarm|\bevent/.test(q)) return 'OperationalEvent';
    if (/\bsite|location|substation|microgrid|depot/.test(q)) return 'Site';
    if (/\basset|battery|inverter|meter|transformer|unit|equipment|capacity/.test(q)) return 'Asset';
    // 3) ontology-driven: infer the type that OWNS an enum value present in the text
    for (const t of META.object_types) {
      for (const p of t.properties) {
        if (p.enum && p.enum.some(v => new RegExp('\\b' + v.toLowerCase() + '\\b').test(q))) return t.name;
      }
    }
    return null;
  }
  function detectFilters(q, type) {
    const filters = [];
    const td = META.object_types.find(t => t.name === type);
    if (!td) return filters;
    // enum-value filters: scan every enum property's allowed values
    for (const p of td.properties) {
      if (p.enum) for (const val of p.enum) {
        if (q.includes(val)) filters.push({ property: p.name, op: 'eq', value: val });
      }
    }
    // numeric threshold on measured_value: "above 90", "over 90", "> 90"
    const m = q.match(/(?:above|over|greater than|>|exceed(?:ing|s)?)\s*(\d+(?:\.\d+)?)/);
    if (m && td.properties.some(p => p.name === 'measured_value')) {
      filters.push({ property: 'measured_value', op: 'gt', value: m[1] });
    }
    const m2 = q.match(/(?:below|under|less than|<)\s*(\d+(?:\.\d+)?)/);
    if (m2 && td.properties.some(p => p.name === 'measured_value')) {
      filters.push({ property: 'measured_value', op: 'lt', value: m2[1] });
    }
    return filters;
  }
  function applyFilter(obj, f) {
    const v = obj[f.property];
    if (v === undefined || v === null) return false;
    if (f.op === 'eq') return String(v).toLowerCase() === String(f.value).toLowerCase();
    if (f.op === 'gt') return Number(v) > Number(f.value);
    if (f.op === 'lt') return Number(v) < Number(f.value);
    if (f.op === 'gte') return Number(v) >= Number(f.value);
    return false;
  }
  function runQuery(question) {
    const q = (question || '').toLowerCase().trim();
    const type = typeFromText(q);
    if (!type) {
      return {
        question, answer: "I can answer questions about " + META.object_types.map(t => t.name).join(', ') + ". Try asking about one of those.",
        grounded: false, structured_query: null, source_object_type: null,
        source_object_ids: [], source_objects: [], result_count: 0
      };
    }
    const operation = /\bhow many|count|number of|total/.test(q) ? 'count' : 'list';
    const filters = detectFilters(q, type);
    const td = META.object_types.find(t => t.name === type);
    const pk = td.primary_key;
    const titleKey = td.title_key;
    let rows = (STORE[type] || []).filter(o => filters.every(f => applyFilter(o, f)));
    const ids = rows.map(o => o[pk]);
    const sq = { object_type: type, operation, filters, limit: 100 };
    const grounded = rows.length > 0;

    let answer;
    const human = type + (rows.length === 1 ? '' : 's');
    if (!grounded) {
      answer = 'No ' + type + ' records match that query.';
    } else if (operation === 'count') {
      answer = 'There ' + (rows.length === 1 ? 'is' : 'are') + ' ' + rows.length + ' ' + human +
        (filters.length ? ' matching ' + filters.map(f => f.property + ' ' + f.op + ' ' + f.value).join(', ') : '') + '.';
    } else {
      const names = rows.map(o => (titleKey ? o[titleKey] : o[pk]));
      answer = 'Found ' + rows.length + ' ' + human + ': ' + names.join(', ') + '.';
    }
    return {
      question, answer, grounded,
      structured_query: sq,
      source_object_type: type,
      source_object_ids: ids,
      source_objects: rows,
      result_count: rows.length
    };
  }

  /* ---------- route table ---------- */
  function delay(ms) { return new Promise(r => setTimeout(r, ms)); }
  function clone(x) { return JSON.parse(JSON.stringify(x)); }

  async function handle(method, path, body) {
    await delay(160 + Math.random() * 220); // feel like a network
    method = method.toUpperCase();

    if (path === '/meta') return clone(META);

    let m = path.match(/^\/objects\/([^/?]+)$/);
    if (m) {
      const type = decodeURIComponent(m[1]);
      const objs = STORE[type] || [];
      return { object_type: type, count: objs.length, objects: clone(objs) };
    }

    if (path === '/recommendations' && method === 'GET') {
      return { count: RECS.length, recommendations: clone(RECS) };
    }

    m = path.match(/^\/recommendations\/([^/]+)\/approve$/);
    if (m && method === 'POST') {
      const rec = RECS.find(r => r.action_id === m[1]);
      if (!rec) throw httpErr(404, 'No such recommendation');
      rec.status = 'approved';
      const so = STORE.RecommendedAction.find(a => a.action_id === rec.action_id);
      if (so) so.status = 'approved';
      return clone(rec);
    }

    m = path.match(/^\/recommendations\/([^/]+)\/execute$/);
    if (m && method === 'POST') {
      const rec = RECS.find(r => r.action_id === m[1]);
      if (!rec) throw httpErr(404, 'No such recommendation');
      rec.status = 'executed';
      const so = STORE.RecommendedAction.find(a => a.action_id === rec.action_id);
      if (so) so.status = 'executed';
      return {
        action_id: rec.action_id,
        status: 'executed',
        handler_receipt: {
          handler: rec.suggested_handler,
          work_order_id: 'WO-' + Math.floor(100000 + Math.random() * 899999),
          dispatched_to: 'Field Crew · North Substation',
          asset_id: 'asset-battery-01',
          action: 'inspect_and_derate',
          accepted_at: new Date().toISOString(),
          status: 'queued'
        }
      };
    }

    if (path === '/query' && method === 'POST') {
      return runQuery(body && body.question);
    }

    throw httpErr(404, 'Unknown route: ' + path);
  }

  function httpErr(status, msg) { const e = new Error(msg); e.status = status; return e; }

  window.OCT_MOCK = { handle, META, STORE, RECS };
})();
