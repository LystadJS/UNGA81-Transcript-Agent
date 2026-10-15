"""Strict served Chromium, local-file replay, exports and accessibility acceptance.

A fresh browser context is created for every test. Only generated fictional HTML
is served. Runtime absence is a failure, not a skipped acceptance test.
"""
from __future__ import annotations
import argparse
import csv
from functools import partial
import hashlib
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import io
import json
import os
from pathlib import Path
import platform
import struct
import threading
import unittest
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright, expect

CONFIG = {}


class LocalOnlyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if urlsplit(self.path).path not in ('/index.html', '/roundtrip.html', '/corrupt.html'):
            self.send_error(404)
            return
        super().do_GET()

    def log_message(self, *_):
        pass


class BrowserAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = CONFIG['build']
        cls.out = CONFIG['out']
        cls.out.mkdir(parents=True, exist_ok=True)
        cls.cat = json.loads((cls.root/'catalogue.json').read_text())
        cls.axe = Path(CONFIG['axe']).read_text() if CONFIG['axe'] else None
        if CONFIG['require_axe'] and not cls.axe:
            raise AssertionError('Pinned axe-core is mandatory in coordinator acceptance')
        cls.a11y = []
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(LocalOnlyHandler, directory=str(cls.root)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'
        cls.pw = sync_playwright().start()
        kwargs = dict(headless=True, args=['--no-sandbox'])
        if CONFIG['chromium']:
            kwargs['executable_path'] = CONFIG['chromium']
        cls.browser = cls.pw.chromium.launch(**kwargs)
        cls.version = cls.browser.version

    @classmethod
    def tearDownClass(cls):
        (cls.out/'axe-results.json').write_text(json.dumps(cls.a11y, indent=2)+'\n')
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width':1440,'height':1080}, accept_downloads=True)
        self.attempts = []
        def route(r):
            url = r.request.url
            if url.startswith(self.url+'/') or url.startswith(('blob:', 'data:', 'file:')):
                r.continue_()
            else:
                self.attempts.append(url)
                r.abort()
        self.context.route('**/*', route)
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda e:self.errors.append(str(e)))
        self.page.goto(self.url+'/index.html', wait_until='load')
        self.ready()

    def tearDown(self):
        self.assertEqual(self.errors, [], 'Unexpected browser errors')
        self.assertEqual(self.attempts, [], 'The application attempted nonlocal networking')
        self.context.close()

    def ready(self):
        expect(self.page.locator('#status')).to_have_attribute('data-state', 'ready')

    def scene(self, name):
        self.page.locator('#scenario').select_option(name)
        expect(self.page.locator('#scenario')).to_have_value(name)
        self.ready()

    def export(self, label, filename):
        with self.page.expect_download() as pending:
            self.page.get_by_role('button', name=label, exact=True).click()
        path=self.out/filename
        pending.value.save_as(path)
        self.assertIsNone(pending.value.failure())
        self.assertGreater(path.stat().st_size, 0)
        return path

    def test_01_served_paired_paths_and_full_frame(self):
        self.assertEqual(self.page.locator('svg').count(),4)
        self.assertEqual(self.page.locator('#matrix button').count(),30)
        self.assertEqual(self.page.locator('#absolute [data-edge^="USA:"]').count(),4)
        self.assertEqual(self.page.locator('#absolute svg').get_attribute('data-radius'),self.page.locator('#relative svg').get_attribute('data-radius'))
        self.assertEqual(self.page.locator('#absolute svg').get_attribute('viewBox'),self.page.locator('#relative svg').get_attribute('viewBox'))
        self.page.screenshot(path=str(self.out/'desktop.png'),full_page=True)

    def test_02_filter_and_keyboard_preserve_baseline(self):
        before=self.page.evaluate("JSON.parse(document.getElementById('catalogue').textContent).scenes[0].model.baseline")
        scale=self.page.locator('#absolute svg').get_attribute('data-radius')
        self.page.locator('#country').select_option('FRA')
        self.assertEqual(self.page.locator('#absolute svg').get_attribute('data-radius'),scale)
        focus=self.page.locator('#absolute [tabindex="0"]')
        focus.focus();self.page.keyboard.press('ArrowLeft');self.page.keyboard.press('Enter')
        self.assertIn('display coordinates',self.page.locator('#point-detail').inner_text())
        self.assertEqual(self.page.evaluate('document.activeElement.tagName.toLowerCase()'),'g')
        after=self.page.evaluate("JSON.parse(document.getElementById('catalogue').textContent).scenes[0].model.baseline")
        self.assertEqual(before,after)

    def test_03_missing_us_never_bridges_or_zero_fills(self):
        self.scene('missing-us');self.page.locator('#period').select_option('p2')
        self.assertIn('Unavailable',self.page.locator('#summary').inner_text())
        for kind in ('absolute','relative','gap'):
            self.assertEqual(self.page.locator(f'#{kind} [data-p-index="2"]').count(),0)
            edges=self.page.locator(f'#{kind} [data-edge]').evaluate_all('(xs)=>xs.map(x=>x.dataset.edge)')
            self.assertTrue(all(':p1:p3' not in e and ':p2:' not in e and not e.endswith(':p2') for e in edges))
        self.assertEqual(self.page.locator('#matrix button[data-period="p2"]').all_text_contents(),['No US']*6)
        self.assertIn('withheld',self.page.locator('#contributions').inner_text().lower())

    def test_04_display_withheld_keeps_metric_and_no_coordinates(self):
        self.scene('display-withheld')
        self.assertEqual(self.page.locator('#absolute svg,#relative svg').count(),0)
        self.assertEqual(self.page.locator('#gap svg').count(),1)
        self.assertNotIn('Unavailable',self.page.locator('#summary > div').nth(1).inner_text())
        self.assertIn('Display withheld',self.page.locator('#absolute').inner_text())

    def test_05_hidden_dimension_and_zero_gap_are_not_stationarity_claims(self):
        self.scene('hidden-dimension')
        self.assertEqual(self.page.locator('#summary strong').nth(1).inner_text(),'4')
        self.assertEqual(self.page.locator('#summary strong').nth(2).inner_text(),'0%')
        self.scene('zero-gap')
        self.assertEqual(self.page.locator('#summary strong').nth(1).inner_text(),'0')
        self.assertIn('undefined',self.page.locator('#contributions').inner_text())

    def test_06_empty_failed_and_support_states_keep_the_frame(self):
        for scene, word in [('empty','No US'),('failed-source','Failed'),('support-gap','Scope gap')]:
            self.scene(scene)
            self.assertEqual(self.page.locator('#matrix button').count(),30)
            self.assertIn(word,self.page.locator('#matrix').inner_text())
        self.page.locator('#matrix button[data-country="CAN"][data-period="p2"]').click()
        self.assertEqual(self.page.locator('#period').input_value(),'p2')
        self.assertEqual(self.page.locator('#country').input_value(),'CAN')

    def test_07_both_source_sides_retain_weights_hashes_and_original_identities(self):
        self.page.locator('#country').select_option('FRA')
        self.page.locator('#period').select_option('p1')
        self.assertIn('Comparator sources · FRA',self.page.locator('#evidence').inner_text())
        self.assertIn('US reference sources · USA',self.page.locator('#evidence').inner_text())
        self.page.locator('#evidence details').first.locator('summary').click()
        data=json.loads(self.page.locator('#evidence pre').first.inner_text())
        self.assertEqual(data['weight'],.5)
        self.assertEqual(data['original_code_point_offsets'],[0,10])
        self.assertTrue(data['synthetic_pointer'].startswith('/synthetic/'))
        self.assertIn('FRA',data['actor_id'])
        self.assertEqual(len(data['source_sha256']),64)

    def test_08_replay_is_exact_and_rejects_arbitrary_models(self):
        replay=self.page.evaluate('window.USReferenceView.getReplay()')
        self.scene('missing-us')
        self.page.locator('#replay-file').set_input_files(dict(name='replay.json',mimeType='application/json',buffer=json.dumps(replay).encode()))
        self.ready()
        self.assertEqual(self.page.evaluate('window.USReferenceView.getReplay()'),replay)
        variants=[{**replay,'publication_eligible':True},{**replay,'model':{}},{**replay,'source_text':'<script id="injected-marker">bad()</script>'},
                  {**replay,'catalogue_sha256':'f'*64},{**replay,'period':'2026-10-05'}]
        for value in variants:
            self.page.get_by_role('button',name='Reset view',exact=True).click()
            self.page.locator('#replay-file').set_input_files(dict(name='bad.json',mimeType='application/json',buffer=json.dumps(value).encode()))
            expect(self.page.locator('#status')).to_have_attribute('data-state', 'failed')
            self.assertEqual(self.page.locator('svg,#evidence pre').count(),0)
            self.assertEqual(self.page.locator('[data-export]:disabled').count(),5)
            self.assertEqual(self.page.locator('#injected-marker').count(),0)

    def test_09_cancel_and_out_of_order_import_never_restore_stale_views(self):
        result=self.page.evaluate('''async()=>{const c=window.USReferenceView,saved=c.getReplay();let resolve;
          const pending=c.importFile({size:100,text:()=>new Promise(r=>resolve=r)});
          c.cancel();resolve(JSON.stringify(saved));await pending;
          return {state:document.getElementById('status').dataset.state,svg:document.querySelectorAll('svg').length};}''')
        self.assertEqual(result,{'state':'cancelled','svg':0})
        self.page.get_by_role('button',name='Reset view',exact=True).click()
        result=self.page.evaluate('''async()=>{const c=window.USReferenceView,saved=c.getReplay();let resolve;
          const pending=c.importFile({size:100,text:()=>new Promise(r=>resolve=r)});
          const select=document.getElementById('scenario');select.value='hidden-dimension';select.dispatchEvent(new Event('change'));
          resolve(JSON.stringify(saved));await pending;return c.getReplay().scene_id;}''')
        self.assertEqual(result,'hidden-dimension')

    def test_10_oversized_import_is_rejected_before_reading(self):
        result=self.page.evaluate('''async()=>{let read=false;await window.USReferenceView.importFile({size:8193,text:()=>{read=true;return Promise.resolve('{}');}});
          return {read,state:document.getElementById('status').dataset.state};}''')
        self.assertEqual(result,{'read':False,'state':'failed'})

    def test_11_svg_and_png_exports_are_safe_and_nonempty(self):
        svg=self.export('Export SVG','paired-trajectories.svg')
        root=ET.fromstring(svg.read_text())
        ids=[e.attrib['id'] for e in root.iter() if 'id' in e.attrib]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertFalse(any(e.tag.split('}')[-1] in ('script','foreignObject') for e in root.iter()))
        self.assertFalse(any(k.lower().startswith('on') for e in root.iter() for k in e.attrib))
        metadata=json.loads(root.find('{http://www.w3.org/2000/svg}metadata').text)
        self.assertFalse(metadata['publication_eligible'])
        self.assertEqual(metadata['model_sha256'],self.cat['scenes'][0]['model']['sha256'])
        png=self.export('Export PNG','paired-trajectories.png').read_bytes()
        self.assertEqual(png[:8],b'\x89PNG\r\n\x1a\n')
        self.assertEqual(struct.unpack('>II',png[16:24]),(2000,1880))
        self.assertGreater(len(png),15000)

    def test_12_csv_and_json_preserve_missingness_and_replay(self):
        self.scene('missing-us')
        path=self.export('Export CSV','all-country-gaps.csv')
        rows=list(csv.DictReader(io.StringIO(path.read_text())))
        self.assertEqual(len(rows),30)
        absent=next(r for r in rows if r['comparison_id']=='USA/p2')
        self.assertEqual(absent['distance'],'');self.assertEqual(absent['reason'],'baseline_missing')
        replay=json.loads(self.export('Export replay JSON','view-replay.json').read_text())
        self.assertEqual(replay,self.page.evaluate('window.USReferenceView.getReplay()'))

    def test_13_standalone_html_replays_served_and_from_local_file(self):
        self.scene('hidden-dimension');self.page.locator('#period').select_option('p3')
        expected=self.page.evaluate('window.USReferenceView.getReplay()')
        path=self.export('Export standalone HTML','standalone.html')
        (self.root/'roundtrip.html').write_bytes(path.read_bytes())
        self.page.goto(self.url+'/roundtrip.html');self.ready()
        self.assertEqual(self.page.evaluate('window.USReferenceView.getReplay()'),expected)
        self.page.goto(path.as_uri());self.ready()  # Mandatory native offline-file acceptance.
        self.assertEqual(self.page.evaluate('window.USReferenceView.getReplay()'),expected)

    def test_14_modified_catalogue_bytes_fail_before_any_render(self):
        html=(self.root/'index.html').read_text().replace('Moving US reference','Corrupt US reference',1)
        (self.root/'corrupt.html').write_text(html)
        self.page.goto(self.url+'/corrupt.html')
        expect(self.page.locator('#status')).to_have_attribute('data-state', 'failed')
        self.assertEqual(self.page.locator('svg').count(),0)
        self.assertEqual(self.page.locator('[data-export]:disabled').count(),5)

    def test_15_mobile_zoom_reduced_motion_and_semantic_alternatives(self):
        for width in (390,320):
            self.page.set_viewport_size({'width':width,'height':844})
            self.page.wait_for_timeout(100)
            self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            self.assertEqual(self.page.locator('#matrix button').count(),30)
            self.assertEqual(self.page.locator('main').count(),1)
            self.assertEqual(self.page.locator('h1').count(),1)
        self.page.set_viewport_size({'width':390,'height':844});self.page.wait_for_timeout(100)
        self.page.emulate_media(reduced_motion='reduce')
        self.assertEqual(self.page.evaluate('document.getAnimations().length'),0)
        self.page.screenshot(path=str(self.out/'mobile.png'),full_page=True)
        for s in self.page.locator('svg').all():
            self.assertTrue(s.get_attribute('aria-labelledby'))
        self.assertTrue(self.page.get_by_role('table').get_by_role('caption').count() or self.page.locator('caption').count())

    def test_16_cancel_suppresses_pending_png_export(self):
        downloads=[]
        self.page.on('download', lambda d:downloads.append(d))
        self.page.evaluate('''()=>{window.OriginalImage=window.Image;window.Image=class {
          set src(value){window.finishTestImage=()=>this.onload();}
        };}''')
        self.page.get_by_role('button',name='Export PNG',exact=True).click()
        self.page.get_by_role('button',name='Cancel and clear',exact=True).click()
        self.page.evaluate('''async()=>{window.finishTestImage();await new Promise(r=>setTimeout(r,0));window.Image=window.OriginalImage;}''')
        self.assertEqual(downloads,[])
        self.assertEqual(self.page.locator('svg').count(),0)

    def test_17_axe_wcag21_aa_all_scenarios(self):
        if not self.axe:
            self.fail('axe-core must be supplied; this is not optional acceptance')
        self.page.evaluate(self.axe)
        for scene in self.cat['scenes']:
            self.scene(scene['id'])
            result=self.page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")
            record=dict(scene=scene['id'],engine=result['testEngine'],
                        violations=[dict(id=v['id'],impact=v['impact'],targets=[n['target'] for n in v['nodes']]) for v in result['violations']],
                        incomplete=[dict(id=v['id'], targets=[n['target'] for n in v['nodes']]) for v in result['incomplete']])
            self.a11y.append(record)
            self.assertEqual(record['violations'],[],json.dumps(record))
        self.page.set_viewport_size({'width':390,'height':844});self.scene('moving')
        result=self.page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")
        self.a11y.append(dict(scene='moving-mobile',engine=result['testEngine'],violations=[v['id'] for v in result['violations']],incomplete=[dict(id=v['id'], targets=[n['target'] for n in v['nodes']]) for v in result['incomplete']]))
        self.assertEqual(result['violations'],[])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir',type=Path,required=True)
    parser.add_argument('--artifact-dir',type=Path,required=True)
    parser.add_argument('--axe',default=os.environ.get('AXE_PATH'))
    parser.add_argument('--require-axe',action='store_true')
    parser.add_argument('--chromium',default=os.environ.get('CHROMIUM_PATH'))
    args=parser.parse_args()
    CONFIG.update(build=args.build_dir.resolve(),out=args.artifact_dir.resolve(),axe=args.axe,require_axe=args.require_axe,chromium=args.chromium)
    CONFIG['out'].mkdir(parents=True,exist_ok=True)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BrowserAcceptance))
    receipt=dict(suite='phase2-strict-browser',tests_run=result.testsRun,failures=[str(t) for t,_ in result.failures],
                 errors=[str(t) for t,_ in result.errors],skipped=[str(t) for t,_ in result.skipped],
                 browser=getattr(BrowserAcceptance,'version',None),python=platform.python_version(),
                 result='pass' if result.wasSuccessful() and not result.skipped else 'fail',
                 source_scope='generated_synthetic_only',publication_eligible=False)
    (CONFIG['out']/'browser-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() and not result.skipped else 1)
