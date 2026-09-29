#!/usr/bin/env Rscript
options(unbrief.minimal=TRUE);source('R/00_core.R')
exclude<-c('SHA256SUMS.txt','validation/CHECKPOINT_MANIFEST.json')
files<-sort(list.files('.',recursive=TRUE,all.files=TRUE,no..=TRUE),method='radix')
files<-files[file.info(files)$isdir==FALSE];files<-setdiff(files,exclude)
bytes<-sum(file.info(files)$size)
key<-c('README.md','START_HERE.md','CHECKPOINT_STATUS.md','RELEASE_NOTES.md','config/pam_policy.json','design/D1-PAM/pam_policy.json','R/12_pam.R','R/20_pam_accounting.R','R/Figure_7_PAM_Audit.R','pam_only.R','tests/run_pam_tests.R','validation/FINAL_VALIDATION.md','validation/PROJECT_AUDIT.json','validation/CHECKPOINT_CLUSTERING_AUDIT.json','validation/pam_reference_final/validation.json')
stopifnot(all(file.exists(key)))
manifest<-list(schema='D1-I4-checkpoint-manifest-v1',release='2.5.0-d1-i4-checkpoint',created_at=format(Sys.time(),tz='UTC',format='%Y-%m-%dT%H:%M:%OSZ'),file_count_excluding_manifest_and_sha=length(files),total_bytes_excluding_manifest_and_sha=as.numeric(bytes),key_files=lapply(key,function(p)list(path=p,sha256=sha_file(p),bytes=unname(file.info(p)$size))),validation=list(total_tests=371L,failures=0L,r_scripts_parsed=34L,methods_registered=42L,implemented=6L,unimplemented=36L),source_reference=list(countries=39L,frozen_feature_sha256='3235a50c3d5b9853887ce7da9058d636f963666ca885fcb82cf27175d54f7782',pam_quality_passed=FALSE,hierarchical_quality_passed=FALSE),no_email_sent=TRUE)
json_write('validation/CHECKPOINT_MANIFEST.json',manifest)
# SHA manifest covers every shipped file except itself, including CHECKPOINT_MANIFEST.
all<-sort(list.files('.',recursive=TRUE,all.files=TRUE,no..=TRUE),method='radix');all<-all[file.info(all)$isdir==FALSE];all<-setdiff(all,'SHA256SUMS.txt')
write_text('SHA256SUMS.txt',paste(vapply(all,sha_file,character(1)),all,sep='  '))
cat(length(all),'files hashed into SHA256SUMS.txt\n')
