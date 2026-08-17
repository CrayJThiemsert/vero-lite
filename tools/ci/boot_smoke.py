"""Boot the app's LIFESPAN in CI, not just its import (PLAN-0107 AC-3).

The CI step this replaces ran ``python -c "import services.api.main"``. That
proves the runtime dependency closure can *import* the entry module — a real
property, and the reason the step exists (an image that could not import at all
shipped for ten days while every test stayed green). But importing is not
booting. Everything the spine actually does on startup happens inside
``lifespan``:

* ``discover_and_register()`` across the vertical plugin trees,
* the six lazy executor registrars,
* persona resolution,
* ``procedures.yaml`` parsing — which ``CLAUDE.md`` §3 promises "fails loudly at
  load, never mid-run".

**That promise had no CI consumer.** A malformed spec, a registrar whose lazy
import is broken in the runtime (``--no-dev``) dependency set, or a persona
resolution failure all sail past an import probe and surface on the live
surface instead. Entering the context manager is what makes the fail-loud
contract CI-visible for the first time.

🔴 **The spec-load catch is ACTIVE-VERTICAL dependent — measured, not assumed.**
``lifespan`` registers only ``_PROCEDURE_EXECUTOR_REGISTRARS[OCT_VERTICAL]``, so
this smoke reaches a ``procedures.yaml`` parse only when *that* vertical's
factory calls ``load_procedures``. Corrupting each spec in turn and booting
(session 235, measured):

===================  =========================================
active vertical      malformed ``procedures.yaml``
===================  =========================================
fleet_maintenance    **CAUGHT** — boot reddens
building_materials   **CAUGHT**
supply_chain         **CAUGHT**
procurement          **CAUGHT**
energy               ⚠️ **MISSED** — boots green
===================  =========================================

⚠️ ``energy`` is the **default** ``OCT_VERTICAL``, and
``verticals/energy/procedures_factory.py`` is the one spec-shipping factory that
never calls ``load_procedures``. Booting the default alone would therefore have
made the weakest possible version of this claim — green, and blind to exactly
the vertical CI runs. **CI runs this smoke once per spec-shipping vertical**
(enumerated from disk, not a frozen list); the ``energy`` residual is real and
stays open — closing it means energy's factory loading its own spec, which is a
behaviour change and out of PLAN-0107's scope.

What this deliberately does NOT claim: the projection loads inside ``lifespan``
are **fail-soft by design** and keep their own dedicated guard
(``tests/test_startup_fleet_projections.py``). This smoke catches the
lifespan-*raising* class only. A green here is not a claim that the app is
healthy — only that booting it does not raise.

Run: ``OCT_VERTICAL=<name> /tmp/vero-runtime-venv/bin/python tools/ci/boot_smoke.py``
Exits 0 on a clean boot, 1 on any exception — and prints a verdict line naming
the vertical either way, because an echoed exit code travels the same corruptible
channel as everything else (Lesson #0007), and a failure that does not name which
vertical it booted is a failure nobody can act on (Lesson #0043).
"""

from __future__ import annotations

import os
import sys
import traceback


def main() -> int:
    vertical = os.environ.get("OCT_VERTICAL", "(default)")
    try:
        # Imported inside main() so an import failure is reported by the same
        # handler as a boot failure, with the same verdict line — rather than
        # dying at module scope with a bare traceback and no verdict.
        from fastapi.testclient import TestClient

        from services.api.main import app

        with TestClient(app):
            pass
    except Exception:
        traceback.print_exc()
        print(
            f"BOOT_SMOKE: FAIL [{vertical}] — lifespan raised (see traceback above)",
            file=sys.stderr,
        )
        return 1
    print(f"BOOT_SMOKE: OK [{vertical}] — lifespan entered and exited cleanly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
