#!/usr/bin/env python3
"""Real Chromium source/weight QA of native W2 synthetic exports in the coordinator research page.

No UN transcript text, outside source requests, publication or public deployment.
"""
import argparse
from contextlib import contextmanager
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading

from playwright.sync_api import sync_playwright


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass


@contextmanager
def serve(directory):
    server = ThreadingHTTPServer(("127.0.0.1", 0),
        functools.partial(Quiet, directory=str(directory)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        thread.join(timeout=10)
        server.server_close()


def upload(page, folder):
    page.locator("#research-w2-sidecar").set_input_files(str(folder / "consensus-v1.json"))
    page.locator("#research-w2-v1").set_input_files(str(folder / "standardized-interchange-v1.json"))
    page.locator("#research-w2-import").click()


def verify(browser, base, fixture, out, name, width, height):
    context = browser.new_context(viewport={"width": width, "height": height},
                                  reduced_motion="reduce")
    page = context.new_page()
    errors, external = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("request", lambda request: external.append(request.url)
            if not request.url.startswith(base + "/") and
            not request.url.startswith("about:") and
            not request.url.startswith("data:") else None)
    try:
        page.goto(base + "/research.html", wait_until="load")
        assert page.locator("#w2 h2").inner_text() == "Inspect native W2 weighted consensus"
        assert page.locator("script[src='research-consensus.js']").count() == 1
        upload(page, fixture)
        page.wait_for_function(
            "() => document.getElementById('research-w2-status').textContent.includes('verified in this browser')",
            timeout=15000)
        summary=page.locator("#research-w2-summary").inner_text()
        report=json.loads((fixture/"consensus-v1.json").read_text())
        assert str(len(report["observation_ids"])) in summary
        assert "weighted" in summary.lower()
        n=len(report["observation_ids"])
        assert page.locator("#research-w2-matrix tbody tr").count() == n
        assert page.locator("#research-w2-matrix .research-w2-pair").count() == n*(n-1)
        first=page.locator("#research-w2-matrix .research-w2-pair").first
        first.focus()
        page.keyboard.press("Enter")
        detail=page.locator("#research-w2-inspection").inner_text()
        assert "Weighted coassigned" in detail
        assert "Raw coassigned" in detail
        assert "Original synthetic observation" in detail
        assert "W2 values are imported without recalculation" in detail

        # Changing either file invalidates all previous source/fit results.
        page.locator("#research-w2-sidecar").set_input_files([])
        assert page.locator("#research-w2-matrix .research-w2-pair").count() == 0
        assert "No source-validated" in page.locator("#research-w2-summary").inner_text()

        with tempfile.TemporaryDirectory() as td:
            directory=Path(td)
            bad=json.loads((fixture/"consensus-v1.json").read_text())
            changed=next(p for p in bad["pairs"] if p["association"] is not None
                         and p["observation_a"] != p["observation_b"])
            changed["association"]=1.0 if changed["association"] == 0 else 0.0
            (directory/"consensus-v1.json").write_text(json.dumps(bad)+"\n")
            page.locator("#research-w2-sidecar").set_input_files(str(directory/"consensus-v1.json"))
            page.locator("#research-w2-import").click()
            page.wait_for_function(
                "() => document.getElementById('research-w2-status').textContent.includes('W2 import refused')",
                timeout=15000)
            assert page.locator("#research-w2-matrix .research-w2-pair").count() == 0

        # A restored, checked native W2 import must not inherit stale failure state.
        upload(page, fixture)
        page.wait_for_function(
            "() => document.getElementById('research-w2-status').textContent.includes('verified in this browser')",
            timeout=15000)
        assert page.locator("#research-w2-matrix .research-w2-pair").count() > 0
        assert "W4's mixed historical inventory" in page.locator("#restrictions").locator("..").inner_text()
        assert page.evaluate("document.documentElement.scrollWidth") <= width + 2
        assert not errors, f"Uncaught browser exceptions: {errors}"
        assert not external, f"Unexpected third-party requests: {external}"
        page.screenshot(path=str(out / ("w2-"+name+"-synthetic.png")), full_page=True)
        return {"viewport":name,"width":width,"height":height,
                "eligible":n,"pair_cells":n*(n-1),"keyboard_pair_inspection":True,
                "source_and_weighted_denominators":True,
                "change_invalidates_export":True,
                "tamper_refused":True,
                "external_requests":0,"exceptions":0,"page_overflow":False}
    finally:
        context.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--site",type=Path,required=True)
    p.add_argument("--fixtures",type=Path,required=True)
    p.add_argument("--browser",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    assert args.site.is_dir() and args.browser.is_file()
    for filename in ["consensus-v1.json","standardized-interchange-v1.json"]:
        assert (args.fixtures / filename).is_file()
    args.output.mkdir(parents=True,exist_ok=False)
    with serve(args.site) as base,sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=str(args.browser.resolve()),
                                   args=["--no-sandbox","--disable-dev-shm-usage"])
        try:
            receipts=[verify(browser,base,args.fixtures,args.output,n,w,h)
                      for n,w,h in [("desktop",1440,900),("mobile",390,844)]]
        finally:
            browser.close()
    receipt={"schema":"un.coord-w2-browser-qa.v1","evaluation_role":"engineering_only",
             "publication_eligible":False,"holdout_access":False,
             "source":"native W2 fictional synthetic fixtures", "viewports":receipts}
    (args.output/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("PASS: native W2 source-bound weighted consensus, desktop/mobile, no external requests")


if __name__=="__main__":
    main()
