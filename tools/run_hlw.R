# Use the existing multi-date upload workflow unchanged, with Cuba refinements.
a<-commandArgs(TRUE)
stopifnot(length(a)==2)
if(!l10n_info()[['UTF-8']])Sys.setlocale('LC_CTYPE','English_United States.utf8')
stopifnot(l10n_info()[['UTF-8']])
ui<-normalizePath(a[1],winslash='/',mustWork=TRUE)
archive<-normalizePath(a[2],winslash='/',mustWork=TRUE)
source(file.path(ui,'R/load.R'));load_readout(ui)
# Cache exact, immutable parser results within this run. The original parser
# still produces every span; repeated topic scans need not parse the same body.
original_split_passages<-split_passages
passage_cache<-new.env(parent=emptyenv())
split_passages<-function(text) {
  key<-digest::digest(text,algo='sha256')
  if(exists(key,envir=passage_cache,inherits=FALSE)) {
    item<-get(key,envir=passage_cache,inherits=FALSE)
    stopifnot(identical(item$text,text));return(item$passages)
  }
  result<-original_split_passages(text)
  assign(key,list(text=text,passages=result),envir=passage_cache)
  result
}
for(text in c('Cuba. Embargo?','Cuba\n\nMedical cooperation.','Caf\u00e9 and Cuba.','')) {
  stopifnot(identical(original_split_passages(text),split_passages(text)))
  stopifnot(identical(original_split_passages(text),split_passages(text)))
}
refinements<-list(
  'Cuba'=list(include=c('Cuban','Cubans','Havana','Havanna'),exclude=character()),
  'Embargo and blockade'=list(include=c('embargo','blockade','bloqueo','economic siege'),exclude=character()),
  'Unilateral sanctions'=list(include=c('unilateral coercive','unilateral sanctions','economic sanctions','financial sanctions','coercive measures'),exclude=character()),
  'Terrorism-list designation'=list(include=c('state sponsor of terrorism','state sponsors of terrorism','sponsors of terrorism','list of terrorist','terrorism list'),exclude=character()),
  'Extraterritorial restrictions'=list(include=c('extraterritorial','extra-territorial','Helms-Burton','Helms Burton','secondary sanctions'),exclude=character()),
  'Medical cooperation'=list(include=c('medical cooperation','medical brigades','Cuban doctors','Cuban medical','health cooperation'),exclude=character()),
  'Humanitarian and development impacts'=list(include=c('humanitarian impact','humanitarian consequences','access to medicines','access to food','right to development','economic warfare','collective punishment'),exclude=character()),
  'Sovereignty and non-interference'=list(include=c('sovereignty','non-interference','noninterference','regime change','self-determination'),exclude=character()))
# The original phrase predicate accepts vectors. Batch those exact predicates
# over a statement's passages instead of recompiling them for every sentence.
original_match_topics<-match_topics
match_topics<-function(statements,topics) {
  available<-statements[statements$status=='available',,drop=FALSE]
  all_rows<-summaries<-list()
  for(topic in topics) {
    includes<-unique(c(topic$label,unlist(topic$include,use.names=FALSE)))
    excludes<-unlist(topic$exclude,use.names=FALSE);topic_rows<-list()
    for(i in seq_len(nrow(available))) {
      s<-available[i,,drop=FALSE];p<-split_passages(s$text);if(!nrow(p))next
      hits<-do.call(cbind,lapply(includes,function(term)phrase_hit(p$quote,term)))
      keep<-rowSums(hits)>0
      if(length(excludes))keep<-keep & !Reduce(`|`,lapply(excludes,function(term)phrase_hit(p$quote,term)))
      ix<-which(keep);if(!length(ix))next
      topic_rows[[length(topic_rows)+1L]]<-data.frame(topic_id=topic$id,topic=topic$label,statement_id=s$statement_id,country=s$country,country_id=s$country_id,source_file=s$source_file,body_sha256=s$body_sha256,passage_id=p$passage_id[ix],start_char=p$start_char[ix],end_char=p$end_char[ix],matched_phrases=vapply(ix,function(j)paste(includes[hits[j,]],collapse=' | '),character(1)),quote=p$quote[ix],stringsAsFactors=FALSE)
    }
    ev<-if(length(topic_rows))do.call(rbind,topic_rows) else empty_evidence()
    all_rows[[length(all_rows)+1L]]<-ev
    summaries[[length(summaries)+1L]]<-data.frame(topic=topic$label,texts_with_matches=length(unique(ev$statement_id)),eligible_texts=nrow(available),unresolved_texts=nrow(available)-length(unique(ev$statement_id)),attributed_countries_with_matches=length(unique(ev$country_id[nzchar(ev$country_id)])),available_attributed_countries=length(unique(available$country_id[nzchar(available$country_id)])),quote_count=nrow(ev),interpretation='literal_candidate_matches_not_semantic_presence',stringsAsFactors=FALSE)
  }
  if(!length(topics))return(original_match_topics(statements,topics))
  list(summary=do.call(rbind,summaries),evidence=do.call(rbind,all_rows),released=FALSE,producer='prototype_literal_v1')
}
test_text<-c('Cuba. Cuban medical brigades! Embargo and blockade.','Caf\u00e9 in Havana; sovereignty.','Nothing relevant.','AI is distinct from aid and said.','Cuba and sanctions. Exclude Cuba here.','Cuba\n\nCuba.','', 'State sponsors of terrorism.')
test_data<-data.frame(status='available',statement_id=paste0('engineering-',seq_along(test_text)),country='Test',country_id='TST',source_file='synthetic_fixture',body_sha256='synthetic',text=test_text,stringsAsFactors=FALSE)
test_topics<-c(make_topics(names(refinements),refinements),make_topics(c('AI','Excluded'),list(Excluded=list(include='Cuba',exclude='Exclude Cuba'))))
normalize_result<-function(x){rownames(x$summary)<-NULL;rownames(x$evidence)<-NULL;x}
stopifnot(identical(normalize_result(original_match_topics(test_data,test_topics)),normalize_result(match_topics(test_data,test_topics))))
cat('Task-local vector matching agrees exactly with original matching on boundary, exclusion, Unicode and empty-text cases.\n')
batches<-jsonlite::fromJSON(file.path(archive,'input-batches.json'))
for(filename in names(batches)) {
  input<-file.path(archive,'input',filename)
  name<-tools::file_path_sans_ext(basename(input))
  preflight<-withCallingHandlers(utils::read.csv(input,fileEncoding='UTF-8',colClasses='character',na.strings=character()),warning=function(w)stop(w))
  stopifnot(nrow(preflight)==batches[[filename]])
  config<-new_config('2026-09-21','2026-09-28',names(refinements),refinements,source='upload')
  job<-file.path(archive,paste0('final-',name))
  if(file.exists(file.path(job,'result.rds')))next
  result<-run_readout(config,job,ui,paths=input,display_names=paste0(name,'.csv'),make_pdf=FALSE)
  stopifnot(nrow(result$statements)==batches[[filename]])
  cat(name,nrow(result$statements),'records;',nrow(result$tracked$evidence),'evidence rows;',result$discovery$status,'\n')
}
