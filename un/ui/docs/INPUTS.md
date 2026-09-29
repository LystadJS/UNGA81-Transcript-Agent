# Input and matching contract

## TXT

Use UTF-8 text, with metadata above an explicit `--- TRANSCRIPT ---` marker. See `examples/transcript_template.txt`.

```text
Country: Example delegation
Country ID: EXAMPLE
Region: Unmapped
Speaker: Example speaker
Date: 2026-09-24
Language: en
Status: available
Source URL:
--- TRANSCRIPT ---
Transcript body goes here.
```

Only the body supplies issue evidence. Metadata is not searched as speech text. The parser recognizes selected aliases such as `Speech Date`, `Country Name`, `ISO3`, and `Transcript URL`. It does not claim compatibility with every UN download format: the actual latest transcript ZIP was unavailable for intake testing. The supplied source country label is retained; a name-derived identifier is marked `source_name:` and is not represented as an official registry resolution.

Missing/invalid dates are excluded from the selected reporting period. A date in a filename is not silently adopted. Empty and explicitly missing-text records contribute to coverage, never to evidence of a country's silence. Supplied region labels are retained; this prototype does not execute the project's authoritative country-registry reconciliation.

## CSV

Required columns: `statement_id`, `country`, `speech_date`, `text`.

Optional columns: `country_id`, `region`, `speaker`, `language`, `source_url`, `declared_status`. Use ISO dates and `en`/`eng`/`English` for English-language discovery. IDs must be nonempty and unique within a file. Source files may contain multiple records for a country; counts of texts and counts of distinct attributed countries are separate.

## ZIP

ZIP uploads contain TXT files, possibly within subfolders. The app streams text members into generated local filenames rather than extracting their supplied paths. It rejects unsafe paths, duplicate member names, and size violations. It never executes uploaded scripts. Other member types are not transcript inputs. The original ZIP remains archived as source bytes.

The `tests/fixtures/unsafe.zip` file is an inert traversal-path test fixture, not a source dataset. Do not manually extract it; the test confirms that intake rejects it.

## Limits and scope

- Up to 20 tracked topics, 100 characters per label, and 30 include/exclude phrases per list.
- At most 32 calendar dates per request, inclusive.
- 2 MB per TXT; 50 MB per statement CSV; 100 MB total selected upload; 2,500 combined statement rows. ZIP decompressed text is also capped at 100 MB.
- Research feature fitting is limited to 500 eligible texts and 5,000 terms. Above its limit, that branch is withheld; it does not secretly sample the input.
- Discovery is English-only when source metadata explicitly identifies English. Other text remains available to literal matching, subject to the date/source checks. No language detection or translation is claimed.

Duplicate identity/date/body combinations are excluded from analytic counts. Conflicting statement IDs are rejected. These are conservative engineering checks, not a complete near-duplicate or revised-source-resolution system.

## Candidate matching, not semantic classification

Labels and explicit include phrases are treated literally with word boundaries. `AI` does not match inside `aid` or `said`; short uppercase acronyms are case-sensitive. Input such as `.*` is not interpreted as a regular expression or command. Matching is multi-label: one passage can support multiple topic candidates. A passage-level exclusion can suppress a match without changing the retained source text or discovery representation.

Quotes use one-based character offsets into the normalized body. Original source bytes have separate hashes. Internal evidence is validated before rendering. CSV exports prefix formula-looking text with an apostrophe to avoid spreadsheet evaluation; exact originals remain in raw source archives and `statements.rds`. Do not mistake that safety prefix for a source character.

This release does not establish recall, precision, false-positive rates, or calibrated model probabilities. A label can be mentioned while the speaker disagrees with it. Literal mention is not policy support, opposition, importance, or stance.
