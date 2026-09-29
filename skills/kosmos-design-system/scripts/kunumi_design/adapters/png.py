#!/usr/bin/env python3
"""The PNG medium: render the artifact and record measured geometry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .. import render as render_mod
from . import ArtifactSpec, EmitResult, register


@dataclass(frozen=True, slots=True)
class PngAdapter:
    """Render one PNG per frame, plus the measurements every later step depends on."""

    name: str = "png"

    def emit(self, spec: ArtifactSpec, out_dir: Path, context: dict[str, Any]) -> EmitResult:
        """Render the artifact, or explain precisely why it could not be rendered.

        Never raises on a missing engine. A machine with no browser must still be able to produce
        the HTML and the Penpot plan, and the honest outcome is a note saying the artifact is
        visually unverified — not a failed run, and never a silent pass.

        Args:
            spec: What is being produced.
            out_dir: Destination directory.
            context: Shared adapter state; measurements are added for the Penpot adapter.

        Returns:
            The rendered files, or a note explaining the engine's absence.
        """
        capability = render_mod.probe()
        if not capability.available:
            return EmitResult(
                medium=self.name,
                notes=(
                    f"Rendered output skipped: {capability.reason}.",
                    f"To enable it: {capability.how_to_install}",
                    "The artifact is visually unverified. Say so on delivery.",
                ),
            )

        result = render_mod.render_html(
            spec.html_path,
            out_dir=out_dir,
            canvas=spec.canvas,
            scale=spec.scale,
            slug=spec.slug,
            reduced_motion=True,
            capability=capability,
        )
        context["measurements"] = result.measurements
        context["renders"] = result.renders

        notes = [f"Rendered with {result.engine}."]
        if not capability.measures:
            notes.append(
                "This engine cannot measure geometry, so the measurement rules stay unevaluated."
            )

        return EmitResult(
            medium=self.name,
            files=(*result.renders, result.meta_path),
            notes=tuple(notes),
        )


register(PngAdapter())
