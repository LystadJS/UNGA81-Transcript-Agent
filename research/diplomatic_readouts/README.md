# Evidence-first research readouts

Offline stdlib Python module: `readout.py`. Templates: emerging themes, discourse communities, changing actor profiles, boundary cases, source-backed anomalies.

Required disclosures: population, period, denominator, exclusions, missingness. Sources: id, sha256, accepted, privacy=public. Findings: supporting and contrary references with source_id/start/end. Country attribution requires verified flag; stance requires proposition-specific verified evidence. Statistical, source and review gates must all pass. Failed gates withhold interpretations. No embedded source passages, delivery or publication.

Run: `python3 -m unittest discover -s tests -v`. Render: `render(report, "json"|"markdown"|"html")`; export: `export(report, directory)`.

Coordinator integration: independently authenticate source hashes and offset bounds, map accepted research contracts, supply trusted gates (never consumer-supplied authorization), validate D1 O1–O5 and quick-reader regressions, and integrate only through a separate coordinator-owned PR. This isolated renderer cannot authenticate hashes, offsets, statistical calibration or reviewer identity. No empirical findings claimed.
