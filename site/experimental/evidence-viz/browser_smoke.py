#!/usr/bin/env python3
"""Local-only browser acceptance and screenshot capture.

Requires: pip install playwright && python -m playwright install chromium
Run from anywhere:
    python site/experimental/evidence-viz/browser_smoke.py
No UN transcripts, external AI service, or HTTP source is contacted.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from xml.etree import ElementTree as ET

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
VIEWS = ("consensus", "country-theme", "network", "longitudinal")


def verify(page, viewport: str, output: Path) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.goto((HERE / "index.html").as_uri())
    page.locator(".ev-panel").first.wait_for(timeout=10000)
    assert page.locator(".ev-panel").count() == 4
    assert page.locator('[data-ev-inspect]').count() >= 20
    assert page.locator("svg[role=img]").count() == 4
    assert page.get_by_text("SYNTHETIC / NOT FOR PUBLICATION").count() == 1

    # Native button interaction, Enter key, and source ledger inspectability.
    button = page.locator('[data-ev-inspect]').first
    button.focus()
    assert button.evaluate("(el) => document.activeElement === el")
    page.keyboard.press("Enter")
    assert "Selected evidence" in page.locator(".ev-inspector").first.inner_text()
    assert "Synthetic fixture" in page.locator(".ev-inspector").first.inner_text()

    # Both offline exports must be parsable; no remote resource is needed.
    with page.expect_download() as svg_download:
        page.get_by_role("button", name="Export SVG").first.click()
    svg_path = output / ("consensus-" + viewport + "-export.svg")
    svg_download.value.save_as(str(svg_path))
    xml = ET.parse(svg_path).getroot()
    assert xml.tag.endswith("svg")
    with page.expect_download() as html_download:
        page.get_by_role("button", name="Export static HTML").first.click()
    saved_html = output / ("consensus-" + viewport + "-export.html")
    html_download.value.save_as(str(saved_html))
    assert "<script" not in saved_html.read_text(encoding="utf-8").lower()

    # Capture actual browser viewports and each chart with its controls.
    page.screenshot(path=str(output / ("suite-" + viewport + ".png")), full_page=True)
    for kind in VIEWS:
        page.locator('[data-ev-kind="' + kind + '"]').screenshot(
            path=str(output / (kind + "-" + viewport + ".png"))
        )

    # Real empty frame rather than simply hiding otherwise populated results.
    page.locator("#scenario").select_option("empty")
    assert page.locator(".ev-panel").count() == 4
    assert page.locator(".ev-withheld").count() == 4
    assert "Frame 0" in page.locator(".ev-provenance").first.inner_text()

    # Failure and withholding are explicit and do not expose old graphics.
    for status in ("withheld", "failed"):
        page.locator("#scenario").select_option(status)
        assert page.locator(".ev-withheld").count() == 4
        assert page.locator('[data-ev-inspect]').count() == 0

    # Entire page fits the viewport; each large SVG has a local horizontal
    # scroll region on small devices instead of forcing page-level overflow.
    width = page.evaluate("document.documentElement.scrollWidth")
    assert width <= page.viewport_size["width"] + 1, (
        f"Page-level overflow on {viewport}: {width}"
    )
    assert not errors, f"Uncaught browser errors on {viewport}: {errors}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, default=HERE / "previews" / "browser")
    parser.add_argument("--browser-path", type=Path, default=None,
                        help="Use an existing local Chromium/Chrome binary (no browser download).")
    args = parser.parse_args()
    output = args.outdir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path=str(args.browser_path.resolve()) if args.browser_path else None,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        try:
            for name, width, height in (
                ("desktop", 1440, 900),
                ("mobile", 390, 844),
            ):
                page = browser.new_page(
                    viewport={"width": width, "height": height},
                    accept_downloads=True,
                    device_scale_factor=1,
                    reduced_motion="reduce",
                )
                try:
                    verify(page, name, output)
                finally:
                    page.close()
        finally:
            browser.close()
    print("PASS: desktop/mobile, keyboard, exports, empty/withheld/failed; screenshots:", output)


if __name__ == "__main__":
    main()
