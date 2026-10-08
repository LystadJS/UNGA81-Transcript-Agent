#!/usr/bin/env python3
"""Offline browser acceptance with fabricated review records; no real transcripts."""
from pathlib import Path
import json, subprocess, tempfile, sys, os
from playwright.sync_api import sync_playwright

def main(destination: Path):
    if destination.exists(): raise ValueError('Never overwrite prior test evidence')
    destination.mkdir(parents=True)
    repo=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as temp:
        tmp=Path(temp)
        # This fixture is generated only from synthetic records; source-text strings
        # and meeting IDs do not correspond to any real UN proceeding.
        packet={'schema':'un.quick-reader-adjudication-benchmark.v1','corpus_sha256':'e8fb980cf638e2aef39d0ca3564836c6120201a059e806ccaaee3fd5cc4f593e',
            'coverage':{'additional_meetings':13},'cases':[
                {'kind':'position','id':'position:synthetic_first','source_id':'synthetic_first#0','meeting_id':'synthetic_first',
                 'source_sha256':'a'*64,'source_url':'https://transcripts.un.org/en/synthetic_fiction_only','source_excerpt':'We support humanitarian access in this entirely synthetic example.',
                 'recorded_country':'Fictional State','issue_id':'humanitarian','current_classification':'support_or_advocacy_expressed'},
                {'kind':'abstention','id':'abstention:synthetic_second','source_id':'synthetic_second#0','meeting_id':'synthetic_second',
                 'source_sha256':'b'*64,'source_url':'https://transcripts.un.org/en/synthetic_fiction_only','source_excerpt':'Fictional journalist raises a question without a national position.',
                 'recorded_country':'Fictional State','issue_id':'human_rights','current_classification':None}
            ]}
        src='''const B=require('./research/reference_tests/quick_reader_benchmark.cjs');const fs=require('fs');const p=JSON.parse(fs.readFileSync(process.argv[1]));p.case_binding_sha256=B.bindingFor(p);fs.writeFileSync(process.argv[1],JSON.stringify(p));'''
        b=tmp/'benchmark.json';b.write_text(json.dumps(packet));subprocess.run(['node','-e',src,str(b)],cwd=repo,check=True)
        x=json.loads(b.read_text())
        r=tmp/'assistant.json';r.write_text(json.dumps({'schema':'un.quick-reader-adjudication-choices.v1','case_binding_sha256':x['case_binding_sha256'],'reviewer_type':'assistant_provisional','choices':[]}))
        out=tmp/'index.html';subprocess.run(['node',str(repo/'research/reference_tests/render_adjudication_view.cjs'),str(b),str(r),str(out)],check=True)
        evidence=[]
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(headless=True,executable_path=os.getenv('CHROME_BINARY','/usr/bin/chromium'),args=['--no-sandbox','--disable-dev-shm-usage'])
            for width in (1440,390):
                page=browser.new_page(viewport={'width':width,'height':800},accept_downloads=True)
                errors=[];requests=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('request',lambda req:requests.append(req.url))
                page.set_content(out.read_text(),wait_until='domcontentloaded')
                assert page.locator('#counter').inner_text()=='1 / 2'
                assert page.locator('#progress').inner_text().startswith('0 of 2')
                page.locator('#reviewer').fill('Synthetic Test Reviewer')
                page.locator('.answer select').nth(0).select_option('individual_country')
                page.locator('.answer select').nth(1).select_option('supported_expression')
                page.locator('.answer textarea').fill('Synthetic reviewer accepted the artificial stance statement.')
                assert page.locator('#progress').inner_text().startswith('1 of 2')
                with page.expect_download(timeout=12000) as future:page.locator('#download').click()
                local=destination/f'export-{width}.json';future.value.save_as(local)
                export=json.loads(local.read_text())
                assert len(export['choices'])==1 and export['choices'][0]['id']=='position:synthetic_first'
                page.locator('#next').click();assert page.locator('#counter').inner_text()=='2 / 2'
                assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'), 'horizontal overflow'
                assert not errors and not requests,(errors,requests)
                page.screenshot(path=str(destination/f'screenshot-{width}.png'),full_page=True)
                evidence.append({'width':width,'cases':2,'export_decisions':1,'errors':errors,'external_requests':requests,'horizontal_overflow':False})
                page.close()
            browser.close()
        (destination/'receipt.json').write_text(json.dumps({'schema':'un.quick-reader-benchmark-ui-synthetic.v1','checks':'PASS','evidence':evidence,'reserved_content_opened':0},indent=2)+'\n')
        print(json.dumps({'status':'PASS','desktop_mobile':True,'no_network':True,'synthetic':True,'checks':len(evidence)}))

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('Usage: test_quick_reader_adjudication_ui.py NEW_OUTPUT_DIR')
    main(Path(sys.argv[1]))
