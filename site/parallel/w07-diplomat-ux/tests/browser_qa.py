"""Strict HTTP-served Chromium QA. Navigation failure is BLOCKED, never a DOM fallback pass."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
from playwright.sync_api import sync_playwright, expect

HERE = Path(__file__).resolve().parent
CASES = [
    'entry_and_country', 'topic_only', 'meeting_disambiguation', 'inclusive_dates',
    'partial_coverage', 'empty_result', 'failed_reader', 'unavailable_history',
    'keyboard_evidence_and_focus', 'save_reopen_no_refit', 'export_read_model',
    'corrupt_import_clears', 'forged_authority_refused', 'omitted_veto_refused',
    'revocation_clears_content', 'expired_export_refused', 'cancel_import',
    'highlight_is_selection_only', 'mobile_390', 'mobile_320', 'reduced_motion',
    'no_remote_requests_or_page_errors'
]

def api(origin, path, data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(origin + path, data=None if data is None else json.dumps(data).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=15) as res:
        return json.load(res)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--chromium', help='Explicit Chromium executable; otherwise use installed Playwright Chromium.')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    receipt = {'schema':'u1.served-browser-qa.v1','synthetic_only':True,'served_navigation_verified':False,
               'mode':'strict_http_no_fallback','status':'NOT_RUN','authored_checks':len(CASES),
               'checks':[], 'page_errors':[], 'external_requests':[], 'screenshots':[],
               'playwright':importlib.metadata.version('playwright'), 'publication_eligible':False}
    process = subprocess.Popen(['node',str(HERE/'fixture-host.mjs'),'--qa'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        config = json.loads(process.stdout.readline())
        receipt['c0'] = config['dependencies']['c0']
        origin, token = config['origin'], config['qaToken']
        with sync_playwright() as p:
            launch = {'headless':True, 'args':['--no-sandbox','--disable-dev-shm-usage']}
            if args.chromium:
                launch['executable_path'] = args.chromium
            browser = p.chromium.launch(**launch)
            receipt['chromium'] = browser.version
            probe = browser.new_page()
            try:
                response = probe.goto(config['url'],wait_until='networkidle',timeout=20000)
                assert response and response.status == 200
                expect(probe.get_by_role('button',name='Create briefing',exact=True)).to_be_enabled()
                assert probe.url == config['url']
                receipt['served_navigation_verified'] = True
            except Exception as exc:
                receipt.update(status='BLOCKED',blocker=str(exc)[:700],checks_executed=0)
                browser.close()
                return 2
            probe.close()
            for case in CASES:
                api(origin,'/__u1__/test-event',{'name':'reset'},token)
                context = browser.new_context(viewport={'width':1440,'height':1024},accept_downloads=True)
                page = context.new_page()
                errors, external = [], []
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.on('request',lambda request:external.append(request.url) if not request.url.startswith(origin+'/') else None)
                try:
                    page.goto(config['url'],wait_until='networkidle')
                    expect(page.locator('#create')).to_be_enabled()
                    def make(country='BRA',topic='',start='2024-09-23',end='2024-09-23'):
                        page.locator('#country').select_option(country)
                        page.locator('#topic').select_option(topic)
                        page.locator('#from').fill(start)
                        page.locator('#to').fill(end)
                        page.locator('#create').click()
                        expect(page.locator('#briefing')).to_have_attribute('aria-busy','false')
                        expect(page.locator('#briefing .report-top')).to_be_visible()
                    def meeting(value):
                        page.get_by_role('button',name='Meetings',exact=True).click()
                        page.locator(f'input[name="meeting"][value="{value}"]').check()
                        page.locator('#create').click()
                        expect(page.locator('#briefing .report-top')).to_be_visible()
                    def bundle():
                        return api(origin,'/__u1__/resolve',{'page':'explore','country':'BRA','topic':None,'period':{'start':'2024-09-23','end':'2024-09-23'},'meeting':None})
                    def upload(value):
                        page.locator('#about > summary').click()
                        page.locator('#bundle-file').set_input_files({'name':'synthetic.json','mimeType':'application/json','buffer':value.encode()})
                    if case=='entry_and_country':
                        make(start='',end='');expect(page.locator('#briefing')).to_contain_text('Brazil');expect(page.locator('#briefing')).to_contain_text('available preview period')
                    elif case=='topic_only':
                        make(country='',topic='climate');expect(page.locator('#briefing')).to_contain_text('Climate and energy');expect(page.locator('[data-evidence]')).to_have_count(2)
                    elif case=='meeting_disambiguation':
                        page.get_by_role('button',name='Meetings',exact=True).click();page.locator('#meeting-search').fill('Sustainable futures');expect(page.locator('.meeting-choice')).to_have_count(2);page.locator('input[value="1"]').check();page.locator('#create').click();expect(page.locator('#briefing')).to_contain_text('2024-09-24')
                    elif case=='inclusive_dates':
                        make(country='',start='2024-09-23',end='2024-09-24');expect(page.locator('[data-evidence]')).to_have_count(6)
                    elif case=='partial_coverage':
                        meeting('1');expect(page.locator('#briefing')).to_contain_text('partial account')
                    elif case=='empty_result':
                        make(country='CAN',topic='peace');expect(page.locator('#status')).to_have_text('No matching records');expect(page.get_by_role('button',name='Export read-only result')).to_be_disabled()
                    elif case=='failed_reader':
                        meeting('03');expect(page.locator('#status')).to_have_text('Briefing could not be prepared');expect(page.locator('[data-evidence]')).to_have_count(0)
                    elif case=='unavailable_history':
                        make(start='2001-01-01',end='2001-01-02');expect(page.locator('#briefing')).to_contain_text('not evidence that nothing was said');expect(page.locator('.stats')).to_have_count(0)
                    elif case=='keyboard_evidence_and_focus':
                        make();button=page.locator('[data-evidence="e01"]');button.focus();page.keyboard.press('Enter');expect(page.locator('#evidence-dialog')).to_be_visible();expect(page.locator('#evidence-content')).to_contain_text('Invented example:');page.keyboard.press('Escape');expect(page.locator('#evidence-dialog')).not_to_be_visible();expect(page.locator('[data-evidence="e01"]')).to_be_focused()
                    elif case=='save_reopen_no_refit':
                        make();page.get_by_role('button',name='Save briefing',exact=True).click();expect(page.locator('#saved-count')).to_have_text('1');page.get_by_role('button',name='Saved briefings 1').click();page.get_by_role('button',name='Open briefing',exact=True).click();expect(page.locator('#briefing')).to_contain_text('Brazil')
                    elif case=='export_read_model':
                        make()
                        with page.expect_download() as download:
                            page.get_by_role('button',name='Export read-only result').click()
                        export_path=args.output/'read-model.json';download.value.save_as(export_path)
                        value=json.loads(export_path.read_text());assert value['schema']=='un.product-readiness.v1' and not value['publication_eligible'];assert all(not s['evidence'] and s['display'] is None for s in value['sections'] if s['state']=='withheld')
                    elif case=='corrupt_import_clears':
                        make();upload('{broken');expect(page.locator('#status')).to_contain_text('could not be verified');expect(page.locator('[data-evidence]')).to_have_count(0)
                    elif case=='forged_authority_refused':
                        make();b=bundle();b['trustedReceiptSetSha256']='a'*64;upload(json.dumps(b));expect(page.locator('#status')).to_contain_text('could not be verified');expect(page.locator('[data-evidence]')).to_have_count(0)
                    elif case=='omitted_veto_refused':
                        b=bundle();api(origin,'/__u1__/test-event',{'name':'veto'},token);upload(json.dumps(b));expect(page.locator('#status')).to_contain_text('could not be verified');expect(page.locator('[data-evidence]')).to_have_count(0)
                    elif case=='revocation_clears_content':
                        make();page.locator('[data-evidence="e01"]').click();expect(page.locator('#evidence-dialog')).to_be_visible();api(origin,'/__u1__/test-event',{'name':'revoke'},token);expect(page.locator('#evidence-dialog')).not_to_be_visible(timeout=5000);expect(page.locator('[data-evidence]')).to_have_count(0)
                    elif case=='expired_export_refused':
                        make();api(origin,'/__u1__/test-event',{'name':'expire'},token);expect(page.locator('#status')).to_contain_text('expired',timeout=5000);expect(page.get_by_role('button',name='Export read-only result')).to_have_count(0)
                    elif case=='cancel_import':
                        make();page.locator('#about > summary').click();page.locator('#cancel-import').click();expect(page.locator('[data-evidence]')).to_have_count(0)
                    elif case=='highlight_is_selection_only':
                        make(country='');before=page.locator('.stats').inner_text();page.get_by_role('button',name='United States',exact=True).click();assert page.locator('.stats').inner_text()==before;expect(page.locator('.highlighted')).to_have_count(1);expect(page.locator('[data-evidence]')).to_have_count(4)
                    elif case in ('mobile_390','mobile_320'):
                        width=390 if case=='mobile_390' else 320;page.set_viewport_size({'width':width,'height':844});make();assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth');expect(page.locator('#create')).to_be_visible();page.screenshot(path=str(args.output/(case+'.png')),full_page=True);receipt['screenshots'].append(case+'.png')
                    elif case=='reduced_motion':
                        page.emulate_media(reduced_motion='reduce');make();assert page.evaluate('matchMedia("(prefers-reduced-motion: reduce)").matches')
                    elif case=='no_remote_requests_or_page_errors':
                        make();page.locator('[data-evidence="e01"]').click();expect(page.locator('#evidence-dialog')).to_be_visible();assert not errors and not external;page.screenshot(path=str(args.output/'desktop.png'),full_page=True);receipt['screenshots'].append('desktop.png')
                    if errors or external:
                        raise AssertionError({'page_errors':errors,'external_requests':external})
                    receipt['checks'].append({'name':case,'status':'PASS'})
                except Exception as exc:
                    receipt['checks'].append({'name':case,'status':'FAIL','error':str(exc)[:1200]})
                finally:
                    receipt['page_errors'].extend(errors);receipt['external_requests'].extend(external);context.close()
            browser.close()
        receipt['checks_executed']=len(receipt['checks'])
        receipt['status']='PASS' if all(c['status']=='PASS' for c in receipt['checks']) else 'FAIL'
        return 0 if receipt['status']=='PASS' else 1
    except Exception as exc:
        receipt.update(status='BLOCKED',blocker=str(exc)[:1000],checks_executed=len(receipt['checks']))
        return 2
    finally:
        process.terminate()
        try: process.wait(timeout=10)
        except subprocess.TimeoutExpired: process.kill();process.wait()
        receipt['asset_sha256']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in HERE.parent.iterdir() if f.suffix in ('.mjs','.html','.css')}
        (args.output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print(json.dumps({'status':receipt['status'],'served_navigation_verified':receipt['served_navigation_verified'],'checks_executed':len(receipt['checks'])}))

if __name__=='__main__':
    sys.exit(main())
