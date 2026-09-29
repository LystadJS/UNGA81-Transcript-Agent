#!/usr/bin/env Rscript
# Native R entry point; no Python is invoked.
if (!l10n_info()[["UTF-8"]]) invisible(try(Sys.setlocale("LC_CTYPE", if(.Platform$OS.type=="windows") "English_United States.utf8" else "C.UTF-8"),silent=TRUE))
main <- function() {
  args<-commandArgs(trailingOnly=TRUE)
  opt<-list(source="live",date="",config="config/config.json",input="",lookback="1",`run-id`="",`prepared-at`="",minimal="false")
  for(a in args){if(a=="--help"){cat("Rscript run_daily.R --source=live|local|replay --date=YYYY-MM-DD\n--input=PATH --config=PATH --lookback=1 --run-id=ID --prepared-at=UTC_TIMESTAMP\n--minimal=true is an explicit base-R offline replay/JSON-extractive option.\n");return(invisible(NULL))};if(!grepl("^--[^=]+=",a))stop("Use --name=value arguments");k<-sub("^--([^=]+)=.*$","\\1",a);if(!k%in%names(opt))stop("Unknown argument: ",k);opt[[k]]<-sub("^--[^=]+=","",a)}
  allargs<-commandArgs(trailingOnly=FALSE);self<-sub("^--file=","",allargs[grepl("^--file=",allargs)][1]);root<-normalizePath(dirname(self),winslash="/",mustWork=TRUE)
  old<-getwd();setwd(root);on.exit(setwd(old),add=TRUE)
  libconfig<-file.path(root,"config/library_path.txt");if(file.exists(libconfig)){lib<-readLines(libconfig,warn=FALSE);if(length(lib)&&dir.exists(lib[1])).libPaths(c(lib[1],.libPaths()))}
  if(getRversion()<"4.3.0")stop("R >=4.3 required; reference offline execution uses R 4.6.1")
  options(warn=1,encoding="UTF-8",unbrief.minimal=identical(opt$minimal,"true"))
  scripts<-list.files("R",pattern="^[0-9].*\\.R$",full.names=TRUE)
  for(f in c(scripts,list.files("R",pattern="^Figure_.*\\.R$",full.names=TRUE)))parse(f,encoding="UTF-8")
  cat("Parsed successfully: all R workflow and figure modules.\n")
  for(f in scripts)sys.source(f,envir=globalenv())
  assert(opt$source%in%c("live","local","replay"),"Invalid source mode");assert(opt$minimal%in%c("true","false"),"--minimal must be true or false")
  if(!file.exists(opt$config)&&opt$source=="replay")opt$config<-"config/config.example.json"
  cfg<-load_config(opt$config)
  if(isTRUE(getOption("unbrief.minimal"))) {
    assert(opt$source=="replay"||(opt$source=="local"&&cfg$analysis_mode=="extractive"&&grepl("\\.json$",opt$input,ignore.case=TRUE)),"Minimal mode supports offline replay or local JSON extractive processing only")
    cat("Explicit minimal R mode: archived/JSON sources only; package and network paths are not being tested.\n")
  } else {
    need_packages(c("jsonlite","digest","base64enc"))
    if(opt$source=="live"||cfg$analysis_mode=="openai"&&opt$source!="replay")need_packages("httr2")
    if(opt$source=="local"&&!grepl("\\.json$",opt$input,ignore.case=TRUE))need_packages("xml2")
  }
  if(!nzchar(opt$date))opt$date<-as.character(as.Date(format(Sys.time(),"%Y-%m-%d",tz=cfg$timezone))-1)
  parse_source_date(opt$date)
  lookback<-suppressWarnings(as.integer(opt$lookback));assert(!is.na(lookback)&&lookback>=1&&lookback<=14,"lookback must be 1-14")
  assert(opt$source=="live"||lookback==1,"Lookback applies only to live mode")
  assert(capabilities("png"),"R has no PNG device support")
  dir.create("output",showWarnings=FALSE);lock<-file.path(root,"output/.run-lock")
  assert(dir.create(lock,showWarnings=FALSE),"Another run or stale lock exists. Inspect its owner before removal; no concurrent run started")
  write_text(file.path(lock,"owner.txt"),c(paste0("pid=",Sys.getpid()),paste0("host=",Sys.info()[["nodename"]]),paste0("started=",format(Sys.time(),tz="UTC",usetz=TRUE))))
  on.exit(unlink(lock,recursive=TRUE),add=TRUE)
  budget<-new.env(parent=emptyenv());budget$used<-0L
  dates<-as.Date(opt$date)-rev(seq_len(lookback)-1L);failed_days<-character()
  for(j in seq_along(dates)) {
    day<-as.character(dates[j]);id<-if(nzchar(opt[["run-id"]]))opt[["run-id"]] else paste0(format(Sys.time(),"%Y%m%dT%H%M%S",tz="UTC"),"_",Sys.getpid())
    assert(grepl("^[A-Za-z0-9_-]+$",id),"Unsafe run ID");run<-file.path(root,"output",day,id);assert(!dir.exists(run),"Run exists; immutable run IDs cannot be overwritten")
    dir.create(run,recursive=TRUE);dir.create(file.path(run,"logs"));dir.create(file.path(run,"figures"))
    write_text(file.path(run,"R_sessionInfo.txt"),capture.output(sessionInfo()))
    result<-tryCatch({
      prepare_run(root,run,cfg,opt$source,day,opt$input,opt[["prepared-at"]],budget)
      prepare_analytics(root,run,cfg)
      run_audit_figures(root,run)
      qa<-finalize_run(root,run,cfg)
      if(isTRUE(cfg$generation$fail_on_review_required %||% TRUE)&&json_read(file.path(run,"brief.json"))$status=="REVIEW_REQUIRED")return_value<-"review_required" else return_value<-"complete"
      return_value
    },error=function(e){json_write(file.path(run,"FAILED.json"),list(error=conditionMessage(e),no_email_sent=TRUE)); if(!file.exists(file.path(run,"audit/analytics/method_ledger.csv"))) account_preparation_failure(root,run,cfg,conditionMessage(e)); message(conditionMessage(e));"failed"})
    if(result!="complete")failed_days<-c(failed_days,day)
  }
  cat("All files are local; no email has been sent.\n")
  if(length(failed_days)){cat("Days requiring attention:",paste(failed_days,collapse=", "),"\n");return(2L)}
  cat("Executed successfully: native R workflow completed.\n");0L
}
status<-tryCatch(main(),error=function(e){message(conditionMessage(e));1L})
if(is.numeric(status)&&status!=0)quit(status=status)
