# Implementation references and source provenance

Documentation was checked on 24 September 2026. Reading documentation is not the same as successfully executing its remote API or installing the package.

| Primary reference | Used for |
|---|---|
| [UN Transcripts — About](https://transcripts.un.org/en/about) | Programmatic `.json`/`.txt` meeting data; date-search inventory; automatic/unofficial-record warning and evolving preview coverage |
| [UN Transcripts — agent guide](https://transcripts.un.org/llms.txt) | Public programmatic discovery reference linked by the service |
| [OpenAI — Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs) | Responses API `text.format`, JSON Schema, detectable refusals; documentation examples include the configurable starting model |
| [OpenAI — separate billing systems](https://help.openai.com/en/articles/9039756) | ChatGPT and API billing are separate; paid API setup is a local operator task |
| [httr2 — request bodies](https://httr2.r-lib.org/reference/req_body.html) | Native-R HTTP request payload construction; raw JSON body switches to POST |
| [renv — snapshot](https://pkgs.rstudio.com/renv/reference/snapshot.html) | Record actual installed dependency versions in a lockfile |
| [renv — restore](https://pkgs.rstudio.com/renv/reference/restore.html) | Restore recorded versions; disable newer-version substitution on failed restore |
| [renv — lockfiles](https://rstudio.github.io/renv/reference/lockfiles.html) | Dependency names, versions, sources and restoration contract |
| [chromote — introductory documentation](https://rstudio.github.io/chromote/articles/chromote.html) | Optional R-based Chromium DevTools rendering checks |
| [Microsoft — New-ScheduledTaskTrigger](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtasktrigger?view=windowsserver2025-ps) | Daily/clock-time task trigger construction |

## Local provenance

The approved clean full-width email, USUN seal, original full-text DOCX corpus, reviewed summaries and legacy issue codes came from the user's supplied/generated conversation artifacts. The reference example retains those original source hashes and the inherited review provenance. Engineering fixtures are separately labeled and do not represent actual diplomatic statements.

The author's existing `LystadJS/UN-Transcript-Intelligence-Dynamic-Voting-Alignment` repository was consulted read-only for its existing source collection/parsing conventions. This release is a standalone implementation, not a committed merge or a claim that the existing repository's full test suite was run.

The saved source archive, normalized corpus and approval history are evidence of what was provided and previously reviewed. They do not independently authenticate every delivered-speech date or every political assertion in those texts. The Rwanda date/session discrepancy is retained as an inherited source note where present.

The release's output checksums and generation-code hashes give a reproducible local chain. They are not digital signatures or institutional clearance.
