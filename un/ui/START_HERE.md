# Start here — Diplomat Readout Interface

**Interface release:** 0.2.0-d1-i4. **Backend:** UN Daily Briefing 2.5.0 D1-I4 checkpoint.

The normal user workflow is intentionally small: choose one reporting date, type the issues to track, and click **Generate readout**. The interface runs the installed D1 pipeline over the full eligible corpus and applies the user's tracked topics as a separate evidence-retrieval layer. It never sends the email automatically.

## First-time installation

1. Run `Setup.bat` from this `ui` folder.
2. Run `Verify.bat`.
3. Run `Start.bat`.
4. Your browser opens the local interface.

The installation owner should retain the checkpoint's normal R setup and package controls. `interfaces/shiny_v1.R` is pinned by `../config/shiny_adapter.sha256`; the interface refuses an unpinned adapter.

## Daily use

1. Leave **Use the installed pipeline** selected.
2. Choose a single reporting date.
3. Add or remove tracked issues. Up to 20 are allowed; an empty list is valid.
4. Optional: add explicit related phrases or passage-level exclusions.
5. Click **Generate readout**.
6. Review the email preview and supporting passages.
7. Save the unsent `.eml`, HTML, PDF when available, or the audit ZIP.

Tracked-topic matches are evidence candidates, not released semantic presence classifications. A non-match remains unresolved. Suggested themes are audit-only research output unless D1's O2 publication contract independently releases them.

## Practice mode

**Practice with sample speeches** uses 18 fictional statements and the interface reference backend. It does not exercise D1 and must not be interpreted as UN analysis.

See `docs/INTEGRATION.md` and `../validation/SHINY_CHECK.md` for the exact boundary and executed tests.
