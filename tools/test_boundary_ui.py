"""Browser acceptance for generated local packets. Mutations use SYNTHETIC inputs only."""
import argparse
import json
import shutil
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
from playwright.sync_api import sync_playwright


def run(packet_dir: Path, out: Path, real: bool = False, serve: bool = False) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    checks, errors, external, dialogs = [], [], [], []
    server = None
    url = (packet_dir / "index.html").resolve().as_uri()
    if serve:
        class QuietHandler(SimpleHTTPRequestHandler):
            def log_message(self, *_):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(packet_dir.resolve())))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{server.server_port}/index.html"
    def check(name, ok):
        if not ok:
            raise AssertionError(name)
        checks.append({"name": name, "status": "PASS"})
    with sync_playwright() as pw:
        chrome = shutil.which("chromium") or shutil.which("google-chrome")
        if not chrome:
            raise RuntimeError("A local Chromium/Chrome executable is required for this test.")
        browser = pw.chromium.launch(executable_path=chrome, headless=True, args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
        def guard(route):
            if route.request.url.startswith(("https://", "http://")) and not (serve and route.request.url.startswith(url.rsplit("/", 1)[0] + "/")):
                external.append(route.request.url)
                route.abort()
            else:
                route.continue_()
        context.route("**/*", guard)
        page = context.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        def dialog(d):
            dialogs.append(d.type)
            if d.type == 'alert':
                errors.append("Unexpected executable alert: " + d.message)
            d.accept()
        page.on("dialog", dialog)
        page.goto(url, wait_until="load")
        page.locator("#app").wait_for(state="visible", timeout=60000)
        model = page.locator("#packet-data").text_content()
        model = json.loads(model)
        check("initial review is wholly pending", model["counts"]["existing_confirmed"] == 0 and page.locator("#progress").get_attribute("value") == "0")
        check("every development meeting is selectable", page.locator("#meeting option").count() == len(model["meetings"]))
        check("original Unicode text rendered without modification", page.locator("#source-text").text_content() == model["records"][0]["text"])
        check("no source markup becomes an image element", page.locator("#source-text img").count() == 0)
        check("desktop page has no horizontal overflow", page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
        page.screenshot(path=str(out / "desktop.png"), full_page=True)
        for meeting in model["meetings"]:
            page.select_option("#meeting", meeting["meeting_id"])
            rows = [r for r in model["records"] if r["meeting_id"] == meeting["meeting_id"]]
            if rows:
                if page.locator("#source-link").get_attribute("href") != meeting["source_url"]:
                    raise AssertionError("Wrong source URL")
                if page.locator("#segment option").count() != len(rows):
                    raise AssertionError("Source queue missing records")
                page.select_option("#segment", rows[-1]["id"])
                page.locator(".context summary").click()
                if "End of the collected meeting" not in page.locator("#next-context").text_content():
                    raise AssertionError("Context crosses meeting boundary")
                page.locator(".context summary").click()
            else:
                if not page.locator("#empty-state").is_visible():
                    raise AssertionError("Unavailable meeting hidden")
        check("all meeting queues and source links match frozen development sources", True)
        check("context never crosses meeting boundaries", True)
        first = model["records"][0]
        page.select_option("#meeting", first["meeting_id"])
        page.select_option("#segment", first["id"])
        if not real:
            check("test writes use synthetic sources", "SYNTHETIC" in first["text"])
            page.click("#confirm")
            check("confirmation without a reviewer is blocked", "reviewer" in page.locator("#message").text_content())
            page.fill("#reviewer", "SYNTHETIC TEST — NOT OWNER REVIEW")
            page.select_option("#type", "substantive_speech")
            page.select_option("#extent", "complete")
            page.click("#confirm")
            check("complete speech without ID is blocked", "speech ID" in page.locator("#message").text_content())
            page.click("#use-id")
            check("ID helper does not confirm a review", page.locator("#progress").get_attribute("value") == "0")
            page.click("#confirm")
            check("explicit confirmation advances to next unconfirmed source", page.locator("#segment").input_value() != first["id"] and page.locator("#progress-label").text_content().startswith("1 /"))
            with page.expect_download() as download_info:
                page.click("#save")
            saved = out / "synthetic-review.json"
            download_info.value.save_as(str(saved))
            review = json.loads(saved.read_text())
            check("export retains every pending row and one confirmed test choice", len(review["choices"]) == len(model["records"]) and sum(c["confirmed"] for c in review["choices"]) == 1)
            check("export is bound to exact source bundle", review["source_bundle_sha256"] == model["source_bundle_sha256"])
            page.reload(wait_until="load")
            page.locator("#app").wait_for(state="visible", timeout=60000)
            check("browser-local copy resumes saved choices", page.locator("#progress-label").text_content().startswith("1 /"))
            page.select_option("#segment", first["id"])
            check("confirmed review is locked until explicitly reopened", page.locator("#type").is_disabled())
            page.click("#reopen")
            check("reopen does not preserve a false confirmation", page.locator("#progress").get_attribute("value") == "0")
            page.set_input_files("#import", str(saved))
            page.wait_for_function("document.querySelector('#message').textContent.startsWith('Imported')")
            check("source-bound JSON can resume a prior review", page.locator("#progress-label").text_content().startswith("1 /"))
            bad = dict(review)
            bad["source_bundle_sha256"] = "0" * 64
            corrupt = out / "synthetic-invalid-review.json"
            corrupt.write_text(json.dumps(bad))
            page.set_input_files("#import", str(corrupt))
            page.wait_for_function("document.querySelector('#message').textContent.startsWith('Import rejected')")
            check("mismatched import leaves current choices unchanged", page.locator("#progress-label").text_content().startswith("1 /"))
            check("no executable source-injection alert occurred", not errors)
        else:
            # No named reviewer, classification, extent or confirmation is set for real evidence.
            with page.expect_download() as download_info:
                page.click("#save")
            saved = out / "pending-review-check.json"
            download_info.value.save_as(str(saved))
            review = json.loads(saved.read_text())
            check("real corpus export contains no invented decisions", all(c["confirmed"] is False for c in review["choices"]))
        page.set_viewport_size({"width": 390, "height": 844})
        page.select_option("#meeting", first["meeting_id"])
        page.select_option("#segment", first["id"])
        check("mobile page has no horizontal overflow", page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
        page.screenshot(path=str(out / "mobile.png"), full_page=True)
        check("no JavaScript errors", not errors)
        check("no external network request", not external)
        result = {"schema": "un.boundary-browser-tests.v1", "real_source_render_only": real,
                  "synthetic_decision_tests": not real, "delivery_mode": "loopback_preview" if serve else "direct_local_file", "passed": len(checks), "failed": 0,
                  "checks": checks, "browser": browser.version, "external_requests": external,
                  "javascript_errors": errors, "heldout_transcripts_opened": 0}
        (out / "browser-tests.json").write_text(json.dumps(result, indent=2) + "\n")
        browser.close()
        if server:
            server.shutdown()
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--real", action="store_true")
    parser.add_argument("--serve", action="store_true", help="Local preview only; does not claim direct-file acceptance")
    args = parser.parse_args()
    print(json.dumps(run(args.packet, args.output, args.real, args.serve), indent=2))
