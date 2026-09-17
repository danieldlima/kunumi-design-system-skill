#!/usr/bin/env python3
"""The HTML medium: validate the authoring artifact and place it in the output directory."""

from __future__ import annotations

import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .. import scan
from ..rules import SCRIPTS_DIR
from . import ArtifactSpec, EmitResult, register

_NETWORK_RE = re.compile(r"""(?:src|href)\s*=\s*["'](https?:)?//""", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class HtmlAdapter:
    """Normalise and check the HTML every other medium derives from."""

    name: str = "html"

    def emit(self, spec: ArtifactSpec, out_dir: Path, context: dict[str, Any]) -> EmitResult:
        """Copy the artifact into the output directory and verify its references.

        Three things are checked here rather than in the rule set, because they are properties of
        the *delivery* rather than of the design: the token sheet has to be reachable, every local
        asset has to exist, and nothing may be fetched from the network. An artifact that renders
        only while online is not a deliverable.

        Args:
            spec: What is being produced.
            out_dir: Destination directory.
            context: Shared adapter state; the parsed document is added for later media.

        Returns:
            The emitted files plus any notes about unresolved references.
        """
        source = spec.html_path
        if not source.is_file():
            raise SystemExit(f"No such artifact: {source}")

        text = scan.read_text(source)
        document = scan.parse_html(text, str(source))
        context["document"] = document

        notes: list[str] = []

        if not any("kunumi-tokens.css" in href for href in document.stylesheet_hrefs):
            notes.append(
                "No kunumi-tokens.css link found. The artifact will not inherit the token layer, "
                "its reduced-motion block, or the dark theme."
            )

        for href in document.stylesheet_hrefs:
            if "://" in href or href.startswith("//"):
                notes.append(f"Stylesheet fetched from the network: {href}")
            elif not (source.parent / href).resolve().is_file():
                notes.append(f"Stylesheet does not resolve on disk: {href}")

        if _NETWORK_RE.search(text):
            notes.append(
                "The artifact references a network URL. Approved assets are bundled; resolve them "
                "through kunumi_lookup.py sources instead."
            )

        missing = [
            node.attrs["src"]
            for node in document.nodes
            if node.attrs.get("src")
            and "://" not in node.attrs["src"]
            and not (source.parent / node.attrs["src"]).resolve().exists()
        ]
        for item in dict.fromkeys(missing):
            notes.append(f"Asset does not resolve on disk: {item}")

        if not document.nodes_with("data-kunumi-frame"):
            notes.append(
                "No data-kunumi-frame declared, so the render captures the viewport rather than "
                "each deliverable surface."
            )

        destination = out_dir / f"{spec.slug}.html"
        if source.resolve() != destination.resolve():
            shutil.copyfile(source, destination)
            files = (destination,)
        else:
            files = (source,)

        return EmitResult(medium=self.name, files=files, notes=tuple(notes))


register(HtmlAdapter())
