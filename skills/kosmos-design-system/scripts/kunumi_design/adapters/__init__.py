#!/usr/bin/env python3
"""Output media for a Kunumi artifact.

HTML is the authoring medium and every other output derives from it. That is not an arbitrary
pick: `template-preview.html` already proves the model — a self-contained, `file://`-openable
artifact that links the token sheet and loads approved marks by relative path with no build step.
Rendering it gives PNG; measuring it gives the geometry a Penpot proposal needs.

The Penpot adapter is the interesting boundary. Python emits a *plan* and never touches the
network: no MCP client, no credentials, no HTTP anywhere in this package. The agent executes the
plan through the Penpot MCP tools and pulls the result back as a PNG, so the identical lint and
visual critique run on the round-trip.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Protocol, runtime_checkable

Identity = Literal["kunumi", "unlimited", "instituto"]
MEDIA = ("html", "png", "penpot")
DEFAULT_MEDIA = ("html", "png")


@dataclass(frozen=True, slots=True)
class ArtifactSpec:
    """What is being produced, and in which media.

    Attributes:
        slug: Output basename.
        identity: Which Kunumi identity the artifact belongs to. Never mix lockups or expressive
            systems across identities without an explicit co-branding request.
        scope: Rule scope the artifact is reviewed under.
        medium: Requested outputs, one or more of `html`, `png`, `penpot`.
        canvas: Delivery size in CSS pixels.
        scale: Device scale factor for raster output.
        html_path: The HTML that every medium derives from.
        notes: Free text carried into the Penpot plan for the reviewing designer.
    """

    slug: str
    identity: Identity
    scope: str
    medium: tuple[str, ...]
    canvas: tuple[int, int]
    scale: float
    html_path: Path
    notes: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any], *, base: Path | None = None) -> ArtifactSpec:
        """Build a spec from a JSON mapping.

        Args:
            payload: The parsed spec.
            base: Directory that relative paths resolve against.

        Returns:
            The spec.

        Raises:
            SystemExit: When a required field is missing or a medium is unknown.
        """
        try:
            html = Path(payload["html"])
        except KeyError:
            raise SystemExit("Artifact spec needs an `html` field") from None
        if base and not html.is_absolute():
            html = base / html

        medium = tuple(payload.get("medium", DEFAULT_MEDIA))
        unknown = [name for name in medium if name not in MEDIA]
        if unknown:
            raise SystemExit(f"Unknown medium {unknown}; expected any of {list(MEDIA)}")

        canvas = payload.get("canvas", [1920, 1080])
        return cls(
            slug=payload.get("slug") or html.stem,
            identity=payload.get("identity", "kunumi"),
            scope=payload.get("scope", "web.new"),
            medium=medium,
            canvas=(int(canvas[0]), int(canvas[1])),
            scale=float(payload.get("scale", 2)),
            html_path=html,
            notes=payload.get("notes", ""),
        )


@dataclass(frozen=True, slots=True)
class EmitResult:
    """What one adapter produced.

    Attributes:
        medium: Adapter name.
        files: Files written.
        agent_actions: Steps the adapter cannot perform itself and the agent must run.
        notes: Anything the caller should carry into its delivery message.
    """

    medium: str
    files: tuple[Path, ...] = ()
    agent_actions: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Render the result as a JSON-ready mapping."""
        return {
            "medium": self.medium,
            "files": [str(path) for path in self.files],
            "agentActions": list(self.agent_actions),
            "notes": list(self.notes),
        }


@runtime_checkable
class MediumAdapter(Protocol):
    """The contract every output medium implements."""

    name: str

    def emit(self, spec: ArtifactSpec, out_dir: Path, context: dict[str, Any]) -> EmitResult:
        """Produce this medium's output for a spec."""
        ...


ADAPTERS: dict[str, MediumAdapter] = {}


def register(adapter: MediumAdapter) -> MediumAdapter:
    """Record an adapter under its own name."""
    ADAPTERS[adapter.name] = adapter
    return adapter


def emit(spec: ArtifactSpec, out_dir: Path, context: dict[str, Any] | None = None) -> tuple[EmitResult, ...]:
    """Run every requested medium, in the declared order.

    Args:
        spec: What to produce.
        out_dir: Directory for the outputs.
        context: Shared state adapters may read or add to, such as render measurements. Ordering
            matters: `png` populates the geometry that `penpot` binds its shapes to.

    Returns:
        One result per requested medium.

    Raises:
        SystemExit: When a requested medium has no adapter registered.
    """
    from . import html as _html  # noqa: F401
    from . import penpot as _penpot  # noqa: F401
    from . import png as _png  # noqa: F401

    context = context if context is not None else {}
    out_dir.mkdir(parents=True, exist_ok=True)

    ordered = [name for name in MEDIA if name in spec.medium]
    results: list[EmitResult] = []
    for name in ordered:
        adapter = ADAPTERS.get(name)
        if adapter is None:
            raise SystemExit(f"No adapter registered for medium {name!r}")
        results.append(adapter.emit(spec, out_dir, context))
    return tuple(results)
