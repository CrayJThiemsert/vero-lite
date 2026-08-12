/* ============================================================
   OCT — operate auth-module (PLAN-0054 SD-A ii).

   The SINGLE frontend credential seam for OPERATE POSTs (gate/resolve,
   cancel). v1 holds a pilot static API key (PLAN-0047) in sessionStorage;
   v2 swaps the credential SOURCE *here* (key -> a session token) without
   touching the operate UI or the backend's get_current_principal dependency.

   Reads stay header-less (view-monitor getJSON) — only operate POSTs attach
   Bearer via authHeader(). The stored key is per-tab (sessionStorage: cleared
   on tab close), never localStorage. login() VALIDATES the key at login by
   probing GET /whoami (PLAN-0058) — the ONE auth-validating read — so a bad key
   is rejected AT login instead of on the first operate POST; the display identity
   is still what the operator typed (login-SHAPED — the REAL auth is the key the
   backend resolves to a person_id + SoD-checks, so the display cannot escalate
   privilege). v2's clean upgrade: swap the credential SOURCE (key -> session
   token) behind the same probe + get_current_principal seam.
   ============================================================ */
(function () {
  'use strict';
  const KEY = 'oct.operate.session';  // sessionStorage key (per-tab)

  function session() {
    try { return JSON.parse(sessionStorage.getItem(KEY) || 'null'); }
    catch (e) { return null; }
  }
  function isLoggedIn() { const s = session(); return !!(s && s.key); }
  function identity() { const s = session(); return s ? s.identity : null; }
  // PLAN-0103 Step 6 — the audited id, and whether the server is the one who
  // said so. Two accessors rather than one because the banner's claim depends on
  // the second: "recorded in the audit trail under this name" is true only when
  // the name came back from /whoami.
  function personId() { const s = session(); return s ? (s.person_id || null) : null; }
  function serverResolved() { const s = session(); return !!(s && s.server_resolved); }

  async function login(rawKey, ident) {
    const key = (rawKey || '').trim();
    if (!key) throw new Error('Enter your operator API key.');
    // Reject-at-login (PLAN-0058): probe the fail-closed auth seam with the
    // entered key BEFORE storing a session. A bad key -> 401/403 surfaces here
    // instead of on the first operate POST. With auth disabled the probe returns
    // 200 (dev/demo open mode), so login proceeds as before.
    const res = await fetch('/whoami', { headers: { Authorization: 'Bearer ' + key } });
    if (!res.ok) {
      let detail = 'Login failed — invalid operator key (HTTP ' + res.status + ').';
      try { const body = await res.json(); if (body && body.detail) detail = body.detail; }
      catch (e) { /* non-JSON error body */ }
      throw new Error(detail);
    }
    // PLAN-0103 Step 6: the SERVER's resolved identity WINS over anything typed.
    // /whoami already returns the authored Person.name for the key it resolved
    // (routers/whoami.py), and until now that answer was discarded in favour of
    // free text. On a published surface that gap is the whole problem: a visitor
    // could type any name and it rendered beside a real governed decision. This
    // is not a privilege fix — the backend always resolved the person from the
    // key — it is a DISPLAY-honesty fix, and it is what lets the persona picker
    // promise "recorded under this name" without qualification.
    //
    // The typed value survives only as the fallback for auth-disabled dev boxes,
    // where /whoami answers person_id=null because there is nobody to resolve.
    let served = null;
    try { served = await res.json(); }
    catch (e) { /* non-JSON 200 — fall back to what was typed */ }
    const resolved = served && (served.display_name || served.person_id);
    const id = resolved || (ident || '').trim();
    if (!id) throw new Error('Enter a display identity (e.g. appr-pm).');
    sessionStorage.setItem(KEY, JSON.stringify({
      key: key,
      identity: id,
      // Kept distinct from `identity`: the display string is bilingual prose
      // ("วิรัช — ผจก.เดินรถ"), while this is the id the audit trail records.
      // The disclosure banner shows both, so a visitor can match what they see
      // on screen to what they would find in the trace.
      person_id: served ? (served.person_id || null) : null,
      // True when the server resolved the identity itself. The banner reads this
      // to decide whether it may claim the name is the audited one — on a dev box
      // with auth disabled it is just what someone typed, and saying otherwise
      // would be the same lie in the opposite direction.
      server_resolved: !!resolved
    }));
    return session();
  }
  function logout() { sessionStorage.removeItem(KEY); }

  // Bearer header for OPERATE POSTs ONLY — never attached to reads.
  function authHeader() {
    const s = session();
    return s && s.key ? { Authorization: 'Bearer ' + s.key } : {};
  }

  window.OCT = window.OCT || {};
  window.OCT.Auth = { login: login, logout: logout, authHeader: authHeader,
    session: session, isLoggedIn: isLoggedIn, identity: identity,
    personId: personId, serverResolved: serverResolved };
})();
