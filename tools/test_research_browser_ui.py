"""Desktop/mobile Chrome check for source-free research wiring."""
from __future__ import annotations
import argparse,json,threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from functools import partial
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET
from playwright.sync_api import sync_playwright

def check(browser,url,out,name):
  width,height=(1440,900) if name=='desktop' else (390,844)
  context=browser.new_context(viewport={'width':width,'height':height},accept_downloads=True,reduced_motion='reduce')
  page=context.new_page();errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('request',lambda r:errors.append('External request '+r.url) if urlsplit(r.url).hostname!='127.0.0.1' else None)
  try:
    page.goto(url+'/research.html',wait_until='load')
    page.locator('#research-summary:not([hidden])').wait_for(timeout=15000)
    assert page.locator('.ev-panel').count()==4
    assert page.locator('svg[role=img]').count()==4
    assert 'Accepted W5 and W6' in page.locator('#research-status').inner_text()
    assert 'Unavailable: 1' in page.locator('#research-summary').inner_text()
    first=page.locator('[data-ev-inspect]').first
    first.focus();page.keyboard.press('Enter')
    assert 'Selected evidence' in page.locator('.ev-inspector').first.inner_text()
    with page.expect_download() as download:
      page.get_by_role('button',name='Export SVG').first.click()
    svg=out/('research-'+name+'.svg');download.value.save_as(str(svg))
    assert ET.parse(svg).getroot().tag.endswith('svg')
    page.screenshot(path=str(out/('research-'+name+'.png')),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth')<=width+1,'Page overflow'
    fixture=json.loads(page.evaluate('JSON.stringify(UNEvidenceFixture.fixture())'))
    sample=out/('synthetic-'+name+'.json');sample.write_text(json.dumps(fixture),encoding='utf-8')
    page.locator('#research-file').set_input_files(sample)
    page.locator('#research-open').click()
    assert page.locator('.ev-panel').count()==4
    fixture['envelope']['producer']['fixture_kind']='private_development'
    sample.write_text(json.dumps(fixture),encoding='utf-8')
    page.locator('#research-file').set_input_files(sample)
    page.locator('#research-open').click()
    assert page.locator('.ev-panel').count()==0
    assert 'Evidence rejected' in page.locator('#research-status').inner_text()
    page.locator('#research-example').click()
    assert page.locator('.ev-panel').count()==4
    page.locator('#research-clear').click()
    assert page.locator('.ev-panel').count()==0
    assert page.locator('#research-summary').is_hidden()
    assert not errors,errors
    return {'viewport':name,'status':'PASS','external_requests':0}
  finally:context.close()

def main():
  a=argparse.ArgumentParser()
  a.add_argument('--site',required=True,type=Path)
  a.add_argument('--outdir',required=True,type=Path)
  a.add_argument('--browser-path',required=True,type=Path)
  p=a.parse_args();p.outdir.mkdir(parents=True,exist_ok=True)
  server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(p.site.resolve())))
  thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
    url='http://127.0.0.1:'+str(server.server_port)
    with sync_playwright() as pw:
      b=pw.chromium.launch(headless=True,executable_path=str(p.browser_path.resolve()),
        args=['--no-sandbox','--disable-dev-shm-usage'])
      try:
        views=[check(b,url,p.outdir,n) for n in ('desktop','mobile')]
        page=b.new_page()
        try:
          for link in ('/parallel/w05-browser/experimental/method-lab/index.html',
                       '/parallel/w05-browser/experimental/method-lab/worker.js',
                       '/experimental/evidence-viz/index.html'):
            response=page.goto(url+link)
            assert response and response.status==200,link
          page.goto(url+'/experimental/evidence-viz/index.html')
          assert page.locator('.ev-panel').count()==4
        finally:page.close()
      finally:b.close()
    print(json.dumps({'status':'PASS','views':views,'source':'synthetic-only'}))
  finally:server.shutdown();server.server_close()
if __name__=='__main__':main()
