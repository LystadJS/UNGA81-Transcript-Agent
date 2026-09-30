# Uploaded General Debate ZIP comparison

Compared on 30 September 2026 against the current private `review-work/hlw`
archive supporting this repository. The uploaded file was
`UNGA81_2026-09-22_to_28_General_Debate_TXT_COMPLETE.zip`.

**Result: no new or missing transcript passages in the six daily sessions.**
All 460 turns matched in order after whitespace normalization; wording, case and
punctuation were retained. All start times matched within one second. Uploaded
TXT hashes matched both supplied checksum records and the source index; archived
JSON hashes matched their existing manifest. ZIP integrity passed. TXT and JSON
are different representations and are not claimed to be byte-identical files.

| Date | Uploaded turns | Archived turns | Ordered text |
|---|---:|---:|---|
| September 22 | 71 | 71 | Equal |
| September 23 | 78 | 78 | Equal |
| September 24 | 85 | 85 | Equal |
| September 25 | 78 | 78 | Equal |
| September 26 | 71 | 71 | Equal |
| September 28 | 77 | 77 | Equal |

The uploaded September 27 file is a calendar coverage marker, not a transcript;
it was not counted as an additional session. Historical documentation describing
September 28 as missing refers to an older delivery, not this current archive.

## What the six excluded later-date records actually contain

Comparison of the TXT speaker headings with the preserved JSON segment positions
clarifies the six records excluded from the 137 country-attributed candidates:

| Date | Excluded group | Turns | Treatment |
|---|---|---:|---|
| September 24 | GA / PGA | 42 | Chair/president attribution; inspect role and content before any country-level use |
| September 24 | EU / President of the European Council | 1 | Identified non-country delegation; retain separately if EU is in scope |
| September 24 | Speaker 37, Speaker 39, Speaker 44 | 3 | Identity unresolved; retain without assigning a country |
| September 25 | GA / PGA | 39 | Chair/president attribution |
| September 26 | GA / Chair | 36 | Chair attribution |
| September 28 | GA / PGA | 39 | Chair/president attribution |

These groups were never lost from the raw archive. They were excluded only from
the country-attributed evaluation selection. The upload repeats the same source
headings and supplies no new identity evidence for the three unknown turns. No
country labels or duplicate speeches were added. The 137-candidate set remains
unchanged. The EU statement can be a separate evaluation stratum if desired; it
must not be assigned a national ISO3 code merely to pass the country validator.

## Remaining gaps and recommended next steps

The original high-level-week coverage snapshot lists 41 broader-week events and
15 other-week proceedings without transcripts, versus zero General Debate
sessions without transcripts. Separate ongoing caption recovery may change those
counts; this comparison does not overwrite its files or assess those results.
The uploaded ZIP contains no broader-week sessions and cannot fill those gaps.

Next, prepare the later-date review packet from the existing 137 candidates,
checking national-address versus chair/right-of-reply boundaries. Keep the EU
statement separate and resolve unknown speakers only from additional evidence.
An identical second download confirms source consistency, not ASR accuracy or
independent transcription. Human relevance labels and transcript-quality checks
remain necessary before reporting model performance.

## Reproduction and evidence

```powershell
python tools/compare_transcript_zip.py C:\path\to\upload.zip review-work/hlw comparison.json
```

The command reads both sources without extracting or changing them and refuses
to overwrite an existing report. See [machine-readable comparison](../research/validation/i9/upload-comparison.json)
for source URLs, hashes and per-day checks. Raw uploaded transcript text is not
committed to Git.
