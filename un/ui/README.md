# UN Readout — Diplomat Interface 0.2.0-d1-i4

A local Shiny interface for the UN Transcript Intelligence / Daily Readout workflow. It is bundled with the 2.5.0 D1-I4 checkpoint and designed so a nontechnical user can supply their own tracked issues without editing configuration files or code.

## User-visible concepts

- **Tracked issues:** topics entered by the user. Matching is literal/explicitly expanded and retains supporting source passages. Non-match is unresolved, not absence.
- **Suggested themes:** full-corpus, unsupervised research candidates shown only in the audit-oriented interface view. They do not bypass the D1 O2 publication gate.
- **Daily readout:** D1's existing full-width country readout with exactly five analytical slots and an unsent `.eml` export.

The interface request is immutable and hash-bound. User-selected topics do not alter the discovery corpus, legacy codebook, archived runs, or D1 publication policy. Each D1 interface run uses isolated mutable history/cache/reference namespaces.

See `START_HERE.md` for installation and `docs/INTEGRATION.md` for the technical contract.
