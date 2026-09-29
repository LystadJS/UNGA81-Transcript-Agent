# Validate the exact generated MIME bytes, table balance and plotted counts.
count_pattern <- function(pattern,text,perl=TRUE) {m<-gregexpr(pattern,text,perl=perl)[[1]];if(m[1]<0)0L else length(m)}
parse_mime <- function(raw) {
  text<-rawToChar(raw)
  assert(!grepl("\n",gsub("\r\n","",text,fixed=TRUE),fixed=TRUE),"MIME contains bare LF line endings")
  lines<-strsplit(text,"\r\n",fixed=TRUE)[[1]];assert(all(nchar(lines,type="bytes")<=998),"MIME line exceeds RFC limit")
  parse_part<-function(lines,depth=0L) {
    assert(depth<10,"MIME nesting exceeds limit");split<-which(lines=="")[1];assert(!is.na(split)&&split>1,"Malformed MIME headers")
    hs<-lines[seq_len(split-1)];unfold<-character()
    for(h in hs){if(grepl("^[ \t]",h)){assert(length(unfold)>0,"Orphan folded header");unfold[length(unfold)]<-paste(unfold[length(unfold)],trimws(h))}else unfold<-c(unfold,h)}
    assert(all(grepl("^[A-Za-z0-9-]+:",unfold)),"Invalid MIME header")
    keys<-tolower(sub(":.*$","",unfold));assert(!anyDuplicated(keys),"Duplicate MIME headers")
    heads<-setNames(trimws(sub("^[^:]+:","",unfold)),keys)
    body<-if(split<length(lines))lines[(split+1):length(lines)] else character()
    type<-tolower(sub(";.*$","",heads[["content-type"]] %||% "text/plain"))
    if(startsWith(type,"multipart/")) {
      ct<-heads[["content-type"]];assert(grepl('boundary="[^"]+"',ct),"Missing MIME boundary")
      boundary<-sub('.*boundary="([^"]+)".*','\\1',ct);delim<-paste0("--",boundary)
      starts<-which(body==delim);end<-which(body==paste0(delim,"--"));assert(length(starts)>0&&length(end)==1&&end>tail(starts,1),"Invalid multipart boundary sequence")
      ends<-c(starts[-1],end)-1;children<-lapply(seq_along(starts),function(i)parse_part(body[(starts[i]+1):ends[i]],depth+1))
      list(headers=heads,type=type,parts=children,bytes=raw())
    } else {
      assert(identical(heads[["content-transfer-encoding"]],"base64"),"Unexpected transfer encoding")
      list(headers=heads,type=type,parts=list(),bytes=unb64(paste(body,collapse="")))
    }
  }
  parse_part(lines)
}
flatten_mime <- function(part) c(list(part),unlist(lapply(part$parts,flatten_mime),recursive=FALSE))
check_tables <- function(html) {
  matches<-regmatches(html,gregexpr("</?(table|tr|td)\\b[^>]*>",html,ignore.case=TRUE,perl=TRUE))[[1]];stack<-character()
  for(tag in matches){name<-tolower(sub("^</?([A-Za-z]+).*","\\1",tag));if(startsWith(tag,"</")){assert(length(stack)>0&&tail(stack,1)==name,"Unbalanced HTML table markup");stack<-head(stack,-1)}else stack<-c(stack,name)}
  assert(!length(stack),"Unclosed HTML table markup");invisible(TRUE)
}
png_size <- function(raw) {
  assert(length(raw)>=24&&identical(raw[1:8],as.raw(c(137,80,78,71,13,10,26,10))),"Invalid PNG header")
  c(width=sum(as.integer(raw[17:20])*256^(3:0)),height=sum(as.integer(raw[21:24])*256^(3:0)))
}
validate_output <- function(root,run,cfg) {
  brief<-json_read(file.path(run,"brief.json"));n<-brief$country_count;raw<-read_bytes(file.path(run,"daily_briefing.eml"))
  mime<-parse_mime(raw);assert(identical(mime$headers[["x-unsent"]],"1"),"Unsent marker missing")
  parts<-flatten_mime(mime);htmls<-Filter(function(x)x$type=="text/html",parts);texts<-Filter(function(x)x$type=="text/plain",parts);images<-Filter(function(x)x$type=="image/png",parts)
  assert(length(htmls)==1&&length(texts)==1,"Expected one HTML and one plaintext MIME body")
  cp<-readRDS(file.path(run,"checkpoint.rds"));analytics_qa<-validate_analytics_output(root,run,cp)
  assert(length(images)==1L+length(cp$analytics$inline_images)&&length(images)<=4L,"Incorrect allowlisted inline image count")
  html<-rawToChar(htmls[[1]]$bytes);check_tables(html);visible(html)
  assert(count_pattern('class="country-title"',html)==n,"Country section count mismatch")
  assert(!grepl("<script|<iframe",html,ignore.case=TRUE),"Executable HTML forbidden in email")
  assert(!grepl("\\[[A-Z]{3}\\.[0-9]+\\]|SOURCE FILE:|\\bREF:|\\[Recipient|\\[your.email",html,perl=TRUE),"Visible internal or placeholder artifacts")
  tags<-regmatches(html,gregexpr("<img\\b[^>]*>",html,perl=TRUE))[[1]]
  cids<-vapply(images,function(im)sub("^<|>$","",im$headers[["content-id"]]),character(1))
  # Remove both angle brackets explicitly; sub alone replaces only the first.
  cids<-vapply(images,function(im)gsub("[<>]","",im$headers[["content-id"]]),character(1))
  assert(length(tags)==length(images)&&!anyDuplicated(cids),"Image/CID count mismatch")
  for(tag in tags) {
    src<-sub('.*src="([^"]+)".*','\\1',tag);assert(startsWith(src,"cid:"),"Email image is not embedded")
    at<-match(sub("^cid:","",src),cids);assert(!is.na(at),"Unresolved inline image")
    assert(png_size(images[[at]]$bytes)["width"]<=840,"Oversized embedded image")
    width<-as.integer(sub('.* width="([0-9]+)".*','\\1',tag));assert(!is.na(width)&&width<=840,"Oversized HTML image attribute")
    assert(grepl("^inline;",images[[at]]$headers[["content-disposition"]]),"Image not inline")
  }
  assert(length(raw)<=cfg$email$max_message_bytes,"Message exceeds configured byte limit")
  rows<-read.csv(file.path(run,"data/country_issue_long.csv"),na.strings="",check.names=FALSE,fileEncoding="UTF-8")
  assert(nrow(rows)==n*brief$issue_count&&!anyDuplicated(paste(rows$iso3,rows$issue_id)),"Issue matrix shape/duplicate error")
  freq_path<-file.path(run,"data/issue_frequency.csv");freq<-NULL
  if(file.exists(freq_path)) {
    freq<-read.csv(freq_path,na.strings="",check.names=FALSE,fileEncoding="UTF-8")
    for(i in seq_len(nrow(freq))){r<-rows[rows$issue_id==freq$issue_id[i],];assert(sum(r$code==1,na.rm=TRUE)==freq$n_present[i]&&sum(is.na(r$code))==freq$n_unknown[i],"Frequency/unknown count mismatch")}
  }
  region_path<-file.path(run,"data/regional_issue_matrix.csv");region<-NULL
  if(file.exists(region_path)) {
    region<-read.csv(region_path,na.strings="",check.names=FALSE,fileEncoding="UTF-8")
    for(i in seq_len(nrow(region))){r<-rows[rows$issue_id==region$issue_id[i]&rows$region==region$region[i],];assert(sum(r$code==1,na.rm=TRUE)==region$n_present[i],"Regional count mismatch")}
  }
  if(file.exists(file.path(run,"data/issue_network_nodes.csv"))&&file.exists(file.path(run,"data/issue_network_edges.csv"))) {
    nodes<-read.csv(file.path(run,"data/issue_network_nodes.csv"),fileEncoding="UTF-8",stringsAsFactors=FALSE)
    edges<-read.csv(file.path(run,"data/issue_network_edges.csv"),fileEncoding="UTF-8",stringsAsFactors=FALSE)
    assert(all(FIXED_ISSUE_IDS%in%nodes$issue_id),"Audit network dropped a fixed topic")
    assert(all(edges$pair_complete)&all(edges$n_pair_observed==n),"Audit network selected an unresolved topic pair")
    assert(!nrow(edges)||all(edges$n_copresent>0),"Audit network fabricated a zero-overlap connection")
  }
  cp<-readRDS(file.path(run,"checkpoint.rds"));expected<-order_country_readouts(cp$speeches,cfg)
  assert(identical(vapply(cp$speeches,function(s)s$iso3,character(1)),vapply(expected,function(s)s$iso3,character(1))),"Stored countries are not region-first alphabetical")
  title_text<-function(cls) {
    pattern<-paste0('<div class="',cls,'"[^>]*>[^<]*</div>')
    tags<-regmatches(html,gregexpr(pattern,html,perl=TRUE))[[1]]
    sub('</div>$','',sub('^<div[^>]*>','',tags))
  }
  assert(identical(unname(title_text("country-title")),unname(vapply(expected,function(s)html_escape(s$country),character(1)))),"HTML countries not ordered like the source-bound registry")
  expected_regions<-unique(vapply(expected,function(s)s$region,character(1)))
  assert(identical(unname(title_text("region-title")),if(length(expected_regions))unname(html_escape(expected_regions)) else character()),"HTML regional group order mismatch")
  if(!is.null(freq))assert(identical(as.character(head(freq$issue_id,4)),FIXED_ISSUE_IDS),"Fixed topics missing or reordered in audit figure data")
  assert(count_pattern('class="fixed-watchlist"',html)==1,"Permanent watchlist missing")
  for(id in FIXED_ISSUE_IDS)assert(sum(rows$issue_id==id)==n,"Permanent topic has missing country decisions")
  plain<-rawToChar(texts[[1]]$bytes)
  for(reg in expected_regions)assert(grepl(paste0("=== ",toupper(reg)," | "),plain,fixed=TRUE),"Plaintext missing a regional heading")
  if(!is.null(freq))assert(all(freq$n_present+freq$n_absent+freq$n_unknown==n),"Presence/absence/unresolved accounting does not reconcile")
  if(brief$source=="replay") {snapshot<-json_read(file.path(root,"examples",brief$date,"snapshot.json"));for(id in names(snapshot$expected_counts))assert(sum(rows$issue_id==id & rows$code==1,na.rm=TRUE)==snapshot$expected_counts[[id]],paste("Archived count mismatch:",id))}
  assert(count_pattern('class="analytics-slot"',html)==5L,"Email must contain exactly five analytical sections")
  tags<-regmatches(html,gregexpr('id="analytics-O[0-9]+"',html,perl=TRUE))[[1]]
  assert(identical(tags,paste0('id="analytics-',D1_SLOT_IDS,'"')),"Analytical sections missing or reordered")
  assert(!grepl("Selected requests |Cross-speech issue patterns",html,fixed=FALSE),"Legacy extra analytical section leaked into email")
  for(f in FIGURE_FILES)assert(!grepl(f,html,fixed=TRUE),"Audit-only figure leaked into email")
  for(i in seq_along(D1_SLOT_IDS))assert(grepl(toupper(paste0(i,". ",D1_SLOT_TITLES[i])),plain,fixed=TRUE),"Plaintext lacks a required analytical section")
  for(p in cp$analytics$report_packets)assert(grepl(html_escape(p$reason),html,fixed=TRUE)&&grepl(p$reason,plain,fixed=TRUE),"HTML/plaintext packet reason differs")
  c(list(passed=TRUE,country_sections=n,coding_cells=nrow(rows),mime_parts=length(parts),inline_images=length(images),message_bytes=length(raw),html_table_balance="passed",cid_resolution="passed",frequency_reconciliation=if(!is.null(freq))"passed" else "not available: audit-only chart failed",regional_reconciliation=if(!is.null(region))"passed" else "not available: audit-only chart failed",live_outlook_rendering="not tested",fixed_topics="Iran, Cuba, Ukraine, AI: complete and ordered",country_ordering="region_then_alphabetical",region_sections=length(expected_regions),semantic_accuracy="Structural QA does not establish semantic accuracy; model review is not human review."),analytics_qa)
}
finalize_run <- function(root,run,cfg) {
  build_email(root,run,cfg);qa<-validate_output(root,run,cfg);json_write(file.path(run,"validation.json"),qa)
  brief<-json_read(file.path(run,"brief.json"));json_write(file.path(run,"checkpoint.json"),list(stage="complete",status=brief$status,no_email_sent=TRUE,analytics=list(design="D1",milestone="I2",methods_accounted=qa$methods_accounted,prerequisite_checks=qa$prerequisite_checks,released_models=qa$released_models,five_output_contract=qa$five_output_packet_contract)))
  files<-sort(list.files(run,recursive=TRUE,full.names=TRUE));files<-files[basename(files)!="SHA256SUMS.txt"]
  manifest<-vapply(files,function(f)paste(sha_file(f),substring(f,nchar(run)+2),sep="  "),character(1));write_text(file.path(run,"SHA256SUMS.txt"),manifest)
  rel<-substring(run,nchar(root)+2);latest<-list(run=rel,date=brief$date,status=brief$status,eml=paste0(rel,"/daily_briefing.eml"))
  json_write(file.path(root,"output/latest.json"),latest)
  json_write(file.path(root,"output",paste0("latest_",brief$date,".json")),latest)
  cat("COMPLETE:",file.path(run,"daily_briefing.eml"),"\n");invisible(qa)
}
