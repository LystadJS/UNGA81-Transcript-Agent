#!/usr/bin/env python3
"""Real Chromium C5 synthetic-only browser QA. No original UN source access."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import functools
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
from xml.etree import ElementTree

from playwright.sync_api import sync_playwright

W4_FILES = [
    "SHA256.json", "w4-source-panel.json", "w4-analysis.json",
    "w4-envelope.json", "w4-panel.json"
]


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return


@contextmanager
def serve(directory):
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(Quiet, directory=str(directory))
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        thread.join(timeout=10)
        server.server_close()


def w2_upload(page, folder):
    page.locator("#research-w2-sidecar").set_input_files(
        str(folder / "w2-consensus.json"))
    page.locator("#research-w2-v1").set_input_files(
        str(folder / "w2-v1-interchange.json"))
    page.locator("#research-w2-import").click()
    page.wait_for_function(
        "() => document.getElementById('research-w2-status').textContent.includes('verified in this browser')",
        timeout=20000
    )


def w4_upload(page, folder):
    page.locator("#research-w4-files").set_input_files(
        [str(folder / f) for f in W4_FILES])
    page.locator("#research-w4-import").click()


def wait_w4(page):
    page.wait_for_function(
        "() => document.getElementById('research-w4-status').textContent.startsWith('Verified original W4 frozen basis')",
        timeout=25000,
    )


def download_and_verify(page, out: Path, button: str, name: str, ext: str):
    with page.expect_download(timeout=20000) as downloaded:
        page.locator(button).click()
    dest = out / (name + "." + ext)
    downloaded.value.save_as(str(dest))
    assert dest.stat().st_size > 150
    if ext == "svg":
        assert ElementTree.parse(dest).getroot().tag.endswith("svg")
    else:
        content = dest.read_text(encoding="utf-8")
        assert "<script" not in content.lower()
        assert "source" in content.lower()
    return dest.name


def make_invalid_w4_fixture(folder: Path, target: Path):
    """Recalculate manifest after tampering, to exercise semantic refusal."""
    target.mkdir()
    content = {}
    for filename in W4_FILES[1:]:
        content[filename] = (folder / filename).read_bytes()
    panel = json.loads(content["w4-panel.json"])
    point = next(
        p for a in panel["actors"] for p in a["positions"]
        if p["status"] == "observed"
    )
    point["xy"][0] += 1
    content["w4-panel.json"] = (
        json.dumps(panel, indent=2) + "\n"
    ).encode()
    for filename, data in content.items():
        (target / filename).write_bytes(data)
    hashes = {filename: hashlib.sha256(data).hexdigest()
              for filename, data in content.items()}
    (target / "SHA256.json").write_text(json.dumps(hashes) + "\n")


def verify(browser, base: str, w2: Path, w4: Path, pinned: Path,
           missing: Path, out: Path, device: str, width: int, height: int):
    context = browser.new_context(
        viewport={"width": width, "height": height},
        reduced_motion="reduce", accept_downloads=True, device_scale_factor=1,
    )
    page = context.new_page()
    errors, outside = [], []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.on("request", lambda req: outside.append(req.url)
            if not req.url.startswith(base + "/")
            and not req.url.startswith(("about:", "data:")) else None)
    try:
        page.goto(base + "/research.html", wait_until="load")
        assert page.locator("script[src='research-evidence-renderer.js']").count() == 1
        assert page.locator("script[src='research-evidence.js']").count() == 1
        assert page.locator("#research-w2-evidence-chart .ev-panel").count() == 0
        assert page.locator("#research-w4-chart .ev-panel").count() == 0
        assert page.locator("#research-w2-evidence-svg").is_disabled()

        w2_upload(page, w2)
        page.locator("#research-w2-evidence").evaluate("(el) => el.open=true")
        page.wait_for_function(
            "() => document.querySelector('#research-w2-evidence-chart .ev-panel') !== null",
            timeout=20000,
        )
        assert "W2 WEIGHTED" in page.locator(
            "#research-w2-evidence-chart svg").first.inner_text()
        assert "25" in page.locator(
            "#research-w2-evidence-chart .ev-provenance").inner_text()
        assert page.locator("#research-w2-evidence-chart [data-ev-inspect]").count() > 300
        source = page.locator("#research-w2-evidence-chart [data-ev-inspect]").first
        source.focus()
        assert source.evaluate("(el) => document.activeElement === el")
        page.keyboard.press("Enter")
        detail = page.locator(
            "#research-w2-evidence-chart .ev-inspector").inner_text()
        assert "assigned-both weight" in detail
        assert "planned weight" in detail
        assert "Original" not in detail or "W2" in detail
        assert "Method-family planned-weight audit" in page.locator(
            "#research-w2-evidence-chart").inner_text()
        download_and_verify(page, out, "#research-w2-evidence-svg",
                            "w2-" + device, "svg")
        download_and_verify(page, out, "#research-w2-evidence-html",
                            "w2-" + device, "html")

        # A changed file is no longer a validated input: clear C5 and export.
        page.locator("#research-w2-sidecar").set_input_files([])
        assert page.locator("#research-w2-evidence-chart .ev-panel").count() == 0
        assert page.locator("#research-w2-evidence-svg").is_disabled()
        w2_upload(page, w2)
        page.wait_for_function(
            "() => document.querySelector('#research-w2-evidence-chart .ev-panel') !== null",
            timeout=20000,
        )

        w4_upload(page, w4)
        wait_w4(page)
        assert page.locator("#research-w4-chart [data-ev-inspect]").count() >= 10
        assert "rigid_full_refit" in page.locator(
            "#research-w4-chart").inner_text() or (
                "p0 → p1" in page.locator("#research-w4-chart").inner_text()
            )
        w4source = page.locator("#research-w4-chart [data-ev-inspect]").first
        w4source.focus()
        page.keyboard.press("Enter")
        assert "Synthetic fixture" in page.locator(
            "#research-w4-chart .ev-inspector").inner_text()
        download_and_verify(page, out, "#research-w4-svg",
                            "w4-" + device, "svg")
        download_and_verify(page, out, "#research-w4-html",
                            "w4-" + device, "html")

        # Saved pinned-transform alignment does NOT invent new anchor fits.
        w4_upload(page, pinned)
        wait_w4(page)
        assert "identity_pinned_transform" in page.locator(
            "#research-w4-chart").inner_text() or (
                "p0 → p1" in page.locator("#research-w4-chart").inner_text()
            )
        # One unavailable source series may contain many missing observations.
        w4_upload(page, missing)
        wait_w4(page)
        assert "missing 1" in page.locator(
            "#research-w4-chart .ev-provenance").inner_text()

        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "forged"
            make_invalid_w4_fixture(w4, bad)
            w4_upload(page, bad)
            page.wait_for_function(
                "() => document.getElementById('research-w4-status').textContent.includes('C5 evidence refused')",
                timeout=20000,
            )
            assert page.locator("#research-w4-chart .ev-panel").count() == 0
            assert page.locator("#research-w4-svg").is_disabled()
            assert page.locator("#research-w4-html").is_disabled()
        w4_upload(page, w4)
        wait_w4(page)
        assert page.locator("#research-w4-chart .ev-panel").count() == 1

        assert page.evaluate("document.documentElement.scrollWidth") <= width + 2, (
            f"C5 caused {device} page-level overflow"
        )
        assert not errors, f"Uncaught browser errors: {errors}"
        assert not outside, f"Remote/out-of-origin browser requests: {outside}"
        page.screenshot(path=str(out / f"c5-{device}-full.png"), full_page=True)
        page.locator("#research-w2-evidence-chart .ev-panel").screenshot(
            path=str(out / f"w2-{device}-panel.png"))
        page.locator("#research-w4-chart .ev-panel").screenshot(
            path=str(out / f"w4-{device}-panel.png"))
        return {
            "viewport": device, "width": width, "height": height,
            "w2_weighted_source": True, "w4_original_alignment": True,
            "w4_pinned_accepted": True, "w4_missing_family_accepted": True,
            "checksum_and_semantic_tampering_refused": True,
            "svg_html_verified": True, "keyboard_inspection": True,
            "external_requests": 0, "page_errors": 0, "page_overflow": False,
        }
    finally:
        context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--w2", type=Path, required=True)
    parser.add_argument("--w4", type=Path, required=True)
    parser.add_argument("--pinned", type=Path, required=True)
    parser.add_argument("--missing", type=Path, required=True)
    parser.add_argument("--browser", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert args.site.is_dir() and args.browser.is_file()
    for f in W4_FILES:
        assert (args.w4/f).is_file()
        assert (args.pinned/f).is_file()
        assert (args.missing/f).is_file()
    for f in ("w2-consensus.json", "w2-v1-interchange.json"):
        assert (args.w2/f).is_file()
    args.output.mkdir(parents=True, exist_ok=False)
    with serve(args.site) as base, sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True, executable_path=str(args.browser.resolve()),
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        try:
            results = [
                verify(browser, base, args.w2, args.w4, args.pinned,
                       args.missing, args.output, name, width, height)
                for name, width, height in (
                    ("desktop", 1440, 900), ("mobile", 390, 844)
                )
            ]
        finally:
            browser.close()
    receipt = {
        "schema": "un.c5.browser-qa.synthetic.v1",
        "evaluation_role": "engineering_only",
        "publication_eligible": False,
        "heldout_transcripts_opened": 0,
        "viewports": results,
    }
    (args.output/"receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n")
    print("PASS: W2/W4 C5 local source-backed desktop/mobile, exports, no remote requests")


if __name__ == "__main__":
    main()
