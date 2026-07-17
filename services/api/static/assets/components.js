/* ============================================================
   OCT — Shared UI components & DOM helpers.
   ============================================================ */
(function () {
  'use strict';
  const Onto = () => window.OCT.Onto;

  /* ---- tiny hyperscript ---- */
  function h(tag, attrs, children) {
    const el = document.createElement(tag);
    if (attrs) for (const k in attrs) {
      const v = attrs[k];
      if (v == null || v === false) continue;
      if (k === 'class') el.className = v;
      // SECURITY (PLAN-0040 C2 review): `html:` is the ONLY innerHTML sink. NEVER pass
      // draft/LLM-sourced or otherwise untrusted text here — it is parsed as markup (XSS).
      // Pass such text as a CHILD (textContent, safe) or via `text:`. Used today only for
      // static SVG/icon strings; the procedure render path correctly never uses it.
      else if (k === 'html') el.innerHTML = v;
      else if (k === 'text') el.textContent = v;
      else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v);
      else if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2).toLowerCase(), v);
      else if (k === 'dataset') Object.assign(el.dataset, v);
      else el.setAttribute(k, v);
    }
    if (children != null) appendChildren(el, children);
    return el;
  }
  function appendChildren(el, c) {
    if (Array.isArray(c)) c.forEach(x => appendChildren(el, x));
    else if (c instanceof Node) el.appendChild(c);
    else if (c != null && c !== false) el.appendChild(document.createTextNode(String(c)));
  }
  function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); return el; }

  /* ---- icons (stroke, 24-grid) ---- */
  const ICONS = {
    map: '<path d="M9 5 3 7v12l6-2 6 2 6-2V5l-6 2-6-2Z"/><path d="M9 5v12M15 7v12"/>',
    anomaly: '<path d="M12 3 2 20h20L12 3Z"/><path d="M12 10v4M12 17.5v.5"/>',
    ask: '<path d="M21 12a8 8 0 0 1-11.3 7.3L3 21l1.7-6.7A8 8 0 1 1 21 12Z"/>',
    flow: '<rect x="3" y="9" width="5" height="6" rx="1"/><rect x="16" y="9" width="5" height="6" rx="1"/><path d="M8 12h5M12 10l2 2-2 2"/>',
    refresh: '<path d="M21 12a9 9 0 1 1-2.6-6.4M21 4v5h-5"/>',
    arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    check: '<path d="m4 12 5 5L20 6"/>',
    play: '<path d="M7 5v14l11-7-11-7Z"/>',
    x: '<path d="M6 6l12 12M18 6 6 18"/>',
    chevron: '<path d="m9 6 6 6-6 6"/>',
    spark: '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2 2M16 16l2 2M18 6l-2 2M8 16l-2 2"/>',
    pin: '<path d="M12 21s7-6.3 7-11a7 7 0 1 0-14 0c0 4.7 7 11 7 11Z"/><circle cx="12" cy="10" r="2.5"/>',
    link: '<path d="M9 15 15 9M10 6l1-1a4 4 0 0 1 6 6l-1 1M14 18l-1 1a4 4 0 0 1-6-6l1-1"/>',
    db: '<ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    gauge: '<path d="M12 13l4-4M21 12a9 9 0 1 0-18 0"/><path d="M3 12h2M19 12h2M12 3v2"/>',
    cpu: '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3"/><rect x="10" y="10" width="4" height="4" rx="1"/>',
    bolt: '<path d="M13 2 4 14h6l-1 8 9-12h-6l1-8Z"/>',
    grid: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    receipt: '<path d="M6 3h12v18l-3-2-3 2-3-2-3 2V3Z"/><path d="M9 8h6M9 12h6"/>',
    // `person` is the trace-badge HUMAN actor glyph (PLAN-0080 L-4). Deliberately not
    // `check` — check already means "Approve"/"Dispatched" on the action buttons.
    person: '<circle cx="12" cy="8" r="3.5"/><path d="M5.5 20a6.5 6.5 0 0 1 13 0"/>',
    dot: '<circle cx="12" cy="12" r="4"/>'
  };
  function icon(name, attrs) {
    const a = Object.assign({ viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '1.6', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, attrs || {});
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    for (const k in a) svg.setAttribute(k, a[k]);
    svg.innerHTML = ICONS[name] || ICONS.dot;
    return svg;
  }

  /* ---- status badge from an enum value ---- */
  function badge(value, opts) {
    opts = opts || {};
    const cls = Onto().statusClass(value);
    return h('span', { class: 'badge ' + cls + (opts.solid ? ' solid' : '') }, [
      opts.led !== false ? h('span', { class: 'led' }) : null,
      String(value)
    ]);
  }

  /* ---- object-type tag ---- */
  function typeTag(typeName, glyphColor) {
    return h('span', { class: 'typetag' }, [
      h('span', { class: 'gl', style: glyphColor ? { background: glyphColor } : null }),
      typeName
    ]);
  }

  /* ---- affected-entity chip ---- */
  function entityChip(ent, onClick) {
    return h('button', { class: 'ent-chip', onClick: onClick || null }, [
      h('span', { class: 'et' }, ent.object_type),
      h('span', { class: 'en' }, ent.title || ent.primary_key),
      h('span', { class: 'eid mono' }, ent.primary_key)
    ]);
  }

  /* ---- timestamp formatting (UTC, demo-friendly: "HH:MM UTC · D Mon YYYY") ---- */
  const _MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function fmtTimestamp(val) {
    const d = new Date(val);
    if (isNaN(d.getTime())) return String(val);
    const hh = String(d.getUTCHours()).padStart(2, '0');
    const mm = String(d.getUTCMinutes()).padStart(2, '0');
    return hh + ':' + mm + ' UTC · ' + d.getUTCDate() + ' ' + _MONTHS[d.getUTCMonth()] + ' ' + d.getUTCFullYear();
  }

  /* ---- value formatting for detail rows ---- */
  function fmtValue(type, prop, obj) {
    const val = obj[prop.name];
    if (val == null || val === '') return h('span', { class: 'faint' }, '—');
    if (prop.type === 'enum') return badge(val);
    if (prop.type === 'timestamp' || prop.type === 'datetime')
      return h('span', { class: 'mono', style: { fontSize: '12px' } }, fmtTimestamp(val));
    if (prop.type === 'ref') {
      const r = Onto().resolveRef(type, prop.name, obj);
      const label = r && r.obj ? Onto().label(prop.target, r.obj) : val;
      const a = h('a', { href: '#', title: 'Go to ' + prop.target }, [
        label, h('span', { class: 'faint mono', style: { marginLeft: '6px', fontSize: '11px' } }, val)
      ]);
      a.addEventListener('click', (e) => {
        e.preventDefault();
        document.dispatchEvent(new CustomEvent('oct:navobj', { detail: { type: prop.target, id: val } }));
      });
      return a;
    }
    if (prop.type === 'float' || prop.type === 'date' || prop.type === 'datetime' || /id$/.test(prop.name))
      return h('span', { class: 'mono', style: { fontSize: '12px' } }, String(val));
    return document.createTextNode(String(val));
  }

  /* ---- detail panel: iterate a type's /meta properties ---- */
  function detailRows(type, obj) {
    const td = Onto().typeDef(type);
    const kv = h('div', { class: 'kv' });
    td.properties.forEach(p => {
      const v = fmtValue(type, p, obj);
      const valWrap = h('div', { class: 'v' + ((p.type === 'float' || /id$/.test(p.name)) ? ' mono' : '') });
      valWrap.appendChild(v);
      kv.appendChild(h('div', { class: 'row' }, [
        h('div', { class: 'k' }, p.name),
        valWrap
      ]));
    });
    return kv;
  }

  /* ---- reasoning trace stepper ---- */
  // The attribution channel. A kind resolves against the ONE registry in
  // trace-kinds.js (PLAN-0080 AC-1) — no substring sniffing, which was dishonest in
  // BOTH directions: it left 14 of 16 procedure-engine kinds unattributed AND
  // coloured `scored_rule_selected` as if it were the recommender's `rule_check`.
  // An unknown kind degrades VISIBLY (AC-4): raw token, `unmapped` style, and NO
  // actor claimed — asserting an attribution we do not have is the exact dishonesty
  // this replaces.
  function traceKind(kind) {
    const raw = String(kind == null ? '' : kind);
    const e = (window.OCT_TRACE_KINDS || {})[raw];
    if (!e) return { label: raw, cls: 'unmapped', actor: 'unknown', unmapped: true };
    return { label: e.label, cls: e.cls, actor: e.actor, unmapped: false };
  }
  // colour = mechanism (theme.css semantics), glyph = actor (L-4). `data-actor` is the
  // probe-able channel: icon() silently falls back to `dot` for an unknown name, so the
  // SVG alone cannot be asserted against.
  function traceBadge(kind, opts) {
    opts = opts || {};
    const t = traceKind(kind);
    const glyph = (window.OCT_TRACE_ACTOR_GLYPH || {})[t.actor];
    const el = h('span', {
      class: 'badge ' + t.cls,
      style: Object.assign({ textTransform: 'none' }, opts.style || {}),
      title: t.unmapped ? 'unmapped trace kind — raw engine token' : String(kind),
      dataset: { actor: t.actor }
    }, t.label);
    if (glyph) el.insertBefore(icon(glyph, { width: 11, height: 11 }), el.firstChild);
    return el;
  }
  function reasoningTrace(steps) {
    const wrap = h('ol', { class: 'trace' });
    (steps || []).forEach((s, i) => {
      const hasDetail = s.detail && Object.keys(s.detail).length;
      const detailBox = hasDetail ? h('div', { class: 'trace-detail' }, kvDump(s.detail)) : null;
      const item = h('li', { class: 'trace-step' }, [
        h('div', { class: 'trace-rail' }, [
          h('span', { class: 'trace-node ' + traceKind(s.kind).cls }, String(i + 1)),
          h('span', { class: 'trace-line' })
        ]),
        h('div', { class: 'trace-body' }, [
          h('div', { class: 'trace-top' }, [
            traceBadge(s.kind),
            s.step_id ? h('span', { class: 'faint mono', style: { fontSize: '10.5px' } }, s.step_id) : null,
            hasDetail ? h('button', { class: 'trace-toggle', onClick: (e) => {
              const open = item.classList.toggle('open');
              e.currentTarget.textContent = open ? 'Hide detail' : 'Show detail';
            } }, 'Show detail') : null
          ]),
          h('div', { class: 'trace-summary' }, s.summary),
          detailBox
        ].filter(Boolean))
      ]);
      wrap.appendChild(item);
    });
    return wrap;
  }

  /* ---- key/value dump of a detail object ---- */
  function kvDump(obj) {
    const tbl = h('div', { class: 'kvdump' });
    Object.keys(obj).forEach(k => {
      let v = obj[k];
      // scalar arrays read nicely comma-joined; an array/object of OBJECTS (e.g. the
      // governed_decision SoD tie naming the approver) must JSON-stringify — a plain
      // join() renders each element as the useless "[object Object]".
      if (Array.isArray(v) && v.every(x => x == null || typeof x !== 'object')) v = v.join(', ');
      else if (v != null && typeof v === 'object') v = JSON.stringify(v);
      tbl.appendChild(h('div', { class: 'kvdump-row' }, [
        h('span', { class: 'kvdump-k mono' }, k),
        h('span', { class: 'kvdump-v mono' }, String(v))
      ]));
    });
    return tbl;
  }

  /* ---- state blocks ---- */
  function loadingState(msg) {
    return h('div', { class: 'state' }, h('div', { class: 'box' }, [
      h('div', { class: 'spinner' }),
      h('p', null, msg || 'Loading…')
    ]));
  }
  function errorState(title, msg, onRetry) {
    return h('div', { class: 'state' }, h('div', { class: 'box' }, [
      h('div', { style: { color: 'var(--crit)', marginBottom: '10px' } }, icon('anomaly', { width: 26, height: 26 })),
      h('h3', null, title || 'Could not load'),
      h('p', null, msg || ''),
      onRetry ? h('button', { class: 'btn sm', style: { marginTop: '14px' }, onClick: onRetry }, 'Retry') : null
    ]));
  }

  window.OCT = window.OCT || {};
  Object.assign(window.OCT, {
    h, clear, icon, badge, typeTag, entityChip, fmtValue, fmtTimestamp, detailRows,
    reasoningTrace, traceKind, traceBadge, kvDump, loadingState, errorState
  });
})();
