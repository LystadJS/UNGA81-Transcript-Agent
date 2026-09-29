#!/usr/bin/env Rscript
# Install a private R package library once, then record its actual versions with renv.
if(!l10n_info()[["UTF-8"]])invisible(try(Sys.setlocale("LC_CTYPE",if(.Platform$OS.type=="windows")"English_United States.utf8" else "C.UTF-8"),silent=TRUE))
args<-commandArgs(trailingOnly=TRUE);with_browser<-"--with-browser=true"%in%args;restore<-"--restore=true"%in%args
self<-sub("^--file=","",commandArgs()[grepl("^--file=",commandArgs())][1]);root<-normalizePath(dirname(self),winslash="/",mustWork=TRUE);setwd(root)
source("R/00_core.R");assert(getRversion()>="4.3.0","Install R >=4.3; R 4.6.1 is the tested reference")
lib<-file.path(root,"library",paste0("R-",R.version$major,".",strsplit(R.version$minor,".",fixed=TRUE)[[1]][1]),R.version$platform)
dir.create(lib,recursive=TRUE,showWarnings=FALSE);.libPaths(c(lib,.libPaths()))
options(repos=c(CRAN="https://cloud.r-project.org"),timeout=300)
core<-c("jsonlite","httr2","xml2","digest","base64enc","renv","Matrix","cluster","igraph");wanted<-c(core,if(with_browser)"chromote")
lock<-file.path(root,"renv.lock")
if(restore) {
  assert(file.exists(lock),"No installed-environment lock exists yet. Run setup.R once to install and freeze dependencies")
  if(!requireNamespace("renv",quietly=TRUE))install.packages("renv",lib=lib)
  need_packages("renv");renv::restore(project=root,library=lib,lockfile=lock,prompt=FALSE,clean=FALSE,retry=FALSE)
} else {
  if(file.exists(lock))stop("renv.lock already exists. Use --restore=true to restore exact versions; do not silently upgrade the frozen environment")
  missing<-wanted[!vapply(wanted,function(p)p%in%rownames(installed.packages(lib.loc=lib)),logical(1))]
  if(length(missing))install.packages(missing,lib=lib,dependencies=NA)
  need_packages(wanted)
  renv::snapshot(project=root,library=lib,type="all",lockfile=lock,prompt=FALSE)
}
need_packages(wanted);write_text("config/library_path.txt",lib)
json_write("config/runtime.local.json",list(rscript=normalizePath(file.path(R.home("bin"),"Rscript"),winslash="/",mustWork=FALSE),library=lib,R_version=as.character(getRversion())))
if(!file.exists("config/config.json"))file.copy("config/config.example.json","config/config.json")
write_text("validation/installed_sessionInfo.txt",capture.output(sessionInfo()))
csv_write("validation/installed_packages.csv",as.data.frame(installed.packages(lib.loc=lib)[,c("Package","Version","Built")],stringsAsFactors=FALSE))
cat("Setup complete. Actual installed versions are recorded in renv.lock.\nNext: Rscript doctor.R, then run the bundled replay before enabling live mode.\n")
