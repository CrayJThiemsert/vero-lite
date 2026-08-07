"""The shipped credentials verifier — guarded, because it shipped unguarded.

`deploy/published/verify_tunnel_credentials.py` is an operator tool the bring-up
runbook tells people to trust, and it had no tests at all. Its very first run
against a real `cloudflared tunnel create` reddened: 2025.8.1 writes a fourth key
(`Endpoint`) that the allowlist, written from the classic three-key shape, had
never seen. The file was fine; the tool was wrong.

**These tests drive `main()` and read the ledger it records.** The first draft
re-implemented the script's set arithmetic in a helper and compared against that
— which promptly disagreed with itself over which side of `_REQUIRED - keys` was
"missing". A guard that recomputes what it is guarding can only ever prove the
copy is self-consistent, so every case below writes a real file, runs the real
entry point, and asserts on the real verdicts.

The script is loaded by path rather than imported: it lives under `deploy/`,
which is not on the import path and is not meant to be.
"""

from __future__ import annotations

import base64
import importlib.util
import json
import os
from pathlib import Path
from types import ModuleType

import pytest

_SCRIPT = Path("deploy/published/verify_tunnel_credentials.py")
_CONFIG = Path("deploy/published/cloudflared/config.yml")
_RUNBOOK = Path("docs/runbooks/published-demo-bring-up.md")

#: A well-formed credentials file as cloudflared 2025.8.1 actually writes one —
#: four keys, `Endpoint` empty. Structurally valid and semantically meaningless.
_REAL_SHAPE: dict[str, str] = {
    "AccountTag": "0" * 32,
    "TunnelID": "11111111-2222-3333-4444-555555555555",
    "TunnelSecret": base64.b64encode(bytes(32)).decode(),
    "Endpoint": "",
}

#: The one check that cannot pass while `config.yml` names the tunnel rather than
#: identifying it by UUID. Expected, and documented in the runbook as expected.
_NAME_VS_UUID = "config tunnel: matches credentials"


@pytest.fixture(scope="module")
def verifier() -> ModuleType:
    """The script, loaded from its committed path."""
    assert _SCRIPT.is_file(), f"{_SCRIPT} is missing — the runbook tells operators to run it"
    spec = importlib.util.spec_from_file_location("verify_tunnel_credentials", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(
    verifier: ModuleType,
    tmp_path: Path,
    payload: object,
    *,
    mode: int = 0o600,
    with_config: bool = False,
    in_repo: bool = False,
) -> dict[str, bool]:
    """Write `payload`, run the real `main()`, return {check label: passed}."""
    home = tmp_path / ("repo" if in_repo else "outside")
    home.mkdir(parents=True, exist_ok=True)
    if in_repo:
        (home / ".git").mkdir(exist_ok=True)
        home = home / "sub"
        home.mkdir(exist_ok=True)

    cred = home / "creds.json"
    cred.write_text(payload if isinstance(payload, str) else json.dumps(payload), "utf-8")
    cred.chmod(mode)

    argv = ["verify", str(cred)]
    if with_config:
        argv.append(str(_CONFIG))

    verifier._results.clear()
    verifier.main(argv)
    return {label: ok for label, ok, _ in verifier._results}


def test_the_shape_cloudflared_actually_writes_is_accepted(
    verifier: ModuleType, tmp_path: Path
) -> None:
    """The regression: `Endpoint` reddened a correct file on its first real run."""
    results = _run(verifier, tmp_path, _REAL_SHAPE)
    failed = [label for label, ok in results.items() if not ok]
    assert not failed, (
        f"a credentials file as cloudflared 2025.8.1 writes it fails on {failed}. "
        "The tool must accept what the tool it verifies produces"
    )


def test_against_the_committed_config_only_the_name_check_fails(
    verifier: ModuleType, tmp_path: Path
) -> None:
    """Pins the ONE expected FAIL, so any other one is visibly new.

    `config.yml` names the tunnel instead of giving its UUID (runbook §2.3, kept
    deliberately so the deploy host never needs the account-wide cert), and a name
    cannot be matched to a UUID offline. Without this test the operator guidance
    "one FAIL is expected" would drift the moment a second one appeared.
    """
    results = _run(verifier, tmp_path, _REAL_SHAPE, with_config=True)
    failed = {label for label, ok in results.items() if not ok}
    assert failed == {_NAME_VS_UUID}, f"expected exactly the name-vs-UUID FAIL, got {failed}"


def test_an_unknown_key_is_still_rejected(verifier: ModuleType, tmp_path: Path) -> None:
    """Widening the allowlist must not disarm it.

    Adding `Endpoint` could just as easily have been "stop checking unexpected
    keys", and the check that catches a hand-edited file or a pasted TUNNEL_TOKEN
    would be gone with nothing reporting its absence.
    """
    results = _run(verifier, tmp_path, {**_REAL_SHAPE, "TotallyMadeUpKey": "x"})
    assert results["no unexpected keys"] is False


def test_a_missing_secret_is_reported(verifier: ModuleType, tmp_path: Path) -> None:
    """A truncated copy is the realistic transfer failure."""
    truncated = {k: v for k, v in _REAL_SHAPE.items() if k != "TunnelSecret"}
    results = _run(verifier, tmp_path, truncated)
    assert results["required keys present"] is False


def test_a_tunnel_token_blob_is_rejected(verifier: ModuleType, tmp_path: Path) -> None:
    """The mistake the tool exists to catch: the wrong KIND of credential.

    A `TUNNEL_TOKEN` is a bare base64 string, and it is what an operator reaches
    for when a page says "the tunnel credentials". Accepting it would move the
    ingress map into the Cloudflare dashboard, where no test in this repo can see
    it and every AC-6(a) assertion would keep passing regardless.
    """
    results = _run(verifier, tmp_path, "eyJhIjoiMDEyMyIsInQiOiIxMTExIn0=" + "a" * 140)
    assert results["valid JSON"] is False


@pytest.mark.parametrize(
    "field,bad_value,expected_fail",
    [
        ("AccountTag", "0" * 31, "AccountTag shape"),
        ("AccountTag", "z" * 32, "AccountTag shape"),
        ("TunnelID", "not-a-uuid", "TunnelID shape"),
        ("TunnelSecret", "not!base64!", "TunnelSecret shape"),
        ("TunnelSecret", base64.b64encode(bytes(16)).decode(), "TunnelSecret shape"),
    ],
)
def test_each_field_shape_discriminates(
    verifier: ModuleType, tmp_path: Path, field: str, bad_value: str, expected_fail: str
) -> None:
    """Every shape check must reject as well as accept, or it asserts nothing.

    The last row is the one worth having: 16 decoded bytes is valid base64 and
    the wrong length, so a check that only asked "does it decode" would pass it.
    """
    results = _run(verifier, tmp_path, {**_REAL_SHAPE, field: bad_value})
    assert results[expected_fail] is False


@pytest.mark.skipif(os.name != "posix", reason="the script skips the mode check off posix")
def test_a_world_readable_file_is_reported(verifier: ModuleType, tmp_path: Path) -> None:
    """Measured on the deploy host: a copied file inherits a far wider ACL."""
    results = _run(verifier, tmp_path, _REAL_SHAPE, mode=0o644)
    assert results["permissions <= 0600"] is False


def test_a_credentials_file_inside_a_worktree_is_refused(
    verifier: ModuleType, tmp_path: Path
) -> None:
    """One `git add -A` from a public commit is the whole reason for this check."""
    results = _run(verifier, tmp_path, _REAL_SHAPE, in_repo=True)
    assert results["outside any git repo"] is False


def test_the_runbook_still_points_at_this_script() -> None:
    """A tool nobody is told to run is a tool nobody runs."""
    runbook = _RUNBOOK.read_text(encoding="utf-8")
    assert _SCRIPT.as_posix() in runbook, (
        f"{_SCRIPT} is no longer referenced by {_RUNBOOK} — either the runbook lost the "
        "step or the script moved"
    )
