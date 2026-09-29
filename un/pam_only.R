#!/usr/bin/env Rscript
# Reuse an archived M02 frozen feature artifact; run only M09 PAM and audit outputs.
main <- function() {
  self<-sub("^--file=","",commandArgs()[grepl("^--file=",commandArgs())][1]);root<-normalizePath(dirname(self),winslash="/",mustWork=TRUE)
  old<-getwd();setwd(root);on.exit(setwd(old),add=TRUE)
  opt<-list(input="",output="",minimal="false");for(a in commandArgs(trailingOnly=TRUE)){if(a=="--help"){cat("Rscript pam_only.R --input=ARCHIVED_RUN --output=NEW_DIRECTORY --minimal=true|false\n");return(invisible(NULL))};if(!grepl("^--[^=]+=",a))stop("Use --name=value arguments");k<-sub("^--([^=]+)=.*$","\\1",a);if(!k%in%names(opt))stop("Unknown argument: ",k);opt[[k]]<-sub("^--[^=]+=","",a)}
  options(unbrief.minimal=identical(opt$minimal,"true"),unbrief.root=root)
  for(f in list.files("R",pattern="^[0-9].*\\.R$",full.names=TRUE))source(f)
  need_packages(c("Matrix","cluster"));input<-normalizePath(opt$input,winslash="/",mustWork=TRUE);assert(nzchar(opt$output)&&!dir.exists(opt$output)&&!file.exists(opt$output),"Use a new output directory")
  fpath<-file.path(input,"audit/analytics/artifacts/M02.rds");assert(file.exists(fpath),"Input lacks M02 frozen feature artifact");feature<-readRDS(fpath)
  cp<-if(file.exists(file.path(input,"checkpoint.rds")))readRDS(file.path(input,"checkpoint.rds"))else NULL;i2_validate_features(feature,cp,root)
  hash_before<-sha_file(fpath);dir.create(opt$output,recursive=TRUE);run<-normalizePath(opt$output,winslash="/",mustWork=TRUE);dir.create(file.path(run,"audit/analytics/artifacts"),recursive=TRUE);dir.create(file.path(run,"logs"),recursive=TRUE)
  immutable_write(file.path(run,"audit/analytics/artifacts/M02.rds"),read_bytes(fpath));value<-pam_execute(feature,cp,root);pam_validate(value,feature,root,cp);immutable_write(file.path(run,"audit/analytics/artifacts/M09.rds"),serialize(value,NULL,version=3));pam_write_tables(value,run);fig<-pam_run_figure(root,run);assert(fig$state=="executed","PAM audit figure failed")
  write_text(file.path(run,"audit.html"),c('<!doctype html><html><head><meta charset="utf-8"><title>PAM audit</title><style>body{font:15px Arial;color:#202B38;padding:24px}table{border-collapse:collapse}td,th{border-bottom:1px solid #D6DEE7;padding:8px;text-align:left}</style></head><body>',pam_audit_block(run),'</body></html>'))
  assert(identical(sha_file(fpath),hash_before),"Original frozen M02 bytes changed")
  json_write(file.path(run,"validation.json"),list(computations="executed_and_recomputed_in_R",M02_byte_unchanged=TRUE,M09="audit_only",engineering_screen_passed=value$quality$passed,selected_k=value$numerical$selected_k,selected_medoids=value$numerical$selected_medoids,planned_replicates=nrow(value$numerical$resample_ledger),successful_replicates=sum(value$numerical$resample_ledger$status=="executed"),no_email_sent=TRUE))
  write_text(file.path(run,"R_sessionInfo.txt"),capture.output(sessionInfo()));paths<-sort(list.files(run,recursive=TRUE,full.names=TRUE),method="radix");write_text(file.path(run,"SHA256SUMS.txt"),paste(vapply(paths,sha_file,character(1)),substring(paths,nchar(run)+2),sep="  "));cat("Executed successfully: PAM audit; frozen M02 unchanged; no email output modified.\n")
}
tryCatch(main(),error=function(e){message(conditionMessage(e));quit(status=1L)})
