# Build the reviewed datasets

Start with **one or two issues, explicitly named propositions, and a small
annotation pilot**. Do not begin by training all models. The source files,
review decisions and held-out evaluation are the foundation for every method.

The included tools create review workspaces and check their structure. They
do not establish that a review is truthful, identify a reviewer, certify model
accuracy, or authorize publication. The I6 research kernels currently accept
synthetic engineering fixtures only. Connecting a reviewed bundle to the daily
pipeline remains a separate implementation and acceptance step.

## 1. Create a private working folder

Use Python 3.11+ and a short folder outside your public Git checkout, such as
`C:\un-data\pilot`. From the repository directory run:

```powershell
python tools/review_data.py init C:\un-data\pilot
```

For a practice start using the existing 39-speech replay:

```powershell
python tools/review_data.py init C:\un-data\replay-review --replay un\examples\2026-09-23\speeches.json
```

This copies text and creates paragraph offsets. It deliberately leaves review
labels, original availability times and missing source URLs blank. The existing
automatic/inherited classifications do **not** become gold labels. The bundled
replay alone cannot support a historical evaluation.

You can edit the CSVs in a spreadsheet editor, but save UTF-8 CSV, preserve all
headers, and never change the text files after making passage offsets. Keep
reviewer details and private annotations out of public Git. Empty templates
also live in `data/templates/`.

## 2. Build the source register

Use authoritative source records. The UN provides a
[general-debate speech dataset](https://digitallibrary.un.org/record/4067189/)
and [guidance for finding debate statements](https://www.un.org/en/delegate/general-debate-statements-your-fingertips).
Metadata availability does not prove that every record contains a usable full
text. Inspect and retain the actual document behind each text.

For each speech, fill `sources.csv`:

- Stable source ID and ISO3 country identifier.
- Speech date, language and genre, such as `general_debate`.
- Original source URL and the timestamp when the source was actually available.
  Record an uncertainty note separately if the historical availability cannot
  be established; do not substitute today's download time as a historical fact.
- Relative path to the unchanged UTF-8 text and its SHA-256 hash.
- A duplicate-group ID for near-duplicates, translations or revised versions
  that must stay in the same evaluation partition.

Keep original PDF/DOCX bytes and extraction notes alongside the working corpus.
Record OCR/translation status and inspect paragraph ordering. The current
validator checks canonical text hashes; it does not independently certify OCR,
translation quality, country identity or the completeness of the source census.

For historical work, a useful **pilot design**, not a sufficiency guarantee, is
the same countries' general-debate speeches over at least three sessions.
Annual speeches are annual observations. They cannot be turned into daily
history by inserting zero-valued rows.

## 3. Define the tasks before labelling

Write a short codebook, freeze a version, and provide positive, negative and
ambiguous examples. Start with roughly 100–200 diverse passages as an annotation
pilot; the final dataset size must follow class coverage, uncertainty estimates
and learning curves rather than this starting number.

Issue relevance is a separate task from stance. In `annotations.csv`, issue
labels are `relevant`, `not_relevant` or `insufficient`. A negative label applies
to the reviewed passage; it does not establish that a whole speech or country
never addressed the issue. Include independently sampled passages, not only
keyword hits, so missed wording can be evaluated.

In `propositions.csv`, define a precise claim, target, scope and version. For
example, a **fictional coding exercise** could use: “The speaker supports a
legally binding international agreement governing military AI.” Do not use
“AI” as a stance proposition: it is a topic, not a position.

Stance labels are:

| Label | Coding rule |
|---|---|
| support | Explicit support for the named proposition and target |
| oppose | Explicit opposition to that proposition |
| conditional | Support or opposition depends on a stated condition; record it |
| descriptive | Discusses the proposition without adopting a position |
| insufficient | Missing context, ambiguity, quotation/attribution uncertainty or otherwise unresolvable |

Do not turn insufficient evidence into “neutral.” Code quoted statements
according to who adopts the position, not merely who is mentioned. Record the
exact passage and any required surrounding context. Preserve proposition
versions: a changed claim is a changed prediction task.

## 4. Review independently, then adjudicate

Assign two reviewers to each passage/task/proposition. They work independently
and do not see each other's decisions or model predictions. Use pseudonymous
reviewer IDs in the analytical files; keep the identity mapping separately.

Each reviewer adds an annotation ID, passage ID, task, proposition, label,
reviewer ID, timestamp and short rationale. `passages.csv` stores exact quotes
and **zero-based Unicode-codepoint offsets with an exclusive end position**.
Offsets refer to the complete canonical text, not HTML or a reformatted copy.

A third reviewer resolves each item in `adjudications.csv`. Preserve the two
original labels, the final label, adjudicator, timestamp and reason, including
agreements. Disputed cases can remain insufficient; do not force a substantive
label to make a balanced dataset.

Measure raw agreement and a suitable chance-corrected measure by task and class;
inspect confusion patterns and uncertainty, not just a single overall score.
Revise unclear rules and repeat the pilot before locking a gold version.
[Artstein and Poesio](https://aclanthology.org/J08-4004/) discuss why agreement
measures and their assumptions need to match the annotation task. Agreement is
evidence about reliability, not proof of truth.

## 5. Freeze the evaluation split

Fill `splits.csv` with `train`, `calibration` or `test` for each reviewed source.
All passages from a speech, exact duplicate texts and duplicate groups must stay
together. Use earlier observations for training, a later period for calibration,
and a still later untouched test period.

The default `time_and_country` scheme also keeps countries disjoint across all
three partitions. It is a demanding test of transfer to unseen countries. If
the actual question is future speeches by already observed countries, use an
explicit `time_only` scheme and describe that narrower claim. The current I6
classifier kernels require the stricter disjoint-country scheme.

Select hyperparameters within training data, or preregister a fixed setting.
Use calibration data to set score calibration and abstention thresholds. Do
not inspect the final test set while choosing labels, thresholds, models or
features. Fit vocabulary, IDF, scaling and feature selection on training data
only. Near-duplicate grouping must precede the split.

Keep retrospective research evaluation separate from an “as known on that day”
backtest: the latter must also respect source, label and model availability
timestamps. Labels created today do not prove that a model was available years ago.

## 6. Validate the review files

After actual human review, set `dataset_kind` to `real`, enter an ISO-8601 UTC
cutoff and set `human_review_complete` to true in `bundle.json`. These are human
attestations, not a way to bypass missing review rows.

```powershell
python tools/review_data.py validate C:\un-data\pilot --capability labels --out C:\un-data\pilot\labels-check.json
python tools/review_data.py validate C:\un-data\pilot --capability stance --out C:\un-data\pilot\stance-check.json
```

Fix every reported error. Independently inspect a sample of accepted rows and
retain a versioned manifest/hash list before using the bundle. A passing check
does not establish enough examples of every class or acceptable model accuracy.
Do not overwrite earlier reviewed dataset versions.

## 7. Build and validate stance capability

Start with transparent lexical/regularized baselines before neural models.
Compare the same propositions, feature basis and splits. Report per-class
precision/recall, macro metrics, confusion matrices, calibration, and accuracy
versus retained coverage when the model abstains. Inspect results by country,
date, language and genre. Preserve exact supporting evidence with each output.

The I6 M17 kernel exercises a regularized four-class head, temperature calibration
and abstention on synthetic data. It is **not** a released stance model. M15
uses a frozen representation plus a binary head; M03 currently aggregates cached
vectors and does not run an encoder. Before deployment, supply the approved
encoder/checkpoint, tokenizer, licensing/processing authorization, content hash,
preprocessing contract and benchmark results. M16 fine-tuning needs a separate
validated training/checkpoint implementation.

Promote only after preregistered held-out criteria and human error review pass.
The daily pipeline currently has no approved import-to-publication route for
these reviewed labels. Integration must independently verify the dataset
manifest, model artifact, environment and predictions before any release gate
can change. Do not edit registry gate flags to manufacture readiness.

## 8. Build historical-change capability

Fill `history.csv` with source ID, issue/proposition, a frozen representation ID,
comparability group and observation index. Each group must refer to the same
country, genre, language and task. Use the same vocabulary/IDF or approved encoder
across the comparison. Document missing statements, translation changes and
transcript revisions; do not treat them as a country's movement.

```powershell
python tools/review_data.py validate C:\un-data\history --capability history --out C:\un-data\history\check.json
```

Begin with M22 high-dimensional distances between new and prior comparable
observations. Check examples manually against the original passages. A large
distance can result from text quality or changing subject matter. It is not,
by itself, a stance shift.

Next assess historical-only anomaly scoring (M23), carefully specified
change-point models (M24), and cluster correspondence (M27). Frozen PCA does not
require Procrustes; use M25 only for separately estimated compatible maps with
independent, full-rank anchors. Keep arrivals/departures and splits/merges visible.

Backtest with rolling cutoffs, naive baselines and country-level uncertainty
assessment. Validate false alerts using OCR, text-length, missingness and topic
composition perturbations. Longer latent-state/sequence methods (M28–M30, M38)
need adequate repeated sequences, stable measurement, convergence and a
demonstrated gain over simpler baselines. Three annual speeches are a pilot for
pairwise comparison, not adequate evidence for a temporal transformer.

## 9. Build diffusion and relational-event datasets

Choose the outcome first. “First observed rhetorical endorsement” and “policy
adoption” are different events. A policy-adoption claim needs an actual policy
record. In `events.csv`, record the actor, target/proposition or action definition,
event type, source, exact evidence passage, event time and availability time.
Use `task=event` annotations with `confirmed`, `not_confirmed` or `insufficient`,
two independent reviewers and an adjudicated confirmation for every included event.

For observed interactions, record the actual sender, receiver and action. A
co-mention does not establish an interaction. Preserve timestamp precision and
ties; do not invent ordering to satisfy a model.

Build `risk.csv` from an explicit observation process: which countries could
have the event, when they enter observation, the interval start/stop, observed
event ID/outcome, and censoring explanation. Stop first-event risk after the
event. A missing speech is not an observed non-event. Identify already-adopted
countries at entry and justify left truncation. Do not code unknown prior
adoption as “never adopted.”

In `edges.csv`, keep observed-interaction, vote, text-similarity and stance layers
separate. Retain source evidence and availability times. The current validator
supports a **static preexisting network**, available before the recipient's first
risk interval; time-varying networks still need an interval-specific extension.

Compute lagged exposure using only prior events and prior available edges.
Record missing-neighbour coverage rather than silently counting unknown states
as non-adoption. Retain common-shock covariates and justify the risk set.

```powershell
python tools/review_data.py validate C:\un-data\events --capability events --out C:\un-data\events\events-check.json
python tools/review_data.py validate C:\un-data\events --capability diffusion --out C:\un-data\events\diffusion-check.json
```

Start with a no-network baseline, then M39 discrete-time hazard with correctly
specified durations/censoring. The current engineering kernel supports equal
interval lengths only. M40 tests a Gaussian network-lag association. M41 currently
implements ordinal conditional choice over known directed risk sets, not event
waiting times. M42 still needs a Bayesian model implementation, prior checks,
posterior predictive checks, convergence, effective-sample-size and sampler diagnostics.

Use forward event-time evaluation and calibration. Report association unless
a defensible identification design addresses shared shocks, selection,
homophily and reverse causality. Chronological resemblance does not establish
causal diffusion.

## 10. Hand off a reproducible review bundle

Keep these together: immutable sources, canonical texts/hashes, source register,
passage offsets, codebook/propositions, both reviews, adjudications, split policy,
comparison/risk/exposure tables, validator output, limitations, and reviewer
sign-off. Supply a private local path to the bundle when it is ready.

Then implement the reviewed-bundle loader, fit using only the permitted split,
run independent prediction/artifact checks, backtest and inspect errors, and
retain audit-only status until release acceptance is met. See
[I6 implementation status](../research/README.md) for exactly what is written
and tested versus still pending. No new model is published by these tools.
