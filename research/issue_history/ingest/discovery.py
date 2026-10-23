"""Bounded catalog metadata discovery; no fetching and no guessed download URLs."""
from html.parser import HTMLParser
from urllib.parse import urljoin,urlparse

CATALOG={
    "ga_adopted_votes":{"url":"https://digitallibrary.un.org/record/4060887?ln=en","body":"GA","verified_catalog_link":True,"download_schema_verified":False},
    "sc_adopted_votes":{"url":"https://digitallibrary.un.org/record/4055387?ln=en","body":"SC","verified_catalog_link":True,"download_schema_verified":False},
}
class Links(HTMLParser):
    def __init__(self): super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            href=dict(attrs).get("href")
            if href:self.links.append(href)

def discover_downloads(family,html,max_bytes=262144):
    if family not in CATALOG: raise ValueError("Unknown official source family")
    if not isinstance(html,str) or len(html.encode())>max_bytes: raise ValueError("Catalog metadata exceeds bounded size")
    catalog=CATALOG[family];parser=Links();parser.feed(html)
    found=[]
    for href in parser.links:
        url=urljoin(catalog["url"],href);parsed=urlparse(url)
        if parsed.scheme!="https" or parsed.hostname!="digitallibrary.un.org":continue
        if not parsed.path.lower().endswith((".csv",".json",".xml")):continue
        if url not in found:found.append(url)
        if len(found)>20:raise ValueError("Catalog download count exceeds discovery bound")
    return {"family":family,"catalog_url":catalog["url"],"candidate_downloads":found,"status":"candidates_require_schema_and_permission_review" if found else "no_verified_download","adapter_status":"remote_format_unverified","fetched":False}


def transcript_inventory(raw,day,page=1,max_bytes=1048576):
    """Parse one verified official inventory format without opening transcript URLs."""
    import hashlib,json,re
    from datetime import date
    if not isinstance(day,str) or date.fromisoformat(day).isoformat()!=day:raise ValueError("Expected exact inventory date")
    if type(page) is not int or not 1<=page<=50:raise ValueError("Bounded inventory page required")
    if not isinstance(raw,bytes) or len(raw)>max_bytes:raise ValueError("Inventory metadata exceeds byte bound")
    value=json.loads(raw)
    if not isinstance(value,dict):raise ValueError("Inventory response must be an object")
    if type(value.get("page")) is not int or value.get("page")!=page or type(value.get("total")) is not int or value["total"]<0 or type(value.get("hasMore")) is not bool or not isinstance(value.get("meetings"),list):raise ValueError("Unexpected official inventory format")
    if len(value["meetings"])>500 or len(value["meetings"])>value["total"]:raise ValueError("Inventory count exceeds bound")
    rows=[];seen=set()
    for item in value["meetings"]:
        if not isinstance(item,dict):raise ValueError("Inventory meeting must be an object")
        slug=item.get("slug")
        if not isinstance(slug,str) or not re.fullmatch(r"[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+){1,5}",slug) or slug in seen:raise ValueError("Duplicate or invalid inventory slug")
        seen.add(slug)
        if not isinstance(item.get("date"),str) or item["date"][:10]!=day or type(item.get("hasTranscript")) is not bool:raise ValueError("Inventory date or transcript availability mismatch")
        body="SC" if slug.startswith("sc/") else "GA_C"+slug.split("/")[1][1:] if re.match(r"ga/c[1-6]/",slug) else "GA" if slug.startswith("ga/") else "other"
        links={}
        for key,suffix in (("pageUrl",""),("jsonUrl",".json"),("textUrl",".txt")):
            href=item.get(key)
            if href is None:links[key]=None;continue
            url=urljoin("https://transcripts.un.org",href)
            if url!="https://transcripts.un.org/en/"+slug+suffix:raise ValueError("Inventory link identity mismatch")
            links[key]=url
        rows.append({"meeting_id":slug,"date":day,"body":body,"recorded_body":item.get("body"),"category":item.get("category"),"transcript_advertised":item["hasTranscript"],**links})
    if not value["hasMore"] and page==1 and len(rows)!=value["total"]:raise ValueError("Single-page inventory count mismatch")
    return {"family":"un_transcript_inventory","date":day,"page":page,"total":value["total"],"has_more":value["hasMore"],"metadata_sha256":hashlib.sha256(raw).hexdigest(),"meetings":rows,"availability":"entries_returned_not_transcript_verified" if rows else "no_entries_returned_not_verified_absence","transcript_text_fetched":False}
