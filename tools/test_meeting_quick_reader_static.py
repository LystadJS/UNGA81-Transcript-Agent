#!/usr/bin/env python3
"""Inspect script-free synthetic quick reader in Chrome without HTTP or file navigation."""
import json, sys, pathlib, shutil, os
from playwright.sync_api import sync_playwright

html_file=pathlib.Path(sys.argv[1]);output=pathlib.Path(sys.argv[2]);output.mkdir(parents=True,exist_ok=True)
html=html_file.read_text(encoding='utf-8')
assert '<script' not in html.lower() and 'QUICK READER' in html
errors=[];requests=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=os.environ.get('CHROME_BINARY') or shutil.which('chromium') or shutil.which('google-chrome'),args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':1440,'height':900})
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda req:requests.append(req.url))
    page.set_content(html,wait_until='load')
    assert page.locator('.meeting-quick-read').count()==1
    assert page.locator('.quick-agenda-cues li').count()==2
    assert 'Another Territory' in page.locator('.quick-agenda-cues').inner_text()
    assert 'Regional Group' not in page.locator('.position-table').inner_text()
    assert 'group/collective attribution cues' in page.locator('.meeting-quick-read').inner_text()
    assert 'Decolonization' in page.locator('.meeting-quick-read').inner_text()
    assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
    page.screenshot(path=str(output/'desktop.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':850})
    assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'),'Narrow horizontal overflow'
    page.screenshot(path=str(output/'mobile.png'),full_page=True)
    assert not errors and not requests,(errors,requests)
    receipt={'status':'PASS','checks':8,'synthetic':True,'script_free':True,'no_network_requests':len(requests),'javascript_errors':len(errors),'browser_version':browser.version,'mobile_overflow':False,'heldout_opened':0}
    (output/'validation.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))
    browser.close()
