#!/usr/bin/env python3
"""Capability probing and headless rendering, without importing a browser dependency.

The rule set needs three things the static pass cannot supply: whether a lockup clears its 28px
minimum once `clamp()` has resolved, what the artifact actually looks like at delivery size, and
a PNG a human or an agent can inspect. All three need a real engine.

This module stays standard library only and shells out to `_render_worker.py`. That keeps the
skill installable and usable with no dependency at all: when no engine is reachable, `lint` still
runs and reports the measurement rules as skipped rather than passing them by default. Only
`render`, which the user asked for explicitly, may fail hard.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


WORKER = Path(__file__).resolve().parent / "_render_worker.py"
INSTALL_HINT = (
    "uv run --with playwright python -m playwright install chromium"
    "  (or set KUNUMI_RENDER_CMD)"
)


@dataclass(frozen=True, slots=True)
class RenderCapability:
    """What this machine can actually render with.

    Attributes:
        available: Whether any engine was found.
        engine: Identifier of the chosen engine.
        reason: Why this engine was chosen, or why none was.
        how_to_install: The command that would make rendering available.
        measures: Whether the engine can report geometry. A full-page screenshot without DOM
            access still produces an image but cannot answer the measurement rules, and saying so
            is the difference between a skipped rule and a false pass.
    """

    available: bool
    engine: str
    reason: str
    how_to_install: str = INSTALL_HINT
    measures: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Render the capability as a JSON-ready mapping."""
        return {
            "available": self.available,
            "engine": self.engine,
            "reason": self.reason,
            "howToInstall": self.how_to_install,
            "measures": self.measures,
        }


def _playwright_importable() -> bool:
    """Whether `playwright` can be imported by the current interpreter."""
    from importlib.util import find_spec

    try:
        return find_spec("playwright") is not None
    except (ImportError, ValueError):
        return False


def probe() -> RenderCapability:
    """Choose a render engine, first match wins.

    Returns:
        The chosen capability. Order is deliberate: an in-process playwright is fastest, an
        explicit `KUNUMI_RENDER_CMD` is the escape hatch for engines this module never heard of,
        and `uv` is the zero-install path that reuses an already-cached Chromium.
    """
    if _playwright_importable():
        return RenderCapability(
            available=True,
            engine="playwright-chromium",
            reason="playwright is importable in this interpreter",
            measures=True,
        )

    override = os.environ.get("KUNUMI_RENDER_CMD")
    if override:
        return RenderCapability(
            available=True,
            engine="external-command",
            reason="KUNUMI_RENDER_CMD is set",
            measures=False,
        )

    if shutil.which("uv"):
        return RenderCapability(
            available=True,
            engine="uv-playwright",
            reason="uv is on PATH; the worker runs under `uv run --with playwright`",
            measures=True,
        )

    return RenderCapability(
        available=False,
        engine="none",
        reason="playwright is not importable, KUNUMI_RENDER_CMD is unset, and uv is not on PATH",
        measures=False,
    )


@dataclass(frozen=True, slots=True)
class Measurement:
    """One measured element from a rendered artifact.

    Attributes:
        tag: Lowercased tag name.
        role: Value of `data-kunumi-role`, or empty.
        frame: Value of `data-kunumi-frame`, or empty.
        exempt: Whether the element sits inside a `data-kunumi-exempt` subtree.
        classes: Class list.
        element_id: Element id, or empty.
        src: Value of `src`, or empty.
        width: Rendered width in CSS pixels.
        height: Rendered height in CSS pixels.
        computed: Computed style values the measurement rules consult.
        visible: Whether the element occupies space and is displayed.
        line_boxes: Number of rendered line boxes, or 0 when the element holds no text.
    """

    tag: str
    role: str
    frame: str
    exempt: bool
    classes: tuple[str, ...]
    element_id: str
    src: str
    width: float
    height: float
    computed: dict[str, str]
    visible: bool
    line_boxes: int = 0

    @property
    def source_name(self) -> str:
        """Basename of the element's `src`, lowercased."""
        return Path(self.src).name.lower() if self.src else ""


@dataclass(frozen=True, slots=True)
class RenderResult:
    """The outcome of one render.

    Attributes:
        artifact: The HTML that was rendered.
        engine: Engine used.
        renders: Paths of the PNGs produced, one per frame.
        measurements: Measured elements.
        meta_path: Path of the written `*.render.json`.
        sources: Basename of each source the render depicts - the HTML and every stylesheet it
            links on disk - to the SHA-256 of its content at render time.
    """

    artifact: Path
    engine: str
    renders: tuple[Path, ...]
    measurements: tuple[Measurement, ...]
    meta_path: Path
    sources: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Render the result as a JSON-ready mapping."""
        return {
            "schema": "kunumi.render/v1",
            "schemaVersion": 2,
            "artifact": str(self.artifact),
            "engine": self.engine,
            "renders": [str(path) for path in self.renders],
            "sources": dict(sorted(self.sources.items())),
            "measurements": [
                {
                    "tag": item.tag,
                    "role": item.role,
                    "frame": item.frame,
                    "exempt": item.exempt,
                    "classes": list(item.classes),
                    "id": item.element_id,
                    "src": item.src,
                    "width": item.width,
                    "height": item.height,
                    "visible": item.visible,
                    # Round-trips as the worker's own key, so a reloaded render.json feeds
                    # typography.display.long-title the same line count a live render does.
                    "lineBoxes": item.line_boxes,
                    **item.computed,
                }
                for item in self.measurements
            ],
        }


def content_digest(path: Path) -> str:
    """Hash a file's content, the identity `artifact.stale` compares against.

    Args:
        path: File to hash.

    Returns:
        The hex SHA-256 of the file's bytes.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_digests(html: Path) -> dict[str, str]:
    """Digest the sources a render of `html` depicts.

    Content, not modification time: a fresh checkout stamps every file with the moment it was
    written, in whatever order git wrote them, so an mtime comparison calls a current render
    stale - or a stale one current - depending on the checkout rather than on the content.

    Args:
        html: The artifact being rendered.

    Returns:
        Basename to SHA-256 for the HTML and every local stylesheet it links that resolves.
    """
    from . import scan

    digests = {html.name: content_digest(html)}
    document = scan.parse_html(scan.read_text(html), str(html))
    for href in document.stylesheet_hrefs:
        if "://" in href:
            continue
        linked = (html.parent / href).resolve()
        if linked.is_file():
            digests[linked.name] = content_digest(linked)
    return digests


def _parse_measurements(raw: list[dict[str, Any]]) -> tuple[Measurement, ...]:
    """Turn the worker's JSON into Measurement records."""
    computed_keys = (
        "fontFamily", "fontSize", "lineHeight", "letterSpacing",
        "textTransform", "color", "backgroundColor",
    )
    return tuple(
        Measurement(
            tag=str(item.get("tag", "")),
            role=str(item.get("role", "")),
            frame=str(item.get("frame", "")),
            exempt=bool(item.get("exempt", False)),
            classes=tuple(item.get("classes", ())),
            element_id=str(item.get("id", "")),
            src=str(item.get("src", "")),
            width=float(item.get("width", 0.0)),
            height=float(item.get("height", 0.0)),
            computed={key: str(item.get(key, "")) for key in computed_keys},
            visible=bool(item.get("visible", False)),
            line_boxes=int(item.get("lineBoxes", 0) or 0),
        )
        for item in raw
    )


def render_html(
    html: Path,
    *,
    out_dir: Path,
    canvas: tuple[int, int] = (1920, 1080),
    scale: float = 2.0,
    slug: str | None = None,
    reduced_motion: bool = False,
    capability: RenderCapability | None = None,
) -> RenderResult:
    """Render an HTML artifact to PNG and measure its annotated elements.

    One PNG per `[data-kunumi-frame]`, or a single viewport screenshot when the artifact declares
    no frames. Alongside them, a `*.render.json` carrying the measured geometry, which is both
    what the measurement rules consume and what accompanies the image into the visual critique.

    Args:
        html: The artifact to render.
        out_dir: Directory for the PNGs and the render metadata.
        canvas: Viewport size in CSS pixels.
        scale: Device scale factor, so exports are inspectable at delivery size.
        slug: Basename for the outputs; defaults to the HTML stem.
        reduced_motion: Emulate `prefers-reduced-motion: reduce`.
        capability: Pre-probed capability, to avoid probing twice.

    Returns:
        The render result.

    Raises:
        SystemExit: When no engine is available, or the worker fails. This call is only made when
            a render was asked for explicitly, so failing loudly is correct here; `lint` never
            routes through this path without first checking `probe()`.
    """
    capability = capability or probe()
    if not capability.available:
        raise SystemExit(
            f"Cannot render: {capability.reason}.\nTo enable it: {capability.how_to_install}"
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    slug = slug or html.stem
    spec = {
        "html": str(html.resolve()),
        "outDir": str(out_dir.resolve()),
        "slug": slug,
        "width": canvas[0],
        "height": canvas[1],
        "scale": scale,
        "reducedMotion": reduced_motion,
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
        json.dump(spec, handle)
        spec_path = Path(handle.name)

    try:
        command = _worker_command(capability, spec_path)
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise SystemExit(
                f"Render failed with {capability.engine} (exit {completed.returncode}).\n"
                f"{detail}\nTo install the engine: {capability.how_to_install}"
            )
        payload = json.loads(completed.stdout.strip().splitlines()[-1])
    finally:
        spec_path.unlink(missing_ok=True)

    measurements = _parse_measurements(payload.get("measurements", []))
    renders = tuple(Path(item) for item in payload.get("renders", []))

    result = RenderResult(
        artifact=html,
        engine=capability.engine,
        renders=renders,
        measurements=measurements,
        meta_path=out_dir / f"{slug}.render.json",
        sources=source_digests(html),
    )
    result.meta_path.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result


def _worker_command(capability: RenderCapability, spec_path: Path) -> list[str]:
    """Build the subprocess command for the chosen engine."""
    if capability.engine == "playwright-chromium":
        return [sys.executable, str(WORKER), str(spec_path)]
    if capability.engine == "uv-playwright":
        return ["uv", "run", "--quiet", "--script", str(WORKER), str(spec_path)]
    if capability.engine == "external-command":
        template = os.environ["KUNUMI_RENDER_CMD"]
        return ["sh", "-c", f"{template} {spec_path}"]
    raise SystemExit(f"No worker command for engine {capability.engine!r}")


def load_measurements(path: Path) -> tuple[Measurement, ...]:
    """Read measured geometry back from a `*.render.json`.

    Args:
        path: Path to the render metadata.

    Returns:
        The measured elements.

    Raises:
        SystemExit: When the file is missing or does not carry the render schema.
    """
    if not path.exists():
        raise SystemExit(f"No such render metadata: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "kunumi.render/v1":
        raise SystemExit(f"{path}: not a kunumi.render/v1 document")
    return _parse_measurements(payload.get("measurements", []))
