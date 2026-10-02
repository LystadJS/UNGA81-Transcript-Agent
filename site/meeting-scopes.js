/*
 * Shared meeting-scope rules for live collection and saved collections.
 *
 * Only meeting metadata is inspected. Transcript text, speaker affiliations,
 * and subject-matter keywords never determine committee membership.
 */
(function (root) {
  'use strict';

  const ORIGIN = 'https://transcripts.un.org';

  const OPTIONS = Object.freeze([
    { value: 'general_debate', label: 'General Debate meetings' },
    { value: 'all', label: 'All UN meetings in the inventory' },
    { value: 'committee_1', label: 'First Committee — Disarmament and International Security' },
    { value: 'committee_2', label: 'Second Committee — Economic and Financial' },
    { value: 'committee_3', label: 'Third Committee — Social, Humanitarian and Cultural' },
    { value: 'committee_4', label: 'Fourth Committee — Special Political and Decolonization' },
    { value: 'committee_5', label: 'Fifth Committee — Administrative and Budgetary' },
    { value: 'committee_6', label: 'Sixth Committee — Legal' }
  ]);

  const VALID_SCOPES = new Set(OPTIONS.map(option => option.value));

  const ORDINALS = [
    'first|1st',
    'second|2nd',
    'third|3rd',
    'fourth|4th',
    'fifth|5th',
    'sixth|6th'
  ];

  const NAMES = [
    'disarmament and international security',
    'economic and financial',
    'social humanitarian and cultural',
    'special political and decolonization',
    'administrative and budgetary',
    'legal'
  ];


  // Normalize only metadata labels; do not search the speech for committee names.
  function normalize(value) {
    return String(value || '')
      .normalize('NFKC')
      .toLowerCase()
      .replace(/&/g, ' and ')
      .replace(/[^\p{L}\p{N}]+/gu, ' ')
      .trim()
      .replace(/\s+/g, ' ');
  }


  function isValid(scope) {
    return VALID_SCOPES.has(scope);
  }


  function label(scope) {
    return OPTIONS.find(option => option.value === scope)?.label || 'Other / unclassified meeting';
  }


  // A canonical UN path is stronger evidence than a descriptive title.
  // Example: /en/ga/c3/81/1 identifies Third Committee, session 81, meeting 1.
  function committeeFromPath(value) {
    if (typeof value !== 'string' || !value.trim()) return null;

    try {
      const url = new URL(value, ORIGIN + '/');

      if (url.origin !== ORIGIN || url.username || url.password) return null;

      const match = url.pathname.match(/^\/(?:[a-z]{2}\/)?ga\/c([1-6])(?:\/|$)/i);

      return match ? 'committee_' + match[1] : null;
    } catch {
      return null;
    }
  }


  function classifyMeeting(meeting) {
    const paths = [
      meeting.pageUrl,
      meeting.jsonUrl,
      meeting.source_url,
      meeting.slug
    ];

    const pathScopes = new Set(paths.map(committeeFromPath).filter(Boolean));

    // Conflicting committee identifiers are not safe to assign to either one.
    if (pathScopes.size > 1) return 'other';
    if (pathScopes.size === 1) return [...pathScopes][0];

    const title = normalize(meeting.title || meeting.meeting);

    // Accept a committee label at the start of a meeting title, optionally
    // introduced by "General Assembly". A press briefing ABOUT a committee
    // is not automatically a meeting OF that committee.
    const prefix = '^(?:general assembly )?';
    const matches = [];

    for (let index = 0; index < ORDINALS.length; index++) {
      const numbered = new RegExp(prefix + '(?:' + ORDINALS[index] + ') committee\\b');
      const named = new RegExp(
        prefix + NAMES[index] + ' (?:issues )?(?:(?:' + ORDINALS[index] + ') )?committee\\b'
      );
      const explicitNumber = new RegExp('\\b(?:' + ORDINALS[index] + ') committee\\b');
      const assemblyContext = /\bgeneral assembly\b/.test(title) || explicitNumber.test(title);

      if (numbered.test(title) || (named.test(title) && assemblyContext)) {
        matches.push('committee_' + (index + 1));
      }
    }

    if (matches.length === 1) return matches[0];
    if (matches.length > 1) return 'other';

    // A committee's own general debate must not become the GA General Debate.
    if (/\bcommittee\b/.test(title)) return 'other';

    return /\bgeneral debate\b/.test(title) ? 'general_debate' : 'other';
  }


  function recordScope(record) {
    const inferred = classifyMeeting({
      title: record.meeting,
      source_url: record.source_url,
      slug: typeof record.id === 'string' ? record.id.split('#')[0] : ''
    });

    if (inferred !== 'other') return inferred;

    // Do not override ambiguous committee metadata with a legacy coarse label.
    const hasCommitteePath = [record.source_url, record.id?.split('#')[0]]
      .some(value => committeeFromPath(value) !== null);

    if (hasCommitteePath || /\bcommittee\b/.test(normalize(record.meeting))) return 'other';

    // Older exports used only "general_debate" and "other". Keep explicit
    // supported values when the retained metadata cannot refine them.
    return isValid(record.scope) && record.scope !== 'all' ? record.scope : 'other';
  }


  function matchesMeeting(meeting, scope) {
    if (!isValid(scope)) throw Error('Invalid meeting scope.');

    return scope === 'all' || classifyMeeting(meeting) === scope;
  }


  function matchesRecord(record, scope) {
    if (!isValid(scope)) throw Error('Invalid meeting scope.');

    return scope === 'all' || recordScope(record) === scope;
  }


  // A broad saved collection can be narrowed, but a narrow collection cannot
  // supply other committees or the full UN inventory.
  function covers(collectedScope, requestedScope) {
    return isValid(collectedScope) && isValid(requestedScope) &&
      (collectedScope === 'all' || collectedScope === requestedScope);
  }


  const api = {
    OPTIONS,
    isValid,
    label,
    committeeFromPath,
    classifyMeeting,
    recordScope,
    matchesMeeting,
    matchesRecord,
    covers
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  } else {
    root.UNMeetingScopes = api;
  }

})(typeof globalThis !== 'undefined' ? globalThis : this);
