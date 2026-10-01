"""Archive verified organizer/delegation publications before video-derived drafts.

These URLs were matched to the 2026 events by title, date and publisher.
Agendas and outcome documents remain distinct from speeches in the report.
"""
import argparse,datetime as dt,hashlib,json,urllib.request,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from bs4 import BeautifulSoup
from pypdf import PdfReader

SOURCES=[
 ('pga','c29148720b48','https://www.un.org/pga/81/documents/speeches/social-business-youth-technology-21-september-2026/','html'),
 ('unwomen-original','43630b2b4ca7','https://www.unwomen.org/en/news-stories/speech/2026/09/speech-multilateralism-will-only-remain-fit-for-purpose-if-it-shares-power-centres-womens-leadership-and-delivers-for-the-people-it-serves','html'),
 ('unops','a173d086de17','https://www.unops.org/news-and-stories/speeches/grids-global-accelerator-launch-event','html'),
 ('russia','634fef94fa16','https://russiaun.ru/en/news/24092026','html'),
 ('icrc','4ee531a98087','https://www.icrc.org/en/statement/joint-statement-global-initiative-galvanize-political-commitment-international-humanitarian-law','html'),
 ('gln','6613621f4cda','https://globalleadersnetwork.org/wp-content/uploads/2026/09/UNGA81_GLN-Communique.pdf','pdf'),
 ('programme','','https://www.un.org/en/sdgmediazone/UNGA81/programme','html'),
 ('pmnch','6613621f4cda','https://pmnch.who.int/news-and-events/events/item/2026/09/22/partner-events/financing-for-women-s-children-s-and-adolescents-health-in-a-time-of-austerity','html'),
 ('ilo','cc5c5a4aef9f','https://admin.live.ilo.org/sites/default/files/transcripts/b4afb9d1-88e5-4d6c-ba6a-0dd5cdd29acf/1790276184/en.docx','docx')]

def collect(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);records=[]
    prior={x['id']:x for x in json.loads((root/'manifest.json').read_text(encoding='utf-8'))} if (root/'manifest.json').exists() else {}
    for name,aid,url,ext in SOURCES:
        target=root/(name+'.'+ext);sidecar=root/(name+'.json')
        old=json.loads(sidecar.read_text(encoding='utf-8')) if sidecar.exists() else prior.get(name,{})
        record=dict(id=name,archive_id=aid,url=url,file=name+'.'+ext)
        try:
            if target.exists():
                raw=target.read_bytes();record['retrieved_at']=old.get('retrieved_at');record['reused_cached_bytes']=True
            else:
                with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as response:raw=response.read(10_000_001)
                if len(raw)>10_000_000:raise ValueError('Oversized publication')
                target.write_bytes(raw);record['retrieved_at']=dt.datetime.now(dt.timezone.utc).isoformat()
            if ext=='pdf':text='\n'.join(p.extract_text() for p in PdfReader(target).pages)
            elif ext=='docx':
                with zipfile.ZipFile(target) as archive:document=ET.fromstring(archive.read('word/document.xml'))
                ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                text='\n'.join(''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in document.findall('.//w:p',ns))
            else:
                soup=BeautifulSoup(raw,'html.parser')
                for tag in soup(['script','style','nav','footer','header']):tag.decompose()
                text=soup.get_text('\n',strip=True)
            (root/(name+'.txt')).write_text(text,encoding='utf-8')
            record.update(status='downloaded',sha256=hashlib.sha256(raw).hexdigest(),chars=len(text))
        except Exception as error:record.update(status='error',error=str(error))
        sidecar.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');records.append(record)
        print(name,record['status'],flush=True)
    # Preserve separately captured browser text when a publisher blocks direct HTTP.
    for name in ('unctad',):
        sidecar=root/(name+'.json')
        if sidecar.exists():
            record=json.loads(sidecar.read_text(encoding='utf-8'))
            if record.get('capture_method'):
                raw=(root/record['file']).read_bytes()
                assert hashlib.sha256(raw).hexdigest()==record['sha256']
                (root/(name+'.txt')).write_bytes(raw);records.append(record)
    (root/'manifest.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output');a=p.parse_args();collect(a.output)
