# Keep internal sentence locators in the audit, not in reader-facing notes.
reader_source_note <- function(x) {
  x <- gsub("\\bat S[0-9]{3,}(?:[-–—]S[0-9]{3,})?\\b", "in the source text", x, perl=TRUE)
  sub("^S[0-9]{3,}(?= (?:calls|gives|states|reports|says)\\b)", "The source text", x, perl=TRUE)
}
# Outlook-safe HTML and RFC MIME serialization. No Outlook automation or Python needed.
html_escape <- function(x) {
  x<-visible(x);for(k in c("&","<",">",'"',"'"))x<-gsub(k,switch(k,'&'="&amp;",'<'="&lt;",'>'="&gt;",'"'="&quot;","'"="&#39;"),x,fixed=TRUE)
  x
}
p_html <- function(text,size=14) sprintf('<div style="font-family:Arial,Helvetica,sans-serif;font-size:%dpx;line-height:%dpx;color:#202B38;margin:0 0 9px 0;">%s</div>',size,ceiling(size*1.5),text)
section_html <- function(title) sprintf('<div style="font-family:Arial,Helvetica,sans-serif;font-size:11px;line-height:16px;font-weight:bold;color:#002D74;letter-spacing:.3px;border-bottom:1px solid #D6DEE7;padding:0 0 4px 0;margin:20px 0 8px 0;">%s</div>',html_escape(title))
bullets_html <- function(bullets) paste0('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;">',paste(vapply(bullets,function(b)sprintf('<tr><td width="18" valign="top" style="width:18px;padding:0 0 7px 0;font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:20px;color:#002D74;">&#8226;</td><td valign="top" style="padding:0 0 7px 0;font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:20px;color:#202B38;"><strong>%s.</strong> %s</td></tr>',html_escape(sub("[.]$","",b$label)),html_escape(b$text)),character(1)),collapse="\n"),'</table>')
meta_html <- function(items,cls="meta") {
  cells<-vapply(names(items),function(k)sprintf('<td class="%s" width="25%%" valign="top" style="width:25%%;padding:7px 9px;border-right:1px solid #D6DEE7;"><div style="font-family:Arial,Helvetica,sans-serif;font-size:9px;line-height:12px;font-weight:bold;color:#002D74;">%s</div><div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;line-height:17px;color:#202B38;">%s</div></td>',cls,html_escape(k),html_escape(if(nzchar(str1(items[[k]])))items[[k]] else "Not provided")),character(1))
  paste0('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;background:#F6F8FA;border-top:1px solid #D6DEE7;border-bottom:1px solid #D6DEE7;margin:0 0 10px 0;"><tr>',paste(cells,collapse=""),'</tr></table>')
}
FIGURE_FILES<-c("Figure_1_Issue_Frequency.png","Figure_2_Regional_Issue_Heatmap.png","Figure_3_Issue_Cooccurrence_Network.png")
FIGURE_TITLES<-c("Issues raised across national statements","Regional issue emphasis","Issue co-occurrence across speeches")
FIGURE_NOTES<-c("Fixed topics lead in the order Iran, Cuba, Ukraine, AI; remaining issues are sorted by frequency. Categories overlap; unresolved decisions are not silently coded absent.","Cells show countries coded present divided by the full regional sample. An asterisk marks unresolved decisions. These daily samples are not representative regional estimates.","Node area reflects issue frequency. Links show Jaccard overlap only for topic pairs fully coded across the corpus, subject to the printed thresholds. Unresolved topics can remain isolated. Co-occurrence is not agreement or causation; broad/narrow category overlap is partly definitional.")
english_date <- function(day) {d<-as.Date(day);sprintf("%d %s %s",as.integer(format(d,"%d")),month.name[as.integer(format(d,"%m"))],format(d,"%Y"))}
fold_base64 <- function(raw) {x<-b64(raw);if(!nzchar(x))return("");start<-seq.int(1,nchar(x),76);paste(substring(x,start,pmin(start+75,nchar(x))),collapse="\r\n")}
header_text <- function(x) {
  x<-visible(x);assert(length(x)==1&&!grepl("[\r\n]",x),"Header injection rejected")
  # Fold UTF-8 encoded words on character boundaries rather than splitting bytes.
  chars<-strsplit(x,"",fixed=TRUE)[[1]];chunks<-character();chunk<-""
  for(ch in chars){if(nchar(paste0(chunk,ch),type="bytes")>36&&nzchar(chunk)){chunks<-c(chunks,chunk);chunk<-""};chunk<-paste0(chunk,ch)}
  if(nzchar(chunk))chunks<-c(chunks,chunk)
  paste(vapply(chunks,function(s)paste0("=?UTF-8?B?",b64(charToRaw(enc2utf8(s))),"?="),character(1)),collapse="\r\n ")
}
validate_address <- function(x) {
  assert(length(x)==1&&is.character(x)&&grepl("^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(\\.[A-Za-z0-9-]+)+$",x)&&!grepl("[\r\n]",x),"Use a valid plain email address without placeholders/display-name syntax")
  x
}
rfc_date <- function(stamp) {
  d<-as.POSIXct(stamp,format="%Y-%m-%dT%H:%M:%S",tz="UTC");assert(!is.na(d),"Invalid preparation timestamp")
  lt<-as.POSIXlt(d,tz="UTC");sprintf("%s, %02d %s %04d %02d:%02d:%02d +0000",c("Sun","Mon","Tue","Wed","Thu","Fri","Sat")[lt$wday+1],lt$mday,month.abb[lt$mon+1],lt$year+1900,lt$hour,lt$min,as.integer(lt$sec))
}
assemble_mime <- function(plain,html,images,subject,prepared_at,status,from="",to=list()) {
  content_key<-sha_text(paste0(plain,html));b1<-paste0("UNBRIEF_",substr(content_key,1,24),"_alt");b2<-paste0("UNBRIEF_",substr(content_key,1,24),"_rel")
  headers<-c(paste0("Subject: ",header_text(subject)),paste0("Date: ",rfc_date(prepared_at)),paste0("Message-ID: <",substr(content_key,1,32),"@unbrief.local>"),"X-Unsent: 1",paste0("X-UNBrief-Status: ",status),"MIME-Version: 1.0")
  if(nzchar(from))headers<-c(headers,paste0("From: ",validate_address(from)))
  if(length(to))headers<-c(headers,paste0("To: ",paste(vapply(to,validate_address,character(1)),collapse=",\r\n ")))
  headers<-c(headers,paste0('Content-Type: multipart/alternative; boundary="',b1,'"'))
  lines<-c(headers,"",paste0("--",b1),'Content-Type: text/plain; charset="utf-8"',"Content-Transfer-Encoding: base64","",fold_base64(charToRaw(enc2utf8(plain))),paste0("--",b1),paste0('Content-Type: multipart/related; type="text/html"; boundary="',b2,'"'),"",paste0("--",b2),'Content-Type: text/html; charset="utf-8"',"Content-Transfer-Encoding: base64","",fold_base64(charToRaw(enc2utf8(html))))
  for(im in images) {
    assert(grepl("^[A-Za-z0-9_.-]+$",im$name)&&grepl("^[A-Za-z0-9@_.-]+$",im$cid),"Unsafe MIME filename/CID")
    lines<-c(lines,paste0("--",b2),paste0('Content-Type: image/png; name="',im$name,'"'),"Content-Transfer-Encoding: base64",paste0("Content-ID: <",im$cid,">"),paste0('Content-Disposition: inline; filename="',im$name,'"'),"",fold_base64(im$bytes))
  }
  charToRaw(enc2utf8(paste(c(lines,paste0("--",b2,"--"),paste0("--",b1,"--"),""),collapse="\r\n")))
}
build_email <- function(root,run,cfg) {
  cp<-readRDS(file.path(run,"checkpoint.rds"));brief<-cp$brief;speeches<-cp$speeches;analyses<-cp$analyses
  speeches<-order_country_readouts(speeches,cfg)
  n<-length(speeches);date<-english_date(brief$date);status<-switch(brief$status,REPLAY="Archived replay / non-final",REVIEW_REQUIRED="Review required / non-final",AUTOMATED_CHECKS_PASSED="Automated checks passed / non-final",EMPTY="No qualifying text retrieved")
  rendered<-d1_render_packets(cp,run,cfg)
  takeaway<-if(n) paste0("This readout contains ",n," country summaries, grouped by region. All five analytical sections are retained; each numerical display appears only when its source and quality checks pass.") else "No qualifying country text was retrieved for this date; this does not establish that no meetings or speeches took place. All five analytical sections retain their unavailable states."
  if(brief$source=="replay")takeaway<-paste(takeaway,"This archived replay preserves inherited summaries and is not a fresh semantic review.")
  else if(brief$analysis_mode=="extractive")takeaway<-paste(takeaway,"Country points are source excerpts, not independently reviewed narrative summaries.")
  parts<-c(read_text(file.path(root,"templates/email_head.html")),section_html(toupper(cfg$scope_label)),sprintf('<div style="font-family:Georgia,serif;font-size:30px;line-height:34px;font-weight:bold;color:#062135;margin:0;">%s</div>',html_escape(date)),'<div style="height:2px;line-height:2px;background:#002D74;margin:7px 0 9px 0;">&nbsp;</div>',p_html("Country entries are grouped by region and alphabetized within each region. Evidence and detailed audit information are retained separately.",11),meta_html(list(COVERAGE=paste(n,"countries"),`SPEECH DATE`=date,PREPARED=substr(brief$prepared_at,1,10),STATUS=status)))
  if(brief$status=="REVIEW_REQUIRED")parts<-c(parts,p_html(sprintf("<strong>Coverage and review note.</strong> Automated checks require review before distribution. %d collection or analysis problem(s) are recorded in the audit.",length(brief$collection$errors)),12))
  parts<-c(parts,paste0('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;margin:0 0 14px 0;"><tr><td width="5" style="width:5px;background:#002D74;font-size:1px;line-height:1px;">&nbsp;</td><td style="background:#E7F1F8;padding:10px 12px;"><div style="font-size:10px;line-height:14px;font-weight:bold;color:#002D74;margin-bottom:4px;">EXECUTIVE TAKEAWAY</div>',p_html(html_escape(takeaway)),'</td></tr></table>'))
  parts<-c(parts,rendered$html,section_html("Country readouts | by region, then alphabetical"))
  plain<-c(cfg$email$brand_name,cfg$scope_label,date,paste("STATUS:",status),paste("COVERAGE:",n,"countries"),"","EXECUTIVE TAKEAWAY",takeaway,"",rendered$plain,"COUNTRY READOUTS | BY REGION, THEN ALPHABETICAL","")
  previous_region<-""
  for(s in speeches) {
    if(!identical(previous_region,s$region)) {
      region_n<-sum(vapply(speeches,function(x)identical(x$region,s$region),logical(1)))
      parts<-c(parts,region_heading_html(s$region,region_n))
      plain<-c(plain,paste0("=== ",toupper(s$region)," | ",region_n," ",if(region_n==1)"COUNTRY" else "COUNTRIES"," ==="),"")
      previous_region<-s$region
    }
    a<-analyses[[s$iso3]];flags<-reader_source_note(unique(c(unlist(s$flags),unlist(a$flags))))
    parts<-c(parts,sprintf('<table class="country-section" role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0" style="width:100%%;margin:0 0 18px 0;"><tr><td style="border-top:2px solid #002D74;padding-top:12px;"><div class="country-title" style="font-family:Georgia,serif;font-size:21px;line-height:26px;font-weight:bold;color:#062135;margin:0 0 7px 0;">%s</div>',html_escape(s$country)),meta_html(list(SPEAKER=s$speaker,TITLE=s$title,DATE=date,REGION=s$region),"country-meta-cell"))
    if(length(flags))parts<-c(parts,p_html(paste0("<strong>Source / review note.</strong> ",html_escape(paste(flags,collapse=" "))),11))
    if(a$verification$status=="extractive_provisional")parts<-c(parts,p_html("The following points are verbatim source excerpts, not independently worded summaries.",11))
    if(a$verification$status=="failed")parts<-c(parts,p_html("The full text is archived, but no summary passed automated checks.",12)) else parts<-c(parts,bullets_html(a$bullets))
    if(nzchar(s$source_url))parts<-c(parts,p_html(sprintf('<a href="%s" style="color:#002D74;">Read the source transcript</a>',html_escape(source_url(s$source_url))),11))
    parts<-c(parts,"</td></tr></table>")
    plain<-c(plain,toupper(s$country),paste("Speaker:",s$speaker,"| Title:",s$title),paste("Date:",date,"| Region:",s$region),if(length(flags))paste("Source/review note:",flags),vapply(a$bullets,function(b)paste0("- ",b$label,". ",b$text),character(1)),if(nzchar(s$source_url))paste("Source:",s$source_url),"")
  }
  parts<-c(parts,section_html("Sources and method"),p_html(html_escape(brief$collection$coverage_note),11),p_html("Regional categories are analytical display groups, not UN electoral groups. Topic codes measure presence, not sentiment or support. The fixed topics Iran, Cuba, Ukraine and AI remain visible; assessments are withheld until a producer is released. Their order is a fixed display convention. Evidence quotations and review details remain in the accompanying audit.",11))
  if(nzchar(str1(brief$collection$coding_note)))parts<-c(parts,p_html(html_escape(brief$collection$coding_note),11))
  parts<-c(parts,'</td></tr><tr><td class="pad" style="padding:12px 44px;border-top:1px solid #D6DEE7;background:#F6F8FA;font-family:Arial,Helvetica,sans-serif;font-size:10px;line-height:15px;color:#667085;">U.S. Mission to the United Nations | INTERNAL | NON-FINAL<br>Machine-generated working product. No distribution approval is implied.</td></tr></table></body></html>')
  preview<-paste(parts,collapse="\n");plain<-paste(c(plain,brief$collection$coverage_note,"INTERNAL | NON-FINAL",""),collapse="\n")
  write_text(file.path(run,"daily_briefing.html"),preview);write_text(file.path(run,"daily_briefing.txt"),plain)
  image_names<-c("USUN_Seal.png",rendered$images);images<-list();body<-portable<-preview
  atomic_bytes(file.path(run,"figures/USUN_Seal.png"),read_bytes(file.path(root,"assets/USUN_Seal.png")))
  for(name in image_names) {
    bytes<-read_bytes(file.path(run,"figures",name));cid<-paste0("unbrief-",substr(sha_raw(bytes),1,20),"@local")
    images<-c(images,list(list(name=name,cid=cid,bytes=bytes)))
    body<-gsub(paste0("figures/",name),paste0("cid:",cid),body,fixed=TRUE)
    portable<-gsub(paste0("figures/",name),paste0("data:image/png;base64,",b64(bytes)),portable,fixed=TRUE)
  }
  write_text(file.path(run,"daily_briefing_preview.html"),portable)
  raw<-assemble_mime(plain,body,images,paste(cfg$email$subject_prefix,date,sep=" | "),brief$prepared_at,brief$status,cfg$email$from_address,cfg$email$to_addresses)
  atomic_bytes(file.path(run,"daily_briefing.eml"),raw)
  audit<-c('<!doctype html><html><head><meta charset="utf-8"><title>Source and analysis audit</title><style>body{font:15px/1.55 Arial;color:#243746;max-width:1100px;margin:30px auto;padding:0 20px}h1,h2{color:#062135}table{border-collapse:collapse;width:100%}td,th{padding:8px;text-align:left;border:1px solid #ccd6df}blockquote{border-left:3px solid #557e9c;padding-left:14px}code{overflow-wrap:anywhere}</style></head><body>',sprintf('<h1>Source and analysis audit | %s</h1><p>%s</p>',brief$date,html_escape(brief$status)))
  previous_region<-""
  for(s in speeches){
    if(!identical(previous_region,s$region)){audit<-c(audit,paste0("<h1>",html_escape(s$region),"</h1>"));previous_region<-s$region}
    a<-analyses[[s$iso3]];audit<-c(audit,sprintf('<h2>%s</h2><p>Source SHA-256: <code>%s</code><br>Text SHA-256: <code>%s</code><br>Analysis: %s</p>',html_escape(s$country),s$source_sha256,s$text_sha256,html_escape(a$verification$status)))
    original_notes<-unique(c(unlist(s$flags),unlist(a$flags)));if(length(original_notes))audit<-c(audit,paste0("<p><strong>Original source/review notes:</strong> ",html_escape(paste(original_notes,collapse=" ")),"</p>"))
    if(nzchar(s$original_summary))audit<-c(audit,paste0('<details><summary>Original supplied summary</summary><p>',html_escape(s$original_summary),'</p></details>'))
    for(b in a$bullets){audit<-c(audit,sprintf('<h3>%s</h3><p>%s</p><details><summary>Supporting source passages</summary>',html_escape(b$label),html_escape(b$text)));for(ev in b$evidence)audit<-c(audit,sprintf('<blockquote><strong>%s</strong> %s</blockquote>',html_escape(ev$sentence_id),html_escape(ev$quote)));audit<-c(audit,'</details>')}
    audit<-c(audit,'<table><tr><th>Issue</th><th>Decision</th><th>Basis and evidence</th></tr>')
    for(i in a$issues)audit<-c(audit,sprintf('<tr><td>%s</td><td>%s</td><td>%s<br>%s</td></tr>',html_escape(i$issue_id),html_escape(i$status),html_escape(i$rationale),paste(vapply(i$evidence,function(ev)html_escape(paste(ev$sentence_id,ev$quote,sep=": ")),character(1)),collapse="<br>")))
    audit<-c(audit,paste0('</table><details><summary>Full source text</summary><p>',gsub("\n","<br>",html_escape(s$text),fixed=TRUE),'</p></details>'))
  }
  write_text(file.path(run,"audit.html"),c(audit,"</body></html>"));append_d1_audit(run,cp);invisible(TRUE)
}
