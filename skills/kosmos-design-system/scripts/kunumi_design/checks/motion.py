#!/usr/bin/env python3
"""Motion checks for web artifacts."""

from __future__ import annotations

from collections.abc import Iterable

from ..findings import Finding
from ..rules import Rule
from . import Context, register

ANIMATING_PROPERTIES = ("animation", "animation-name", "animation-duration", "transition",
                        "transition-duration", "transition-property")


@register("reduced_motion_present")
def reduced_motion_present(rule: Rule, context: Context) -> Iterable[Finding]:
    """Require a reduced-motion escape in any artifact that animates.

    An artifact that links `kunumi-tokens.css` inherits the global reduced-motion block it
    carries, so linking the token sheet satisfies the rule rather than triggering it.
    """
    animating = [
        declaration
        for declaration in context.target.declarations
        if declaration.prop in ANIMATING_PROPERTIES
        and not declaration.in_keyframes
        and not context.is_exempt(declaration)
    ]
    if not animating:
        return

    if any(declaration.in_reduced_motion for declaration in context.target.cascade):
        return

    document = context.target.document
    if document is not None:
        for href in document.stylesheet_hrefs:
            if "kunumi-tokens.css" in href:
                return

    first = animating[0]
    yield context.finding(
        rule,
        first,
        locus=context.target.path.name,
        line=first.line,
        observed=f"{len(animating)} animated declarations, no reduced-motion block",
        expected="@media (prefers-reduced-motion: reduce)",
    )
