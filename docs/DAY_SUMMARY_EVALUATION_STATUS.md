# Day-summary evaluation status

## Current result

**The repaired daily summary has not passed empirical acceptance.** A finalized owner-reviewed three-day development sample now exists in the private project workspace: 12 meetings and 439 retained source segments. It informed the 1.40.0 repair described in [DAY_SUMMARY_DEVELOPMENT_REPAIR_2026-11-05.md](DAY_SUMMARY_DEVELOPMENT_REPAIR_2026-11-05.md). The repaired output still needs a new owner review; development replay counts are not accuracy rates on untouched data.

The checked-in `readiness.json` and empty sample registration below are the earlier protocol-setup receipt. They are preserved as historical evidence, not a claim that the later private owner review never occurred. No private labels or source-bearing review files are reproduced here, and the frozen thresholds are unchanged. The new five-level stance model has its own [model card](MODEL_CARD.md) and does not inherit daily-summary acceptance.

## Earlier protocol-setup result

At protocol setup, the requested semantic evaluation was **not evaluated because that workspace contained no owner-reviewed daily-summary sample spanning multiple UN bodies and meeting types**. No error rate was reported as zero. The historical machine-readable receipt is [`research/day_summary_evaluation/readiness.json`](../research/day_summary_evaluation/readiness.json).

The available owner-reviewed artifacts cannot supply the four required denominators:

| Existing evidence | Actual review scope | Why it cannot score the day summary |
|---|---|---|
| `research/validation/i9/owner-completion.json` and `owner-revision2.json` | 24 AI-relevance passage decisions from 23 September | Aggregate relevance decisions, not complete daily topics, claims, grouping or attribution |
| `research/validation/i9/later-review-completion.json` | 24 AI-relevance decisions from 24–26 September | General Debate national addresses only; private passage decisions are not present |
| `research/validation/i9/sep28-review-completion.json` | 24 held-out AI-relevance decisions from 28 September | Already evaluated for one issue; not an untouched complete-summary sample |
| `docs/passage-type-reviewed-mask.json` | Structural passage types across six General Debate assets | Can inform procedural filtering, but contains no topic, claim, grouping or attribution decisions |
| `docs/reviewed-units-validation.json` | Boundaries and audio decisions for 12 excerpts from three speeches | General Debate only and no complete-summary semantic labels |

The samples visible at that earlier protocol-setup stage were General Debate or national-address material. They did not cover a Security Council meeting, Main Committee, Human Rights Council, treaty body, resumed meeting part or multi-body day with complete summary annotations. `research/validation/i9/owner-daily-validation.json` is structural product QA and explicitly says that it does not establish semantic accuracy. This limitation must not be misread as describing the later three-day development review.

## Locked acceptance criteria

The prospective protocol and thresholds were frozen before any untouched daily-summary test sample was registered or opened:

- unsupported claim rate: at most 5%;
- missed substantive-topic rate: at most 15%;
- incorrect grouping rate: at most 5%;
- attribution error rate: at most 5%;
- critical evidence, identity, collective-attribution, repetition and silent-output errors: zero; and
- one-action browser completion: 100%.

The lock also requires minimum coverage across days, UN bodies, meeting types, meetings, assessable claims, assessable topics, assessable grouping decisions and assessable country-attribution decisions. Its frozen legacy commitments remain empty. A separate source-bound registration manifest binds any future sample to meeting IDs, source IDs and source hashes without altering the threshold lock. The current registration is empty, so readiness remains `not_evaluated_missing_owner_samples`. See [`DAY_SUMMARY_EVALUATION_PROTOCOL.md`](DAY_SUMMARY_EVALUATION_PROTOCOL.md), the machine-readable acceptance lock and `research/day_summary_evaluation/sample-registration.json`.

## Executed validation

The offline evaluator passed 19 synthetic contract tests covering all four metrics, row-level per-day/body/type breakdowns, assessable-only coverage, separate claim/topic body-concentration gates, the required browser receipt during the evaluation window, registration-before-review, prospective post-lock development review, disjoint development/test dates and source IDs/hashes, tamper detection, owner confirmation, unreviewable decisions and validated critical-error failure.

The one-action browser acceptance passed against synthetic General Assembly plenary and Security Council responses. One activation of **Generate report** produced one complete daily summary, three automatic charts, three readable table alternatives and three source drill-downs. The saved analysis JSON retained the complete summary and all three visualization objects, and the script-free standalone HTML retained the same rendered summary, chart tables and source drill-downs. Advanced methods remained collapsed, desktop and 390-pixel mobile layouts did not overflow, and no JavaScript error occurred.

These engineering results confirm the workflow and evaluator. They do not substitute synthetic labels for owner review and do not estimate semantic accuracy.

## Untouched-test state

No untouched daily-summary test was evaluated. The 37 reserved October 5–6 transcripts remain unopened. Before acceptance, reconcile the private source-bound development manifests with the evaluation protocol, complete owner review of the repaired output, and register a disjoint non-reserved untouched sample. Any threshold change requires a new protocol version and a new untouched sample.
