#!/usr/bin/env python3
"""Render a Claude Code session JSONL transcript to flat Markdown.

Purpose
-------
Claude Code persists every session (assistant text, extended thinking,
tool calls, tool results) as an append-only JSONL file under the host's
``~/.claude/projects/<encoded-project>/<session-id>.jsonl``. In the Code
tab UI the tool/process blocks are collapsed by default, which makes it
painful to hand a *complete* transcript to the Chat or Cowork tab for
follow-up analysis.

This tool reads that JSONL and renders a single flat Markdown document
containing the full conversation including the normally-collapsed
process steps, so it can be dropped into ``.claude/handoffs/`` and handed
to another tier without manual expand-and-drag.

It is intentionally dependency-free (stdlib only) so it runs from any
environment that can see the JSONL file (WSL reading the Windows host
``/mnt/c/...`` path, or a native CLI session).

Usage
-----
    # Most robust: explicit path to the .jsonl
    python tools/handoffs/render_transcript.py /path/to/<session-id>.jsonl \\
        --out .claude/handoffs/session-10/2026-05-16-1300-code-foo-transcript.md

    # Or: pick the most recently modified session in a project dir
    #   (project dir = ~/.claude/projects/<encoded-cwd>, encoded via
    #    encode_project_path; under WSL the host root is /mnt/c/...)
    python tools/handoffs/render_transcript.py \\
        --project-dir "$PROJECT_DIR" --latest --out transcript.md

    # Only the last 2 turns, no thinking:
    python tools/handoffs/render_transcript.py session.jsonl --last 2 --no-thinking
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Record-level ``type`` values that carry conversational content. Everything
# else (queue-operation, attachment, ai-title, last-prompt, ...) is metadata
# noise and is skipped.
RENDERABLE_RECORD_TYPES = frozenset({"user", "assistant", "system"})

_PERSISTED_RE = re.compile(r"Full output saved to:\s*(?P<path>.+?)\s*\n", re.IGNORECASE)


@dataclass(frozen=True)
class RenderOptions:
    """Filters controlling what ends up in the rendered Markdown."""

    include_thinking: bool = True
    include_tools: bool = True
    last_turns: int = 0  # 0 = all
    resolve_spill: bool = False
    max_block_chars: int = 0  # 0 = unlimited


def encode_project_path(path: str) -> str:
    """Encode a working-directory path the way Claude Code names its dir.

    Every non-alphanumeric character becomes a single ``-`` and the
    result is lower-cased. Example::

        \\\\wsl.localhost\\ubuntu-24.04\\home\\crayj\\work\\vero-lite
        -> --wsl-localhost-ubuntu-24-04-home-crayj-work-vero-lite
    """
    return re.sub(r"[^A-Za-z0-9]", "-", path).lower()


def iter_records(jsonl_path: Path) -> Iterator[dict[str, Any]]:
    """Yield each JSON object from the transcript, skipping blank/bad lines."""
    with jsonl_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                yield obj


def resolve_jsonl(
    session: str | None,
    project_dir: Path | None,
    *,
    latest: bool,
) -> Path:
    """Resolve the JSONL file from an explicit path, a session id, or --latest."""
    if session is not None:
        candidate = Path(session)
        if candidate.is_file():
            return candidate
        if project_dir is not None:
            by_id = project_dir / f"{session}.jsonl"
            if by_id.is_file():
                return by_id
        msg = f"could not resolve session {session!r} to a .jsonl file"
        raise FileNotFoundError(msg)

    if latest:
        if project_dir is None:
            msg = "--latest requires --project-dir"
            raise ValueError(msg)
        files = sorted(
            project_dir.glob("*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not files:
            msg = f"no .jsonl files under {project_dir}"
            raise FileNotFoundError(msg)
        return files[0]

    msg = "provide a session path/id, or --project-dir with --latest"
    raise ValueError(msg)


def _truncate(text: str, limit: int) -> str:
    if limit <= 0 or len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated {len(text) - limit} chars]"


def _maybe_resolve_spill(text: str, jsonl_path: Path) -> str:
    """Inline a ``<persisted-output>`` spill file when it can be located."""
    match = _PERSISTED_RE.search(text)
    if match is None:
        return text
    raw = match.group("path").strip()
    spill = _to_local_path(raw, jsonl_path)
    if spill is not None and spill.is_file():
        body = spill.read_text(encoding="utf-8", errors="replace")
        return f"{text}\n\n--- resolved spill ({spill}) ---\n{body}"
    return text


def _to_local_path(raw: str, jsonl_path: Path) -> Path | None:
    """Best-effort map a recorded (possibly Windows) path to a local one."""
    win = re.match(r"^([A-Za-z]):[\\/](.*)$", raw)
    if win is not None:
        drive = win.group(1).lower()
        rest = win.group(2).replace("\\", "/")
        mnt = Path(f"/mnt/{drive}/{rest}")
        if mnt.exists():
            return mnt
    direct = Path(raw.replace("\\", "/"))
    if direct.exists():
        return direct
    # Fall back to the spill living next to the transcript.
    sibling = jsonl_path.with_suffix("") / "tool-results" / Path(raw).name
    if sibling.exists():
        return sibling
    return None


def _stringify_tool_result_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text" and isinstance(item.get("text"), str):
                    parts.append(item["text"])
                else:
                    parts.append(f"[{item.get('type', 'block')}]")
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def _render_block(
    block: dict[str, Any],
    opts: RenderOptions,
    jsonl_path: Path,
) -> list[str]:
    btype = block.get("type")

    if btype == "text":
        text = block.get("text")
        return [_truncate(text, opts.max_block_chars)] if isinstance(text, str) else []

    if btype == "thinking":
        if not opts.include_thinking:
            return []
        thought = block.get("thinking")
        if not isinstance(thought, str) or not thought.strip():
            return []
        body = _truncate(thought, opts.max_block_chars)
        return ["> **[thinking]**", "", "```text", body, "```"]

    if btype == "tool_use":
        if not opts.include_tools:
            return []
        name = block.get("name", "?")
        payload = json.dumps(block.get("input", {}), indent=2, ensure_ascii=False)
        return [
            f"> **[tool_use]** `{name}`",
            "",
            "```json",
            _truncate(payload, opts.max_block_chars),
            "```",
        ]

    if btype == "tool_result":
        if not opts.include_tools:
            return []
        raw = _stringify_tool_result_content(block.get("content"))
        if opts.resolve_spill:
            raw = _maybe_resolve_spill(raw, jsonl_path)
        flag = " (error)" if block.get("is_error") else ""
        return [
            f"> **[tool_result{flag}]**",
            "",
            "```text",
            _truncate(raw, opts.max_block_chars),
            "```",
        ]

    return []


def _render_content(
    content: object,
    opts: RenderOptions,
    jsonl_path: Path,
) -> list[str]:
    if isinstance(content, str):
        return [_truncate(content, opts.max_block_chars)] if content.strip() else []
    if not isinstance(content, list):
        return []
    out: list[str] = []
    for block in content:
        if isinstance(block, dict):
            rendered = _render_block(block, opts, jsonl_path)
            if rendered:
                out.append("\n".join(rendered))
    return out


def _render_record(
    rec: dict[str, Any],
    opts: RenderOptions,
    jsonl_path: Path,
) -> str | None:
    if rec.get("type") not in RENDERABLE_RECORD_TYPES:
        return None
    message = rec.get("message")
    if not isinstance(message, dict):
        return None
    role = message.get("role", rec.get("type", "?"))
    body = _render_content(message.get("content"), opts, jsonl_path)
    if not body:
        return None

    ts = rec.get("timestamp", "")
    sidechain = " · sidechain" if rec.get("isSidechain") else ""
    branch = rec.get("gitBranch")
    branch_tag = f" · `{branch}`" if isinstance(branch, str) and branch else ""
    header = f"## {role} · {ts}{sidechain}{branch_tag}"
    return "\n\n".join([header, *body])


def render_transcript(
    jsonl_path: Path,
    opts: RenderOptions,
) -> str:
    """Render the whole transcript file to a Markdown string."""
    records = list(iter_records(jsonl_path))
    type_counts = Counter(r.get("type") for r in records)

    rendered: list[str] = []
    for rec in records:
        chunk = _render_record(rec, opts, jsonl_path)
        if chunk is not None:
            rendered.append(chunk)

    if opts.last_turns > 0:
        rendered = rendered[-opts.last_turns :]

    session_id = jsonl_path.stem
    generated = datetime.now(tz=UTC).isoformat()
    counts = ", ".join(f"{k}={v}" for k, v in sorted(type_counts.items()) if k)
    preamble = "\n".join(
        [
            f"# Transcript — session `{session_id}`",
            "",
            f"- Source: `{jsonl_path}`",
            f"- Generated (UTC): {generated}",
            f"- Records: {len(records)} ({counts})",
            f"- Rendered turns: {len(rendered)}",
            "- Filters: "
            + ", ".join(
                [
                    f"thinking={opts.include_thinking}",
                    f"tools={opts.include_tools}",
                    f"last={opts.last_turns or 'all'}",
                    f"resolve_spill={opts.resolve_spill}",
                ]
            ),
            "",
            "---",
        ]
    )
    return preamble + "\n\n" + "\n\n---\n\n".join(rendered) + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="render_transcript.py",
        description="Render a Claude Code session JSONL to flat Markdown.",
    )
    parser.add_argument(
        "session",
        nargs="?",
        help="Path to a .jsonl file, or a bare session id (needs --project-dir).",
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=None,
        help="Directory holding <session-id>.jsonl files.",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Pick the most recently modified .jsonl in --project-dir.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write Markdown here (default: stdout).",
    )
    parser.add_argument(
        "--last",
        type=int,
        default=0,
        metavar="N",
        help="Render only the last N turns (0 = all).",
    )
    parser.add_argument(
        "--no-thinking",
        action="store_true",
        help="Exclude extended-thinking blocks.",
    )
    parser.add_argument(
        "--no-tools",
        action="store_true",
        help="Exclude tool_use / tool_result blocks.",
    )
    parser.add_argument(
        "--resolve-spill",
        action="store_true",
        help="Inline <persisted-output> spill files when locatable.",
    )
    parser.add_argument(
        "--max-block-chars",
        type=int,
        default=0,
        metavar="N",
        help="Truncate any single rendered block to N chars (0 = unlimited).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    session: str | None = args.session
    project_dir: Path | None = args.project_dir
    out_path: Path | None = args.out

    try:
        jsonl_path = resolve_jsonl(session, project_dir, latest=bool(args.latest))
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    opts = RenderOptions(
        include_thinking=not bool(args.no_thinking),
        include_tools=not bool(args.no_tools),
        last_turns=int(args.last),
        resolve_spill=bool(args.resolve_spill),
        max_block_chars=int(args.max_block_chars),
    )

    markdown = render_transcript(jsonl_path, opts)

    if out_path is None:
        sys.stdout.write(markdown)
        print(
            f"\n[render_transcript] rendered from {jsonl_path} (stdout)",
            file=sys.stderr,
        )
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")
    # Always announce where the export landed (workflow requirement).
    print(f"[render_transcript] exported -> {out_path.resolve()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
