"""Adapter tests, including the render/static parity that was a real defect.

The exemption rule is implemented twice — once in Python for the static pass and once in
JavaScript inside the render worker. They drifted: the JS version had no frame reset, so marking a
preview harness as chrome silently exempted the artifact it exists to display, and the Penpot plan
came out empty. Parity is asserted here because two implementations of one rule will drift again.
"""

from __future__ import annotations

import json

import pytest


def test_spec_rejects_an_unknown_medium(fixtures_dir):
    from kunumi_design import adapters

    with pytest.raises(SystemExit):
        adapters.ArtifactSpec.from_dict(
            {"html": str(fixtures_dir / "compliant-card.html"), "medium": ["figma"]}
        )


def test_spec_requires_an_html_field():
    from kunumi_design import adapters

    with pytest.raises(SystemExit):
        adapters.ArtifactSpec.from_dict({"slug": "x"})


def test_media_run_in_dependency_order_not_request_order(fixtures_dir, tmp_path):
    """penpot binds to geometry png measures, so ordering is fixed rather than as-typed."""
    from kunumi_design import adapters

    spec = adapters.ArtifactSpec(
        slug="ordering",
        identity="kunumi",
        scope="web.new",
        medium=("penpot", "html", "png"),
        canvas=(400, 300),
        scale=1.0,
        html_path=fixtures_dir / "compliant-card.html",
    )
    results = adapters.emit(spec, tmp_path)
    assert [result.medium for result in results] == ["html", "png", "penpot"]


def test_html_adapter_flags_a_missing_token_sheet(fixtures_dir, tmp_path):
    from kunumi_design import adapters

    spec = adapters.ArtifactSpec(
        slug="tokens-missing",
        identity="kunumi",
        scope="web.new",
        medium=("html",),
        canvas=(400, 300),
        scale=1.0,
        html_path=fixtures_dir / "compliant-card.html",
    )
    (result,) = adapters.emit(spec, tmp_path)
    assert any("kunumi-tokens.css" in note for note in result.notes)
    assert (tmp_path / "tokens-missing.html").exists()


def test_penpot_adapter_never_performs_the_network_step(fixtures_dir, tmp_path):
    """Python emits a plan; the agent executes it. No MCP client, no socket, no credential."""
    from kunumi_design import adapters

    spec = adapters.ArtifactSpec(
        slug="plan-only",
        identity="instituto",
        scope="web.instituto",
        medium=("penpot",),
        canvas=(400, 300),
        scale=1.0,
        html_path=fixtures_dir / "compliant-card.html",
    )
    (result,) = adapters.emit(spec, tmp_path)
    plan = json.loads((tmp_path / "plan-only.penpot-plan.json").read_text(encoding="utf-8"))

    assert plan["schema"] == "kunumi.penpot-plan/v1"
    assert plan["identity"] == "instituto"
    assert result.agent_actions
    assert any("mcp__penpot__execute_code" in action for action in result.agent_actions)
    assert any("export_shape" in action for action in result.agent_actions)


def test_engine_package_imports_no_network_client():
    """Guard the boundary that keeps the MCP path open: the engine must stay dependency-free."""
    from pathlib import Path

    from kunumi_design import rules

    package = Path(rules.__file__).parent
    forbidden = ("import requests", "import httpx", "import urllib.request", "import socket")
    offenders: list[str] = []
    for path in package.rglob("*.py"):
        if path.name == "_render_worker.py":
            continue  # the worker is a subprocess and declares its own dependency
        text = path.read_text(encoding="utf-8")
        offenders.extend(f"{path.name}: {token}" for token in forbidden if token in text)
    assert offenders == []


def _engine_available() -> bool:
    from kunumi_design import render

    capability = render.probe()
    return capability.available and capability.measures


@pytest.mark.skipif(not _engine_available(), reason="no measuring render engine available")
def test_exemption_parity_between_static_and_rendered_passes(skill_dir, tmp_path):
    """The frame reset must behave identically in Python and in the worker's JavaScript."""
    from kunumi_design import render, scan

    html = skill_dir / "assets" / "web" / "template-preview.html"
    document = scan.parse_html(scan.read_text(html), str(html))

    static_frames = {
        node.attrs["data-kunumi-frame"]
        for node in document.nodes_with("data-kunumi-frame")
        if not document.is_exempt_node(node)
    }
    assert static_frames, "frames must not be exempt just because the viewer around them is"

    result = render.render_html(html, out_dir=tmp_path, canvas=(1200, 700), scale=1.0,
                              reduced_motion=True)
    rendered_frames = {item.frame for item in result.measurements if item.frame and not item.exempt}
    assert rendered_frames <= static_frames
    assert rendered_frames, "the render worker must apply the same frame reset"


@pytest.mark.skipif(not _engine_available(), reason="no measuring render engine available")
def test_penpot_plan_binds_tokens_rather_than_literals(skill_dir, tmp_path):
    from kunumi_design import adapters

    spec = adapters.ArtifactSpec(
        slug="bound",
        identity="kunumi",
        scope="web.new",
        medium=("png", "penpot"),
        canvas=(1200, 700),
        scale=1.0,
        html_path=skill_dir / "assets" / "web" / "template-preview.html",
    )
    adapters.emit(spec, tmp_path)
    plan = json.loads((tmp_path / "bound.penpot-plan.json").read_text(encoding="utf-8"))

    assert plan["operations"], "an annotated, rendered artifact must yield operations"
    boards = [op for op in plan["operations"] if op["op"] == "createBoard"]
    assert boards and boards[0]["bindFill"] == "--kunumi-gelo"
    assert all(
        op.get("bindFill") is None or op["bindFill"].startswith("--kunumi-")
        for op in plan["operations"]
    )
