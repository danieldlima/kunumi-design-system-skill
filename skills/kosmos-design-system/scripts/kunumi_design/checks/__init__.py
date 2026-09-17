#!/usr/bin/env python3
"""The check registry and the review driver.

A check implements a *mechanism* — how to find a declaration, how to classify a selector, how to
recognise a mark. Every *value* it compares against comes from the rule's params or from the
derived registry. No check may branch on its own rule id; that is what keeps the rule set data.

The static pass is deliberately not a cascade resolver. Where a question genuinely needs computed
style or measured geometry, the rule declares `requires: ["render"]` and is reported as skipped
until the render pass can answer it, rather than being answered badly here.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from .. import scan
from ..findings import Finding, Report, sort_findings
from ..rules import Registry, Rule, resolve_scope


TargetKind = Literal["html", "css", "raster", "vector", "other"]

_CLASS_TOKEN_RE = re.compile(r"[.#]([A-Za-z_][\w-]*)")
_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")

DISPLAY_SELECTOR_HINTS = ("kunumi-display", "kunumi-title", "kunumi-category", "kunumi-menu")
# A title past two lines is set in Figtree, sentence case, tracking 0 - see
# typography.md#the-long-title-exception. It keeps the display leading range, so it stays
# classified as display; only the case and tracking rules step aside for it.
LONG_TITLE_SELECTOR_HINTS = ("kunumi-title-long",)
BODY_SELECTOR_HINTS = ("kunumi-body", "kunumi-subtitle", "kunumi-kicker")
DISPLAY_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")
BODY_TAGS = ("p", "li", "dd", "blockquote")
LOGO_SELECTOR_HINTS = ("logo", "lockup", "wordmark", "brand-mark", "brandmark", "symbol-mark")
LOGO_ASSET_KINDS = ("lockup", "wordmark", "icon", "complete-mark")

_MAGIC = {
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpeg",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
    b"RIFF": "webp",
}


@dataclass(frozen=True, slots=True)
class Target:
    """One artifact, parsed once and shared by every check.

    Attributes:
        path: Path to the artifact.
        kind: Coarse artifact class, deciding which checks can say anything.
        text: Text content, empty for binaries.
        declarations: CSS declarations, from the file itself or its inline `<style>` blocks.
        inherited: Declarations from stylesheets the artifact links and that resolve on disk.
            Presence checks need these: `.kunumi-display` gets its uppercase from
            `kunumi-tokens.css`, so an HTML artifact judged on its inline `<style>` alone reads
            as missing a rule it actually inherits.
        document: Parsed HTML, when the artifact is HTML.
        head: First bytes, for binaries, so format claims can be verified.
    """

    path: Path
    kind: TargetKind
    text: str
    declarations: tuple[scan.Declaration, ...]
    inherited: tuple[scan.Declaration, ...]
    document: scan.Document | None
    head: bytes

    @property
    def cascade(self) -> tuple[scan.Declaration, ...]:
        """Own declarations plus inherited ones, for presence questions."""
        return self.declarations + self.inherited


@dataclass(slots=True)
class Context:
    """Shared, per-target derived state that several checks need.

    Attributes:
        registry: The loaded rule registry.
        scope: Scope name in force for this target.
        target: The artifact under review.
        exempt_tokens: Selector tokens covered by `data-kunumi-exempt`.
        exempt_tags: Tag names of exempt nodes carrying no class or id, so a bare `body { ... }`
            rule can be recognised as chrome.
        logo_tokens: Selector tokens belonging to a brand mark.
        capabilities: Capabilities available for this run, such as `{"render"}`.
        measurements: Measured geometry from a render, empty when none was supplied.
        mark_names: Basenames of every approved brand mark, derived from semantic-index.json.
    """

    registry: Registry
    scope: str
    target: Target
    exempt_tokens: frozenset[str] = frozenset()
    exempt_tags: frozenset[str] = frozenset()
    logo_tokens: frozenset[str] = frozenset()
    capabilities: frozenset[str] = frozenset()
    measurements: tuple[Any, ...] = ()
    mark_names: frozenset[str] = frozenset()

    def owns(self, declaration: scan.Declaration) -> bool:
        """Whether a declaration lives in the artifact under review.

        A defect inherited from a linked stylesheet is that stylesheet's finding, not this
        artifact's. Reporting it here would duplicate it the moment both files are linted.
        """
        return declaration.path == str(self.target.path)

    def selector_tokens(self, selector: str) -> frozenset[str]:
        """Extract the class and id tokens a selector references."""
        return frozenset(match.group(1) for match in _CLASS_TOKEN_RE.finditer(selector))

    def is_exempt(self, declaration: scan.Declaration) -> bool:
        """Whether a declaration sits on a surface marked as not-a-brand-artifact.

        Errs toward suppression: a declaration is exempt when *any* token in its selector belongs
        to an exempt subtree. Viewer chrome and brand artifact share stylesheets, and a missed
        finding on chrome costs far less than a false finding that teaches the reader to ignore
        the linter.
        """
        if self.exempt_tokens and (
            self.selector_tokens(declaration.selector) & self.exempt_tokens
        ):
            return True
        if not self.exempt_tags:
            return False
        head = re.split(r"[\s>+~,:]", declaration.selector.strip(), maxsplit=1)[0].lower()
        return head in self.exempt_tags

    def is_logo(self, declaration: scan.Declaration) -> bool:
        """Whether a declaration targets a brand mark."""
        selector = declaration.selector.lower()
        if any(hint in selector for hint in LOGO_SELECTOR_HINTS):
            return True
        return bool(self.selector_tokens(declaration.selector) & self.logo_tokens)

    def finding(
        self,
        rule: Rule,
        declaration: scan.Declaration | None,
        *,
        locus: str | None = None,
        line: int | None = None,
        observed: str | None = None,
        expected: str | None = None,
        message: str | None = None,
    ) -> Finding:
        """Build a finding, filling everything derivable from the rule and the declaration."""
        return Finding(
            rule=rule.id,
            severity=rule.severity,
            scope=self.scope,
            locus=locus or (declaration.selector if declaration else str(self.target.path.name)),
            path=str(self.target.path),
            line=line if line is not None else (declaration.line if declaration else None),
            message=message or rule.message,
            fix=rule.fix,
            observed=observed,
            expected=expected,
            authority=rule.authority,
        )


CheckFn = Callable[[Rule, Context], Iterable[Finding]]
CHECKS: dict[str, CheckFn] = {}


def register(name: str) -> Callable[[CheckFn], CheckFn]:
    """Register a check mechanism under the name rules refer to it by.

    Args:
        name: The `check` value used in `design-rules.json`.

    Returns:
        A decorator that records the function and returns it unchanged.
    """

    def decorate(function: CheckFn) -> CheckFn:
        CHECKS[name] = function
        return function

    return decorate


# ---------------------------------------------------------------------------- shared helpers

def number(value: str) -> float | None:
    """Read the first number in a value, or None when there is none."""
    match = _NUMBER_RE.search(value)
    return float(match.group(0)) if match else None


def to_px(value: str, *, root_px: float = 16.0) -> float | None:
    """Convert a length to px when it is expressible, otherwise None.

    Args:
        value: A CSS length.
        root_px: Root font size used for rem conversion.

    Returns:
        The length in px, or None for values that depend on context the static pass cannot
        resolve: `%`, `vw`, `clamp()`, `calc()`, and `em`, which is relative to the element's
        own font size rather than the root.
    """
    raw = value.strip().lower()
    if raw in ("0", "0px", "0rem"):
        return 0.0
    if any(token in raw for token in ("calc", "clamp", "min(", "max(", "var(", "%", "vw", "vh", "auto")):
        return None
    magnitude = number(raw)
    if magnitude is None:
        return None
    if raw.endswith("rem"):
        return magnitude * root_px
    if raw.endswith("em"):
        return None
    if raw.endswith("px"):
        return magnitude
    return None


def is_long_title(selector: str) -> bool:
    """Whether a selector carries the long-title exception.

    Checked before the display hints elsewhere, because `kunumi-title-long` contains
    `kunumi-title` and would otherwise be judged as an ordinary display selector.
    """
    lowered = selector.lower()
    return any(hint in lowered for hint in LONG_TITLE_SELECTOR_HINTS)


def classify_role(selector: str) -> str | None:
    """Classify a selector as display or body text, or neither.

    Returns:
        `"display"`, `"body"`, or None when the selector carries no type role. Returning None is
        the point: an unclassifiable selector must not be judged against either range.
    """
    lowered = selector.lower()
    if any(hint in lowered for hint in DISPLAY_SELECTOR_HINTS):
        return "display"
    if any(hint in lowered for hint in BODY_SELECTOR_HINTS):
        return "body"
    tags = re.findall(r"(?:^|[\s,>+~])([a-z][a-z0-9]*)", lowered)
    if any(tag in DISPLAY_TAGS for tag in tags):
        return "display"
    if any(tag in BODY_TAGS for tag in tags):
        return "body"
    return None


def token_properties(
    declarations: Sequence[scan.Declaration],
) -> dict[str, dict[str, list[scan.Declaration]]]:
    """Index declarations by selector token, then property.

    Static analysis cannot resolve the cascade, but it can ask a weaker and still useful
    question: is this property declared *anywhere* for a selector mentioning this class? That is
    what keeps `.kunumi-title { font-size }` from being reported as missing the
    `text-transform: uppercase` that the grouped `.kunumi-title, .kunumi-category` block sets.

    Args:
        declarations: Declarations to index.

    Returns:
        A mapping of selector token to property name to the declarations involved.
    """
    index: dict[str, dict[str, list[scan.Declaration]]] = {}
    for declaration in declarations:
        for match in _CLASS_TOKEN_RE.finditer(declaration.selector):
            bucket = index.setdefault(match.group(1), {})
            bucket.setdefault(declaration.prop, []).append(declaration)
    return index


def resolve_var_color(name: str, context: Context) -> str | None:
    """Resolve a custom property to a hex, following one level of aliasing.

    Args:
        name: Custom property name.
        context: The review context, for the target's own declarations.

    Returns:
        The normalized hex, or None when it cannot be resolved statically.
    """
    for declaration in context.target.cascade:
        if declaration.prop != name:
            continue
        direct = scan.normalize_color(declaration.value)
        if direct:
            return direct
        aliases = scan.find_vars(declaration.value)
        if len(aliases) == 1 and aliases[0] != name:
            return resolve_var_color(aliases[0], context)
    return context.registry.palette.var_by_hex and next(
        (hex_value for hex_value, var in context.registry.palette.var_by_hex.items() if var == name),
        None,
    )


# ---------------------------------------------------------------------------- target loading

def detect_kind(path: Path, head: bytes, text: str) -> TargetKind:
    """Classify an artifact by content first, extension second."""
    for magic, _ in _MAGIC.items():
        if head.startswith(magic):
            return "raster"
    suffix = path.suffix.lower()
    if suffix in (".html", ".htm"):
        return "html"
    if suffix == ".css":
        return "css"
    if suffix == ".svg":
        return "vector"
    if suffix in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
        return "raster"
    if "<html" in text[:2048].lower():
        return "html"
    return "other"


def actual_raster_format(head: bytes) -> str | None:
    """Identify a raster format from its magic bytes.

    Args:
        head: The file's first bytes.

    Returns:
        A lowercase format name, or None when the bytes match no known raster header.
    """
    for magic, name in _MAGIC.items():
        if head.startswith(magic):
            return name
    return None


def load_target(path: Path) -> Target:
    """Read and parse one artifact.

    Args:
        path: Path to the artifact.

    Returns:
        The parsed target.
    """
    head = path.open("rb").read(16)
    is_binary = actual_raster_format(head) is not None
    text = "" if is_binary else scan.read_text(path)
    kind = detect_kind(path, head, text)

    document: scan.Document | None = None
    declarations: tuple[scan.Declaration, ...] = ()
    inherited: list[scan.Declaration] = []
    if kind == "html":
        document = scan.parse_html(text, str(path))
        declarations = tuple(document.styles)
        for href in document.stylesheet_hrefs:
            if "://" in href:
                continue
            linked = (path.parent / href).resolve()
            if linked.is_file():
                inherited.extend(scan.parse_css(scan.read_text(linked), str(linked)))
    elif kind == "css":
        declarations = scan.parse_css(text, str(path))

    return Target(
        path=path,
        kind=kind,
        text=text,
        declarations=declarations,
        inherited=tuple(inherited),
        document=document,
        head=head,
    )


def _logo_asset_names() -> frozenset[str]:
    """Collect the basenames of every approved brand mark.

    Derived from `semantic-index.json` rather than hardcoded, so a new mark added to the index is
    recognised as a mark without touching this module.

    Returns:
        Lowercase basenames of brand-mark assets.
    """
    try:
        import kunumi_lookup

        index = kunumi_lookup.load("semantic-index.json")
    except Exception:  # pragma: no cover - the index is optional for the checks to run
        return frozenset()
    return frozenset(
        Path(entry["localPath"]).name.lower()
        for entry in index.get("featuredSources", [])
        if entry.get("kind") in LOGO_ASSET_KINDS
    )


def build_context(
    target: Target,
    registry: Registry,
    scope: str,
    capabilities: frozenset[str],
    measurements: Sequence[Any] = (),
) -> Context:
    """Derive the shared per-target state the checks rely on.

    Args:
        target: The parsed artifact.
        registry: The loaded registry.
        scope: Scope in force.
        capabilities: Capabilities available for this run.
        measurements: Measured geometry from a render, when one is available.

    Returns:
        The populated context.
    """
    exempt: set[str] = set()
    exempt_tags: set[str] = set()
    logos: set[str] = set()
    mark_names = _logo_asset_names()

    document = target.document
    if document is not None:
        for node in document.nodes:
            if document.is_exempt_node(node):
                classes = node.attrs.get("class", "").split()
                exempt.update(classes)
                if node.attrs.get("id"):
                    exempt.add(node.attrs["id"])
                if not classes and not node.attrs.get("id"):
                    exempt_tags.add(node.tag)

            source = Path(node.attrs.get("src", "")).name.lower()
            role = node.attrs.get("data-kunumi-role", "").lower()
            if role == "logo" or (source and source in mark_names):
                logos.update(node.attrs.get("class", "").split())
                if node.attrs.get("id"):
                    logos.add(node.attrs["id"])

    return Context(
        registry=registry,
        scope=scope,
        target=target,
        exempt_tokens=frozenset(exempt),
        exempt_tags=frozenset(exempt_tags),
        logo_tokens=frozenset(logos),
        capabilities=capabilities,
        measurements=tuple(measurements),
        mark_names=mark_names,
    )


def review(
    paths: Sequence[Path],
    registry: Registry,
    *,
    scope_override: str | None = None,
    capabilities: frozenset[str] = frozenset(),
    only_rule: str | None = None,
    measurements: Sequence[Any] = (),
    renders: Sequence[str] = (),
) -> list[Report]:
    """Run every applicable check over every artifact.

    Args:
        paths: Artifacts to review.
        registry: The loaded registry.
        scope_override: Scope named on the command line, bypassing detection.
        capabilities: Capabilities available, such as `{"render"}`.
        only_rule: Restrict the run to a single rule id, for debugging a finding.
        measurements: Measured geometry, enabling the rules that declare `requires: ["render"]`.
        renders: Paths of accompanying PNGs, recorded on the report.

    Returns:
        One report per artifact, in input order.
    """
    from . import artifact, color, geometry, logo, motion, typography  # noqa: F401

    reports: list[Report] = []
    for path in paths:
        target = load_target(path)
        scope, reason = resolve_scope(path, target.text, registry, scope_override)
        active, skipped = registry.effective_rules(scope, capabilities=capabilities)
        context = build_context(target, registry, scope, capabilities, measurements)

        findings: list[Finding] = []
        evaluated = 0
        for rule in active:
            if only_rule and rule.id != only_rule:
                continue
            check = CHECKS.get(rule.check)
            if check is None:
                raise SystemExit(f"{rule.id}: no check registered as {rule.check!r}")
            evaluated += 1
            findings.extend(check(rule, context))

        reports.append(
            Report(
                artifact=str(path),
                scope=scope,
                scope_reason=reason,
                findings=sort_findings(findings),
                rules_evaluated=evaluated,
                rules_skipped=skipped,
                renders=tuple(renders),
            )
        )
    return reports
