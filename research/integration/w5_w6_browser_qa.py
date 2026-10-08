#!/usr/bin/env python3
"""Synthetic W5 browser acceptance with genuine desktop/mobile Chromium.

W5 Node/CDP suite verifies Worker, source/hash replay, cancellation and PCA/LSA
numeric parity. This is independent Playwright screenshot/keyboard inspection.
No network source, model download, real UN text or private data is allowed.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


@contextmanager
def serve(site: Path):
    server = ThreadingHTTPServer(("127.0.0.1", 0),
        functools.partial(QuietHandler, directory=str(site)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        thread.join(timeout=10)
        server.server_close()


def exercise(browser, origin: str, name: str, width: int, height: int,
             destination: Path) -> dict:
    context = browser.new_context(
        viewport={"width": width, "height": height}, accept_downloads=True,
        device_scale_factor=1, reduced_motion="reduce",
    )
    page = context.new_page()
    errors = []
    outside = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("request", lambda r: outside.append(r.url)
            if not r.url.startswith(origin + "/") and
            not r.url.startswith("data:") and
            not r.url.startswith("about:") else None)
    try:
        page.goto(origin + "/parallel/w05-browser/experimental/method-lab/index.html",
                  wait_until="load")
        assert page.locator("h1").inner_text() == "Research Method Lab"
        page.locator("#example").click()
        page.locator("#results:not([hidden])").wait_for(timeout=20000)
        assert page.locator("#observations tbody tr").count() == 5
        assert page.locator("#left option").count() == 3
        width_metrics = page.evaluate("""() => ({
            doc: document.documentElement.scrollWidth,
            viewport: window.innerWidth,
            heap: performance.memory ? performance.memory.usedJSHeapSize : null
        })""")
        assert width_metrics["doc"] <= width_metrics["viewport"] + 2, \
            f"{name} page horizontal overflow: {width_metrics}"
        inspector = page.locator("#observations tbody button").first
        inspector.focus()
        assert inspector.evaluate("(e) => document.activeElement === e")
        page.keyboard.press("Enter")
        assert "Text SHA-256" in page.locator("#inspection").inner_text()
        assert "not verified speaker" in page.locator("#inspection").inner_text().lower()
        assert "source" in page.locator("#inspection").inner_text().lower()
        page.screenshot(path=str(destination / f"w5-{name}.png"), full_page=True)
        page.locator("#authorize").check()
        assert page.locator("#results").is_hidden()
        assert page.locator("#export").is_disabled()
        assert not errors, f"{name} browser errors: {errors}"
        assert not outside, f"{name} unexpected remote traffic: {outside}"
        return {"viewport": name, "width": width, "height": height,
            "source_rows": 5, "method_models": 3,
            "keyboard_inspection": True, "stale_export_invalidated": True,
            "page_horizontal_overflow": False, "external_requests": 0,
            "uncaught_browser_errors": 0, "measured_js_heap_bytes": width_metrics["heap"]}
    finally:
        context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--browser-path", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    assert args.site.is_dir() and args.browser_path.is_file()
    out = args.outdir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    with serve(args.site) as origin, sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True, executable_path=str(args.browser_path.resolve()),
            args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            records = [
                exercise(browser, origin, name, width, height, out)
                for name, width, height in [
                    ("desktop", 1440, 900), ("mobile", 390, 844)
                ]
            ]
        finally:
            browser.close()
    evidence = {
        "schema": "un.w5.synthetic-browser-qa.v1",
        "fixture": "invented, no original source content",
        "publication_eligible": False, "heldout_transcripts_opened": 0,
        "viewports": records,
        "limitations": [
            "No private development, real transcript or MiniLM inference",
            "Performance timings not representative of 600-source/real workloads",
            "No public deployment or government stance claim",
        ],
    }
    (out/"w5-browser-qa.json").write_text(json.dumps(evidence, indent=2)+"\n",
                                          encoding="utf8")
    print("W5 real Chromium synthetic browser QA passed: " +
          json.dumps({"viewports":len(records),"external_requests":0}))


if __name__ == "__main__":
    main()
