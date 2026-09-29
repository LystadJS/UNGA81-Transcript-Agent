from pathlib import Path
import os
import sys
import shutil
from html import escape
import json
import base64
r=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
css=(r/'www/app.css').read_text()

seal_uri="data:image/png;base64,"+base64.b64encode((r/"www/seal.png").read_bytes()).decode()
def icon(name):
 return '<span class="ui-icon" aria-hidden="true">'+(r/"www"/(name+".svg")).read_text(encoding="utf-8")+'</span>'
# This is explicitly a static, read-only layout preview, not a Shiny session.
html='''<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>UN Readout — Static Interface Preview</title><style>'''+css+'''
.preview-strip{background:#fff6e7;padding:12px 30px;font-size:12px;color:#705021;border-bottom:1px solid #ecdbbd;line-height:1.5}.preview-strip strong{margin-right:8px}.form-group label{display:block}.date-preview{display:flex;gap:8px;align-items:center}.date-preview input{width:46%;padding:9px 7px;background:white}.preview-chips{display:flex;flex-wrap:wrap;gap:6px;border:1px solid #c7d1df;border-radius:6px;padding:10px;margin:7px 0 10px;min-height:120px}.chip{display:inline-flex;align-items:center;gap:12px;background:#eef3fa;border:1px solid #d6e0ef;color:#002d74;padding:6px 8px;font-size:12px;border-radius:4px}.chip span{color:#597091}.input-hint{width:100%;font-size:12px;color:#8893a1;padding:6px 0 2px}.preview-radio{display:block;font-size:12px;margin:12px 0;line-height:1.4}.preview-radio input{vertical-align:middle;margin:0 7px 0 0}.export-toolbar button{border:1px solid #D6DEE7}.nav-tabs{list-style:none;margin:0;padding:0;border-bottom:1px solid #D6DEE7}.nav-tabs li{margin:0;padding:0}.nav-tabs a{display:block;text-decoration:none}.empty-footnote{font-size:11px}.preview-pill{padding:8px 10px;font-size:11px;background:#edf3fa;color:#002d74;border-radius:4px;margin-top:16px}.preview-buttons{pointer-events:none}.email-frame{height:880px}.btn[disabled]{cursor:default;opacity:1}.generate-button{border:1px solid #002d74}.page-footer{line-height:1.6}
</style></head><body><div class="preview-strip"><strong>READ-ONLY INTERFACE PREVIEW</strong> This shows the intended layout with the R-generated practice draft. Controls do not run here. Open <b>Start.bat</b> after setup to use Shiny. Preview controls are illustrative; use Shiny for analysis.</div>
<header class="masthead"><img class="brand-mark" src="'''+seal_uri+'''" alt="U.S. Mission to the United Nations"><div><div class="eyebrow light">U.S. MISSION TO THE UNITED NATIONS</div><div class="brand-title">Daily Readout</div></div><div class="header-status">Local processing<span>/</span>Unsent drafts only</div></header>
<main class="app-shell"><div class="page-intro"><div><div class="eyebrow">YOUR BRIEFING, YOUR ISSUES</div><h1>What would you like to follow?</h1><p>Add your topics. The readout also checks the full transcript collection for other themes.</p></div><span class="status-badge">D1-I4 integrated · audit-gated</span></div>
<div class="workspace"><aside class="setup-card"><div class="card-heading"><span class="step-number">'''+icon("settings")+'''</span><h2>Set up your readout</h2></div>
<div class="form-group"><label class="control-label">Reporting period</label><div class="date-preview"><input aria-label="Start date" disabled class="form-control" value="Sep 23, 2026"><span>to</span><input aria-label="End date" disabled class="form-control" value="Sep 25, 2026"></div></div>
<label class="control-label">Issues I want to track</label><div class="preview-chips"><div class="chip">Iran <span>×</span></div><div class="chip">Cuba <span>×</span></div><div class="chip">Ukraine <span>×</span></div><div class="chip">Artificial Intelligence <span>×</span></div><div class="input-hint">Type an issue, then press Enter</div></div>
<p class="field-help">Type any topic and press Enter. Remove a topic with its ×. Up to 20 topics; none is also allowed.</p><p class="micro-note">Matching uses exact wording and approved related phrases, not automatic paraphrase interpretation.</p>
<details class="optional-panel"><summary>Refine matching <span>Optional</span></summary><p class="field-help">In the live application, add related phrases or passage-level exclusions.</p></details>
<div class="source-block"><label class="control-label">Transcripts</label><label class="preview-radio"><input type="radio" checked disabled>Practice with sample speeches</label><label class="preview-radio"><input type="radio" disabled>Use my transcript files</label><label class="preview-radio"><input type="radio" disabled>Use the installed pipeline</label><div class="source-notice">Practice sample: 18 fictional training statements, dated 24 September 2026. These are not UN speeches.</div></div>
<button disabled class="btn btn-primary generate-button">'''+icon("document")+'''Generate readout</button><p class="privacy-note">Nothing is emailed automatically. This prototype makes no external AI calls.</p><details class="optional-panel"><summary>Save my topics</summary><p class="field-help">The live application can save topics in this browser profile. No transcript text is stored there.</p></details></aside>
<section class="results-card"><div class="card-heading"><span class="step-number">'''+icon("document")+'''</span><h2>Review your readout</h2></div><div class="progress-panel complete"><p>Practice draft generated by the R backend. Analytical candidates remain audit-only.</p></div>
<div class="result-summary"><div class="result-metric"><strong>18</strong><span>available texts</span></div><div class="result-metric"><strong>4</strong><span>tracked topics</span></div><div class="result-scope"><strong>Sep 23–25, 2026</strong><span>Practice data · not a UN assessment</span></div></div>
<div class="export-toolbar preview-buttons"><button disabled class="btn btn-primary">'''+icon("mail")+'''Save email</button><button disabled class="btn btn-subtle">'''+icon("download")+'''Save PDF</button><button disabled class="btn btn-subtle">'''+icon("document")+'''Save HTML</button></div>
<ul class="nav nav-tabs"><li class="active"><a>'''+icon("mail")+'''Email preview</a></li><li><a>'''+icon("search")+'''Topic matches</a></li><li><a>'''+icon("themes")+'''Suggested themes</a></li><li><a>'''+icon("coverage")+'''Coverage</a></li></ul><div class="tab-content"><iframe class="email-frame" title="Actual R-generated synthetic email" sandbox="" srcdoc="'''+escape((r/'validation/demo_run/readout.html').read_text(encoding='utf-8'), quote=True)+'''"></iframe></div><details class="optional-panel analyst-panel"><summary>Evidence and diagnostics</summary><p>Source evidence, run settings, research candidates, and audit ZIP are separate from released email analysis.</p></details></section></div>
<footer class="page-footer">Static layout preview, not a running Shiny session. D1-I4 integration is available in installed-pipeline mode; outputs remain audit-gated and unsent.</footer></main></body></html>'''
(r/'Interface Preview.html').write_text(html,encoding='utf-8')
if "--html-only" in sys.argv:
 sys.exit(0)
from playwright.sync_api import sync_playwright
checks=[]
with sync_playwright() as p:
 container_mode=os.environ.get('UN_READOUT_BROWSER_NO_SANDBOX')=='1'
 browser_path=os.environ.get('CHROMOTE_CHROME') or shutil.which('chromium') or shutil.which('google-chrome')
 if not browser_path: raise RuntimeError('An approved local Chromium-family browser is required for this optional preview check.')
 browser=p.chromium.launch(executable_path=browser_path,headless=True,chromium_sandbox=not container_mode,args=['--disable-dev-shm-usage','--disable-gpu']+(['--no-zygote','--single-process'] if container_mode else []))
 try:
  page=browser.new_page(device_scale_factor=1)
  for width,height,name in [(1440,1200,'desktop'),(390,844,'mobile')]:
   page.set_viewport_size({'width':width,'height':height})
   errors=[]
   page.on('pageerror', lambda exc:errors.append(str(exc)))
   page.set_content(html,wait_until='load')
   page.screenshot(path=str(r/f'validation/interface_{name}.png'),full_page=False,timeout=15000)
   dimensions=page.evaluate('({viewport:innerWidth,document:document.documentElement.scrollWidth})')
   checks.append({'surface':'static_interface_preview','viewport':width,'no_horizontal_overflow':dimensions['document']<=width,'javascript_errors':errors,'not_live_shiny':True})

 finally:browser.close()
(r/'validation/static_preview_validation.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(checks,indent=2))
