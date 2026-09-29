#!/usr/bin/env Rscript
# Read-only by default. Lock recovery requires an exact token and explicit local confirmation.
main<-function() {
  opts<-list(command="verify",store="history",`as-of`="",`event-date`="",out="",minimal="false",
             `owner-token`="",`confirm-owner-stopped`="false")
  for(arg in commandArgs(trailingOnly=TRUE)) {
    if(arg=="--help") {cat("Rscript history_tool.R --command=verify|query|labels|inspect-lock|release-lock --store=history\n--as-of=YYYY-MM-DDTHH:MM:SSZ --event-date=YYYY-MM-DD --out=output/query.csv --minimal=true|false\nrelease-lock additionally requires --owner-token=EXACT_TOKEN --confirm-owner-stopped=true\n");return(invisible(NULL))}
    if(!grepl("^--[^=]+=",arg))stop("Use --name=value options")
    key<-sub("^--([^=]+)=.*$","\\1",arg);if(!key%in%names(opts))stop("Unknown option: ",key)
    opts[[key]]<-sub("^--[^=]+=","",arg)
  }
  self<-sub("^--file=","",commandArgs()[grepl("^--file=",commandArgs())][1])
  root<-normalizePath(dirname(self),winslash="/",mustWork=TRUE);setwd(root)
  if(file.exists("config/library_path.txt")){lib<-readLines("config/library_path.txt",warn=FALSE)[1];if(dir.exists(lib)).libPaths(c(lib,.libPaths()))}
  if(!opts$minimal%in%c("true","false"))stop("Invalid --minimal value")
  options(unbrief.minimal=opts$minimal=="true")
  for(f in list.files("R",pattern="^[0-9].*\\.R$",full.names=TRUE)){parse(f,encoding="UTF-8");source(f)}
  cat("Parsed successfully: native-R historical-store modules.\n")
  if(!isTRUE(getOption("unbrief.minimal")))need_packages(c("jsonlite","digest"))
  store<-file.path(root,relative_path(opts$store));assert(dir.exists(store),"Historical store does not exist")
  if(opts$command=="verify") {cat(json_text(history_verify(store)),"\n");return(invisible(TRUE))}
  if(opts$command%in%c("inspect-lock","release-lock")) {
    lock<-file.path(store,".write-lock");assert(dir.exists(lock),"No history write lock exists")
    owner<-json_read(file.path(lock,"owner.json"))
    if(opts$command=="inspect-lock"){cat(json_text(owner),"\n");return(invisible(TRUE))}
    assert(identical(opts[["confirm-owner-stopped"]],"true")&&identical(opts[["owner-token"]],owner$token),"Explicit stopped-owner confirmation and matching token are required")
    # No remote process termination and no assumption that a saved PID is still meaningful.
    dest<-file.path(store,paste0("recovered_lock_",substr(owner$token,1,16)))
    assert(!dir.exists(dest)&&file.rename(lock,dest),"Could not preserve and release the confirmed stale lock")
    cat("Preserved owner evidence in",dest,". No process was terminated.\n");return(invisible(TRUE))
  }
  assert(opts$command%in%c("query","labels"),"Unknown history command")
  assert(nzchar(opts[["as-of"]])&&nzchar(opts[["event-date"]]),"As-of and event-date cutoffs are both required")
  result<-if(opts$command=="query")history_index(store,opts[["as-of"]],opts[["event-date"]]) else history_labels(store,opts[["as-of"]],opts[["event-date"]])
  if(nzchar(opts$out)) {
    path<-file.path(root,relative_path(opts$out));assert(!file.exists(path),"Refusing to overwrite an existing historical query export")
    if(opts$command=="query")csv_write(path,result) else json_write(path,result)
    cat("Executed successfully:",length(if(is.data.frame(result))seq_len(nrow(result)) else result),"records exported to",path,"\n")
  } else cat(json_text(result),"\n")
}
tryCatch(main(),error=function(e){message(conditionMessage(e));quit(status=1)})
