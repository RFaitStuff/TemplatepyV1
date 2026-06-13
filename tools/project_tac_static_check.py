#!/usr/bin/env python3
"""Static sanity checks for Project Tac's Ren'Py automation layer.

This does not replace Ren'Py lint. It catches fast, repo-local mistakes that
are easy to introduce while editing registries and author-facing helpers.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"


IGNORE_DIRS = {"cache", "saves", "tl", "gui", "libs"}
OLD_CONTENT_PATTERNS = [
    "configure_location(",
    "register_interactable(",
    "available_if=(lambda",
]


def rpy_files():
    for path in GAME.rglob("*.rpy"):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        yield path


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def collect_labels(text: str):
    return re.findall(r"^\s*label\s+([A-Za-z_][\w]*)\s*(?:\([^)]*\))?\s*:", text, re.M)


def collect_string_label_refs(text: str):
    refs = []
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0]
        m = re.match(r"^\s*jump\s+(?!expression\b)([A-Za-z_][\w]*)\b", line)
        if m:
            refs.append(m.group(1))
        m = re.match(r"^\s*call\s+(?!screen\b|expression\b)([A-Za-z_][\w]*)\b", line)
        if m:
            refs.append(m.group(1))
        for pat in (
            r"Jump\(\s*[\"']([A-Za-z_][\w]*)[\"']",
            r"Call\(\s*[\"']([A-Za-z_][\w]*)[\"']",
            r"renpy\.call(?:_in_new_context)?\(\s*[\"']([A-Za-z_][\w]*)[\"']",
            r"renpy\.jump\(\s*[\"']([A-Za-z_][\w]*)[\"']",
        ):
            refs.extend(re.findall(pat, line))
    return refs


def iter_init_python_blocks(path: Path, lines: list[str]):
    in_block = False
    base_indent = 0
    block_lines: list[str] = []
    start_line = 0

    for index, line in enumerate(lines, 1):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if not in_block:
            if re.match(r"^\s*init(?:\s+[-\w]+)?\s+python\s*:", line):
                in_block = True
                base_indent = indent
                block_lines = []
                start_line = index + 1
            continue

        if stripped.strip() and indent <= base_indent:
            yield start_line, block_lines
            in_block = False
            if re.match(r"^\s*init(?:\s+[-\w]+)?\s+python\s*:", line):
                in_block = True
                base_indent = indent
                block_lines = []
                start_line = index + 1
            continue

        block_lines.append(line)

    if in_block:
        yield start_line, block_lines


def dedent_block(block_lines: list[str]) -> str:
    nonempty = [line for line in block_lines if line.strip()]
    if not nonempty:
        return ""
    min_indent = min(len(line) - len(line.lstrip()) for line in nonempty)
    return "".join(line[min_indent:] if len(line) >= min_indent else line for line in block_lines)


def check_init_python_parse(path: Path, text: str, issues: list[str]):
    lines = text.splitlines(True)
    for start, block in iter_init_python_blocks(path, lines):
        code = dedent_block(block)
        if not code.strip():
            continue
        try:
            ast.parse(code, filename=f"{rel(path)}:{start}")
        except SyntaxError as exc:
            issues.append(f"{rel(path)}:{start}: init python syntax error: {exc.msg}")


def check_old_patterns(path: Path, text: str, issues: list[str]):
    path_text = rel(path)
    if "/Game/Content/" not in path_text and "/Game/_Data/" not in path_text:
        return
    for pattern in OLD_CONTENT_PATTERNS:
        if pattern in text:
            issues.append(f"{path_text}: old authoring pattern remains: {pattern}")


def check_requirement_strings(path: Path, text: str, issues: list[str]):
    allowed_prefixes = {
        "flag", "no_flag", "unless", "blocked_by_flag", "item", "no_item",
        "tag", "quest_done", "quest_started", "quest_unlocked",
        "quest_step", "loc", "location", "area", "time", "weekday",
        "mood", "present", "system", "stat",
    }
    for match in re.finditer(r"req\((.*?)\)", text, re.S):
        snippet = match.group(1)
        for rule in re.findall(r"[\"']([^\"']+:[^\"']*)[\"']", snippet):
            prefix = rule.split(":", 1)[0]
            if "." in prefix:
                continue
            if prefix not in allowed_prefixes and not re.match(r"^[A-Za-z_]\w*$", prefix):
                line = text[: match.start()].count("\n") + 1
                issues.append(f"{rel(path)}:{line}: suspicious requirement prefix '{prefix}' in {rule!r}")


def main() -> int:
    issues: list[str] = []
    labels: dict[str, list[str]] = {}
    refs: list[tuple[str, str]] = []

    files = list(rpy_files())
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        check_init_python_parse(path, text, issues)
        check_old_patterns(path, text, issues)
        check_requirement_strings(path, text, issues)
        for label in collect_labels(text):
            labels.setdefault(label, []).append(rel(path))
        refs.extend((ref, rel(path)) for ref in collect_string_label_refs(text))

    for label, paths in sorted(labels.items()):
        if len(paths) > 1:
            issues.append(f"duplicate label '{label}' in: {', '.join(paths)}")

    known = set(labels)
    for ref, path in refs:
        if ref not in known and not ref.startswith("_call_"):
            issues.append(f"{path}: string label reference '{ref}' was not found")

    if issues:
        print("Project Tac static check found issues:\n")
        for issue in issues:
            print("- " + issue)
        return 1

    print(f"Project Tac static check passed ({len(files)} .rpy files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
