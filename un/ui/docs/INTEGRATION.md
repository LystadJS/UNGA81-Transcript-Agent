# D1-I4 integration — adapter v1

The interface is bundled with the 2.5.0 D1-I4 checkpoint. `interfaces/shiny_v1.R` is pinned by `config/shiny_adapter.sha256` and is verified at application startup.

The adapter is additive: legacy CLI/replay behavior and the legacy Iran/Cuba/Ukraine/AI codebook remain unchanged. User-selected topics exist only in the immutable interface request and are evaluated as literal evidence-retrieval candidates. A non-match is unresolved, not absence, and no user topic bypasses the D1 O1 classifier/publication gate.

Installed-pipeline mode processes one reporting date at a time. If the checkpoint has a bundled replay for that date, the replay is used; otherwise the D1 live collector runs with the checkpoint's extractive/no-external-AI configuration. D1 method accounting still receives the full eligible corpus, independently of the user's tracked topics. The interface can additionally display current-corpus clustering suggestions as audit-only research candidates; D1 O2 remains authoritative for publication and is not released by the adapter.

Each interface request receives isolated history/cache/reference namespaces under `runtime/shiny/<request-hash>/` so user sessions do not rewrite legacy history or share mutable model state. Outputs remain unsent drafts.
