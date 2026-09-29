# Exact source affiliation, immutable raw bytes and explicit non-delivery accounting.
sentence_units <- function(text) {
  chunks<-strsplit(text,'(?<=[.!?])[[:space:]]+(?=[A-ZÀ-Ý“"\x27])|\\n+',perl=TRUE)[[1]]
  chunks<-trimws(chunks);chunks<-chunks[nzchar(chunks)]
  lapply(seq_along(chunks),function(i)list(id=sprintf("S%04d",i),text=chunks[i]))
}
parse_source_date <- function(x) {
  x<-trimws(x)
  if(grepl("^[0-9]{4}-[0-9]{2}-[0-9]{2}$",x)) {d<-as.Date(x);assert(!is.na(d)&&as.character(d)==x,"Invalid source date");return(x)}
  months<-c(month.name,month.abb);nums<-rep(seq_len(12),2)
  parts<-strsplit(gsub(",","",x),"[[:space:]]+")[[1]]
  assert(length(parts)==3,"Unsupported date; use ISO YYYY-MM-DD")
  m<-match(parts[1],months);if(!is.na(m)){day<-parts[2];year<-parts[3]} else {m<-match(parts[2],months);day<-parts[1];year<-parts[3]}
  assert(!is.na(m),"Unrecognized English month");out<-sprintf("%s-%02d-%02d",year,nums[m],as.integer(day));parse_source_date(out)
}
normalized_speech <- function(r,registry) {
  for(k in c("iso3","country","speaker","title","date","text","source_type")) assert(is.character(r[[k]])&&length(r[[k]])==1,paste("Missing normalized string",k))
  parse_source_date(r$date);c<-resolve_country(registry,r$iso3);assert(!is.null(c),"Unknown country ISO3")
  cc<-resolve_country(registry,r$country);assert(!is.null(cc)&&identical(cc$iso3,c$iso3),"Country name conflicts with ISO3")
  assert(word_count(r$text)>=20,"Source text too short");visible(r$text)
  r$sentences<-r$sentences %||% sentence_units(r$text)
  ids<-vapply(r$sentences,function(s)str1(s$id),character(1));assert(all(nzchar(ids))&&!anyDuplicated(ids),"Missing or duplicate sentence IDs")
  assert(identical(norm(paste(vapply(r$sentences,function(s)str1(s$text),character(1)),collapse=" ")),norm(r$text)),"Sentence units do not reconstruct full text")
  r$region<-r$region %||% c$region;r$flags<-r$flags %||% list();r$original_summary<-r$original_summary %||% ""
  r$source_url<-r$source_url %||% "";r$source_file<-r$source_file %||% "";computed_hash<-sha_text(r$text)
  if(!is.null(r$text_sha256))assert(identical(r$text_sha256,computed_hash),"Normalized text hash mismatch")
  r$text_sha256<-computed_hash
  r$source_sha256<-r$source_sha256 %||% r$text_sha256
  if(nzchar(r$source_url))source_url(r$source_url)
  r
}
safe_zip <- function(path,max_bytes=250000000,max_files=2000) {
  info<-utils::unzip(path,list=TRUE)
  assert(nrow(info)<=max_files&&sum(info$Length)<=max_bytes&&all(info$Length<=25000000),"Archive exceeds configured limits")
  names<-gsub("\\\\","/",info$Name)
  assert(!any(grepl("^/|(^|/)\\.\\.(/|$)|:",names))&&!anyDuplicated(names),"Unsafe/duplicate archive paths")
  info
}
docx_paragraphs <- function(path) {
  need_packages("xml2");info<-safe_zip(path,50000000,2000)
  assert(sum(info$Name=="word/document.xml")==1,"DOCX lacks document.xml")
  temp<-tempfile();dir.create(temp);on.exit(unlink(temp,recursive=TRUE))
  utils::unzip(path,files="word/document.xml",exdir=temp)
  bytes<-read_bytes(file.path(temp,"word/document.xml"));raw<-rawToChar(bytes)
  assert(!grepl("<!DOCTYPE|<!ENTITY",raw,ignore.case=TRUE),"Unsafe XML declarations")
  doc<-xml2::read_xml(bytes,options="NONET");ns<-c(w="http://schemas.openxmlformats.org/wordprocessingml/2006/main")
  ps<-xml2::xml_find_all(doc,".//w:body/w:p",ns)
  vapply(ps,function(p)paste(xml2::xml_text(xml2::xml_find_all(p,".//w:t",ns)),collapse=""),character(1))
}
parse_docx <- function(path,name,day,registry,archive) {
  ps<-trimws(docx_paragraphs(path));ps<-ps[nzchar(ps)]
  ds<-sub("^Date:[[:space:]]*","",ps[startsWith(ps,"Date:")]);assert(length(ds)==1,"Missing or ambiguous document date")
  date<-parse_source_date(ds);if(date!=day)return(list(excluded=list(source=name,reason="different_date",date=date)))
  h<-which(norm(ps)=="full speech text");assert(length(h)==1&&h<length(ps),"Full Speech Text heading missing or ambiguous")
  text<-paste(ps[(h+1):length(ps)],collapse="\n");assert(word_count(text)>=50,"Full speech text too short")
  rawcountry<-trimws(sub("[-_ ]*UNGA[[:space:]]*[0-9]+.*$","",tools::file_path_sans_ext(basename(name)),ignore.case=TRUE))
  c<-resolve_country(registry,rawcountry);assert(!is.null(c),paste("Unresolved source country:",rawcountry))
  get_meta<-function(key){m<-ps[seq_len(h-1)];v<-m[startsWith(m,paste0(key,":"))];if(length(v)==1)trimws(sub("^[^:]+:","",v)) else ""}
  speaker<-get_meta("Speaker");title<-"";rx<-"^(Head of Government|Prime Minister|Vice President|President|King|Minister of Foreign Affairs)[[:space:]]+(.+)$"
  if(grepl(rx,speaker)){title<-sub(rx,"\\1",speaker);speaker<-sub(rx,"\\2",speaker)}
  sidx<-which(norm(ps)=="speech summary");original<-if(length(sidx)==1&&sidx<h-1)paste(ps[(sidx+1):(h-1)],collapse="\n") else ""
  source<-archive_store(archive,read_bytes(path),name,"docx");flags<-list()
  if(!nzchar(speaker))flags<-c(flags,list("Speaker is missing in source metadata."))
  if(grepl("80th (session|general assembly)",text,ignore.case=TRUE)&&grepl("81",name))flags<-c(flags,list("Session reference conflicts with the file label; not silently corrected."))
  r<-list(iso3=c$iso3,country=c$country,speaker=speaker,title=title,date=date,region=c$region,region_source=get_meta("Region"),source_type="supplied_full_text",source_file=name,source_sha256=source$sha256,source_url="",text=text,sentences=sentence_units(text),original_summary=original,flags=flags)
  list(speech=normalized_speech(r,registry))
}
collect_local <- function(path,day,registry,archive) {
  speeches<-excluded<-errors<-list()
  if(grepl("\\.json$",path,ignore.case=TRUE)) {
    archive_store(archive,read_bytes(path),basename(path));records<-json_read(path)
    assert(is.list(records)&&is.null(names(records)),"Local JSON must be an array of normalized speeches")
    for(r in records) {
      if(!identical(r$date,day)){excluded<-c(excluded,list(list(source=r$source_file %||% "",reason="different_date")));next}
      result<-tryCatch(normalized_speech(r,registry),error=function(e)e)
      if(inherits(result,"error"))errors<-c(errors,list(list(source=r$source_file %||% "",error=conditionMessage(result)))) else speeches<-c(speeches,list(result))
    }
  } else {
    names<-paths<-character();temp<-NULL
    if(grepl("\\.zip$",path,ignore.case=TRUE)) {
      info<-safe_zip(path);temp<-tempfile();dir.create(temp);on.exit(unlink(temp,recursive=TRUE))
      keep<-grepl("\\.docx$",info$Name,ignore.case=TRUE);names<-info$Name[keep]
      for(x in info$Name[!keep & !grepl("/$",info$Name)])excluded<-c(excluded,list(list(source=x,reason="unsupported_file_type")))
      if(length(names))utils::unzip(path,files=names,exdir=temp);paths<-file.path(temp,names)
    } else if(dir.exists(path)){paths<-list.files(path,pattern="\\.docx$",full.names=TRUE,ignore.case=TRUE);names<-basename(paths);assert(length(paths)>0,"No DOCX documents found")}
    else {assert(grepl("\\.docx$",path,ignore.case=TRUE),"Use a DOCX, DOCX folder, ZIP or normalized JSON");paths<-path;names<-basename(path)}
    for(i in seq_along(paths)) {
      result<-tryCatch(parse_docx(paths[i],names[i],day,registry,archive),error=function(e)e)
      if(inherits(result,"error"))errors<-c(errors,list(list(source=names[i],error=conditionMessage(result))))
      else {if(!is.null(result$speech))speeches<-c(speeches,list(result$speech));if(!is.null(result$excluded))excluded<-c(excluded,list(result$excluded))}
    }
  }
  list(speeches=speeches,collection=list(source_mode="local",status=if(length(errors))"PARTIAL" else "COMPLETE_WITHIN_SUPPLIED_CORPUS",errors=errors,excluded=excluded,inventory_total=length(speeches)+length(excluded)+length(errors),coverage_note="Coverage is limited to supplied files, not an independently verified delivered-speaker census."))
}
parse_api_detail <- function(doc,item,day,registry,cfg,source) {
  video<-doc$video;tr<-doc$transcript
  assert(identical(substr(str1(video$date),1,10),day)&&identical(video$slug,item$slug),"Detail/inventory identity mismatch")
  assert(is.list(tr)&&identical(tr$language,cfg$live$locale)&&length(tr$data)>0,"Requested transcript missing/empty or wrong language")
  assert(nzchar(str1(doc$disclaimer)),"Missing automatic-transcript disclaimer")
  outputs<-excluded<-list();numbers<-numeric()
  for(index in seq_along(tr$data)) {
    s<-tr$data[[index]];num<-s$statement_number
    assert(is.numeric(num)&&length(num)==1&&is.finite(num)&&num>0&&num==floor(num)&&!num %in% numbers,"Invalid or duplicated statement number");numbers<-c(numbers,num)
    sp<-s$speaker %||% list();assert(is.list(sp),"Unexpected speaker schema")
    page<-source_url(s$pageUrl %||% item$pageUrl);assert(sub("\\?.*$","",page)==sub("\\?.*$","",source_url(item$pageUrl)),"Statement URL identifies another meeting")
    sentences<-list()
    for(pi in seq_along(s$paragraphs))for(si in seq_along(s$paragraphs[[pi]]$sentences)) {
      v<-s$paragraphs[[pi]]$sentences[[si]];assert(is.character(v$text)&&length(v$text)==1,"Sentence text missing")
      assert(is.numeric(v$start)&&is.numeric(v$end)&&length(v$start)==1&&length(v$end)==1&&is.finite(v$start)&&is.finite(v$end)&&v$start>=0&&v$end>=v$start,"Invalid source sentence times")
      sentences<-c(sentences,list(list(id=sprintf("S%04d",length(sentences)+1),text=v$text,start=v$start,end=v$end,pointer=sprintf("/transcript/data/%d/paragraphs/%d/sentences/%d",index-1,pi-1,si-1),url=paste0(sub("\\?.*$","",source_url(item$pageUrl)),"?t=",ceiling(v$start)))))
    }
    assert(length(sentences)>0,"Statement has no sentence data");text<-paste(vapply(sentences,function(v)v$text,character(1)),collapse=" ")
    c<-resolve_country(registry,str1(sp$affiliation),str1(sp$affiliation_full));role<-str1(sp[["function"]]);reason<-""
    if(is.null(c))reason<-"unresolved_country_or_institutional_speaker"
    else if(grepl("(president|chair).{0,25}general assembly|secretary.general",role,ignore.case=TRUE))reason<-"institutional_speaker"
    else if(word_count(text)<cfg$live$min_statement_words)reason<-"below_configured_word_threshold"
    if(nzchar(reason)){excluded<-c(excluded,list(list(source=item$slug,statement_number=num,speaker=sp,words=word_count(text),reason=reason)));next}
    flags<-list();if(isTRUE(tr$timestamps_flagged))flags<-c(flags,list("Source flags timestamps as unreliable; text retained, timing claims withheld."))
    if(!nzchar(str1(sp$name)))flags<-c(flags,list("Speaker name missing in source."))
    r<-list(iso3=c$iso3,country=c$country,speaker=str1(sp$name,"Not provided"),title=role,date=day,region=c$region,region_source=c$region_basis,source_type="UN_automatic_transcript",source_file=paste0(item$slug,".json"),source_sha256=source$sha256,source_url=page,text=text,sentences=sentences,flags=flags,original_summary="",source_disclaimer=doc$disclaimer,meeting_id=item$slug,statement_number=as.character(num),agenda_item=str1(video$agenda_item),genre=if(grepl("general debate",str1(item$title),ignore.case=TRUE))"general_debate" else "unspecified",genre_basis="discovered meeting title",language=tr$language,translation_version=str1(tr$translation_version,"unspecified"),event_time=str1(video$date,day),event_time_precision=if(grepl("T",str1(video$date),fixed=TRUE))"source_timestamp_unverified_precision" else "date")
    outputs<-c(outputs,list(normalized_speech(r,registry)))
  }
  list(speeches=outputs,excluded=excluded)
}
collect_live <- function(day,registry,archive,cfg,fetch=http_raw) {
  st<-cfg$live;items<-list();seen<-character();expected<-NULL;done<-FALSE
  for(page in seq_len(st$max_pages)) {
    url<-sprintf("%s/%s/meetings.json?date=%s&xlang=1&page=%d",st$base_url,st$locale,day,page)
    raw<-fetch(url,st);archive_store(archive,raw,url);doc<-json_raw(raw)
    assert(is.numeric(doc$total)&&length(doc$total)==1&&doc$total>=0&&doc$total==floor(doc$total)&&is.logical(doc$hasMore)&&length(doc$hasMore)==1&&identical(as.numeric(doc$page),as.numeric(page))&&is.list(doc$meetings),"Inventory schema changed")
    assert(identical(doc$total,doc$totalIncludingOther),"Other-language meetings omitted despite xlang=1")
    if(is.null(expected))expected<-doc$total;assert(identical(expected,doc$total),"Inventory changed during pagination; rerun")
    for(item in doc$meetings) {
      assert(all(c("slug","date","title","body","hasTranscript","pageUrl","jsonUrl")%in%names(item)),"Malformed inventory item")
      assert(is.logical(item$hasTranscript)&&length(item$hasTranscript)==1&&!is.na(item$hasTranscript)&&!item$slug%in%seen,"Invalid inventory transcript flag or duplicate slug")
      assert(substr(str1(item$date),1,10)==day,"Inventory date mismatch");source_url(item$pageUrl);source_url(item$jsonUrl)
      seen<-c(seen,item$slug);items<-c(items,list(item))
    }
    if(!doc$hasMore){done<-TRUE;break};assert(length(doc$meetings)>0,"Pagination made no progress")
  }
  assert(done&&length(items)==expected,"Inventory page limit reached or count mismatch")
  speeches<-excluded<-errors<-list();matched<-0L
  for(item in items) {
    include<-grepl(st$meeting_title_regex,str1(item$title),ignore.case=TRUE,perl=TRUE)&&grepl(st$meeting_body_regex,paste(str1(item$body),str1(item$category),str1(item$title)),ignore.case=TRUE,perl=TRUE)
    if(!include){excluded<-c(excluded,list(list(source=item$slug,reason="outside_configured_meeting_scope")));next}
    matched<-matched+1L
    if(!isTRUE(item$hasTranscript)){errors<-c(errors,list(list(source=item$slug,error="No transcript available at collection time")));next}
    result<-tryCatch({url<-source_url(item$jsonUrl);raw<-fetch(url,st);source<-archive_store(archive,raw,url);parse_api_detail(json_raw(raw),item,day,registry,cfg,source)},error=function(e)e)
    if(inherits(result,"error"))errors<-c(errors,list(list(source=item$slug,error=conditionMessage(result)))) else {speeches<-c(speeches,result$speeches);excluded<-c(excluded,result$excluded)
      unresolved<-Filter(function(x)identical(x$reason,"unresolved_country_or_institutional_speaker")&&(x$words %||% 0)>=st$min_statement_words&&!grepl("secretary.general|general assembly",str1(x$speaker[["function"]]),ignore.case=TRUE),result$excluded)
      if(length(unresolved))errors<-c(errors,list(list(source=item$slug,error=sprintf("%d long statement(s) have unresolved country attribution; inspect excluded records.",length(unresolved)))))
    }
    if(identical(fetch,http_raw))Sys.sleep(st$request_interval_seconds)
  }
  list(speeches=speeches,collection=list(source_mode="live",status=if(length(errors))"PARTIAL" else "COMPLETE_WITHIN_DISCOVERED_SCOPE",inventory_total=length(items),in_scope_meetings=matched,errors=errors,excluded=excluded,coverage_note="Completeness is relative to the successful UN API inventory and configured scope, not an independently reconciled delivered-speaker roster. UN automatic transcripts are not official records."))
}
group_countries <- function(speeches) {
  out<-duplicates<-list()
  ids<-unique(vapply(speeches,function(s)s$iso3,character(1)))
  for(id in ids) {
    parts<-Filter(function(s)s$iso3==id,speeches);seen<-character();kept<-list()
    for(s in parts) {hash<-sha_text(norm(s$text));if(hash%in%seen)duplicates<-c(duplicates,list(list(iso3=id,source=s$source_file,reason="exact_text_duplicate"))) else {kept<-c(kept,list(s));seen<-c(seen,hash)}}
    r<-kept[[1]];r$source_parts<-lapply(kept,function(p)p[setdiff(names(p),c("sentences","text","original_summary"))])
    if(length(kept)>1) {
      sentences<-list();for(j in seq_along(kept))for(s in kept[[j]]$sentences){s$id<-paste0("P",j,"_",s$id);sentences<-c(sentences,list(s))}
      r$sentences<-sentences;r$text<-paste(vapply(sentences,function(s)s$text,character(1)),collapse=" ");r$text_sha256<-sha_text(r$text)
      r$source_sha256<-sha_text(paste(vapply(kept,function(s)s$source_sha256,character(1)),collapse="|"))
      r$speaker<-paste(unique(vapply(kept,function(s)s$speaker,character(1))),collapse="; ");r$title<-paste(unique(vapply(kept,function(s)s$title,character(1))),collapse="; ")
      r$original_summary<-paste(vapply(kept,function(s)s$original_summary %||% "",character(1)),collapse="\n")
      r$flags<-as.list(unique(c(unlist(lapply(kept,function(s)s$flags)),sprintf("%d distinct interventions grouped for this country; not counted as separate countries.",length(kept)))))
    }
    out<-c(out,list(r))
  }
  list(speeches=out,duplicates=duplicates)
}
