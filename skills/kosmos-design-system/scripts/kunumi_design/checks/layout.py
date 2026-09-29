#!/usr/bin/env python3
"""Responsive layout checks against the breakpoints in `tokens.json#layout`."""

from __future__ import annotations

import re
from collections.abc import Iterable

from .. import scan
from ..findings import Finding
from ..rules import Rule
from . import Context, register

_FEATURE_RE = re.compile(r"\(\s*(min|max)-width\s*:\s*(\d*\.?\d+)(px|r?em)\s*\)", re.IGNORECASE)
_RANGE_RE = re.compile(r"\bwidth\s*(>=|<=|>|<)\s*(\d*\.?\d+)(px|r?em)", re.IGNORECASE)


def _width_conditions(header: str) -> list[tuple[str, float]]:
    """Read the width conditions of one `@media` header as (bound, px) pairs.

    Both the classic `(min-width: 768px)` form and the range form `(width >= 768px)` are read.
    `em` and `rem` in a media query are relative to the initial font size, 16px, whatever the
    page sets, so they convert exactly.

    Args:
        header: The at-rule header, such as `@media (min-width: 768px)`.

    Returns:
        `("min", px)` or `("max", px)` for every width condition in the header.
    """
    conditions: list[tuple[str, float]] = []
    for bound, raw, unit in _FEATURE_RE.findall(header):
        px = float(raw) * (1 if unit.lower() == "px" else 16)
        conditions.append((bound.lower(), px))
    for operator, raw, unit in _RANGE_RE.findall(header):
        px = float(raw) * (1 if unit.lower() == "px" else 16)
        conditions.append(("min" if operator.startswith(">") else "max", px))
    return conditions


@register("breakpoint_scale")
def breakpoint_scale(rule: Rule, context: Context) -> Iterable[Finding]:
    """Report media-query widths off the sanctioned breakpoints, aggregated into one finding.

    A `min-width` must equal a breakpoint. A `max-width` may equal one, or sit up to the token
    tolerance below it (767px, 767.98px), which is how a max query meets the matching min query
    without overlap. One finding per artifact, like `spacing_scale`: a page with six invented
    breakpoints has made one decision about its layout, not six defects.
    """
    layout = context.registry.layout
    breakpoints = layout.breakpoints_px
    if not breakpoints:
        return
    tolerance = layout.max_width_tolerance_px

    def allowed(bound: str, px: float) -> bool:
        if px in breakpoints:
            return True
        return bound == "max" and any(0 < bp - px <= tolerance for bp in breakpoints)

    offenders: list[tuple[scan.Declaration, str]] = []
    seen: set[str] = set()
    for declaration in context.target.declarations:
        if not context.owns(declaration) or context.is_exempt(declaration):
            continue
        for header in declaration.at_rules:
            if not header.lower().startswith("@media") or header in seen:
                continue
            conditions = _width_conditions(header)
            if any(not allowed(bound, px) for bound, px in conditions):
                seen.add(header)
                offenders.append((declaration, header))

    if not offenders:
        return

    first, _ = offenders[0]
    sample = ", ".join(header for _, header in offenders[:3])
    more = f" and {len(offenders) - 3} more" if len(offenders) > 3 else ""
    expected = " / ".join(f"{value:g}px" for value in sorted(breakpoints))
    yield context.finding(
        rule,
        first,
        locus=f"{len(offenders)} media queries",
        observed=f"{sample}{more}",
        expected=f"min-width at {expected}; max-width at a breakpoint or up to {tolerance:g}px below",
    )
