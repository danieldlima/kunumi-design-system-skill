#!/usr/bin/env python3
"""Derive the checkable rule set from `tokens.json` and `design-rules.json`.

`tokens.json` already encodes much of the brandbook as structured data: the prohibition with both
of its exceptions, per-variable case and tracking, line-height ranges, the spacing scale. Those
rules are *derived* here rather than transcribed, so changing a token changes the rule with no
Python edit. `validate-skills.py` shows the alternative — it hardcodes the two prohibition
exception names in Python while the same names sit in `tokens.json` one directory away.

Rules whose authority is prose live in `references/design-rules.json`. Python owns the mechanism
(how to find a declaration); JSON owns values, severities, scopes, and authority strings.
"""

from __future__ import annotations

import fnmatch
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .findings import SEVERITY_ORDER, Severity


SKILL_DIR = Path(__file__).resolve().parents[2]
REFERENCES_DIR = SKILL_DIR / "references"
SCRIPTS_DIR = SKILL_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

DESIGN_RULES_SCHEMA = "kunumi.design-rules/v1"
DEFAULT_SCOPE = "web.new"


def load_tokens() -> dict[str, Any]:
    """Read the token source of truth, reusing the lookup layer's accessor.

    Returns:
        The parsed contents of `references/tokens.json`.
    """
    import kunumi_lookup

    return kunumi_lookup.load_tokens()


def load_design_rules() -> dict[str, Any]:
    """Read the declared rule and scope definitions.

    Returns:
        The parsed contents of `references/design-rules.json`.

    Raises:
        SystemExit: When the file is missing or carries an unexpected schema, since every check
            depends on it and a silent empty registry would report a clean artifact.
    """
    path = REFERENCES_DIR / "design-rules.json"
    if not path.exists():
        raise SystemExit(f"Missing rule definitions: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != DESIGN_RULES_SCHEMA:
        raise SystemExit(f"{path}: expected schema {DESIGN_RULES_SCHEMA}, got {data.get('schema')!r}")
    return data


# ---------------------------------------------------------------------------- derived rules

@dataclass(frozen=True, slots=True)
class PaletteRules:
    """Color rules derived from `tokens.color`.

    Attributes:
        institutional: Approved institutional hex to token name.
        instituto: Instituto gradient stop hexes.
        deck_support: Deck-only hexes, subordinate to the brandbook.
        product: Product-layer tonal steps, admitted only as values of a semantic role.
        chart: The five chart hexes, in brandbook order.
        chart_vars: The chart custom property names.
        superseded: Hexes retired for chart work.
        asset_local: Hexes that may exist only inside a specific exported asset.
        prohibited: Prohibited hex to the single custom property allowed to carry it.
        semantic_vars: Semantic role custom properties preferred over literal hexes.
        var_by_hex: Approved hex to its canonical custom property.
    """

    institutional: dict[str, str]
    instituto: frozenset[str]
    deck_support: frozenset[str]
    product: frozenset[str]
    chart: tuple[str, ...]
    chart_vars: frozenset[str]
    superseded: frozenset[str]
    asset_local: frozenset[str]
    prohibited: dict[str, str]
    semantic_vars: frozenset[str]
    var_by_hex: dict[str, str]

    @property
    def approved(self) -> frozenset[str]:
        """Every hex that may appear in brand work without further justification."""
        return (
            frozenset(self.institutional)
            | self.instituto
            | self.deck_support
            | self.product
            | frozenset(self.chart)
        )


def derive_palette(tokens: dict[str, Any]) -> PaletteRules:
    """Build the color rule set from the token tree.

    The prohibition's two exceptions are read from `color.prohibition.observedException.hex` and
    `color.prohibition.institutoGradientException`, and matched back to the custom property that
    is allowed to carry each one — so adding a third exception is a token edit, not a code edit.

    Args:
        tokens: The parsed `tokens.json` mapping.

    Returns:
        The derived palette rules.
    """
    color = tokens["color"]

    institutional = {
        entry["hex"].upper(): entry["token"] for entry in color["institutional"]["entries"]
    }
    var_by_hex = {
        entry["hex"].upper(): entry["cssVar"] for entry in color["institutional"]["entries"]
    }
    instituto_entries = color["instituto"]["entries"]
    for entry in instituto_entries:
        var_by_hex.setdefault(entry["hex"].upper(), entry["cssVar"])
    for entry in color["chart"]["entries"]:
        var_by_hex.setdefault(entry["hex"].upper(), entry["cssVar"])
    for entry in color["deckSupport"]["entries"]:
        var_by_hex.setdefault(entry["hex"].upper(), entry["cssVar"])
    product_entries = color.get("product", {}).get("entries", [])
    for entry in product_entries:
        var_by_hex.setdefault(entry["hex"].upper(), entry["cssVar"])

    prohibition = color["prohibition"]
    white = prohibition["observedException"]["hex"].upper()
    black_hex = next(
        (e["hex"].upper() for e in instituto_entries if e["token"] == "black"),
        "#000000",
    )
    black_var = next(
        (e["cssVar"] for e in instituto_entries if e["token"] == "black"),
        "--kunumi-instituto-black",
    )
    prohibited = {white: "--kunumi-surface-raised", black_hex: black_var}

    return PaletteRules(
        institutional=institutional,
        instituto=frozenset(e["hex"].upper() for e in instituto_entries),
        deck_support=frozenset(e["hex"].upper() for e in color["deckSupport"]["entries"]),
        product=frozenset(e["hex"].upper() for e in product_entries),
        chart=tuple(e["hex"].upper() for e in color["chart"]["entries"]),
        chart_vars=frozenset(e["cssVar"] for e in color["chart"]["entries"]),
        superseded=frozenset(hex_value.upper() for hex_value in color["supersededChart"]["entries"]),
        asset_local=frozenset(e["hex"].upper() for e in color["assetLocal"]["entries"]),
        prohibited=prohibited,
        semantic_vars=frozenset(
            role["cssVar"] for role in color.get("semantic", {}).get("roles", [])
        ),
        var_by_hex=var_by_hex,
    )


def prohibition_exception_css_vars(tokens: dict[str, Any]) -> dict[str, str]:
    """Map each prohibited hex to the one custom property allowed to carry it.

    Exposed as a standalone function so `validate-skills.py` can stop hardcoding
    `--kunumi-instituto-black` and `--kunumi-surface-raised` as Python literals while the same
    names already sit in `tokens.json` under `color.prohibition`.

    Args:
        tokens: The parsed `tokens.json` mapping.

    Returns:
        A mapping from uppercase hex to the sanctioned custom property name.
    """
    return dict(derive_palette(tokens).prohibited)


_RANGE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%\s*-\s*(\d+(?:\.\d+)?)\s*%")


def _parse_percent_range(raw: str) -> tuple[float, float]:
    """Turn a `"110% - 140%"` string into a `(1.10, 1.40)` ratio pair."""
    match = _RANGE_RE.search(raw)
    if not match:
        raise ValueError(f"unparseable range: {raw!r}")
    return float(match.group(1)) / 100, float(match.group(2)) / 100


@dataclass(frozen=True, slots=True)
class TypographyRules:
    """Type rules derived from `tokens.typography`.

    Attributes:
        display_family: First-choice display family.
        display_alternate: The brandbook's named alternate.
        display_fallback: The display stack, in order.
        display_tracking: Required display tracking, as an em ratio.
        text_family: Body family.
        text_fallback: The body stack, in order.
        text_tracking: Required body tracking, as an em ratio.
        line_height: Role name to inclusive `(min, max)` ratio range.
        emphasis_colors: The only colors a highlight may use.
        emphasis_forbidden_on: Where a highlight may never be applied.
        variables: The brandbook's own named type variables, untouched.
    """

    display_family: str
    display_alternate: str
    display_fallback: tuple[str, ...]
    display_tracking: float
    text_family: str
    text_fallback: tuple[str, ...]
    text_tracking: float
    line_height: dict[str, tuple[float, float]]
    emphasis_colors: frozenset[str]
    emphasis_forbidden_on: str
    variables: tuple[dict[str, Any], ...]

    @property
    def display_families(self) -> frozenset[str]:
        """Families that may only be used for titles."""
        return frozenset({self.display_family, self.display_alternate})


def derive_typography(tokens: dict[str, Any]) -> TypographyRules:
    """Build the type rule set from the token tree.

    Args:
        tokens: The parsed `tokens.json` mapping.

    Returns:
        The derived typography rules.
    """
    typography = tokens["typography"]
    display = typography["display"]
    text = typography["text"]
    emphasis = typography["emphasis"]

    return TypographyRules(
        display_family=display["family"],
        display_alternate=display["alternate"],
        display_fallback=tuple(display["fallbackOrder"]),
        display_tracking=display["letterSpacingPercent"] / 100,
        text_family=text["family"],
        text_fallback=tuple(text["fallbackOrder"]),
        text_tracking=text["letterSpacingPercent"] / 100,
        line_height={
            role: _parse_percent_range(raw)
            for role, raw in typography["lineHeightRanges"].items()
        },
        emphasis_colors=frozenset(color.upper() for color in emphasis["colors"]),
        emphasis_forbidden_on=emphasis["forbiddenOn"],
        variables=tuple(typography["variables"]),
    )


@dataclass(frozen=True, slots=True)
class GeometryRules:
    """Geometry rules derived from `tokens.geometry`.

    Attributes:
        radii_px: The only sanctioned border radii, in px.
        spacing_px: The product spacing scale, in px.
        brandbook_px: Brandbook geometry values that deliberately sit off the spacing scale.
        card_padding_px: Brandbook card padding.
        card_gap_px: Brandbook card gap.
        text_column_px: The canonical text column width.
    """

    radii_px: frozenset[float]
    spacing_px: frozenset[float]
    brandbook_px: frozenset[float]
    card_padding_px: float
    card_gap_px: float
    text_column_px: float


def _px(raw: str) -> float:
    """Read a `"30px"` style value as a float."""
    return float(str(raw).strip().removesuffix("px"))


def derive_geometry(tokens: dict[str, Any]) -> GeometryRules:
    """Build the geometry rule set from the token tree.

    `geometry.cardPaddingNote` states that 30px deliberately sits off the 4px product scale, so
    the brandbook values are collected separately and exempted from the scale check. Without that
    split, the linter flags the brandbook's own number.

    Args:
        tokens: The parsed `tokens.json` mapping.

    Returns:
        The derived geometry rules.
    """
    geometry = tokens["geometry"]
    card_padding = _px(geometry["cardPadding"])
    card_gap = _px(geometry["cardGap"])
    text_column = _px(geometry["textColumn"])

    return GeometryRules(
        radii_px=frozenset({_px(geometry["radius"]["card"]), _px(geometry["radius"]["control"])}),
        spacing_px=frozenset(float(entry["px"]) for entry in geometry["spacing"]["entries"]),
        brandbook_px=frozenset({card_padding, card_gap, text_column}),
        card_padding_px=card_padding,
        card_gap_px=card_gap,
        text_column_px=text_column,
    )


@dataclass(frozen=True, slots=True)
class LayoutRules:
    """Responsive layout rules derived from `tokens.layout`.

    Attributes:
        breakpoints_px: The sanctioned `min-width` breakpoints, in px.
        max_width_tolerance_px: How far below a breakpoint a `max-width` query may sit.
        container_px: The content container's maximum width.
    """

    breakpoints_px: frozenset[float]
    max_width_tolerance_px: float
    container_px: float


def derive_layout(tokens: dict[str, Any]) -> LayoutRules:
    """Build the layout rule set from the token tree.

    Args:
        tokens: The parsed `tokens.json` mapping.

    Returns:
        The derived layout rules. An empty breakpoint set when the token tree has no layout
        block, so an older token file still loads.
    """
    layout = tokens.get("layout", {})
    breakpoints = layout.get("breakpoints", {})
    return LayoutRules(
        breakpoints_px=frozenset(
            float(entry["minWidthPx"]) for entry in breakpoints.get("entries", [])
        ),
        max_width_tolerance_px=float(breakpoints.get("maxWidthTolerancePx", 0)),
        container_px=float(layout.get("container", {}).get("maxWidthPx", 0)),
    )


@dataclass(frozen=True, slots=True)
class InteractionRules:
    """Interaction and mark-size rules derived from `tokens.interaction` and `tokens.logo`.

    Attributes:
        focus_ring_width_px: Width of the focus ring.
        target_min_px: Minimum pointer target size.
        target_recommended_px: Recommended touch target size.
        logo_min_px: Minimum rendered lockup height of the positive RGB mark.
        og_size_px: The Open Graph image size, as (width, height).
    """

    focus_ring_width_px: float
    target_min_px: float
    target_recommended_px: float
    logo_min_px: float
    og_size_px: tuple[int, int]


def derive_interaction(tokens: dict[str, Any]) -> InteractionRules:
    """Build the interaction rule set from the token tree.

    Args:
        tokens: The parsed `tokens.json` mapping.

    Returns:
        The derived interaction rules.
    """
    interaction = tokens.get("interaction", {})
    target = interaction.get("targetSize", {})
    og = tokens.get("digital", {}).get("og", {})
    return InteractionRules(
        focus_ring_width_px=float(interaction.get("focusRing", {}).get("widthPx", 0)),
        target_min_px=float(target.get("minPx", 0)),
        target_recommended_px=float(target.get("recommendedPx", 0)),
        logo_min_px=float(tokens.get("logo", {}).get("minHeight", {}).get("positiveRgbPx", 0)),
        og_size_px=(int(og.get("widthPx", 0)), int(og.get("heightPx", 0))),
    )


@dataclass(frozen=True, slots=True)
class GradientStop:
    """One Instituto signature gradient stop.

    Attributes:
        token: Stop token name.
        hex: Stop color.
        centre_percent: Measured centre of the stop's band on the 1918px reference bar.
    """

    token: str
    hex: str
    centre_percent: float


def derive_instituto_gradient(tokens: dict[str, Any]) -> tuple[GradientStop, ...]:
    """Build the Instituto gradient stop sequence from the token tree.

    Args:
        tokens: The parsed `tokens.json` mapping.

    Returns:
        The seven stops, in bar order.
    """
    return tuple(
        GradientStop(
            token=entry["token"],
            hex=entry["hex"].upper(),
            centre_percent=float(entry["centrePercent"]),
        )
        for entry in tokens["color"]["instituto"]["entries"]
    )


# ---------------------------------------------------------------------------- declared rules

@dataclass(frozen=True, slots=True)
class Rule:
    """One declared rule.

    Attributes:
        id: Dotted rule id.
        check: Name of the check function that implements the mechanism.
        severity: Severity in the scope being evaluated.
        params: Check-specific values, owned by JSON rather than Python.
        authority: Source file and anchor the rule comes from.
        fix: The instruction offered with every finding.
        message: Optional message template overriding the check's default.
        applies_to: Artifact surfaces the rule binds to, such as `declaration` or `text-node`.
            Binding copy rules to `text-node` is what structurally keeps them away from
            `src=`, `url()` and `--kunumi-*`, rather than excluding those by regex.
        requires: Capabilities the rule needs, such as `render`.
        opt_in: When true the rule is inactive unless a scope's `adds` selects it.
    """

    id: str
    check: str
    severity: Severity
    params: dict[str, Any]
    authority: str
    fix: str
    message: str
    applies_to: tuple[str, ...]
    requires: tuple[str, ...]
    opt_in: bool

    def with_severity(self, severity: Severity) -> Rule:
        """Return a copy of the rule carrying a different severity."""
        return Rule(
            id=self.id,
            check=self.check,
            severity=severity,
            params=self.params,
            authority=self.authority,
            fix=self.fix,
            message=self.message,
            applies_to=self.applies_to,
            requires=self.requires,
            opt_in=self.opt_in,
        )


@dataclass(frozen=True, slots=True)
class Scope:
    """One rule scope.

    Attributes:
        name: Scope id, such as `web.instituto`.
        label: Human description.
        inherits: Parent scopes, applied before this scope's own adjustments.
        demote: Rule id pattern to reduced severity. Preferred over `relax`, because demoting
            keeps the observation and only drops the alarm.
        relax: Rule id patterns switched off entirely.
        adds: Rule id patterns to activate from the opt-in pool.
        why: The authority for this scope's relaxations. Required whenever anything is relaxed.
        detect: Declarations that select this scope automatically.
    """

    name: str
    label: str
    inherits: tuple[str, ...]
    demote: dict[str, Severity]
    relax: tuple[str, ...]
    adds: tuple[str, ...]
    why: str
    detect: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Registry:
    """The complete rule set, derived and declared.

    Attributes:
        tokens: The raw token tree, for checks that need an unmodelled corner.
        palette: Derived color rules.
        typography: Derived type rules.
        geometry: Derived geometry rules.
        layout: Derived responsive layout rules.
        interaction: Derived interaction and mark-size rules.
        gradient: Derived Instituto gradient stops.
        rules: Every declared rule, at its default severity.
        scopes: Every scope, by name.
    """

    tokens: dict[str, Any]
    palette: PaletteRules
    typography: TypographyRules
    geometry: GeometryRules
    layout: LayoutRules
    interaction: InteractionRules
    gradient: tuple[GradientStop, ...]
    rules: tuple[Rule, ...]
    scopes: dict[str, Scope]

    def resolved_scope(self, name: str) -> Scope:
        """Flatten a scope's inheritance chain into one scope.

        Args:
            name: Scope id.

        Returns:
            A scope whose `demote`, `relax` and `adds` include every inherited entry, with the
            child's own entries applied last.

        Raises:
            SystemExit: When the scope, or one of its parents, is not declared.
        """
        if name not in self.scopes:
            known = ", ".join(sorted(self.scopes))
            raise SystemExit(f"Unknown scope {name!r}. Known scopes: {known}")

        scope = self.scopes[name]
        demote: dict[str, Severity] = {}
        relax: list[str] = []
        adds: list[str] = []
        for parent in scope.inherits:
            merged = self.resolved_scope(parent)
            demote.update(merged.demote)
            relax.extend(merged.relax)
            adds.extend(merged.adds)
        demote.update(scope.demote)
        relax.extend(scope.relax)
        adds.extend(scope.adds)

        return Scope(
            name=scope.name,
            label=scope.label,
            inherits=scope.inherits,
            demote=demote,
            relax=tuple(dict.fromkeys(relax)),
            adds=tuple(dict.fromkeys(adds)),
            why=scope.why,
            detect=scope.detect,
        )

    def effective_rules(
        self, scope_name: str, *, capabilities: frozenset[str] = frozenset()
    ) -> tuple[tuple[Rule, ...], tuple[str, ...]]:
        """Select and adjust the rules that apply in a scope.

        Args:
            scope_name: Scope id to evaluate under.
            capabilities: Available capabilities, such as `{"render"}`. Rules requiring a missing
                capability are reported as skipped rather than silently passing.

        Returns:
            A pair of (active rules with scope-adjusted severity, skipped rule ids).
        """
        scope = self.resolved_scope(scope_name)
        active: list[Rule] = []
        skipped: list[str] = []

        for rule in self.rules:
            if rule.opt_in and not _matches_any(rule.id, scope.adds):
                skipped.append(rule.id)
                continue
            if _matches_any(rule.id, scope.relax):
                skipped.append(rule.id)
                continue
            missing = tuple(need for need in rule.requires if need not in capabilities)
            if missing:
                skipped.append(rule.id)
                continue

            severity = rule.severity
            for pattern, demoted in scope.demote.items():
                if _matches_any(rule.id, (pattern,)):
                    severity = demoted
                    break
            active.append(rule if severity == rule.severity else rule.with_severity(severity))

        return tuple(active), tuple(dict.fromkeys(skipped))


def _matches_any(rule_id: str, patterns: tuple[str, ...]) -> bool:
    """Test a rule id against a tuple of fnmatch patterns."""
    return any(fnmatch.fnmatchcase(rule_id, pattern) for pattern in patterns)


def _severity(raw: str, *, where: str) -> Severity:
    """Validate a severity string coming from JSON."""
    if raw not in SEVERITY_ORDER:
        raise SystemExit(f"{where}: unknown severity {raw!r}; expected one of {list(SEVERITY_ORDER)}")
    return raw  # type: ignore[return-value]


def load_registry(tokens: dict[str, Any] | None = None) -> Registry:
    """Assemble the full registry from both sources.

    Args:
        tokens: Optional pre-loaded token tree, so tests can derive rules from a mutated copy.

    Returns:
        The assembled registry.
    """
    tokens = tokens if tokens is not None else load_tokens()
    declared = load_design_rules()

    rules: list[Rule] = []
    for raw in declared["rules"]:
        rules.append(
            Rule(
                id=raw["id"],
                check=raw["check"],
                severity=_severity(raw["severity"], where=raw["id"]),
                params=raw.get("params", {}),
                authority=raw.get("authority", ""),
                fix=raw.get("fix", ""),
                message=raw.get("message", ""),
                applies_to=tuple(raw.get("appliesTo", ("declaration",))),
                requires=tuple(raw.get("requires", ())),
                opt_in=bool(raw.get("optIn", False)),
            )
        )

    scopes: dict[str, Scope] = {}
    for name, raw in declared["scopes"].items():
        scopes[name] = Scope(
            name=name,
            label=raw.get("label", name),
            inherits=tuple(raw.get("inherits", ())),
            demote={
                pattern: _severity(value, where=f"scope {name}")
                for pattern, value in raw.get("demote", {}).items()
            },
            relax=tuple(raw.get("relax", ())),
            adds=tuple(raw.get("adds", ())),
            why=raw.get("why", ""),
            detect=tuple(raw.get("detect", ())),
        )

    return Registry(
        tokens=tokens,
        palette=derive_palette(tokens),
        typography=derive_typography(tokens),
        geometry=derive_geometry(tokens),
        layout=derive_layout(tokens),
        interaction=derive_interaction(tokens),
        gradient=derive_instituto_gradient(tokens),
        rules=tuple(rules),
        scopes=scopes,
    )


# ---------------------------------------------------------------------------- scope resolution

_SCOPE_ATTR_RE = re.compile(
    r"""data-kunumi-scope\s*=\s*["']([a-z0-9._-]+)["']""", re.IGNORECASE
)
_SCOPE_META_RE = re.compile(
    r"""<meta[^>]+name\s*=\s*["']kunumi-scope["'][^>]+content\s*=\s*["']([a-z0-9._-]+)["']""",
    re.IGNORECASE,
)
_SCOPE_COMMENT_RE = re.compile(r"/\*\s*kunumi-scope\s*:\s*([a-z0-9._-]+)\s*\*/", re.IGNORECASE)


def resolve_scope(
    path: Path, text: str, registry: Registry, override: str | None = None
) -> tuple[str, str]:
    """Decide which scope an artifact is evaluated under.

    Mirrors the Source Order in `SKILL.md`: a source the user names wins, then what the artifact
    itself declares, then inference, then the default.

    Args:
        path: Path to the artifact.
        text: The artifact's text content.
        registry: The loaded registry, for scope validation and `detect` patterns.
        override: Scope named explicitly on the command line.

    Returns:
        A pair of (scope name, human-readable reason for the choice).
    """
    if override:
        if override not in registry.scopes:
            known = ", ".join(sorted(registry.scopes))
            raise SystemExit(f"Unknown scope {override!r}. Known scopes: {known}")
        return override, "named on the command line"

    meta = _SCOPE_META_RE.search(text)
    if meta and meta.group(1) in registry.scopes:
        return meta.group(1), "declared by <meta name=kunumi-scope>"

    attr = _SCOPE_ATTR_RE.search(text)
    if attr and attr.group(1) in registry.scopes:
        return attr.group(1), "declared by data-kunumi-scope"

    comment = _SCOPE_COMMENT_RE.search(text)
    if comment and comment.group(1) in registry.scopes:
        return comment.group(1), "declared by a /* kunumi-scope */ header comment"

    name = path.name.lower()
    for scope in registry.scopes.values():
        for pattern in scope.detect:
            if pattern.startswith("path:") and fnmatch.fnmatchcase(name, pattern[5:].lower()):
                return scope.name, f"inferred from the filename pattern {pattern[5:]!r}"

    return DEFAULT_SCOPE, "default; no override and no in-artifact declaration"
