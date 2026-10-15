/** Reviewed plain-language presentation; imported text is never rendered as HTML. */
export const STATES=Object.freeze({idle:'Choose your question',loading:'Preparing your briefing',ready:'Briefing ready',partial:'Some information is unavailable',empty:'No matching records',failed:'Briefing could not be prepared',withheld:'Briefing unavailable'});
export const REASONS=Object.freeze({
  source_unavailable:'Comparable records are not available for these dates. This is not evidence that nothing was said.',
  required_gate:'This section is not cleared for this preview. Available sections remain below.',
  trajectory_not_integrated:'US-relative trajectories are not connected to this preview. No positions or changes are shown.',
  no_matches:'The available invented records contain no matches for these selections.',
  incomplete_coverage:'Some records could not be included. Treat the visible records as a partial account.',
  synthetic_reader_failure:'The example reader failed. No missing values have been replaced with zero.',
  resource_limit:'This selection exceeds the supported range. Your dates have not been shortened.',
  unsupported_regime:'This type of briefing is not available for the selected records.',
  invalid_contract_or_decision:'The bundle or its current permissions could not be verified. Previous results have been cleared.',
  permission_changed:'Access changed or expired. The previous briefing and its exports have been cleared.',
  selection_changed:'Selections changed. Create a briefing to apply them.',
  invalid_bundle:'The imported bundle could not be verified. Previous results have been cleared.',
  could_not_create:'The briefing could not be prepared. Check your selections or try again.',
  saved:'Saved for this session. Reopening checks current access without recalculating results.',
  development_not_authorized:'This preview accepts invented records only.'
});
export const reasonText = code => REASONS[code] || 'This section is unavailable. No unsupported result is shown.';
export const SECTIONS=Object.freeze({overview:'Overview',evidence:'Supporting evidence',comparison:'Compare with the United States',changes:'Changes over time'});
export function scopeTitle(query,catalog) {
  const country=id=>catalog.countries.find(x=>x.id===id)?.name || id;
  const topic=catalog.topics.find(x=>x.id===query.resolved.topic)?.name;
  const meeting=catalog.meetings.find(x=>x.id===query.resolved.meeting);
  return meeting ? meeting.name : query.resolved.countries.length ? query.resolved.countries.map(country).join(' and ')+(topic?' · '+topic:'') : topic || 'All available topics';
}
