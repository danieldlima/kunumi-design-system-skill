#!/usr/bin/env python3
"""Extract checkable structure from CSS and HTML using only the standard library.

Deliberately not a cascade resolver. Static scanning answers "is this declaration written
anywhere" and "does this element carry this attribute"; anything that needs computed style or
measured geometry belongs in `render`, not here. Keeping that line sharp is what stops the static
pass from making confident claims it cannot support.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path


# ---------------------------------------------------------------------------- CSS

@dataclass(frozen=True, slots=True)
class Declaration:
    """One `property: value` pair, with the context needed to judge it.

    Attributes:
        prop: Lowercased property name.
        value: Raw value text, whitespace-collapsed.
        selector: The nearest selector text, or the at-rule header inside keyframes.
        at_rules: Enclosing at-rule headers, outermost first. A declaration inside
            `@media (prefers-reduced-motion: reduce)` must not be read as a base rule.
        line: 1-based line of the declaration.
        path: File the declaration came from.
    """

    prop: str
    value: str
    selector: str
    at_rules: tuple[str, ...]
    line: int
    path: str

    @property
    def in_reduced_motion(self) -> bool:
        """Whether this declaration only applies under reduced-motion."""
        return any("prefers-reduced-motion" in rule for rule in self.at_rules)

    @property
    def in_keyframes(self) -> bool:
        """Whether this declaration sits inside an `@keyframes` block."""
        return any(rule.startswith("@keyframes") for rule in self.at_rules)


def strip_comments(text: str) -> str:
    """Remove CSS comments while preserving line numbers.

    Args:
        text: CSS source.

    Returns:
        The source with every comment replaced by an equal count of newlines, so later line
        arithmetic stays correct.
    """
    def _blank(match: re.Match[str]) -> str:
        return "\n" * match.group(0).count("\n")

    return re.sub(r"/\*.*?\*/", _blank, text, flags=re.DOTALL)


def parse_css(text: str, path: str, *, line_offset: int = 0) -> tuple[Declaration, ...]:
    """Walk CSS and collect declarations with their selector and at-rule context.

    Args:
        text: CSS source.
        path: Path recorded on each declaration.
        line_offset: Lines to add, for CSS lifted out of an HTML `<style>` block.

    Returns:
        Every declaration found, in source order.
    """
    source = strip_comments(text)
    declarations: list[Declaration] = []
    stack: list[str] = []
    buffer: list[str] = []
    line = 1 + line_offset
    buffer_line = line

    def header() -> str:
        return " ".join("".join(buffer).split())

    def collapse(raw: str) -> str:
        return " ".join(raw.split())

    index = 0
    length = len(source)
    while index < length:
        char = source[index]

        if char == "\n":
            line += 1
            buffer.append("\n")
            index += 1
            continue

        if char in "\"'":
            quote = char
            buffer.append(char)
            index += 1
            while index < length:
                buffer.append(source[index])
                if source[index] == "\n":
                    line += 1
                if source[index] == quote and source[index - 1] != "\\":
                    index += 1
                    break
                index += 1
            continue

        if char == "{":
            stack.append(header())
            buffer = []
            buffer_line = line
            index += 1
            continue

        if char == "}":
            _flush_declaration(declarations, buffer, stack, buffer_line, path, collapse)
            if stack:
                stack.pop()
            buffer = []
            buffer_line = line
            index += 1
            continue

        if char == ";":
            _flush_declaration(declarations, buffer, stack, buffer_line, path, collapse)
            buffer = []
            buffer_line = line
            index += 1
            continue

        if not buffer or not buffer[-1].strip():
            if not "".join(buffer).strip():
                buffer_line = line
        buffer.append(char)
        index += 1

    return tuple(declarations)


def _flush_declaration(
    sink: list[Declaration],
    buffer: list[str],
    stack: list[str],
    line: int,
    path: str,
    collapse,
) -> None:
    """Turn a buffered `prop: value` fragment into a Declaration, if it is one."""
    raw = "".join(buffer).strip()
    if not raw or ":" not in raw or not stack:
        return
    prop, _, value = raw.partition(":")
    prop = collapse(prop).lower()
    value = collapse(value)
    if not prop or not value or " " in prop or prop.startswith("@"):
        return

    at_rules = tuple(item for item in stack if item.startswith("@"))
    selector = next((item for item in reversed(stack) if not item.startswith("@")), stack[-1])
    sink.append(
        Declaration(
            prop=prop,
            value=value,
            selector=selector,
            at_rules=at_rules,
            line=line,
            path=path,
        )
    )


# ---------------------------------------------------------------------------- colors

_HEX_RE = re.compile(r"#([0-9a-fA-F]{3,8})\b")
_FUNC_RE = re.compile(r"\brgba?\(([^()]*)\)", re.IGNORECASE)
_VAR_RE = re.compile(r"var\(\s*(--[a-zA-Z0-9_-]+)")
_COLOR_MIX_RE = re.compile(r"color-mix\(\s*in\s+[a-z-]+\s*,(.*)\)", re.IGNORECASE | re.DOTALL)


def normalize_hex(raw: str) -> str | None:
    """Normalize a hex color literal to uppercase `#RRGGBB`, discarding alpha.

    Args:
        raw: Hex digits, with or without a leading `#`.

    Returns:
        The normalized color, or None when the literal is not a valid length.
    """
    digits = raw.lstrip("#")
    if len(digits) in (3, 4):
        digits = "".join(char * 2 for char in digits[:3])
    elif len(digits) in (6, 8):
        digits = digits[:6]
    else:
        return None
    return f"#{digits.upper()}"


def normalize_color(value: str) -> str | None:
    """Normalize a single color expression to `#RRGGBB`.

    Handles the forms the repository's own CSS actually uses, including space-separated
    `rgb(28 33 39 / 0.42)`. Without this, every alpha usage in `kunumi-tokens.css` reads as an
    unapproved color.

    Args:
        value: A color expression.

    Returns:
        The normalized color, or None when the value is not a resolvable literal.
    """
    value = value.strip()
    hex_match = _HEX_RE.fullmatch(value)
    if hex_match:
        return normalize_hex(hex_match.group(1))

    func_match = _FUNC_RE.fullmatch(value)
    if func_match:
        body = func_match.group(1).split("/")[0]
        parts = [part for part in re.split(r"[\s,]+", body.strip()) if part]
        if len(parts) < 3:
            return None
        channels: list[int] = []
        for part in parts[:3]:
            try:
                channels.append(
                    round(float(part.rstrip("%")) * 255 / 100)
                    if part.endswith("%")
                    else int(round(float(part)))
                )
            except ValueError:
                return None
        return "#" + "".join(f"{max(0, min(255, channel)):02X}" for channel in channels)

    return None


def find_colors(value: str) -> tuple[str, ...]:
    """Collect every resolvable color literal in a value, including inside gradients.

    Args:
        value: A declaration value.

    Returns:
        Normalized `#RRGGBB` colors, in source order, without deduplication.
    """
    found: list[str] = []
    for match in _HEX_RE.finditer(value):
        normalized = normalize_hex(match.group(1))
        if normalized:
            found.append(normalized)
    for match in _FUNC_RE.finditer(value):
        normalized = normalize_color(match.group(0))
        if normalized:
            found.append(normalized)
    return tuple(found)


def find_vars(value: str) -> tuple[str, ...]:
    """Collect every custom property referenced by a value.

    Args:
        value: A declaration value.

    Returns:
        Custom property names, in source order.
    """
    return tuple(match.group(1) for match in _VAR_RE.finditer(value))


def color_mix_bases(value: str) -> tuple[str, ...]:
    """Extract the token references a `color-mix()` is built from.

    `color-mix(in srgb, var(--kunumi-gelo) 72%, transparent)` is Gelo, not a new color. Resolving
    the base keeps token-derived translucency from reading as an invented value.

    Args:
        value: A declaration value.

    Returns:
        The custom property names inside any `color-mix()` call.
    """
    match = _COLOR_MIX_RE.search(value)
    if not match:
        return ()
    return tuple(name for name in find_vars(match.group(1)))


# ---------------------------------------------------------------------------- HTML

@dataclass(frozen=True, slots=True)
class Node:
    """One HTML element, with enough ancestry to resolve subtree annotations.

    Attributes:
        tag: Lowercased tag name.
        attrs: Attribute mapping; valueless attributes map to an empty string.
        line: 1-based line of the start tag.
        parent: Index of the parent node in the document's node list, or None at the root.
        index: This node's own index in the document's node list.
    """

    tag: str
    attrs: dict[str, str]
    line: int
    parent: int | None
    index: int


@dataclass(frozen=True, slots=True)
class TextRun:
    """A run of visible text, tied to the element that contains it.

    Attributes:
        text: The text content, stripped.
        line: 1-based line where the run starts.
        parent: Index of the containing node, or None.
    """

    text: str
    line: int
    parent: int | None


@dataclass(slots=True)
class Document:
    """A parsed HTML artifact.

    Attributes:
        path: Path to the HTML file.
        nodes: Every element, in document order.
        texts: Every visible text run, excluding script and style contents.
        styles: CSS declarations lifted from inline `<style>` blocks.
        stylesheet_hrefs: `href` values of every `<link rel=stylesheet>`.
    """

    path: str
    nodes: list[Node] = field(default_factory=list)
    texts: list[TextRun] = field(default_factory=list)
    styles: list[Declaration] = field(default_factory=list)
    stylesheet_hrefs: list[str] = field(default_factory=list)

    def ancestors(self, node: Node) -> tuple[Node, ...]:
        """Walk from a node's parent to the root.

        Args:
            node: The node to walk up from.

        Returns:
            Ancestors, nearest first.
        """
        chain: list[Node] = []
        current = node.parent
        while current is not None:
            parent = self.nodes[current]
            chain.append(parent)
            current = parent.parent
        return tuple(chain)

    def attr_in_scope(self, node: Node, name: str) -> str | None:
        """Find an attribute on a node or its nearest ancestor that carries it.

        This is what makes subtree annotation work: `data-kunumi-exempt` on a wrapper has to
        cover everything inside it, because `template-preview.html` mixes viewer chrome and brand
        artifact in one file.

        Args:
            node: The node to resolve from.
            name: Attribute name.

        Returns:
            The nearest value, or None when neither the node nor any ancestor carries it.
        """
        if name in node.attrs:
            return node.attrs[name]
        for ancestor in self.ancestors(node):
            if name in ancestor.attrs:
                return ancestor.attrs[name]
        return None

    def is_exempt_node(self, node: Node) -> bool:
        """Whether a node sits in chrome rather than in brand artifact.

        Walks toward the root looking for `data-kunumi-exempt`, but stops at any
        `data-kunumi-frame`: a frame is by definition a deliverable brand surface, so it re-enters
        brand scope even when the viewer around it is exempt. Without that reset, marking a
        preview harness as chrome would silently exempt the artifact it exists to display.

        Args:
            node: The node to resolve from.

        Returns:
            True when the nearest annotation is an exemption.
        """
        if "data-kunumi-frame" in node.attrs:
            return False
        if "data-kunumi-exempt" in node.attrs:
            return True
        for ancestor in self.ancestors(node):
            if "data-kunumi-frame" in ancestor.attrs:
                return False
            if "data-kunumi-exempt" in ancestor.attrs:
                return True
        return False

    def nodes_with(self, name: str) -> tuple[Node, ...]:
        """Select every node carrying an attribute.

        Args:
            name: Attribute name.

        Returns:
            Matching nodes, in document order.
        """
        return tuple(node for node in self.nodes if name in node.attrs)


class _Collector(HTMLParser):
    """Build a Document, tracking parentage and line numbers."""

    _VOID = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }

    def __init__(self, document: Document) -> None:
        super().__init__(convert_charrefs=True)
        self.document = document
        self._open: list[int] = []
        self._style_buffer: list[tuple[str, int]] = []
        self._in_style = False
        self._in_script = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        node = Node(
            tag=tag,
            attrs={key.lower(): (value or "") for key, value in attrs},
            line=self.getpos()[0],
            parent=self._open[-1] if self._open else None,
            index=len(self.document.nodes),
        )
        self.document.nodes.append(node)

        if tag == "link":
            rel = node.attrs.get("rel", "").lower()
            href = node.attrs.get("href")
            if "stylesheet" in rel and href:
                self.document.stylesheet_hrefs.append(href)

        if tag == "style":
            self._in_style = True
        elif tag == "script":
            self._in_script = True

        if tag not in self._VOID:
            self._open.append(node.index)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() not in self._VOID and self._open:
            self._open.pop()

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "style":
            self._in_style = False
        elif tag == "script":
            self._in_script = False
        if self._open:
            self._open.pop()

    def handle_data(self, data: str) -> None:
        if self._in_style:
            self._style_buffer.append((data, self.getpos()[0]))
            return
        if self._in_script or not data.strip():
            return
        self.document.texts.append(
            TextRun(
                text=data.strip(),
                line=self.getpos()[0],
                parent=self._open[-1] if self._open else None,
            )
        )

    def finish(self) -> None:
        """Parse buffered `<style>` contents once the document is complete."""
        for block, start_line in self._style_buffer:
            self.document.styles.extend(parse_css(block, self.document.path, line_offset=start_line - 1))


def parse_html(text: str, path: str) -> Document:
    """Parse an HTML artifact into nodes, text runs, and inline CSS.

    Args:
        text: HTML source.
        path: Path recorded on the document and its declarations.

    Returns:
        The parsed document.
    """
    document = Document(path=path)
    collector = _Collector(document)
    collector.feed(text)
    collector.close()
    collector.finish()
    return document


def read_text(path: Path) -> str:
    """Read a file as UTF-8, tolerating undecodable bytes.

    Args:
        path: File to read.

    Returns:
        The file's text, with undecodable bytes replaced rather than raising — a mislabelled
        binary must still reach the checks that detect exactly that.
    """
    return path.read_text(encoding="utf-8", errors="replace")
