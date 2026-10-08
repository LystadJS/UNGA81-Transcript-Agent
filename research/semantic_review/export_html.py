"""Export the executed notebook as a self-contained, script-free reading copy."""
from pathlib import Path
import argparse
import nbformat
import mistune

CSS="""body{margin:0;background:#f5f5f3;color:#252d34;font:17px/1.6 Georgia,serif}main{max-width:1020px;margin:auto;background:white;padding:36px 48px 70px;border-top:9px solid #243b53}h1,h2,h3,h4{font-family:Arial,sans-serif;color:#243b53;line-height:1.25}h1{font-size:36px;margin:0 0 16px}h2{font-size:26px;margin:36px 0 16px;border-bottom:2px solid #b19a6a;padding-bottom:10px}h3{font-size:22px;margin-top:32px}a{color:#214e72;overflow-wrap:anywhere}code{font-size:14px;overflow-wrap:anywhere}p{margin:12px 0 18px}figure{margin:22px 0}img{display:block;max-width:100%;height:auto}table{border-collapse:collapse;width:100%;font:14px/1.45 Arial,sans-serif}th,td{padding:9px 10px;text-align:left!important;border-bottom:1px solid #dde1e5;vertical-align:top;overflow-wrap:anywhere}tbody th{min-width:64px}th{font-weight:bold;background:#edf1f4}thead tr{text-align:left!important}.table-wrap{overflow-x:auto;margin:16px 0 24px}.example{border-left:3px solid #b19a6a;padding:0 0 0 20px;margin:22px 0}.example p{font-size:16px}footer{margin-top:35px;color:#59636b;font:14px Arial,sans-serif}@media(max-width:600px){main{padding:24px 16px 40px}body{font-size:16px}h1{font-size:29px}h2{font-size:23px}h3{font-size:20px}th,td{padding:7px}figure{margin:18px -8px}.example{padding-left:12px}}@media print{body{background:white}main{max-width:none;padding:0;border-top:0}figure,table{break-inside:avoid}}"""

def export(path: Path) -> Path:
    nb=nbformat.read(path,as_version=4)
    parts=[];fig=0;md=mistune.create_markdown(escape=False,plugins=['table'])
    for cell in nb.cells:
        if cell.cell_type=='markdown':parts.append(md(cell.source))
        elif cell.cell_type=='code':
            if cell.get('execution_count') is None:raise ValueError('Execute all notebook cells before exporting')
            for output in cell.get('outputs',[]):
                if output.get('output_type')=='error':raise ValueError('Notebook contains an execution error')
                data=output.get('data',{})
                if 'image/png' in data:
                    fig+=1;parts.append(f'<figure><img alt="Diagnostic figure {fig}" src="data:image/png;base64,{data["image/png"]}"></figure>')
                elif 'text/html' in data:parts.append('<div class="table-wrap">'+data['text/html']+'</div>')
    if fig!=5:raise ValueError('Expected all five diagnostic figures')
    page='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'"><title>UN lexical and semantic comparison</title><style>'+CSS+'</style></head><body><main>'+''.join(parts)+'<footer>Provisional research output. No human approval, held-out test, coalition finding, or publication clearance is implied.</footer></main></body></html>'
    destination=path.with_suffix('.html');destination.write_text(page,encoding='utf8');return destination

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('notebook',type=Path)
    print(export(parser.parse_args().notebook))
