"""Coordinator-only, real-HTTP U1 review probes. No DOM or response replacement."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

CASES = ['keyboard_form', 'saved_no_reroute', 'delayed_export_invalidated',
         'delayed_import_cancelled', 'dialog_focus', 'visual_desktop', 'visual_390', 'visual_320']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    host_script = args.root / 'site/parallel/w07-diplomat-ux/tests/fixture-host.mjs'
    host = subprocess.Popen(['node', str(host_script), '--qa'], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    receipt = {'schema': 'coord.u1.browser-review.v1', 'synthetic_only': True,
               'publication_eligible': False, 'served_navigation_verified': False,
               'checks': [], 'screenshots': {}, 'status': 'NOT_RUN'}
    try:
        cfg = json.loads(host.stdout.readline())
        def api(path, value):
            req = urllib.request.Request(cfg['origin'] + path, json.dumps(value).encode(),
                {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + cfg['qaToken']})
            with urllib.request.urlopen(req, timeout=15) as res:
                return json.load(res)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            receipt['chromium'] = browser.version
            for case in CASES:
                api('/__u1__/test-event', {'name': 'reset'})
                width = {'visual_390': 390, 'visual_320': 320}.get(case, 1440)
                context = browser.new_context(viewport={'width': width, 'height': 1024}, accept_downloads=True)
                page = context.new_page()
                page.set_default_timeout(6000)
                errors, requests, downloads, held = [], [], [], []
                pause = [True]
                page.on('pageerror', lambda err: errors.append(str(err)))
                page.on('request', lambda req: requests.append((req.method, req.url)))
                page.on('download', lambda item: downloads.append(item))
                try:
                    response = page.goto(cfg['url'], wait_until='networkidle')
                    assert response.status == 200 and page.url == cfg['url']
                    expect(page.locator('#create')).to_be_enabled()
                    receipt['served_navigation_verified'] = True
                    def make():
                        page.locator('#country').select_option('BRA')
                        page.locator('#from').fill('2024-09-23')
                        page.locator('#to').fill('2024-09-23')
                        page.locator('#create').click()
                        expect(page.locator('#briefing .report-top')).to_be_visible()
                        expect(page.locator('[data-evidence="e01"]')).to_be_visible()
                    def await_held():
                        limit = time.monotonic() + 5
                        while not held and time.monotonic() < limit:
                            page.wait_for_timeout(20)
                        assert held, 'real trust request was not intercepted'
                    def hold(route):
                        if pause[0]: held.append(route)
                        else: route.continue_()
                    def release():
                        # Complete paused routes before unregistering the handler.
                        pause[0] = False
                        for route in list(held):
                            route.continue_()
                        held.clear()
                        page.unroute('**/__u1__/trust/*', hold)
                        page.wait_for_load_state('networkidle')
                    if case == 'keyboard_form':
                        page.keyboard.press('Tab')
                        expect(page.locator('.skip')).to_be_focused()
                        page.keyboard.press('Enter')
                        expect(page.locator('#main')).to_be_focused()
                        page.keyboard.press('Tab')
                        expect(page.locator('#country')).to_be_focused()
                        page.keyboard.press('b')
                        expect(page.locator('#country')).to_have_value('BRA')
                        visited = []
                        for _ in range(20):
                            visited.append(page.evaluate('document.activeElement.id'))
                            if visited[-1] == 'create':
                                break
                            page.keyboard.press('Tab')
                        assert visited[-1] == 'create', visited
                        page.keyboard.press('Enter')
                        expect(page.locator('#briefing .report-top')).to_be_visible()
                        expect(page.locator('[data-evidence="e01"]')).to_be_visible()
                    elif case == 'saved_no_reroute':
                        make()
                        before = len([x for x in requests if x[1].endswith('/resolve')])
                        page.get_by_role('button', name='Save briefing', exact=True).click()
                        expect(page.locator('#saved-count')).to_have_text('1')
                        page.get_by_role('button', name='Saved briefings 1').click()
                        page.get_by_role('button', name='Open briefing', exact=True).click()
                        expect(page.locator('[data-evidence="e01"]')).to_be_visible()
                        assert before == len([x for x in requests if x[1].endswith('/resolve')])
                    elif case == 'delayed_export_invalidated':
                        make()
                        page.route('**/__u1__/trust/*', hold)
                        page.get_by_role('button', name='Export read-only result').click()
                        await_held()
                        page.locator('#country').select_option('CAN')
                        expect(page.locator('[data-evidence]')).to_have_count(0)
                        release()
                        expect(page.locator('#briefing .report-top')).to_have_count(0)
                        assert not downloads, 'stale download was emitted'
                    elif case == 'delayed_import_cancelled':
                        make()
                        bundle = api('/__u1__/resolve', {'page': 'explore', 'country': 'BRA', 'topic': None,
                            'period': {'start': '2024-09-23', 'end': '2024-09-23'}, 'meeting': None})
                        page.locator('#about > summary').click()
                        page.route('**/__u1__/trust/*', hold)
                        page.locator('#bundle-file').set_input_files({'name': 'synthetic.json',
                            'mimeType': 'application/json', 'buffer': json.dumps(bundle).encode()})
                        await_held()
                        page.locator('#cancel-import').click()
                        release()
                        expect(page.locator('#briefing .report-top')).to_have_count(0)
                        expect(page.locator('[data-evidence]')).to_have_count(0)
                    elif case == 'dialog_focus':
                        make()
                        page.locator('[data-evidence="e01"]').focus()
                        page.keyboard.press('Enter')
                        expect(page.locator('#evidence-dialog')).to_be_visible()
                        expect(page.locator('#close-evidence')).to_be_focused()
                        page.keyboard.press('Tab')
                        assert page.evaluate('document.activeElement.closest("dialog") !== null'), 'Modal Tab lost visible focus: ' + page.evaluate('document.activeElement.tagName')
                        page.keyboard.press('Shift+Tab')
                        expect(page.locator('#close-evidence')).to_be_focused()
                        page.screenshot(path=str(args.output/'dialog.png'))
                        page.keyboard.press('Escape')
                        expect(page.locator('[data-evidence="e01"]')).to_be_focused()
                    else:
                        make()
                        page.evaluate('window.scrollTo(0,0)')
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                        assert page.locator('.skip').evaluate('(e) => e.getBoundingClientRect().bottom <= 0 && e !== document.activeElement')
                        expect(page.locator('label[for="country"]')).to_be_visible()
                        # Normalize the scroll position for full-page capture. This is not DOM injection.
                        page.screenshot(path=str(args.output/(case+'.png')), full_page=True)
                    assert not errors, errors
                    assert all(url.startswith(cfg['origin']+'/') for _, url in requests), requests
                    receipt['checks'].append({'name': case, 'status': 'PASS'})
                except Exception as exc:
                    receipt['checks'].append({'name': case, 'status': 'FAIL', 'error': str(exc)[:2000]})
                    page.screenshot(path=str(args.output/(case+'-failure.png')))
                finally:
                    for route in held:
                        try: route.abort()
                        except Exception: pass
                    context.close()
            browser.close()
        receipt['status'] = 'PASS' if len(receipt['checks']) == len(CASES) and all(c['status']=='PASS' for c in receipt['checks']) else 'FAIL'
    except Exception as exc:
        receipt.update(status='BLOCKED', blocker=str(exc)[:1000])
    finally:
        host.terminate()
        try: host.wait(timeout=10)
        except subprocess.TimeoutExpired: host.kill(); host.wait()
        receipt['screenshots'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in args.output.glob('*.png')}
        (args.output/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
        print(json.dumps(receipt))
    return 0 if receipt['status']=='PASS' else 1

if __name__=='__main__':
    raise SystemExit(main())
