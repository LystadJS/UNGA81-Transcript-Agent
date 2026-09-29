"""Optional local PDF fallback, not required for Shiny or email generation.

Used only when pagedown is unavailable. Requires an existing approved installation
of Python + Playwright and a local Chromium-family browser. Downloads nothing.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("browser", type=Path)
    args = parser.parse_args()
    source = args.input.resolve(strict=True)
    output = args.output.resolve()
    browser_path = args.browser.resolve(strict=True)
    if source.suffix.lower() not in {".htm", ".html"} or output.suffix.lower() != ".pdf":
        raise ValueError("Expected a local HTML input and PDF output.")
    if source.parent != output.parent:
        raise ValueError("The PDF must be written beside this run's HTML.")
    from playwright.sync_api import sync_playwright

    container_mode = os.environ.get("UN_READOUT_BROWSER_NO_SANDBOX") == "1"
    extra = ["--disable-dev-shm-usage"]
    if container_mode:
        extra += ["--no-zygote", "--single-process"]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=str(browser_path), headless=True,
            chromium_sandbox=not container_mode, args=extra, timeout=15000,
        )
        try:
            context = browser.new_context(java_script_enabled=False)
            page = context.new_page()
            page.route("**/*", lambda route: route.continue_()
                       if route.request.url.startswith("data:") else route.abort())
            # The report is self-contained. Load bytes rather than navigating to a
            # file URL; do not grant the browser access to other local files.
            page.set_content(source.read_text(encoding="utf-8"),
                             wait_until="load", timeout=15000)
            page.pdf(path=str(output), print_background=True,
                     prefer_css_page_size=True, display_header_footer=False)
        finally:
            browser.close()
    if not output.is_file() or output.stat().st_size < 1000:
        raise RuntimeError("The browser did not produce a nonempty PDF.")
    with output.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            raise RuntimeError("PDF signature verification failed.")
    print("PDF created with the optional local Playwright fallback.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"PDF fallback failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
