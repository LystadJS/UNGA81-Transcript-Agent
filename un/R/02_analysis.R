# Full-text, evidence-constrained summaries and a separate model review pass.
validate_evidence <- function(evidence,sentences) {
  assert(is.list(evidence),"Evidence must be an array")
  ids<-vapply(sentences,function(s)s$id,character(1));texts<-vapply(sentences,function(s)s$text,character(1))
  for(ev in evidence) {
    assert(is.list(ev)&&setequal(names(ev),c("sentence_id","quote")),"Malformed evidence object")
    at<-match(ev$sentence_id,ids);assert(!is.na(at),"Unknown evidence sentence ID")
    assert(is.character(ev$quote)&&length(ev$quote)==1&&nchar(trimws(ev$quote))>=5&&grepl(ev$quote,texts[at],fixed=TRUE),"Evidence quote is not an exact source substring")
  }
  invisible(TRUE)
}
validate_analysis <- function(a,speech,book,inherited=FALSE) {
  assert(is.list(a)&&is.list(a$bullets)&&length(a$bullets)>=1&&length(a$bullets)<=5,"Expected 1-5 supported summary points")
  for(b in a$bullets) {
    assert(is.character(b$text)&&length(b$text)==1&&is.character(b$label)&&length(b$label)==1,"Malformed summary point")
    visible(b$text);visible(b$label);assert(nchar(b$text)<=1400&&nchar(b$label)<=100,"Summary point too long")
    assert(!grepl("<[^>]+>|\\[[A-Z]{3}\\.[0-9]+\\]|SOURCE FILE:|\\bREF:",paste(b$label,b$text),perl=TRUE),"Summary contains formatting/audit artifacts")
    assert(length(b$evidence)>0,"Summary point lacks evidence");validate_evidence(b$evidence,speech$sentences)
  }
  assert(is.list(a$issues),"Issue decisions missing")
  ids<-vapply(a$issues,function(i)str1(i$issue_id),character(1));expected<-vapply(book,function(i)i$issue_id,character(1))
  assert(length(ids)==length(book)&&!anyDuplicated(ids)&&setequal(ids,expected),"Missing, duplicate or unknown issue decision")
  for(i in a$issues) {
    assert(i$status %in% c("present","absent","uncertain"),"Invalid issue status")
    assert(nzchar(trimws(str1(i$rationale))),"Issue decision lacks rationale")
    if(i$status=="present"&&!inherited)assert(length(i$evidence)>0,"Present code lacks source evidence")
    validate_evidence(i$evidence %||% list(),speech$sentences)
  }
  assert(is.list(a$flags)&&all(vapply(a$flags,function(x)is.character(x)&&length(x)==1,logical(1))),"Invalid analysis flags")
  a
}
extractive_analysis <- function(speech,book) {
  selected<-issues<-list();ids<-character()
  for(issue in book) {
    hit<-Filter(function(s)grepl(issue$extractive_regex,s$text,ignore.case=TRUE,perl=TRUE),speech$sentences)
    evidence<-lapply(head(hit,3),function(s)list(sentence_id=s$id,quote=s$text))
    issues<-c(issues,list(list(issue_id=issue$issue_id,status=if(length(hit))"present" else "uncertain",evidence=evidence,rationale=if(length(hit))"Provisional lexicon hit; not semantically adjudicated." else "No lexicon hit; absence is NOT established.")))
    useful<-Filter(function(s)nchar(s$text)>=30&&nchar(s$text)<=800&&!s$id%in%ids,hit)
    if(length(useful)){s<-useful[[1]];s$label<-issue$label;selected<-c(selected,list(s));ids<-c(ids,s$id)}
  }
  if(!length(selected))selected<-lapply(head(Filter(function(s)nchar(s$text)>=30&&nchar(s$text)<=800,speech$sentences),4),function(s){s$label<-"Speech excerpt";s})
  assert(length(selected)>0,"No usable extractive sentences")
  bullets<-lapply(head(selected,5),function(s)list(label=s$label,text=s$text,evidence=list(list(sentence_id=s$id,quote=s$text))))
  list(bullets=bullets,issues=issues,flags=list("EXTRACTIVE FALLBACK: exact source excerpts and provisional keyword coding; not a reviewed narrative summary."),verification=list(status="extractive_provisional",notes="No model generation or semantic review performed."))
}
new_model_client <- function(root,cfg,run,fetch=http_raw,budget=NULL) {
  e<-new.env(parent=emptyenv());e$root<-root;e$cfg<-cfg;e$run<-run;e$fetch<-fetch;e$usage<-list();e$calls<-0L
  if(is.null(budget)){budget<-new.env(parent=emptyenv());budget$used<-0L}
  e$budget<-budget;e
}
model_call <- function(client,prompt,payload,schema,name,model) {
  cfg<-client$cfg;assert(isTRUE(cfg$allow_external_ai),"External AI is disabled; authorize public-source processing explicitly")
  key<-Sys.getenv("OPENAI_API_KEY");assert(nzchar(key),"OPENAI_API_KEY is missing; configure it locally, not in chat")
  st<-cfg$model;assert(client$budget$used<st$max_calls_per_run,"Invocation-wide model-call budget reached")
  client$budget$used<-client$budget$used+1L;client$calls<-client$calls+1L
  req<-list(model=model,store=FALSE,input=list(list(role="system",content=prompt),list(role="user",content=json_text(payload))),text=list(format=list(type="json_schema",name=name,strict=TRUE,schema=schema)),max_output_tokens=st$max_output_tokens)
  fingerprint<-sha_text(json_text(req));stem<-sprintf("%03d_%s",client$calls,fingerprint)
  json_write(file.path(client$run,"audit/model_requests",paste0(stem,".json")),req)
  st$max_response_bytes<-5000000
  raw<-client$fetch(st$endpoint,st,body=charToRaw(enc2utf8(json_text(req))),headers=list(Authorization=paste("Bearer",key),`Content-Type`="application/json"))
  response<-json_raw(raw);atomic_bytes(file.path(client$run,"audit/model_responses",paste0(stem,".json")),raw)
  assert(identical(response$status,"completed"),"Model response incomplete; no truncated output accepted")
  pieces<-character()
  for(item in response$output)for(x in item$content) {assert(!identical(x$type,"refusal"),"Model refused the requested analysis");if(identical(x$type,"output_text"))pieces<-c(pieces,str1(x$text))}
  assert(length(pieces)>0,"Missing structured model output")
  client$usage<-c(client$usage,list(list(request_sha256=fingerprint,model_requested=model,model_returned=response$model,response_id=response$id,usage=response$usage %||% list())))
  json_write(file.path(client$run,"audit/model_usage.json"),client$usage)
  json_raw(charToRaw(enc2utf8(paste(pieces,collapse=""))))
}
model_analyze <- function(client,speech,book) {
  cfg<-client$cfg;assert(nchar(speech$text)<=cfg$model$max_input_chars_per_country,"Speech exceeds configured input bound; full text is never silently truncated")
  prompt<-read_text(file.path(client$root,"prompts/summarize.txt"));review<-read_text(file.path(client$root,"prompts/review.txt"))
  schema<-json_read(file.path(client$root,"schemas/country_analysis.json"));rschema<-json_read(file.path(client$root,"schemas/review.json"))
  schema<-bind_issue_schema(schema,book);rschema<-bind_issue_schema(rschema,book)
  payload<-list(country=speech$country,speaker_as_supplied=speech$speaker,date_as_supplied=speech$date,prior_summary=speech$original_summary %||% "",sentences=speech$sentences,codebook=book)
  cache_key<-sha_text(json_text(list(version=UNBRIEF_VERSION,payload=payload,source_sha256=speech$source_sha256,prompt=prompt,review=review,schema=schema,review_schema=rschema,model_settings=cfg$model)))
  cache<-file.path(client$root,cfg$storage$cache_dir,paste0(cache_key,".json"))
  if(isTRUE(cfg$model$cache)&&file.exists(cache)) {
    c<-json_read(cache);assert(identical(c$cache_key,cache_key)&&identical(c$analysis_sha256,sha_text(json_text(c$analysis))),"Cached analysis identity/hash mismatch")
    a<-validate_analysis(c$analysis,speech,book);a$verification$cache_reused<-TRUE;return(a)
  }
  first<-model_call(client,prompt,payload,schema,"country_analysis",cfg$model$name);validate_analysis(first,speech,book)
  payload$proposed_analysis<-first
  result<-model_call(client,review,payload,rschema,"country_review",cfg$model$review_name)
  assert(result$decision %in% c("accept","revise","hold"),"Invalid review decision")
  final<-validate_analysis(result$analysis,speech,book)
  final$verification<-list(status=if(result$decision=="hold")"model_hold" else "model_reviewed",decision=result$decision,notes=result$notes,cache_reused=FALSE,cache_key=cache_key,reviewer_is_human=FALSE)
  if(isTRUE(cfg$model$cache))json_write(cache,list(cache_key=cache_key,analysis_sha256=sha_text(json_text(final)),analysis=final))
  final
}
failed_analysis <- function(book,message) list(bullets=list(),issues=lapply(book,function(i)list(issue_id=i$issue_id,status="uncertain",evidence=list(),rationale="Analysis unavailable; inspect audit errors.")),flags=list("Summary unavailable: automated analysis did not pass validation."),verification=list(status="failed",notes=message))
