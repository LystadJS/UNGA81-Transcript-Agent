"""Build the closed Phase 1 research-sidecar JSON Schema. No source access."""
import json
from pathlib import Path


def contract():
    def obj(properties):
        return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}
    def arr(items, lo=0, hi=20000, unique=False):
        result={'type':'array','items':items,'minItems':lo,'maxItems':hi}
        if unique: result['uniqueItems']=True
        return result
    def enum(*values):return {'enum':list(values)}
    def const(value):return {'const':value}
    def ref(name):return {'$ref':'#/$defs/'+name}
    def nullable(value):return {'anyOf':[value,{'type':'null'}]}
    def mapping(value):return {'type':'object','propertyNames':token,'additionalProperties':value,'maxProperties':20000}
    def guard(value, field, then, otherwise):
        value['allOf']=[{'if':{'properties':{field:const('ready')},'required':[field]},
            'then':{'properties':then},'else':{'properties':otherwise}}]
        return value
    token={'type':'string','pattern':r'^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,159}$','maxLength':160}
    sha={'type':'string','pattern':'^[0-9a-f]{64}$','maxLength':64}
    number={'type':'number','minimum':-1e210,'maximum':1e210}
    source_number={'type':'number','minimum':-1e100,'maximum':1e100}
    count={'type':'integer','minimum':0,'maximum':9007199254740991}
    iso={'type':'string','pattern':'^[A-Z]{3}$','maxLength':3}
    date={'type':'string','pattern':r'^\d{4}-\d{2}-\d{2}$','format':'date'}
    vector=arr(number,2,1024)
    xy=arr(number,2,2)
    states=enum('ready','empty','failed','withheld')
    d={}
    d['receipt']=obj({'kind':const('synthetic_consistency_only'),'hash_basis':const('sha256/usref-wire-v1'),'panel_sha256':sha})
    identity={'producer_schema':token,'producer_version':token,'producer_panel_sha256':sha,'selection_sha256':sha,'runtime_id':token}
    d['identity']=obj(identity)
    d['metric']=obj({'id':token,'version':token,'fingerprint':sha,'dimension':{'type':'integer','minimum':2,'maximum':1024},
        'feature_order':arr(token,2,1024,True),'space_kind':enum('full_feature_space','retained_score_space'),
        'preprocessing_id':token,'normalization':token,'fit_selection_sha256':sha,'training_cutoff':date,'upstream_fingerprint':sha})
    display={'method':token,'basis':arr(arr(source_number,2,2),2,1024),'center':arr(source_number,2,1024),'metric_fingerprint':sha,'fit_id':token}
    d['display_input']=obj(display)
    d['display_output']={'anyOf':[obj({'state':const('ready'),'reason':const(None),**display,'sha256':sha}),
        obj({'state':const('withheld'),'reason':enum('display_transform_missing','display_transform_invalid')})]}
    d['scope']=obj({'countries':arr(iso,1,256,True),'genres':arr(token,1,32,True),'language':token,'source_type':token,'topic_id':token,
        'support_mode':const('common'),'weight_policy':const('w4_equal_meeting_within_genre_equal_genre_v1'),
        'source_unit_policy':const('one_vector_per_original_parent'),'baseline_iso3':const('USA'),'baseline_mode':const('contemporaneous')})
    d['period']=obj({'id':token,'start':date,'end':date})
    evidence={k:nullable(token) for k in ['actor_id','speaker_id','speech_id','review_receipt','meeting_id','source_family_id','parent_id','missing_reason']}
    evidence.update({k:nullable(sha) for k in ['source_sha256','text_sha256','parent_text_sha256','representation_fingerprint']})
    evidence.update({'id':{'type':'string','pattern':r'^(syn-|fictional-)[A-Za-z0-9_.:/-]+$','maxLength':160},
        'period':token,'date':nullable(date),'country_iso3':nullable(iso),'capacity':enum('national','collective','un_staff','unknown'),
        'attribution_status':enum('synthetic_verified','unverified'),'genre':token,'language':token,'source_type':token,'topic_id':token,
        'source_status':enum('available','unavailable','unverified','failed','empty_transcript','inventory_failed','excluded_language'),
        'source_hash_basis':const('synthetic'),'start':nullable(count),'end':nullable(count),
        'source_pointer':nullable({'type':'string','pattern':r'^/synthetic/[A-Za-z0-9_/-]{1,200}$','maxLength':211})})
    d['evidence']=obj(evidence)
    d['observation']=obj({**evidence,'vector':nullable(arr(source_number,2,1024))})
    d['observation']['allOf']=[{'if':{'properties':{'source_status':const('available')},'required':['source_status']},
        'then':{'properties':{'vector':arr(source_number,2,1024),'date':date,'missing_reason':const(None)}},
        'else':{'properties':{'vector':const(None),'missing_reason':token}}}]
    d['source']=obj({'schema':const('un.us-relative-source-panel.v1'),'split':const('synthetic'),
        'identity':ref('identity'),'metric_space':ref('metric'),'display_space':nullable(ref('display_input')),'scope':ref('scope'),
        'periods':arr(ref('period'),2,256),'observations':arr(ref('observation'))})
    coverage=obj({'unit':const('source_observation'),'inventory':count,'included':count,'excluded':count})
    profile=obj({'id':token,'country_iso3':iso,'period':token,'scope_sha256':sha,'metric_fingerprint':sha,
        'excluded':arr(obj({'observation_id':token,'reason':token})),'coverage':coverage,'state':states,'reason':nullable(token),
        'vector':nullable(vector),'contributions':arr(obj({'observation_id':token,'weight':{'type':'number','exclusiveMinimum':0,'maximum':1}})), 'sha256':sha})
    d['profile']=guard(profile,'state',{'vector':vector,'reason':const(None),'contributions':{'minItems':1}},
        {'vector':const(None),'reason':token,'contributions':{'maxItems':0}})
    projected=obj({'state':enum('ready','withheld'),'reason':nullable(token),'country_xy':nullable(xy),'us_xy':nullable(xy),
        'relative_xy':nullable(xy),'visible_squared_gap_fraction':nullable({'type':'number','minimum':0,'maximum':1.000000001}),
        'fraction_reason':nullable(token)})
    d['projected']=guard(projected,'state',{'reason':const(None),'country_xy':xy,'us_xy':xy,'relative_xy':xy},
        {'reason':token,'country_xy':const(None),'us_xy':const(None),'relative_xy':const(None),'visible_squared_gap_fraction':const(None),'fraction_reason':token})
    comparison=obj({'id':token,'country_iso3':iso,'period':token,'country_profile_sha256':sha,'us_profile_sha256':sha,
        'state':enum('ready','withheld'),'reason':nullable(token),'distance':nullable({'type':'number','minimum':0,'maximum':1e210}),
        'relative_vector':nullable(vector),'display':nullable(ref('projected'))})
    d['comparison']=guard(comparison,'state',{'reason':const(None),'distance':{'type':'number','minimum':0},'relative_vector':vector,'display':ref('projected')},
        {'reason':token,'distance':const(None),'relative_vector':const(None),'display':const(None)})
    metrics={k:number for k in ['gap_change','country_displacement','us_displacement','relative_displacement',
        'squared_gap_country_contribution','squared_gap_us_contribution']}
    metrics.update({k:vector for k in ['country_change','us_change','relative_change']})
    metrics.update({k:nullable(number) for k in ['gap_country_contribution','gap_us_contribution','reconciliation_residual']})
    metrics.update({'decomposition_status':enum('ready','undefined_zero_gaps'),'interpretation':const('algebraic_not_causal')})
    d['metrics']=guard(obj(metrics),'decomposition_status',
        {k:number for k in ['gap_country_contribution','gap_us_contribution','reconciliation_residual']},
        {k:const(None) for k in ['gap_country_contribution','gap_us_contribution','reconciliation_residual']})
    transition=obj({'country_iso3':iso,'before':token,'after':token,'before_comparison_id':token,'after_comparison_id':token,
        'state':enum('ready','withheld'),'reason':nullable(token),'metrics':nullable(ref('metrics'))})
    d['transition']=guard(transition,'state',{'reason':const(None),'metrics':ref('metrics')}, {'reason':token,'metrics':const(None)})
    d['output']=obj({'schema':const('un.us-relative-trajectories.v1'),'version':const('0.1.0'),'split':const('synthetic'),
        'hash_basis':const('sha256/usref-wire-v1'),
        'identity':obj({**identity,'source_panel_sha256':sha,'metric_input_sha256':sha,'comparison_set_id':sha,'consistency_receipt':ref('receipt')}),
        'metric_space':ref('metric'),'display_space':ref('display_output'),
        'baseline':obj({'iso3':const('USA'),'mode':const('contemporaneous'),'attribution_rule':const('verified_national_capacity'),'profile_hashes':mapping(sha)}),
        'scope':ref('scope'),'periods':arr(ref('period'),2,256),'profiles':arr(ref('profile')),'comparisons':arr(ref('comparison')),
        'transitions':arr(ref('transition')),'evidence':arr(ref('evidence')),
        'coverage':obj({**coverage['properties'],'source_status_counts':mapping(count),'exclusion_reasons':mapping(count)}),
        'uncertainty':obj({'state':const('withheld'),'reason':const('uncertainty_unavailable'),'interval':const(None)}),
        'sensitivity':obj({'state':const('withheld'),'reason':const('not_executed'),'attempts':arr({},0,0)}),
        'permissions':obj({'evaluation_role':const('engineering_only'),'publication_eligible':const(False),
            'real_data_eligible':const(False),'holdout_access':const(False),'approval_receipts':arr({},0,0)}),'sha256':sha})
    return {'$schema':'https://json-schema.org/draft/2020-12/schema',
        '$id':'urn:unga81:research:us-relative-trajectories:phase1:0.1.0',
        'title':'US-relative synthetic research sidecar; NOT official interchange', '$ref':'#/$defs/output','$defs':d}


def write_contract():
    path=Path(__file__).with_name('schema')/'us_relative.schema.json'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(contract(),indent=2,sort_keys=True)+'\n')
    return path


if __name__=='__main__':
    write_contract()
