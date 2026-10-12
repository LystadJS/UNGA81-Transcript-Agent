#!/usr/bin/env python3
"""Real Chromium synthetic QA of W2/W4 source-linked read models, offline only."""
from __future__ import annotations

import argparse
from pathlib import Path
from xml.etree import ElementTree

from playwright.sync_api import sync_playwright


def verify(page, kind: str, out: Path, path: Path) -> None:
    errors: list[str] = []
    remote: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("request", lambda request: remote.append(request.url)
            if request.url.startswith(("http://", "https://")) else None)
    page.goto(path.resolve().as_uri(), wait_until="load")
    page.locator("#w2-chart .ev-panel").wait_for()
    assert page.locator(".ev-panel").count() == 2
    assert page.locator("svg[role=img]").count() == 2
    assert "Two synthetic producers rendered" in page.locator("#qa-status").inner_text()
    assert "W2 WEIGHTED" in page.locator("#w2-chart").inner_text()
    assert "Inventory 6 meetings" in page.locator("#w2-chart").inner_text()
    assert "p0" in page.locator("#w4-chart").inner_text()
    assert "rigid_full_refit" in page.locator("#w4-chart").inner_text() or (
        "p0 → p1" in page.locator("#w4-chart").inner_text()
    )
    assert page.locator("#w4-chart [data-ev-inspect]").count() > 0
    # Source-inspection keyboard path: Tab-focusable native button and Enter.
    source = page.locator("#w2-chart [data-ev-inspect]").first
    source.focus()
    assert source.evaluate("(el) => document.activeElement === el")
    page.keyboard.press("Enter")
    readout = page.locator("#w2-chart .ev-inspector").inner_text()
    assert "W2 weighted conditional association" in readout
    assert "planned weight" in readout
    assert "fictional-unit-" in readout
    move = page.locator("#w4-chart [data-ev-inspect]").first
    move.focus()
    page.keyboard.press("Enter")
    assert "Synthetic fixture" in page.locator("#w4-chart .ev-inspector").inner_text()

    for name in ("w2", "w4"):
        for ext in ("svg", "html"):
            with page.expect_download() as item:
                page.get_by_role("button", name=f"Export {name.upper()} {ext.upper()}").click()
            file = out / f"{name}-{kind}.{ext}"
            item.value.save_as(str(file))
            assert file.is_file() and file.stat().st_size > 100
            if ext == "svg":
                assert ElementTree.parse(file).getroot().tag.endswith("svg")
            else:
                raw = file.read_text(encoding="utf-8")
                assert "<script" not in raw.lower()
                assert "Synthetic engineering" in raw
    page.screenshot(path=str(out / f"integrated-{kind}.png"), full_page=True)
    for name in ("w2", "w4"):
        page.locator(f"#{name}-chart .ev-panel").screenshot(
            path=str(out / f"{name}-{kind}.png")
        )
    width = page.evaluate("document.documentElement.scrollWidth")
    assert width <= page.viewport_size["width"] + 1, (
        f"Page level overflow on {kind}: {width}"
    )
    assert not errors, f"JavaScript errors: {errors}"
    assert not remote, f"Unexpected external network requests: {remote}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--browser", type=Path)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        kwargs = {"headless": True}
        if args.browser:
            kwargs["executable_path"] = str(args.browser)
        browser = playwright.chromium.launch(**kwargs)
        try:
            for name, width, height in (("desktop", 1440, 900), ("mobile", 390, 844)):
                page = browser.new_page(
                    viewport={"width": width, "height": height},
                    accept_downloads=True, device_scale_factor=1,
                    reduced_motion="reduce",
                )
                try:
                    verify(page, name, args.outdir, args.preview / "index.html")
                finally:
                    page.close()
        finally:
            browser.close()
    print("PASS: W2/W4 source-linked Chromium desktop/mobile, keyboard, exports, offline.")


if __name__ == "__main__":
    main()
