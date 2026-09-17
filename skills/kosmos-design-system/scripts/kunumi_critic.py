#!/usr/bin/env python3
"""Review Kunumi web artifacts against the brandbook rules derived from tokens.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from kunumi_design import adapters as adapters_mod
from kunumi_design import decisions as decisions_mod
from kunumi_design import findings as findings_mod
from kunumi_design import render as render_mod
from kunumi_design import rules as rules_mod
from kunumi_design.checks import review as run_review

REVIEWABLE_SUFFIXES = (".html", ".htm", ".css", ".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp")


def collect_paths(raw: list[str]) -> list[Path]:
    """Expand the command line into a concrete, ordered artifact list.

    Args:
        raw: Paths as given, which may be files or directories.

    Returns:
        Reviewable files, deduplicated and sorted.

    Raises:
        SystemExit: When a named path does not exist, since silently reviewing nothing would
            report a clean result.
    """
    collected: list[Path] = []
    for item in raw:
        path = Path(item)
        if not path.exists():
            raise SystemExit(f"No such path: {path}")
        if path.is_dir():
            collected.extend(
                child
                for child in sorted(path.rglob("*"))
                if child.is_file() and child.suffix.lower() in REVIEWABLE_SUFFIXES
            )
        else:
            collected.append(path)
    return list(dict.fromkeys(collected))


def command_rules(args: argparse.Namespace) -> int:
    """Print the rule set as it applies in a scope, so it can be argued with."""
    registry = rules_mod.load_registry()
    capabilities = frozenset({"render"}) if args.with_render else frozenset()
    active, skipped = registry.effective_rules(args.scope, capabilities=capabilities)

    if args.search:
        needle = args.search.lower()
        active = tuple(
            rule for rule in active
            if needle in rule.id.lower()
            or needle in rule.message.lower()
            or needle in rule.authority.lower()
        )

    if args.json:
        scope = registry.resolved_scope(args.scope)
        print(json.dumps(
            {
                "schema": "kunumi.design-rules-effective/v1",
                "scope": args.scope,
                "label": scope.label,
                "why": scope.why,
                "capabilities": sorted(capabilities),
                "rules": [
                    {
                        "id": rule.id,
                        "check": rule.check,
                        "severity": rule.severity,
                        "authority": rule.authority,
                        "message": rule.message,
                        "requires": list(rule.requires),
                        "params": rule.params,
                    }
                    for rule in active
                ],
                "skipped": list(skipped),
            },
            ensure_ascii=False,
            indent=2,
        ))
        return 0

    scope = registry.resolved_scope(args.scope)
    print(f"scope {args.scope} - {scope.label}")
    if scope.why:
        print(f"  why: {scope.why}")
    print()
    for rule in active:
        marker = " (needs render)" if rule.requires else ""
        print(f"{rule.severity:<9} {rule.id}{marker}")
        print(f"  {rule.message}")
        print(f"  authority: {rule.authority}")
        print()
    if skipped:
        print(f"not evaluated in this scope: {', '.join(skipped)}")
        print()
    print(f"matches={len(active)} shown={len(active)} skipped={len(skipped)} scope={args.scope}")
    return 0


def command_lint(args: argparse.Namespace) -> int:
    """Review artifacts and report findings."""
    registry = rules_mod.load_registry()
    paths = collect_paths(args.paths)

    measurements: tuple = ()
    capabilities: frozenset[str] = frozenset()
    if args.render:
        measurements = render_mod.load_measurements(Path(args.render))
        capabilities = frozenset({"render"})

    reports = run_review(
        paths,
        registry,
        scope_override=args.scope,
        capabilities=capabilities,
        only_rule=args.rule,
        measurements=measurements,
    )
    if args.severity_min:
        reports = [report.filtered(args.severity_min) for report in reports]

    if args.json:
        if len(reports) == 1:
            print(findings_mod.format_json(reports[0]))
        else:
            print(json.dumps(
                {
                    "schema": "kunumi.design-report-set/v1",
                    "reports": [report.to_dict() for report in reports],
                },
                ensure_ascii=False,
                indent=2,
            ))
    else:
        for report in reports:
            if not report.findings and not args.verbose:
                continue
            print(f"=== {report.artifact}")
            print(f"    scope {report.scope} ({report.scope_reason})")
            print()
            print(findings_mod.format_text(report))
            print()
        combined = findings_mod.merge(reports)
        print(combined.tally() + f" artifacts={len(reports)}")

    return max(report.exit_code for report in reports) if reports else 0



def parse_canvas(raw: str) -> tuple[int, int]:
    """Read a `1920x1080` canvas argument.

    Args:
        raw: The argument text.

    Returns:
        The canvas as a `(width, height)` pair.

    Raises:
        SystemExit: When the argument is not two positive integers separated by `x`.
    """
    try:
        width, _, height = raw.lower().partition("x")
        return int(width), int(height)
    except ValueError:
        raise SystemExit(f"Bad --canvas {raw!r}; expected WIDTHxHEIGHT, e.g. 1920x1080") from None


def command_render(args: argparse.Namespace) -> int:
    """Render an artifact to PNG and record measured geometry."""
    capability = render_mod.probe()
    if args.probe:
        print(json.dumps(capability.to_dict(), ensure_ascii=False, indent=2))
        return 0 if capability.available else 1

    html = Path(args.html)
    if not html.is_file():
        raise SystemExit(f"No such artifact: {html}")

    out_dir = Path(args.out_dir) if args.out_dir else Path("output/kunumi-design") / html.stem
    result = render_mod.render_html(
        html,
        out_dir=out_dir,
        canvas=parse_canvas(args.canvas),
        scale=args.scale,
        slug=args.slug,
        reduced_motion=args.reduced_motion,
        capability=capability,
    )

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return 0

    print(f"engine {result.engine}")
    for path in result.renders:
        print(f"  render {path}")
    print(f"  measured {len(result.measurements)} elements -> {result.meta_path}")
    print()
    print(f"renders={len(result.renders)} measured={len(result.measurements)}")
    return 0


def command_review(args: argparse.Namespace) -> int:
    """Render, lint, and print the exact paths to open for the visual pass.

    This is the loop's workhorse. It deliberately prints the render paths even when the lint is
    clean, because a clean lint is not a passed review: the checklist still has to be answered
    against the image.
    """
    registry = rules_mod.load_registry()
    html = Path(args.html)
    if not html.is_file():
        raise SystemExit(f"No such artifact: {html}")

    out_dir = Path(args.out_dir) if args.out_dir else Path("output/kunumi-design") / html.stem
    capability = render_mod.probe()

    measurements: tuple = ()
    renders: tuple[str, ...] = ()
    notes: list[str] = []
    if capability.available and capability.measures:
        result = render_mod.render_html(
            html,
            out_dir=out_dir,
            canvas=parse_canvas(args.canvas),
            scale=args.scale,
            reduced_motion=args.reduced_motion,
            capability=capability,
        )
        measurements = result.measurements
        renders = tuple(str(path) for path in result.renders)
    else:
        notes.append(
            f"Rendered inspection skipped: {capability.reason}. "
            f"To enable it: {capability.how_to_install}"
        )

    capabilities = frozenset({"render"}) if measurements else frozenset()
    report = run_review(
        [html],
        registry,
        scope_override=args.scope,
        capabilities=capabilities,
        measurements=measurements,
        renders=renders,
    )[0]

    if args.json:
        payload = report.to_dict()
        payload["renderCapability"] = capability.to_dict()
        payload["notes"] = notes
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return report.exit_code

    print(f"=== {report.artifact}")
    print(f"    scope {report.scope} ({report.scope_reason})")
    print()
    print(findings_mod.format_text(report))
    print()
    for note in notes:
        print(f"note  render.unavailable")
        print(f"  {note}")
        print()
    if renders:
        print("Now open every render and answer references/critique-checklist.md in writing.")
        print("The lint report is not a substitute for looking at the artifact.")
        for path in renders:
            print(f"  {path}")
    print()
    return report.exit_code

def command_decisions(args: argparse.Namespace) -> int:
    """List recorded design decisions, so precedent is read before it is remade."""
    all_decisions = decisions_mod.load_all()
    selected = decisions_mod.select(
        all_decisions,
        search=args.search,
        rule=args.rule,
        status=args.status,
        scope=args.scope,
    )
    shown = selected[: args.limit]

    if args.json:
        print(json.dumps(
            {
                "schema": "kunumi.decisions/v1",
                "nextId": decisions_mod.next_id(all_decisions),
                "decisions": [item.to_dict() for item in shown],
            },
            ensure_ascii=False,
            indent=2,
        ))
        return 0

    for item in shown:
        rules = ", ".join(item.rules) if item.rules else "-"
        print(f"{item.id} · {item.status} · {item.date} · scope {item.scope}")
        print(f"  {item.title}")
        print(f"  artifact: {item.artifact}")
        print(f"  rules: {rules}")
        print(f"  {item.path}")
        print()
    print(
        f"matches={len(selected)} shown={len(shown)} "
        f"next-id={decisions_mod.next_id(all_decisions)}"
    )
    return 0

def command_emit(args: argparse.Namespace) -> int:
    """Produce an artifact in every requested medium.

    Media run in a fixed order rather than the order they were typed, because `penpot` binds its
    shapes to the geometry that `png` measures. Asking for penpot alone yields an empty plan and
    says so.
    """
    source = Path(args.source)
    if not source.is_file():
        raise SystemExit(f"No such artifact or spec: {source}")

    if source.suffix.lower() == ".json":
        payload = json.loads(source.read_text(encoding="utf-8"))
        spec = adapters_mod.ArtifactSpec.from_dict(payload, base=source.parent)
    else:
        media = tuple(args.medium) if args.medium else adapters_mod.DEFAULT_MEDIA
        unknown = [name for name in media if name not in adapters_mod.MEDIA]
        if unknown:
            raise SystemExit(
                f"Unknown medium {unknown}; expected any of {list(adapters_mod.MEDIA)}"
            )
        spec = adapters_mod.ArtifactSpec(
            slug=args.slug or source.stem,
            identity=args.identity,
            scope=args.scope or rules_mod.DEFAULT_SCOPE,
            medium=media,
            canvas=parse_canvas(args.canvas),
            scale=args.scale,
            html_path=source,
            notes=args.notes or "",
        )

    out_dir = Path(args.out_dir) if args.out_dir else Path("output/kunumi-design") / spec.slug
    results = adapters_mod.emit(spec, out_dir)

    if args.json:
        print(json.dumps(
            {
                "schema": "kunumi.emit/v1",
                "slug": spec.slug,
                "scope": spec.scope,
                "identity": spec.identity,
                "media": list(spec.medium),
                "outDir": str(out_dir),
                "results": [result.to_dict() for result in results],
            },
            ensure_ascii=False,
            indent=2,
        ))
        return 0

    actions: list[str] = []
    for result in results:
        print(f"{result.medium}")
        for path in result.files:
            print(f"  wrote {path}")
        for note in result.notes:
            print(f"  note: {note}")
        actions.extend(result.agent_actions)
        print()

    if actions:
        print("Steps this tool cannot perform - run them yourself, in order:")
        for index, action in enumerate(actions, start=1):
            print(f"  {index}. {action}")
        print()

    files = sum(len(result.files) for result in results)
    print(f"media={len(results)} files={files} actions={len(actions)} out-dir={out_dir}")
    return 0

def build_parser() -> argparse.ArgumentParser:
    """Assemble the command line.

    Returns:
        The configured parser.
    """
    parser = argparse.ArgumentParser(
        prog="kunumi_critic.py",
        description=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    rules_parser = subparsers.add_parser(
        "rules", help="Show the rule set as it applies in a scope."
    )
    rules_parser.add_argument("--scope", default=rules_mod.DEFAULT_SCOPE)
    rules_parser.add_argument("--search")
    rules_parser.add_argument(
        "--with-render", action="store_true", help="Include rules that need measured geometry."
    )
    rules_parser.add_argument("--json", action="store_true")

    lint_parser = subparsers.add_parser("lint", help="Review artifacts against the rule set.")
    lint_parser.add_argument("paths", nargs="+")
    lint_parser.add_argument("--scope", help="Override scope detection.")
    lint_parser.add_argument("--rule", help="Evaluate a single rule id.")
    lint_parser.add_argument(
        "--severity-min",
        choices=list(findings_mod.SEVERITY_ORDER),
        help="Drop findings below this severity.",
    )
    lint_parser.add_argument(
        "--render", help="Path to a render.json carrying measured geometry."
    )
    lint_parser.add_argument(
        "--verbose", action="store_true", help="List artifacts that produced no findings."
    )
    lint_parser.add_argument("--json", action="store_true")

    render_parser = subparsers.add_parser(
        "render", help="Render an artifact to PNG and measure its annotated elements."
    )
    render_parser.add_argument("html", nargs="?")
    render_parser.add_argument("--canvas", default="1920x1080")
    render_parser.add_argument("--scale", type=float, default=2.0)
    render_parser.add_argument("--slug")
    render_parser.add_argument("--out-dir")
    render_parser.add_argument(
        "--reduced-motion", action="store_true", help="Emulate prefers-reduced-motion: reduce."
    )
    render_parser.add_argument(
        "--probe", action="store_true", help="Report the available engine and exit."
    )
    render_parser.add_argument("--json", action="store_true")

    review_parser = subparsers.add_parser(
        "review", help="Render, lint, and list the renders to inspect visually."
    )
    review_parser.add_argument("html")
    review_parser.add_argument("--scope")
    review_parser.add_argument("--canvas", default="1920x1080")
    review_parser.add_argument("--scale", type=float, default=2.0)
    review_parser.add_argument("--out-dir")
    review_parser.add_argument("--reduced-motion", action="store_true")
    review_parser.add_argument("--json", action="store_true")

    emit_parser = subparsers.add_parser(
        "emit", help="Produce an artifact as HTML, PNG, a Penpot plan, or several."
    )
    emit_parser.add_argument("source", help="An HTML artifact, or a JSON artifact spec.")
    emit_parser.add_argument(
        "--medium", action="append", choices=list(adapters_mod.MEDIA),
        help="Repeatable. Defaults to html and png.",
    )
    emit_parser.add_argument(
        "--identity", default="kunumi", choices=["kunumi", "unlimited", "instituto"]
    )
    emit_parser.add_argument("--scope")
    emit_parser.add_argument("--canvas", default="1920x1080")
    emit_parser.add_argument("--scale", type=float, default=2.0)
    emit_parser.add_argument("--slug")
    emit_parser.add_argument("--notes")
    emit_parser.add_argument("--out-dir")
    emit_parser.add_argument("--json", action="store_true")

    decisions_parser = subparsers.add_parser(
        "decisions", help="List recorded design decisions."
    )
    decisions_parser.add_argument("--search")
    decisions_parser.add_argument("--rule", help="Entries interpreting this rule id.")
    decisions_parser.add_argument("--status")
    decisions_parser.add_argument("--scope")
    decisions_parser.add_argument("--limit", type=int, default=20)
    decisions_parser.add_argument("--json", action="store_true")

    return parser


def main() -> int:
    """Dispatch a subcommand.

    Returns:
        The process exit code: 2 when a blocker was found, 1 for a violation, 0 otherwise.
    """
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "rules":
        return command_rules(args)
    if args.command == "lint":
        return command_lint(args)
    if args.command == "render":
        return command_render(args)
    if args.command == "review":
        return command_review(args)
    if args.command == "emit":
        return command_emit(args)
    if args.command == "decisions":
        return command_decisions(args)
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
