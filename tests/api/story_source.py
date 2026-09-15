"""Shared readers for the story-mode explainer's source guards (PLAN-0126).

The explainer lives in ``services/api/static/story/`` and, like the console, has no
build step and no JS test runner (``docs/conventions/ui.md`` §5), so every guard on it
is a Python test that reads the files as text. Three test modules need the same three
readings — the pinned data block, the page's references, and comment-free text — and a
reading done three different ways is how a guard ends up agreeing with a broken file.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tests.api.js_source import strip_js_comments

__all__ = [
    "AUTHORED_FILES",
    "BLOCK_BEGIN",
    "BLOCK_END",
    "REPO_ROOT",
    "STATIC_DIR",
    "STORY_DIR",
    "VENDORED_FILES",
    "authored_text",
    "extract_block",
    "external_references",
    "references",
]

REPO_ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = REPO_ROOT / "services" / "api" / "static"
STORY_DIR = STATIC_DIR / "story"

#: The files a person writes. The vendored library is excluded BY NAME, never by a
#: pattern, so a new authored file cannot fall out of the scan unnoticed.
AUTHORED_FILES = ("index.html", "story.css", "story-data.js", "story.js")
VENDORED_FILES = ("three.module.min.js", "THREE_LICENSE.txt")

BLOCK_BEGIN = "/* STORY_DATA_JSON_BEGIN */"
BLOCK_END = "/* STORY_DATA_JSON_END */"

_SCHEME = r"(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//)"
_REFERENCE_PATTERNS = {
    "html": re.compile(r"""\b(?:src|href)\s*=\s*["']([^"']+)["']"""),
    "js": re.compile(r"""\b(?:from|import)\s*\(?\s*["']([^"']+)["']"""),
    "css": re.compile(r"""(?:@import\s+|url\(\s*)["']?([^"')\s]+)["']?"""),
}


def extract_block(source: str) -> dict[str, Any]:
    """``json.loads`` the text between the delimiters — the same slice the browser runs."""
    start = source.index(BLOCK_BEGIN) + len(BLOCK_BEGIN)
    stop = source.index(BLOCK_END)
    block: dict[str, Any] = json.loads(source[start:stop])
    return block


def authored_text(name: str, source: str | None = None) -> str:
    """One authored file's text with its comments blanked (HTML, CSS or JS)."""
    text = source if source is not None else (STORY_DIR / name).read_text(encoding="utf-8")
    if name.endswith(".html"):
        return re.sub(r"<!--.*?-->", lambda m: " " * len(m.group(0)), text, flags=re.DOTALL)
    if name.endswith(".css"):
        return re.sub(r"/\*.*?\*/", lambda m: " " * len(m.group(0)), text, flags=re.DOTALL)
    return strip_js_comments(text)


def references(name: str, text: str) -> list[str]:
    """Every src/href (HTML), module specifier (JS) or url()/@import (CSS) in ``text``."""
    kind = "html" if name.endswith(".html") else "css" if name.endswith(".css") else "js"
    return _REFERENCE_PATTERNS[kind].findall(text)


def external_references(name: str, text: str) -> list[str]:
    """The references that leave the origin — a scheme (``https:``, ``data:``) or ``//``."""
    return [ref for ref in references(name, text) if re.match(_SCHEME, ref)]
