#!/usr/bin/env Rscript
# Rebuild any completed archived run without source retrieval or model calls.
if(!l10n_info()[["UTF-8"]])invisible(try(Sys.setlocale("LC_CTYPE",if(.Platform$OS.type=="windows")"English_United States.utf8" else "C.UTF-8"),silent=TRUE))
main<-function(){
  args<-commandArgs(trailingOnly=TRUE);opt<-list(input="",`run-id`="",minimal="false")
  for(a in args){if(!grepl("^--[^=]+=",a))stop("Use --input=RUN_DIRECTORY --run-id=NEW_ID --minimal=true|false");k<-sub("^--([^=]+)=.*$","\\1",a);if(!k%in%names(opt))stop("Unknown argument");opt[[k]]<-sub("^--[^=]+=","",a)}
  self<-sub("^--file=","",commandArgs()[grepl("^--file=",commandArgs())][1]);root<-normalizePath(dirname(self),winslash="/",mustWork=TRUE)
  input<-normalizePath(opt$input,winslash="/",mustWork=TRUE);setwd(root)
  if(file.exists("config/library_path.txt")){lib<-readLines("config/library_path.txt",warn=FALSE)[1];if(dir.exists(lib)).libPaths(c(lib,.libPaths()))}
  if(!opt$minimal%in%c("true","false"))stop("--minimal must be true or false")
  options(unbrief.minimal=identical(opt$minimal,"true"))
  for(f in list.files("R",pattern="^[0-9].*\\.R$",full.names=TRUE)){parse(f,encoding="UTF-8");source(f)}
  cat("Parsed successfully: R workflow modules.\n")
  if(!isTRUE(getOption("unbrief.minimal")))need_packages(c("jsonlite","digest","base64enc"))
  assert(file.exists(file.path(input,"checkpoint.rds"))&&file.exists(file.path(input,"SHA256SUMS.txt")),"Input is not a completed archived run")
  for(line in readLines(file.path(input,"SHA256SUMS.txt"),warn=FALSE)) {
    assert(grepl("^[0-9a-f]{64}  ",line),"Malformed archive checksum entry")
    hash<-substr(line,1,64);rel<-substring(line,67);assert(!grepl("^/|^[A-Za-z]:|(^|/)\\.\\.(/|$)",rel),"Unsafe archive path")
    assert(identical(sha_file(file.path(input,rel)),hash),paste("Archived checksum mismatch:",rel))
  }
  code<-read.csv(file.path(input,"code_manifest.csv"),stringsAsFactors=FALSE)
  for(i in seq_len(nrow(code))){assert(!grepl("^/|^[A-Za-z]:|(^|/)\\.\\.(/|$)",code$path[i]),"Unsafe generation-code path");assert(identical(sha_file(file.path(root,code$path[i])),code$sha256[i]),paste("Generation code/asset differs; restore the original workflow release:",code$path[i]))}
  cp<-readRDS(file.path(input,"checkpoint.rds"));assert(cp$brief$code_version==UNBRIEF_VERSION,"Workflow version mismatch")
  id<-if(nzchar(opt[["run-id"]]))opt[["run-id"]] else paste0("rebuild_",format(Sys.time(),"%Y%m%dT%H%M%S",tz="UTC"))
  assert(grepl("^[A-Za-z0-9_-]+$",id),"Unsafe run ID");run<-file.path(root,"output",cp$brief$date,id);assert(!dir.exists(run),"Cannot overwrite an archived run")
  lock<-file.path(root,"output/.run-lock");assert(dir.create(lock,showWarnings=FALSE),"Another run or stale lock exists");on.exit(unlink(lock,recursive=TRUE),add=TRUE)
  write_text(file.path(lock,"owner.txt"),paste0("pid=",Sys.getpid(),"; rebuild"));dir.create(run,recursive=TRUE)
  for(name in c("checkpoint.rds","brief.json","config_used.json","code_manifest.csv","data","audit","raw")){src<-file.path(input,name);if(file.exists(src)||dir.exists(src))assert(file.copy(src,run,recursive=dir.exists(src)),paste("Could not copy",name))}
  dir.create(file.path(run,"figures"));dir.create(file.path(run,"logs"))
  run_audit_figures(root,run)
  i2_rebuild_projection_images(root,run,cp)
  hc_run_figure(root,run)
  build_email(root,run,cp$config);qa<-validate_output(root,run,cp$config)
  identical_eml<-identical(sha_file(file.path(input,"daily_briefing.eml")),sha_file(file.path(run,"daily_briefing.eml")))
  json_write(file.path(run,"reproduction_check.json"),list(input_run=basename(input),no_network_used=TRUE,eml_byte_identical=identical_eml,interpretation=if(identical_eml)"Identical output bytes." else "Bytes differ; inspect platform/fonts/R environment. Do not claim exact reproduction."))
  finalize_run(root,run,cp$config)
  cat("Executed successfully: archived run rebuilt entirely in R. Byte-identical EML:",identical_eml,"\n")
}
tryCatch(main(),error=function(e){message(conditionMessage(e));quit(status=1)})
