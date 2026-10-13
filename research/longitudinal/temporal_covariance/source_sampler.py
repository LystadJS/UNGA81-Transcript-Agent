#!/usr/bin/env python3
"""Reproduce the frozen 2008–2015 source-meeting sampling frame from UN index.

Run on authorized PRIVATE original UN speaker-index CSV only; prints aggregate
sampling counts and refuses a changed source frame or selected meeting identity.
Speaker-linked output is never put into GitHub.
"""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import argparse,csv,hashlib,json,random,re

ORIGINAL_UN_INDEX_SHA="841ae22d6485a7e3c0bce84830f09c43d75421ce9b3a58408d20dfec3cbbaf43"
FRAME_SHA="70373a36d240cbd0403f3d5d6c7f8df2049a09122de34fc4863ec2af8766ad9d"
SELECTION_SHA="e90e4b0182154ce367d6b1db55ea7f0d4047e3badcf5fcc9b1c9c3c01c612f2b"
YEAR_COUNTS=(12,11,12,18,16,18,15,16)
CHOSEN_SPEAKER_ROWS=(126,142,144,80,92,87,110,77)

def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def select(metadata_rows):
    by=defaultdict(lambda:defaultdict(list))
    for row in metadata_rows:
        try:year=int(row["GA Session"])+1945
        except (ValueError,TypeError):continue
        if 2008<=year<=2015:
            symbol=(row.get("Meeting Symbol") or "").strip()
            if re.fullmatch(fr"A/{year-1945}/PV\.\d+",symbol):
                by[year][symbol].append(row)
    frame,selected=[],[]
    annual=[]
    for year in range(2008,2016):
        meetings=sorted(by[year],key=lambda s:int(s.split(".")[-1]))
        if len(meetings)!=YEAR_COUNTS[year-2008]:
            raise ValueError("Original UN meeting/year universe changed")
        total=0
        for quartile in range(4):
            group=meetings[quartile*len(meetings)//4:(quartile+1)*len(meetings)//4]
            if len(group)<2:raise ValueError("No two source meetings in stratum")
            rng=random.Random(20261013+year*71+quartile*101)
            drawn=set(rng.sample(group,2))
            for symbol in group:
                frame.append({"year":year,"session":year-1945,"meeting_symbol":symbol,
                  "stratum":quartile+1,"stratum_N_meetings":len(group),
                  "meeting_inclusion_probability":2/len(group),
                  "selected":symbol in drawn,"index_speaker_rows":len(by[year][symbol])})
            for symbol in sorted(drawn,key=lambda s:int(s.split(".")[-1])):
                selected.append({"year":year,"session":year-1945,
                  "stratum":quartile+1,"source_symbol":symbol,"stratum_size":len(group),
                  "inclusion_prob":2/len(group),
                  "index_speaker_rows":len(by[year][symbol])})
                total+=len(by[year][symbol])
        if total!=CHOSEN_SPEAKER_ROWS[year-2008]:
            raise ValueError("Precommitted speaker-index row count changed")
        annual.append({"year":year,"source_meetings":len(meetings),"selected_meetings":8,
                       "speaker_rows_in_selected":total})
    if len(frame)!=118 or len(selected)!=64 or digest(frame)!=FRAME_SHA or digest(selected)!=SELECTION_SHA:
        raise ValueError("Frozen historical sampling design fingerprint mismatch")
    return frame,selected,annual

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--un-index",type=Path)
    p.add_argument("--selftest",action="store_true")
    args=p.parse_args()
    if args.selftest:
        fake=[]
        for year,number in zip(range(2008,2016),YEAR_COUNTS):
            for num in range(1,number+1):
                fake.append({"GA Session":str(year-1945),
                             "Meeting Symbol":f"A/{year-1945}/PV.{num}"})
        try:
            select(fake)
            raise AssertionError("Changed synthetic source distribution falsely accepted")
        except ValueError:
            print("PASS synthetic changed-source fingerprint rejection")
        return
    if not args.un_index:raise ValueError("Approved --un-index CSV required")
    if hashlib.sha256(args.un_index.read_bytes()).hexdigest()!=ORIGINAL_UN_INDEX_SHA:
        raise ValueError("Original UN index bytes differ")
    with args.un_index.open(encoding="utf-8-sig",newline="") as f:
        frame,selected,annual=select(list(csv.DictReader(f)))
    print(json.dumps({"source_index_sha256":ORIGINAL_UN_INDEX_SHA,"frame_sha256":FRAME_SHA,
       "selection_sha256":SELECTION_SHA,"PV_frame_count":len(frame),
       "selected_PV_count":len(selected),"year_aggregate":annual,
       "membership_population_validated":False,"heldout_2026_meetings_accessed":0}))

if __name__=="__main__":main()
