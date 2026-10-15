/* Offline fictional catalogue consumer. No fitting, fetch, storage or arbitrary model import. */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else { root.USReferenceViews = api; api.mount(document).then(controller=>{root.USReferenceView=controller;}).catch(()=>{document.getElementById('status').textContent='Catalogue integrity validation failed. No charts or exports are available.';document.getElementById('status').dataset.state='failed';}); }
})(typeof globalThis === 'object' ? globalThis : this, function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const NAME = {USA:'United States', CAN:'Canada', FRA:'France', IND:'India', BRA:'Brazil', GBR:'United Kingdom'};
  const COL = {USA:'#303b49', CAN:'#126478', FRA:'#754287', IND:'#975025', BRA:'#365fc1', GBR:'#555e69'};
  const REPLAY = 'un.us-relative-view-replay.v1';
  const need = (test, message) => { if (!test) throw new Error(message); };
  const exact = (o, keys) => need(o && !Array.isArray(o) && typeof o === 'object' &&
    Object.keys(o).sort().join('|') === [...keys].sort().join('|'), 'Unexpected replay fields');
  const freeze = o => { if (o && typeof o === 'object' && !Object.isFrozen(o)) {Object.values(o).forEach(freeze);Object.freeze(o);} return o; };
  const esc = x => String(x).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt = x => x === null || x === undefined ? 'Unavailable' : Number(x).toLocaleString('en-US',{maximumFractionDigits:3});
  const short = x => x.length > 28 ? x.slice(0,25)+'…' : x;
  const reason = x => x ? x.replaceAll('_',' ') : 'ready';
  function row(model, country, period) { return model.comparisons.find(x=>x.country_iso3===country && x.period===period); }
  function profile(model, country, period) { return model.profiles.find(x=>x.country_iso3===country && x.period===period); }
  function radius(model) {
    let max = 1;
    for (const c of model.comparisons) if(c.display?.state==='ready') {
      for (const key of ['country_xy','us_xy','relative_xy']) for(const x of c.display[key]) max = Math.max(max,Math.abs(x));
    }
    return Math.ceil(max*1.22*2)/2; // Frozen for the entire scene, not the selected country/period.
  }
  function series(model, country, kind) {
    const points = model.periods.map((p,i)=>{
      const r=row(model,country,p.id), d=r.display;
      const value=kind==='gap'?r.distance:d?.state==='ready'?d[kind==='absolute'?'country_xy':'relative_xy']:null;
      return {i,period:p.id,date:p.end,value,ready:r.state==='ready' && value!==null};
    });
    const edges=model.transitions.filter(t=>t.country_iso3===country && t.state==='ready').map(t=>{
      const a=points.find(p=>p.period===t.before),b=points.find(p=>p.period===t.after);
      return a?.ready && b?.ready && b.i===a.i+1 ? [a,b] : null;
    }).filter(Boolean);
    return {points,edges};
  }
  function elapsedPositions(periods) {
    const dates=periods.map(p=>Date.parse(p.end+'T00:00:00Z')), span=dates.at(-1)-dates[0];
    need(span>0 && dates.every(Number.isFinite),'Invalid plotting dates');
    return dates.map(d=>(d-dates[0])/span);
  }
  function replay(catalogue, sceneId, country, period) {
    const scene=catalogue.scenes.find(s=>s.id===sceneId);
    need(scene && scene.model.scope.countries.includes(country) && scene.model.periods.some(p=>p.id===period),'Unknown catalogue selection');
    return {schema:REPLAY,catalogue_sha256:catalogue.sha256,scene_id:sceneId,model_sha256:scene.model.sha256,
      country_iso3:country,period,publication_eligible:false,split:'synthetic'};
  }
  function validateReplay(value, catalogue) {
    exact(value,['schema','catalogue_sha256','scene_id','model_sha256','country_iso3','period','publication_eligible','split']);
    need(value.schema===REPLAY && value.catalogue_sha256===catalogue.sha256 && value.publication_eligible===false && value.split==='synthetic','Unsupported replay');
    const expected=replay(catalogue,value.scene_id,value.country_iso3,value.period);
    need(Object.keys(expected).every(k=>value[k]===expected[k]),'Replay does not match the built-in synthetic catalogue');
    return expected;
  }
  function csv(model) {
    const fields=['comparison_id','country_iso3','period','period_start','period_end','state','reason',
      'country_state','country_reason','us_state','us_reason','distance','relative_x','relative_y',
      'visible_squared_gap_fraction','country_profile_sha256','us_profile_sha256','model_sha256',
      'comparison_set_id','weight_policy','split','publication_eligible'];
    const cell=x=>{
      if(x===null || x===undefined) return '';
      let s=String(x);
      if(typeof x==='string' && /^[=+@\-\t\r]/.test(s)) s="'"+s;
      return '"'+s.replaceAll('"','""')+'"';
    };
    return [fields.join(','),...model.comparisons.map(c=>{
      const p=model.periods.find(p=>p.id===c.period),cp=profile(model,c.country_iso3,c.period),up=profile(model,'USA',c.period);
      return [c.id,c.country_iso3,c.period,p.start,p.end,c.state,c.reason,cp.state,cp.reason,up.state,up.reason,
        c.distance,c.display?.relative_xy?.[0],c.display?.relative_xy?.[1],c.display?.visible_squared_gap_fraction,
        cp.sha256,up.sha256,model.sha256,model.identity.comparison_set_id,model.scope.weight_policy,'synthetic',false].map(cell).join(',');
    })].join('\r\n')+'\r\n';
  }
  async function mount(doc) {
    const data=doc.getElementById('catalogue').textContent;
    for(const el of doc.querySelectorAll('button,select,input'))el.disabled=true;
    const bytes=new TextEncoder().encode(data);
    const hash=Array.from(new Uint8Array(await doc.defaultView.crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
    need(hash==='@@CATALOGUE_BYTES_SHA@@','Catalogue bytes changed');
    const catalogue=freeze(JSON.parse(data));
    for(const el of doc.querySelectorAll('button,select,input'))el.disabled=false;
    const originalHTML='<!doctype html>\n'+doc.documentElement.outerHTML;
    let active=null, generation=0;
    const $=id=>doc.getElementById(id);
    function status(text, state) { $('status').textContent=text; $('status').dataset.state=state; }
    function clear(state, text) {
      active=null;
      for(const id of ['absolute','relative','gap','contributions','matrix','evidence','summary','provenance']) $(id).replaceChildren();
      for(const b of doc.querySelectorAll('[data-export]')) b.disabled=true;
      $('period').disabled=true; $('country').disabled=true;
      status(text,state);
    }
    function selection() { need(active,'No validated selection'); return replay(catalogue,active.scene.id,active.country,active.period); }
    function choose(sceneId, country='CAN', period=null) {
      generation++;
      const scene=catalogue.scenes.find(s=>s.id===sceneId); need(scene,'Unknown scenario');
      country=scene.model.scope.countries.includes(country)?country:'CAN';
      period=period || scene.model.periods.at(-1).id;
      validateReplay(replay(catalogue,sceneId,country,period),catalogue);
      active={scene,country,period};
      $('scenario').value=sceneId;
      $('country').replaceChildren(...scene.model.scope.countries.map(c=>new Option(NAME[c]+' · '+c,c)));
      $('country').value=country; $('country').disabled=false;
      $('period').replaceChildren(...scene.model.periods.map(p=>new Option(p.end.slice(0,4)+' · '+short(p.id),p.id)));
      $('period').value=period; $('period').disabled=false;
      for(const b of doc.querySelectorAll('[data-export]')) b.disabled=false;
      render();
      status('Ready — bundled synthetic scenario; source-bound results, not authenticated UN evidence.','ready');
    }
    function pick(country,period,focusKind=null) {
      if(!active)return;
      generation++; active={...active,country,period}; $('country').value=country; $('period').value=period; render();
      if(focusKind) {
        const point=doc.querySelector('#'+focusKind+' [data-p-index="'+active.scene.model.periods.findIndex(p=>p.id===period)+'"][data-country="'+country+'"]');
        if(point)point.focus();
      }
    }
    function svgRoot(id,label,description,w=480,h=458) {
      const s=doc.createElementNS(NS,'svg'); s.setAttribute('viewBox',`0 0 ${w} ${h}`);
      s.setAttribute('role','group'); s.setAttribute('aria-labelledby',id+'-title '+id+'-desc');
      s.innerHTML=`<title id="${id}-title">${esc(label)}</title><desc id="${id}-desc">${esc(description)}</desc>`;
      return s;
    }
    function add(s,tag,attrs,text) {
      const el=doc.createElementNS(NS,tag); for(const [k,v] of Object.entries(attrs||{}))el.setAttribute(k,String(v));
      if(text!==undefined)el.textContent=text; s.append(el); return el;
    }
    function marker(s,kind,c,p,x,y,radius=5) {
      const label=`${NAME[c]}, ${active.scene.model.periods[p.i].end.slice(0,4)}, ${p.period}; ${kind==='gap'?'high-dimensional distance '+fmt(p.value):'display coordinates '+p.value.map(fmt).join(', ')}`;
      const g=add(s,'g',{'data-p-index':p.i,'data-country':c,role:'button',tabindex:-1,'aria-label':label,'aria-pressed':String(active.country===c && active.period===p.period)});
      add(g,'circle',{cx:x,cy:y,r:16,fill:'transparent',stroke:'none'});
      if(c==='USA')add(g,'rect',{x:x-radius,y:y-radius,width:radius*2,height:radius*2,fill:'white',stroke:COL[c],'stroke-width':2});
      else add(g,'circle',{cx:x,cy:y,r:radius,fill:COL[c],stroke:'white','stroke-width':1.5});
      if(active.period===p.period)add(g,'circle',{cx:x,cy:y,r:10,fill:'none',stroke:COL[c],'stroke-width':1.5});
      const tooltip=()=>{$('point-detail').textContent=label;};
      g.addEventListener('focus',tooltip);g.addEventListener('mouseenter',tooltip);
      g.addEventListener('click',()=>pick(c,p.period,kind));
      g.addEventListener('keydown',event=>{
        if(event.key==='Enter'||event.key===' '){event.preventDefault();pick(c,p.period,kind);}
        else if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End'].includes(event.key)){
          event.preventDefault();const all=[...s.querySelectorAll('[data-p-index]')],i=all.indexOf(g);
          const next=event.key==='Home'?0:event.key==='End'?all.length-1:(i+(['ArrowRight','ArrowDown'].includes(event.key)?1:-1)+all.length)%all.length;
          all.forEach(el=>el.setAttribute('tabindex','-1'));all[next].setAttribute('tabindex','0');all[next].focus();
        }
      });return g;
    }
    function rove(s) {
      const points=[...s.querySelectorAll('[data-p-index]')];
      const focus=points.find(p=>p.dataset.country===active.country && +p.dataset.pIndex===active.scene.model.periods.findIndex(p=>p.id===active.period)) || points[0];
      if(focus)focus.setAttribute('tabindex','0');
    }
    function pathPlot(kind) {
      const {model}=active.scene,host=$(kind);host.replaceChildren();
      if(model.display_space.state!=='ready') {host.textContent='Display withheld — '+reason(model.display_space.reason)+'. High-dimensional metrics below are unaffected.';return;}
      const width=Math.max(340,Math.min(480,host.clientWidth||480)),bound=radius(model),side=width-100,left=64,top=42;
      const X=x=>left+(x+bound)/(2*bound)*side,Y=y=>top+(bound-y)/(2*bound)*side;
      const s=svgRoot(kind,kind==='absolute'?'Absolute trajectories':'Trajectories centered on the contemporaneous US',
        'Fictional profiles. Fixed common axes with equal x and y units. Squares and dashed lines denote USA. Circles and solid lines denote the comparator. Arrow keys inspect points; Enter selects. Missing periods are not bridged.',width,side+110);
      s.dataset.radius=bound;
      add(s,'rect',{x:left,y:top,width:side,height:side,fill:'#fff',stroke:'#d9dee4'});
      for(let i=-2;i<=2;i++){
        const value=i*bound/2;
        add(s,'line',{x1:X(value),x2:X(value),y1:top,y2:top+side,stroke:value===0?'#aab3bd':'#e3e7ec'});
        add(s,'line',{x1:left,x2:left+side,y1:Y(value),y2:Y(value),stroke:value===0?'#aab3bd':'#e3e7ec'});
        add(s,'text',{x:X(value),y:top+side+24,'text-anchor':'middle',fill:'#344252','font-size':12},fmt(value));
        add(s,'text',{x:left-12,y:Y(value)+4,'text-anchor':'end',fill:'#344252','font-size':12},fmt(value));
      }
      add(s,'text',{x:left+side/2,y:side+94,'text-anchor':'middle','font-size':13,fill:'#344252'},kind==='absolute'?'Fixed display axis 1':'Country − USA · display axis 1');
      add(s,'text',{x:18,y:top+side/2,transform:`rotate(-90 18 ${top+side/2})`,'text-anchor':'middle','font-size':13,fill:'#344252'},kind==='absolute'?'Fixed display axis 2':'Country − USA · display axis 2');
      const defs=add(s,'defs');
      for(const c of [...new Set(['USA',active.country])]){
        const arr=add(defs,'marker',{id:kind+'-arrow-'+c,viewBox:'0 0 10 10',refX:8,refY:5,markerWidth:5,markerHeight:5,orient:'auto-start-reverse'});
        add(arr,'path',{d:'M 0 0 L 10 5 L 0 10 z',fill:COL[c]});
        const data=series(model,c,kind);
        if(kind==='relative' && c==='USA') {
          if(data.points.some(p=>p.ready)) {
            add(s,'rect',{x:X(0)-6,y:Y(0)-6,width:12,height:12,fill:'white',stroke:COL.USA,'stroke-width':2});
            add(s,'text',{x:X(0)+14,y:Y(0)+40,'font-size':12,fill:COL.USA},'USA origin');
          }
          continue;
        }
        for(const [a,b] of data.edges)add(s,'line',{'data-edge':`${c}:${a.period}:${b.period}`,x1:X(a.value[0]),y1:Y(a.value[1]),x2:X(b.value[0]),y2:Y(b.value[1]),
          stroke:COL[c],'stroke-width':2.5,'stroke-dasharray':c==='USA'?'7 5':'none','marker-end':`url(#${kind}-arrow-${c})`});
        const available=data.points.filter(p=>p.ready),first=available[0],last=available.at(-1);
        const coincident=first && last && first.value[0]===last.value[0] && first.value[1]===last.value[1];
        for(const p of available){
          marker(s,kind,c,p,X(p.value[0]),Y(p.value[1]));
          if(p===first || (p===last && !coincident)) {
            const years=p===first && coincident && first!==last?model.periods[first.i].end.slice(0,4)+'–'+model.periods[last.i].end.slice(0,4):model.periods[p.i].end.slice(0,4);
            add(s,'text',{x:X(p.value[0])+(c==='USA'?-12:12),y:Y(p.value[1])+(c==='USA'?-12:17),'text-anchor':c==='USA'?'end':'start','font-size':12,fill:COL[c]},c+' '+years);
          }
        }
      }
      if(!series(model,active.country,kind).points.some(p=>p.ready))add(s,'text',{x:left+side/2,y:25,'text-anchor':'middle','font-size':13,fill:'#684923'},'Comparator coordinates unavailable');
      rove(s);host.append(s);
    }
    function gapPlot() {
      const model=active.scene.model,host=$('gap');host.replaceChildren();
      const width=Math.max(340,Math.min(900,host.clientWidth||900));
      const s=svgRoot('gap','High-dimensional distance from the contemporaneous US',
        'Fictional values. Numeric elapsed time at period end. Zero-based distance axis. Gaps are not interpolated. The US self-distance is zero only when observed.',width,265);
      const times=elapsedPositions(model.periods),X=i=>56+times[i]*(width-90);
      const maximum=Math.max(1,...model.comparisons.filter(c=>c.distance!==null).map(c=>c.distance))*1.12;
      const Y=y=>211-y/maximum*170;
      s.dataset.maximum=maximum;
      for(let i=0;i<4;i++){const value=i*maximum/3;
        add(s,'line',{x1:56,x2:width-34,y1:Y(value),y2:Y(value),stroke:'#d9dee4'});
        add(s,'text',{x:44,y:Y(value)+4,'text-anchor':'end','font-size':12,fill:'#344252'},fmt(value));
      }
      add(s,'text',{x:56,y:19,'font-size':13,fill:'#344252'},'Euclidean distance · D = '+model.metric_space.dimension);
      for(let i=0;i<model.periods.length;i++)add(s,'text',{x:X(i),y:241,'text-anchor':'middle','font-size':12,fill:'#344252'},model.periods[i].end.slice(0,4));
      const selected=model.periods.findIndex(p=>p.id===active.period);
      add(s,'line',{x1:X(selected),x2:X(selected),y1:34,y2:214,stroke:'#65717e','stroke-dasharray':'3 5'});
      for(const c of [...new Set(['USA',active.country])]){
        const data=series(model,c,'gap');
        for(const [a,b] of data.edges)add(s,'line',{'data-edge':`${c}:${a.period}:${b.period}`,x1:X(a.i),y1:Y(a.value),x2:X(b.i),y2:Y(b.value),stroke:COL[c],'stroke-width':2.5,'stroke-dasharray':c==='USA'?'7 5':'none'});
        for(const p of data.points)if(p.ready)marker(s,'gap',c,p,X(p.i),Y(p.value));
      }
      rove(s);host.append(s);
    }
    function contributions() {
      const model=active.scene.model,host=$('contributions');host.replaceChildren();
      const t=model.transitions.find(t=>t.country_iso3===active.country && t.after===active.period);
      if(!t||t.state!=='ready'||t.metrics.decomposition_status!=='ready') {
        host.textContent=!t?'No preceding declared period.':t.state!=='ready'?'Contribution display withheld — adjacent endpoint unavailable.':'Contribution ratios undefined — both observed gaps are zero.';return;
      }
      const width=Math.max(340,Math.min(640,host.clientWidth||640)),zero=width*.54;
      const m=t.metrics,s=svgRoot('decomp','Algebraic contributions to the change in the gap',
        'These two signed algebraic contributions sum to the observed gap change. They are not causal effects.',width,168);
      const max=Math.max(Math.abs(m.gap_country_contribution),Math.abs(m.gap_us_contribution),0.1),X=v=>zero+v/max*width*.19;
      add(s,'line',{x1:zero,x2:zero,y1:16,y2:95,stroke:'#65717e'});
      for(const [i,label,v,c] of [[0,active.country+' movement',m.gap_country_contribution,COL[active.country]],[1,'USA movement',m.gap_us_contribution,COL.USA]]){
        const y=22+i*40;add(s,'text',{x:5,y:y+17,'font-size':14,fill:'#253548'},label);
        add(s,'rect',{x:Math.min(zero,X(v)),y,width:Math.abs(X(v)-zero),height:24,fill:c});
        add(s,'text',{x:width*.77,y:y+17,'font-size':14,fill:'#253548'},(v>=0?'+':'')+fmt(v));
      }
      add(s,'text',{x:5,y:124,'font-size':13,fill:'#253548'},`Gap change ${fmt(m.gap_change)} · algebraic, not causal`);
      add(s,'text',{x:5,y:149,'font-size':12,fill:'#253548'},'Reconciliation residual '+m.reconciliation_residual.toExponential(2));
      host.append(s);
    }
    function matrix() {
      const model=active.scene.model,host=$('matrix');host.replaceChildren();
      const table=doc.createElement('table');table.className='matrix';
      const max=Math.max(1,...model.comparisons.filter(c=>c.distance!==null).map(c=>c.distance));
      table.innerHTML='<caption>All declared countries × periods. Common scope and one shared US reference per period. Darker cells indicate larger observed gaps, not political judgments.</caption><thead><tr><th scope="col">Country</th>'+model.periods.map(p=>'<th scope="col">'+esc(p.end.slice(0,4))+'</th>').join('')+'</tr></thead>';
      const body=doc.createElement('tbody');
      for(const c of model.scope.countries){
        const tr=doc.createElement('tr'); const th=doc.createElement('th');th.scope='row';th.textContent=c+(c==='USA'?' · reference':'');tr.append(th);
        for(const p of model.periods){
          const r=row(model,c,p.id),cp=profile(model,c,p.id),up=profile(model,'USA',p.id),td=doc.createElement('td'),b=doc.createElement('button');
          b.type='button';b.dataset.country=c;b.dataset.period=p.id;b.dataset.state=r.state;
          const detail=r.state==='ready'?'distance '+fmt(r.distance):reason(r.reason)+'; country '+cp.state+'; USA '+up.state;
          b.setAttribute('aria-label',`${NAME[c]}, ${p.end.slice(0,4)}: ${detail}`);
          b.setAttribute('aria-pressed',String(c===active.country && p.id===active.period));
          if(r.state==='ready') {b.textContent=fmt(r.distance);b.style.backgroundColor=`hsl(194 35% ${97-r.distance/max*19}%)`;}
          else {b.textContent=cp.state==='failed'?'Failed':r.reason==='baseline_missing'?'No US':r.reason==='scope_incompatible'?'Scope gap':'Missing';b.className='unavailable';}
          b.addEventListener('click',()=>{pick(c,p.id);const fresh=[...$('matrix').querySelectorAll('button')].find(x=>x.dataset.country===c&&x.dataset.period===p.id);fresh?.focus();});
          td.append(b);tr.append(td);
        }body.append(tr);
      }table.append(body);host.append(table);
    }
    function evidence() {
      const model=active.scene.model,host=$('evidence');host.replaceChildren();
      for(const [heading,c] of [['Comparator sources',active.country],['US reference sources','USA']]){
        const p=profile(model,c,active.period),section=doc.createElement('section'),h=doc.createElement('h3');h.textContent=heading+' · '+c;section.append(h);
        const state=doc.createElement('p');state.textContent=`${p.state} · ${reason(p.reason)}. Inventory ${p.coverage.inventory}; eligible ${p.coverage.included}; excluded ${p.coverage.excluded}.`;section.append(state);
        const ph=doc.createElement('p');ph.className='hash';ph.textContent='Profile SHA256: '+p.sha256;section.append(ph);
        const records=model.evidence.filter(e=>e.country_iso3===c&&e.period===active.period);
        if(!records.length){const empty=doc.createElement('p');empty.textContent='No source observations in this declared cell.';section.append(empty);}
        for(const e of records){
          const detail=doc.createElement('details'),summary=doc.createElement('summary');
          const weight=p.contributions.find(x=>x.observation_id===e.id)?.weight;
          summary.textContent=e.genre+' · '+e.source_status+' · weight '+(weight===undefined?'not used':fmt(weight));detail.append(summary);
          const pre=doc.createElement('pre');pre.textContent=JSON.stringify({observation_id:e.id,date:e.date,actor_id:e.actor_id,speaker_id:e.speaker_id,
            speech_id:e.speech_id,capacity:e.capacity,attribution_status:e.attribution_status,review_receipt:e.review_receipt,
            source_status:e.source_status,missing_reason:e.missing_reason,meeting_id:e.meeting_id,source_family_id:e.source_family_id,
            source_sha256:e.source_sha256,text_sha256:e.text_sha256,parent_id:e.parent_id,parent_text_sha256:e.parent_text_sha256,
            original_code_point_offsets:[e.start,e.end],synthetic_pointer:e.source_pointer,weight:weight??null},null,2);detail.append(pre);section.append(detail);
        }host.append(section);
      }
    }
    function render() {
      const {scene,country,period}=active,model=scene.model,c=row(model,country,period),p=model.periods.find(p=>p.id===period);
      $('scenario-note').textContent=scene.note;
      $('point-detail').textContent='Focus a plotted point to inspect its values. Arrow keys move within a plot; Enter or Space selects it.';
      const fraction=c.display?.visible_squared_gap_fraction;
      $('summary').innerHTML=`<div><span>Selected comparator</span><strong>${esc(country)} · ${esc(p.end.slice(0,4))}</strong><small>${esc(p.start)} – ${esc(p.end)}</small></div><div><span>High-dimensional gap to USA</span><strong>${esc(fmt(c.distance))}</strong><small>${esc(c.state==='ready'?'Euclidean units · observed fictional profile':reason(c.reason))}</small></div><div><span>Squared gap visible in 2D</span><strong>${fraction===null||fraction===undefined?'Unavailable':fmt(100*fraction)+'%'}</strong><small>${c.distance===0?'Undefined at an observed zero gap':c.display?.state==='ready'?'The remaining gap lies outside the plane':'Display coordinates unavailable'}</small></div>`;
      pathPlot('absolute');pathPlot('relative');gapPlot();contributions();matrix();evidence();
      $('provenance').textContent=`Source-bound model SHA256: ${model.sha256}\nComparison set: ${model.identity.comparison_set_id}\nUS baseline: USA, contemporaneous; support: common; weights: ${model.scope.weight_policy}\nMetric: ${model.metric_space.dimension} dimensions; ${model.metric_space.space_kind}; ${model.metric_space.fingerprint}\nCatalogue SHA256: ${catalogue.sha256}\nSource/profile hashes establish synthetic consistency only. Uncertainty and sensitivity are withheld. Publication eligible: false.`;
    }
    function blobDownload(content,type,ext) {
      const blob=content instanceof Blob?content:new Blob([content],{type});
      const url=URL.createObjectURL(blob),link=doc.createElement('a');link.href=url;link.download='us-relative-synthetic.'+ext;
      doc.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);
    }
    function exportedSVG() {
      need(active,'No validated model');
      const out=doc.createElementNS(NS,'svg');out.setAttribute('xmlns',NS);out.setAttribute('viewBox','0 0 1000 940');out.setAttribute('width','1000');out.setAttribute('height','940');out.setAttribute('role','img');out.setAttribute('font-family','system-ui, sans-serif');out.setAttribute('aria-labelledby','export-title export-desc');
      add(out,'title',{id:'export-title'},'Synthetic US-relative trajectories — '+active.country);
      add(out,'desc',{id:'export-desc'},'Paired absolute and US-centered paths, high-dimensional gap series, and noncausal contributions. No real transcripts. Unavailable views remain withheld.');
      add(out,'rect',{width:1000,height:940,fill:'#ffffff'});
      add(out,'text',{x:28,y:32,fill:'#23344a','font-family':'Arial, sans-serif','font-size':20},'US-relative trajectories · SYNTHETIC ONLY · '+active.country);
      add(out,'text',{x:28,y:58,fill:'#344252','font-family':'Arial, sans-serif','font-size':12},active.scene.title+' · selected '+active.period+' · uncertainty withheld; publication ineligible');
      add(out,'text',{x:35,y:82,'font-size':15,fill:'#23344a'},'Absolute trajectories');
      add(out,'text',{x:535,y:82,'font-size':15,fill:'#23344a'},'US-centered trajectories');
      const layout=[['absolute',10,85,480,458],['relative',510,85,480,458],['gap',22,535,956,280],['contributions',22,785,640,152]];
      for(const [id,x,y,w,h] of layout){
        const original=$(id).querySelector('svg');
        if(original){const clone=original.cloneNode(true);clone.setAttribute('x',x);clone.setAttribute('y',y);clone.setAttribute('width',w);clone.setAttribute('height',h);
          for(const el of clone.querySelectorAll('[role="button"]')){el.removeAttribute('tabindex');el.removeAttribute('role');el.removeAttribute('aria-pressed');}
          out.append(clone);
        }else add(out,'text',{x:x+20,y:y+40,'font-size':13,fill:'#684923'},id+': withheld / unavailable');
      }
      add(out,'text',{x:680,y:834,'font-size':12,fill:'#344252'},'Algebraic contributions, not causal effects.');
      add(out,'text',{x:680,y:858,'font-size':12,fill:'#344252'},'Missing periods are never bridged.');
      add(out,'metadata',{},JSON.stringify({replay:selection(),model_sha256:active.scene.model.sha256,split:'synthetic',publication_eligible:false}));
      return new XMLSerializer().serializeToString(out);
    }
    async function exportAs(format) {
      if(!active)return;const ticket=generation;
      if(format==='json')blobDownload(JSON.stringify(selection(),null,2)+'\n','application/json','json');
      else if(format==='csv')blobDownload(csv(active.scene.model),'text/csv;charset=utf-8','csv');
      else if(format==='html') {
        const page=new DOMParser().parseFromString(originalHTML,'text/html');page.documentElement.dataset.initialReplay=JSON.stringify(selection());
        blobDownload('<!doctype html>\n'+page.documentElement.outerHTML,'text/html;charset=utf-8','html');
      }else if(format==='svg')blobDownload(exportedSVG(),'image/svg+xml','svg');
      else if(format==='png'){
        const src=URL.createObjectURL(new Blob([exportedSVG()],{type:'image/svg+xml'}));
        try {
          const img=new Image();await new Promise((resolve,reject)=>{img.onload=resolve;img.onerror=reject;img.src=src;});
          if(ticket!==generation || !active)return;
          const canvas=doc.createElement('canvas');canvas.width=2000;canvas.height=1880;
          const ctx=canvas.getContext('2d');need(ctx,'Canvas unavailable');ctx.drawImage(img,0,0,2000,1880);
          const b=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));
          if(ticket===generation && active){need(b,'PNG export failed');blobDownload(b,'image/png','png');}
        }finally{URL.revokeObjectURL(src);}
      }
    }
    async function importFile(file) {
      const ticket=++generation;clear('loading','Validating local replay…');
      try{
        need(file && file.size<=8192,'Replay size limit');const value=JSON.parse(await file.text());
        if(ticket!==generation)return;
        const accepted=validateReplay(value,catalogue);choose(accepted.scene_id,accepted.country_iso3,accepted.period);
      }catch{if(ticket===generation)clear('failed','Replay rejected. Charts, source details and exports were cleared. Only matching bundled synthetic replays are accepted.');}
    }
    $('scenario').replaceChildren(...catalogue.scenes.map(s=>new Option(s.title,s.id)));
    $('scenario').addEventListener('change',()=>choose($('scenario').value));
    $('country').addEventListener('change',()=>{if(active)pick($('country').value,active.period);});
    $('period').addEventListener('change',()=>{if(active)pick(active.country,$('period').value);});
    $('replay-file').addEventListener('change',e=>{const file=e.target.files[0];e.target.value='';if(file)importFile(file);});
    $('cancel').addEventListener('click',()=>{generation++;clear('cancelled','Cancelled. No previous charts or exports remain. Select a scenario to resume.');});
    $('reset').addEventListener('click',()=>choose('moving'));
    for(const b of doc.querySelectorAll('[data-export]'))b.addEventListener('click',()=>exportAs(b.dataset.export).catch(()=>status('Export failed; no fallback file was emitted.','failed')));
    doc.defaultView.addEventListener('resize',()=>{if(active)render();});
    try{
      if(doc.documentElement.dataset.initialReplay){const r=validateReplay(JSON.parse(doc.documentElement.dataset.initialReplay),catalogue);choose(r.scene_id,r.country_iso3,r.period);}
      else choose('moving');
    }catch{clear('failed','Initial replay rejected. Select a bundled scenario to resume.');}
    // Narrow hooks support deterministic race tests; no model-input setter exists.
    return {importFile,cancel:()=>{generation++;clear('cancelled','Cancelled.');},getReplay:()=>selection()};
  }
  return {radius,series,elapsedPositions,replay,validateReplay,csv,mount};
});
