#!/usr/bin/env python3
"""The Penpot medium: emit a plan the agent executes, never a network call.

This adapter writes a declarative operation list and stops. Python in this package never imports
an MCP client, never opens a socket, and never holds a credential — so the engine stays a thing
the MCP surface *consumes* rather than a thing that depends on it, which is what keeps the path to
an MCP server or a subagent open without restructuring.

The round-trip is the point: the agent runs the plan through `mcp__penpot__execute_code`, pulls
the result back with `mcp__penpot__export_shape`, and the identical lint and visual critique run
on the export. A Penpot proposal that was never looked at is not a proposal.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..rules import load_registry
from . import ArtifactSpec, EmitResult, register

_ROLE_SHAPES = {
    "logo": "image",
    "title": "text",
    "body": "text",
    "chart": "board",
}


@dataclass(frozen=True, slots=True)
class PenpotAdapter:
    """Derive an ordered, token-bound shape plan from the measured artifact."""

    name: str = "penpot"

    def emit(self, spec: ArtifactSpec, out_dir: Path, context: dict[str, Any]) -> EmitResult:
        """Write `<slug>.penpot-plan.json` and the agent steps that execute it.

        Args:
            spec: What is being produced.
            out_dir: Destination directory.
            context: Shared adapter state; reads the measurements the PNG adapter recorded.

        Returns:
            The plan file plus the ordered agent actions.
        """
        measurements = context.get("measurements", ())
        registry = load_registry()
        palette = registry.palette

        operations: list[dict[str, Any]] = []
        for item in measurements:
            if item.exempt or not item.visible:
                continue
            if not item.frame and not item.role:
                continue

            if item.frame:
                operations.append(
                    {
                        "op": "createBoard",
                        "name": item.frame,
                        "width": round(item.width, 2),
                        "height": round(item.height, 2),
                        "bindFill": palette.var_by_hex.get(
                            _hex_of(item.computed.get("backgroundColor", ""))
                        ),
                    }
                )
                continue

            operations.append(
                {
                    "op": "createShape",
                    "kind": _ROLE_SHAPES.get(item.role, "rect"),
                    "role": item.role,
                    "width": round(item.width, 2),
                    "height": round(item.height, 2),
                    "asset": item.source_name or None,
                    "bindFill": palette.var_by_hex.get(_hex_of(item.computed.get("color", ""))),
                    "typography": {
                        "fontFamily": item.computed.get("fontFamily", ""),
                        "fontSize": item.computed.get("fontSize", ""),
                        "lineHeight": item.computed.get("lineHeight", ""),
                        "letterSpacing": item.computed.get("letterSpacing", ""),
                        "textTransform": item.computed.get("textTransform", ""),
                    }
                    if _ROLE_SHAPES.get(item.role) == "text"
                    else None,
                }
            )

        plan = {
            "schema": "kunumi.penpot-plan/v1",
            "schemaVersion": 1,
            "slug": spec.slug,
            "identity": spec.identity,
            "scope": spec.scope,
            "canvas": {"width": spec.canvas[0], "height": spec.canvas[1]},
            "source": str(spec.html_path),
            "notes": spec.notes,
            "tokenAuthority": "references/tokens.json via design-rules.json",
            "operations": operations,
        }

        path = out_dir / f"{spec.slug}.penpot-plan.json"
        path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        export = out_dir / f"{spec.slug}-penpot.png"
        actions = (
            f"Read {path} and execute its operations with mcp__penpot__execute_code. "
            "Bind every fill and typography value to the Penpot token named in the plan; "
            "do not type literal values.",
            f"Export the resulting board with mcp__penpot__export_shape into {export}.",
            f"Review the export like any other artifact: "
            f"kunumi_critic.py lint {export} --scope {spec.scope}, then look at it against "
            "references/critique-checklist.md.",
        )
        notes: list[str] = []
        if not operations:
            if not measurements:
                notes.append(
                    "The plan is empty because nothing was measured. Request the png medium too, "
                    "so the artifact is rendered before the plan is derived."
                )
            else:
                notes.append(
                    f"The plan is empty although {len(measurements)} elements were measured: none "
                    "carried data-kunumi-frame or data-kunumi-role, or all sat inside a "
                    "data-kunumi-exempt subtree. Annotate the artifact and re-emit."
                )

        return EmitResult(
            medium=self.name, files=(path,), agent_actions=actions, notes=tuple(notes)
        )


def _hex_of(computed: str) -> str:
    """Normalise a computed color to `#RRGGBB`, or empty when unresolvable."""
    from .. import scan

    return scan.normalize_color(computed) or ""


register(PenpotAdapter())
