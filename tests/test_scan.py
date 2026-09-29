"""Scanner tests, concentrated on the negative controls.

Each of these corresponds to a construct that exists in the repository's own CSS and that a naive
linter reports wrongly. They are the difference between a tool that gets used and one that gets
muted.
"""

from __future__ import annotations


def test_space_separated_rgb_with_alpha_resolves_to_chumbo():
    from kunumi_design import scan

    assert scan.normalize_color("rgb(28 33 39 / 0.42)") == "#1C2127"


def test_short_hex_expands():
    from kunumi_design import scan

    assert scan.normalize_color("#abc") == "#AABBCC"


def test_color_mix_resolves_to_its_base_token():
    from kunumi_design import scan

    bases = scan.color_mix_bases("color-mix(in srgb, var(--kunumi-gelo) 72%, transparent)")
    assert bases == ("--kunumi-gelo",)


def test_gradient_stops_are_all_collected():
    from kunumi_design import scan

    colors = scan.find_colors("linear-gradient(90deg, #FF9516 5.2%, #000000 93.6%)")
    assert colors == ("#FF9516", "#000000")


def test_selectors_survive_parsing_intact():
    from kunumi_design import scan

    declarations = scan.parse_css(".instituto-cover .slide__logo { filter: invert(1); }", "x.css")
    assert declarations[0].selector == ".instituto-cover .slide__logo"
    assert declarations[0].prop == "filter"


def test_reduced_motion_declarations_are_marked():
    from kunumi_design import scan

    css = "@media (prefers-reduced-motion: reduce) { * { transition-duration: 1ms; } }"
    declarations = scan.parse_css(css, "x.css")
    assert declarations[0].in_reduced_motion is True


def test_keyframe_declarations_are_marked():
    from kunumi_design import scan

    css = "@keyframes drift { from { transform: scale(1.05); } }"
    declarations = scan.parse_css(css, "x.css")
    assert declarations[0].in_keyframes is True


def test_comments_do_not_shift_line_numbers():
    from kunumi_design import scan

    css = "/* a\nb\nc */\n.x { color: #F04E44; }"
    declarations = scan.parse_css(css, "x.css")
    assert declarations[0].line == 4


def test_em_lengths_are_not_converted():
    """`em` is relative to the element's own font size, which the static pass cannot resolve."""
    from kunumi_design.checks import to_px

    assert to_px("0.15em") is None
    assert to_px("1.5rem") == 24.0
    assert to_px("clamp(1rem, 2vw, 3rem)") is None
