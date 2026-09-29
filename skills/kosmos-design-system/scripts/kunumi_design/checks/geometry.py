#!/usr/bin/env python3
"""Geometry checks against the radius set and the product spacing scale."""

from __future__ import annotations

import re
from collections.abc import Iterable

from .. import scan
from ..findings import Finding
from ..rules import Rule
from . import Context, register, to_px

_LENGTH_RE = re.compile(r"-?\d*\.?\d+(?:px|rem|em)\b|\b0\b")


@register("radius_allowed")
def radius_allowed(rule: Rule, context: Context) -> Iterable[Finding]:
    """Flag a border radius outside the sanctioned card and control values."""
    allowed = context.registry.geometry.radii_px

    for declaration in context.target.declarations:
        if "border-radius" not in declaration.prop or context.is_exempt(declaration):
            continue
        for token in _LENGTH_RE.findall(declaration.value):
            magnitude = to_px(token)
            if magnitude is None or magnitude == 0:
                continue
            if magnitude not in allowed:
                yield context.finding(
                    rule, declaration,
                    observed=f"{declaration.prop}: {token} ({magnitude:g}px)",
                    expected=" or ".join(f"{value:g}px" for value in sorted(allowed)),
                )
                break


@register("spacing_scale")
def spacing_scale(rule: Rule, context: Context) -> Iterable[Finding]:
    """Report spacing values off the 4px product scale, aggregated into one finding.

    Deliberately one finding per artifact rather than one per declaration. A page with sixteen
    off-scale rem values is one decision about spacing discipline, not sixteen defects, and
    sixteen advisories is how a reader learns to skip the advisory tier entirely. The aggregate
    keeps the signal and drops the noise.

    Brandbook geometry values are exempt, because `geometry.cardPaddingNote` states that the 30px
    card padding deliberately sits off the scale. Flagging it would put the linter in conflict
    with the brandbook it enforces.
    """
    geometry = context.registry.geometry
    allowed = geometry.spacing_px | geometry.brandbook_px
    properties = tuple(rule.params.get("properties", ()))

    offenders: list[tuple[scan.Declaration, str, float]] = []
    for declaration in context.target.declarations:
        if declaration.prop not in properties or context.is_exempt(declaration):
            continue
        if declaration.prop.startswith("--"):
            continue
        for token in _LENGTH_RE.findall(declaration.value):
            magnitude = to_px(token)
            if magnitude is None or magnitude in allowed:
                continue
            offenders.append((declaration, token, magnitude))
            break

    if not offenders:
        return

    first, _, _ = offenders[0]
    sample = ", ".join(
        f"{declaration.selector} {declaration.prop}: {token}"
        for declaration, token, _ in offenders[:3]
    )
    more = f" and {len(offenders) - 3} more" if len(offenders) > 3 else ""
    yield context.finding(
        rule,
        first,
        locus=f"{len(offenders)} declarations",
        observed=f"{sample}{more}",
        expected="every spacing value on a --kunumi-space-* step",
    )
