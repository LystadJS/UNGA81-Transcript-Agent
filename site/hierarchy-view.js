/* Source-linked hierarchy, preserved as SVG in the script-free HTML report. */
(function(root){
  'use strict';
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function diagram(fit,records,compact,small=false){
    const h=fit.hierarchical,n=fit.points.length,byId=new Map(records.map(r=>[r.id,r]));
    const cuts=new Map(h.cut_nodes.map((id,i)=>[id,fit.clusters[i]]));
    const position=new Map(),leaves=[],paths=[],max=h.merges.at(-1).height||1;
    const width=small?365:1030,edge=small?155:540,labelX=small?175:570;
    const x=value=>edge-value/max*(small?140:500);
    function visit(node){
      const merge=node>=n?h.merges[node-n]:null,group=compact?cuts.get(node):null;
      if(group||!merge){
        const point=group?fit.points.find(p=>p.id===group.representative_id):fit.points[node];
        const source=byId.get(point.id),y=55+leaves.length*(compact?54:20),px=compact&&merge?x(merge.height):edge;
        const label=group?`Cluster ${group.cluster} · ${group.size} passages`:`${source.country} · ${point.id}`;
        const title=group?`Cluster ${group.cluster}; nearest-to-centroid example: ${source.country} · ${source.date}`:`${source.country} · ${source.date} · cluster ${point.cluster} · ${point.id}`;
        leaves.push(`<a href="${esc(source.source_url)}" target="_blank" rel="noopener noreferrer" aria-label="${esc(title)}"><path d="M ${px} ${y} H ${labelX-10}" stroke="#c7d3de" stroke-dasharray="2 3"/><circle cx="${px}" cy="${y}" r="4" fill="${root.UNClusterView.colors[point.cluster-1]}"/><text x="${labelX}" y="${y+4}" font-size="12" fill="#002d74">${esc(label.length>62?label.slice(0,59)+'…':label)}</text><title>${esc(title+'\n'+source.text.slice(0,220))}</title></a>`);
        position.set(node,{x:px,y});return;
      }
      visit(merge.left);visit(merge.right);
      const a=position.get(merge.left),b=position.get(merge.right),px=x(merge.height),y=(a.y+b.y)/2;
      paths.push(`<path d="M ${a.x} ${a.y} H ${px} V ${b.y} H ${b.x}" fill="none" stroke="#536477" stroke-width="1.4"><title>${esc('Merge '+merge.node+' · height '+merge.height.toFixed(5)+' · '+merge.size+' passages')}</title></path>`);
      position.set(node,{x:px,y});
    }
    visit(2*n-2);
    const height=85+(leaves.length-1)*(compact?54:20);
    return `<div class="hierarchy-map${compact?(small?' hierarchy-small':' hierarchy-wide'):' hierarchy-full'}" tabindex="0" role="region" aria-label="${compact?'Cluster overview dendrogram':'Full passage dendrogram, scroll to inspect'}"><svg viewBox="0 0 ${width} ${height}" role="group" aria-label="${esc(h.linkage)} dendrogram"><title>${compact?'Hierarchy above the selected k groups':'Complete passage hierarchy'} · ${esc(h.linkage)} linkage</title>
      <text x="${small?15:40}" y="16" font-size="12">Merge height</text>${(small?[0,.5,1]:[0,.25,.5,.75,1]).map(t=>`<text x="${x(t*max)}" y="34" text-anchor="middle" font-size="11">${(t*max).toFixed(2)}</text>`).join('')}
      ${paths.join('')}${leaves.join('')}</svg></div>`;
  }
  function render(fit,records,table){
    const h=fit.hierarchical;
    return `<section class="hierarchy-section"><h4>How the groups merge</h4>
      <p class="method-note">The overview stops at the selected ${h.k} groups. Branch positions show merge height; vertical order is for reading. Select a group to inspect its nearest-to-centroid source example.</p>
      ${h.tied_cut?'<p class="warning">The selected cut crosses tied merge heights. Row order resolves ties; a height threshold alone would not produce this exact number of groups.</p>':''}
      ${diagram(fit,records,true)}${diagram(fit,records,true,true)}
      <details><summary>Full passage dendrogram</summary><p class="method-note">Every included passage appears once. Scroll to read the leaves and open their sources. This ordering does not establish political alignment.</p>${diagram(fit,records,false)}</details>
      <details><summary>Hierarchy record</summary><p class="method-note">${esc(h.height_definition)}. Leaves use indexes 0–${fit.points.length-1} in point order; subsequent indexes identify merges. Download Hierarchy CSV for all merges and leaf identifiers.</p>
      ${table(['Node','Left child','Right child','Height','Passages'],h.merges.map(m=>[m.node,m.left,m.right,m.height.toFixed(6),m.size]))}</details></section>`;
  }
  root.UNHierarchyView={render,diagram};
})(globalThis);
