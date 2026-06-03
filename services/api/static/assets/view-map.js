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

  let root, mapEl, sideEl;
  let selected = null;       // { type, id }
  let anomalyAssetIds = [];  // primary keys flagged by recommendations

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
    return root;
  }

  async function ensureData() {
    if (!O.State.meta) await O.loadMeta();
    if (Object.keys(O.State.objects).length < O.State.meta.object_types.length) await O.loadAllObjects();
    if (!O.State.recommendations.length) { try { await O.loadRecommendations(); } catch (e) {} }
    anomalyAssetIds = [];
    O.State.recommendations.forEach(r => (r.affected_entities || []).forEach(e => anomalyAssetIds.push(e.primary_key)));
  }

  function render() {
    clear(mapEl); clear(sideEl);
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
      // tether
      const ln = document.createElementNS(NS, 'line');
      ln.setAttribute('x1', p.x); ln.setAttribute('y1', p.y);
      ln.setAttribute('x2', ax); ln.setAttribute('y2', ay);
      ln.setAttribute('stroke', 'var(--line-strong)'); ln.setAttribute('stroke-width', '1');
      layerLinks.appendChild(ln);
      // satellite group
      const gg = document.createElementNS(NS, 'g');
      gg.setAttribute('class', 'mnode asset' + (flagged ? ' flagged' : '') + (isSel(assetType, aId) ? ' sel' : ''));
      gg.style.cursor = 'pointer';
      const statusCls = sp ? O.Onto.statusClass(a[sp.name]) : 's-neutral';
      const col = statusVar(statusCls);
      if (flagged) {
        const halo = document.createElementNS(NS, 'circle');
        halo.setAttribute('cx', ax); halo.setAttribute('cy', ay); halo.setAttribute('r', 9);
        halo.setAttribute('class', 'halo'); halo.setAttribute('fill', 'none');
        halo.setAttribute('stroke', 'var(--crit)'); halo.setAttribute('stroke-width', '1.5');
        gg.appendChild(halo);
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
    fo.setAttribute('x', p.x + 18); fo.setAttribute('y', p.y - 26); fo.setAttribute('width', 240); fo.setAttribute('height', 56);
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
      card.appendChild(h('div', { class: 'anomaly-banner' }, [
        h('div', { class: 'ab-top' }, [icon('anomaly', { width: 16, height: 16 }), h('b', null, 'Anomaly on this record')]),
        h('div', { class: 'muted', style: { fontSize: '12px', margin: '2px 0 10px' } }, rec ? rec.title : 'Flagged by the decision engine.'),
        h('button', { class: 'btn ok sm', onClick: () => document.dispatchEvent(new CustomEvent('oct:goto', { detail: { view: 'B', action: rec && rec.action_id } })) }, [
          'Investigate in Anomaly & Decision', icon('arrow', { width: 14, height: 14 })
        ])
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
