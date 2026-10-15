"""Actual Chromium desktop/mobile and saved-run replay QA, synthetic only.
Usage: python browser_smoke.py [--output /tmp/rv2-browser]
Playwright 1.x and installed Chromium required; no remote server or source data.
"""
import argparse
import contextlib
import functools
import http.server
import json
import pathlib
import socketserver
import threading
import xml.etree.ElementTree as ET

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@contextlib.contextmanager
def server():
    handler = functools.partial(QuietHandler, directory=str(ROOT))
    with http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler) as httpd:
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            yield f'http://127.0.0.1:{httpd.server_port}/'
        finally:
            httpd.shutdown()
            thread.join(timeout=5)


def assert_plot(page, name):
    assert page.locator('section.rv-panel').count() == 4
    assert page.locator('.rv-figure svg').count() == 4
    assert page.locator('svg > title').count() == 4
    consensus = page.locator('section[data-kind="consensus"]')
    assert consensus.get_by_text('66.7%').count() >= 1, f'{name}: weighted association missing'
    assert consensus.get_by_text('0.0%').count() >= 1, f'{name}: assessed zero missing'
    assert consensus.get_by_text('N/A').count() >= 1, f'{name}: no joint-fit case missing'
    assert page.get_by_text('Frame 5 · eligible 3 · included 3 · excluded 2 · missing/failed 2').count() >= 1
    assert page.locator('section[data-kind="longitudinal"] svg').get_by_text('WITHHELD').count() == 1
    assert page.locator('section[data-kind="method-comparison"] svg').get_by_text('INCOMPATIBLE').count() == 1
    assert page.get_by_text('ABSTAIN').count() == 0


def test_size(browser, base_url, out, width, height, html=None):
    context = browser.new_context(viewport={'width': width, 'height': height}, accept_downloads=True)
    page = context.new_page()
    bad_network = []
    exceptions = []
    page.on('request', lambda req: bad_network.append(req.url) if not req.url.startswith(base_url) else None)
    page.on('pageerror', lambda exc: exceptions.append(str(exc)))
    if html is None:
        page.goto(base_url, wait_until='networkidle')
    else:
        # This environment blocks Chromium page navigation, including localhost.
        # set_content still executes the exact checked-in scripts/CSS in actual Chromium.
        page.set_content(html, wait_until='load')
    page.locator('#rv-status').get_by_text('Verified synthetic run', exact=False).wait_for()
    assert_plot(page, f'{width}x{height}')
    assert not exceptions, f'Browser JS errors: {exceptions}'
    assert not bad_network, f'Unexpected remote requests: {bad_network}'
    overflow = page.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth')
    assert overflow <= 1, f'whole-page horizontal overflow {overflow}px at {width}px'
    page.screenshot(path=str(out / f'full-{width}x{height}.png'), full_page=True)
    summary = page.get_by_text('Full source, country-attribution, and review ledger', exact=False)
    summary.focus()
    page.keyboard.press('Enter')
    assert page.locator('details[open]').count() == 1
    assert page.locator('details').get_by_text('SRC-E').count() >= 1
    assert page.locator('details').get_by_text('Invented source extraction failure').count() >= 1
    assert not exceptions

    with page.expect_download() as info:
        page.locator('#rv-json').click()
    data = json.loads(pathlib.Path(info.value.path()).read_text())
    assert len(data['sources']) == 5
    assert abs(data['panels'][0]['rows'][0]['association']-.4/.6)<1e-12
    assert data['panels'][0]['rows'][2]['association'] is None
    assert data['panels'][2]['alignments'][1]['status'] == 'withheld'
    with page.expect_download() as info:
        page.locator('#rv-html').click()
    html=pathlib.Path(info.value.path()).read_text()
    assert '<script' not in html.lower() and 'fetch(' not in html.lower()
    assert 'SRC-E' in html and 'missing/failed 2' in html
    with page.expect_download() as info:
        page.locator('#rv-svg').click()
    ET.parse(info.value.path())

    page.locator('#rv-replay').set_input_files({
        'name':'saved-run.json','mimeType':'application/json',
        'buffer':json.dumps(data).encode('utf-8')
    })
    page.locator('#rv-status').get_by_text('Verified synthetic run', exact=False).wait_for()
    assert_plot(page, 'saved-run replay')

    corrupt=json.loads(json.dumps(data))
    corrupt['panels'][0]['rows'][0]['association']=.12
    page.locator('#rv-replay').set_input_files({
        'name':'corrupt-saved-run.json','mimeType':'application/json',
        'buffer':json.dumps(corrupt).encode('utf-8')
    })
    page.locator('#rv-status').get_by_text('ABSTAIN', exact=False).wait_for()
    assert page.locator('#rv-output').inner_text() == ''
    assert page.locator('#rv-json').is_disabled()
    assert page.locator('#rv-html').is_disabled()
    assert page.locator('#rv-svg').is_disabled()
    assert page.locator('#rv-panel-select').is_disabled()

    page.locator('#rv-reset').click()
    page.locator('#rv-status').get_by_text('Verified synthetic run', exact=False).wait_for()
    assert_plot(page,'restored fixture')
    assert not exceptions
    assert not bad_network
    context.close()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='/tmp/unga81-rv2-browser')
    args=parser.parse_args()
    out=pathlib.Path(args.output);out.mkdir(parents=True,exist_ok=True)
    with server() as base, sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        html=None
        probe=browser.new_page()
        try:
            probe.goto(base,wait_until='load',timeout=5000)
        except Exception as error:
            if 'ERR_BLOCKED_BY_ADMINISTRATOR' not in str(error):
                raise
            fixture=json.loads((ROOT/'fixture.json').read_text())
            raw=(ROOT/'index.html').read_text()
            raw=raw.replace('<link rel="stylesheet" href="style.css">',
                '<style>'+ (ROOT/'style.css').read_text() +'</style>')
            raw=raw.replace('<script src="renderer.js"></script>',
                '<script>'+ (ROOT/'renderer.js').read_text() +'</script>')
            raw=raw.replace('<script>\n(function(){',
                '<script>window.fetch = async function() { return {ok:true,json:async()=>'+
                '('+json.dumps(fixture)+')'+'}; };</script><script>\n(function(){')
            html=raw
            print('LIMITATION: Chromium blocks localhost/file/data navigation; using actual Chromium set_content with exact inline app/CSS and synthetic fixture')
        finally:
            probe.close()
        for w,h in [(1440,900),(390,844)]:
            test_size(browser,base,out,w,h,html)
            print(f'PASS Chromium {w}x{h}: display, source ledger, keyboard, script-free exports, XML, replay, invalidation, no network/overflow')
        browser.close()
    print('Browser QA PASS; screenshots:',out)


if __name__=='__main__':
    main()
