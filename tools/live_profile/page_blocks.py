"""Writing generated content into files without noise: change detection and marked Markdown blocks."""
from __future__ import annotations

import re
from pathlib import Path

STAMP = re.compile(r"updated \d{1,2} [A-Z][a-z]{2} \d{2}:\d{2} UTC")


def without_stamp(text: str) -> str:
    return STAMP.sub("", text)


def write_if_changed(path: Path, content: str) -> bool:
    """Write only when the content differs once the refresh timestamp is ignored."""
    if path.exists() and without_stamp(path.read_text(encoding="utf-8")) == without_stamp(content):
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def replace_block(path: Path, name: str, body: str) -> bool:
    """Replace the text between <!-- live:NAME:start --> and <!-- live:NAME:end --> in a Markdown file."""
    pattern = re.compile(rf"(<!-- live:{re.escape(name)}:start -->\n)(?:.*?\n)?(<!-- live:{re.escape(name)}:end -->)", re.S)
    text = path.read_text(encoding="utf-8")
    if not pattern.search(text):
        raise ValueError(f"markers live:{name} not found in {path}")
    updated = pattern.sub(lambda m: m.group(1) + body + "\n" + m.group(2), text)
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8")
    return True
