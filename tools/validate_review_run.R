# Revalidate a completed daily run after an audit-only review attachment.
a<-commandArgs(TRUE)
if(length(a)!=2)stop('Usage: Rscript tools/validate_review_run.R PACKAGE_ROOT RUN_DIRECTORY')
root<-normalizePath(a[1],winslash='/',mustWork=TRUE)
run<-normalizePath(a[2],winslash='/',mustWork=TRUE)
setwd(root)
libconfig<-file.path(root,'config/library_path.txt')
if(file.exists(libconfig)){lib<-readLines(libconfig,warn=FALSE);if(length(lib)&&dir.exists(lib[1])).libPaths(c(lib[1],.libPaths()))}
options(unbrief.minimal=FALSE,encoding='UTF-8')
for(f in list.files(file.path(root,'R'),pattern='^[0-9].*\\.R$',full.names=TRUE))sys.source(f,envir=globalenv())
cp<-readRDS(file.path(run,'checkpoint.rds'))
qa<-validate_output(root,run,cp$config)
stopifnot(qa$passed,qa$methods_accounted==42,qa$prerequisite_checks==133,qa$five_output_packet_contract=='passed')
cat(jsonlite::toJSON(qa,auto_unbox=TRUE),'\n')
