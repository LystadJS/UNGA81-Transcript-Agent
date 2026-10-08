/* Public fixture: invented identifiers and values only. No UN source observations. */
(function (root, factory) {
  'use strict';
  const api=factory();
  if (typeof module==='object' && module.exports) module.exports=api;
  else root.UNEvidenceFixture=api;
})(typeof globalThis==='object'?globalThis:this,function(){
  'use strict';
  const sha=c=>c.repeat(64);
  const periods=['2025','2026','2027'];
  const national=['Illustrative State A','Illustrative State B','Illustrative State C','Illustrative State D'];
  const ids=Array.from({length:10},(_,i)=>'S'+String(i+1).padStart(2,'0'));
  const shares=[
    [.70,.30,0],[.70,.30,0],[.70,.30,0],
    [.20,.50,.30],[.30,.60,.10],[.20,.50,.30],
    [.25,.55,.20],[.30,.60,.10],[.40,.40,.20],[.30,.20,.50]
  ];
  function fixture(){
    const observations=ids.map((id,i)=>({
      id,
      text_sha256: String(i+1).padStart(2,'0').repeat(32),
      parent_id:null,parent_text_sha256:null,
      meeting_id:'demo-meeting-'+(i%3+1),speech_id:null,
      source_family_id:'demo-family-'+(i%3+1),
      date: i===9?'2026-03-01':periods[i%3]+'-03-01',
      country: i===9?null:national[Math.floor(i/3)],
      source_url:null,json_pointer:'/synthetic/'+id,
      start:null,end:null,unit:'synthetic',review_status:'not_applicable',
      exclusion_reasons:[],source_status:'available',missing_reason:null
    }));
    observations.push({
      id:'S11',text_sha256:null,parent_id:null,parent_text_sha256:null,
      meeting_id:'demo-meeting-4',speech_id:null,source_family_id:'demo-family-4',
      date:'2026-03-01',country:national[3],source_url:null,json_pointer:null,
      start:null,end:null,unit:'synthetic',review_status:'not_applicable',
      exclusion_reasons:['source_unavailable'],source_status:'unavailable',
      missing_reason:'Synthetic source absent from collected observations'
    });
    const models=[
      {model_id:'demo-nmf',method_family:'factorization',method:'nmf',
        representation_id:'demo-tfidf-2026',representation_version:'frozen-1',
        fit_version:'synthetic-1',fit_split:'synthetic',parameters_sha256:sha('d'),
        training_selection_sha256:sha('c'),diagnostic_basis:'Synthetic component shares only'},
      {model_id:'demo-partition',method_family:'partition',method:'pam',
        representation_id:'demo-tfidf-2026',representation_version:'frozen-1',
        fit_version:'synthetic-1',fit_split:'synthetic',parameters_sha256:sha('e'),
        training_selection_sha256:sha('c'),diagnostic_basis:'Synthetic cluster IDs only'}
    ];
    const results=ids.flatMap((id,i)=>[
      {model_id:'demo-nmf',observation_id:id,status:'assigned',
        cluster:1+shares[i].indexOf(Math.max(...shares[i])),membership_kind:'nmf_share',
        memberships:shares[i],membership_strength:null,
        representation_basis_id:'demo-tfidf-2026',reason:null},
      {model_id:'demo-partition',observation_id:id,
        status:i>7?'unassigned':'assigned',cluster:i>7?0:(i<4?1:2),
        membership_kind:'none',memberships:null,membership_strength:null,
        representation_basis_id:'demo-tfidf-2026',reason:i>7?'Synthetic noise / unassigned':null}
    ]);
    // Source unavailable is also excluded, not an observed zero. Preserve
    // one explicit result row for every model/source identity in the frame.
    for (const model_id of ['demo-nmf', 'demo-partition']) results.push({
      model_id, observation_id:'S11', status:'excluded', cluster:null,
      membership_kind:'none',memberships:null,membership_strength:null,
      representation_basis_id:'demo-tfidf-2026',
      reason:'source_unavailable: Synthetic source absent from collected observations'
    });
    const env={
      schema:'un.parallel-analysis.v1',contract_version:'1.0.0',
      producer:{workstream_id:'W6',adapter_version:'0.1.0',
        code_sha256:sha('a'),runtime:'browser / node 22',
        generated_at:'2026-10-08T14:50:00Z',fixture_kind:'synthetic'},
      upstream:{source_schema:'synthetic.v1',source_engine:'invented-fixtures',
        source_hash_basis:'synthetic',source_sha256:sha('b'),frame_sha256:null,
        corpus_sha256:null,selection_sha256:sha('c'),
        review_sha256:null,missing_reason:null},
      cohort:{split:'synthetic',population:'invented-demo',unit:'synthetic',
        selection_policy:'10 available examples, 1 missing synthetic record',
        weighting:'equal_passage',source_group_unit:'meeting',
        duplicate_policy:'retain_and_flag',total_in_frame:11,eligible:10},
      observations,models,results,
      coverage:{inventory_meetings:4,observations_total:11,eligible:10,
        excluded:1,unavailable_sources:1,
        models:[
          {model_id:'demo-nmf',eligible:10,assigned:10,unassigned:0,
            not_fitted:0,excluded:1,attempted_fits:1,successful_fits:1,failed_fits:0},
          {model_id:'demo-partition',eligible:10,assigned:8,unassigned:2,
            not_fitted:0,excluded:1,attempted_fits:1,successful_fits:1,failed_fits:0}
        ],failure_ledger:[]},
      evidence:ids.map(id=>({observation_id:id,source_url:null,
        json_pointer:'/synthetic/'+id,start:null,end:null,
        role:'context',proposition_id:null,verification:'synthetic'})),
      diagnostics:[{model_id:'demo-partition',name:'demo_assignment_rate',
        value:.8,denominator:10,unit:'observation',status:'descriptive',reason:null}],
      limitations:[
        {code:'synthetic_only',scope:'all',description:'Illustrative only; not source-validated.'},
        {code:'not_stance',scope:'all',description:'Language similarity and memberships do not encode government positions.'}
      ],
      publication_eligible:false,evaluation_role:'engineering_only'
    };
    const observation_refs=observations.slice(0,10).map(o=>({id:o.id,text_sha256:o.text_sha256}));
    const identity={
      source_schema:env.upstream.source_schema,
      source_hash_basis:env.upstream.source_hash_basis,
      source_sha256:env.upstream.source_sha256,
      selection_sha256:env.upstream.selection_sha256,
      unit:env.cohort.unit,weighting:env.cohort.weighting,
      representation_id:'demo-tfidf-2026',representation_version:'frozen-1',
      observation_refs
    };
    const common=(kind,measure,included,warnings=[])=>({
      kind,status:'ready',reason:null,identity:JSON.parse(JSON.stringify(identity)),
      measure,coverage:{frame:11,eligible:10,included,excluded:1,missing:1},
      warnings
    });
    const consensus={
      ...common('consensus','Equal-weight mean across eligible method-family pair co-assignment rates; not a pooled fit probability.',6,[
        'Two method families are illustrative; failure counts and zero opportunities are retained. No significance test was run.'
      ]),
      observation_ids:ids.slice(0,6),
      pairs:[]
    };
    for(let i=0;i<6;i++)for(let j=i+1;j<6;j++){
      if(i===4 && j===5)continue; // genuinely missing pair record
      const noOpportunity=(i===2 && j===4);
      const same=(i<3 && j<3)||(i>=3 && j>=3);
      consensus.pairs.push({
        a:ids[i],b:ids[j],unstable:(i===1&&j===2)||(i===2&&j===3),
        missing_reason:noOpportunity?'No eligible joint successful fits':null,
        families:noOpportunity?[
          {family:'partition',together:0,eligible:0,failed:2},
          {family:'density',together:0,eligible:0,failed:2}
        ]:[
          {family:'partition',together:same?4:1,eligible:5,failed:1},
          {family:'density',together:same?2:0,eligible:3,failed:2}
        ]
      });
    }
    const countryTheme={
      ...common('country-theme',
        'Weighted sum of normalized NMF component shares divided by all eligible weight for that country/component; no stance measurement.',9,[
        'Country and speaker labels are synthetic affiliations; one observation remains unattributed.',
        'One cell is deliberately withheld to demonstrate missing data without replacing it with zero.'
      ]),
      countries:national,unattributed_count:1,
      components:[1,2,3].map(n=>({id:'T'+n,label:'Component '+n})),
      cells:[]
    };
    for(let i=0;i<4;i++)for(let t=0;t<3;t++){
      const row=ids.slice(i*3,i*3+3);
      const missing=i===3,withheld=i===2&&t===2;
      countryTheme.cells.push({
        country:national[i],component:'T'+(t+1),
        status:missing?'missing':withheld?'withheld':'observed',
        weighted_sum:missing||withheld?null:shares.slice(i*3,i*3+3).reduce((s,a)=>s+a[t],0),
        weight_total:missing||withheld?null:3,
        evidence_count:missing||withheld?0:3,
        observation_ids:missing||withheld?[]:row,
        missing_reason:missing?'No eligible source for this synthetic country':
          withheld?'Upstream component attribution deliberately withheld':null
      });
    }
    const network={
      ...common('network','Cosine similarity of fixed synthetic input vectors on the declared high-dimensional representation, not UMAP/MDS coordinates.',7,[
        'Duplicate and agenda sensitivity are upstream flags in this fixture, not measured here.'
      ]),
      graph:{threshold:.60,metric:'cosine_similarity',selection_rule:'one edge per unordered pair ≥ 0.60'},
      nodes:ids.slice(0,7).map((id,i)=>({
        id,label:'P'+(i+1),observation_ids:[id],
        affiliation_status:'unreviewed synthetic source affiliation'
      })),
      edges:[
        ['S01','S02',.91,'stable','stable'],
        ['S01','S03',.73,'sensitive','stable'],
        ['S02','S03',.79,'not_assessed','not_assessed'],
        ['S03','S04',.68,'stable','sensitive'],
        ['S05','S06',.84,'stable','stable']
      ].map(([from,to,strength,duplicate_sensitivity,agenda_sensitivity])=>({
        from,to,strength,eligible_pairs:4,
        duplicate_sensitivity,agenda_sensitivity,
        observation_ids:[from,to]
      }))
    };
    const longitudinal={
      ...common('longitudinal',
        'Pre-aligned illustrative 2D component scores per actor-period; radius is descriptive synthetic spread, not a confidence interval.',9,[
        '2026 → 2027 fails the alignment diagnostic; trajectories across this boundary are withheld.'
      ]),
      periods,
      alignments:[
        {from:'2025',to:'2026',anchors:5,reference_basis:'demo-tfidf-2026',
          selection_comparability:'checked',status:'passed',rank_ok:true,
          degeneracy_ok:true,uncertainty_status:'illustrative_spread_only'},
        {from:'2026',to:'2027',anchors:1,reference_basis:'demo-tfidf-2026',
          selection_comparability:'not_assessed',status:'failed',rank_ok:false,
          degeneracy_ok:false,uncertainty_status:'withheld'}
      ],
      actors:[
        {id:'A',label:'Actor A',roster_status:'matched',
          attribution_status:'synthetic; not independently verified',
          positions:[
            {period:'2025',status:'observed',xy:[-.9,.5],radius:.13,n:1,observation_ids:['S01'],reason:null},
            {period:'2026',status:'observed',xy:[-.5,.16],radius:.18,n:1,observation_ids:['S02'],reason:null},
            {period:'2027',status:'observed',xy:[-.2,-.08],radius:null,n:1,observation_ids:['S03'],reason:null}
          ]},
        {id:'B',label:'Actor B',roster_status:'matched',
          attribution_status:'synthetic; not independently verified',
          positions:[
            {period:'2025',status:'observed',xy:[.65,.8],radius:.16,n:1,observation_ids:['S04'],reason:null},
            {period:'2026',status:'observed',xy:[.40,.23],radius:null,n:1,observation_ids:['S05'],reason:null},
            {period:'2027',status:'withheld',xy:null,radius:null,n:0,observation_ids:[],reason:'Source identity unresolved'}
          ]},
        {id:'C',label:'Actor C',roster_status:'arrival',
          attribution_status:'synthetic; not independently verified',
          positions:[
            {period:'2025',status:'missing',xy:null,radius:null,n:0,observation_ids:[],reason:'Not in starting roster'},
            {period:'2026',status:'observed',xy:[.8,-.72],radius:.12,n:1,observation_ids:['S08'],reason:null},
            {period:'2027',status:'observed',xy:[.6,-.50],radius:.13,n:1,observation_ids:['S09'],reason:null}
          ]}
      ]
    };
    return {envelope:env,panels:[consensus,countryTheme,network,longitudinal]};
  }
  function scenario(kind,state='empty'){
    const f=fixture(),p=f.panels.find(x=>x.kind===kind);
    if(!p)throw Error('Unknown fixture chart');
    p.status=state;
    if (state==='empty') {
      f.envelope.cohort.total_in_frame=0;
      f.envelope.cohort.eligible=0;
      f.envelope.observations=[];
      f.envelope.results=[];
      f.envelope.evidence=[];
      f.envelope.coverage.inventory_meetings=0;
      f.envelope.coverage.observations_total=0;
      f.envelope.coverage.eligible=0;
      f.envelope.coverage.excluded=0;
      f.envelope.coverage.unavailable_sources=0;
      for (const m of f.envelope.coverage.models) {
        m.eligible=0; m.assigned=0; m.unassigned=0;
        m.not_fitted=0; m.excluded=0;
        m.attempted_fits=0; m.successful_fits=0; m.failed_fits=0;
      }
      p.identity.observation_refs=[];
      p.coverage={frame:0,eligible:0,included:0,excluded:0,missing:0};
    }
    p.reason=state==='empty'?'No eligible source observations for this display':
      'Upstream calculation not validated; no display values released';
    p.coverage.included=0;
    return {envelope:f.envelope,panels:[p]};
  }
  return Object.freeze({fixture,scenario});
});
