# Staged execution for methods whose diagnostic gates can only be measured AFTER fitting.
# The final ledger is exhaustive; a withheld candidate remains an inspectable artifact.
I2_METHOD_IDS<-c("M02","M05","M06")
i2_managed_gates <- function(id,value,feature,context,error="") {
  mk<-function(state,cls,reason)list(state=state,blocker_class=cls,reason=reason)
  if(id=="M02")return(list(source_text=gate_decision("source_text",context),
    frozen_vocabulary=if(!is.null(value))mk("pass","version",paste("Source-verified immutable vocabulary/IDF",value$fitted_reference_id)) else
      mk("unestablished","version",paste("No valid frozen feature artifact was produced.",error))))
  fgood<-!is.null(feature)
  refok<-fgood && feature$reference$event_cutoff<=context$event_cutoff &&
    parse_utc(feature$reference$source_as_of_cutoff)<=parse_utc(context$as_of_cutoff)
  g<-list()
  g[[if(id=="M05")"numeric_features" else "distance_matrix"]]<-if(fgood)mk("pass","data",if(id=="M05")"Verified frozen sparse TF-IDF features are available; matrix sizes are capped." else "Euclidean chord distances derive from the same verified L2-normalized features; missing vectors remain unavailable.") else mk("fail","data","M02 did not provide a valid current feature artifact.")
  g$reference_cutoff<-if(refok)mk("pass","version","Reference event and source-availability cutoffs precede or equal the reporting information set; same-day bootstrap is labeled cross-sectional.") else mk("unestablished","version","No time-compatible feature reference is established.")
  g$projection_diagnostics<-if(is.null(value))mk("unestablished","quality",paste("No fitted projection/diagnostic artifact.",error)) else
    if(isTRUE(value$quality$passed))mk("pass","quality","All predeclared source, coverage and numerical display gates passed. These are display checks, not semantic or inferential validation.") else
      mk("fail","quality",paste("Fitted candidate retained but withheld:",paste(value$quality$checks$check[value$quality$checks$state!="pass"],collapse=", ")))
  g
}
i2_read_feature_dependency <- function(run) {
  path<-file.path(run,"audit/analytics/artifacts/M02.rds")
  if(!file.exists(path))return(NULL)
  readRDS(path)
}
i2_run_managed <- function(id,cp,root,run,snapshot,context,available,clock=utc_now) {
  artifact_ref<-artifact_hash<-artifact_time<-error_log<-"";value<-feature<-NULL
  status<-"failed";reason<-"";fit_status<-"blocked";stage<-"preflight";error<-""
  if(id%in%c("M05","M06"))feature<-i2_read_feature_dependency(run)
  result<-tryCatch({
    if(!all(available))i2_abort("dependency","Actual R adapter dependencies are missing; see dependency ledger")
    if(context$statement_records==0L)i2_abort("data","No current source statements; no feature/projection fit attempted")
    if(id!="M02"&&is.null(feature))i2_abort("data","M02 did not produce an eligible feature artifact")
    if(!is.null(feature))i2_validate_features(feature,cp,root)
    stage<-"fit_or_reuse_reference_then_transform"
    value<-if(id=="M02")i2_feature_execute(cp,root,run,snapshot,clock) else i2_projection_execute(feature,cp,root,run,id,clock)
    if(id=="M02")i2_validate_features(value,cp,root) else i2_validate_projection(value,feature,cp,root)
    artifact_ref<-paste0("audit/analytics/artifacts/",id,".rds")
    bytes<-serialize(value,NULL,version=3);immutable_write(file.path(run,artifact_ref),bytes)
    artifact_hash<-sha_raw(bytes);artifact_time<-value$created_at
    if(id=="M02")i2_write_feature_tables(value,run) else i2_write_projection_tables(value,feature,run)
    fit_status<-value$reference_operation
    status<-if(id!="M02"&&!value$quality$passed)"withheld_quality" else "executed"
    reason<-if(id=="M02")paste("Frozen TF-IDF",fit_status,"and source-bound daily transform executed; cosine is not agreement or a probability.") else
      if(status=="withheld_quality")paste("Projection fitted/projected and retained in the audit; failed display gates:",paste(value$quality$checks$check[value$quality$checks$state!="pass"],collapse=", ")) else
        if(id=="M06")"PCoA fit/projected and diagnostics passed; challenger remains audit-only, with no automatic replacement of PCA." else
          "PCA fit/projected and passed the frozen descriptive-display gates; the O3 factory independently validates source and artifact bindings."
    TRUE
  },error=function(e){
    error<<-conditionMessage(e)
    kind<-sub("^d1_i2_","",class(e)[startsWith(class(e),"d1_i2_")][1])
    status<<-if(length(kind)==1L&&!is.na(kind)&&kind%in%c("resources","data","dependency","version"))paste0("blocked_",kind) else if(identical(kind,"quality"))"withheld_quality" else "failed"
    reason<<-paste("No valid",id,"candidate was delivered:",conditionMessage(e))
    fit_status<<-"no_valid_fit_delivered"
    if(nzchar(artifact_ref)&&file.exists(file.path(run,artifact_ref))) {
      # Retain failed bytes as an incident, never as a valid candidate.
      target<-file.path(run,"audit/analytics/errors",paste0(id,"_invalid_candidate.rds"))
      dir.create(dirname(target),recursive=TRUE,showWarnings=FALSE);file.rename(file.path(run,artifact_ref),target)
    }
    artifact_ref<<-artifact_hash<<-artifact_time<<-"";value<<-NULL
    error_log<<-paste0("audit/analytics/errors/",id,".txt");write_text(file.path(run,error_log),conditionMessage(e));FALSE
  })
  gr<-i2_managed_gates(id,value,feature,context,error)
  path<-paste0("audit/analytics/method_proofs/",id,".json")
  proof<-list(schema="D1-I2-method-proof-v1",method_id=id,context=context,collection=cp$brief$collection,
    root_policy_version="D1-I2",artifact_ref=artifact_ref,artifact_sha256=artifact_hash,
    feature_artifact_ref=if(!is.null(feature))"audit/analytics/artifacts/M02.rds" else "",
    feature_artifact_sha256=if(!is.null(feature))sha_object(feature) else "",error=error,
    actual_stage=stage,numerical_result_retained=nzchar(artifact_ref),terminal_status=status,
    fit_status=fit_status,gates=gr,preflight_and_postfit_are_distinct=TRUE)
  json_write(file.path(run,path),proof)
  gate_rows<-lapply(names(gr),function(g)c(list(method_id=id,gate=g),gr[[g]],list(evidence_path=path,evidence_sha256=sha_file(file.path(run,path)))))
  list(status=status,reason=reason,stage=stage,fit_status=fit_status,artifact_ref=artifact_ref,
    artifact_hash=artifact_hash,artifact_time=artifact_time,error_log=error_log,gr=gate_rows,value=value,
    model_release_status=if(id=="M02")"representation_only" else if(id=="M06")"challenger_audit_only" else if(!is.null(value)&&value$quality$passed)"display_contract_eligible" else "unreleased")
}
i2_validate_method_proof <- function(proof,run,root=NULL) {
  id<-proof$method_id;assert(id%in%I2_METHOD_IDS,"Unknown staged method proof")
  if(is.null(root)) {
    # Report-local references are self-contained; the executing workflow supplies policy code.
    root<-getOption("unbrief.root",getwd())
  }
  value<-feature<-NULL
  if(nzchar(proof$feature_artifact_ref)) {
    assert(identical(proof$feature_artifact_ref,"audit/analytics/artifacts/M02.rds"),"Wrong staged dependency")
    assert(identical(sha_file(file.path(run,proof$feature_artifact_ref)),proof$feature_artifact_sha256),"Staged dependency hash mismatch")
    feature<-readRDS(file.path(run,proof$feature_artifact_ref));i2_validate_features(feature,NULL,root)
  }
  if(nzchar(proof$artifact_ref)) {
    assert(identical(proof$artifact_ref,paste0("audit/analytics/artifacts/",id,".rds")),"Unexpected staged artifact path")
    assert(identical(sha_file(file.path(run,proof$artifact_ref)),proof$artifact_sha256),"Staged artifact hash mismatch")
    value<-readRDS(file.path(run,proof$artifact_ref))
    if(id=="M02")i2_validate_features(value,NULL,root) else i2_validate_projection(value,feature,list(brief=list(collection=proof$collection)),root)
  }
  expected<-i2_managed_gates(id,value,feature,proof$context,str1(proof$error))
  # JSON number types are not compared; states, reasons and exact artifact bytes are.
  for(g in names(expected)) {
    assert(g%in%names(proof$gates)&&identical(proof$gates[[g]],expected[[g]]),"Staged gate does not match independently recomputed evidence")
  }
  expected
}
i2_update_context <- function(context,value,run) {
  context$numerical_feature_artifacts<-2L;context$trained_reference_artifacts<-1L
  context$feature_artifact<-list(path="audit/analytics/artifacts/M02.rds",sha256=sha_object(value),reference_id=value$fitted_reference_id)
  context
}
i2_context_feature_decision <- function(gate,context) {
  if(is.null(context$feature_artifact)||!gate%in%c("numeric_features","distance_matrix","frozen_vocabulary","reference_cutoff"))return(NULL)
  list(state="pass",blocker_class=if(gate%in%c("frozen_vocabulary","reference_cutoff"))"version" else "data",
    reason=paste("M02 supplied source-verified frozen TF-IDF artifacts for this snapshot; reference",context$feature_artifact$reference_id,". This does not validate any downstream fit."))
}
i2_validate_context <- function(context,run) {
  if(!is.null(context$feature_artifact)) {
    ref<-context$feature_artifact
    assert(identical(ref$path,"audit/analytics/artifacts/M02.rds")&&identical(sha_file(file.path(run,ref$path)),ref$sha256),"Readiness feature evidence missing/corrupt")
    value<-readRDS(file.path(run,ref$path));i2_validate_features(value)
    assert(identical(value$fitted_reference_id,ref$reference_id)&&identical(value$source_snapshot_id,context$snapshot_id),"Readiness context uses features from a different snapshot")
  }
  invisible(TRUE)
}
