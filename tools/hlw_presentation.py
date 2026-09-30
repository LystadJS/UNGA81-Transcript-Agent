"""Render the existing Cuba evidence as an offline USUN-themed visual brief."""
import csv,html,json,shutil
from pathlib import Path

def render(out,stats,findings,country_index):
    out=Path(out);assets=Path(__file__).with_name('hlw_assets');h=html.escape
    for p in assets.iterdir():
        if p.name!='page.html':shutil.copyfile(p,out/p.name)
    rows=lambda name:list(csv.DictReader((out/name).open(encoding='utf-8-sig',newline='')))
    data={'evidence':rows('evidence.csv'),'coverage':rows('coverage.csv'),'stats':stats}
    payload=json.dumps(data,ensure_ascii=False).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    (out/'data.js').write_text('window.HLW_DATA='+payload+';\n',encoding='utf-8')
    cards=''.join('<article class="finding"><span class="number">'+f'{i:02d}'+'</span><div><h3>'+h(title)+'</h3><p>'+h(body)+'</p><div class="source-links">'+' '.join(f'<a href="{h(url)}">{h(label)} ↗</a>' for label,url in links)+'</div></div></article>' for i,(title,body,links) in enumerate(findings,1))
    table=''.join('<tr><td>'+h(x['country'])+'</td><td>'+h(x['date'])+'</td><td><a href="'+h(x['source_url'])+'">Source statement ↗</a></td></tr>' for x in sorted(country_index.values(),key=lambda x:x['country']))
    page=(assets/'page.html').read_text(encoding='utf-8').replace('@@FINDINGS@@',cards).replace('@@COUNTRIES@@',table)
    # Inline the established local outline icons; no external image dependencies.
    icons=Path(__file__).resolve().parents[1]/'un/ui/www'
    for name in ('coverage','themes','search','settings','download','document'):
        page=page.replace('@@ICON_'+name.upper()+'@@',(icons/(name+'.svg')).read_text(encoding='utf-8'))
    (out/'index.html').write_text(page,encoding='utf-8')
