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
    """Flag a render that no longer depicts the sources it was made from.

    When a `*.render.json` beside the render claims it and recorded source digests, each source
    named in `params.sources` is compared by content: a changed hash is a stale render, whatever
    the file times say. That is what makes the rule give the same answer on every checkout, since
    git stamps files with the moment it wrote them rather than when they last changed.

    A source with no recorded digest - a render made before digests were recorded, or a file the
    render did not depict - falls back to comparing modification times. Coarse by design: it
    cannot prove a render is wrong, only that it can no longer be trusted to be right.
    """
    from ..render import content_digest

    target = context.target
    if target.kind not in ("raster", "vector"):
        return

    try:
        rendered_at = target.path.stat().st_mtime
    except OSError:
        return

    recorded = _recorded_sources(target.path)
    stale_against: list[str] = []
    for name in rule.params.get("sources", ()):
        source = target.path.parent / name
        if not source.exists():
            continue
        if name in recorded:
            if content_digest(source) != recorded[name]:
                stale_against.append(name)
        elif source.stat().st_mtime > rendered_at:
            stale_against.append(name)

    if stale_against:
        yield context.finding(
            rule,
            None,
            locus=target.path.name,
            observed=f"{', '.join(stale_against)} changed since this render",
            expected="a render of the current sources",
        )


def _recorded_sources(render: Path) -> dict[str, str]:
    """Read the source digests from the render record that claims a file.

    Args:
        render: The rendered file.

    Returns:
        Basename to SHA-256, empty when no record claims the file or the record predates digests.
    """
    for meta in render.parent.glob("*.render.json"):
        try:
            payload = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if payload.get("schema") != "kunumi.render/v1":
            continue
        if render.name in {Path(item).name for item in payload.get("renders", ())}:
            return dict(payload.get("sources", {}))
    return {}


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
