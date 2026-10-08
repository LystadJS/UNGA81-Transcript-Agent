#!/usr/bin/env python3
"""Offline browser acceptance: UN endpoints mocked; no transcript service contacted."""
import http.server,json,threading,functools,sys,pathlib,shutil,os
from playwright.sync_api import sync_playwright

ROOT=pathlib.Path(__file__).resolve().parents[1]/'site'
OUT=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path('/mnt/data/meeting-v2/browser')
OUT.mkdir(exist_ok=True,parents=True)
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
slug='ga/c3/81/1';date='2026-10-01';base='https://transcripts.un.org'
meeting={'slug':slug,'title':'Third Committee — SYNTHETIC reader test','date':date,'category':'General Assembly','pageUrl':'/en/'+slug,'jsonUrl':'/en/'+slug+'.json','hasTranscript':True}
def segment(country,text,function='Representative'):
 return {'speaker':{'affiliation':country,'affiliation_full':country,'function':function,'group':'National delegation'},'paragraphs':[{'sentences':[{'text':text}]}]}
records=[
 segment('Kenya','We strongly support humanitarian assistance for displaced people. Continued access to clean water and safe shelter requires transparent coordination among agencies. The delivery problem concerns people rather than abstract policy statements.'),
 segment('Kenya','We oppose humanitarian assistance in this wholly fictional counterexample. Its wording is deliberately included to exercise the mixed-position and source-evidence rules.'),
 segment('Brazil','We support renewable energy and climate action through technical assistance and practical cooperation. The discussion identified infrastructure, reporting, and public access as implementation priorities.'),
 segment('Brazil','We note that a third country supports sanctions. This is a reported position, not a statement by this delegation concerning economic restrictions.'),
 segment('Kenya','Thank you, Madam Chair. I now give the floor to the next speaker.','Chair'),
 segment('UNKNOWN','We welcome a humanitarian response focused on clean water and food security. This sentence is deliberately unattributed for testing. The meeting record should not invent a country identity.'),
]
transcript={'video':{'slug':slug,'date':date},'transcript':{'language':'en','timestamps_flagged':False,'data':records}}
countries=[{'country':n,'region':region,'iso3':code,'aliases':''} for n,region,code in [('Kenya','Africa','KEN'),('Brazil','Latin America','BRA')]]
errors=[];unwanted=[];fetches=[];result={}
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path=os.environ.get('CHROME_BINARY') or shutil.which('chromium') or shutil.which('google-chrome'),args=['--no-sandbox','--disable-dev-shm-usage'])
  page=browser.new_page(viewport={'width':1440,'height':940},accept_downloads=True)
  page.on('pageerror',lambda e:errors.append(str(e)))
  def block(req):
   if req.url.startswith('https://') and not req.url.startswith('https://transcripts.un.org/'):
    unwanted.append(req.url)
  page.on('request',block)
  def un(route):
   u=route.request.url;fetches.append(u)
   if '/meetings.json?' in u:data={'page':1,'total':1,'hasMore':False,'meetings':[meeting]}
   elif u.endswith(slug+'.json'):data=transcript
   else:raise AssertionError('Unexpected UN endpoint '+u)
   route.fulfill(status=200,headers={'access-control-allow-origin':'*'},content_type='application/json',body=json.dumps(data))
  page.route('https://transcripts.un.org/**',un)
  page.route('**/countries.json',lambda route: route.fulfill(status=200,content_type='application/json',body=json.dumps(countries)))
  page.goto('http://127.0.0.1:%s/index.html#analyze'%server.server_address[1])
  page.wait_for_function('document.querySelector("#region").options.length >= 3')
  page.locator('#meetingSelectionMode').select_option('single')
  page.locator('#singleMeetingDate').fill(date)
  page.locator('#findMeetings').click()
  page.wait_for_function('document.querySelector("#individualMeeting").options.length === 2')
  page.locator('#individualMeeting').select_option(slug)
  page.locator('#topic').fill('climate')
  page.locator('#runAnalysis').click()
  page.wait_for_function('!document.querySelector("#analysisOutput").hidden || document.querySelector("#analysisStatus").textContent.startsWith("Could not")',timeout=45000)
  assert page.locator('#analysisOutput').is_visible(),page.locator('#analysisStatus').inner_text()
  assert page.locator('.meeting-quick-read').count()==1
  assert page.locator('.meeting-quick-read').inner_text().find('Country-linked expressions')>=0
  assert 'mixed or qualified' in page.locator('.meeting-quick-read').inner_text().lower()
  assert page.locator('.meeting-quick-read a[href^="https://transcripts.un.org/"]').count()>=1
  with page.expect_download() as info:page.locator('#exportResult').click()
  download=info.value;save=OUT/'analysis.json';download.save_as(save)
  obj=json.loads(save.read_text())
  assert obj['quick_reader']['stats']['source_segments']==6
  assert obj['counts']['matched']<6
  assert obj['quick_reader']['stats']['recorded_countries']==2
  assert obj['quick_reader']['stats']['unresolved_country_segments']==1
  assert all(row['source_url'].startswith(base) for row in obj['quick_reader']['positions'] for row in row['evidence'])
  assert not any(row['country']=='Brazil' and row['issue_id']=='sanctions' for row in obj['quick_reader']['positions'])
  with page.expect_download() as info:page.locator('#exportHTML').click()
  info.value.save_as(OUT/'report.html')
  html=(OUT/'report.html').read_text()
  assert 'QUICK READER' in html and '<script' not in html
  assert html.index('QUICK READER')<html.index('Collection coverage')
  page.screenshot(path=str(OUT/'desktop.png'),full_page=True)
  page.set_viewport_size({'width':390,'height':850})
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Mobile horizontal overflow'
  page.screenshot(path=str(OUT/'mobile.png'),full_page=True)
  result={'status':'PASS','browser':browser.version,'checks':12,'fake_source_segments':6,'topic_filter_matches':obj['counts']['matched'],'quick_reader_all':obj['quick_reader']['stats']['source_segments'],'position_count':len(obj['quick_reader']['positions']),'no_external_ai':not unwanted,'un_requests':len(fetches),'errors':errors,'offsite_requests':unwanted}
  assert not errors and not unwanted,result
  (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
  browser.close()
finally:server.shutdown()
print(json.dumps(result))
