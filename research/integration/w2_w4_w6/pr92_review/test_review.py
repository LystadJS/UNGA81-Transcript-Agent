"""Independent PR92 contrast and calculation review of fictional builds only.
No candidate arithmetic or rendering helper is imported. Authored colors, not
antialiased pixels, are compared. This is not complete WCAG certification.
"""
import argparse
from collections import defaultdict
from functools import partial
import hashlib
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import json
import math
from pathlib import Path
import threading
import unittest
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright, expect

CONFIG = {}
EXPECTED_HTML = '62af9c57400eef36cd58eee4b13abf5e854d78d956004b6a588cbcef4c030a94'
HISTORICAL = {
 'moving': (52, 'a2ad585d76c2d092f521d8d303d208e53ed07148cf2ba9829eed9da66a7c4d8d'),
 'missing-us': (57, '9feaf852650b1e0b67dffa7b3f926e8b203788a5d6c4e9b4c7ba0d73d868db46'),
 'support-gap': (53, 'a6b974be7e49f9f9f8c03941a1f4bc3ffc3e3935ee2d1d5359d3325a113443ff'),
 'hidden-dimension': (49, 'bda61a1ca440174f2d6b2fe96cef9bcb3a413bbf6403b58b3aa600bc9d3409aa'),
 'zero-gap': (45, 'b852cae528a67e2dcd22f0cebbbaca387f3ebb4bd536b375c82a7be816b25d3c'),
 'display-withheld': (21, '098c87cb1631f26c6c7ce3e5bbac296e7a37c1c44c4f4f9c7086c015f425861d'),
 'empty': (66, '28581c334a7478b59bcacb10caed07be4dfbdb2a3fd99e6987a19b04ab2c2f7c'),
 'failed-source': (49, '7e534ab552be934c34d8030fe6974169f83b66d4d914b1158c1291c187e02bc9'),
 'moving-mobile': (52, '1a75374054de538b0e916afcc9c018a0f19fb1af93a4af6b4b6c725dc05f322c')}

# No PASS decision occurs in this browser collector. Python owns thresholds.
# Unknown image/compositing types are rejected, never omitted from coverage.
COLLECT = r'''selectors => {
 const canvas=document.createElement('canvas');canvas.width=canvas.height=1;
 const ctx=canvas.getContext('2d',{willReadFrequently:true});
 function rgb(s) {ctx.clearRect(0,0,1,1);ctx.fillStyle=s;ctx.fillRect(0,0,1,1);return [...ctx.getImageData(0,0,1,1).data];}
 function read(el,selector) {
   const cs=getComputedStyle(el),isSVG=el.tagName.toLowerCase()==='text';
   const fg=rgb(isSVG?cs.fill:cs.color),backdrops=[];
   if(isSVG && +cs.fillOpacity!==1)throw Error('Unsupported text fill opacity');
   for(let e=el;e;e=e.parentElement){const s=getComputedStyle(e);
     if(+s.opacity!==1||s.filter!=='none'||s.mixBlendMode!=='normal')throw Error('Unsupported compositing');
     if(s.backgroundImage!=='none') {
       if(e!==el||!el.classList.contains('unavailable')||!s.backgroundImage.startsWith('repeating-linear-gradient('))throw Error('Unsupported background image');
       const colors=s.backgroundImage.match(/rgba?\([^)]*\)/g)||[];
       if(colors.length!==4)throw Error('Unreviewed patterned background');
       colors.forEach(c=>backdrops.push(rgb(c)));break;
     }
     const bg=rgb(s.backgroundColor);if(bg[3]===255){backdrops.push(bg);break;}
     if(bg[3]!==0)throw Error('Unsupported background alpha');
   }
   if(!backdrops.length||fg[3]!==255||backdrops.some(b=>b[3]!==255))throw Error('No opaque authored color pair');
   const r=el.getBoundingClientRect();
   return {selector,tag:el.tagName.toLowerCase(),text:el.textContent,foreground:fg,backgrounds:backdrops,
     background_image:cs.backgroundImage,font_size:cs.fontSize,rect:{x:r.x,y:r.y,width:r.width,height:r.height},
     outline:cs.outlineStyle==='none'?null:rgb(cs.outlineColor),outline_width:parseFloat(cs.outlineWidth)};
 }
 return selectors.map(selector=>{const all=document.querySelectorAll(selector);if(all.length!==1)throw Error('Nonunique target: '+selector);return read(all[0],selector);});
}'''


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def luminance(rgb):
    values=[v/255 for v in rgb[:3]]
    values=[v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4 for v in values]
    return sum(w*v for w,v in zip((0.2126,0.7152,0.0722),values))


def contrast(a,b):
    x,y=sorted((luminance(a),luminance(b)))
    return (y+0.05)/(x+0.05)


def assess(record, threshold=4.5):
    ratios=[contrast(record['foreground'],bg) for bg in record['backgrounds']]
    return {**record,'minimum_ratio':min(ratios),'threshold':threshold,'passed':min(ratios)>=threshold}


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if urlsplit(self.path).path!='/index.html':
            self.send_error(404);return
        super().do_GET()
    def log_message(self,*_):
        pass


class Review(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=CONFIG['build'];cls.out=CONFIG['out'];cls.out.mkdir(parents=True,exist_ok=True)
        cls.catalogue=json.loads((cls.root/'catalogue.json').read_text())
        cls.inputs=json.loads((cls.root/'verification.json').read_text())
        cls.prior=json.loads(CONFIG['axe_results'].read_text())
        cls.audit=[];cls.stats={}
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(cls.root)))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.origin=f'http://127.0.0.1:{cls.server.server_port}'
        cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch(headless=True)
    @classmethod
    def tearDownClass(cls):
        (cls.out/'contrast-resolution.json').write_text(json.dumps(cls.audit,indent=2)+'\n')
        (cls.out/'observations.json').write_text(json.dumps(cls.stats,indent=2)+'\n')
        cls.browser.close();cls.pw.stop();cls.server.shutdown();cls.server.server_close()
    def setUp(self):
        self.context=self.browser.new_context(viewport={'width':1440,'height':1080},accept_downloads=True)
        self.requests=[];self.errors=[]
        def guard(route):
            url=route.request.url
            if url.startswith(self.origin+'/') or url.startswith(('blob:','data:')):route.continue_()
            else:self.requests.append(url);route.abort()
        self.context.route('**/*',guard)
        self.page=self.context.new_page();self.page.on('pageerror',lambda e:self.errors.append(str(e)))
        self.page.goto(self.origin+'/index.html',wait_until='load');self.ready()
    def tearDown(self):
        self.context.close();self.assertEqual(self.requests,[]);self.assertEqual(self.errors,[])
    def ready(self):
        expect(self.page.locator('#status')).to_have_attribute('data-state','ready')
    def select(self,scene,country='CAN',period='p4',width=1440):
        self.page.set_viewport_size({'width':width,'height':1080})
        self.page.locator('#scenario').select_option(scene)
        self.page.locator('#country').select_option(country)
        self.page.locator('#period').select_option(period);self.ready()
    def test_01_exact_build_and_incomplete_inventory(self):
        self.assertEqual(sha((self.root/'index.html').read_bytes()),EXPECTED_HTML)
        self.assertEqual({s['scene'] for s in self.prior},set(HISTORICAL))
        for scene in self.prior:
            self.assertEqual(scene['violations'],[])
            self.assertEqual({x['id'] for x in scene['incomplete']},{'color-contrast'})
            n,h=HISTORICAL[scene['scene']]
            self.assertEqual(sum(len(i['targets']) for i in scene['incomplete']),n)
            self.assertEqual(sha(json.dumps(scene['incomplete'],sort_keys=True,separators=(',',':')).encode()),h)
        self.stats['historical_targets']=sum(x[0] for x in HISTORICAL.values())
    def test_02_every_incomplete_target_has_measured_contrast(self):
        for scene in self.prior:
            mobile=scene['scene'].endswith('-mobile')
            self.select('moving' if mobile else scene['scene'],width=390 if mobile else 1440)
            selectors=[target[0] for rule in scene['incomplete'] for target in rule['targets']]
            self.assertTrue(all(len(t)==1 for r in scene['incomplete'] for t in r['targets']))
            rows=self.page.evaluate(COLLECT,selectors)
            evaluated=[assess(r) for r in rows]
            self.audit.append({'scene':scene['scene'],'source':'historical-axe-targets','records':evaluated})
            failures=[r for r in evaluated if not r['passed']]
            self.assertEqual(failures,[],json.dumps(failures))
            self.page.screenshot(path=str(self.out/(scene['scene']+'.png')),full_page=True)
        self.stats['resolved_historical_targets']=sum(len(x['records']) for x in self.audit)
    def test_03_all_country_palettes_and_patterned_states(self):
        cases=0;minimum=21
        for scene in self.catalogue['scenes']:
            for country in scene['model']['scope']['countries']:
                self.select(scene['id'],country)
                selectors=self.page.evaluate('''() => [...document.querySelectorAll('svg text,#matrix button')].map((el,i)=>{el.dataset.reviewTarget=String(i);return '[data-review-target="'+i+'"]';})''')
                records=[assess(r) for r in self.page.evaluate(COLLECT,selectors)]
                self.audit.append({'scene':scene['id'],'country':country,'source':'all-country-palette','records':records})
                failures=[r for r in records if not r['passed']]
                self.assertEqual(failures,[],json.dumps(failures))
                minimum=min(minimum,*(r['minimum_ratio'] for r in records));cases+=1
        self.stats.update(palette_selections=cases,palette_minimum_ratio=minimum)
    def test_04_contrast_negative_controls_do_not_pass(self):
        self.assertEqual(contrast([0,0,0],[255,255,255]),21)
        self.assertEqual(contrast([60,60,60],[60,60,60]),1)
        self.assertLess(contrast([119]*3,[255]*3),4.5)
        self.assertGreater(contrast([118]*3,[255]*3),4.5)
        selector='#absolute svg text:first-of-type'
        self.page.locator(selector).evaluate("el=>el.style.fill='white'")
        self.assertFalse(assess(self.page.evaluate(COLLECT,[selector])[0])['passed'])
        self.page.locator('#matrix button.unavailable').first.evaluate("el=>{el.id='review-negative';el.style.setProperty('color','white','important');}")
        self.assertFalse(assess(self.page.evaluate(COLLECT,['#review-negative'])[0])['passed'])
    def test_05_focus_and_required_graphic_marks(self):
        ratios=[]
        for c in self.catalogue['scenes'][0]['model']['scope']['countries']:
            self.select('moving',c)
            marks=self.page.evaluate('''() => [...document.querySelectorAll('svg [data-edge],svg g[role=button] circle,svg g[role=button] rect')].map(e=>{let s=getComputedStyle(e);return {fill:s.fill,stroke:s.stroke};})''')
            for mark in marks:
                for value in mark.values():
                    if value in ('none','rgba(0, 0, 0, 0)','rgb(255, 255, 255)'):continue
                    channels=[float(v) for v in value.removeprefix('rgb(').removesuffix(')').split(',')]
                    ratios.append(contrast(channels,[255,255,255]))
            self.page.locator('#matrix button[aria-pressed=true]').focus()
            r=self.page.evaluate(COLLECT,['#matrix button[aria-pressed=true]'])[0]
            self.assertIsNotNone(r['outline']);self.assertGreaterEqual(r['outline_width'],3)
            for bg in r['backgrounds']:ratios.append(contrast(r['outline'],bg))
        self.assertTrue(ratios);self.assertGreaterEqual(min(ratios),3)
        self.stats['minimum_graphic_focus_ratio']=min(ratios)
    def test_06_independent_source_weights_and_distances(self):
        profiles=0;comparisons=0;transitions=0
        for bundle in self.inputs:
            source,model=bundle['source'],bundle['model'];scope=source['scope'];computed={}
            self.assertEqual(source['split'],'synthetic')
            self.assertEqual(model,next(s['model'] for s in self.catalogue['scenes'] if s['id']==bundle['id']))
            for profile in model['profiles']:
                candidates=[r for r in source['observations'] if r['country_iso3']==profile['country_iso3'] and r['period']==profile['period']]
                usable=[r for r in candidates if r['source_status']=='available' and r['capacity']=='national' and r['attribution_status']=='synthetic_verified' and r['genre'] in scope['genres'] and all(r[k]==scope[k] for k in ('language','topic_id','source_type'))]
                if not usable or {r['genre'] for r in usable}!=set(scope['genres']):
                    self.assertIsNone(profile['vector']);self.assertEqual(profile['contributions'],[]);computed[profile['id']]=None;continue
                grouped=defaultdict(lambda:defaultdict(list))
                for r in usable:grouped[r['genre']][r['meeting_id']].append(r)
                weights={r['id']:1/(len(grouped)*len(meetings)*len(rows)) for meetings in grouped.values() for rows in meetings.values() for r in rows}
                self.assertEqual(set(weights),{r['observation_id'] for r in profile['contributions']})
                for r in profile['contributions']:self.assertAlmostEqual(r['weight'],weights[r['observation_id']],places=12)
                v=[math.fsum(weights[r['id']]*r['vector'][j] for r in usable) for j in range(source['metric_space']['dimension'])]
                for a,b in zip(v,profile['vector']):self.assertAlmostEqual(a,b,places=12)
                computed[profile['id']]=v;profiles+=1
            for row in model['comparisons']:
                c=computed[row['id']];u=computed['USA/'+row['period']]
                if c is None or u is None:self.assertIsNone(row['distance'])
                else:self.assertAlmostEqual(row['distance'],math.dist(c,u),places=12)
                comparisons+=1
            order=[p['id'] for p in model['periods']]
            for t in model['transitions']:
                self.assertEqual(order.index(t['after']),order.index(t['before'])+1)
                if t['metrics'] is not None:
                    c0=computed[t['country_iso3']+'/'+t['before']];c1=computed[t['country_iso3']+'/'+t['after']]
                    u0=computed['USA/'+t['before']];u1=computed['USA/'+t['after']]
                    delta=math.dist(c1,u1)-math.dist(c0,u0)
                    self.assertAlmostEqual(t['metrics']['gap_change'],delta,places=12)
                    if t['metrics']['decomposition_status']=='ready':self.assertAlmostEqual(t['metrics']['gap_country_contribution']+t['metrics']['gap_us_contribution'],delta,places=12)
                transitions+=1
        self.stats.update(independent_ready_profiles=profiles,independent_comparisons=comparisons,independent_transitions=transitions)
    def test_07_export_text_contrast(self):
        with self.page.expect_download() as pending:self.page.get_by_role('button',name='Export SVG',exact=True).click()
        dest=self.out/'review-export.svg';pending.value.save_as(dest)
        import xml.etree.ElementTree as ET
        root=ET.parse(dest).getroot();ns={'s':'http://www.w3.org/2000/svg'}
        texts=root.findall('.//s:text',ns);self.assertGreater(len(texts),40)
        for e in texts:
            color=e.attrib.get('fill');self.assertIsNotNone(color);self.assertTrue(color.startswith('#'))
            rgb=[int(color[i:i+2],16) for i in (1,3,5)]
            self.assertGreaterEqual(contrast(rgb,[255,255,255]),4.5)
        self.assertFalse(root.findall('.//s:script',ns));self.stats['export_text_nodes']=len(texts)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--axe-results',type=Path,required=True);a=p.parse_args()
    CONFIG.update(build=a.build.resolve(),out=a.out.resolve(),axe_results=a.axe_results.resolve())
    CONFIG['out'].mkdir(parents=True,exist_ok=True)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Review))
    receipt={'suite':'pr92-independent-contrast-review','tests_run':r.testsRun,'failures':[str(t) for t,_ in r.failures],
       'errors':[str(t) for t,_ in r.errors],'skipped':[str(t) for t,_ in r.skipped],
       'result':'pass' if r.wasSuccessful() and not r.skipped else 'fail',
       'scope':'synthetic engineering; authored text and essential graphic/focus color pairs',
       'publication_eligible':False,'real_sources_opened':0,'complete_wcag_certification':False}
    (CONFIG['out']/'review-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    raise SystemExit(0 if receipt['result']=='pass' else 1)
