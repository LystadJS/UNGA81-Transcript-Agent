"""One-time, exact-match integration patch; refuses drift and unrelated branches."""
from pathlib import Path
import os

if os.environ.get('GITHUB_REF_NAME') != 'feat/latent-comparison-phase-a':
    raise SystemExit('This integration patch is restricted to its implementation branch.')

def replace(path, old, new):
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    if text.count(old) != 1:
        raise ValueError(f'Expected exactly one original span in {path}')
    p.write_text(text.replace(old, new), encoding='utf-8')

replace('site/latent-core.js',
"const sum=m=>Array.from(m.values()).reduce((s,n)=>s+choose(n),0),expected=sum(rows)*sum(cols)/choose(a.length),top=(sum(rows)+sum(cols))/2;\n    return Math.abs(top-expected)<1e-15?1:(sum(cells)-expected)/(top-expected);",
"// Integer pair-count products avoid unnecessary fractional cancellation (n <= 600).\n    const sum=m=>Array.from(m.values()).reduce((s,n)=>s+choose(n),0);\n    const pairs=choose(a.length),row=sum(rows),col=sum(cols),numerator=2*(sum(cells)*pairs-row*col),denominator=(row+col)*pairs-2*row*col;\n    return denominator===0?1:numerator/denominator;")
replace('site/latent-core.js',
"p[key].length>=2&&p[key].every(Number.isFinite)",
"(key===fit.representation?p[key].length>=1:p[key].length===2)&&p[key].every(Number.isFinite)")
replace('site/latent-core.js',
"const manifest = records => records.map(r=>({id:r.id,text_sha256:r.text_sha256,parent_id:r.parent_id||null}));",
"const manifest = records => records.map(r=>({id:r.id,text_sha256:r.text_sha256,parent_id:r.parent_id||null,date:r.date,country:r.country,region:r.region,language:r.language,scope:r.scope,meeting:r.meeting,source_url:r.source_url,start:r.start??null,end:r.end??null}));")
replace('site/latent-ui.js',
"invalidate();const t=ticket,text=await read($('sourceFile').files[0]);",
"invalidate();payload=null;$('sourceStatus').textContent='Validating selected file type…';const t=ticket,text=await read($('sourceFile').files[0]);")
replace('site/latent-ui.js',
"invalidate();const t=ticket,text=await read($('savedA').files[0],L.LIMIT);",
"invalidate();payload=null;const t=ticket,text=await read($('savedA').files[0],L.LIMIT);")
replace('site/index.html',
'<a href="#analyze">Build a report</a>',
'<a href="#analyze">Build a report</a>\n      <a href="latent.html">Compare latent structure</a>')
replace('README.md',
'# UNGA81 Transcript Agent\n',
'# UNGA81 Transcript Agent\n\n**[Compare latent structure](https://lystadjs.github.io/un/transcript-agent/latent.html)**: saved-run replay, full-parent/reviewed-excerpt comparison, and reusable PCA/LSA, clustering, NMF and display settings. See the [comparison guide](docs/LATENT_COMPARISON.md) and the [unsupervised discovery roadmap](docs/NEXT_STEPS.md). Existing daily publication gates remain unchanged.\n')
print('Applied exact source, replay, UI-state and navigation patches; no numerical fitting engine or D1 file changed.')
