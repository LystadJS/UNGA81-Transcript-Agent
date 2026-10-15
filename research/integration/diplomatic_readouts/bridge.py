"""Coordinator-only synthetic v1 interchange -> source-bound readout candidate.

No consumer/renderer is imported until a caller supplies the accepted readout
module. The bridge never authenticates real UN originals, issues review decisions,
runs statistical models or publishes. Production splits are refused by design.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping

try:
    from jsonschema import Draft202012Validator
except ImportError:
    Draft202012Validator = None

REPO = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO / 'docs/parallel-work/interchange-v1.schema.json'
CODE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$')
HASH = re.compile(r'^[0-9a-f]{64}$')
EXCLUDED_SOURCE_STATES = ('unavailable', 'failed', 'excluded_language', 'empty_transcript', 'inventory_failed')
EVIDENCE_ROLES = {'supporting': 'representative', 'contrary': 'contrary'}
INTENT_KEYS = {'title', 'template', 'findings', 'uncertainty', 'sensitivity', 'alternative_explanations', 'reviewer_note', 'model_id'}
FINDING_KEYS = {'id', 'category', 'label', 'observation', 'pattern', 'reviewer_interpretation',
                'supporting', 'contrary', 'contrary_search', 'uncertainty', 'sensitivity',
                'alternative_explanations', 'country_attribution', 'stance'}


class Withheld(ValueError):
    """Safe fixed-code reason; never contains source bytes or user-authored prose."""
    def __init__(self, code: str):
        assert CODE.fullmatch(code)
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class UpstreamValidation:
    """Opaque result supplied by an upstream validator on a trusted host.

    Digest matching is a consistency check, not a signature. Constructing this
    object from user input is forbidden outside synthetic tests. The caller
    must independently run canonical source and v1 relational validation.
    """
    envelope_sha256: str
    source_schema: str
    source_hash_basis: str
    source_sha256: str
    selection_sha256: str
    contract: str = 'un.parallel-analysis.v1'


@dataclass(frozen=True)
class Candidate:
    """Approved-input-shaped draft, NOT an approved or publishable readout."""
    report: dict
    proofs: Mapping[str, Any]  # trusted readout.SourceReceipt instances; include private original bytes
    envelope_sha256: str
    population_audit: dict


def digest(obj: object) -> str:
    try:
        raw = json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                         allow_nan=False).encode('utf-8')
    except (TypeError, ValueError, UnicodeError) as exc:
        raise Withheld('invalid_json_input') from None
    return sha256(b'un.parallel-analysis.v1\n' + raw).hexdigest()


def _ensure(ok: bool, code: str) -> None:
    if not ok:
        raise Withheld(code)


def _sha(data: bytes) -> str:
    return sha256(data).hexdigest()


def _id(x: object) -> bool:
    return isinstance(x, str) and CODE.fullmatch(x) is not None


def _positive(x: object) -> bool:
    return type(x) is int and x >= 0


def _raw_text(proof: Any) -> str | None:
    try:
        document = proof.original_bytes.decode('utf-8')
        if proof.json_pointer is None:
            return document
        if not isinstance(proof.json_pointer, str) or not proof.json_pointer.startswith('/'):
            return None
        node = json.loads(document)
        for part in proof.json_pointer[1:].split('/'):
            if re.search(r'~(?![01])', part):
                return None
            key = part.replace('~1', '/').replace('~0', '~')
            if isinstance(node, dict):
                node = node[key]
            elif isinstance(node, list) and re.fullmatch(r'0|[1-9][0-9]*', key):
                node = node[int(key)]
            else:
                return None
        return node if isinstance(node, str) else None
    except (UnicodeError, ValueError, KeyError, IndexError, TypeError, OverflowError):
        return None


def validate_interchange(envelope: dict, validation: UpstreamValidation, *, schema_path: Path = SCHEMA_PATH) -> dict:
    """Independent structural + relational preflight, not a replacement for source authentication."""
    _ensure(isinstance(envelope, dict), 'interchange_not_object')
    _ensure(Draft202012Validator is not None, 'jsonschema_dependency_missing')
    _ensure(schema_path.is_file(), 'canonical_schema_unavailable')
    try:
        schema = json.loads(schema_path.read_text('utf-8'))
        Draft202012Validator.check_schema(schema)
        violations = list(Draft202012Validator(schema).iter_errors(envelope))
    except (ValueError, TypeError, UnicodeError, OSError):
        raise Withheld('canonical_schema_unavailable') from None
    _ensure(not violations, 'interchange_schema_invalid')
    _ensure(envelope['schema'] == 'un.parallel-analysis.v1' and
            envelope['publication_eligible'] is False and envelope['evaluation_role'] == 'engineering_only',
            'interchange_publication_authority_invalid')
    _ensure(envelope['cohort']['split'] == 'synthetic' and
            envelope['producer']['fixture_kind'] == 'synthetic', 'real_source_mode_disabled')
    _ensure(isinstance(validation, UpstreamValidation) and
            validation.contract == envelope['schema'] and
            validation.envelope_sha256 == digest(envelope) and
            validation.source_schema == envelope['upstream']['source_schema'] and
            validation.source_hash_basis == envelope['upstream']['source_hash_basis'] and
            validation.source_sha256 == envelope['upstream']['source_sha256'] and
            validation.selection_sha256 == envelope['upstream']['selection_sha256'] and
            isinstance(validation.source_sha256, str) and HASH.fullmatch(validation.source_sha256) and
            isinstance(validation.selection_sha256, str) and HASH.fullmatch(validation.selection_sha256),
            'upstream_validation_receipt_missing_or_mismatch')
    c, a, cv = envelope['cohort'], envelope['observations'], envelope['coverage']
    ids = [o['id'] for o in a]
    mids = [m['model_id'] for m in envelope['models']]
    _ensure(len(ids) == len(set(ids)) and len(mids) == len(set(mids)), 'duplicate_source_or_model_id')
    _ensure(cv['observations_total'] == len(a) and cv['eligible'] == c['eligible'] and
            cv['eligible'] + cv['excluded'] == len(a) and c['total_in_frame'] >= len(a),
            'interchange_population_mismatch')
    _ensure(len(cv['models']) == len(mids) and set(m['model_id'] for m in cv['models']) == set(mids),
            'interchange_model_coverage_mismatch')
    eligible = [o for o in a if o['source_status'] == 'available' and not o['exclusion_reasons']]
    _ensure(len(eligible) == cv['eligible'], 'interchange_eligibility_mismatch')
    byid = {o['id']: o for o in a}
    bymodel = {m['model_id']: m for m in envelope['models']}
    count_models = {m['model_id']: m for m in cv['models']}
    for o in a:
        _ensure((o['start'] is None) == (o['end'] is None), 'interchange_half_null_span')
        if o['start'] is not None:
            _ensure(o['start'] < o['end'], 'interchange_invalid_span')
        _ensure(o['parent_id'] is None or o['parent_text_sha256'] is not None, 'interchange_unverified_parent')
        _ensure(o['source_status'] == 'available' or bool(o['missing_reason']), 'interchange_missing_reason_absent')
        _ensure(o['review_status'] == 'confirmed' or o['speech_id'] is None, 'interchange_unreviewed_speech')
        if o['source_status'] == 'available' and not o['exclusion_reasons']:
            _ensure(o['text_sha256'] is not None, 'interchange_eligible_source_hash_absent')
    result_index = {}
    for result in envelope['results']:
        k = (result['model_id'], result['observation_id'])
        _ensure(k not in result_index and result['model_id'] in bymodel and
                result['observation_id'] in byid, 'interchange_result_join_invalid')
        result_index[k] = result
        _ensure(result['representation_basis_id'] == bymodel[result['model_id']]['representation_id'],
                'interchange_representation_mismatch')
        status = result['status']
        _ensure(status != 'assigned' or type(result['cluster']) is int and result['cluster'] > 0,
                'interchange_cluster_invalid')
        _ensure(status != 'unassigned' or result['cluster'] == 0, 'interchange_unassigned_label_invalid')
        _ensure(status not in ('not_fitted', 'excluded') or
                (result['cluster'] is None and bool(result['reason'])), 'interchange_failed_fit_not_recorded')
        if result['membership_kind'] in ('nmf_share', 'gmm_responsibility'):
            weights = result['memberships']
            _ensure(isinstance(weights, list) and len(weights)>0 and abs(sum(weights)-1) < 1e-6,
                    'interchange_soft_membership_invalid')
        else:
            _ensure(result['memberships'] is None, 'interchange_membership_type_invalid')
    for modelid, model in bymodel.items():
        cm = count_models[modelid]
        rows = [r for r in envelope['results'] if r['model_id'] == modelid]
        _ensure(cm['eligible'] == c['eligible'] and
                cm['eligible'] == sum(cm[k] for k in ('assigned','unassigned','not_fitted')) and
                cm['attempted_fits'] == cm['successful_fits'] + cm['failed_fits'],
                'interchange_fit_coverage_invalid')
        for status in ('assigned','unassigned','not_fitted','excluded'):
            _ensure(sum(r['status']==status for r in rows) == cm[status],
                    'interchange_result_coverage_mismatch')
        _ensure(all((modelid, o['id']) in result_index for o in eligible), 'interchange_missing_eligible_result')
        _ensure(sum(r['status']=='excluded' for r in rows) == cv['excluded'],
                'interchange_exclusion_mismatch')
        for r in rows:
            o = byid[r['observation_id']]
            _ensure((o in eligible) == (r['status'] != 'excluded'), 'interchange_result_eligibility_conflict')
    for f in cv['failure_ledger']:
        _ensure(f['model_id'] in bymodel, 'interchange_unknown_failure_model')
    for e in envelope['evidence']:
        _ensure(e['observation_id'] in byid, 'interchange_unknown_evidence_source')
        obs = byid[e['observation_id']]
        _ensure((e['start'] is None) == (e['end'] is None), 'interchange_evidence_half_null')
        if e['start'] is not None:
            _ensure(e['start'] < e['end'], 'interchange_evidence_span_invalid')
            if obs['start'] is not None:
                _ensure(obs['start'] <= e['start'] and e['end'] <= obs['end'],
                        'interchange_evidence_outside_observation')
        _ensure(e['source_url'] == obs['source_url'] and e['json_pointer'] == obs['json_pointer'],
                'interchange_evidence_identity_mismatch')
    for d in envelope['diagnostics']:
        _ensure(d['model_id'] is None or d['model_id'] in bymodel, 'interchange_diagnostic_model_invalid')
        _ensure(d['status'] not in ('failed','withheld') or bool(d['reason']),
                'interchange_diagnostic_failure_unexplained')
    return {'observations':byid,'models':bymodel,'model_counts':count_models, 'eligible':eligible,
            'result_index':result_index}


def _verify_material(obs: dict, proof: Any, upstream: dict, readout_module: Any) -> None:
    _ensure(isinstance(proof, readout_module.SourceReceipt),
            'authenticated_source_receipt_required')
    _ensure(proof.accepted is True and proof.public is True and type(proof.original_bytes) is bytes and
            isinstance(proof.text, str), 'authenticated_source_receipt_required')
    _ensure(proof.source_id == obs['id'] and proof.representation_id is not None and
            proof.parent_id == obs['parent_id'] and proof.meeting_id == obs['meeting_id'] and
            proof.speech_id == obs['speech_id'] and proof.source_family_id == obs['source_family_id'] and
            proof.source_url == obs['source_url'] and proof.json_pointer == obs['json_pointer'],
            'source_parent_or_representation_mismatch')
    _ensure(obs['text_sha256'] == _sha(proof.text.encode('utf-8')) and
            obs['parent_text_sha256'] == _sha(proof.text.encode('utf-8')),
            'source_text_hash_basis_mismatch')
    _ensure(_raw_text(proof) == proof.text, 'source_original_bytes_mismatch')
    _ensure(obs['start'] is not None and obs['end'] is not None and
            obs['end'] <= len(proof.text), 'source_offset_basis_missing')
    _ensure(upstream['source_hash_basis'] in ('synthetic','raw_response_bytes','canonical_source_text','utf8_response_text','utf8_corpus_export','source_text_file_bytes'),
            'source_hash_basis_unrecognized')


def _make_coverage(envelope: dict, chosen_model: str) -> dict:
    obs, cv, co = envelope['observations'], envelope['coverage'], envelope['cohort']
    unavailable = [x for x in obs if x['source_status'] != 'available']
    missing_external = co['total_in_frame']-len(obs)
    reasons = {}
    missing_reasons = {}
    for o in obs:
        if o['source_status'] in EXCLUDED_SOURCE_STATES:
            label = 'unavailable_' + o['source_status']
            missing_reasons[label] = missing_reasons.get(label,0)+1
        elif o['exclusion_reasons']:
            # Record a deterministic primary reason, not duplicate-count an observation.
            label = 'excluded_' + sorted(o['exclusion_reasons'])[0]
            reasons[label] = reasons.get(label,0)+1
    if missing_external:
        missing_reasons['unobserved_inventory'] = missing_external
    cm = next(x for x in cv['models'] if x['model_id']==chosen_model)
    return {'population':co['population'],
            'period':_period(obs), 'unit':co['unit'], 'weighting':co['weighting'],
            'source_group_unit':co['source_group_unit'],
            'total_in_frame':co['total_in_frame'], 'eligible':cv['eligible'],
            'excluded':cv['excluded']-len(unavailable), 'missing':len(unavailable)+missing_external,
            'exclusion_reasons':[{'code':k,'count':v} for k,v in sorted(reasons.items())],
            'missing_reasons':[{'code':k,'count':v} for k,v in sorted(missing_reasons.items())],
            'planned_fits':cm['attempted_fits']+cm.get('skipped_fits',0),
            'attempted_fits':cm['attempted_fits'], 'converged_fits':cm['successful_fits'],
            'failed_fits':cm['failed_fits'], 'skipped_fits':cm.get('skipped_fits',0),
            'unassigned':cm['unassigned']}


def _period(obs: list[dict]) -> str:
    dates = sorted({o['date'] for o in obs if o['source_status']=='available'})
    return (dates[0]+' to '+dates[-1]) if dates else 'No available dated observation'


def prepare(envelope: dict, intent: dict, proofs: Mapping[str, Any], validation: UpstreamValidation,
            *, schema_path: Path = SCHEMA_PATH, readout_module: Any) -> Candidate:
    """Map a SYNTHETIC canonical v1 output into an unapproved readout candidate.

    No ReviewDecision is created. The separate accepted renderer will withhold
    every finding until a truly independent reviewer/source/privacy decision
    bound to its report digest is supplied by the coordinator.
    """
    v = validate_interchange(envelope, validation, schema_path=schema_path)
    _ensure(type(intent) is dict and set(intent) == INTENT_KEYS and
            isinstance(intent['findings'], list) and intent['findings'],
            'authoring_intent_incomplete')
    chosen = intent['model_id']
    _ensure(_id(chosen) and chosen in v['models'], 'interchange_model_not_selected')
    _ensure(type(proofs) is dict and all(isinstance(k,str) for k in proofs), 'invalid_trusted_registry')
    selected_ids = set()
    rendered_findings = []
    evidence = {}
    for e in envelope['evidence']:
        key = (e['observation_id'],e['role'])
        _ensure(key not in evidence, 'ambiguous_evidence_pointer')
        evidence[key]=e
    for finding in intent['findings']:
        _ensure(type(finding) is dict and set(finding)==FINDING_KEYS,
                'finding_authoring_invalid')
        _ensure(finding['country_attribution'] is None and finding['stance'] is None,
                'country_stance_requires_separate_adjudication')
        _ensure(finding['contrary_search'] in ('not_assessed','identified'),
                'contrary_absence_cannot_be_certified')
        _ensure(isinstance(finding['supporting'],list) and finding['supporting'] and
                isinstance(finding['contrary'],list), 'evidence_binding_missing')
        output_refs = {}
        for kind, role in EVIDENCE_ROLES.items():
            refs=[]
            for obs_id in finding[kind]:
                _ensure(_id(obs_id) and obs_id in v['observations'], 'unknown_evidence_observation')
                obs=v['observations'][obs_id]
                _ensure(obs in v['eligible'], 'unavailable_or_excluded_evidence')
                _ensure((obs_id,role) in evidence, 'unverified_evidence_role_or_identity')
                e=evidence[(obs_id,role)]
                _ensure(e['verification']=='synthetic' and e['start'] is not None and
                        e['end'] is not None and e['end']>e['start'],
                        'evidence_verification_or_span_missing')
                _ensure(v['result_index'][(chosen,obs_id)]['status'] in ('assigned','unassigned','not_fitted'),
                        'model_source_join_invalid')
                proof=proofs.get(obs_id)
                _verify_material(obs,proof,envelope['upstream'],readout_module)
                _ensure(e['end']<=len(proof.text) and e['start']>=0,
                        'evidence_offset_outside_text')
                selected_ids.add(obs_id)
                refs.append({'source_id':obs_id, 'text_sha256':obs['text_sha256'],
                             'representation_id':v['models'][chosen]['representation_id'],
                             'start':e['start'], 'end':e['end'], 'json_pointer':e['json_pointer']})
                _ensure(proof.representation_id == v['models'][chosen]['representation_id'],
                        'evidence_representation_mismatch')
            output_refs[kind]=refs
        _ensure((finding['contrary_search']=='identified') == bool(output_refs['contrary']),
                'contrary_search_ledger_mismatch')
        result = {key:finding[key] for key in FINDING_KEYS if key not in ('supporting','contrary')}
        result.update(output_refs)
        rendered_findings.append(result)
    sources=[]
    for id in sorted(selected_ids):
        proof=proofs[id]; obs=v['observations'][id]
        sources.append({'id':id,'raw_sha256':_sha(proof.original_bytes),
                        'text_sha256':obs['text_sha256'],'hash_basis':'original_bytes',
                        'representation_id':proof.representation_id,'parent_id':proof.parent_id,
                        'text_length':len(proof.text),'source_url':proof.source_url,
                        'meeting_id':proof.meeting_id, 'speech_id':proof.speech_id,
                        'source_family_id':proof.source_family_id,'json_pointer':proof.json_pointer})
    report={'schema':readout_module.SCHEMA,'title':intent['title'],'template':intent['template'],
            'coverage':_make_coverage(envelope,chosen), 'sources':sources,
            'findings':rendered_findings,
            'uncertainty':intent['uncertainty'], 'sensitivity':intent['sensitivity'],
            'alternative_explanations':intent['alternative_explanations'],
            'reviewer_note':intent['reviewer_note']}
    # Full authoring schema is checked by the exact imported readout version.
    # validate() without a reviewer would always return an authorization error,
    # so inspect the closed authoring structure with its native validator.
    _ensure(not readout_module._structure(report), 'generated_readout_schema_invalid')
    return Candidate(report=report, proofs={k:proofs[k] for k in sorted(selected_ids)},
                     envelope_sha256=digest(envelope),
                     population_audit={key:report['coverage'][key] for key in
                         ('total_in_frame','eligible','excluded','missing','planned_fits',
                          'attempted_fits','converged_fits','failed_fits','skipped_fits','unassigned')})
