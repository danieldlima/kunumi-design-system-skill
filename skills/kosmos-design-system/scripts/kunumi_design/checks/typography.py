#!/usr/bin/env python3
"""Type checks, comparing against ranges and variables declared in `tokens.json`."""

from __future__ import annotations

from collections.abc import Iterable

from ..findings import Finding
from ..rules import Rule
from . import Context, classify_role, is_long_title, number, register, token_properties


def _display_tokens(context: Context) -> tuple[str, ...]:
    """Selector tokens that carry a display type role, across the resolved cascade.

    Long-title selectors are excluded. They are display by leading and by scale, but the
    long-title exception sets them in Figtree sentence case at tracking 0, so judging them for
    uppercase or +3% would report a violation against a rule the system itself prescribes.
    """
    index = token_properties(context.target.cascade)
    return tuple(
        token for token in index
        if classify_role(f".{token}") == "display" and not is_long_title(f".{token}")
    )


def _allowed_display_tracking(context: Context) -> frozenset[float]:
    """Tracking ratios the brandbook actually prints for display variables.

    Derived from `typography.variables`, which is why the +10% `Cabecalho/Menu` variable does not
    read as a violation of the +3% default.
    """
    typography = context.registry.typography
    ratios = {typography.display_tracking}
    for variable in typography.variables:
        if variable.get("family") in typography.display_families:
            ratios.add(variable["letterSpacingPercent"] / 100)
    return frozenset(ratios)


@register("display_case")
def display_case(rule: Rule, context: Context) -> Iterable[Finding]:
    """Require uppercase on every display-role selector."""
    index = token_properties(context.target.cascade)

    for token in _display_tokens(context):
        properties = index[token]
        declarations = properties.get("text-transform")
        first = next(iter(properties.values()))[0]
        if context.is_exempt(first) or not context.owns(first):
            continue
        if not declarations:
            yield context.finding(
                rule,
                first,
                locus=f".{token}",
                observed="no text-transform declared",
                expected="text-transform: uppercase",
            )
            continue
        if not any("uppercase" in item.value.lower() for item in declarations):
            offender = declarations[0]
            yield context.finding(
                rule, offender, locus=f".{token}",
                observed=f"text-transform: {offender.value}", expected="uppercase",
            )


@register("display_tracking")
def display_tracking(rule: Rule, context: Context) -> Iterable[Finding]:
    """Require the brandbook's positive tracking on display-role selectors."""
    index = token_properties(context.target.cascade)
    allowed = _allowed_display_tracking(context)
    tracking_vars = ("--kunumi-track-display", "--kunumi-track-menu")

    for token in _display_tokens(context):
        properties = index[token]
        declarations = properties.get("letter-spacing")
        first = next(iter(properties.values()))[0]
        if context.is_exempt(first) or not context.owns(first):
            continue
        if not declarations:
            yield context.finding(
                rule, first, locus=f".{token}",
                observed="no letter-spacing declared",
                expected="letter-spacing: var(--kunumi-track-display)",
            )
            continue
        for item in declarations:
            if any(name in item.value for name in tracking_vars):
                break
            magnitude = number(item.value)
            if magnitude is not None and any(abs(magnitude - ratio) < 0.0005 for ratio in allowed):
                break
        else:
            offender = declarations[0]
            yield context.finding(
                rule, offender, locus=f".{token}",
                observed=f"letter-spacing: {offender.value}",
                expected=f"one of {sorted(f'{ratio:.2f}em' for ratio in allowed)}",
            )


@register("negative_tracking")
def negative_tracking(rule: Rule, context: Context) -> Iterable[Finding]:
    """Flag negative letter-spacing anywhere in a brand artifact."""
    for declaration in context.target.declarations:
        if declaration.prop != "letter-spacing" or context.is_exempt(declaration):
            continue
        magnitude = number(declaration.value)
        if magnitude is not None and magnitude < 0:
            yield context.finding(
                rule, declaration,
                observed=f"letter-spacing: {declaration.value}", expected=">= 0",
            )


@register("family_stack_forbids")
def family_stack_forbids(rule: Rule, context: Context) -> Iterable[Finding]:
    """Flag a forbidden family inside a role's font stack."""
    typography = context.registry.typography
    role = rule.params.get("role", "display")
    forbidden = tuple(str(name).lower() for name in rule.params.get("forbidden", ()))
    families = typography.display_families if role == "display" else {typography.text_family}
    markers = tuple(family.lower() for family in families) + (f"font-{role}",)

    for declaration in context.target.declarations:
        if context.is_exempt(declaration):
            continue
        if declaration.prop != "font-family" and f"font-{role}" not in declaration.prop:
            continue
        value = declaration.value.lower()
        if not any(marker in value or marker in declaration.prop for marker in markers):
            continue
        for name in forbidden:
            if name in value:
                yield context.finding(
                    rule, declaration,
                    observed=f"{declaration.prop}: {declaration.value}",
                    expected=" -> ".join(typography.display_fallback),
                )
                break


@register("line_height_range")
def line_height_range(rule: Rule, context: Context) -> Iterable[Finding]:
    """Compare leading against the brandbook range for its type role.

    Only unitless and percentage leading is judged. A `34px` leading depends on the font size it
    sits with, which the static pass cannot resolve, so it is left alone rather than guessed at.
    """
    role = rule.params.get("role", "display")
    bounds = context.registry.typography.line_height.get(role)
    if bounds is None:
        return
    low, high = bounds

    for declaration in context.target.declarations:
        if declaration.prop != "line-height" or context.is_exempt(declaration):
            continue
        if classify_role(declaration.selector) != role:
            continue
        raw = declaration.value.strip().lower()
        if any(token in raw for token in ("var(", "calc", "clamp", "px", "rem", "em")):
            continue
        magnitude = number(raw)
        if magnitude is None:
            continue
        ratio = magnitude / 100 if raw.endswith("%") else magnitude
        if not (low - 0.005 <= ratio <= high + 0.005):
            yield context.finding(
                rule, declaration,
                observed=f"line-height: {declaration.value} ({ratio:.3f})",
                expected=f"{low:.2f}-{high:.2f}",
            )

@register("long_title_face")
def long_title_face(rule: Rule, context: Context) -> Iterable[Finding]:
    """Flag a title that outruns the display face and should fall back to Figtree.

    The display face is uppercase at +3% tracking, which is what makes it a title. Both traits
    stop helping once a title wraps past two lines: uppercase removes the word shapes a reader
    scans by, and positive tracking widens every line it is already struggling to hold together.

    Requires measured geometry, and for the same reason ADR 0006 gave: whether a title wraps to
    three lines depends on the rendered box, not on the stylesheet. `line-height: normal` computes
    to a string rather than a length, so the render worker counts line boxes directly instead of
    dividing height by leading.
    """
    limit = int(rule.params.get("maxLines", 2))
    # An opening statement is exempt, and the list lives in params so the relaxation is visible
    # in design-rules.json rather than buried here. See ADR 0018.
    exempt_roles = {str(name) for name in rule.params.get("exemptRoles", ())}
    families = {name.lower() for name in context.registry.typography.display_families}

    for item in context.measurements:
        if item.exempt or not item.visible:
            continue
        if item.role in exempt_roles or item.role != "title":
            continue
        if item.line_boxes <= limit:
            continue
        stack = item.computed.get("fontFamily", "").lower()
        if not any(family in stack for family in families):
            continue
        locus = item.element_id or ".".join(item.classes) or item.tag
        yield context.finding(
            rule,
            None,
            locus=locus,
            observed=f"{item.line_boxes} rendered lines in the display face",
            expected=f"the display face at <= {limit} lines, or Figtree sentence case beyond it",
        )
