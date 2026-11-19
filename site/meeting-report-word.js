/* Native editable Word report, built locally from the complete report renderer. */
(function(root){
  'use strict';
  const encoder=new TextEncoder(),W='http://schemas.openxmlformats.org/wordprocessingml/2006/main';
  const xml=value=>String(value).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  const declaration='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>';
  function build(report){return render(root.UNMeetingReport.reportHTML(report));}
  async function buildDraft(report,draft,policy){
    await root.UNReportDraft.open(draft,report,policy);
    return render(root.UNMeetingReport.reportHTML(report)+root.UNReportDraft.reviewHTML(draft,report), 'Editable unreviewed draft copy. Keep original report JSON and returned draft JSON separately to reopen work. Word edits cannot be imported into the reporting workspace.');
  }
  function render(html,notice='Editable reading copy. Save report JSON or its ZIP package to reopen source-verified work in the reporting workspace.'){
    const Core=root.UNMeetingReport;
    if(encoder.encode(html).length>Core.LIMIT)throw Error('Word report exceeds 25 MB. Choose fewer meetings. Current work has not changed.');
    // Refuse unsupported XML characters rather than silently changing source text.
    for(const c of html){const n=c.codePointAt(0);if(!(n===9||n===10||n===13||(n>=32&&n<=0xd7ff)||(n>=0xe000&&n<=0xfffd)||n>=0x10000))throw Error('Word cannot preserve an unsupported control character in this report. Use JSON to retain exact source text.');}
    const document=new DOMParser().parseFromString(html,'text/html'),relationships=[],bookmarks=new Map(),lists=[];
    for(const node of document.querySelectorAll('[id]'))if(!bookmarks.has(node.id))bookmarks.set(node.id,{name:'meeting_'+bookmarks.size,id:bookmarks.size});
    const run=(text,format={})=>{
      const properties=(format.link?'<w:rStyle w:val="Hyperlink"/>':'')+(format.bold?'<w:b/>':'')+(format.italic?'<w:i/>':'');
      return String(text).split(/(\r\n|\r|\n|\t)/).map(part=>part==='\t'?'<w:r><w:tab/></w:r>':/^[\r\n]+$/.test(part)?'<w:r><w:br/></w:r>':'<w:r>'+(properties?'<w:rPr>'+properties+'</w:rPr>':'')+'<w:t xml:space="preserve">'+xml(part)+'</w:t></w:r>').join('');
    };
    function inline(node,format={}){
      if(node.nodeType===3)return run(node.nodeValue,format);
      if(node.nodeType!==1)return '';
      const tag=node.tagName;
      if(tag==='BR')return '<w:r><w:br/></w:r>';
      if(tag==='HR')return run(' — ',format);
      const next={...format,bold:format.bold||tag==='STRONG'||tag==='B',italic:format.italic||tag==='EM'||tag==='I'};
      if(tag==='A'){
        const href=node.getAttribute('href')||'',target=bookmarks.get(href.slice(1));
        if(href.startsWith('#')&&target)return '<w:hyperlink w:anchor="'+target.name+'">'+children(node,{...next,link:true})+'</w:hyperlink>';
        if(/^https:\/\//i.test(href)){
          const id='source_'+relationships.length;relationships.push({id,target:href});
          return '<w:hyperlink r:id="'+id+'">'+children(node,{...next,link:true})+'</w:hyperlink>';
        }
      }
      return (tag==='SPAN'&&node.parentElement?.tagName==='LI'?'<w:r><w:br/></w:r>':'')+children(node,next);
    }
    const children=(node,format)=>[...node.childNodes].map(n=>inline(n,format)).join('');
    function paragraph(node,style='',number=null,format={}){
      const mark=bookmarks.get(node.id),props=(style?'<w:pStyle w:val="'+style+'"/>':'')+(number?'<w:numPr><w:ilvl w:val="'+number.level+'"/><w:numId w:val="'+number.id+'"/></w:numPr>':'');
      return '<w:p>'+(props?'<w:pPr>'+props+'</w:pPr>':'')+(mark?'<w:bookmarkStart w:id="'+mark.id+'" w:name="'+mark.name+'"/>':'')+children(node,format)+(mark?'<w:bookmarkEnd w:id="'+mark.id+'"/>':'')+'</w:p>';
    }
    function list(node,level){
      const id=lists.length+1;lists.push({id,ordered:node.tagName==='OL'});
      return [...node.children].map(li=>{
        const copy=li.cloneNode(true);for(const nested of copy.querySelectorAll('ul,ol'))nested.remove();
        return paragraph(copy,'',{id,level:Math.min(level,8)})+[...li.children].filter(c=>['UL','OL'].includes(c.tagName)).map(c=>list(c,level+1)).join('');
      }).join('');
    }
    function blocks(node,level=0){
      return [...node.childNodes].map(n=>{
        if(n.nodeType===3)return n.nodeValue.trim()?'<w:p>'+run(n.nodeValue)+'</w:p>':'';
        if(n.nodeType!==1)return '';
        const tag=n.tagName;
        if(/^H[1-6]$/.test(tag))return paragraph(n,'Heading'+tag.slice(1));
        if(['P','SUMMARY','BLOCKQUOTE'].includes(tag))return paragraph(n,tag==='BLOCKQUOTE'?'Quote':'');
        if(tag==='TABLE'){
          const rows=[...n.rows],columns=Math.max(1,...rows.map(r=>r.cells.length)),width=Math.floor(10080/columns);
          return '<w:tbl><w:tblPr><w:tblStyle w:val="EvidenceTable"/><w:tblW w:w="10080" w:type="dxa"/><w:tblLayout w:type="fixed"/></w:tblPr><w:tblGrid>'+Array(columns).fill('<w:gridCol w:w="'+width+'"/>').join('')+'</w:tblGrid>'+rows.map(row=>'<w:tr>'+(row.parentElement.tagName==='THEAD'?'<w:trPr><w:tblHeader/></w:trPr>':'')+[...row.cells].map(cell=>'<w:tc><w:tcPr><w:tcW w:w="'+width+'" w:type="dxa"/></w:tcPr>'+paragraph(cell,'',null,{bold:cell.tagName==='TH'})+'</w:tc>').join('')+'</w:tr>').join('')+'</w:tbl>';
        }
        if(tag==='UL'||tag==='OL')return list(n,level);
        return blocks(n,level);
      }).join('');
    }
    const body=blocks(document.body)+'<w:p>'+run(notice)+'</w:p>';
    const documentXML='<w:document xmlns:w="'+W+'" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><w:body>'+body+'<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1080" w:right="1080" w:bottom="1080" w:left="1080"/></w:sectPr></w:body></w:document>';
    const styles='<w:styles xmlns:w="'+W+'"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/><w:lang w:val="en-US"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="120"/></w:pPr></w:pPrDefault></w:docDefaults><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'+Array.from({length:6},(_,i)=>'<w:style w:type="paragraph" w:styleId="Heading'+(i+1)+'"><w:name w:val="heading '+(i+1)+'"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="200" w:after="120"/><w:outlineLvl w:val="'+i+'"/></w:pPr><w:rPr><w:b/><w:color w:val="002D74"/><w:sz w:val="'+[32,28,24,22,22,22][i]+'"/></w:rPr></w:style>').join('')+'<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/><w:basedOn w:val="Normal"/><w:pPr><w:pBdr><w:left w:val="single" w:sz="12" w:color="002D74" w:space="8"/></w:pBdr><w:ind w:left="240"/></w:pPr></w:style><w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/><w:rPr><w:color w:val="002D74"/><w:u w:val="single"/></w:rPr></w:style><w:style w:type="table" w:styleId="EvidenceTable"><w:name w:val="Evidence table"/><w:tblPr><w:tblBorders>'+['top','left','bottom','right','insideH','insideV'].map(side=>'<w:'+side+' w:val="single" w:sz="4" w:color="B8C5D3"/>').join('')+'</w:tblBorders><w:tblCellMar><w:top w:w="90" w:type="dxa"/><w:left w:w="90" w:type="dxa"/><w:bottom w:w="90" w:type="dxa"/><w:right w:w="90" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style></w:styles>';
    const numbering='<w:numbering xmlns:w="'+W+'">'+[false,true].map((ordered,id)=>'<w:abstractNum w:abstractNumId="'+id+'">'+Array.from({length:9},(_,i)=>'<w:lvl w:ilvl="'+i+'"><w:start w:val="1"/><w:numFmt w:val="'+(ordered?'decimal':'bullet')+'"/><w:lvlText w:val="'+(ordered?'%'+(i+1)+'.':'•')+'"/><w:pPr><w:ind w:left="'+(360*(i+1))+'" w:hanging="180"/></w:pPr></w:lvl>').join('')+'</w:abstractNum>').join('')+lists.map(l=>'<w:num w:numId="'+l.id+'"><w:abstractNumId w:val="'+Number(l.ordered)+'"/></w:num>').join('')+'</w:numbering>';
    const relations=entries=>'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+entries+'</Relationships>';
    const relation=(id,type,target,external=false)=>'<Relationship Id="'+id+'" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'+type+'" Target="'+xml(target)+'"'+(external?' TargetMode="External"':'')+'/>';
    const types='<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/></Types>';
    const files=[['[Content_Types].xml',types],['_rels/.rels',relations(relation('office','officeDocument','word/document.xml'))],['word/document.xml',documentXML],['word/styles.xml',styles],['word/numbering.xml',numbering],['word/_rels/document.xml.rels',relations(relation('styles','styles','styles.xml')+relation('numbering','numbering','numbering.xml')+relationships.map(r=>relation(r.id,'hyperlink',r.target,true)).join(''))]];
    return root.UNMeetingReportPackage.zip(files.map(([name,text])=>({name,bytes:encoder.encode(declaration+text)})),'Word report');
  }
  root.UNMeetingReportWord={build,buildDraft};
})(globalThis);
