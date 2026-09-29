#!/usr/bin/env python3
"""Lightweight validation for the Kunumi skills repository."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
TOKEN_OWNER = "kosmos-design-system"


def parse_frontmatter(path: Path) -> tuple[dict[str, str], list[str]]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    if not text.startswith("---\n"):
        return {}, ["missing opening YAML frontmatter marker"]

    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, ["missing closing YAML frontmatter marker"]

    frontmatter: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            errors.append(f"invalid frontmatter line: {line!r}")
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip().strip('"').strip("'")

    return frontmatter, errors


def prohibition_exceptions(skill_dir: Path, tokens: dict) -> dict[str, str]:
    """Read which custom property may carry each prohibited color.

    These two names used to be Python string literals here while `tokens.json` already carried
    them as structured data under `color.prohibition`. Deriving them means a third documented
    exception is a token edit rather than a code edit.

    Args:
        skill_dir: Path to the skill package directory.
        tokens: The parsed token tree.

    Returns:
        A mapping from uppercase hex to its sanctioned custom property, empty when the design
        engine is not importable.
    """
    scripts_dir = skill_dir / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    try:
        from kunumi_design.rules import prohibition_exception_css_vars
    except Exception:
        return {}
    return prohibition_exception_css_vars(tokens)


def validate_tokens(skill_dir: Path) -> list[str]:
    """Check that the token source of truth agrees with everything derived from it.

    The palette used to be duplicated across `tokens.json`, `kunumi-tokens.css`, and
    `brand-foundations.md` with nothing keeping them in sync. This check fails the build when
    they drift, and when a prohibited color reappears.

    Args:
        skill_dir: Path to the skill package directory.

    Returns:
        A list of human-readable error strings; empty when the token layer is consistent.
    """
    errors: list[str] = []
    tokens_path = skill_dir / "references" / "tokens.json"
    css_path = skill_dir / "assets" / "web" / "kunumi-tokens.css"
    foundations_path = skill_dir / "references" / "brand-foundations.md"

    if not tokens_path.exists():
        if skill_dir.name == TOKEN_OWNER:
            return [f"{skill_dir.name}: missing references/tokens.json"]
        return []

    try:
        tokens = json.loads(tokens_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{skill_dir.name}: tokens.json is not valid JSON: {exc}"]

    css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
    foundations = (
        foundations_path.read_text(encoding="utf-8") if foundations_path.exists() else ""
    )

    color = tokens.get("color", {})
    groups = ("institutional", "chart")
    for group in groups:
        for entry in color.get(group, {}).get("entries", []):
            hex_value = entry["hex"]
            css_var = entry["cssVar"]
            if css and f"{css_var}: {hex_value.lower()}" not in css.lower():
                errors.append(
                    f"{skill_dir.name}: {css_var} missing or mismatched in kunumi-tokens.css "
                    f"(tokens.json says {hex_value})"
                )
            if foundations and hex_value.upper() not in foundations.upper():
                errors.append(
                    f"{skill_dir.name}: {hex_value} ({group}) absent from brand-foundations.md"
                )

    # Black and white each survive only as one documented exception:
    # white as the raised card surface, black as the Instituto gradient terminus.
    if css:
        lowered = css.lower()
        exceptions = prohibition_exceptions(skill_dir, tokens)
        terminus = exceptions.get("#000000", "--kunumi-instituto-black")
        surface = exceptions.get("#FFFFFF", "--kunumi-surface-raised")

        black_hits = sum(lowered.count(b) for b in ("#000000", "#000 ", "#000;"))
        if black_hits and terminus not in lowered:
            errors.append(
                f"{skill_dir.name}: pure black used in kunumi-tokens.css without the documented "
                f"{terminus} exception (brandbook/instituto/cor, gradient terminus)"
            )
        if black_hits > 1:
            errors.append(
                f"{skill_dir.name}: black appears {black_hits} times in kunumi-tokens.css; "
                "only the Instituto gradient terminus may use it"
            )
        white_hits = css.lower().count("#ffffff")
        if white_hits and surface not in css:
            errors.append(
                f"{skill_dir.name}: white used in kunumi-tokens.css without the documented "
                f"{surface} exception"
            )
        if white_hits > 1:
            errors.append(
                f"{skill_dir.name}: white appears {white_hits} times in kunumi-tokens.css; "
                "only the raised-surface token may use it"
            )

    # The display face must never carry negative tracking.
    if css and "letter-spacing: -" in css:
        errors.append(
            f"{skill_dir.name}: negative letter-spacing in kunumi-tokens.css; the display face "
            "is tracked +3%"
        )

    if css:
        web_specs_path = skill_dir / "references" / "web-specs.md"
        web_specs = web_specs_path.read_text(encoding="utf-8") if web_specs_path.exists() else ""
        errors.extend(validate_web_layer(skill_dir.name, tokens, css, web_specs))

    return errors


WEB_LAYER_BLOCKS = ("layout", "motion", "elevation", "components", "icons", "logo", "digital")


def _css_block(css: str, header: str) -> str | None:
    """Return the body of the first `header { ... }` block, following nested braces.

    Args:
        css: The stylesheet source.
        header: Exact text preceding the opening brace, such as `.kunumi-theme-dark`.

    Returns:
        The text between the braces, or None when the header is absent.
    """
    match = re.search(re.escape(header) + r"\s*\{", css)
    if not match:
        return None
    depth, start = 1, match.end()
    for index in range(start, len(css)):
        if css[index] == "{":
            depth += 1
        elif css[index] == "}":
            depth -= 1
            if depth == 0:
                return css[start:index]
    return None


def _custom_properties(block: str) -> dict[str, str]:
    """Collect `--name: value` pairs from a CSS block, whitespace-collapsed."""
    block = re.sub(r"/\*.*?\*/", "", block, flags=re.DOTALL)
    return {
        name: " ".join(value.split())
        for name, value in re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", block)
    }


def _role_css(value: object, var_by_token: dict[str, str]) -> str:
    """Render one `color.semantic.roles` value in the form kunumi-tokens.css writes it."""
    if isinstance(value, str):
        return f"var({var_by_token[value]})"
    if isinstance(value, dict) and "mix" in value:
        return f"color-mix(in srgb, var({var_by_token[value['mix']]}) {value['percent']}%, transparent)"
    if isinstance(value, dict) and "hex" in value:
        return value["hex"].lower()
    raise ValueError(f"unreadable role value {value!r}")


def validate_web_layer(skill: str, tokens: dict, css: str, web_specs: str) -> list[str]:
    """Check the web product layer in `tokens.json` against its CSS and prose mirrors.

    Covers what the palette check above does not: product tonal steps, the spacing scale, the
    semantic roles in both themes, the grid at each breakpoint, and the authority every product
    block must carry so it can never pass for a brandbook value.

    Args:
        skill: Skill name, for error messages.
        tokens: The parsed token tree.
        css: The contents of `kunumi-tokens.css`.
        web_specs: The contents of `references/web-specs.md`, empty when absent.

    Returns:
        Human-readable error strings; empty when the web layer is consistent.
    """
    errors: list[str] = []
    lowered = css.lower()
    color = tokens.get("color", {})

    for entry in color.get("product", {}).get("entries", []):
        if f"{entry['cssVar']}: {entry['hex'].lower()}" not in lowered:
            errors.append(f"{skill}: {entry['cssVar']} missing or mismatched in kunumi-tokens.css")
        if web_specs and entry["hex"].upper() not in web_specs.upper():
            errors.append(f"{skill}: product step {entry['hex']} absent from web-specs.md")
    if color.get("product") and not web_specs:
        errors.append(f"{skill}: color.product exists but references/web-specs.md does not")

    for entry in tokens.get("geometry", {}).get("spacing", {}).get("entries", []):
        if f"{entry['cssVar']}: {entry['rem']}" not in css:
            errors.append(f"{skill}: {entry['cssVar']} missing or mismatched in kunumi-tokens.css")

    var_by_token = {
        entry["token"]: entry["cssVar"]
        for group in ("institutional", "product")
        for entry in color.get(group, {}).get("entries", [])
    }
    roles = color.get("semantic", {}).get("roles", [])
    root = _custom_properties(_css_block(css, ":root") or "")
    dark = _custom_properties(_css_block(css, ".kunumi-theme-dark") or "")
    auto_media = _css_block(css, "@media (prefers-color-scheme: dark)") or ""
    auto = _custom_properties(_css_block(auto_media, ".kunumi-theme-auto") or "")
    expected_dark: dict[str, str] = {}
    for role in roles:
        name = role["cssVar"]
        try:
            light_css = _role_css(role["light"], var_by_token)
            dark_css = _role_css(role["dark"], var_by_token)
        except (KeyError, ValueError) as exc:
            errors.append(f"{skill}: semantic role {role['role']} does not resolve: {exc}")
            continue
        if root.get(name) != light_css:
            errors.append(
                f"{skill}: :root {name} is {root.get(name)!r}, tokens.json says {light_css!r}"
            )
        if dark_css != light_css:
            expected_dark[name] = dark_css
    for label, block in ((".kunumi-theme-dark", dark), (".kunumi-theme-auto (dark)", auto)):
        actual = {name: value for name, value in block.items() if name in expected_dark}
        if actual != expected_dark:
            drift = sorted(set(actual.items()) ^ set(expected_dark.items()))
            errors.append(f"{skill}: {label} roles drift from color.semantic.roles: {drift}")
        stray = sorted(
            name for name in block
            if name.startswith("--kunumi-") and name not in {r["cssVar"] for r in roles}
        )
        if stray:
            errors.append(f"{skill}: {label} re-points non-role properties {stray} (ADR 0007)")

    layout = tokens.get("layout", {})
    breakpoint_px = {
        entry["token"]: entry["minWidthPx"]
        for entry in layout.get("breakpoints", {}).get("entries", [])
    }
    columns_var = layout.get("cssVars", {}).get("columns", "--kunumi-grid-columns")
    for grid in layout.get("grids", []):
        source = grid.get("fromBreakpoint")
        if source is None:
            block = root
            where = ":root"
        else:
            where = f"@media (min-width: {breakpoint_px.get(source)}px)"
            block = _custom_properties(_css_block(css, where) or "")
        if block.get(columns_var) != str(grid["columns"]):
            errors.append(
                f"{skill}: {where} sets {columns_var} to {block.get(columns_var)!r}, "
                f"tokens.json grid {grid['token']} says {grid['columns']}"
            )

    for key in WEB_LAYER_BLOCKS:
        if key in tokens and not tokens[key].get("authority"):
            errors.append(f"{skill}: tokens.json {key} carries no authority")
    for key in ("focusRing", "targetSize"):
        if key in tokens.get("interaction", {}) and not tokens["interaction"][key].get("authority"):
            errors.append(f"{skill}: tokens.json interaction.{key} carries no authority")

    return errors


def validate_no_figma_urls() -> list[str]:
    """Keep Figma file URLs out of the skills.

    The brandbook and library files are private; their keys live outside the repository.

    Returns:
        One error per file that names a Figma design or file URL.
    """
    errors: list[str] = []
    pattern = re.compile(r"figma\.com/(?:design|file)/")
    for path in SKILLS_DIR.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in (".md", ".json", ".css", ".html", ".py"):
            continue
        if pattern.search(path.read_text(encoding="utf-8", errors="replace")):
            errors.append(f"{path.relative_to(ROOT)}: names a Figma file URL; keep file keys out of the repo")
    return errors


def validate_reference_links(skill_dir: Path) -> list[str]:
    """Check that every `references/<file>` path named in SKILL.md exists.

    Args:
        skill_dir: Path to the skill package directory.

    Returns:
        A list of error strings for referenced files that are missing on disk.
    """
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return []

    errors: list[str] = []
    text = skill_md.read_text(encoding="utf-8")
    for name in sorted(set(re.findall(r"references/([A-Za-z0-9._-]+)", text))):
        if not (skill_dir / "references" / name).exists():
            errors.append(f"{skill_dir.name}: SKILL.md references missing references/{name}")
    return errors


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"

    if not skill_file.exists():
        return [f"{skill_dir}: missing SKILL.md"]

    metadata, metadata_errors = parse_frontmatter(skill_file)
    errors.extend(f"{skill_file}: {error}" for error in metadata_errors)

    name = metadata.get("name", "")
    description = metadata.get("description", "")

    if not name:
        errors.append(f"{skill_file}: missing frontmatter name")
    elif name != skill_dir.name:
        errors.append(f"{skill_file}: name {name!r} does not match folder {skill_dir.name!r}")
    elif not NAME_RE.fullmatch(name):
        errors.append(f"{skill_file}: name must be lowercase letters, digits, and hyphens only")

    if not description:
        errors.append(f"{skill_file}: missing frontmatter description")
    elif "TODO" in description or "[" in description:
        errors.append(f"{skill_file}: description still looks like a template placeholder")

    text = skill_file.read_text(encoding="utf-8")
    if "TODO" in text:
        errors.append(f"{skill_file}: contains TODO placeholder text")

    return errors


def main() -> int:
    if not SKILLS_DIR.exists():
        print("skills directory does not exist", file=sys.stderr)
        return 1

    skill_dirs = sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir())
    if not skill_dirs:
        print("skills directory is empty", file=sys.stderr)
        return 1

    errors: list[str] = []
    for skill_dir in skill_dirs:
        errors.extend(validate_skill(skill_dir))
        errors.extend(validate_reference_links(skill_dir))
        errors.extend(validate_tokens(skill_dir))
    errors.extend(validate_no_figma_urls())

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(skill_dirs)} skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
