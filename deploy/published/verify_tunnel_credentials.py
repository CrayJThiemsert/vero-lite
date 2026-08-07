#!/usr/bin/env python3
"""Verify a cloudflared LOCALLY-MANAGED tunnel credentials file — without ever
printing its secret.

Everything this prints is safe to paste into a chat, a PR body or a ticket:
shapes, lengths, PASS/FAIL, and a SHA-256 fingerprint of the file. The
``TunnelSecret`` is never echoed and the ``TunnelID`` is masked to its last four
characters — the cross-checks that would otherwise need the full value are done
here, locally, so nobody has to send it anywhere.

Used by ``docs/runbooks/published-demo-bring-up.md`` §4.

Usage
-----
    python3 verify_tunnel_credentials.py <credentials.json> [config.yml]

Exit code is 0 only when every check passes.

Why a fingerprint: after copying the file from the machine that ran
``cloudflared tunnel create`` to the machine that will run the tunnel, run this
on BOTH and compare the ``fingerprint`` line. Equal fingerprints prove the copy
arrived byte-identical; a truncated or newline-mangled copy shows up here rather
than as a mystery at ``docker compose up``, where the error for a corrupt
credentials file is not obviously about the file.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import re
import sys
from pathlib import Path

_UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
_HEX32 = re.compile(r"^[0-9a-fA-F]{32}$")

#: cloudflared writes these three, and they are what the tunnel actually needs.
_REQUIRED = frozenset({"AccountTag", "TunnelID", "TunnelSecret"})

#: Keys cloudflared may also emit. Tolerated, never required.
#:
#: ``Endpoint`` is here because the first real ``tunnel create`` reddened this
#: check: 2025.8.1 writes it (empty on a standard account) and the allowlist,
#: written from the classic three-key shape, had never seen it. Measured, not
#: assumed — which is the only reason it is safe to widen. ``TunnelName`` comes
#: from older builds.
#:
#: The strictness is deliberate and stays: an unexpected key is how a
#: hand-edited file, or a TUNNEL_TOKEN blob pasted in by mistake, gets caught
#: instead of silently tolerated. Widening this set is a decision, not a
#: convenience — add a key only after seeing cloudflared itself write it.
_OPTIONAL = frozenset({"TunnelName", "Endpoint"})

_results: list[tuple[str, bool, str]] = []


def check(label: str, ok: bool, detail: str = "") -> bool:
    """Record one check and return its verdict, so callers can early-exit."""
    _results.append((label, ok, detail))
    return ok


def _enclosing_repo(path: Path) -> Path | None:
    """The nearest ancestor containing a ``.git`` entry, if any."""
    start = path.resolve().parent
    for parent in [start, *start.parents]:
        if (parent / ".git").exists():
            return parent
    return None


def main(argv: list[str]) -> int:
    if not 2 <= len(argv) <= 3:
        print(__doc__)
        return 2

    cred_path = Path(argv[1]).expanduser()
    cfg_path = Path(argv[2]).expanduser() if len(argv) == 3 else None

    print("=== vero-lite tunnel credentials verifier ===")
    print(f"path                 : {cred_path}")

    # --- 1. it must live OUTSIDE any git worktree -------------------------- #
    # A credentials file inside the repo is one `git add -A` away from a public
    # commit (CLAUDE.md §8).
    in_repo = _enclosing_repo(cred_path)
    check(
        "outside any git repo",
        in_repo is None,
        "" if in_repo is None else f"FOUND INSIDE {in_repo} — move it out, now",
    )

    # --- 2. exists, non-empty, plausible size ------------------------------ #
    if not cred_path.is_file():
        check("exists", False, "no such file")
        return report()
    size = cred_path.stat().st_size
    check("exists / non-empty", size > 0, f"{size} bytes")
    # A real credentials file is a small one-line JSON object. Well outside this
    # band means truncation, a pasted token, or the wrong file entirely.
    check("plausible size (120-600 B)", 120 <= size <= 600, f"{size} bytes")

    raw = cred_path.read_bytes()
    print(f"fingerprint (sha256) : {hashlib.sha256(raw).hexdigest()}")

    # --- 3. valid JSON with exactly the expected keys ---------------------- #
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        check("valid JSON", False, f"{type(exc).__name__}: {exc}")
        return report()
    check("valid JSON", isinstance(data, dict), type(data).__name__)
    if not isinstance(data, dict):
        return report()

    keys = set(data)
    missing = _REQUIRED - keys
    unexpected = keys - _REQUIRED - _OPTIONAL
    check("required keys present", not missing, f"missing {sorted(missing)}" if missing else "")
    check(
        "no unexpected keys",
        not unexpected,
        f"unexpected {sorted(unexpected)} — is this a TUNNEL_TOKEN blob or hand-edited?"
        if unexpected
        else "",
    )
    if missing:
        return report()

    # --- 4. each field has the right SHAPE (never the value) --------------- #
    account = str(data["AccountTag"])
    check("AccountTag shape", bool(_HEX32.match(account)), f"len={len(account)}, want 32 hex")

    tunnel_id = str(data["TunnelID"])
    masked = f"...{tunnel_id[-4:]}" if len(tunnel_id) >= 4 else "<short>"
    check("TunnelID shape", bool(_UUID.match(tunnel_id)), f"uuid {masked}")

    secret = str(data["TunnelSecret"])
    try:
        decoded = base64.b64decode(secret, validate=True)
        ok_secret = len(decoded) == 32
        detail = f"base64 -> {len(decoded)} bytes, want 32"
    except (binascii.Error, ValueError) as exc:
        ok_secret = False
        detail = f"not valid base64 ({type(exc).__name__})"
    check("TunnelSecret shape", ok_secret, detail)

    # --- 5. permissions ---------------------------------------------------- #
    if os.name == "posix":
        mode = cred_path.stat().st_mode & 0o777
        check("permissions <= 0600", mode <= 0o600, f"{mode:04o}")
    else:
        check("permissions", True, "skipped on Windows — check the ACL by hand")

    # --- 6. cross-check the committed ingress config ----------------------- #
    _cross_check_config(cfg_path, tunnel_id)
    return report()


def _cross_check_config(cfg_path: Path | None, tunnel_id: str) -> None:
    """Compare the committed ingress config's ``tunnel:`` against these credentials."""
    if cfg_path is None:
        print("\n(no config.yml given — skipping the cross-check)")
        return
    if not cfg_path.is_file():
        check("config.yml readable", False, f"no such file: {cfg_path}")
        return

    match = re.search(r"^tunnel:\s*(\S+)\s*$", cfg_path.read_text(encoding="utf-8"), re.MULTILINE)
    if match is None:
        check("config.yml declares tunnel:", False, "no `tunnel:` key found")
        return
    declared = match.group(1)

    if _UUID.match(declared):
        # The good case: the config names the tunnel by UUID, so this file can be
        # matched to it offline AND cloudflared needs no origin cert at runtime.
        check(
            "config tunnel: matches credentials",
            declared.lower() == tunnel_id.lower(),
            "UUID form — fully checkable offline",
        )
        return

    # `tunnel: <name>` cannot be resolved from a credentials file alone;
    # cloudflared looks the name up through the account origin cert
    # (~/.cloudflared/cert.pem). If that cert is absent on the machine running
    # the tunnel, this fails at RUN time, not here.
    check(
        "config tunnel: matches credentials",
        False,
        f"config says {declared!r} (a NAME, not a UUID) — not verifiable against "
        "this file offline, and cloudflared resolves a name via the account cert, "
        "which the deploy host may not have",
    )
    print()
    print("NOTE — name-vs-UUID. See the bring-up runbook §2.3. Using the UUID makes")
    print("the run cert-free and makes this cross-check real. Settle it by running")
    print("the tunnel on the deploy host; that is the only true test.")


def report() -> int:
    """Print the ledger and return a shell exit code."""
    print()
    width = max(len(label) for label, _, _ in _results)
    failed = sum(1 for _, ok, _ in _results if not ok)
    for label, ok, detail in _results:
        suffix = f"  ({detail})" if detail else ""
        print(f"{label.ljust(width)} : {'PASS' if ok else 'FAIL'}{suffix}")
    print()
    print(f"=== {len(_results)} checks, {failed} FAIL ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
