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

  async function login(rawKey, ident) {
    const key = (rawKey || '').trim();
    const id = (ident || '').trim();
    if (!key) throw new Error('Enter your operator API key.');
    if (!id) throw new Error('Enter a display identity (e.g. appr-pm).');
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
    sessionStorage.setItem(KEY, JSON.stringify({ key: key, identity: id }));
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
    session: session, isLoggedIn: isLoggedIn, identity: identity };
})();
