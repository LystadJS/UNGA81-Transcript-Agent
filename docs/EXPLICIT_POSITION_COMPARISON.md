# Country positions and U.S. baseline — 1.19.0

The report adds a country-by-country table, a selected-country daily trajectory,
source evidence for both sides, and a dedicated comparison CSV. The starting
catalogue covers humanitarian access, civilian protection, a ceasefire, a two-state
solution, TPNW, CTBT and lifting the Cuba embargo. It is a limited deterministic
rule catalogue, not a general opinion model or reviewed government-position set.

The user selects a question, geographic context (or named global treaty), and
comparison country. Recorded national affiliation, direct local action/object
wording and an established context are required. A clear sentence context takes
priority. Otherwise one context in the source segment must match the recorded
meeting title, or an unambiguous title establishes it. Conflicting settings,
unknown explicit places, group/institutional attribution, unresolved wording,
reported advocacy, object negation, conditions and conflicting directions are
withheld from categorical comparison. Rule coverage is intentionally limited;
missed positions and remaining contextual classification errors are possible.
Source excerpts, attribution status and context basis remain inspectable.

A point compares support/opposition for the selected bounded question on the same
calendar date. Internal values 0 and 1 encode same/opposite categories; the UI
never presents them as an ideology scale, overall alignment score or similarity.
Qualified, conflicting or missing evidence has a null value. No statement is
carried forward, no interpolation is used, and lines join adjacent comparable
calendar dates only. The U.S. may change its expression too; a line change does
not independently demonstrate a change in the other country's policy.

Country sources respect the report filters. The U.S. reference uses the same
retained collection, dates, scope, topic, exclusions and passage mask, ignoring
only speaker region. Absent U.S. text cannot be supplied by another collection or
period. Position evidence is deduplicated per country/date/excerpt, separately
from the descriptive report's exact-text deduplication across source records.
Country table rows show each country's latest evidence date and a U.S. comparison
on that exact date; comparable-date counts cover the complete selected period.

Policy, context and country are retained in versioned collection filters. Older
collections default to humanitarian access / Sudan / automatic country selection.
CSV and analysis JSON retain missingness and source identities; script-free HTML
retains the chart and evidence without inactive country-switch buttons. Originals,
recording notes, unresolved exclusions, coverage and meeting groups are retained.

The workspace's three navigation cards separate positions from descriptive charts
and latent language patterns. The latent workspace explains how to reuse the same
saved collection and why clusters and coordinates are not diplomatic positions.
Existing analytical and publication gates remain in place. Synthetic six-date
unit/browser checks cover direction changes, four types of gaps, no bridging,
qualified/collective withholding, matched context, U.S. region exception, identical
cross-country wording, country switching, replay, exports and mobile layout.
The private 14–16 October development collection is used separately for a real
source demonstration. The 37 reserved meetings remain unopened.
