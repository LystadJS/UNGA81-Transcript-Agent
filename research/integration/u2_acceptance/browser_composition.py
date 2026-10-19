"""Strict served test of unchanged U1 assets using U2, not injected DOM or mocks."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import urllib.request
from playwright.sync_api import sync_playwright, expect

parser=argparse.ArgumentParser()
parser.add_argument('--output',required=True)
args=parser.parse_args()
out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
receipt={'schema':'u2.served-composition-review.v1','synthetic_only':True,'publication_eligible':False,'served_navigation_verified':False,'checks':[],'page_errors':[],'external_requests':[],'limitations':['U1 generic no-product presentation unchanged','Evidence prose service not connected','No full accessibility conformance claim']}
host=subprocess.Popen(['node',str(Path(__file__).with_name('composition_host.mjs'))],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=os.environ.copy())
try:
    info=json.loads(host.stdout.readline())
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        receipt['chromium']=browser.version
        page=browser.new_page(viewport={'width':1440,'height':1000},accept_downloads=True)
        page.on('pageerror',lambda error:receipt['page_errors'].append(str(error)))
        page.on('request',lambda req:receipt['external_requests'].append(req.url) if not req.url.startswith(info['origin']+'/') else None)
        response=page.goto(info['url'],wait_until='networkidle')
        assert response.status==200
        expect(page.locator('#create')).to_be_enabled()
        receipt['served_navigation_verified']=True
        def fresh(country='BRA',topic='',period=True):
            page.goto(info['url'],wait_until='networkidle')
            expect(page.locator('#create')).to_be_enabled()
            page.locator('#country').select_option(country)
            page.locator('#topic').select_option(topic)
            if period:
                page.locator('#from').fill('2024-09-23');page.locator('#to').fill('2024-09-23')
            page.locator('#create').focus();page.keyboard.press('Enter')
        def check(name,fn):
            try:
                fn();receipt['checks'].append({'name':name,'status':'PASS'})
            except Exception as error:
                receipt['checks'].append({'name':name,'status':'FAIL','error':str(error)[:1500]})
        def country():
            fresh();expect(page.locator('#status')).to_have_text('Briefing ready')
            expect(page.locator('[data-evidence]')).to_have_count(1)
            page.screenshot(path=str(out/'desktop.png'),full_page=True)
        check('country_from_U2_in_unchanged_U1',country)
        def topic():
            fresh('', 'climate');expect(page.locator('#status')).to_have_text('Briefing ready')
            expect(page.locator('[data-evidence]')).to_have_count(2)
        check('topic_query',topic)
        def meeting():
            page.goto(info['url'],wait_until='networkidle');expect(page.locator('#create')).to_be_enabled()
            page.locator('[data-page="meetings"]').click()
            expect(page.locator('input[name="meeting"]')).to_have_count(2)
            page.locator('input[name="meeting"][value="01"]').check();page.locator('#create').click()
            expect(page.locator('#status')).to_have_text('Briefing ready')
            expect(page.locator('[data-evidence]')).to_have_count(5)
        check('opaque_meeting_disambiguation',meeting)
        def partial():
            fresh(period=False);expect(page.locator('#status')).to_have_text('Some information is unavailable')
        check('missing_unverified_stay_partial',partial)
        def empty():
            fresh('CAN','climate');expect(page.locator('#status')).to_have_text('No matching records')
        check('known_complete_no_match',empty)
        def saved():
            fresh();expect(page.locator('#status')).to_have_text('Briefing ready')
            page.get_by_role('button',name='Save briefing',exact=True).click();expect(page.locator('#saved-count')).to_have_text('1')
            before=page.request.get(info['origin']+'/__u2__/stats').json()['lookups']
            page.locator('[data-page="saved"]').click();page.get_by_role('button',name='Open briefing',exact=True).click()
            expect(page.locator('#status')).to_have_text('Briefing ready')
            assert page.request.get(info['origin']+'/__u2__/stats').json()['lookups']==before
        check('saved_replay_without_router_lookup',saved)
        def export():
            fresh();expect(page.locator('#status')).to_have_text('Briefing ready')
            with page.expect_download() as got:page.get_by_role('button',name='Export read-only result',exact=True).click()
            got.value.save_as(str(out/'read-model.json'));data=json.loads((out/'read-model.json').read_text())
            assert data['schema']=='un.product-readiness.v1' and data['publication_eligible'] is False
            assert 'receipts' not in data and 'query' not in data and data['sections'][0]['evidence']
        check('fresh_filtered_JSON_export',export)
        def unavailable():
            page.goto(info['url'],wait_until='networkidle');expect(page.locator('#create')).to_be_enabled()
            page.locator('#from').fill('1999-01-01');page.locator('#to').fill('1999-01-01');page.locator('#create').click()
            expect(page.locator('#status')).to_contain_text('The briefing could not be prepared')
            expect(page.locator('[data-evidence]')).to_have_count(0)
        check('documented_U1_unavailability_mapping_gap',unavailable)
        def evidence():
            fresh();expect(page.locator('#status')).to_have_text('Briefing ready')
            page.locator('[data-evidence]').first.click()
            expect(page.locator('#evidence-dialog')).not_to_be_visible()
            expect(page.locator('#evidence-content')).to_be_empty()
        check('no_fabricated_evidence_prose_service',evidence)
        def mobile():
            for width in [390,320]:
                page.set_viewport_size({'width':width,'height':900});fresh()
                expect(page.locator('#status')).to_have_text('Briefing ready')
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                page.screenshot(path=str(out/f'mobile-{width}.png'),full_page=True)
        check('responsive_390_and_320',mobile)
        def revoked():
            request=urllib.request.Request(info['origin']+'/__u2__/revoke',data=b'{}',method='POST',headers={'X-Review-Token':info['control']})
            with urllib.request.urlopen(request) as response:assert response.status==200
            expect(page.locator('#status')).to_contain_text('Access changed or expired',timeout=10000)
            expect(page.locator('[data-evidence]')).to_have_count(0)
        check('current_key_revocation_clears_visible_result',revoked)
        browser.close()
    receipt['status']='PASS' if all(c['status']=='PASS' for c in receipt['checks']) and not receipt['page_errors'] and not receipt['external_requests'] else 'FAIL'
except Exception as error:
    receipt['status']='BLOCKED' if not receipt['served_navigation_verified'] else 'FAIL'
    receipt['error']=str(error)[:1500]
finally:
    host.terminate()
    try:host.wait(timeout=5)
    except subprocess.TimeoutExpired:host.kill();host.wait()
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
raise SystemExit(0 if receipt['status']=='PASS' else 1)
