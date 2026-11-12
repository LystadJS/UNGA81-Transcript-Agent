"""Synthetic-only offline browser review acceptance."""
import importlib.util
import re
import json
import os
from pathlib import Path
import tempfile
import functools
import http.server
import threading
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('reviewer',ROOT/'tools/build_private_reviewer.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def main():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        rows=[{'pair_id':str(i),'segment_id':'s'+str(i),'split':'train','text':'</script><script>window.injected=true</script> We support the proposal.',
               'proposition':'Adopt the proposal','country':'Example','capacity':'unknown','date':'2026-09-10','meeting_id':'synthetic',
               'source_id':'revision','source_hash':'a'*64,'owner_confirmed':False,'status':None,'label':None,'national_attribution_valid':None} for i in range(3)]
        draft={'schema':'un.stance-labels.v1','registration_sha256':'f'*64,'owner_confirmed':False,'rows':rows}
        html=root/'review.html';html.write_text(module.render(draft,{'0':{'speaker':'Synthetic speaker','source_url':'javascript:alert(1)'}},{'split':'train','test':'synthetic'}))
        url=html.as_uri(); server=None
        if os.environ.get('REVIEW_TEST_HTTP'):
            handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root))
            server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
            threading.Thread(target=server.serve_forever,daemon=True).start()
            url=f'http://127.0.0.1:{server.server_port}/review.html'
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None,headless=True,args=['--no-sandbox'])
            page=browser.new_page(accept_downloads=True);requests=[];page.on('request',lambda r:requests.append(r.url))
            page.goto(url)
            assert page.evaluate('window.injected') is None
            assert page.locator('#source').is_hidden()
            page.locator('#confirmed').click();assert not page.locator('#confirmed').is_checked()
            page.locator('#reviewer').fill('Owner synthetic test')
            page.locator('#status').select_option('clear');page.locator('#label').select_option('support');page.locator('#national').select_option('true');page.locator('#confirmed').check()
            with page.expect_download() as download:page.locator('#export').click()
            exported=root/'reviewed.json';download.value.save_as(exported)
            data=json.loads(exported.read_text());assert len(data['rows'])==1 and data['owner_confirmed'] is True
            assert data['rows'][0]['text']==rows[0]['text'] and data['registration_sha256']==draft['registration_sha256']
            page.locator('#notes').fill('Borderline intensity');assert not page.locator('#confirmed').is_checked()
            page.locator('#status').select_option('conditional');assert page.locator('#label').is_disabled()
            page.locator('#confirmed').check()
            with page.expect_download() as download:page.locator('#save').click()
            progress=root/'progress.json';download.value.save_as(progress)
            saved=json.loads(progress.read_text());assert saved['rows'][0]['label'] is None and saved['owner_confirmed'] is False
            page.locator('#import').set_input_files(progress);expect(page.locator('#message')).to_have_text(re.compile(r'^Imported'))
            assert page.locator('#notes').input_value()=='Borderline intensity'
            tampered=json.loads(progress.read_text());tampered['rows'][0]['text']='changed';bad=root/'bad.json';bad.write_text(json.dumps(tampered))
            page.locator('#import').set_input_files(bad);expect(page.locator('#message')).to_contain_text('were changed')
            assert page.locator('#text').inner_text()==rows[0]['text']
            tampered=json.loads(progress.read_text());tampered['rows'].append(tampered['rows'][0]);bad.write_text(json.dumps(tampered))
            page.locator('#import').set_input_files(bad);expect(page.locator('#message')).to_contain_text('duplicated')
            for width in (390,1440):
                page.set_viewport_size({'width':width,'height':900})
                overflow=page.evaluate('document.documentElement.scrollWidth > innerWidth + 1')
                if overflow:
                    print(page.evaluate("Array.from(document.querySelectorAll('body *')).filter(e=>e.getBoundingClientRect().right>innerWidth+1).map(e=>({tag:e.tagName,id:e.id,width:e.getBoundingClientRect().width})).slice(0,20)"))
                assert not overflow
            assert not [r for r in requests if r.startswith(('http://','https://')) and r!=url]
            browser.close()
        if server: server.shutdown()
    print('Offline reviewer acceptance passed: source safety, confirmation, JSON round-trip, tamper rejection, mobile and no network')

if __name__=='__main__': main()
