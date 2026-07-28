"""The fleet's PM data import — parsing half (PLAN-0096 Step 9 / AC-10).

Two odometer figures drive the AT-3 calm path, and the partner has neither of them in
a system today:

* the **current** odometer, which his trucks already report — "รถผมติด GPS ไว้แล้วนะ" —
  but which lives in Wialon and is read by eye;
* the **last-service** odometer, which lives in a paper folder in the office and is the
  number every `next_service_due_km` in this vertical is currently GUESSING.

This module turns an exported CSV of either into typed proposals. It does not write
anything, does not know what a fleet is, and does not decide whether a proposal is
right — that is the confirm step's job (``services/db/pm_import.py``), because Q4 is
explicit that the telematics figure is approximate and a human has to look at it
before it becomes the truck's odometer.

**Why import instead of a live API.** Q4 is LOCKED to CSV export + human confirm.
The partner's Wialon figures drift against the dashboard, and an API that silently
overwrote a truck's odometer every few minutes would make every PM due-date a moving
target nobody could audit. A file he exports on a Monday, reviewed by เมย์, is slower
and enormously more honest.

**Fail closed on a mangled file, per row on a mismatched one.** Structure and type
errors abort the WHOLE parse (a file whose header is wrong is not a file we understand,
and half-importing it would leave a fleet in an unknown state). A row naming a plate
the fleet does not have is NOT a mangled file — it is a real, ordinary onboarding
event — so it survives parsing and is rejected, visibly, at the matching step. The
distinction matters: aborting a twenty-truck import because one plate was retired last
month would train เมย์ to stop importing.

Pure + deterministic: no DB, no network, no clock, no LLM.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from typing import Final

#: The service interval, in km. A logged customer answer — "เข้าศูนย์ทุกแสนกิโลฯ"
#: (PLAN-0089 M-5 Q1) — one fixed interval across every truck class. It lives here
#: rather than in the ontology YAML because ``next_service_due_km`` is stored ABSOLUTE:
#: the projection grammar is a fields-only rename with no arithmetic, so there is
#: nowhere downstream to compute `last_service + interval`. This module is that
#: nowhere.
SERVICE_INTERVAL_KM: Final = 100_000.0

#: The plate column — the partner identifies trucks by plate, never by our internal
#: ``truck_id``, and an onboarding CSV he assembles by hand will carry what he knows.
COLUMN_PLATE: Final = "plate"
#: The current telematics reading (the Wialon export half).
COLUMN_ODOMETER: Final = "odometer_km"
#: The paper-PM-folder half. When present, ``next_service_due_km`` is computed here.
COLUMN_LAST_SERVICE: Final = "last_service_odometer_km"

#: Every column this importer understands. **The partner's actual Wialon export
#: header is a named intake question** (alongside the Express export columns) — when
#: his real file arrives, this tuple and ``_normalise_header`` are the only things
#: that change. Naming the seam beats scattering header guesses through the parser.
KNOWN_COLUMNS: Final = (COLUMN_PLATE, COLUMN_ODOMETER, COLUMN_LAST_SERVICE)

#: At least one of these must be present, or the file proposes nothing.
VALUE_COLUMNS: Final = (COLUMN_ODOMETER, COLUMN_LAST_SERVICE)


class PmImportError(ValueError):
    """The CSV could not be understood, so NOTHING is proposed from it (AC-10).

    Carries the row number when the fault is a specific row, so เมย์ is told which
    line to look at rather than being handed 'invalid file'."""


@dataclass(frozen=True)
class ProposedReading:
    """One parsed row — a PROPOSAL about one truck, binding on nothing.

    ``next_service_due_km`` is already absolute here rather than being computed later:
    the arithmetic happens exactly once, at load, in the one module that owns the
    interval. A consumer that received `last_service` and an interval separately would
    eventually add them somewhere else, and the two answers would drift.
    """

    row_number: int
    plate: str
    odometer_km: float | None = None
    last_service_odometer_km: float | None = None
    next_service_due_km: float | None = None


def next_service_due_from(last_service_odometer_km: float) -> float:
    """The ABSOLUTE odometer point at which the next interval service falls due.

    One line, one caller today, and still its own function: this is the arithmetic the
    ontology comment promises is done at load, and a reader checking that promise
    should find it under a name rather than inline in a parser loop.
    """
    return last_service_odometer_km + SERVICE_INTERVAL_KM


def _normalise_header(name: str) -> str:
    """Lower-case, trim, and drop a UTF-8 BOM from one header cell.

    Exports carry a BOM and stray spaces routinely, and a header that differs from
    ``plate`` only by an invisible byte would otherwise fail the file with a message
    naming two identical-looking strings."""
    return name.replace("﻿", "").strip().lower()


def _parse_km(raw: str, *, row_number: int, column: str) -> float | None:
    """Parse one odometer cell, failing CLOSED on anything that is not a real distance.

    An empty cell means 'this row says nothing about this column' and is legitimate —
    the paper-folder file carries no telematics reading and vice versa. Anything else
    that will not parse is a mangled file, because silently coercing it would put an
    invented number in front of a human as though the export had said it. Thousands
    separators are accepted: real exports contain them, and rejecting `412,580` would
    fail honest files for a formatting choice the partner does not control.
    """
    text = raw.replace("﻿", "").strip().replace(",", "")
    if not text:
        return None
    try:
        value = float(text)
    except ValueError as exc:
        raise PmImportError(
            f"row {row_number}: column '{column}' is not a number (got {raw!r}) — "
            "refusing the whole file rather than importing a guessed odometer"
        ) from exc
    if value < 0:
        raise PmImportError(
            f"row {row_number}: column '{column}' is negative ({value}) — an odometer "
            "cannot run backwards, so this file is not the export it claims to be"
        )
    return value


def parse_pm_csv(text: str) -> list[ProposedReading]:
    """Parse a PM CSV export into proposals, failing CLOSED on a mangled file.

    Accepts the Wialon odometer export (``plate`` + ``odometer_km``), the paper-PM-
    folder onboarding sheet (``plate`` + ``last_service_odometer_km``), or one file
    carrying both. Returns proposals in file order; the caller matches them to trucks
    and persists them as unconfirmed.

    Raises :class:`PmImportError` on: an empty file, a missing header, a missing
    ``plate`` column, neither value column, a blank plate, a non-numeric or negative
    odometer, or the same plate appearing twice (which would make the confirm step
    ambiguous about which reading a human accepted).
    """
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise PmImportError("the file is empty — there is no header row to read")

    header = [_normalise_header(name) for name in reader.fieldnames]
    if COLUMN_PLATE not in header:
        raise PmImportError(
            f"the header has no '{COLUMN_PLATE}' column (found {header}) — every "
            "proposal must name the truck it is about"
        )
    present_values = [column for column in VALUE_COLUMNS if column in header]
    if not present_values:
        raise PmImportError(
            f"the header carries none of {list(VALUE_COLUMNS)} (found {header}) — this "
            "file proposes nothing about any truck"
        )

    proposals: list[ProposedReading] = []
    seen: dict[str, int] = {}
    # Row 1 is the header, so the first data row is row 2 — the number เมย์ sees in
    # her spreadsheet, not a zero-based index into a list she cannot see.
    for offset, raw_row in enumerate(reader, start=2):
        row = {_normalise_header(k): (v or "") for k, v in raw_row.items() if k is not None}
        plate = row.get(COLUMN_PLATE, "").replace("﻿", "").strip()
        if not plate:
            raise PmImportError(f"row {offset}: the '{COLUMN_PLATE}' cell is blank")
        if plate in seen:
            raise PmImportError(
                f"row {offset}: plate {plate!r} already appeared on row {seen[plate]} — "
                "a file with two readings for one truck is ambiguous about which one a "
                "human would be confirming"
            )
        seen[plate] = offset

        odometer = _parse_km(
            row.get(COLUMN_ODOMETER, ""), row_number=offset, column=COLUMN_ODOMETER
        )
        last_service = _parse_km(
            row.get(COLUMN_LAST_SERVICE, ""), row_number=offset, column=COLUMN_LAST_SERVICE
        )
        if odometer is None and last_service is None:
            raise PmImportError(
                f"row {offset}: plate {plate!r} carries no value in any of "
                f"{list(VALUE_COLUMNS)} — an empty proposal cannot be confirmed into "
                "anything"
            )
        proposals.append(
            ProposedReading(
                row_number=offset,
                plate=plate,
                odometer_km=odometer,
                last_service_odometer_km=last_service,
                next_service_due_km=(
                    None if last_service is None else next_service_due_from(last_service)
                ),
            )
        )

    if not proposals:
        raise PmImportError("the file has a valid header but no data rows — nothing to propose")
    return proposals
