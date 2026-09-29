#!/usr/bin/env Rscript
# Read-only inspection of trusted local TF-IDF references. Never refits, switches,
# repairs, or changes an ACTIVE pointer. Do not load RDS from untrusted sources.
self<-sub("^--file=","",commandArgs()[grepl("^--file=",commandArgs())][1])
root<-normalizePath(dirname(self),winslash="/",mustWork=TRUE);setwd(root)
if(file.exists("config/library_path.txt")){lib<-readLines("config/library_path.txt",warn=FALSE)[1];if(dir.exists(lib)).libPaths(c(lib,.libPaths()))}
args<-commandArgs(trailingOnly=TRUE);getarg<-function(name,default){a<-args[startsWith(args,paste0("--",name,"="))];if(length(a)>1)stop("Duplicate argument");if(length(a))sub(paste0("^--",name,"="),"",a) else default}
options(unbrief.minimal=identical(getarg("minimal","false"),"true"),unbrief.root=root)
for(f in list.files("R",pattern="^[0-9].*\\.R$",full.names=TRUE))source(f)
command<-getarg("command","list");assert(command%in%c("list","verify"),"Use --command=list or --command=verify")
home<-file.path(root,relative_path(getarg("store","models/tfidf_references")));assert(dir.exists(home),"Reference directory does not exist")
active<-sort(list.files(home,pattern="^ACTIVE.rds$",recursive=TRUE,full.names=TRUE),method="radix");rows<-list()
for(p in active){assert(file.exists(paste0(p,".sha256"))&&identical(sha_file(p),trimws(read_text(paste0(p,".sha256")))),"Reference pointer missing/corrupt")
  ref<-object_read(dirname(p),readRDS(p));if(command=="verify")i2_validate_reference(ref,i2_policy(root,"feature"))
  rows[[length(rows)+1L]]<-list(reference_id=ref$reference_id,reference_event_cutoff=ref$event_cutoff,source_availability_cutoff=ref$source_as_of_cutoff,frozen_at=ref$frozen_at,unique_reference_texts=ref$vocabulary$n_unique_texts,vocabulary_size=length(ref$vocabulary$vocabulary),scope=paste(unlist(ref$scope$signature),collapse=" | "),state=if(command=="verify")"source_transform_verified" else "hash_verified_not_recomputed")}
print(rows_frame(rows,c("reference_id","reference_event_cutoff","source_availability_cutoff","frozen_at","unique_reference_texts","vocabulary_size","scope","state")));cat(sprintf("%s: %d trusted reference(s). No state changed.\n",command,length(rows)))
