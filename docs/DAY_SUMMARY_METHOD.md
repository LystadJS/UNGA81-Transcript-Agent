# Day-level proceeding summary method

## Purpose and boundary

The day summary is a reader-first orientation to the English transcript segments collected for one calendar day. It combines proceedings across the selected meetings while preserving the meeting attached to every result. It does not establish the official agenda, the completeness of the UN record, a meeting decision, or a government's overall position.

The summary is an offline, deterministic extraction. It does not send transcript text, topics, countries, or report settings to a model provider. The public UN inventory and transcript requests remain the only network collection step. After collection, the browser performs classification, grouping, evidence selection, and rendering on the user's device.

## Processing contract

The browser processes the retained source records in this order:

1. Validate the selected day and use eligible English source segments from that day. Keep the source record identifier, meeting identifier, meeting title, recorded country attribution, source URL, and retained source hash with the text.
2. Split each segment into reviewable sentences. Short fragments, unclear wording, and sentences without an allowed source URL cannot support a displayed substantive claim.
3. Classify sentences as substantive, procedural, ceremonial, or unresolved. Procedural and ceremonial sentences remain part of the saved source record but do not enter the substantive topic summary. A courteous opening does not cause the rest of a substantive segment to be discarded.
4. Match substantive sentences to narrowly defined policy questions. Each question has a stable identifier, a reader-facing label, and an explicit synonym set. One sentence may support more than one question when it contains evidence for each, but each claim keeps its own evidence pointer.
5. Extract only explicit proposal, disagreement, or consequential-development cues. The displayed wording stays close to the supporting sentence. Recorded country labels are participants when they have evidence under that question; a mention of a country alone is insufficient.
6. Deduplicate repeated claim/evidence combinations, then assemble a day view and meeting-specific breakdowns. Repetition can increase a coverage count but does not increase the asserted importance of a topic or the strength of a position.
7. Render every substantive claim with at least one supporting passage and its original UN transcript link. If the source contract cannot supply that evidence, the browser withholds the claim.

The engine emits a versioned schema and method identifier so exported reports can record which deterministic rules produced the summary. The collected corpus already records source identifiers, versions, hashes, collection time, and coverage gaps; those fields remain the reproducibility record for the summary.

## Topic identification and synonym boundaries

The day summary uses a policy-question catalogue that is broader and more specific than the earlier fixed issue-family display. Aliases normalize wording that asks the same policy question. For example, `ceasefire` and `cessation of hostilities` may map to the same cessation question.

An umbrella subject is not enough to merge policy questions. Climate finance and emissions reduction remain separate; humanitarian access and protection of humanitarian workers remain separate; imposing sanctions and lifting sanctions remain separate. The canonical identifier represents the policy object and requested action, not merely a shared noun. Negative wording is handled as evidence about the same object only when the local sentence makes that relationship explicit.

The catalogue can also surface a source-derived candidate beyond its named rules when a substantive action cue has a bounded grammatical object. Such a candidate must retain its literal object label and evidence. It is not silently folded into a nearby umbrella topic, and the interface identifies it as source-derived. Generic noun frequency never creates a substantive claim by itself.

These rules reduce synonym fragmentation without claiming semantic equivalence from word similarity. They can miss paraphrases and can still require human review when one sentence contains nested, conditional, quoted, or reported positions.

## Procedural and ceremonial handling

Procedural cues include actions such as giving the floor, opening or adjourning a meeting, announcing the next speaker, and introducing an agenda item. Ceremonial cues include greetings, thanks, congratulations, condolences, and commemorative language when they do not contain a policy action or consequence.

Filtering occurs at the sentence level. A segment that starts with thanks and continues with a proposal keeps the proposal. A ceremonial phrase inside an otherwise substantive sentence does not erase the substantive evidence. Mixed or unresolved sentences are withheld from automatic proposal or disagreement labels when the local wording does not establish the policy object.

## Claims, participation, and evidence

A topic may contain three kinds of source-bound findings:

- **Principal proposals** are explicit calls, requests, recommendations, commitments, or proposed actions tied to a policy object.
- **Disagreements** are explicit opposition, rejection, objection, disputed terms, or incompatible stated courses of action. Topic co-occurrence does not establish disagreement.
- **Consequential developments** are recorded decisions, adoptions, launches, suspensions, withdrawals, material changes, or concrete commitments expressed in the source wording. The label describes the cue in the transcript; it does not independently verify that the development occurred outside the meeting.

Each displayed claim contains an evidence collection with the exact excerpt, source record identifier, meeting identifier, recorded country when available, and an allowed transcript URL. The interface links the excerpt to its source. Participating countries are the distinct, provisionally mapped country labels attached to the topic's supporting records. They are not a roll call, a list of supporters, or evidence of an official national position.

Meeting distinctions remain visible in two ways: every evidence item retains its meeting, and every topic reports its distribution across the day's meetings. Resumed parts can share a formal meeting identity when the collection contract says they do.

## Coverage and consequence are different views

The coverage view orders or tabulates topics by distinct supporting segments and meetings. It answers where the collected text contains repeated discussion. It does not call the first topic the most important, influential, urgent, or agreed topic.

The consequential-development view is separate. It requires explicit outcome or change cues and presents the attached source wording without deriving an importance score from passage counts. A development mentioned once can appear there, while a frequently mentioned subject may have no consequential development. Neither view establishes real-world impact without source review.

## Browser and backend requirements

The report builder needs no application backend, database, account, hosted classifier, or generative AI API for this summary. A modern browser runs the JavaScript engine after the existing collector retrieves public UN records. Static hosting is sufficient.

The collector's network behavior does not change: selected dates and public transcript requests reach the UN transcript service. Analysis data stays in the active browser tab unless the user downloads a saved collection or report. Refreshing or closing the tab can discard unsaved records. Downloaded files are under the user's control.

The application must not place transcript text, report content, or private review material in telemetry or a remote processing request. Public deployment contains code and synthetic test fixtures only. The 37 reserved October 5–6 transcripts remain unopened and are not validation inputs.

## Validation

Automated tests use synthetic records to verify the following invariants:

- multiple meetings are combined without losing their identifiers;
- recognized synonyms group under one policy question while adjacent policy questions remain separate;
- procedural and ceremonial sentences do not become substantive claims, including when a segment also contains substantive text;
- proposals, disagreements, developments, and participants require local source evidence;
- every substantive displayed claim has an allowed source link and evidence metadata;
- coverage counts are labeled as coverage and do not become an importance score; and
- a source-derived policy object can appear beyond the named catalogue without being merged into an unrelated topic.

These checks establish executable behavior on designed cases. They do not measure recall, precision, diplomatic validity, or production transcript quality. Any source-based publication still requires inspection of the linked passage, speaker attribution, coverage gaps, and automatic-transcript limitations.

## Known limitations

Deterministic patterns will miss paraphrases and may withhold complex syntax. Automatic transcripts can contain recognition errors. A source segment may contain more than one speaker or only part of a speech. Recorded affiliation is provisional attribution, not verified identity. Collective statements must not be assigned to one country merely because the source record carries a national affiliation.

The summary describes available collected English text. Pending, unavailable, failed, non-English, late-published, or otherwise uncollected sources remain visible as coverage gaps and can change the day-level picture. Evidence links make a claim inspectable; they do not make it exhaustive or authoritative.
