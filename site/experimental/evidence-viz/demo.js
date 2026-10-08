/* Offline synthetic-only demonstration. */
(function () {
  'use strict';
  const data=UNEvidenceFixture.fixture();
  const target=document.getElementById('ev-panels');
  const status=document.getElementById('ev-status');
  const selector=document.getElementById('scenario');
  let views=[];

  function exportFile(name,body,mime){
    const url=URL.createObjectURL(new Blob([body],{type:mime}));
    const link=document.createElement('a');
    link.href=url;
    link.download=name;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(()=>URL.revokeObjectURL(url),1000);
  }

  function draw(){
    const mode=selector.value;
    const source=mode==='empty'?UNEvidenceFixture.scenario('consensus','empty'):data;
    const panels=mode==='normal'?data.panels:mode==='empty'?[
      source.panels[0],...['country-theme','network','longitudinal'].map(k=>UNEvidenceFixture.scenario(k,'empty').panels[0])
    ]:data.panels.map(p=>({
      ...p,status:mode,
      reason:mode==='empty'?'No eligible observations in the source selection':
        mode==='withheld'?'Upstream statistical evidence not approved':
        'Upstream calculation failed',
      coverage:{...p.coverage,included:0}
    }));
    try {
      views=UNEvidenceViz.mount(target,source.envelope,panels);
      for(const section of target.querySelectorAll('.ev-panel')){
        const box=document.createElement('div');
        box.className='ev-panel-actions';
        const kind=section.dataset.evKind;
        box.innerHTML='<button type="button" data-export="svg" data-kind="'+kind+
          '">Export SVG</button><button type="button" data-export="html" data-kind="'+kind+
          '">Export static HTML</button>';
        section.querySelector('.ev-panel-head').after(box);
      }
      status.textContent=views.length+' synthetic visualizations displayed: '+mode+'.';
    }catch(error){
      target.replaceChildren();
      status.textContent='Evidence rejected: '+error.message;
    }
  }

  target.addEventListener('click',event=>{
    const button=event.target.closest('[data-export]');
    if(!button)return;
    const view=views.find(v=>v.kind===button.dataset.kind);
    if(!view)return;
    if(button.dataset.export==='svg'){
      exportFile(view.kind+'.svg',view.svg,'image/svg+xml;charset=utf-8');
    }else{
      exportFile(view.kind+'.html',UNEvidenceViz.htmlDocument(view),'text/html;charset=utf-8');
    }
  });
  selector.addEventListener('change',draw);
  draw();
})();
