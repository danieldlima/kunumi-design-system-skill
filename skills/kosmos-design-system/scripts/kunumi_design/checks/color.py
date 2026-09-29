#!/usr/bin/env python3
"""Color checks, comparing against palettes derived from `tokens.json`."""

from __future__ import annotations

import re
from collections.abc import Iterable

from .. import scan
from ..findings import Finding
from ..rules import Rule
from . import Context, register

PAINT_PROPERTIES = (
    "color", "background", "background-color", "background-image", "border-color",
    "border-top-color", "border-right-color", "border-bottom-color", "border-left-color",
    "fill", "stroke", "outline-color", "box-shadow", "text-decoration-color",
)


def _colors_in(declaration: scan.Declaration) -> tuple[str, ...]:
    """Every resolvable color literal in a declaration's value."""
    return scan.find_colors(declaration.value)


@register("prohibited_color")
def prohibited_color(rule: Rule, context: Context) -> Iterable[Finding]:
    """Flag a prohibited pure black or white outside its one sanctioned custom property.

    The target hex and the property allowed to carry it both come from
    `tokens.json#color.prohibition`, so a third documented exception is a token edit.
    """
    target = str(rule.params["target"]).upper()
    sanctioned = context.registry.palette.prohibited.get(target)

    for declaration in context.target.declarations:
        if context.is_exempt(declaration) or target not in _colors_in(declaration):
            continue
        if sanctioned and (declaration.prop == sanctioned or sanctioned in declaration.value):
            continue
        yield context.finding(
            rule,
            declaration,
            observed=f"{declaration.prop}: {declaration.value}",
            expected=f"{target} only via {sanctioned}" if sanctioned else "not used",
        )


@register("forbidden_colors")
def forbidden_colors(rule: Rule, context: Context) -> Iterable[Finding]:
    """Flag colors from a retired palette named by `params.source`."""
    source = rule.params.get("source", "superseded")
    forbidden = getattr(context.registry.palette, source, frozenset())

    for declaration in context.target.declarations:
        if context.is_exempt(declaration):
            continue
        for color in _colors_in(declaration):
            if color in forbidden:
                yield context.finding(
                    rule, declaration, observed=color, expected="a color.chart value"
                )


@register("chart_color_misuse")
def chart_color_misuse(rule: Rule, context: Context) -> Iterable[Finding]:
    """Flag the data-only chart palette used as a UI accent or a surface."""
    palette = context.registry.palette
    properties = tuple(rule.params.get("properties", PAINT_PROPERTIES))

    for declaration in context.target.declarations:
        if context.is_exempt(declaration) or declaration.prop not in properties:
            continue
        if declaration.prop in palette.chart_vars:
            continue
        hits = [color for color in _colors_in(declaration) if color in palette.chart]
        hits += [name for name in scan.find_vars(declaration.value) if name in palette.chart_vars]
        if hits:
            yield context.finding(
                rule,
                declaration,
                observed=f"{declaration.prop}: {hits[0]}",
                expected="--kunumi-accent, --kunumi-ground or --kunumi-ink",
            )


@register("unapproved_color")
def unapproved_color(rule: Rule, context: Context) -> Iterable[Finding]:
    """Flag a literal color that belongs to no approved Kunumi palette.

    Colors already covered by a more specific rule — the prohibition pair, the superseded chart
    palette, the asset-local near-Urucum values — are left to those rules, so one defect does not
    produce three findings.
    """
    palette = context.registry.palette
    covered = palette.approved | frozenset(palette.prohibited) | palette.superseded | palette.asset_local

    seen: set[tuple[str, int]] = set()
    for declaration in context.target.declarations:
        if context.is_exempt(declaration):
            continue
        for color in _colors_in(declaration):
            if color in covered or (color, declaration.line) in seen:
                continue
            seen.add((color, declaration.line))
            yield context.finding(
                rule,
                declaration,
                observed=f"{declaration.prop}: {color}",
                expected="an approved token from tokens.json#color",
            )


@register("prefer_semantic_token")
def prefer_semantic_token(rule: Rule, context: Context) -> Iterable[Finding]:
    """Flag an approved brand hex written as a literal where a semantic role token exists.

    Skips custom-property definitions: the token layer is exactly where the literal belongs.
    """
    palette = context.registry.palette

    for declaration in context.target.declarations:
        if context.is_exempt(declaration) or declaration.prop.startswith("--"):
            continue
        if declaration.prop not in PAINT_PROPERTIES:
            continue
        for color in _colors_in(declaration):
            canonical = palette.var_by_hex.get(color)
            if color in palette.institutional and canonical:
                yield context.finding(
                    rule,
                    declaration,
                    observed=f"{declaration.prop}: {color}",
                    expected=f"var({canonical}) or a semantic role token",
                )
                break
