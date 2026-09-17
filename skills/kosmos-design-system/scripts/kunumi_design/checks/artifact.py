#!/usr/bin/env python3
"""Whole-file checks about the delivered artifact rather than its contents."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from ..findings import Finding
from ..rules import Rule
from . import Context, actual_raster_format, register

_EXTENSION_FORMATS = {
    ".png": "png",
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".gif": "gif",
    ".webp": "webp",
}


@register("artifact_format")
def artifact_format(rule: Rule, context: Context) -> Iterable[Finding]:
    """Flag a raster whose extension misdescribes its encoding.

    A `.png` that is really a lossy JPEG is not a naming nit: the brandbook asks for transparent
    PNG for raster work, and the extension is the only claim a consumer can act on.
    """
    target = context.target
    if target.kind != "raster":
        return

    declared = _EXTENSION_FORMATS.get(target.path.suffix.lower())
    actual = actual_raster_format(target.head)
    if declared and actual and declared != actual:
        yield context.finding(
            rule,
            None,
            locus=target.path.name,
            observed=f"{target.path.suffix} declaring {declared}, encoded as {actual}",
            expected=f"an actual {declared} file",
        )


@register("artifact_stale")
def artifact_stale(rule: Rule, context: Context) -> Iterable[Finding]:
    """Flag a render older than the sources it depicts.

    Compares modification times against sibling sources named in `params.sources`. Coarse by
    design: it cannot prove a render is wrong, only that it can no longer be trusted to be right,
    which is the honest claim and enough to send it back through the loop.
    """
    target = context.target
    if target.kind not in ("raster", "vector"):
        return

    try:
        rendered_at = target.path.stat().st_mtime
    except OSError:
        return

    stale_against: list[str] = []
    for name in rule.params.get("sources", ()):
        source = target.path.parent / name
        if source.exists() and source.stat().st_mtime > rendered_at:
            stale_against.append(name)

    if stale_against:
        yield context.finding(
            rule,
            None,
            locus=target.path.name,
            observed=f"older than {', '.join(stale_against)}",
            expected="a render newer than every source it depicts",
        )


@register("artifact_unprovenanced")
def artifact_unprovenanced(rule: Rule, context: Context) -> Iterable[Finding]:
    """Flag a delivered raster that no render claims to have produced.

    `artifact_stale` catches a render that has fallen behind its sources. It cannot catch a file
    that was never a render at all — a screenshot taken in a browser is younger than everything
    and passes every age check. Provenance is the missing half.

    Judged only where rendering is the expected origin, which is a directory holding at least one
    `.html`. Supplied assets — brand marks, bundled fonts — sit in directories with no HTML beside
    them and are never judged, because for them a render.json would be meaningless.

    Matched on file name, not on the recorded path: `renders` stores absolute paths, so the
    recorded value belongs to whichever machine produced it and cannot be compared against a
    checkout somewhere else.
    """
    target = context.target
    if target.kind not in ("raster", "vector"):
        return

    folder = target.path.parent
    if not any(folder.glob("*.html")):
        return

    produced: set[str] = set()
    for meta in folder.glob("*.render.json"):
        try:
            payload = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if payload.get("schema") != "kunumi.render/v1":
            continue
        produced.update(Path(item).name for item in payload.get("renders", ()))

    if target.path.name not in produced:
        yield context.finding(
            rule,
            None,
            locus=target.path.name,
            observed="no render.json beside it claims this file",
            expected="a file produced by kunumi_critic render",
        )
