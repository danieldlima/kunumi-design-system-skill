#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.44"]
# ///
"""Headless render worker, isolated so the engine itself stays dependency-free.

Run as a subprocess, never imported. That is what lets `render.py` remain standard library only
while still driving a real browser: the parent process never has `playwright` in it. The worker
reads one JSON spec path from argv and writes one JSON result to stdout.

Chromium specifically, because `kunumi-tokens.css` uses `color-mix()` and `clamp()` throughout. A
renderer that does not support them would produce a different artifact than the one that ships,
and a render you cannot trust is worse than no render at all.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


MEASURE_JS = """
() => {
  const collect = (element) => {
    const rect = element.getBoundingClientRect();
    const style = window.getComputedStyle(element);
    return {
      tag: element.tagName.toLowerCase(),
      role: element.getAttribute('data-kunumi-role') || '',
      frame: element.getAttribute('data-kunumi-frame') || '',
      // Must mirror scan.Document.is_exempt_node: exemption flows down a subtree but stops
      // at a frame, because a frame is the deliverable brand surface. Taking the nearest of
      // either annotation gives the same answer as the Python walk.
      exempt: (() => {
        const nearest = element.closest('[data-kunumi-exempt], [data-kunumi-frame]');
        return nearest !== null && !nearest.hasAttribute('data-kunumi-frame');
      })(),
      id: element.id || '',
      classes: Array.from(element.classList),
      src: element.getAttribute('src') || '',
      x: rect.x, y: rect.y, width: rect.width, height: rect.height,
      // Line count must be measured, not derived: `line-height: normal` computes to the string
      // "normal", so height / lineHeight is unavailable exactly when a title is unstyled. A range
      // over the element's contents yields one rect per line fragment; distinct tops are lines.
      lineBoxes: (() => {
        try {
          const range = document.createRange();
          range.selectNodeContents(element);
          const tops = [];
          for (const rect of range.getClientRects()) {
            if (rect.width <= 0 || rect.height <= 0) continue;
            if (!tops.some((top) => Math.abs(top - rect.top) < 2)) tops.push(rect.top);
          }
          return tops.length;
        } catch (error) {
          return 0;
        }
      })(),
      fontFamily: style.fontFamily,
      fontSize: style.fontSize,
      lineHeight: style.lineHeight,
      letterSpacing: style.letterSpacing,
      textTransform: style.textTransform,
      color: style.color,
      backgroundColor: style.backgroundColor,
      visible: rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden'
                 && style.display !== 'none',
    };
  };
  const selector = '[data-kunumi-role], [data-kunumi-frame], img, svg';
  return Array.from(document.querySelectorAll(selector)).map(collect);
}
"""


def _launch(playwright):
    """Launch Chromium, preferring the bundled build and falling back to system Chrome.

    Playwright pins an exact Chromium revision and refuses to run against a different one, so a
    machine with an older cached revision would otherwise need a fresh ~130MB download just to
    take a screenshot. Any Chromium renders `color-mix()` and `clamp()` correctly, which is the
    only property this engine choice has to guarantee, so an installed Chrome is an equally valid
    engine and costs nothing.

    Args:
        playwright: An active sync Playwright context.

    Returns:
        A pair of (browser, identifier of what was launched).

    Raises:
        RuntimeError: When neither the bundled build nor a system channel can start, carrying
            both failures so the caller can report the real cause.
    """
    errors: list[str] = []
    try:
        return playwright.chromium.launch(), "bundled-chromium"
    except Exception as error:  # noqa: BLE001 - the message is the useful part
        errors.append(f"bundled chromium: {type(error).__name__}")

    for channel in ("chromium", "chrome", "msedge"):
        try:
            return playwright.chromium.launch(channel=channel), f"channel:{channel}"
        except Exception as error:  # noqa: BLE001
            errors.append(f"channel {channel}: {type(error).__name__}")

    raise RuntimeError(
        "No Chromium engine could be launched. Tried: " + "; ".join(errors)
        + ". Install one with: python -m playwright install chromium"
    )


def main() -> int:
    """Render one artifact and report screenshots plus measured geometry."""
    from playwright.sync_api import sync_playwright

    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    html = Path(spec["html"]).resolve()
    out_dir = Path(spec["outDir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    width, height = int(spec["width"]), int(spec["height"])
    scale = float(spec.get("scale", 2))
    slug = spec.get("slug") or html.stem

    pngs: list[str] = []
    skipped: list[str] = []
    result: dict[str, object] = {}

    with sync_playwright() as playwright:
        browser, launched_with = _launch(playwright)
        result["launchedWith"] = launched_with
        page = browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=scale,
        )
        if spec.get("reducedMotion"):
            page.emulate_media(reduced_motion="reduce")

        page.goto(html.as_uri(), wait_until="load")
        try:
            page.wait_for_function("document.fonts && document.fonts.status === 'loaded'",
                                  timeout=5000)
        except Exception:
            pass
        page.wait_for_timeout(int(spec.get("settleMs", 250)))

        measurements = page.evaluate(MEASURE_JS)

        frames = page.query_selector_all("[data-kunumi-frame]")
        skipped: list[str] = []
        if frames:
            for index, frame in enumerate(frames):
                name = frame.get_attribute("data-kunumi-frame") or f"frame{index + 1}"
                if not frame.is_visible():
                    # Screenshotting a hidden element would produce a blank PNG that looks like a
                    # rendered artifact, which is worse than reporting that it was not captured.
                    # A skip is not silent: it lands in `skippedFrames`, and on the artifact side
                    # `artifact.unprovenanced` plus the frame-to-file test mean an uncaptured frame
                    # can no longer be papered over with a screenshot - which is exactly how the
                    # repo's own previews went unrenderable for two weeks. See ADR 0016.
                    skipped.append(name)
                    continue
                target = out_dir / f"{slug}-{name}.png"
                frame.screenshot(path=str(target))
                pngs.append(str(target))
        else:
            target = out_dir / f"{slug}.png"
            page.screenshot(path=str(target), full_page=bool(spec.get("fullPage", False)))
            pngs.append(str(target))

        result["skippedFrames"] = skipped
        result["userAgent"] = page.evaluate("() => navigator.userAgent")
        browser.close()

    result.update(
        {
            "schema": "kunumi.render/v1",
            "schemaVersion": 1,
            "artifact": str(html),
            "canvas": {"width": width, "height": height, "scale": scale},
            "reducedMotion": bool(spec.get("reducedMotion")),
            "renders": pngs,
            "measurements": measurements,
        }
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
