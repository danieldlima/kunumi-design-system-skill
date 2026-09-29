"""Derivation tests: the guard on "derive from tokens.json, do not hardcode".

Each test mutates an in-memory copy of the token tree and asserts the rule set follows. If a
value is ever transcribed into Python, one of these fails.
"""

from __future__ import annotations


def test_palette_follows_a_changed_institutional_hex(mutable_tokens):
    from kunumi_design import rules

    mutable_tokens["color"]["institutional"]["entries"][0]["hex"] = "#ABCDEF"
    palette = rules.derive_palette(mutable_tokens)
    assert "#ABCDEF" in palette.institutional
    assert "#F04E44" not in palette.institutional


def test_spacing_scale_follows_a_new_step(mutable_tokens):
    from kunumi_design import rules

    mutable_tokens["geometry"]["spacing"]["entries"].append(
        {"token": "space-44", "px": 176, "rem": "11rem", "cssVar": "--kunumi-space-44",
         "figmaVariable": "space/176"}
    )
    geometry = rules.derive_geometry(mutable_tokens)
    assert 176.0 in geometry.spacing_px


def test_radii_follow_the_token_values(mutable_tokens):
    from kunumi_design import rules

    mutable_tokens["geometry"]["radius"]["card"] = "12px"
    geometry = rules.derive_geometry(mutable_tokens)
    assert geometry.radii_px == frozenset({12.0, 4.0})


def test_line_height_ranges_are_parsed_from_percentages(tokens):
    from kunumi_design import rules

    typography = rules.derive_typography(tokens)
    assert typography.line_height["display"] == (1.10, 1.40)
    assert typography.line_height["body"] == (1.40, 1.75)


def test_prohibition_exceptions_come_from_the_token_tree(tokens):
    """The function `validate-skills.py` should use instead of its hardcoded literals."""
    from kunumi_design import rules

    mapping = rules.prohibition_exception_css_vars(tokens)
    assert mapping["#FFFFFF"] == "--kunumi-surface-raised"
    assert mapping["#000000"] == "--kunumi-instituto-black"


def test_brandbook_geometry_is_exempt_from_the_spacing_scale(tokens):
    """geometry.cardPaddingNote states 30px deliberately sits off the 4px scale."""
    from kunumi_design import rules

    geometry = rules.derive_geometry(tokens)
    assert geometry.card_padding_px == 30.0
    assert 30.0 not in geometry.spacing_px
    assert 30.0 in geometry.brandbook_px


def test_display_tracking_allows_the_menu_variable(tokens):
    """Cabecalho/Menu is tracked +10%, and that is the brandbook's own value."""
    from kunumi_design import rules

    typography = rules.derive_typography(tokens)
    menu = next(v for v in typography.variables if v["name"] == "Cabecalho/Menu")
    assert menu["letterSpacingPercent"] == 10
    assert typography.display_tracking == 0.03


def test_instituto_gradient_keeps_its_measured_stops(tokens):
    from kunumi_design import rules

    stops = rules.derive_instituto_gradient(tokens)
    assert len(stops) == 7
    assert stops[0].centre_percent == 5.2
    assert stops[-1].hex == "#000000"
    urucum = next(stop for stop in stops if stop.token == "urucum")
    assert urucum.centre_percent == 35.0


def test_breakpoints_follow_the_layout_tokens(mutable_tokens):
    from kunumi_design import rules

    mutable_tokens["layout"]["breakpoints"]["entries"].append({"token": "xl", "minWidthPx": 1920})
    layout = rules.derive_layout(mutable_tokens)
    assert layout.breakpoints_px == frozenset({768.0, 1440.0, 1920.0})
    assert layout.container_px == 1248.0


def test_semantic_vars_come_from_the_role_table(mutable_tokens):
    """The semantic set used to be a Python literal; it is now color.semantic.roles."""
    from kunumi_design import rules

    mutable_tokens["color"]["semantic"]["roles"].append(
        {"role": "canvas", "cssVar": "--kunumi-canvas", "light": "gelo", "dark": "chumbo"}
    )
    palette = rules.derive_palette(mutable_tokens)
    assert "--kunumi-canvas" in palette.semantic_vars
    assert "--kunumi-on-accent" in palette.semantic_vars


def test_product_steps_are_approved_and_mapped(mutable_tokens):
    from kunumi_design import rules

    mutable_tokens["color"]["product"]["entries"].append(
        {"token": "urucum-800", "hex": "#8F2B24", "cssVar": "--kunumi-urucum-800"}
    )
    palette = rules.derive_palette(mutable_tokens)
    assert "#8F2B24" in palette.approved
    assert palette.var_by_hex["#BC392F"] == "--kunumi-urucum-700"


def test_logo_minimum_and_og_size_follow_the_tokens(mutable_tokens):
    from kunumi_design import rules

    mutable_tokens["logo"]["minHeight"]["positiveRgbPx"] = 32
    mutable_tokens["digital"]["og"]["widthPx"] = 1600
    interaction = rules.derive_interaction(mutable_tokens)
    assert interaction.logo_min_px == 32.0
    assert interaction.og_size_px == (1600, 630)
    assert interaction.target_min_px == 24.0
