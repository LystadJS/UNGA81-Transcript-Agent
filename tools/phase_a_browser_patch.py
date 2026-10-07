"""Exact-match integration changes on the implementation branch only."""
from pathlib import Path
import os
if os.environ.get('GITHUB_REF_NAME')!='feat/latent-comparison-phase-a':raise SystemExit('Wrong branch')
def patch(file,old,new):
 p=Path(file);text=p.read_text();assert text.count(old)==1,(file,old);p.write_text(text.replace(old,new))
patch('tools/test_latent_ui.cjs',"chromium.launch({headless:true})","chromium.launch({headless:true,...(process.env.PW_CHANNEL?{channel:process.env.PW_CHANNEL}:{})})")
patch('.github/workflows/latent-comparison.yml',
'''          npm install --prefix "$RUNNER_TEMP/latent-qa" --ignore-scripts --no-audit --no-fund playwright@1.55.0
          "$RUNNER_TEMP/latent-qa/node_modules/.bin/playwright" install --with-deps chromium''',
'''          timeout 120 npm install --prefix "$RUNNER_TEMP/latent-qa" --ignore-scripts --no-audit --no-fund --fetch-timeout=30000 --fetch-retries=1 playwright@1.55.0
          if command -v google-chrome >/dev/null; then
            google-chrome --version
            echo 'PW_CHANNEL=chrome' >> "$GITHUB_ENV"
          else
            timeout 180 "$RUNNER_TEMP/latent-qa/node_modules/.bin/playwright" install --only-shell chromium
          fi''')
# The counts in the renderer are intentionally numeric; enforce that boundary.
patch('site/latent-core.js',
"const ids=new Set();\n    for(const e of result.entries)",
"const checkCounts=c=>assert(c&&['input','eligible_before_dedup','duplicates','eligible','matched'].every(k=>Number.isSafeInteger(c[k])&&c[k]>=0),'Invalid saved source counts.');\n    checkCounts(result.counts);\n    const ids=new Set();\n    for(const e of result.entries)")
patch('site/latent-core.js',
"const by=new Map(e.result.matched.map(r=>[r.id,r]));assert(by.size===e.result.matched.length,'Duplicate saved passage identity.');",
"checkCounts(e.result.counts);\n      const by=new Map(e.result.matched.map(r=>[r.id,r]));assert(by.size===e.result.matched.length,'Duplicate saved passage identity.');")
print('Patched browser setup, installed Chrome support and numeric-rendering boundary.')
