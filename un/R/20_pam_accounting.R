pam_gates <- function(value,feature,error="") list(
  distance_matrix=list(state=if(is.null(feature))"unestablished" else "pass",blocker_class="data",reason=if(is.null(feature))"No verified M02 frozen feature artifact." else paste("Euclidean chord distance from all frozen features; reference",feature$fitted_reference_id)),
  cluster_stability=list(state=if(is.null(value))"unestablished" else if(value$quality$passed)"pass" else "fail",blocker_class="quality",reason=if(is.null(value))paste("No valid PAM/stability artifact.",error) else if(value$quality$passed)"Engineering PAM checks passed; M09 remains audit-only pending independent release validation." else paste("Fitted PAM retained; failed checks:",paste(value$quality$checks$check[value$quality$checks$state!="pass"],collapse=", "))))

pam_run_managed <- function(id,cp,root,run,snapshot,context,available,clock=utc_now) {
  assert(identical(id,"M09"),"Only M09 is implemented in PAM adapter")
  feature<-value<-NULL;artifact_ref<-artifact_hash<-artifact_time<-error_log<-error<-"";status<-"failed";stage<-"preflight";fit_status<-"no_valid_fit_delivered"
  tryCatch({
    if(!all(available))i2_abort("dependency","M09 requires Matrix, stats and cluster")
    path<-file.path(run,"audit/analytics/artifacts/M02.rds");if(!file.exists(path))i2_abort("data","M02 did not produce frozen feature artifact")
    feature<-readRDS(path);i2_validate_features(feature,cp,root);assert(identical(feature$source_snapshot_id,snapshot$snapshot_id),"M09 dependency uses another snapshot")
    stage<-"fit_current_pam_and_roster_sensitivity";value<-pam_execute(feature,cp,root,clock);pam_validate(value,feature,root,cp)
    artifact_ref<-"audit/analytics/artifacts/M09.rds";bytes<-serialize(value,NULL,version=3);immutable_write(file.path(run,artifact_ref),bytes);artifact_hash<-sha_raw(bytes);artifact_time<-value$created_at;pam_write_tables(value,run)
    status<-if(value$quality$passed)"executed" else "withheld_quality";fit_status<-value$fit_status
  },error=function(e){error<<-conditionMessage(e);kinds<-class(e)[startsWith(class(e),"d1_i2_")];kind<-if(length(kinds))sub("^d1_i2_","",kinds[1])else"";status<<-if(kind%in%c("data","resources","dependency","version"))paste0("blocked_",kind)else"failed";artifact_ref<<-artifact_hash<<-artifact_time<<-"";value<<-NULL;error_log<<-"audit/analytics/errors/M09.txt";write_text(file.path(run,error_log),error)})
  gr<-pam_gates(value,feature,error);reason<-if(is.null(value))paste("No valid M09 result:",error)else gr$cluster_stability$reason
  proof_path<-"audit/analytics/method_proofs/M09.json";proof<-list(schema="D1-PAM-method-proof-v1",method_id="M09",context=context,collection=cp$brief$collection,artifact_ref=artifact_ref,artifact_sha256=artifact_hash,feature_artifact_ref=if(is.null(feature))"" else "audit/analytics/artifacts/M02.rds",feature_artifact_sha256=if(is.null(feature))"" else sha_object(feature),error=error,terminal_status=status,actual_stage=stage,fit_status=fit_status,publication_eligible=FALSE,gates=gr)
  json_write(file.path(run,proof_path),proof);gate_rows<-lapply(names(gr),function(g)c(list(method_id=id,gate=g),gr[[g]],list(evidence_path=proof_path,evidence_sha256=sha_file(file.path(run,proof_path)))))
  list(status=status,reason=reason,stage=stage,fit_status=fit_status,artifact_ref=artifact_ref,artifact_hash=artifact_hash,artifact_time=artifact_time,error_log=error_log,gr=gate_rows,value=value,model_release_status="audit_only")
}

pam_validate_proof <- function(proof,run,root=getOption("unbrief.root",getwd())) {
  assert(identical(proof$method_id,"M09")&&identical(proof$publication_eligible,FALSE),"Wrong PAM proof")
  feature<-value<-NULL
  if(nzchar(proof$feature_artifact_ref)){path<-file.path(run,proof$feature_artifact_ref);assert(identical(sha_file(path),proof$feature_artifact_sha256),"M09 dependency hash mismatch");feature<-readRDS(path);i2_validate_features(feature,root=root);assert(identical(feature$source_snapshot_id,proof$context$snapshot_id),"M09 proof uses another snapshot")}
  if(nzchar(proof$artifact_ref)){assert(identical(proof$artifact_ref,"audit/analytics/artifacts/M09.rds")&&!is.null(feature),"Wrong M09 result path");assert(identical(sha_file(file.path(run,proof$artifact_ref)),proof$artifact_sha256),"M09 artifact hash mismatch");value<-readRDS(file.path(run,proof$artifact_ref));pam_validate(value,feature,root);assert(identical(json_minimal(value$collection),json_minimal(proof$collection)),"M09 source quality proof mismatch")}
  expected<-pam_gates(value,feature,str1(proof$error));assert(identical(names(expected),names(proof$gates)),"M09 prerequisite list changed");for(g in names(expected))assert(identical(expected[[g]],proof$gates[[g]]),"M09 readiness contradicts recomputed evidence");expected
}

pam_run_figure <- function(root,run) {
  output<-paste0("audit/figures/",PAM_IMAGE);dir.create(file.path(run,"audit/figures"),recursive=TRUE,showWarnings=FALSE)
  if(!file.exists(file.path(run,"audit/analytics/artifacts/M09.rds")))row<-list(script="Figure_7_PAM_Audit.R",state="blocked_data",artifact_ref="",sha256="",log="",inline_in_email=FALSE) else {
    log<-"logs/Figure_7_PAM_Audit.R.log";status<-tryCatch(system2(file.path(R.home("bin"),"Rscript"),vapply(c("--vanilla",file.path(root,"R/Figure_7_PAM_Audit.R"),run),shQuote,character(1)),stdout=file.path(run,log),stderr=file.path(run,log)),error=function(e){write_text(file.path(run,log),conditionMessage(e));1L});ok<-identical(as.integer(status),0L)&&file.exists(file.path(run,output));row<-list(script="Figure_7_PAM_Audit.R",state=if(ok)"executed" else "failed",artifact_ref=if(ok)output else "",sha256=if(ok)sha_file(file.path(run,output))else"",log=log,inline_in_email=FALSE)
  }
  csv_write(file.path(run,"audit/analytics/pam_figure_ledger.csv"),list(row),names(row));invisible(row)
}

pam_audit_block <- function(run) {
  path<-file.path(run,"audit/analytics/artifacts/M09.rds");if(!file.exists(path))return('<h2>PAM clustering — unavailable</h2><p>See M09 in the method ledger.</p>')
  v<-readRDS(path);n<-v$numerical;checks<-v$quality$checks;observed_text<-ifelse(is.na(checks$observed),"Not evaluable",checks$observed)
  rows<-vapply(seq_len(nrow(checks)),function(i)sprintf('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>',html_escape(checks$check[i]),html_escape(checks$state[i]),html_escape(observed_text[i]),html_escape(checks$criterion[i])),character(1))
  c('<h2>M09 PAM / k-medoids — audit only</h2>','<p>PAM uses the same full frozen TF-IDF Euclidean-chord distance matrix as M07. Medoids are inspectable lexical exemplars; clusters are not geopolitical blocs.</p>',sprintf('<p><strong>Selected audit cut:</strong> k=%d; medoids: %s.</p>',n$selected_k,html_escape(paste(n$selected_medoids,collapse=", "))),'<table><tr><th>Check</th><th>State</th><th>Observed</th><th>Criterion</th></tr>',rows,'</table>',if(file.exists(file.path(run,"audit/figures",PAM_IMAGE)))sprintf('<img src="audit/figures/%s" alt="Audit-only PAM clustering diagnostics" style="max-width:100%%;height:auto">',PAM_IMAGE)else'<p>Audit figure unavailable; inspect figure ledger.</p>')
}
