// PLAN-0126 Step 2 — the stage-1 prototype's scene and story track, as a same-origin ES module.
import * as THREE from './three.module.min.js?v=160'; // vendored Three.js 0.160.0 (PLAN-0126 Step 1)

/* =====================================================================
   1–3. THE PINNED DATA — graph, procedure, rules and Act-4 cases.
   They live in story-data.js (window.STORY_DATA): one strict-JSON block
   that tests/api/test_story_drift.py pins against the repo's real
   ontology loader, procedure loader, sourcing rule and seed (PLAN-0126
   SD-3 = b). This page evaluates NO business rule — a case's outcome is
   read from its pinned `expected`, never computed here. The only check
   that runs in the browser is the closed-vocabulary schema check below.
   ===================================================================== */
const DATA = window.STORY_DATA;
const OUTCOMES = new Set(['ok', 'fail', 'approved']);
const BASES = new Set(['under_threshold', 'three_quotes', 'sole_source_justified', 'quotes_required']); // sourcing.py

function schemaProblems(d) {
  if (!d || typeof d !== 'object') return ['window.STORY_DATA is missing'];
  const problems = [];
  const o = d.ontology || {}, pr = d.procedure || {}, r = d.rules || {};
  if (!Array.isArray(o.object_types) || !o.object_types.length) problems.push('ontology.object_types');
  if (!Array.isArray(o.link_types) || !o.link_types.length) problems.push('ontology.link_types');
  if (!Array.isArray(o.undeclared_refs)) problems.push('ontology.undeclared_refs');
  if (!d.emitters || !Object.keys(d.emitters).length) problems.push('emitters');
  if (!Array.isArray(pr.steps) || !pr.steps.length || !pr.gates) problems.push('procedure');
  else if (!Array.isArray(pr.llm_assist_steps) || pr.llm_assist_steps.length !== 1 || !pr.gates[pr.llm_assist_steps[0]]) problems.push('procedure.llm_assist_steps');
  if (!Array.isArray(r.tiers) || !r.tiers.length) problems.push('rules.tiers');
  if (!Array.isArray(d.cases) || !d.cases.length) problems.push('cases');
  else d.cases.forEach((c, i) => {
    const e = (c && c.expected) || {};
    if (!OUTCOMES.has(e.outcome)) problems.push(`cases[${i}].expected.outcome`);
    if (!BASES.has(e.basis)) problems.push(`cases[${i}].expected.basis`);
    if (!Array.isArray(r.tiers) || !r.tiers.some(t => t.role === e.tier_role)) problems.push(`cases[${i}].expected.tier_role`);
  });
  return problems;
}
const PROBLEMS = schemaProblems(DATA);
if (PROBLEMS.length) {
  // A page that cannot trust its data says so on screen instead of narrating it.
  document.getElementById('cap-act').textContent = 'ข้อมูลของหน้านี้ไม่ผ่านการตรวจ';
  document.getElementById('cap-th').textContent = 'story-data.js ไม่ครบหรือผิดรูป — หน้านี้จะไม่เล่าเรื่องจากข้อมูลที่ตรวจไม่ผ่าน';
  document.getElementById('cap-sub').textContent = PROBLEMS.join(' · ');
  throw new Error('STORY_DATA failed its schema check: ' + PROBLEMS.join(', '));
}

const OBJECT_TYPES = DATA.ontology.object_types;
const LINK_TYPES = DATA.ontology.link_types;            // [name, from, to]
const UNDECLARED_REFS = DATA.ontology.undeclared_refs;  // [from, to] — `type: ref` with no link_types entry, drawn dashed
const EMITTERS = Object.values(DATA.emitters);          // display labels, in block order
const STEPS = DATA.procedure.steps.map(s => {
  const g = DATA.procedure.gates[s.id];
  return { ...s, gate: g ? (g.kind === 'rule_gate' ? 1 : 2) : undefined };
});
const DOA_TIERS = DATA.rules.tiers;                     // persona order on the ladder
// The step that carries llm_assist, and its autonomy, both read from the pinned block. This line
// was hand-typed as `fulfill · …` in v1, and fulfill's llm_assist is null (s309).
const ASSIST_STEP = DATA.procedure.llm_assist_steps[0];
const ASSIST_SUB = `${ASSIST_STEP} · autonomy: ${DATA.procedure.gates[ASSIST_STEP].autonomy} · llm_assist: advisory`;
const ACT4_CASES = DATA.cases;

/* =====================================================================
   4. THE STORY TRACK — acts, captions, camera keys, focus, sources.
   Captions obey the intro-video rulings: barely say AI, no URL, no band
   numeral read out, tamper-evident (never immutable), and never "the
   model decides nothing" — the honest claim is who holds the authority.
   ===================================================================== */
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const ACTS = [
  { code: '0', name: 'เปิดเรื่อง', start: 0, end: 8,
    focus: { hero: 1, lattice: .35, rail: .25, human: .25, codegen: .2, narrative: .2, existing: .15, ask: .12 },
    cam: [[0, V(2, 6, 46), V(2, 0, 0)], [8, V(2, 4, 37), V(2, 0, 0)]],
    captions: [
      [0, 'รถหกล้อ truck-01 เพลาขาดกลางทางแถวปากช่อง — ของเต็มคัน ต้องถึงโคราชก่อนสี่โมงเย็น', 'event-reading-02 · severity: critical · อู่เสนอราคาซ่อม ฿48,000'],
      [4.2, 'vero-lite คือเครื่องยนต์ที่ เฝ้าดู → ตัดสิน → ขออนุมัติ → ลงมือ ตามกติกาของกองรถคุณเอง', 'monitor → decide → approve → act'],
    ],
    sources: [['verticals/fleet_maintenance/data_adapter/synthetic.py:283-303', 'เหตุการณ์ ฿48,000 ที่ปากช่อง (ข้อมูลตัวอย่าง)'],
              ['CLAUDE.md §3 · ADR-0032 D6', 'vero-lite เป็นเครื่องยนต์ monitor→decide→approve→act']] },
  { code: '1a', name: 'เรื่องเล่า → โครงสร้าง', start: 8, end: 22,
    focus: { narrative: 1, lattice: 1, existing: .2, codegen: .12, rail: .12, human: .15, ask: .08 },
    cam: [[8.8, V(-15, 4, 18), V(-13, 1.5, 0)], [22, V(-10, 2.5, 17), V(-8, .6, 0)]],
    captions: [
      [8, 'กติกาของกองรถกระจายอยู่ในสายโทรศัพท์ กลุ่ม LINE สมุดจด และในหัวช่างใหญ่', 'ยังไม่มีโครงสร้าง — ทุกคนจำคนละแบบ'],
      [14, 'เราเขียนมันลงเป็นโครงสร้างเดียว — รถ อู่ เหตุการณ์ เคสซ่อม ใบเสนอราคา', 'fleet_maintenance_v0.yaml · object_types 10 · link_types 7'],
    ],
    sources: [['verticals/fleet_maintenance/ontology/fleet_maintenance_v0.yaml:33-575', 'object type 10 ชนิด · link type 7 เส้น · ref อีก 4 เส้นที่ไม่ได้ประกาศเป็น link (เส้นประ)'],
              ['verticals/fleet_maintenance/procedures.yaml:262-265', 'สัญญาณเดิมอยู่ในกลุ่ม LINE และสมุดจด']] },
  { code: '1b', name: 'ข้อมูลเดิมไม่ต้องรื้อ', start: 22, end: 35,
    focus: { existing: 1, lattice: 1, narrative: .3, codegen: .12, rail: .12, human: .15, ask: .08 },
    cam: [[22.8, V(-15, -2.5, 18), V(-13, -2.2, 0)], [35, V(-10, -.5, 18), V(-9, -1, 0)]],
    captions: [
      [22, 'ข้อมูลที่มีอยู่แล้วต่อเข้ามาได้ — แต่ผ่านเข้ามาเฉพาะฟิลด์ที่ประกาศไว้ในโครงสร้างเท่านั้น', 'db_objects.py · allowlist อ่านจาก YAML — คอลัมน์ใหม่ถูกกันไว้จนกว่าจะมีคนประกาศ'],
      [28.5, 'ส่วนที่ไม่เคยมีใครเขียนไว้ คนต้องเติมเอง: เพดานซ่อมของแต่ละคัน ระยะเข้าศูนย์ คำเรียกไทย–อังกฤษ', 'pm_import.py · CSV เข้ามาเป็นข้อเสนอ — คนยืนยันทีละแถว'],
    ],
    sources: [['verticals/fleet_maintenance/data_adapter/db_objects.py:1-22', 'ตารางเคสซ่อม 3 ตาราง ถูกฉายผ่าน allowlist ของ property ที่ YAML ประกาศ'],
              ['verticals/fleet_maintenance/pm_import.py:11-21', 'CSV เลขไมล์ → ข้อเสนอเท่านั้น ไม่เขียนอะไร จนกว่าคนยืนยัน'],
              ['verticals/fleet_maintenance/ontology/fleet_maintenance_v0.yaml:72-95', 'เพดานซ่อมต่อคัน และจุดเข้าศูนย์ที่ต้องมีคนยืนยัน']],
    notClaimed: ['ภาพนี้ไม่ได้อ้างว่าระบบดึงโครงสร้างจากฐานข้อมูลเดิมได้เอง — ยังไม่มีโค้ดส่วนนั้น'] },
  { code: '2', name: 'ต้นฉบับเดียว ของเจ็ดอย่าง', start: 35, end: 50,
    focus: { lattice: 1, codegen: 1, narrative: .1, existing: .1, rail: .3, human: .15, ask: .1 },
    cam: [[35.8, V(-7, .5, 11), V(-6.5, 0, 0)], [42, V(-4, 1, 14), V(-3, 0, 0)], [50, V(-2, 1.5, 20), V(-1, 0, 0)]],
    captions: [
      [35, 'จากโครงสร้างเดียว ระบบสร้างของออกมาได้เจ็ดอย่าง — ทุกชิ้นพูดภาษาเดียวกัน', 'code_generator.py · generate_all'],
      [41, 'เจ็ดอย่างออกพร้อมกันในจังหวะเดียว — ไม่ใช่เขียนทีละชิ้นแล้วหวังว่าจะตรงกัน', EMITTERS.join(' · ')],
    ],
    sources: [['services/engine/code_generator.py:917-940', 'generate_all เรียก emitter ทั้ง 7'],
              ['services/engine/code_generator.py:900-914', 'ของ fleet ทั้ง 7 เป็นไฟล์อ้างอิง (gitignored) — commit เฉพาะของ energy/core']] },
  { code: '3', name: 'ถามภาษาคน ตอบจากของจริง', start: 50, end: 70,
    focus: { ask: 1, lattice: .5, codegen: .3, rail: .15, human: .15, narrative: .08, existing: .08 },
    cam: [[50.8, V(5, -3.8, 15), V(4.5, -5.8, 0)], [57, V(11, -3.2, 18), V(11.5, -5.8, 0)], [70, V(12.5, -3, 19), V(12.5, -5.5, 0)]],
    captions: [
      [50, 'ถ้าให้โมเดลตอบจากความจำ คำตอบอาจฟังดูดี แต่ไม่มีใครตรวจที่มาได้', 'ไม่มีที่มา = ตรวจไม่ได้'],
      [56.5, 'vero-lite ให้โมเดลแค่แปลคำถาม เป็นคำค้นที่ถามได้เฉพาะ 10 ชนิดในโครงสร้าง', 'nl_query.py · translate — object_type ถูกล็อกด้วย enum ของโครงสร้าง'],
      [62.5, 'การค้นเป็นโค้ดล้วน แล้วเรียบเรียงจากข้อมูลที่ค้นได้เท่านั้น — ไม่เจอ ก็ตอบว่าไม่พบ', 'execute (ไม่มีโมเดล) → phrase · คำตอบแนบ id ของข้อมูลที่อ่าน'],
    ],
    sources: [['services/engine/nl_query.py:8-35', 'translate → execute → phrase · ผลว่าง = คำตอบตายตัว'],
              ['docs/plans/done/0109-fleet-repair-cases-queryable-from-ask.md:58-68', 'คำถามตัวอย่าง "มีเคสซ่อมของ truck-01 กี่เคส"']],
    notClaimed: ['ภาพนี้ไม่ได้อ้างว่าโมเดลเรียก MCP tools ตอนทำงาน — mcp_tools.json ถูกสร้างไว้ แต่ยังเป็นทางเลือก B ที่เลื่อนไป (nl_query.py:31-32)'] },
  { code: '4', name: 'เส้นทางที่ถูกกำกับ', start: 70, end: 95,
    focus: { rail: 1, human: 1, lattice: .45, codegen: .2, ask: .1, narrative: .08, existing: .08 },
    cam: [[70.8, V(6, 4, 21), V(8, 1.2, 0)], [77, V(12.5, 1.6, 13), V(14, .4, 0)], [85, V(16, 3.6, 16), V(17, 2, 0)], [95, V(14.5, 3.2, 22), V(14, 1.4, 0)]],
    captions: [
      [70, 'เมื่อยืนยันใบเสนอราคาของเคสซ่อม เส้นทางอนุมัติเริ่มทันที', 'event: repair_quote_accepted → governed_repair_approval'],
      // the rest of this act's captions are derived from ACT4_CASES in section 6
    ],
    sources: [['verticals/fleet_maintenance/procedures.yaml:180-409', 'intake → judge → reshape → quote_gate → approve → fulfill'],
              ['verticals/fleet_maintenance/procedures.yaml:294-322', 'quote_gate: rule_gate three_quote — ด่านแข็ง ข้ามไม่ได้'],
              ['verticals/fleet_maintenance/sourcing.py:51-94', 'เกณฑ์ยอดเงิน + ผู้ขายต่างเจ้ากันสามเจ้า'],
              ['verticals/fleet_maintenance/data_adapter/synthetic.py:255-303', 'เคสใน seed: truck-03 ฿15,000 → ผจก.เดินรถ · truck-01 ฿48,000 → เจ้าของกิจการ'],
              ['verticals/fleet_maintenance/procedures.yaml:343-349 · :416-420', 'สายอนุมัติตามวงเงิน + คนขอ ≠ คนอนุมัติ']] },
  { code: '5', name: 'ปิด', start: 95, end: 105,
    focus: { rail: 1, human: 1, lattice: .7, codegen: .6, ask: .55, narrative: .5, existing: .5, hero: 0 },
    cam: [[95.8, V(12, 4.5, 25), V(10, .5, 0)], [105, V(2, 7, 48), V(2, 0, 0)]],
    captions: [
      [95, 'คนอยู่ในลูป: ทุกก้อนที่เกินเพดานต้องมีคนอนุมัติ · คนอยู่บนลูป: เห็นทุกขั้น ตรวจย้อนได้ทุกเมื่อ', 'ทุกขั้นถูกบันทึกแบบ tamper-evident — ถ้ามีใครแก้ย้อนหลัง ตรวจจับได้'],
      [100.5, 'นั่นคือเหตุผล — ต่อจากนี้ ดูของจริง', 'ต่อไป: Tab I เคสซ่อม → Tab H การอนุมัติ'],
    ],
    sources: [['docs/strategy/public/intro-video-production-rulings.md §3', 'ใช้คำว่า tamper-evident · ไม่อ่านตัวเลขขอบวงเงิน · ไม่มี URL บนจอ']] },
];
let TOTAL = ACTS[ACTS.length - 1].end;   // recomputed once act 4 is sized from its cases (section 6)
const ZONES = ['hero','narrative','existing','lattice','codegen','rail','ask','human'];

/* =====================================================================
   5. SCENE — every dimmable material is registered with its zone, so
   focus is "dim everything else", never "highlight the subject".
   ===================================================================== */
const stageEl = document.getElementById('stage');
const labelsEl = document.getElementById('labels');
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setClearColor(0x090c12, 1);
stageEl.prepend(renderer.domElement);
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x090c12, 42, 110);
const camera = new THREE.PerspectiveCamera(40, 1, .1, 240);
const COL = { accent: 0x4d8df0, ok: 0x46b377, warn: 0xe0a23c, crit: 0xe5544b, neutral: 0x6b7689,
  tx0: 0xeef1f6, tx1: 0xaeb7c6, tx2: 0x717c8e, line: 0x2a3547 };

const clamp01 = x => Math.max(0, Math.min(1, x));
const ease = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
const prog = (t, at, dur) => clamp01((t - at) / dur);
const lerp = (a, b, u) => a + (b - a) * u;

const dimmables = [];
function reg(mat, zone, base, owner) {
  mat.transparent = true; mat.depthWrite = false;
  dimmables.push({ mat, zone, base, owner });
  return mat;
}
function box(w, h, d, color, zone, { fill = .1, edge = .85, dashed = false, pos = V(0, 0, 0) } = {}) {
  const owner = { vis: 1 };
  const g = new THREE.BoxGeometry(w, h, d);
  const grp = new THREE.Group();
  const fillMat = reg(new THREE.MeshBasicMaterial({ color }), zone, fill, owner);
  const edgeMat = reg(dashed ? new THREE.LineDashedMaterial({ color, dashSize: .1, gapSize: .07 })
                             : new THREE.LineBasicMaterial({ color }), zone, edge, owner);
  const lines = new THREE.LineSegments(new THREE.EdgesGeometry(g), edgeMat);
  if (dashed) lines.computeLineDistances();
  grp.add(new THREE.Mesh(g, fillMat), lines);
  grp.position.copy(pos);
  grp.userData = { owner, fillMat, edgeMat, baseFill: fill, baseEdge: edge };
  scene.add(grp);
  return grp;
}
function tube(points, color, zone, { radius = .03, base = .32, owner } = {}) {
  const curve = new THREE.CatmullRomCurve3(points);
  const mat = reg(new THREE.MeshBasicMaterial({ color }), zone, base, owner);
  scene.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 72, radius, 6, false), mat));
  return curve;
}
function dashedCurve(points, color, zone, { base = .5, owner } = {}) {
  const curve = new THREE.CatmullRomCurve3(points);
  const mat = reg(new THREE.LineDashedMaterial({ color, dashSize: .16, gapSize: .12 }), zone, base, owner);
  const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(curve.getPoints(60)), mat);
  line.computeLineDistances();
  scene.add(line);
  return curve;
}

const labels = [];
function label(text, cls, pos, zone, { owner, dy = 0, dx = 0, far = 70 } = {}) {
  const el = document.createElement('div');
  el.className = 'lb ' + cls;
  el.textContent = text;
  labelsEl.appendChild(el);
  const L = { el, pos, zone, owner, dx, dy, far, shown: false };
  labels.push(L);
  return L;
}

const flows = [];
function flow(curve, color, zone, { count = 6, speed = .14, size = .09, base = .95, owner, on = () => true, step } = {}) {
  const mat = reg(new THREE.MeshBasicMaterial({ color }), zone, base, owner);
  const mesh = new THREE.InstancedMesh(new THREE.BoxGeometry(size, size, size), mat, count);
  mesh.frustumCulled = false;
  scene.add(mesh);
  flows.push({ curve, mesh, count, speed, on, step });
}

// ---- ground: a faint control-room floor, no zone (always present) ----
const grid = new THREE.GridHelper(96, 48, COL.line, COL.line);
grid.position.set(2, -11, 0);
reg(grid.material, null, .22);
scene.add(grid);

// ---- zone 2: the lattice, laid out by ref depth (no authored coordinates) ----
const LX = -7;
const refsOf = Object.fromEntries(OBJECT_TYPES.map(o => [o, new Set()]));
for (const [, f, to] of LINK_TYPES) refsOf[f].add(to);
for (const [f, to] of UNDECLARED_REFS) refsOf[f].add(to);
const layerOf = {};
const depthOf = o => layerOf[o] ?? (layerOf[o] = refsOf[o].size ? 1 + Math.max(...[...refsOf[o]].map(depthOf)) : 0);
OBJECT_TYPES.forEach(depthOf);
const byLayer = {};
for (const o of OBJECT_TYPES) (byLayer[layerOf[o]] ??= []).push(o);
const nodePos = {};
for (const [ly, list] of Object.entries(byLayer)) {
  list.forEach((o, i) => { nodePos[o] = V(LX + (i - (list.length - 1) / 2) * 2.7, 2.6 - Number(ly) * 1.3, 0); });
}
// When each type enters the lattice: from the narrative (1a), from existing tables (1b), then the rest.
const FROM_NARRATIVE = ['OperationalEvent', 'Truck', 'Depot', 'Vendor', 'Alert'];
const FROM_TABLES = ['RepairCase', 'RepairCaseQuote', 'RepairCaseAcceptedQuote'];
const nodeAppearAt = {};
FROM_NARRATIVE.forEach((o, i) => { nodeAppearAt[o] = 14 + i * 1.1 + 1.5; });
FROM_TABLES.forEach((o, i) => { nodeAppearAt[o] = 25.2 + i * .7; });
nodeAppearAt.RecommendedAction = 31; nodeAppearAt.AlertEventLink = 31.4;

const nodes = {};
for (const o of OBJECT_TYPES) {
  const b = box(.8, .8, .8, COL.accent, 'lattice', { fill: .14, edge: .95, pos: nodePos[o] });
  nodes[o] = b;
  label(o, 'lb-node', nodePos[o], 'lattice', { owner: b.userData.owner, dy: 26, far: 34 });
}
const edgeOwners = [];
for (const [name, f, to] of LINK_TYPES) {
  const owner = { vis: 1 }; edgeOwners.push({ owner, f, to });
  const a = nodePos[f], b = nodePos[to];
  tube([a, V((a.x + b.x) / 2, (a.y + b.y) / 2, .9), b], COL.accent, 'lattice', { radius: .022, base: .45, owner });
}
for (const [f, to] of UNDECLARED_REFS) {
  const owner = { vis: 1 }; edgeOwners.push({ owner, f, to });
  const a = nodePos[f], b = nodePos[to];
  dashedCurve([a, V((a.x + b.x) / 2, (a.y + b.y) / 2, -.9), b], COL.accent, 'lattice', { base: .55, owner });
}
label('โครงสร้างกลาง', 'lb-zone', V(LX, 4.4, 0), 'lattice');

// ---- act 0 hero marker on the event that starts the story ----
const heroRing = new THREE.Mesh(new THREE.TorusGeometry(.95, .035, 8, 48),
  reg(new THREE.MeshBasicMaterial({ color: COL.crit }), 'hero', 1));
heroRing.position.copy(nodePos.OperationalEvent);
scene.add(heroRing);
label('truck-01 · ฿48,000', 'lb-case', nodePos.OperationalEvent, 'hero', { dy: -34 }).el.dataset.state = 'fail';

// ---- zone 1 (upper): loose narrative blocks that snap into the lattice ----
const NARRATIVE = [
  ['คนขับโทรแจ้ง: เพลาขาดที่ปากช่อง', 'OperationalEvent', V(-19.6, 4.3, 1.1), .18],
  ['รถหกล้อ 2 คัน · หัวลาก 1 คัน', 'Truck', V(-15.1, 3.7, -1.2), -.12],
  ['ลานบางพลี · อู่คู่สัญญาปากช่อง', 'Depot', V(-18.6, 2.3, .6), .08],
  ['อู่และร้านที่เคยใช้', 'Vendor', V(-14.4, 1.4, .9), -.2],
  ['เรื่องไหนด่วน ต้องมีคนดู', 'Alert', V(-19.9, .5, -.8), .14],
];
const blocks = NARRATIVE.map(([text, type, loose, rot], i) => {
  const b = box(2.6, .72, .12, COL.tx1, 'narrative', { fill: .08, edge: .7, pos: loose });
  b.rotation.z = rot;
  const L = label(text, 'lb-thai', b.position, 'narrative', { owner: b.userData.owner, far: 40 });
  return { b, L, type, loose, rot, snapAt: 14 + i * 1.1 };
});
label('เรื่องเล่า · กติกาในหัวคน', 'lb-zone', V(-17, 5.8, 0), 'narrative');

// ---- zone 1 (lower): existing tables → allowlist → lattice; CSV → proposals ----
const EX = -17, FILTER_X = -12.1;
box(7.2, 3.6, 1.8, COL.accent, 'existing', { fill: .025, edge: .55, pos: V(EX, -3.8, 0) });
label('ข้อมูลที่มีอยู่แล้ว', 'lb-zone', V(EX, -1.4, 0), 'existing');
box(.06, 4.2, 2.2, COL.accent, 'existing', { fill: .07, edge: .7, pos: V(FILTER_X, -3.4, 0) });
label('allowlist · เฉพาะ property ที่ประกาศ', 'lb-node', V(FILTER_X, -5.9, 0), 'existing', { far: 40 });
const TABLES = [['ตารางเคสซ่อม', 'RepairCase'], ['ตารางใบเสนอราคา', 'RepairCaseQuote'], ['ตารางใบที่ยืนยัน', 'RepairCaseAcceptedQuote']];
TABLES.forEach(([th, type], i) => {
  const y = -2.9 - i * .95;
  box(5.4, .5, .1, COL.accent, 'existing', { fill: .1, edge: .8, pos: V(EX, y, 0) });
  label(th, 'lb-thai', V(EX - .6, y, .1), 'existing', { far: 40 });
  const c = tube([V(EX + 2.7, y, 0), V(FILTER_X, y + .3, .3), V(-9.6, (y + nodePos[type].y) / 2, .7), nodePos[type]],
    COL.accent, 'existing', { radius: .018, base: .3 });
  flow(c, COL.accent, 'existing', { count: 4, speed: .22, on: t => t >= 23.2 && t < 36 });
  // columns the YAML never declared travel to the allowlist and end there
  const blocked = new THREE.CatmullRomCurve3([V(EX + 2.7, y - .12, 0), V((EX + 2.7 + FILTER_X) / 2, y - .22, .15), V(FILTER_X - .08, y - .1, .3)]);
  flow(blocked, COL.neutral, 'existing', { count: 2, speed: .3, size: .08, on: t => t >= 23.2 && t < 36 });
});
box(4.6, .5, .1, COL.tx1, 'existing', { fill: .05, edge: .6, dashed: true, pos: V(EX, -7.4, 0) });
label('CSV เลขไมล์ · plate, odometer_km', 'lb-node', V(EX, -7.4, .1), 'existing', { far: 40 });
const csvCurve = tube([V(EX + 2.3, -7.4, 0), V(-12, -6.6, 1.4), V(-9.3, -1.6, 1.6), nodePos.Truck], COL.warn, 'existing', { radius: .018, base: .3 });
flow(csvCurve, COL.warn, 'existing', { count: 3, speed: .16, on: t => t >= 28.5 && t < 36 });
const proposalOwner = { vis: 0 };
const proposalLabel = label('ข้อเสนอ · รอคนยืนยันทีละแถว', 'lb-chip', csvCurve.getPointAt(.42), 'existing', { owner: proposalOwner, far: 45 });

// the gaps nobody ever wrote down — dashed until a person fills them
const GAPS = [
  ['เพดานซ่อมต่อคัน', V(nodePos.Truck.x - 1.3, nodePos.Truck.y + .1, .5)],
  ['จุดเข้าศูนย์ถัดไป', V(nodePos.Truck.x + 1.3, nodePos.Truck.y + .1, .5)],
  ['คำเรียก ไทย ↔ อังกฤษ', V(LX - 4.3, 2.6, .5)],
  ['ชื่ออู่ = ข้อความอิสระ', V(nodePos.RepairCaseQuote.x + 1.4, nodePos.RepairCaseQuote.y - .1, .5)],
];
const GAP_OPEN_AT = 28.5, GAP_FILL_AT = 31.5;
const gaps = GAPS.map(([text, p]) => {
  const empty = box(.46, .46, .46, COL.warn, 'lattice', { fill: 0, edge: .95, dashed: true, pos: p });
  const solid = box(.46, .46, .46, COL.warn, 'lattice', { fill: .42, edge: 1, pos: p });
  const chipOwner = { vis: 0 };
  const L = label(text, 'lb-chip', p, 'lattice', { owner: chipOwner, dy: -22, far: 40 });
  return { empty, solid, L, chipOwner };
});

// ---- zone 3: seven emitters fed from one trunk ----
const GX = 2;
const trunk = tube([V(LX, 0, 1.3), V(-4.8, .25, 1.1), V(-3.4, 0, .4)], COL.accent, 'codegen', { radius: .03, base: .35 });
const slabs = EMITTERS.map((name, i) => {
  const y = 3 - i;
  const s = box(3, .56, .08, COL.accent, 'codegen', { fill: .12, edge: .9, pos: V(GX, y, 0) });
  const c = tube([V(-3.4, 0, .4), V(-1.3, y * .55, .5), V(GX - 1.5, y, 0)], COL.accent, 'codegen', { radius: .02, base: .28 });
  flow(c, COL.accent, 'codegen', { count: 2, speed: .2, on: t => t >= 43 });
  label(name, 'lb-node', V(GX, y, .1), 'codegen', { far: 36 });
  return { s, c };
});
label('ของเจ็ดอย่าง จากต้นฉบับเดียว', 'lb-zone', V(GX, 4.3, 0), 'codegen');
const tokenMat = reg(new THREE.MeshBasicMaterial({ color: COL.tx0 }), 'codegen', 1);
const token = new THREE.Mesh(new THREE.BoxGeometry(.22, .22, .22), tokenMat);
const fanTokens = slabs.map(() => new THREE.Mesh(new THREE.BoxGeometry(.15, .15, .15), tokenMat));
scene.add(token, ...fanTokens);

// ---- zone 4: the governed procedure rail, two solid gates ----
const RX = { intake: 7, judge: 9.6, reshape: 12.2, quote_gate: 14.8, approve: 18.2, fulfill: 21.2 };
tube([V(6, 0, 0), V(14, 0, 0), V(22.2, 0, 0)], COL.accent, 'rail', { radius: .045, base: .3 });
const stepBoxes = {};
for (const s of STEPS) {
  const p = V(RX[s.id], 0, 0);
  if (s.gate) {
    stepBoxes[s.id] = box(.32, 2.8, 2.8, s.gate === 1 ? COL.tx1 : COL.warn, 'rail', { fill: .1, edge: .9, pos: p });
    label(s.th, 'lb-thai', V(p.x, 1.4, 0), 'rail', { dy: -18, far: 52 });
  } else {
    stepBoxes[s.id] = box(.62, .62, .62, COL.tx1, 'rail', { fill: .1, edge: .8, pos: p });
  }
  label(s.id, 'lb-node', V(p.x, s.gate ? -1.4 : -.31, 0), 'rail', { dy: 16, far: 46 });
}
label('เส้นทางที่ถูกกำกับ · governed_repair_approval', 'lb-zone', V(14, -2.7, 0), 'rail');
const trigCurve = tube([nodePos.RepairCaseAcceptedQuote, V(-3, -3.9, 2.2), V(3, -3.9, 2.4), V(6, -1.2, 1), V(RX.intake, 0, 0)],
  COL.accent, 'rail', { radius: .022, base: .3 });
label('repair_quote_accepted', 'lb-node', V(3, -3.9, 2.4), 'rail', { dy: 16, far: 40 });

// ---- the human plane: always faintly lit, never dark ----
const HY = 5.4;
const planeGeo = new THREE.PlaneGeometry(17.5, 6.5);
const plane = new THREE.Mesh(planeGeo, reg(new THREE.MeshBasicMaterial({ color: COL.tx0, side: THREE.DoubleSide }), 'human', .035));
const planeEdge = new THREE.LineSegments(new THREE.EdgesGeometry(planeGeo), reg(new THREE.LineBasicMaterial({ color: COL.warn }), 'human', .3));
for (const m of [plane, planeEdge]) { m.rotation.x = -Math.PI / 2; m.position.set(14.2, HY, 0); scene.add(m); }
label('ระนาบคน · มองเห็นทุกขั้น', 'lb-zone', V(6.4, HY + .1, -3.1), 'human');
function persona(text, p, dy = -28) {
  const owner = { vis: 1 };
  const disc = new THREE.Mesh(new THREE.CylinderGeometry(.5, .5, .1, 36), reg(new THREE.MeshBasicMaterial({ color: COL.warn }), 'human', .35, owner));
  const ring = new THREE.Mesh(new THREE.TorusGeometry(.64, .026, 6, 40), reg(new THREE.MeshBasicMaterial({ color: COL.warn }), 'human', .9, owner));
  ring.rotation.x = Math.PI / 2;
  disc.position.copy(p); ring.position.copy(p);
  scene.add(disc, ring);
  // far 42, not 62: on act 5's wide dolly (camera ≈50 out) the ladder is narrower than its
  // labels, so past 42 they stacked on each other (s309, measured in the browser).
  label(text, 'lb-thai', p, 'human', { dy, far: 42 });
  return { p, ring };
}
const requester = persona('ช่างใหญ่ · คนขอ', V(RX.intake, HY, 0));
// Neighbouring rungs are 1.8 world units apart — fewer pixels than one label is wide once the
// camera pulls back — so odd rungs label BELOW the disc: a pixel gap that no distance closes.
const ladder = Object.fromEntries(DOA_TIERS.map((tier, i) =>
  [tier.role, persona(tier.role, V(RX.approve - 1.8 + i * 1.8, HY + i * .45, -1.2 + i * .6), i % 2 ? 30 : -28)]));
// Anchored to the top rung in PIXELS (dy), not placed in world space: a world offset shrinks with
// camera distance, so the old HY + 1.7 slid onto the top persona's label in acts 4 and 5.
label('สายอนุมัติตามวงเงิน', 'lb-zone', ladder[DOA_TIERS[DOA_TIERS.length - 1].role].p, 'human', { dy: -56, far: 42 });
const beam = new THREE.Mesh(new THREE.CylinderGeometry(.06, .06, 1, 10), reg(new THREE.MeshBasicMaterial({ color: COL.ok }), 'human', 1));
beam.visible = false;
scene.add(beam);

// ---- ask row: memory vs. the grounded three-stage path ----
const AY = -6.6;
const A = { q: V(5, AY, 0), memory: V(1.2, AY, 0), translate: V(8.4, AY, 0), execute: V(11.9, AY, 0),
  phrase: V(15.4, AY, 0), answer: V(18.9, AY, 0), empty: V(15.4, AY - 2.3, 0) };
const memOwner = { vis: 1 };
const memory = new THREE.Mesh(new THREE.IcosahedronGeometry(.6, 0),
  reg(new THREE.MeshBasicMaterial({ color: COL.neutral, wireframe: true }), 'ask', .9, memOwner));
memory.position.copy(A.memory);
scene.add(memory);
label('ความจำของโมเดล', 'lb-thai', A.memory, 'ask', { owner: memOwner, dy: -32, far: 44 });
box(.6, .6, .6, COL.accent, 'ask', { pos: A.translate });
box(.6, .6, .6, COL.accent, 'ask', { pos: A.execute });
box(.6, .6, .6, COL.accent, 'ask', { pos: A.phrase });
box(.6, .6, .6, COL.ok, 'ask', { pos: A.answer });
box(.6, .6, .6, COL.neutral, 'ask', { pos: A.empty });
label('translate · โมเดลแปลคำถาม', 'lb-thai', A.translate, 'ask', { dy: 32, far: 44 });
label('execute · ค้นจริง ไม่มีโมเดล', 'lb-thai', A.execute, 'ask', { dy: -32, far: 44 });
label('phrase · เรียบเรียงจากที่ค้นได้', 'lb-thai', A.phrase, 'ask', { dy: -32, far: 44 });
label('คำตอบ + id ที่อ่าน', 'lb-thai', A.answer, 'ask', { dy: 32, far: 44 });
label('ไม่พบ → คำตอบตายตัว', 'lb-thai', A.empty, 'ask', { dy: 30, far: 44 });
label('มีเคสซ่อมของ truck-01 กี่เคส', 'lb-q', A.q, 'ask', { dy: -44, far: 50 });
label('ถามเป็นภาษาคน', 'lb-zone', V(10.5, AY + 1.9, 0), 'ask');
const toMemory = tube([A.q, V(3.1, AY + .5, .4), A.memory], COL.neutral, 'ask', { radius: .02, base: .35, owner: memOwner });
flow(toMemory, COL.tx2, 'ask', { count: 3, speed: .3, owner: memOwner, on: t => t >= 50.4 });
const grounded = [[A.q, V(6.7, AY - .35, .3), A.translate], [A.translate, V(10.1, AY + .3, .2), A.execute],
  [A.execute, V(13.6, AY - .3, .2), A.phrase], [A.phrase, V(17.1, AY + .3, .2), A.answer]];
for (const pts of grounded) {
  flow(tube(pts, COL.accent, 'ask', { radius: .03, base: .38 }), COL.tx0, 'ask', { count: 3, speed: .24, on: t => t >= 56.5 });
}
flow(tube([A.execute, V(13.4, AY - 1.7, .3), A.empty], COL.neutral, 'ask', { radius: .02, base: .3 }), COL.tx2, 'ask',
  { count: 1, speed: .12, on: t => t >= 62.5 });
const enumCurve = tube([nodePos.RepairCaseAcceptedQuote, V(-5, -7.5, 1.2), V(3, -9.3, 1.4), V(7.2, -7.7, .6), A.translate],
  COL.accent, 'ask', { radius: .02, base: .3 });
flow(enumCurve, COL.accent, 'ask', { count: 4, speed: .12, on: t => t >= 56.5 });
label('enum · 10 ชนิดนี้เท่านั้น', 'lb-node', V(3, -9.3, 1.4), 'ask', { dy: 16, far: 46 });
const SC_N = 28;
const scatter = new THREE.InstancedMesh(new THREE.BoxGeometry(.08, .08, .08),
  reg(new THREE.MeshBasicMaterial({ color: COL.tx2 }), 'ask', .9, memOwner), SC_N);
scatter.frustumCulled = false;
scene.add(scatter);
const scatterDirs = Array.from({ length: SC_N }, (_, i) => {
  const a = i * 2.39996, e = Math.sin(i * 12.9898) * .9;
  return V(Math.cos(a) * Math.cos(e), Math.sin(e), Math.sin(a) * Math.cos(e));
});

// ---- act 5 loop: cases keep arriving; every third is stopped at gate 1 ----
const LOOP_N = 12;
const loopMesh = new THREE.InstancedMesh(new THREE.BoxGeometry(.14, .14, .14),
  reg(new THREE.MeshBasicMaterial({ color: COL.tx0 }), 'rail', .95), LOOP_N);
loopMesh.frustumCulled = false;
scene.add(loopMesh);

/* =====================================================================
   6. ACT 4 — each case's path and captions follow its PINNED outcome
   (`expected`, checked against the real rules by CI — see section 1–3).
   ===================================================================== */
const D = { trig: 1.6, step: .9, hold: .9, bounce: 1.8, toGate2: 1.1, wait: 3.2, open: .7, toFulfill: 1.1, done: .9, okExit: 1.4, gap: 1.0 };
const baht = n => '฿' + n.toLocaleString('en-US');
const PLANS = ACT4_CASES.map(c => {
  const e = c.expected;
  const outcome = e.outcome;
  const dur = outcome === 'ok' ? D.trig + D.step + D.okExit
    : outcome === 'fail' ? D.trig + 3 * D.step + D.hold + D.bounce
    : D.trig + 3 * D.step + D.hold + D.toGate2 + D.wait + D.open + D.toFulfill + D.done;
  return {
    truck: c.truck, what: c.what, amountThb: c.amount_thb, distinctVendors: c.distinct_vendors,
    illustrative: c.illustrative, breach: e.breach, sourcing: { pass: e.sourcing_pass, basis: e.basis },
    tier: { role: e.tier_role }, outcome, dur,
  };
});
const ACT4 = ACTS.find(a => a.code === '4');
// Act 4 is sized by its cases, so a caption stays readable however many cases run; past
// ACT4_MAX the cases compress instead of the act growing further.
const ACT4_MAX = 45;
const CAMK = {
  wide: [V(6, 4, 21), V(8, 1.2, 0)], intake: [V(9, 2.6, 17), V(10, .6, 0)],
  gate1: [V(12.5, 1.6, 13), V(14, .4, 0)], ladder: [V(16, 3.6, 16), V(17, 2, 0)], out: [V(14.5, 3.2, 22), V(14, 1.4, 0)],
};
{
  const from = ACT4.start + 1.6;
  const raw = PLANS.reduce((s, p) => s + p.dur, 0) + D.gap * Math.max(0, PLANS.length - 1);
  const k = Math.min(1, (ACT4_MAX - 2.8) / Math.max(raw, .001));
  const camKeys = [[ACT4.start + .8, ...CAMK.wide]];
  let cursor = from;
  for (const p of PLANS) {
    p.t0 = cursor; p.k = k; cursor += (p.dur + D.gap) * k;
    const at = sec => p.t0 + sec * k;
    const gate1At = D.trig + 3 * D.step;
    camKeys.push([at(0), ...CAMK.intake]);
    if (p.outcome !== 'ok') camKeys.push([at(gate1At - .6), ...CAMK.gate1]);
    if (p.outcome === 'approved') camKeys.push([at(gate1At + D.hold + D.toGate2), ...CAMK.ladder]);
    if (p.outcome === 'ok') {
      ACT4.captions.push([at(D.trig + D.step), `${p.truck} · ${baht(p.amountThb)} ต่ำกว่าเพดานซ่อมของคันนี้ — ช่างใหญ่ตัดสินเองได้ ไม่ต้องเข้าสายอนุมัติ`, 'judge · verdict: ok']);
    } else if (p.outcome === 'fail') {
      ACT4.captions.push([at(gate1At), `งานซ่อมก้อนใหญ่ต้องเทียบราคาจากสามเจ้า — เคสนี้มีแค่ ${p.distinctVendors} เจ้า ด่านนี้กั้นไว้ ข้ามไม่ได้`, `quote_gate · three_quote → ${p.sourcing.basis}`]);
    } else {
      const passText = { three_quotes: 'เทียบราคาครบสามเจ้าแล้ว ผ่านด่านแรก — แต่เงินยังไม่ออก',
        under_threshold: 'ยอดไม่ถึงเกณฑ์ต้องเทียบราคา ผ่านด่านแรก — แต่เงินยังไม่ออก',
        sole_source_justified: 'ไม่มีเจ้าอื่นให้เทียบ แต่มีคนเขียนเหตุผลลงบันทึก ผ่านด่านแรก — แต่เงินยังไม่ออก' }[p.sourcing.basis];
      ACT4.captions.push([at(gate1At), passText, `quote_gate · basis: ${p.sourcing.basis}`]);
      ACT4.captions.push([at(gate1At + D.hold + D.toGate2), `รอ${p.tier.role}อนุมัติ — ช่างใหญ่ที่เปิดเคส อนุมัติเคสของตัวเองไม่ได้`, `approve · doa_tier → ${p.tier.role} · separation of duties`]);
      ACT4.captions.push([at(gate1At + D.hold + D.toGate2 + D.wait), 'คนอนุมัติ แล้วระบบจึงลงมือ — โมเดลช่วยร่างสรุปให้ แต่อำนาจอนุมัติเป็นของคนเสมอ', ASSIST_SUB]);
    }
    if (p.illustrative) ACT4.sources.push([`ACT4_CASES · ${p.truck} ${baht(p.amountThb)} · ${p.distinctVendors} เจ้า`, 'ภาพประกอบกฎ — ไม่ใช่ run ที่อยู่ใน seed (เคสใน seed เทียบราคาครบสามเจ้าแล้ว synthetic.py:291-295)']);
  }
  // size act 4 from its cases, then slide every later act by the same delta
  const newEnd = Math.max(ACT4.start + 12, cursor - D.gap * k + 1.2);
  const delta = newEnd - ACT4.end;
  ACT4.end = newEnd;
  camKeys.push([newEnd, ...CAMK.out]);
  ACT4.cam = camKeys.sort((a, b) => a[0] - b[0]).filter((key, i, all) => i === 0 || key[0] - all[i - 1][0] >= 1.2);
  for (const a of ACTS.slice(ACTS.indexOf(ACT4) + 1)) {
    a.start += delta; a.end += delta;
    for (const c of a.captions) c[0] += delta;
    for (const c of a.cam) c[0] += delta;
  }
  TOTAL = ACTS[ACTS.length - 1].end;
}
for (const a of ACTS) a.captions.sort((x, y) => x[0] - y[0]);

const G1 = RX.quote_gate - .32, G2 = RX.approve - .36;
function caseFrame(p, t) {
  const r = (t - p.t0) / p.k;
  if (r < 0 || r > p.dur + .4) return null;
  let s = r;
  const out = { pos: null, state: 'run', fade: 1, gate1: null, gate2: null, beam: 0 };
  const onRail = x => V(x, 0, 0);
  if (s < D.trig) { out.pos = trigCurve.getPointAt(ease(s / D.trig)); return out; }
  s -= D.trig;
  if (s < D.step) { out.pos = onRail(lerp(RX.intake, RX.judge, ease(s / D.step))); return out; }
  s -= D.step;
  if (p.outcome === 'ok') {
    const u = clamp01(s / D.okExit);
    out.pos = V(RX.judge + u * 1.2, -u * 1.8, u * 1.2); out.state = 'done'; out.fade = 1 - prog(s, D.okExit - .2, .6);
    return out;
  }
  if (s < D.step) { out.pos = onRail(lerp(RX.judge, RX.reshape, ease(s / D.step))); return out; }
  s -= D.step;
  if (s < D.step) { out.pos = onRail(lerp(RX.reshape, G1, ease(s / D.step))); return out; }
  s -= D.step;
  if (s < D.hold) {
    out.pos = onRail(G1); out.gate1 = p.sourcing.pass ? 'pass' : 'fail'; out.state = p.sourcing.pass ? 'run' : 'fail';
    return out;
  }
  s -= D.hold;
  if (p.outcome === 'fail') {
    const u = clamp01(s / D.bounce);
    out.pos = V(G1 - ease(u) * 1.5, Math.sin(u * Math.PI) * .6 - u * u * 1.7, 0);
    out.state = 'fail'; out.gate1 = u < .45 ? 'fail' : null; out.fade = 1 - prog(u, .7, .3);
    return out;
  }
  if (s < D.toGate2) { out.pos = onRail(lerp(G1, G2, ease(s / D.toGate2))); out.gate1 = s < .5 ? 'pass' : null; return out; }
  s -= D.toGate2;
  if (s < D.wait) { out.pos = onRail(G2); out.state = 'wait'; out.gate2 = 'wait'; return out; }
  s -= D.wait;
  if (s < D.open) { out.pos = onRail(G2); out.state = 'wait'; out.gate2 = 'open'; out.beam = s / D.open; return out; }
  s -= D.open;
  if (s < D.toFulfill) { out.pos = onRail(lerp(G2, RX.fulfill, ease(s / D.toFulfill))); out.state = 'done'; out.gate2 = s < .4 ? 'open' : null; return out; }
  s -= D.toFulfill;
  out.pos = onRail(RX.fulfill); out.state = 'done'; out.fade = 1 - prog(s, D.done - .3, .7);
  return out;
}
const travelers = PLANS.map(p => {
  const owner = { vis: 0 };
  const mat = reg(new THREE.MeshBasicMaterial({ color: COL.tx0 }), 'rail', 1, owner);
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(.3, .3, .3), mat);
  scene.add(mesh);
  const L = label(`${p.truck} · ${baht(p.amountThb)} · ${p.distinctVendors} เจ้า`, 'lb-case', V(0, 0, 0), 'rail', { owner, dy: -30, far: 60 });
  return { p, owner, mat, mesh, L, state: '' };
});

/* =====================================================================
   7. EVALUATE — the whole frame is a pure function of the story clock t
   (plus an ambient clock for idle particles), so pause / step / seek are free.
   ===================================================================== */
const UP = V(0, 1, 0);
const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const zoneW = {};
const CAM = ACTS.flatMap(a => a.cam.map(([at, pos, tgt]) => ({ at, pos, tgt }))).sort((a, b) => a.at - b.at);
const orbit = { theta: 0, phi: 0, zoom: 1 };
const actIndexAt = tt => { for (let i = ACTS.length - 1; i >= 0; i--) if (tt >= ACTS[i].start) return i; return 0; };
const rebuildOut = (tt, at) => tt < 8 ? 1 : tt < 9 ? 1 - prog(tt, 8, 1) : prog(tt, at, .8);
const M4 = new THREE.Matrix4(), P3 = new THREE.Vector3(), Q3 = new THREE.Vector3(), S3 = new THREE.Vector3(1, 1, 1);
const QUAT = new THREE.Quaternion();

function evaluate(t, amb) {
  const ai = actIndexAt(Math.min(t, TOTAL - 1e-6));
  const cur = ACTS[ai].focus, prev = ai > 0 ? ACTS[ai - 1].focus : cur;
  const fu = ease(prog(t, ACTS[ai].start, 1.2));
  for (const z of ZONES) zoneW[z] = Math.max(z === 'hero' ? 0 : .05, lerp(prev[z] ?? 0, cur[z] ?? 0, fu));
  zoneW.human = Math.max(zoneW.human, .2);

  // lattice: finished preview in act 0, dissolved, then rebuilt type by type
  for (const o of OBJECT_TYPES) nodes[o].userData.owner.vis = rebuildOut(t, nodeAppearAt[o]);
  for (const e of edgeOwners) e.owner.vis = Math.min(nodes[e.f].userData.owner.vis, nodes[e.to].userData.owner.vis) *
    (t >= 8 && t < 22 ? prog(t, Math.max(nodeAppearAt[e.f], nodeAppearAt[e.to]) + .4, .8) : 1);
  heroRing.scale.setScalar(1 + .12 * Math.sin(amb * 4));

  for (const bl of blocks) {
    const u = ease(prog(t, bl.snapAt, 1.6));
    bl.b.position.lerpVectors(bl.loose, nodePos[bl.type], u);
    bl.b.position.y += (1 - u) * Math.sin(amb * .8 + bl.snapAt) * .08;
    bl.b.rotation.z = bl.rot * (1 - u);
    bl.b.scale.setScalar(lerp(1, .34, u));
    bl.b.userData.owner.vis = 1 - prog(t, bl.snapAt + 1.4, .4);
  }
  for (const g of gaps) {
    g.empty.userData.owner.vis = t < GAP_OPEN_AT ? 0 : prog(t, GAP_OPEN_AT, .6) * (1 - prog(t, GAP_FILL_AT, .6));
    g.solid.userData.owner.vis = rebuildOut(t, GAP_FILL_AT);
    g.chipOwner.vis = prog(t, GAP_OPEN_AT, .5) * (1 - prog(t, 35, .5));
    g.L.el.classList.toggle('filled', t >= GAP_FILL_AT);
  }
  proposalOwner.vis = prog(t, 29, .5) * (1 - prog(t, 35, .5));
  const confirmed = t >= GAP_FILL_AT;
  if (proposalLabel.confirmed !== confirmed) {
    proposalLabel.confirmed = confirmed;
    proposalLabel.el.textContent = confirmed ? 'คนยืนยันแล้ว → Truck' : 'ข้อเสนอ · รอคนยืนยันทีละแถว';
    proposalLabel.el.classList.toggle('filled', confirmed);
  }

  // codegen: one token in, seven out in the same frame, all slabs light together
  for (const s of slabs) s.s.userData.owner.vis = lerp(.3, 1, prog(t, 42.8, .3));
  token.visible = t >= 38.6 && t < 40.8;
  if (token.visible) trunk.getPointAt(ease(prog(t, 38.6, 2.2)), token.position);
  fanTokens.forEach((m, i) => {
    m.visible = t >= 40.8 && t < 42.8;
    if (m.visible) slabs[i].c.getPointAt(ease(prog(t, 40.8, 2)), m.position);
  });

  // ask row
  memOwner.vis = t < 56.5 ? 1 : lerp(1, .35, prog(t, 56.5, 1));
  memory.rotation.set(amb * .2, amb * .3, 0);
  for (let i = 0; i < SC_N; i++) {
    const ph = (amb * .35 + i / SC_N) % 1;
    const sc = t >= 51 ? 1 - ph : 0;
    P3.copy(A.memory).addScaledVector(scatterDirs[i], .5 + ph * 3.4);
    S3.setScalar(Math.max(sc, 1e-4));
    M4.compose(P3, QUAT.identity(), S3);
    scatter.setMatrixAt(i, M4);
  }
  scatter.instanceMatrix.needsUpdate = true;

  // rail: gates, travelers, human pulse
  let g1 = null, g2 = null, beamF = 0, beamRole = null;
  for (const r of Object.values(ladder)) r.ring.scale.setScalar(1);
  for (const tr of travelers) {
    const f = caseFrame(tr.p, t);
    tr.owner.vis = f ? f.fade : 0;
    tr.mesh.visible = !!f;
    if (!f) continue;
    tr.mesh.position.copy(f.pos);
    tr.mesh.rotation.set(amb * 1.3, amb * .9, 0);
    tr.L.pos.copy(f.pos);
    const col = { run: COL.tx0, fail: COL.crit, wait: COL.warn, done: COL.ok }[f.state];
    tr.mat.color.setHex(col);
    if (tr.state !== f.state) { tr.state = f.state; tr.L.el.dataset.state = f.state; }
    if (f.gate1) g1 = f.gate1;
    if (f.gate2) { g2 = f.gate2; beamRole = tr.p.tier.role; }
    if (f.beam) beamF = f.beam;
    if (f.state === 'wait') ladder[tr.p.tier.role].ring.scale.setScalar(1 + .18 * Math.abs(Math.sin(amb * 3)));
  }
  // act 5 loop — cases keep arriving; every third stops at gate 1
  const looping = t >= ACTS[ACTS.length - 1].start;
  let nearReject = false;
  for (let i = 0; i < LOOP_N; i++) {
    const ph = (amb * .055 + i / LOOP_N) % 1;
    const x = lerp(RX.intake, RX.fulfill + .6, ph);
    const rejected = i % 3 === 0 && x > G1;
    if (i % 3 === 0 && Math.abs(x - G1) < .35) nearReject = true;
    S3.setScalar(looping && !rejected ? 1 : 1e-4);
    P3.set(x, 0, 0);
    M4.compose(P3, QUAT.identity(), S3);
    loopMesh.setMatrixAt(i, M4);
  }
  loopMesh.instanceMatrix.needsUpdate = true;
  if (looping && !g1 && nearReject) g1 = 'fail';
  const gate1 = stepBoxes.quote_gate.userData, gate2 = stepBoxes.approve.userData;
  const g1col = g1 === 'fail' ? COL.crit : g1 === 'pass' ? COL.ok : COL.tx1;
  gate1.fillMat.color.setHex(g1col); gate1.edgeMat.color.setHex(g1col);
  gate1.owner.vis = g1 ? 2.6 : 1;
  const g2col = g2 === 'open' ? COL.ok : COL.warn;
  gate2.fillMat.color.setHex(g2col); gate2.edgeMat.color.setHex(g2col);
  gate2.owner.vis = g2 === 'wait' ? 1.4 + .9 * Math.abs(Math.sin(amb * 3)) : g2 === 'open' ? 2.6
    : looping ? 1 + .5 * Math.max(0, Math.sin(amb * 1.6)) : 1;
  beam.visible = beamF > 0 && !!beamRole;
  if (beam.visible) {
    const start = ladder[beamRole].p, end = V(RX.approve, 1.4, 0);
    Q3.copy(end).sub(start);
    const full = Q3.length(); Q3.normalize();
    const len = full * Math.min(1, beamF * 1.6);
    beam.position.copy(start).addScaledVector(Q3, len / 2);
    beam.scale.set(1, Math.max(len, .001), 1);
    beam.quaternion.setFromUnitVectors(UP, Q3);
  }

  for (const f of flows) {
    const on = f.on(t);
    f.mesh.visible = on;
    if (!on) continue;
    for (let i = 0; i < f.count; i++) {
      f.curve.getPointAt((amb * f.speed + i / f.count) % 1, P3);
      M4.makeTranslation(P3.x, P3.y, P3.z);
      f.mesh.setMatrixAt(i, M4);
    }
    f.mesh.instanceMatrix.needsUpdate = true;
  }
  for (const d of dimmables) {
    d.mat.opacity = d.base * (d.zone ? zoneW[d.zone] : 1) * (d.owner ? d.owner.vis : 1);
    d.mat.visible = d.mat.opacity > .004;
  }
  return ai;
}

function placeCamera(t, aspect) {
  let i = 0;
  while (i < CAM.length - 1 && CAM[i + 1].at <= t) i++;
  const a = CAM[i], b = CAM[Math.min(i + 1, CAM.length - 1)];
  const u = a === b || t <= a.at ? 0 : reduced ? 1 : ease(prog(t, a.at, b.at - a.at));
  const tgt = P3.lerpVectors(a.tgt, b.tgt, u).clone();
  const off = Q3.lerpVectors(a.pos, b.pos, u).sub(tgt);
  const fit = aspect < 1 ? Math.min(2.5, 1.3 / aspect) : aspect < 1.45 ? 1.18 : 1;
  off.multiplyScalar(fit * orbit.zoom).applyAxisAngle(UP, orbit.theta);
  const right = new THREE.Vector3().crossVectors(UP, off).normalize();
  off.applyAxisAngle(right, orbit.phi);
  camera.position.copy(tgt).add(off);
  camera.lookAt(tgt);
}

const LP = new THREE.Vector3();
function placeLabels(w, h) {
  for (const L of labels) {
    let op = (L.zone ? zoneW[L.zone] : 1) * (L.owner ? Math.min(1, L.owner.vis) : 1);
    op *= 1 - prog(camera.position.distanceTo(L.pos), L.far - 6, 6);
    LP.copy(L.pos).project(camera);
    const show = op > .12 && LP.z < 1 && Math.abs(LP.x) < 1.15 && Math.abs(LP.y) < 1.15;
    if (show !== L.shown) { L.el.style.visibility = show ? 'visible' : 'hidden'; L.shown = show; }
    if (!show) continue;
    const x = (LP.x * .5 + .5) * w + L.dx, y = (-LP.y * .5 + .5) * h + L.dy;
    L.el.style.transform = `translate(${x.toFixed(1)}px,${y.toFixed(1)}px) translate(-50%,-50%)`;
    L.el.style.opacity = Math.min(1, op * 1.15).toFixed(2);
  }
}

/* =====================================================================
   8. CONTROLS — questions will interrupt a live demo.
   ===================================================================== */
const $ = id => document.getElementById(id);
let t = 0, amb = 0, playing = !reduced, ended = false;
const actsNav = $('acts');
const actBtns = ACTS.map((a, i) => {
  const b = document.createElement('button');
  b.type = 'button'; b.className = 'act-btn';
  b.style.flexGrow = String(a.end - a.start);
  b.title = `ฉาก ${a.code} · ${a.name}`;
  const fill = document.createElement('span'); fill.className = 'fill';
  b.appendChild(fill);
  const code = document.createElement('span'); code.textContent = a.code;
  const nm = document.createElement('span'); nm.className = 'nm'; nm.textContent = a.name;
  b.append(code, nm);
  b.addEventListener('click', () => seek(a.start));
  actsNav.appendChild(b);
  return b;
});
// The play/pause glyph swaps its path data — no markup is written (docs/conventions/ui.md §3).
const PLAY_D = 'M8 5v14l11-7z', PAUSE_D = 'M9 5v14M15 5v14';
const setIcon = d => $('ico-play').firstElementChild.setAttribute('d', d);
function setPlaying(v) {
  if (v && ended) { t = 0; ended = false; }
  playing = v;
  if (v) { orbit.theta = 0; orbit.phi = 0; orbit.zoom = 1; }
  setIcon(v ? PAUSE_D : PLAY_D);
}
function seek(tt) { t = Math.max(0, Math.min(TOTAL - .001, tt)); ended = false; }
function stepAct(dir) {
  const i = actIndexAt(t);
  if (dir < 0 && t - ACTS[i].start > 1.5) return seek(ACTS[i].start);
  seek(ACTS[Math.max(0, Math.min(ACTS.length - 1, i + dir))].start);
}
function toggle(id, cls) {
  const on = document.body.classList.toggle(cls);
  if ($(id)) $(id).setAttribute('aria-pressed', String(on));
}
let sourcesOpen = false, sourcesAct = -1;
function renderSources(ai) {
  const a = ACTS[ai], box = $('sources');
  box.replaceChildren();
  const k = document.createElement('div'); k.className = 'k'; k.textContent = `ฉาก ${a.code} · ที่มา`;
  const h = document.createElement('h2'); h.textContent = a.name;
  const ul = document.createElement('ul');
  for (const [path, note] of a.sources) {
    const li = document.createElement('li');
    const c = document.createElement('code'); c.textContent = path;
    const s = document.createElement('span'); s.textContent = note;
    li.append(c, s); ul.appendChild(li);
  }
  box.append(k, h, ul);
  if (a.notClaimed) {
    const k2 = document.createElement('div'); k2.className = 'k'; k2.textContent = 'สิ่งที่ภาพนี้ไม่ได้อ้าง';
    const ul2 = document.createElement('ul'); ul2.className = 'not';
    for (const n of a.notClaimed) { const li = document.createElement('li'); const s = document.createElement('span'); s.textContent = n; li.appendChild(s); ul2.appendChild(li); }
    box.append(k2, ul2);
  }
  sourcesAct = ai;
}
function setSources(v) {
  sourcesOpen = v; $('sources').hidden = !v; $('btn-src').setAttribute('aria-pressed', String(v));
  if (v) renderSources(actIndexAt(t));
}
$('btn-play').addEventListener('click', () => setPlaying(!playing));
$('btn-prev').addEventListener('click', () => stepAct(-1));
$('btn-next').addEventListener('click', () => stepAct(1));
$('btn-src').addEventListener('click', () => setSources(!sourcesOpen));
$('btn-clean').addEventListener('click', () => toggle('btn-clean', 'clean'));
window.addEventListener('keydown', e => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const k = e.key.toLowerCase();
  if (k === ' ') { e.preventDefault(); setPlaying(!playing); }
  else if (k === 'arrowright') stepAct(1);
  else if (k === 'arrowleft') stepAct(-1);
  else if (/^[0-6]$/.test(k)) seek(ACTS[Number(k)].start);
  else if (k === 'h') toggle('btn-clean', 'clean');
  else if (k === 'c') document.body.classList.toggle('nocap');
  else if (k === 's') setSources(!sourcesOpen);
  else if (k === 'r') { seek(0); setPlaying(true); }
});

// orbit by hand while paused or after the end
const canvas = renderer.domElement;
let drag = null;
canvas.addEventListener('pointerdown', e => { if (!playing) { drag = { x: e.clientX, y: e.clientY }; canvas.setPointerCapture(e.pointerId); } });
canvas.addEventListener('pointermove', e => {
  if (!drag) return;
  orbit.theta -= (e.clientX - drag.x) * .005;
  orbit.phi = Math.max(-.9, Math.min(.9, orbit.phi - (e.clientY - drag.y) * .004));
  drag = { x: e.clientX, y: e.clientY };
});
canvas.addEventListener('pointerup', () => { drag = null; });
canvas.addEventListener('wheel', e => { if (!playing) { e.preventDefault(); orbit.zoom = Math.max(.45, Math.min(2.2, orbit.zoom * (1 + e.deltaY * .001))); } }, { passive: false });

// captions: swap with a short fade, only when the line actually changes
const capEl = $('caption');
let capKey = '', capTimer = 0;
function setCaption(ai) {
  const a = ACTS[ai];
  let line = a.captions[0];
  for (const c of a.captions) if (c[0] <= t) line = c;
  const key = ai + '|' + line[1];
  if (key === capKey) return;
  capKey = key;
  capEl.classList.add('swap');
  clearTimeout(capTimer);
  capTimer = setTimeout(() => {
    $('cap-act').textContent = `ฉาก ${a.code} · ${a.name}`;
    $('cap-th').textContent = line[1];
    $('cap-sub').textContent = line[2];
    capEl.classList.remove('swap');
  }, reduced ? 0 : 220);
}
const fmt = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;

/* =====================================================================
   9. LOOP
   ===================================================================== */
function resize() {
  const w = stageEl.clientWidth, h = stageEl.clientHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / Math.max(h, 1);
  camera.updateProjectionMatrix();
}
window.addEventListener('resize', resize);
resize();
setPlaying(playing);

let last = performance.now();
function frame(now) {
  const dt = Math.min(.1, (now - last) / 1000);
  last = now;
  const rate = reduced ? .4 : 1;
  if (playing) {
    t += dt; amb += dt * rate;
    if (t >= TOTAL) { t = TOTAL; ended = true; playing = false; setIcon(PLAY_D); }
  } else if (ended) {
    amb += dt * rate;
  }
  const ai = evaluate(t, amb);
  placeCamera(t, camera.aspect);
  renderer.render(scene, camera);
  placeLabels(stageEl.clientWidth, stageEl.clientHeight);
  setCaption(ai);
  actBtns.forEach((b, i) => {
    const a = ACTS[i];
    b.firstChild.style.transform = `scaleX(${clamp01((t - a.start) / (a.end - a.start))})`;
    b.setAttribute('aria-current', String(i === ai));
  });
  $('clock').textContent = `${fmt(t)} / ${fmt(TOTAL)}`;
  if (sourcesOpen && sourcesAct !== ai) renderSources(ai);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
