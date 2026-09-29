"""Independent local export checks. Requires beautifulsoup4 and PyMuPDF.
This is optional engineering validation, not a runtime Shiny dependency.
"""
from __future__ import annotations
import csv
from email import policy
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import re
import sys
from bs4 import BeautifulSoup
import fitz

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
run = root / 'validation' / 'demo_run'
checks: list[dict] = []
def check(name: str, condition: bool, detail: str = '') -> None:
    checks.append({'check': name, 'passed': bool(condition), 'detail': detail})
    print(('PASS' if condition else 'FAIL') + ' | ' + name)

raw = (run / 'readout.eml').read_bytes()
message = BytesParser(policy=policy.default).parsebytes(raw)
parts = [p for p in message.walk() if not p.is_multipart()]
check('MIME parser reports no defects', all(not p.defects for p in message.walk()))
check('Exactly one HTML and one plaintext body', sorted(p.get_content_type() for p in parts) == ['text/html','text/plain'])
check('Draft flag retained and no recipients or sender set', message['X-Unsent'] == '1' and not any(message[h] for h in ['To','Cc','Bcc','From']))
check('EML uses CRLF throughout', not re.search(rb'(?<!\r)\n', raw))
check('MIME lines within transport limit', max(map(len, raw.split(b'\r\n'))) <= 998)
for kind, filename in [('text/html','readout.html'),('text/plain','readout.txt')]:
    part = next(p for p in parts if p.get_content_type() == kind)
    check(f'{kind} round-trip matches saved file', part.get_payload(decode=True) == (run/filename).read_bytes())
html = (run/'readout.html').read_text(encoding='utf-8')
soup = BeautifulSoup(html, 'html.parser')
check('Exactly five ordered analytical sections', [s['data-output-id'] for s in soup.select('[data-output-id]')] == [f'O{i}' for i in range(1,6)])
check('Email includes no scripts or external image requests', not soup.find_all('script') and not any(x.get('src','').startswith(('http:','https:','file:')) for x in soup.find_all('img')))
check('Synthetic-data notice is present', 'PRACTICE DATA' in soup.get_text())
check('Country extracts account for all 18 training statements', len(soup.select('.country-card')) == 18)
config = json.loads((run/'request.json').read_text())
check('Topic configuration is a list of four objects', isinstance(config['fixed_topics'],list) and len(config['fixed_topics'])==4)
packets = json.loads((run/'report_packets.json').read_text())
check('No analytical packet is released', all(not x['released'] and x['payload'] is None for x in packets))
with (root/'examples/synthetic_statements.csv').open(encoding='utf-8', newline='') as handle:
    statements = {r['statement_id']:r for r in csv.DictReader(handle)}
with (run/'source_evidence.csv').open(encoding='utf-8', newline='') as handle:
    evidence = list(csv.DictReader(handle))
check('All exported quotations have exact source character spans', all(statements[e['statement_id']]['text'][int(e['start_char'])-1:int(e['end_char'])] == e['quote'] for e in evidence), f'{len(evidence)} source-evidence rows')
check('All evidence body hashes match source text', all(hashlib.sha256(statements[e['statement_id']]['text'].encode()).hexdigest() == e['body_sha256'] for e in evidence))
with (run/'manifest.csv').open(encoding='utf-8', newline='') as handle:
    manifest = list(csv.DictReader(handle))
check('All manifest file hashes verify', all(hashlib.sha256((run/m['path']).read_bytes()).hexdigest()==m['sha256'] for m in manifest), f'{len(manifest)} manifest entries')
provenance = json.loads((run/'provenance.json').read_text())
check('Receipt explicitly distinguishes prototype from D1', provenance['engine']=='prototype_reference_not_D1' and provenance['analytical_outputs_released']==0)
check('Request fingerprint verifies', hashlib.sha256((run/'request.json').read_bytes()).hexdigest()==provenance['request_sha256'])
pdf = fitz.open(run/'readout.pdf')
check('PDF is readable and contains five pages', len(pdf)==5)
check('PDF contains synthetic notice and all country source extracts', 'PRACTICE DATA' in ''.join(p.get_text() for p in pdf) and all(f'Training delegation {i:02}' in ''.join(p.get_text() for p in pdf) for i in range(1,19)))
overflow=[]
for i,page in enumerate(pdf):
    for block in page.get_text('blocks'):
        x0,y0,x1,y1,*_ = block
        if x0 < -0.5 or y0 < -0.5 or x1 > page.rect.width+0.5 or y1 > page.rect.height+0.5:
            overflow.append({'page': i+1, 'box': [x0,y0,x1,y1]})
check('No PDF text blocks extend outside page bounds', not overflow, json.dumps(overflow))
(root/'validation'/'export_validation.json').write_text(json.dumps({'checks':checks,'passed':sum(x['passed'] for x in checks),'total':len(checks)},indent=2),encoding='utf-8')
print(f"RESULT: {sum(c['passed'] for c in checks)}/{len(checks)} checks passed")
raise SystemExit(0 if all(c['passed'] for c in checks) else 1)
