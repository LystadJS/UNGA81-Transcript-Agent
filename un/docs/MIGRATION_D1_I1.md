> Historical I1 document retained for provenance. For the current release, read D1_I2_IMPLEMENTATION.md and MIGRATION_D1_I2.md.

# Migration from v2.1 to D1-I1

1. Extract this release separately. Keep original v2.1 source and completed archives byte-for-byte unchanged; those archives require their matching release.
2. Transfer only authorized nonsecret settings: narrative model choice, source scope, limits and real sender/recipient values. Keep the new `analytics` block, fixed-topic policy and region settings. Do not copy old runtime/library/latest pointers or overwrite the new code.
3. Install into the new directory. An existing locally verified `renv.lock` can be copied and restored with `Setup-Windows.ps1 -Restore`; otherwise perform initial setup and freeze actual installed versions. I1 introduces no new third-party dependency.
4. Configure credentials locally with the existing key script. Do not share `.secrets`, environment files or keys. No credential is included here.
5. Run both R test suites and a replay, inspect the EML in your actual Outlook client, then perform a real nonempty live-day acceptance run. The five analytical sections remain unavailable until later validated producers are released; that is not a failed rendering test.
6. Only after acceptance, explicitly disable the old scheduled task and install a new one with your desired time from this directory. Extraction does not change any task. Weekly/monthly heavy training is not implemented.
7. Start a fresh active `history/`. The bundled `examples/href` is a separately labeled replay store. Do not mix fixtures into real historical features or call inherited labels gold. Historical import/adjudicated recoding from older releases requires the next version-aware import stage.

For continued development, no user action is required to authorize local implementation of the next D1 stage. Operational deployment and API credentials remain your local choices. No email-sending feature is added.
