/* ============================================================
   OCT — operate auth-module (PLAN-0054 SD-A ii).

   The SINGLE frontend credential seam for OPERATE POSTs (gate/resolve,
   cancel). v1 holds a pilot static API key (PLAN-0047) in sessionStorage;
   v2 swaps the credential SOURCE *here* (key -> a session token) without
   touching the operate UI or the backend's get_current_principal dependency.

   Reads stay header-less (view-monitor getJSON) — only operate POSTs attach
   Bearer via authHeader(). The stored key is per-tab (sessionStorage: cleared
   on tab close), never localStorage. login() is OPTIMISTIC: the shipped API has
   no auth-validating READ to probe (reads are ungated), so a bad key surfaces as
   a 403 on the first operate POST; the display identity is what the operator
   typed (login-SHAPED — the REAL auth is the key the backend resolves to a
   person_id + SoD-checks, so the display cannot escalate privilege). v2's clean
   upgrade: validate the credential + resolve the identity server-side.
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

  function login(rawKey, ident) {
    const key = (rawKey || '').trim();
    const id = (ident || '').trim();
    if (!key) throw new Error('Enter your operator API key.');
    if (!id) throw new Error('Enter a display identity (e.g. appr-pm).');
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
