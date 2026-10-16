"""Source-free, non-authorizing private-source handoff proposal.

This module deliberately has no function that can issue an approval or read any
original source bytes. All gates are locked NOT_RUN. It is not a private-host
source validator and cannot serve as a ReviewDecision or UpstreamValidation.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re

SCHEMA_ID = 'un.private-source-authorization.proposal.v0'
REQUIRED_GATES = (
    'source_registry', 'original_bytes', 'text_transform', 'original_offsets',
    'selection_and_duplicates', 'source_dependence', 'country_attribution',
    'proposition_stance', 'owner_review', 'privacy', 'statistical_identification',
    'reserved_holdout', 'd1_publication',
)
HASH = re.compile(r'^[a-f0-9]{64}$')
VALID_BASIS = frozenset((
    'utf8_corpus_export', 'raw_response_bytes', 'utf8_response_text',
    'canonical_source_text', 'source_text_file_bytes', 'synthetic',
))
VALID_SOURCES = frozenset((
    'un.browser.corpus.v1', 'un.latent-comparison.v1', 'un.passage-corpus.v1',
    'un.review.v1', 'synthetic.v1',
))

class AuthorizationWithheld(ValueError):
    """Non-sensitive rejection code."""


def make_proposal(envelope: dict, envelope_digest: str) -> dict:
    """Emit only a zero-authority, synthetic metadata proposal; no source bytes.

    This does not validate the supplied analysis. Invoke canonical schema and
    relational source checks first; this preview never upgrades their verdicts.
    """
    if not isinstance(envelope, dict) or not isinstance(envelope_digest, str) or not HASH.fullmatch(envelope_digest):
        raise AuthorizationWithheld('invalid_or_unverified_envelope_reference')
    try:
        upstream = envelope['upstream']
        cohort = envelope['cohort']
        coverage = envelope['coverage']
        if not (envelope['schema'] == 'un.parallel-analysis.v1'
                and envelope['publication_eligible'] is False
                and envelope['evaluation_role'] == 'engineering_only'
                and cohort['split'] == 'synthetic'
                and envelope['producer']['fixture_kind'] == 'synthetic'):
            raise AuthorizationWithheld('real_source_authorization_not_implemented')
        source_schema = upstream['source_schema']
        hash_basis = upstream['source_hash_basis']
        source_sha = upstream['source_sha256']
        selection_sha = upstream['selection_sha256']
        counts = {key: coverage[key] for key in (
            'observations_total', 'eligible', 'excluded', 'unavailable_sources')}
        counts['total_in_frame'] = cohort['total_in_frame']
    except (TypeError, KeyError):
        raise AuthorizationWithheld('missing_public_proposal_metadata') from None
    if (source_schema not in VALID_SOURCES or hash_basis not in VALID_BASIS
            or not isinstance(source_sha, str) or not HASH.fullmatch(source_sha)
            or not isinstance(selection_sha, str) or not HASH.fullmatch(selection_sha)):
        raise AuthorizationWithheld('unbound_upstream_source_lineage')
    if (any(type(x) is not int or x < 0 for x in counts.values())
            or counts['eligible'] + counts['excluded'] != counts['observations_total']
            or counts['total_in_frame'] < counts['observations_total']
            or counts['unavailable_sources'] > counts['excluded']):
        raise AuthorizationWithheld('inconsistent_source_population')
    return {
        'schema': SCHEMA_ID,
        'contract_version': '0.1.0',
        'authority': 'none',
        'mode': 'design_only',
        'source_split': 'synthetic',
        'evaluation_role': 'engineering_only',
        'source_identity': {
            'upstream_source_schema': source_schema,
            'source_hash_basis': hash_basis,
            'source_sha256': source_sha,
            'selection_sha256': selection_sha,
            'envelope_sha256': envelope_digest,
        },
        'population': counts,
        'gate_status': {key: 'NOT_RUN' for key in REQUIRED_GATES},
        'reserved_holdout': {
            'meetings_reserved': 37,
            'transcripts_opened': 0,
            'access_granted': False,
        },
        'contains_original_source_text': False,
        'contains_row_level_source_evidence': False,
        'authorized': False,
        'publication_eligible': False,
        'delivery_eligible': False,
    }


def assert_design_only(proposal: dict) -> None:
    """Check closed proposal invariants independently of an optional JSON Schema engine."""
    if not isinstance(proposal, dict):
        raise AuthorizationWithheld('proposal_invalid')
    expected = {
        'schema', 'contract_version', 'authority', 'mode', 'source_split',
        'evaluation_role', 'source_identity', 'population', 'gate_status',
        'reserved_holdout', 'contains_original_source_text',
        'contains_row_level_source_evidence', 'authorized',
        'publication_eligible', 'delivery_eligible',
    }
    if set(proposal) != expected:
        raise AuthorizationWithheld('proposal_extra_or_missing_fields')
    if (proposal['schema'] != SCHEMA_ID or proposal['contract_version'] != '0.1.0'
            or proposal['authority'] != 'none' or proposal['mode'] != 'design_only'
            or proposal['source_split'] != 'synthetic'
            or proposal['evaluation_role'] != 'engineering_only'):
        raise AuthorizationWithheld('proposal_cannot_grant_authority')
    if (proposal['authorized'] is not False or proposal['publication_eligible'] is not False
            or proposal['delivery_eligible'] is not False
            or proposal['contains_original_source_text'] is not False
            or proposal['contains_row_level_source_evidence'] is not False):
        raise AuthorizationWithheld('proposal_cannot_grant_authority')
    if proposal['reserved_holdout'] != {'meetings_reserved': 37, 'transcripts_opened': 0,
                                         'access_granted': False}:
        raise AuthorizationWithheld('reserved_holdout_must_remain_sealed')
    if proposal['gate_status'] != {key: 'NOT_RUN' for key in REQUIRED_GATES}:
        raise AuthorizationWithheld('private_gates_must_remain_not_run')
    identity = proposal['source_identity']
    if not isinstance(identity, dict) or set(identity) != {'upstream_source_schema',
         'source_hash_basis', 'source_sha256', 'selection_sha256', 'envelope_sha256'}:
        raise AuthorizationWithheld('source_identity_invalid')
    if identity['upstream_source_schema'] not in VALID_SOURCES or identity['source_hash_basis'] not in VALID_BASIS:
        raise AuthorizationWithheld('source_identity_invalid')
    if not all(isinstance(identity[key], str) and HASH.fullmatch(identity[key]) for key in (
        'source_sha256','selection_sha256','envelope_sha256')):
        raise AuthorizationWithheld('source_identity_invalid')
    p = proposal['population']
    if not isinstance(p, dict) or set(p) != {
         'total_in_frame','observations_total','eligible','excluded','unavailable_sources'}:
        raise AuthorizationWithheld('population_invalid')
    if (any(type(v) is not int or v < 0 for v in p.values()) or
            p['total_in_frame'] < p['observations_total'] or
            p['eligible'] + p['excluded'] != p['observations_total'] or
            p['unavailable_sources'] > p['excluded']):
        raise AuthorizationWithheld('population_invalid')


def proposal_digest(proposal: dict) -> str:
    assert_design_only(proposal)
    raw = json.dumps(proposal, sort_keys=True, separators=(',', ':'),
                     ensure_ascii=False, allow_nan=False).encode('utf-8')
    return sha256(b'un.private-source-authorization.proposal.v0\n' + raw).hexdigest()
