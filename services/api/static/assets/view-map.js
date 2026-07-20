/* ============================================================
   View A — Operational Map
   Plots geo-bearing objects (Sites) on a schematic lat/lng canvas;
   groups referencing objects (Assets) under them; detail panel built
   by iterating /meta properties. Everything is ontology-driven.
   ============================================================ */
(function () {
  'use strict';
  const O = window.OCT;
  const { h, clear, icon, badge } = O;

  let root, mapEl, sideEl, tlEl;
  let selected = null;        // { type, id }
  let anomalyAssetIds = [];   // primary keys flagged by recommendations
  let resolvedAssetIds = [];  // flagged keys whose decision is executed (resolved)
  // PLAN-0084: in-flight governed runs keyed 'ObjectType|pk' (from /runs subject) —
  // a PARALLEL signal to the recommendation flags above, never coupled to them.
  let runsByAsset = {};
  const RUN_INFLIGHT = { waiting_human: 1, running: 1 };  // SD-C: never terminal states

  function geoColor(i) {
    const hues = [210, 150, 35, 280, 0];
    return 'oklch(0.70 0.12 ' + hues[i % hues.length] + ')';
  }

  function project(objs, geo, W, H, pad) {
    const lats = objs.map(o => +o[geo.lat]), lngs = objs.map(o => +o[geo.lng]);
    let minLa = Math.min(...lats), maxLa = Math.max(...lats);
    let minLo = Math.min(...lngs), maxLo = Math.max(...lngs);
    let spanLa = maxLa - minLa || 0.1, spanLo = maxLo - minLo || 0.1;
    // pad the geographic span so points aren't on the edge
    minLa -= spanLa * 0.35; maxLa += spanLa * 0.35;
    minLo -= spanLo * 0.35; maxLo += spanLo * 0.35;
    spanLa = maxLa - minLa; spanLo = maxLo - minLo;
    return (o) => ({
      x: pad + ((+o[geo.lng] - minLo) / spanLo) * (W - 2 * pad),
      y: pad + (1 - (+o[geo.lat] - minLa) / spanLa) * (H - 2 * pad)
    });
  }

  function build() {
    root = h('div', { class: 'view-inner mapview' });

    // header
    root.appendChild(h('div', { class: 'view-head' }, [
      h('div', null, [
        h('div', { class: 'eyebrow', style: { marginBottom: '4px' } }, 'View A · Operational Map'),
        h('h1', null, 'Where, and in what state'),
      ]),
      h('div', { class: 'flex' }),
      h('div', { class: 'view-head-meta', id: 'mapCounts' })
    ]));

    const body = h('div', { class: 'map-body' });
    mapEl = h('div', { class: 'map-canvas-wrap' });
    sideEl = h('aside', { class: 'map-side' });
    body.appendChild(mapEl);
    body.appendChild(sideEl);
    root.appendChild(body);

    // incident timeline rail (full width, below the map + side)
    tlEl = h('div', { class: 'map-timeline card' });
    root.appendChild(tlEl);
    return root;
  }

  async function ensureData() {
    if (!O.State.meta) await O.loadMeta();
    if (Object.keys(O.State.objects).length < O.State.meta.object_types.length) await O.loadAllObjects();
    // PLAN-0015 D4: refresh the decision-sensitive data on every mount so a
    // decision taken in Screen B — the status + approved_at/executed_at, and the
    // execute-time recovery reading — is reflected on return to Screen A.
    try { await O.loadRecommendations(); } catch (e) {}
    try { await O.loadObjects('OperationalEvent'); } catch (e) {}
    recomputeFlags();
    // PLAN-0084 Step 3: governed-run flags from /runs — a DIRECT fetch (the Monitor
    // getJSON precedent), NEVER O.API.request, which silently serves mock data on any
    // failure (api.js fallback). A runs-read failure must mean "no markers", not fake
    // markers: on any error the map renders fully with zero run flags (AC-5).
    try { computeRunFlags(await getRunsJSON()); } catch (e) { runsByAsset = {}; }
  }

  async function getRunsJSON() {
    const res = await fetch('/runs');
    const ct = res.headers.get('content-type') || '';
    if (!res.ok || !ct.includes('json')) throw new Error('runs unavailable');
    return res.json();
  }

  function computeRunFlags(payload) {
    runsByAsset = {};
    ((payload && payload.runs) || []).forEach(r => {
      const s = r.subject;
      if (!s || !s.object_type || !s.primary_key || !RUN_INFLIGHT[r.status]) return;
      const key = s.object_type + '|' + s.primary_key;   // exact type+pk, data-driven
      (runsByAsset[key] = runsByAsset[key] || []).push(r);
    });
  }

  function recomputeFlags() {
    anomalyAssetIds = []; resolvedAssetIds = [];
    O.State.recommendations.forEach(r => (r.affected_entities || []).forEach(e => {
      anomalyAssetIds.push(e.primary_key);
      if (r.status === 'executed') resolvedAssetIds.push(e.primary_key);
    }));
  }

  function render() {
    clear(mapEl); clear(sideEl); if (tlEl) clear(tlEl);
    const meta = O.State.meta;
    const geoTypes = O.Onto.geoTypes();
    if (!geoTypes.length) { mapEl.appendChild(O.errorState('No mappable objects', 'No object type in /meta exposes coordinates.')); return; }

    // counts header
    const counts = O.h('div', { class: 'counts' }, meta.object_types.map((t, i) =>
      h('span', { class: 'count-chip' }, [
        h('span', { class: 'cg', style: { background: geoColor(i) } }),
        h('b', null, (O.State.objects[t.name] || { count: 0 }).count),
        h('span', { class: 'muted' }, t.name + ((O.State.objects[t.name] || {}).count === 1 ? '' : 's'))
      ])
    ));
    const ch = document.getElementById('mapCounts'); if (ch) { clear(ch); ch.appendChild(counts); }

    // ---- SVG canvas ----
    const W = 1000, H = 660, pad = 90;
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    svg.setAttribute('class', 'map-canvas');
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');

    // grid + frame
    let bg = '<defs><pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
      + '<path d="M40 0H0V40" fill="none" stroke="rgba(255,255,255,0.035)" stroke-width="1"/></pattern></defs>';
    bg += '<rect x="0" y="0" width="' + W + '" height="' + H + '" fill="url(#grid)"/>';
    bg += '<rect x="1" y="1" width="' + (W - 2) + '" height="' + (H - 2) + '" fill="none" stroke="var(--line)" stroke-width="1"/>';
    // corner ticks
    [[16, 16], [W - 16, 16], [16, H - 16], [W - 16, H - 16]].forEach(([x, y]) => {
      bg += '<circle cx="' + x + '" cy="' + y + '" r="2" fill="var(--tx-3)"/>';
    });
    svg.innerHTML = bg;

    // gather geo objects across all geo types (Sites here)
    const allGeo = [];
    geoTypes.forEach(t => (O.State.objects[t.name] || { objects: [] }).objects.forEach(o => allGeo.push({ type: t.name, o })));
    const geo0 = O.Onto.geoProps(geoTypes[0].name);
    const proj = project(allGeo.map(g => g.o), geo0, W, H, pad);

    // links: assets grouped under their referenced site — draw faint tether for cluster
    const layerLinks = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    const layerNodes = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    svg.appendChild(layerLinks); svg.appendChild(layerNodes);

    // coordinate readouts (lat/lng axes labels)
    allGeo.forEach((g, i) => {
      const p = proj(g.o);
      drawSite(layerNodes, layerLinks, g, p, i);
    });

    mapEl.appendChild(h('div', { class: 'map-stage' }, [
      svg,
      h('div', { class: 'map-axislabel tl mono' }, 'LAT / LNG SCHEMATIC'),
      h('div', { class: 'map-axislabel br mono' }, meta.namespace ? (meta.vertical + ' · ' + meta.namespace) : meta.vertical)
    ]));

    // The contextual panel — the selected record's detail, or the "select a node"
    // hint — is always the top slot (primary focus / reading order), with the
    // legend a stable reference anchored BELOW in both states. Keeping the legend
    // fixed at the bottom avoids the top/bottom swap between idle and selected.
    // The side column scrolls (views.css .map-side) so the legend stays reachable.
    if (selected) renderDetail(selected.type, selected.id);
    else renderHint();
    renderLegend();

    renderTimeline();
  }

  function assetsForSite(siteId) {
    const assetType = (O.State.meta.object_types.find(t =>
      O.Onto.refs(t.name).some(r => r.target && O.Onto.geoProps(r.target))) || {}).name;
    if (!assetType) return { type: null, list: [] };
    const ref = O.Onto.refs(assetType).find(r => O.Onto.geoProps(r.target));
    const list = (O.State.objects[assetType] || { objects: [] }).objects.filter(a => a[ref.name] === siteId);
    return { type: assetType, ref: ref.name, list };
  }

  function drawSite(layerNodes, layerLinks, g, p, idx) {
    const NS = 'http://www.w3.org/2000/svg';
    const siteType = g.type, site = g.o;
    const siteId = site[O.Onto.pk(siteType)];
    const label = O.Onto.label(siteType, site);
    const color = geoColor(idx);
    const { type: assetType, list } = assetsForSite(siteId);

    // asset satellites around the site
    const R = 46;
    list.forEach((a, k) => {
      const ang = (-90 + (k - (list.length - 1) / 2) * 30) * Math.PI / 180;
      const ax = p.x + Math.cos(ang) * R, ay = p.y + Math.sin(ang) * R;
      const aId = a[O.Onto.pk(assetType)];
      const sp = O.Onto.statusProp(assetType);
      const flagged = anomalyAssetIds.includes(aId);
      const resolved = resolvedAssetIds.includes(aId);
      const govRuns = runsByAsset[assetType + '|' + aId] || [];
      // tether
      const ln = document.createElementNS(NS, 'line');
      ln.setAttribute('x1', p.x); ln.setAttribute('y1', p.y);
      ln.setAttribute('x2', ax); ln.setAttribute('y2', ay);
      ln.setAttribute('stroke', 'var(--line-strong)'); ln.setAttribute('stroke-width', '1');
      layerLinks.appendChild(ln);
      // satellite group
      const gg = document.createElementNS(NS, 'g');
      gg.setAttribute('class', 'mnode asset' + (flagged ? ' flagged' : '') + (resolved ? ' resolved' : '') + (govRuns.length ? ' gov' : '') + (isSel(assetType, aId) ? ' sel' : ''));
      gg.style.cursor = 'pointer';
      const statusCls = sp ? O.Onto.statusClass(a[sp.name]) : 's-neutral';
      const col = statusVar(statusCls);
      if (flagged) {
        // The anomaly ring: pulsing red while active, a static green ring once
        // the decision is executed (PLAN-0015 D4 — the map node "resolves").
        const halo = document.createElementNS(NS, 'circle');
        halo.setAttribute('cx', ax); halo.setAttribute('cy', ay); halo.setAttribute('r', 9);
        halo.setAttribute('class', 'halo' + (resolved ? ' resolved' : '')); halo.setAttribute('fill', 'none');
        halo.setAttribute('stroke', resolved ? 'var(--ok)' : 'var(--crit)'); halo.setAttribute('stroke-width', '1.5');
        gg.appendChild(halo);
      }
      if (govRuns.length) {
        // PLAN-0084 SD-C: the DISTINCT "governed run in flight" marker — a dashed amber
        // ring, deliberately separate from the red anomaly halo above ("anomaly detected"
        // ≠ "governed run awaiting a human" — attribution legibility, PLAN-0080).
        const gr = document.createElementNS(NS, 'circle');
        gr.setAttribute('cx', ax); gr.setAttribute('cy', ay); gr.setAttribute('r', 12);
        gr.setAttribute('class', 'run-halo'); gr.setAttribute('fill', 'none');
        gr.setAttribute('stroke', 'var(--warn)'); gr.setAttribute('stroke-width', '1.5');
        gr.setAttribute('stroke-dasharray', '3 3');
        gg.appendChild(gr);
      }
      const c = document.createElementNS(NS, 'circle');
      c.setAttribute('cx', ax); c.setAttribute('cy', ay); c.setAttribute('r', 6.5);
      c.setAttribute('fill', 'var(--bg-2)'); c.setAttribute('stroke', col); c.setAttribute('stroke-width', '2');
      gg.appendChild(c);
      const inner = document.createElementNS(NS, 'circle');
      inner.setAttribute('cx', ax); inner.setAttribute('cy', ay); inner.setAttribute('r', 2.5); inner.setAttribute('fill', col);
      gg.appendChild(inner);
      gg.addEventListener('click', (e) => { e.stopPropagation(); select(assetType, aId); });
      layerNodes.appendChild(gg);
    });

    // site marker
    const gNode = document.createElementNS(NS, 'g');
    gNode.setAttribute('class', 'mnode site' + (isSel(siteType, siteId) ? ' sel' : ''));
    gNode.style.cursor = 'pointer';
    const ring = document.createElementNS(NS, 'circle');
    ring.setAttribute('cx', p.x); ring.setAttribute('cy', p.y); ring.setAttribute('r', 13);
    ring.setAttribute('fill', 'var(--bg-1)'); ring.setAttribute('stroke', color); ring.setAttribute('stroke-width', '2.5');
    gNode.appendChild(ring);
    const dot = document.createElementNS(NS, 'circle');
    dot.setAttribute('cx', p.x); dot.setAttribute('cy', p.y); dot.setAttribute('r', 4.5); dot.setAttribute('fill', color);
    gNode.appendChild(dot);
    // label plate
    const fo = document.createElementNS(NS, 'foreignObject');
    // Label plate sits BELOW the node: the asset satellites always fan into the upper
    // hemisphere (angles centered on -90°, see the arc above), so the space beneath the
    // site is the only region guaranteed clear of them — placing the plate up-and-right
    // let the rightmost satellite (~ -30°) collide with the label (map-legibility fix).
    fo.setAttribute('x', p.x + 18); fo.setAttribute('y', p.y + 14); fo.setAttribute('width', 240); fo.setAttribute('height', 56);
    const plate = h('div', { class: 'site-plate', xmlns: 'http://www.w3.org/1999/xhtml' }, [
      h('div', { class: 'sp-name' }, label),
      h('div', { class: 'sp-meta mono' }, [
        site[O.Onto.statusProp(siteType) ? O.Onto.statusProp(siteType).name : ''] || siteType,
        h('span', { class: 'faint' }, '  ' + (+site[O.Onto.geoProps(siteType).lat]).toFixed(2) + ', ' + (+site[O.Onto.geoProps(siteType).lng]).toFixed(2))
      ]),
      h('div', { class: 'sp-assets muted' }, list.length + ' ' + (assetType || 'asset') + (list.length === 1 ? '' : 's'))
    ]);
    fo.appendChild(plate);
    gNode.appendChild(fo);
    gNode.addEventListener('click', (e) => { e.stopPropagation(); select(siteType, siteId); });
    layerNodes.appendChild(gNode);
  }

  function statusVar(cls) {
    return { 's-ok': 'var(--ok)', 's-info': 'var(--info)', 's-warn': 'var(--warn)', 's-crit': 'var(--crit)', 's-neutral': 'var(--neutral)' }[cls] || 'var(--neutral)';
  }
  function isSel(type, id) { return selected && selected.type === type && selected.id === id; }
  function select(type, id) { selected = { type, id }; render(); }

  /* ---------- side panel ---------- */
  function renderLegend() {
    const meta = O.State.meta;
    const card = h('div', { class: 'card legend' }, [
      h('div', { class: 'legend-head eyebrow' }, 'Legend · from /meta'),
      h('div', { class: 'legend-types' }, meta.object_types.map((t, i) =>
        h('div', { class: 'legend-row' }, [
          h('span', { class: 'cg', style: { background: O.Onto.geoProps(t.name) ? geoColor(i) : 'transparent', border: O.Onto.geoProps(t.name) ? 'none' : '1px dashed var(--line-strong)' } }),
          h('span', { class: 'lt-name' }, t.name),
          h('span', { class: 'faint mono lt-pk' }, t.primary_key || '')
        ])
      )),
      h('div', { class: 'divider', style: { margin: '4px 0 10px' } }),
      h('div', { class: 'legend-head eyebrow' }, 'Status enums'),
      h('div', { class: 'legend-enums' }, enumLegend())
    ]);
    sideEl.appendChild(card);
  }
  function enumLegend() {
    const seen = new Set(); const out = [];
    O.State.meta.object_types.forEach(t => {
      const sp = O.Onto.statusProp(t.name);
      if (sp && sp.enum) sp.enum.forEach(v => { if (!seen.has(v)) { seen.add(v); out.push(O.badge(v)); } });
    });
    return h('div', { class: 'enum-wrap' }, out);
  }

  function renderHint() {
    const n = anomalyAssetIds.length;
    const anomNote = n ? (' ' + (n === 1 ? 'One record is' : n + ' records are') + ' reporting an anomaly — ringed in red.') : '';
    sideEl.appendChild(h('div', { class: 'card map-hint' }, [
      h('div', { class: 'mh-icon' }, icon('pin', { width: 20, height: 20 })),
      h('div', { class: 'mh-title' }, 'Select a node'),
      h('div', { class: 'muted', style: { fontSize: '12.5px' } }, 'Click any node on the canvas to inspect its full record.' + anomNote)
    ]));
  }

  function renderDetail(type, id) {
    const pk = O.Onto.pk(type);
    const obj = (O.State.objects[type] || { objects: [] }).objects.find(o => o[pk] === id);
    if (!obj) return;
    const flagged = anomalyAssetIds.includes(id);
    const card = h('div', { class: 'card detail-card' });
    // header
    card.appendChild(h('div', { class: 'detail-head' }, [
      h('div', null, [
        O.typeTag(type),
        h('div', { class: 'detail-title' }, O.Onto.label(type, obj))
      ]),
      h('button', { class: 'iconbtn', onClick: () => { selected = null; render(); } }, icon('x'))
    ]));

    if (flagged) {
      const rec = O.State.recommendations.find(r => (r.affected_entities || []).some(e => e.primary_key === id));
      const status = rec ? rec.status : 'proposed';
      const resolved = status === 'executed';
      // The recorded decision times (PLAN-0015 D3) — shown once present.
      const times = [];
      if (rec && rec.approved_at) times.push(h('div', { class: 'dt-row' }, [h('span', { class: 'dt-k' }, 'Approved'), h('span', { class: 'dt-v mono' }, O.fmtTimestamp(rec.approved_at))]));
      if (rec && rec.executed_at) times.push(h('div', { class: 'dt-row' }, [h('span', { class: 'dt-k' }, 'Executed'), h('span', { class: 'dt-v mono' }, O.fmtTimestamp(rec.executed_at))]));
      card.appendChild(h('div', { class: 'anomaly-banner' + (resolved ? ' resolved' : '') }, [
        h('div', { class: 'ab-top' }, [
          icon(resolved ? 'check' : 'anomaly', { width: 16, height: 16 }),
          h('b', null, resolved ? 'Resolved — action executed' : 'Anomaly on this record'),
          rec ? O.badge(status, { solid: true }) : null
        ].filter(Boolean)),
        h('div', { class: 'muted', style: { fontSize: '12px', margin: '2px 0 10px' } }, rec ? rec.title : 'Flagged by the decision engine.'),
        times.length ? h('div', { class: 'decision-times' }, times) : null,
        resolved ? null : h('button', { class: 'btn ok sm', onClick: () => document.dispatchEvent(new CustomEvent('oct:goto', { detail: { view: 'B', action: rec && rec.action_id } })) }, [
          'Investigate in Anomaly & Decision', icon('arrow', { width: 14, height: 14 })
        ])
      ].filter(Boolean)));
    }

    // PLAN-0084: the node's in-flight governed runs → jump to the EXACT run in Monitor.
    // Newest-first (the /runs list order), capped per SD-E; the tail line opens Monitor
    // unfiltered. Fully data-driven from /runs `subject` — no hardcoded ids (ui.md).
    const nodeRuns = runsByAsset[type + '|' + id] || [];
    if (nodeRuns.length) {
      const CAP = 5;
      const rows = nodeRuns.slice(0, CAP).map(r =>
        h('div', { class: 'gov-run-row' }, [
          h('span', { class: 'mono grr-id', title: r.run_id }, r.run_id),
          O.badge(r.status),
          h('button', {
            class: 'btn sm gov-open',
            onClick: () => document.dispatchEvent(new CustomEvent('oct:goto', { detail: { view: 'H', run: r.run_id } }))
          }, ['Open in Monitor ', icon('arrow', { width: 13, height: 13 })])
        ]));
      if (nodeRuns.length > CAP) {
        rows.push(h('button', {
          class: 'btn sm gov-more',
          onClick: () => document.dispatchEvent(new CustomEvent('oct:goto', { detail: { view: 'H' } }))
        }, '+' + (nodeRuns.length - CAP) + ' more — open Monitor'));
      }
      card.appendChild(h('div', { class: 'detail-children gov-runs' }, [
        h('div', { class: 'eyebrow', style: { marginBottom: '8px' } }, 'Governed runs · in flight'),
        ...rows
      ]));
    }

    card.appendChild(h('div', { class: 'detail-body' }, O.detailRows(type, obj)));

    // grouped children (assets under a site)
    const { type: assetType, list } = assetsForSite(id);
    if (assetType && list.length && type !== assetType) {
      card.appendChild(h('div', { class: 'detail-children' }, [
        h('div', { class: 'eyebrow', style: { padding: '12px 0 8px' } }, assetType + 's at this ' + type + ' · ' + list.length),
        h('div', { class: 'child-list' }, list.map(a => {
          const aId = a[O.Onto.pk(assetType)];
          const sp = O.Onto.statusProp(assetType);
          return h('button', { class: 'child-row' + (anomalyAssetIds.includes(aId) ? ' flagged' : ''), onClick: () => select(assetType, aId) }, [
            h('span', { class: 'cr-name' }, O.Onto.label(assetType, a)),
            sp ? O.badge(a[sp.name]) : null,
            anomalyAssetIds.includes(aId) ? h('span', { class: 'cr-warn' }, icon('anomaly', { width: 14, height: 14 })) : null
          ]);
        }))
      ]));
    }
    sideEl.appendChild(card);
  }

  /* ---------- incident timeline rail ---------- */
  function tlPad(n) { return String(n).padStart(2, '0'); }
  function tlHHMM(val) { const d = new Date(val); return tlPad(d.getUTCHours()) + ':' + tlPad(d.getUTCMinutes()); }
  function tlDate(val) {
    const M = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const d = new Date(val);
    return d.getUTCDate() + ' ' + M[d.getUTCMonth()] + ' ' + d.getUTCFullYear();
  }
  function renderTimeline() {
    if (!tlEl) return;
    const evType = 'OperationalEvent';
    const store = O.State.objects[evType];
    const td = O.Onto.typeDef(evType);
    if (!store || !store.objects.length || !td) return;
    const tsProp = (td.properties.find(p => p.type === 'timestamp' || p.type === 'datetime') || {}).name;
    if (!tsProp) return;
    const sevProp = (O.Onto.statusProp(evType) || {}).name;
    const pkE = O.Onto.pk(evType);
    let events = store.objects.filter(e => e[tsProp]).slice()
      .sort((a, b) => new Date(a[tsProp]) - new Date(b[tsProp]));
    if (!events.length) return;

    // Scope the rail to the selected site / asset so it reflects what the
    // operator is inspecting (a selected event scopes to its own site); with
    // nothing selected it shows every site's events. This makes it an
    // operational timeline, not a single stuck incident.
    let scopeLabel = 'all sites';
    if (selected) {
      let filterId = selected.id, labelType = selected.type, labelId = selected.id;
      if (selected.type === evType) {
        const ev = store.objects.find(e => e[pkE] === selected.id);
        if (ev && ev.site_id) { filterId = ev.site_id; labelType = null; labelId = ev.site_id; }
      }
      const inScope = events.filter(e => e.asset_id === filterId || e.site_id === filterId);
      if (inScope.length) {
        events = inScope;
        const lt = labelType || (O.Onto.geoTypes()[0] || {}).name;
        const lo = lt ? (O.State.objects[lt] || { objects: [] }).objects.find(o => o[O.Onto.pk(lt)] === labelId) : null;
        scopeLabel = lo ? O.Onto.label(lt, lo) : String(labelId);
      }
    }

    // The pulsing "breach" hero is the single most-severe reading (severity
    // 'critical'); an alarm (severity 'error') stays red but does not pulse.
    const isCrit = (e) => sevProp && String(e[sevProp]).toLowerCase() === 'critical';

    // Decision beats for an in-scope incident (PLAN-0015 D4): the operator's
    // approve / execute clicks, recorded server-side (approved_at/executed_at),
    // laid on the SAME time axis as the events. A recommendation is in scope when
    // its affected entity appears among the scoped events' *_id fields (generic
    // over asset_id / shipment_id — AC-template). On 'executed' the incident
    // resolves: the breach marker + map node turn green/✓.
    const scopedIds = new Set();
    events.forEach(e => Object.keys(e).forEach(k => { if (/_id$/.test(k) && e[k] != null) scopedIds.add(e[k]); }));
    let incidentStatus = null;
    const decisions = [];
    (O.State.recommendations || []).forEach(r => {
      if (!(r.affected_entities || []).some(e => scopedIds.has(e.primary_key))) return;
      incidentStatus = r.status;
      if (r.approved_at) decisions.push({ ts: r.approved_at, kind: 'approved', rec: r });
      if (r.executed_at) decisions.push({ ts: r.executed_at, kind: 'executed', rec: r });
    });
    const resolved = incidentStatus === 'executed';

    // Unified, time-sorted beats: operational events + decision beats. Even
    // chronological spacing (4%..96%) so every beat is legible and the climax
    // never overlaps; the per-marker time labels carry the real timing.
    const beats = events.map(e => ({ ts: e[tsProp], kind: 'event', e: e }))
      .concat(decisions)
      .filter(b => b.ts)
      .sort((a, b) => new Date(a.ts) - new Date(b.ts));
    const n = beats.length;
    const xOf = (i) => (n <= 1 ? 50 : 4 + (i / (n - 1)) * 92);

    tlEl.appendChild(h('div', { class: 'tl-head' }, [
      h('span', { class: 'eyebrow' }, 'Operational timeline'),
      h('span', { class: 'faint mono', style: { fontSize: '10.5px' } }, tlDate(events[0][tsProp]) + ' · ' + scopeLabel),
      incidentStatus ? h('span', { class: 'tl-status ' + O.Onto.statusClass(incidentStatus) }, [
        icon(resolved ? 'check' : 'anomaly', { width: 12, height: 12 }),
        resolved ? 'Resolved' : incidentStatus
      ]) : null,
      h('div', { class: 'tl-legend' }, [
        h('span', { class: 'tl-leg s-info' }, [h('i'), 'normal']),
        h('span', { class: 'tl-leg s-warn' }, [h('i'), 'warning']),
        h('span', { class: 'tl-leg s-crit' }, [h('i'), 'critical']),
      ]),
    ].filter(Boolean)));

    const track = h('div', { class: 'tl-track' }, h('div', { class: 'tl-axis' }));
    const scale = h('div', { class: 'tl-scale' });
    beats.forEach((b, i) => {
      const left = xOf(i) + '%';
      if (b.kind === 'event') {
        const e = b.e;
        const id = e[pkE];
        const cls = sevProp ? O.Onto.statusClass(e[sevProp]) : 's-neutral';
        const breach = isCrit(e);
        const breachResolved = breach && resolved;
        track.appendChild(h('button', {
          class: 'tl-marker ' + (breachResolved ? 's-ok' : cls) + (breach ? ' breach' : '') + (breachResolved ? ' resolved' : '') + (isSel(evType, id) ? ' sel' : ''),
          style: { left: left },
          title: tlHHMM(e[tsProp]) + ' · ' + (e.description || e.event_type || id),
          onClick: (ev) => { ev.stopPropagation(); select(evType, id); },
        }, [
          (breach && !breachResolved) ? h('span', { class: 'tl-pulse' }) : null,
          breachResolved ? icon('check', { width: 13, height: 13, class: 'tl-check' }) : h('span', { class: 'tl-dot' })
        ].filter(Boolean)));
        scale.appendChild(h('span', {
          class: 'tl-tick' + (breach ? ' breach' : '') + (breachResolved ? ' resolved' : ''),
          style: { left: left },
        }, tlHHMM(e[tsProp])));
      } else {
        // decision beat — approve (intermediate, info) / execute (resolves, ok)
        const isExec = b.kind === 'executed';
        track.appendChild(h('button', {
          class: 'tl-marker tl-decision ' + (isExec ? 's-ok' : 's-info'),
          style: { left: left },
          title: (isExec ? 'Decision executed · ' : 'Decision approved · ') + O.fmtTimestamp(b.ts),
          onClick: (ev) => { ev.stopPropagation(); document.dispatchEvent(new CustomEvent('oct:goto', { detail: { view: 'B', action: b.rec && b.rec.action_id } })); },
        }, h('span', { class: 'tl-decision-dot' }, icon('check', { width: 10, height: 10 }))));
        scale.appendChild(h('span', {
          class: 'tl-tick tl-decision-tick ' + (isExec ? 's-ok' : 's-info'),
          style: { left: left },
        }, (isExec ? 'exec' : 'appr') + ' ' + tlHHMM(b.ts)));
      }
    });
    tlEl.appendChild(track);
    tlEl.appendChild(scale);
  }

  /* ---------- lifecycle ---------- */
  async function mount(container) {
    clear(container);
    container.appendChild(build());
    mapEl.appendChild(O.loadingState('Loading operational picture…'));
    try {
      await ensureData();
      render();
    } catch (e) {
      clear(mapEl); mapEl.appendChild(O.errorState('Could not load map', String(e.message || e), () => mount(container)));
    }
  }
  function focusObject(type, id) { selected = { type, id }; if (mapEl) render(); }

  window.OCT.ViewMap = { mount, focusObject };
})();
