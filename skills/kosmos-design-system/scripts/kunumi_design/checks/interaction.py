#!/usr/bin/env python3
"""Interaction checks: focus indication and published-page metadata."""

from __future__ import annotations

import re
from collections.abc import Iterable

from .. import scan
from ..findings import Finding
from ..rules import Rule
from . import Context, register

INTERACTIVE_TAGS = ("button", "select", "textarea", "summary")
OUTLINE_PROPERTIES = ("outline", "outline-style", "outline-width")
INDICATOR_PROPERTIES = ("outline", "outline-style", "outline-width", "outline-color", "box-shadow",
                        "border", "border-color", "border-bottom", "border-bottom-color",
                        "text-decoration", "text-decoration-line", "background", "background-color")
_REMOVED_RE = re.compile(r"^(?:none|0(?:px|rem|em)?)(?:\s|$)", re.IGNORECASE)


def split_selector_list(selector: str) -> list[str]:
    """Split a selector list on its top-level commas.

    Commas inside `:is()`, `:where()` or `:not()` belong to the inner list and must not split
    the outer one.

    Args:
        selector: A selector list, such as `a:focus, button:is(.x, .y):focus`.

    Returns:
        The individual complex selectors, stripped.
    """
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for char in selector:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    parts.append("".join(current).strip())
    return [part for part in parts if part]


def _is_focus_selector(selector: str) -> bool:
    """Whether a single selector styles an element while it has keyboard or pointer focus.

    `:focus-within` styles an ancestor and `:not(:focus-visible)` is the documented way to drop
    the ring for pointer focus only, so neither counts as removing a focus indicator.
    """
    lowered = selector.lower()
    if ":not(:focus-visible)" in lowered:
        return False
    return bool(re.search(r":focus(?:-visible)?(?![\w-])", lowered))


def _removes(declaration: scan.Declaration) -> bool:
    """Whether a declaration turns the outline off."""
    return declaration.prop in OUTLINE_PROPERTIES and bool(_REMOVED_RE.match(declaration.value))


def _interactive_nodes(context: Context) -> list[scan.Node]:
    """Every non-exempt element a keyboard user can reach."""
    document = context.target.document
    if document is None:
        return []
    found: list[scan.Node] = []
    for node in document.nodes:
        if document.is_exempt_node(node):
            continue
        attrs = node.attrs
        reachable = (
            node.tag in INTERACTIVE_TAGS
            or (node.tag == "a" and "href" in attrs)
            or (node.tag == "input" and attrs.get("type", "").lower() != "hidden")
        )
        tabindex = attrs.get("tabindex")
        if tabindex is not None:
            try:
                reachable = reachable or int(tabindex) >= 0
            except ValueError:
                pass
        if reachable:
            found.append(node)
    return found


@register("focus_visible_present")
def focus_visible_present(rule: Rule, context: Context) -> Iterable[Finding]:
    """Require a focus style in any artifact with keyboard-reachable elements.

    Linking `kunumi-tokens.css` satisfies the rule, because the token sheet carries the ring for
    every interactive element. Browsers do draw a default ring, which is why this is an advisory:
    the page is usable, it just does not show the Kunumi ring.
    """
    nodes = _interactive_nodes(context)
    if not nodes:
        return

    for declaration in context.target.cascade:
        if any(":focus" in part.lower() and ":focus-within" not in part.lower()
               for part in split_selector_list(declaration.selector)):
            return

    document = context.target.document
    if document is not None and any("kunumi-tokens.css" in href for href in document.stylesheet_hrefs):
        return

    first = nodes[0]
    yield context.finding(
        rule,
        None,
        locus=context.target.path.name,
        line=first.line,
        observed=f"{len(nodes)} interactive elements, no :focus-visible style",
        expected="the Kunumi focus ring, from kunumi-tokens.css or an equivalent :focus-visible rule",
    )


@register("focus_indicator_removed")
def focus_indicator_removed(rule: Rule, context: Context) -> Iterable[Finding]:
    """Flag an outline removed on focus with nothing drawn in its place.

    A replacement counts when the artifact itself sets a visible indicator - a non-removed
    outline, a box-shadow, a border or a background - on the same selector, or on any
    `:focus-visible` selector. The token sheet's own ring does not count: it is written inside
    `:where()`, so its specificity is zero and the artifact's `:focus` rule beats it.
    """
    owned = [
        declaration
        for declaration in context.target.declarations
        if context.owns(declaration) and not context.is_exempt(declaration)
    ]

    replacing_selectors: set[str] = set()
    has_visible_rule = False
    for declaration in owned:
        if declaration.prop not in INDICATOR_PROPERTIES or _removes(declaration):
            continue
        if declaration.value.strip().lower() in ("none", "transparent", "0"):
            continue
        for part in split_selector_list(declaration.selector):
            replacing_selectors.add(part)
            if ":focus-visible" in part.lower() and ":not(:focus-visible)" not in part.lower():
                has_visible_rule = True

    for declaration in owned:
        if not _removes(declaration):
            continue
        for part in split_selector_list(declaration.selector):
            if not _is_focus_selector(part):
                continue
            if part in replacing_selectors or has_visible_rule:
                continue
            yield context.finding(
                rule,
                declaration,
                locus=part,
                observed=f"{part} {{ {declaration.prop}: {declaration.value} }}",
                expected="a replacement indicator, or :focus:not(:focus-visible) to drop the ring for pointer focus only",
            )
            break


@register("social_meta_present")
def social_meta_present(rule: Rule, context: Context) -> Iterable[Finding]:
    """Require the sharing metadata a published page needs.

    Opt-in through the `web.published` scope: a mock-up or a slide replica has no business
    carrying Open Graph tags. When the page declares its image size, the size must be the one
    in `tokens.json#digital.og`.
    """
    document = context.target.document
    if document is None:
        return

    properties: dict[str, str] = {}
    has_icon = False
    for node in document.nodes:
        if node.tag == "meta":
            key = (node.attrs.get("property") or node.attrs.get("name") or "").lower()
            if key:
                properties[key] = node.attrs.get("content", "")
        elif node.tag == "link" and "icon" in node.attrs.get("rel", "").lower().split():
            has_icon = True

    missing = [key for key in ("og:title", "og:image") if not properties.get(key)]
    if not has_icon:
        missing.append('<link rel="icon">')
    if missing:
        yield context.finding(
            rule,
            None,
            locus=context.target.path.name,
            observed="missing " + ", ".join(missing),
            expected="og:title, og:image and a rel=icon link",
        )

    width, height = context.registry.interaction.og_size_px
    declared = (properties.get("og:image:width"), properties.get("og:image:height"))
    if all(declared) and (declared[0], declared[1]) != (str(width), str(height)):
        yield context.finding(
            rule,
            None,
            locus=context.target.path.name,
            observed=f"og:image declared {declared[0]}x{declared[1]}",
            expected=f"{width}x{height}",
            message="The Open Graph image is not the size tokens.json#digital.og specifies.",
        )
