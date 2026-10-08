#!/usr/bin/env python3
"""P2 original-PV expansion: aggregate only, no original PDF/text upload."""
import collections,hashlib,json,os,pathlib,re,urllib.request,urllib.error,time
import fitz

target=pathlib.Path(__file__).with_name("p2_expansion_38_meetings.txt")
symbols=[s.strip() for s in target.read_text().splitlines() if s.strip() and not s.startswith("#")]
assert len(symbols)==len(set(symbols))==38
assert all(re.fullmatch(r"A/7[1-8]/PV\.\d+",x) for x in symbols)
stats=collections.defaultdict(lambda:{"requested":0,"full_pdf_byte_verified":0,"text_extraction_complete":0,"failed":0})
failures=collections.Counter()
for symbol in symbols:
 year=int(symbol.split("/")[1])+1945
 stat=stats[year];stat["requested"]+=1
 url="https://documents.un.org/api/symbol/access?l=en&s="+urllib.parse.quote(symbol,safe="")+"&t=pdf"
 try:
  request=urllib.request.Request(url,headers={"User-Agent":"UNGA81-P2-source-fidelity/0.1","Accept":"application/pdf"})
  with urllib.request.urlopen(request,timeout=50) as response:
   data=response.read(25_000_001)
  if len(data)>25_000_000 or not data.startswith(b"%PDF-") or b"%%EOF" not in data[-4096:]:
   raise ValueError("not_complete_pdf")
  original_sha=hashlib.sha256(data).hexdigest()
  assert len(original_sha)==64
  stat["full_pdf_byte_verified"]+=1
  try:
   with fitz.open(stream=data,filetype="pdf") as pdf:
    pages=len(pdf)
    n=sum(len(p.get_text()) for p in pdf)
   if pages>0 and n>=300:stat["text_extraction_complete"]+=1
   else:failures["text_missing_or_scanned"]+=1
  except Exception:failures["pdf_text_extraction_failed"]+=1
 except urllib.error.HTTPError as ex:
  stat["failed"]+=1;failures["http_"+str(ex.code)]+=1
 except (ValueError,TimeoutError,urllib.error.URLError,OSError) as ex:
  stat["failed"]+=1;failures[type(ex).__name__]+=1
 time.sleep(.12)
result={"schema":"un.w4.p2.original-pv-expansion.aggregate.v1",
"yearly":[{"year":year,**stats[year]} for year in range(2016,2024)],
"totals":{k:sum(v[k] for v in stats.values()) for k in ("requested","full_pdf_byte_verified","text_extraction_complete","failed")},
"failure_kinds":dict(failures),
"independently_compared_to_Harvard_speech_text":False,
"new_validated_country_year_observations":0,
"source_bytes_archived_outside_runner":False,
"raw_PDF_or_extracted_text_exported":False,
"historical_years_only":True,"heldout_2026_meetings_accessed":False,"publication_eligible":False}
print(json.dumps(result,sort_keys=True))
output=pathlib.Path(os.getenv("RUNNER_TEMP","/tmp"))/"w4_p2_expansion_aggregate.json"
output.write_text(json.dumps(result,indent=2)+"\n")
