# Compare batched outputs to the unmodified application matcher on real records.
a<-commandArgs(TRUE);stopifnot(length(a)==2)
if(!l10n_info()[['UTF-8']])Sys.setlocale('LC_CTYPE','English_United States.utf8')
source(file.path(a[1],'R/load.R'));load_readout(a[1])
counts<-list()
for(filename in names(jsonlite::fromJSON(file.path(a[2],'input-batches.json')))) {
  run<-file.path(a[2],paste0('final-',tools::file_path_sans_ext(filename)))
  result<-readRDS(file.path(run,'result.rds'));s<-result$statements
  positive<-unique(result$tracked$evidence$statement_id)
  selected<-unique(c(head(which(s$statement_id %in% positive),8L),head(which(!s$statement_id %in% positive),5L),head(order(nchar(s$text),decreasing=TRUE),2L)))
  selected<-sort(selected);subset<-s[selected,,drop=FALSE]
  expected<-match_topics(subset,result$config$fixed_topics)$evidence
  actual<-result$tracked$evidence[result$tracked$evidence$statement_id %in% subset$statement_id,,drop=FALSE]
  rownames(expected)<-NULL;rownames(actual)<-NULL
  stopifnot(identical(expected,actual))
  counts[[filename]]<-list(real_records=length(selected),evidence_rows=nrow(actual),exact_agreement=TRUE)
  cat(filename,':',length(selected),'real records,',nrow(actual),'evidence rows agree exactly.\n')
}
jsonlite::write_json(counts,file.path(a[2],'matcher-equivalence.json'),pretty=TRUE,auto_unbox=TRUE)
