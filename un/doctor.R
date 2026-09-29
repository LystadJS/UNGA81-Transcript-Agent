#!/usr/bin/env Rscript
self<-sub("^--file=","",commandArgs()[grepl("^--file=",commandArgs())][1]);root<-normalizePath(dirname(self),winslash="/",mustWork=TRUE);setwd(root)
source("R/00_core.R");if(file.exists("config/library_path.txt")){lib<-readLines("config/library_path.txt",warn=FALSE)[1];if(dir.exists(lib)).libPaths(c(lib,.libPaths()))}
packages<-c("jsonlite","httr2","xml2","digest","base64enc","renv","chromote")
checks<-list(R_version=as.character(getRversion()),R_reference="4.6.1",PNG=capabilities("png"),timezone=Sys.timezone(),reporting_timezone="America/New_York",api_key_available=nzchar(Sys.getenv("OPENAI_API_KEY")),api_key_value="never logged",native_outlook_tested=FALSE)
checks$packages<-lapply(packages,function(p)list(package=p,installed=requireNamespace(p,quietly=TRUE),version=if(requireNamespace(p,quietly=TRUE))as.character(packageVersion(p)) else NULL));checks$packages[[length(packages)]]$optional<-TRUE
checks$config_present<-file.exists("config/config.json");checks$dependency_lock_present<-file.exists("renv.lock")
if("--network=true"%in%commandArgs(trailingOnly=TRUE)) {
  need_packages(c("httr2","jsonlite"));d<-as.character(as.Date(format(Sys.time(),"%Y-%m-%d",tz="America/New_York"))-1)
  result<-tryCatch(http_raw(paste0("https://transcripts.un.org/en/meetings.json?date=",d,"&xlang=1&page=1"),list(timeout_seconds=30,max_attempts=1,max_response_bytes=25000000)),error=function(e)e)
  checks$un_endpoint<-if(inherits(result,"error"))list(passed=FALSE,error=conditionMessage(result)) else list(passed=TRUE,bytes=length(result))
} else checks$un_endpoint<-list(passed=NULL,note="Not tested; use --network=true for a read-only UN inventory request")
json_write("validation/doctor.json",checks);cat(json_text(checks),"\n")
cat("An API key stored using Set-ApiKey.ps1 is loaded only by Run-Daily.ps1; a missing ambient key here is not an error.\n")
