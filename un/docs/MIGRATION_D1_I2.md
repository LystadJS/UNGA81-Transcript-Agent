# Migration to 2.3.0-d1-i2

1. Keep the full 2.2.0-d1-i1 installation, completed reports, dependency lock and historical store unchanged. Its reports require its matching code for exact rebuilding.
2. Extract this release into a separate stable local directory, not an actively syncing folder. Copy only authorized non-secret settings into the new configuration; keep the I2 analytics block and both new policy files.
3. Install/freeze the actual local R dependencies with `scripts/Setup-Windows.ps1`. Matrix is now required for M02/M05/M06. The bundled Linux example is not a promise of bitwise equivalence to a different Windows R/Matrix/font environment.
4. `scripts/Test-Workflow.ps1` generates a fresh local replay first, then executes all three R test suites. This avoids trying to validate a Linux-frozen numerical reference with a different tokenizer/runtime. Inspect the generated Outlook EML.
5. A new live namespace initializes from its first source collection. Replay and engineering namespaces are separate and cannot seed a production reference. Do not copy the example model directory into active `models/`. Preserve the `examples/mref/` objects only as read-only reference evidence.
6. Existing I1 history is schema-compatible, but migrate only by making a complete copy while no writer is active; verify it with `history_tool.R`. Never merge partial directory trees or mutate the old store. A new source acquisition preserves original event dates and its actual new availability time.
7. Complete a nonempty live-source run and inspect the collection, method and gate ledgers. Only then disable the old Windows task and register a new task pointing at the new directory. No task or existing repository was changed here.

## Reference inspection

```powershell
$rt = Get-Content .\config\runtime.local.json -Raw | ConvertFrom-Json
& $rt.rscript --vanilla .\reference_tool.R --command=list --store=models/tfidf_references
& $rt.rscript --vanilla .\reference_tool.R --command=verify --store=models/tfidf_references
```

List verifies pointer/content hashes; verify additionally recomputes the source transformation under the matching environment. Neither command switches, trains, repairs or deletes a reference.

To deliberately change a reference, set a **new** `analytics.feature_reference_namespace` before its next acquisition and document the model-policy decision. The new namespace is not comparable to the old one until all desired historical observations have been re-transformed into the same reference space. Never erase a pointer to suppress a mismatch, turn threshold flags on to force release, or pool the inherited mixed-version topic labels as gold.

## Complete archived replay

```powershell
& $rt.rscript --vanilla .\rebuild.R --input=output/2026-09-23/d1_i2_reference --run-id=my_rebuild
```

This requires the matching recorded R/Matrix/locale/graphics environment and exact code. `--minimal=true` is the tested offline I/O profile on reference R 4.6.1, not a way to bypass reference checks. For routine Windows use, generate a new local reference and then rebuild that local archive. The workflow does not silently downgrade or refit an incompatible frozen archive.
