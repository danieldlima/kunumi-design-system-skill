#!/usr/bin/env python3
"""Mark integrity checks, applied only to declarations targeting a brand mark."""

from __future__ import annotations

import re
from collections.abc import Iterable

from ..findings import Finding
from ..rules import Rule
from . import Context, register

_SCALE_RE = re.compile(r"\bscale\(\s*([^)]*)\)", re.IGNORECASE)
_SCALE_AXIS_RE = re.compile(r"\bscale([XY])\(\s*([^)]*)\)", re.IGNORECASE)


@register("declaration_forbidden_on_role")
def declaration_forbidden_on_role(rule: Rule, context: Context) -> Iterable[Finding]:
    """Flag effects and recoloring applied to a mark.

    The brandbook's fourth prohibition forbids effects and other colors on the mark. A CSS
    `filter` that inverts a mark is exactly that: the correct fix is always to reach for the
    approved positive or negative file instead.
    """
    if rule.params.get("role") != "logo":
        return
    properties = tuple(rule.params.get("properties", ()))
    functions = tuple(str(name).lower() for name in rule.params.get("functions", ()))

    for declaration in context.target.declarations:
        if context.is_exempt(declaration) or not context.is_logo(declaration):
            continue
        if declaration.prop in properties:
            yield context.finding(
                rule, declaration,
                observed=f"{declaration.prop}: {declaration.value}",
                expected="no effect on the mark",
            )
            continue
        value = declaration.value.lower()
        for name in functions:
            if f"{name}(" in value:
                yield context.finding(
                    rule, declaration,
                    observed=f"{declaration.prop}: {declaration.value}",
                    expected="the approved positive or negative mark file",
                )
                break


@register("non_uniform_scale")
def non_uniform_scale(rule: Rule, context: Context) -> Iterable[Finding]:
    """Flag a transform that alters the mark's proportions.

    A uniform `scale(1.05)` is untouched; only genuinely anisotropic scaling is a distortion.
    """
    if rule.params.get("role") != "logo":
        return

    for declaration in context.target.declarations:
        if context.is_exempt(declaration) or not context.is_logo(declaration):
            continue
        if "transform" not in declaration.prop:
            continue

        axes = {axis.upper(): value for axis, value in _SCALE_AXIS_RE.findall(declaration.value)}
        if len(axes) == 1:
            yield context.finding(
                rule, declaration,
                observed=f"{declaration.prop}: {declaration.value}",
                expected="uniform scaling",
            )
            continue

        for raw in _SCALE_RE.findall(declaration.value):
            parts = [part.strip() for part in raw.split(",") if part.strip()]
            if len(parts) >= 2 and len(set(parts[:2])) > 1:
                yield context.finding(
                    rule, declaration,
                    observed=f"{declaration.prop}: scale({raw})",
                    expected="uniform scaling",
                )
                break


@register("logo_min_height")
def logo_min_height(rule: Rule, context: Context) -> Iterable[Finding]:
    """Flag a mark rendered below its digital minimum height.

    Requires measured geometry: `clamp()` sizing makes the rendered height of a lockup
    statically unknowable, so this rule declares `requires: ["render"]` and stays in
    `rulesSkipped` until the render pass supplies bounding boxes.

    Only visible marks are judged, and that is a general guard rather than an accommodation for
    any one artifact: a mark measuring zero because its container is not on screen is not an
    undersized mark. It used to be justified by `template-preview.html`, which kept three
    off-screen slides mounted; that file is now a contact sheet with every frame visible
    (ADR 0016), so nothing in this repository depends on the guard any more. It stays because the
    next artifact might.

    The minimum is derived from `tokens.json#logo.minHeight.positiveRgbPx`, not declared as a
    rule param, so the brandbook value lives in one place.
    """
    minimum = context.registry.interaction.logo_min_px

    for item in context.measurements:
        if item.exempt or not item.visible:
            continue
        is_mark = item.role == "logo" or (
            item.source_name and item.source_name in context.mark_names
        )
        if not is_mark or item.height <= 0:
            continue
        if item.height < minimum:
            locus = item.source_name or item.element_id or ".".join(item.classes) or item.tag
            yield context.finding(
                rule,
                None,
                locus=locus,
                observed=f"{item.height:.1f}px of rendered lockup height",
                expected=f">= {minimum:g}px",
            )
