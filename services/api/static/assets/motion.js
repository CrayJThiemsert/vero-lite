/* ============================================================
   OCT — Motion driver (PLAN-0033 Phase C, AC-10 / AC-12 / AC-13).

   The single orchestration seam for story-mode animation. Every
   tween / loop / timer / rAF / listener is registered on a *scope*
   so that scope.kill() tears DOWN the lot — this is how the
   lifecycle teardown contract (AC-13) is enforced: a scene owns one
   Motion scope, leave -> scope.kill() -> zero leaked timelines.

   Driver: a zero-dependency WAAPI + rAF + timer implementation. It
   is also the reduced-motion floor (AC-10) and the offline default
   (AC-12, no CDN). GSAP is the planned primary spine (PLAN-0033 F3);
   once its 2026 licence is verified and it is vendored locally, a
   GSAP-backed driver can register behind this same scope() interface
   (see Motion.useDriver) without touching scene code.

   prefers-reduced-motion: tweens/loops/travel collapse to their
   final visual state instantly (state still reads as colour+icon+
   label); narration *pacing* (after/every) is preserved — reduced
   motion suppresses MOTION, not the click-through timing.
   ============================================================ */
(function () {
  'use strict';

  const reduceMQ = window.matchMedia
    ? window.matchMedia('(prefers-reduced-motion: reduce)')
    : { matches: false };
  function reduced() { return !!reduceMQ.matches; }

  // Global live registry — the AC-13 leak probe reads this. Anything
  // still here after every scope is killed is a leak.
  const live = { anims: new Set(), timers: new Set(), rafs: new Set(), listeners: new Set() };

  function applyFinalFrame(el, keyframes) {
    const last = Array.isArray(keyframes) ? keyframes[keyframes.length - 1] : keyframes;
    if (!last || typeof last !== 'object') return;
    Object.keys(last).forEach(k => {
      if (k === 'offset' || k === 'easing' || k === 'composite') return;
      try { el.style[k] = last[k]; } catch (e) { /* non-style key */ }
    });
  }

  function makeScope(name) {
    const anims = new Set();      // WAAPI Animation handles
    const timers = new Set();     // setTimeout / setInterval ids
    const rafs = new Set();       // requestAnimationFrame ids
    const listeners = [];         // { target, type, fn, opts }
    let killed = false;

    function dropAnim(a) { anims.delete(a); live.anims.delete(a); }

    const scope = {
      name: name || 'scope',
      get killed() { return killed; },

      /* one-shot tween; reduced-motion -> jump to final frame, no motion */
      tween(el, keyframes, opts) {
        opts = opts || {};
        if (killed || !el || !el.animate) return Promise.resolve();
        if (reduced()) { applyFinalFrame(el, keyframes); return Promise.resolve(); }
        const dur = opts.duration != null ? opts.duration : 420;
        const a = el.animate(keyframes, Object.assign({ duration: 420, easing: 'cubic-bezier(.4,0,.2,1)', fill: 'both' }, opts));
        anims.add(a); live.anims.add(a);
        const drop = () => dropAnim(a);
        a.addEventListener('finish', drop);
        a.addEventListener('cancel', drop);
        if (a.finished && a.finished.then) a.finished.then(drop, drop);
        // backstop: even if 'finish' / the finished promise never settle (a
        // backgrounded tab or throttled document timeline can leave a one-shot
        // "running"), drop the handle shortly after it should have completed so
        // the activeCount() leak probe (AC-13) stays accurate and bounded across
        // a long session. The element itself is removed on teardown.
        const bt = setTimeout(() => { timers.delete(bt); live.timers.delete(bt); drop(); }, dur + 250);
        timers.add(bt); live.timers.add(bt);
        return a.finished ? a.finished.catch(() => {}) : Promise.resolve();
      },

      /* infinite loop (active-node pulse, edge flow); reduced-motion -> no-op (the
         static colour+icon+label already encodes the state) */
      loop(el, keyframes, opts) {
        if (killed || !el || !el.animate || reduced()) return null;
        const a = el.animate(keyframes, Object.assign({ duration: 1300, easing: 'ease-in-out', iterations: Infinity }, opts));
        anims.add(a); live.anims.add(a);
        return a;
      },

      /* travel a token dot from (x0,y0) to (x1,y1); reduced-motion -> snap to end */
      travel(el, x0, y0, x1, y1, opts) {
        if (killed || !el) return Promise.resolve();
        const from = 'translate(' + x0 + 'px,' + y0 + 'px)';
        const to = 'translate(' + x1 + 'px,' + y1 + 'px)';
        return this.tween(el, [{ transform: from }, { transform: to }], Object.assign({ duration: 700, easing: 'ease-in-out' }, opts));
      },

      /* narration pacing — timing preserved under reduced-motion */
      after(ms, fn) {
        if (killed) return null;
        const id = setTimeout(() => { timers.delete(id); live.timers.delete(id); if (!killed) fn(); }, ms);
        timers.add(id); live.timers.add(id);
        return id;
      },
      every(ms, fn) {
        if (killed) return null;
        const id = setInterval(() => { if (!killed) fn(); }, ms);
        timers.add(id); live.timers.add(id);
        return id;
      },
      cancelTimer(id) {
        if (id == null) return;
        clearTimeout(id); clearInterval(id);
        timers.delete(id); live.timers.delete(id);
      },
      raf(fn) {
        if (killed) return null;
        const id = requestAnimationFrame((t) => { rafs.delete(id); live.rafs.delete(id); if (!killed) fn(t); });
        rafs.add(id); live.rafs.add(id);
        return id;
      },

      /* listeners go through the scope so teardown detaches them */
      on(target, type, fn, opts) {
        if (killed || !target) return fn;
        target.addEventListener(type, fn, opts);
        const rec = { target, type, fn, opts };
        listeners.push(rec); live.listeners.add(rec);
        return fn;
      },

      /* the teardown contract: kill EVERYTHING this scope owns */
      kill() {
        if (killed) return;
        killed = true;
        anims.forEach(a => { try { a.cancel(); } catch (e) {} live.anims.delete(a); });
        anims.clear();
        timers.forEach(id => { clearTimeout(id); clearInterval(id); live.timers.delete(id); });
        timers.clear();
        rafs.forEach(id => { cancelAnimationFrame(id); live.rafs.delete(id); });
        rafs.clear();
        listeners.forEach(r => { try { r.target.removeEventListener(r.type, r.fn, r.opts); } catch (e) {} live.listeners.delete(r); });
        listeners.length = 0;
      }
    };
    return scope;
  }

  window.OCT = window.OCT || {};
  window.OCT.Motion = {
    scope: makeScope,
    reduced: reduced,
    /* AC-13 leak probe — total must be 0 after every scope is killed */
    activeCount: function () {
      return {
        anims: live.anims.size,
        timers: live.timers.size,
        rafs: live.rafs.size,
        listeners: live.listeners.size,
        total: live.anims.size + live.timers.size + live.rafs.size + live.listeners.size
      };
    },
    driver: 'waapi'
    /* useDriver(gsapDriver): reserved seam for the vendored-GSAP spine (F3). */
  };
})();
