#!/usr/bin/env python3
"""Private, fail-closed P2 original-UN-PV -> W1 source-frame adapter.

Does NOT modify the legacy v1 analytical schema or approve P2 as a source enum.
Runs only on authorized input paths; writes row-linked results outside checkout.
"""
import argparse,csv,hashlib,io,json,os,pathlib,tarfile,zipfile

ROOT=pathlib.Path(__file__).resolve().parents[3]
def digest(blob):return hashlib.sha256(blob).hexdigest()
def read_csv(z,name):
    return list(csv.DictReader(io.StringIO(z.read(name).decode("utf-8-sig"))))
def source_rows(panel,source_grid,pv_manifest,pv_zip,harvard_tar):
    evidence={(r["iso3"],int(r["year"])):r for r in source_grid}
    assert len(evidence)==len(source_grid),"Duplicate country-year P2 evidence"
    originals={r["symbol"]:r for r in pv_manifest}
    assert originals,"No original PV manifest"
    with zipfile.ZipFile(pv_zip) as z:
        for symbol,entry in originals.items():
            member="original_UN_GA_PV/"+symbol.replace("/","_")+".pdf"
            payload=z.read(member)
            assert payload.startswith(b"%PDF-") and len(payload)==int(entry["official_pdf_bytes"])
            assert digest(payload)==entry["official_pdf_sha256"],"Original UN source bytes changed"
    verified={r["id"]:r for r in panel["observations"] if r["source_status"]=="available"}
    if not verified:raise ValueError("No original source-supported observations")
    filenames={r["iso3"]+"_"+str(int(r["year"])-1945)+"_"+str(r["year"])+".txt"
               for r in verified.values()}
    contents={}
    with tarfile.open(harvard_tar,mode="r|gz") as tar:
        for member in tar:
            name=pathlib.PurePosixPath(member.name).name
            if member.isfile() and not name.startswith("._") and name in filenames:
                if name in contents:raise ValueError("Duplicate Harvard speech member")
                contents[name]=tar.extractfile(member).read()
    assert len(contents)==len(filenames),"Missing original Harvard speech bytes"
    observations=[]
    for row in panel["observations"]:
        claim=evidence.get((row["iso3"],int(row["year"])))
        assert claim,"Missing explicit P2 source-inventory record"
        if row["source_status"]!="available":
            assert row.get("date") is None and row.get("text_sha256") is None
            assert row.get("source_sha256") is None and row.get("vector") is None
            continue
        assert claim["status"]=="strong_original_PV_full_speech_correspondence"
        assert float(claim["original_PV_Harvard_7gram_coverage"])>=.90
        assert row["observed_p2_strong_match"] is True
        assert row["actor_kind"]=="recorded_affiliation" and not row.get("person_identity_authenticated")
        assert row["date_basis"] in ("independent_UN_index","official_UN_PV_header")
        assert row["source_hash_basis"]=="raw_response_bytes"
        assert claim["original_official_meeting_symbol"]==row["meeting_id"]
        assert claim["official_PV_original_byte_sha256"]==row["source_sha256"]
        assert claim["Harvard_v14_corresponding_text_sha256"]==row["text_sha256"]
        assert originals[row["meeting_id"]]["official_pdf_sha256"]==row["source_sha256"]
        if row["date_basis"]=="independent_UN_index":
            assert claim["official_date_from_UN_index"]==row["date"]
        else:
            assert row["iso3"]=="BHS" and row["year"] in (2016,2017,2023)
            assert not claim["official_date_from_UN_index"]
        filename=row["iso3"]+"_"+str(int(row["year"])-1945)+"_"+str(row["year"])+".txt"
        content=contents[filename]
        assert digest(content)==row["text_sha256"],"Harvard speech bytes differ from P2 original hash"
        text=content.decode("utf-8")
        assert text.encode("utf-8")==content
        observations.append({"id":row["id"],"split":"development","source_status":"available",
          "exclusion_reasons":[],"text":text,"text_sha256":row["text_sha256"],
          "meeting_id":row["meeting_id"],"source_family_id":row["source_family_id"],
          "date":row["date"],"country":row["actor_id"],"affiliation":row["actor_id"],
          "genre":row["genre"],"role":"recorded_country_affiliation",
          "unit":"source_segment","review_status":"unreviewed","parent_id":None,
          "parent_text_sha256":None,"start":None,"end":None,"source_url":row.get("source_url")})
    return observations,len(panel["observations"])-len(observations),len(originals)

def main():
    p=argparse.ArgumentParser()
    for name in ("panel","p2-zip","pv-zip","harvard-tar","upstream","out-private"):
        p.add_argument("--"+name,required=True,type=pathlib.Path)
    a=p.parse_args();out=a.out_private.resolve()
    if out==ROOT or ROOT in out.parents:raise ValueError("Refuse source-bearing output under public GitHub checkout")
    if out.exists():raise ValueError("Refuse to overwrite private output")
    panel=json.loads(a.panel.read_text())
    upstream=json.loads(a.upstream.read_text())
    assert panel["schema"]=="un.longitudinal-panel.v1" and panel["split"]=="development"
    assert upstream["source_schema"]=="un.p2.original-pv-reconciled.v1"
    assert panel["source_population_p2_selection_sha256"]==upstream["selection_sha256"]
    with zipfile.ZipFile(a.p2_zip) as z:
        grid=read_csv(z,"private_reconciliation/private_W4_candidate_99_by_8_observation_grid.csv")
        manifest=read_csv(z,"private_reconciliation/private_full_original_pdf_byte_manifest.csv")
    rows,missing,pvs=source_rows(panel,grid,manifest,a.pv_zip,a.harvard_tar)
    result={"schema":"un.source-validation.frame.v1","split":"development",
      "source_schema":upstream["source_schema"],"source_engine":upstream["source_engine"],
      "source_hash_basis":upstream["source_hash_basis"],
      "source_sha256":upstream["source_sha256"],
      "unit":"source_segment","inventory_meetings":pvs,
      "observations":rows,
      "provenance_extension_status":"P2_SOURCE_AUTHENTICATED_BUT_NOT_IN_LEGACY_V1_ENUM",
      "release_eligible":False}
    os.umask(0o077)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"status":"authenticated_private_W1_input_only","verified_speech_bytes":len(rows),
      "other_source_cells_preserved_in_external_inventory":missing,"PV_original_byte_hashes_checked":pvs,
      "W1_original_enum_accepted":False,"old_v1_interchange_accepted":False,
      "source_rows_published":False,"publication_eligible":False}))

if __name__=="__main__":main()
