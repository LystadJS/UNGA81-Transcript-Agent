# The only I2 ready producer: source-bound, quality-gated PCA for O3.
# PCoA never replaces PCA merely because it happens to look better.
I2_O3_PRODUCER<-"M05:tfidf-pca-display-v1"
I2_O3_IMAGE<-"Figure_4_Country_Discourse_Map.png"
i2_run_projection_figures<-function(root,run) {
  scripts<-c("M05"="Figure_4_Country_Discourse_Map.R","M06"="Figure_5_PCoA_Audit.R")
  names_png<-c("M05"=I2_O3_IMAGE,"M06"="Figure_5_PCoA_Audit.png")
  ledger<-list()
  for(id in names(scripts)) {
    artifact<-file.path(run,"audit/analytics/artifacts",paste0(id,".rds"))
    state<-"not_available";sha<-"";why<-"No valid numerical projection artifact was produced."
    if(file.exists(artifact)) {
      v<-readRDS(artifact);ok<-sum(apply(v$coordinates,1,function(z)all(is.finite(z))))>=3L
      if(ok) {
        log<-file.path(run,"logs",paste0(scripts[[id]],".log"));dir.create(dirname(log),recursive=TRUE,showWarnings=FALSE)
        code<-system2(file.path(R.home("bin"),"Rscript"),vapply(c("--vanilla",file.path(root,"R",scripts[[id]]),run),shQuote,character(1)),stdout=log,stderr=log)
        path<-file.path(run,"audit/figures",names_png[[id]])
        if(as.integer(code)==0L&&file.exists(path)){state<-"executed";sha<-sha_file(path);why<-"PNG rendered; every ISO3 label placed without detected label-box overlap."}
        else {state<-"failed";why<-"Standalone figure or label-layout validation failed; no inline image is eligible."}
      }
    }
    ledger[[length(ledger)+1L]]<-list(method_id=id,script=scripts[[id]],state=state,reason=why,
      image_path=paste0("audit/figures/",names_png[[id]]),sha256=sha,role=if(id=="M05")"eligible_only_after_O3_release" else "audit_only")
  }
  csv_write(file.path(run,"audit/analytics/projection_figure_ledger.csv"),ledger,c("method_id","script","state","reason","image_path","sha256","role"))
  invisible(ledger)
}
i2_o3_assessment <- function(cp,run,cutoff,root=getOption("unbrief.root",getwd())) {
  model_path<-"audit/analytics/artifacts/M05.rds";feature_path<-"audit/analytics/artifacts/M02.rds"
  if(!file.exists(file.path(run,model_path))||!file.exists(file.path(run,feature_path)))return(list(ready=FALSE,reason="Map withheld: no valid frozen PCA candidate is available. No artificial coordinates are generated."))
  f<-readRDS(file.path(run,feature_path));v<-readRDS(file.path(run,model_path))
  i2_validate_features(f,cp,root);i2_validate_projection(v,f,cp,root)
  snap<-readRDS(file.path(run,"audit/history/snapshot.rds"))
  assert(identical(f$source_snapshot_id,snap$snapshot_id)&&identical(f$source_as_of_cutoff,snap$as_of_cutoff),"Map uses another source snapshot")
  i2_feature_units(cp,snap)
  assert(parse_utc(v$created_at)<=parse_utc(cutoff)&&parse_utc(f$created_at)<=parse_utc(cutoff),"Map model/data use future availability")
  d<-read.csv(file.path(run,"data/pca_country_coordinates.csv"),stringsAsFactors=FALSE,check.names=FALSE)
  expected<-f$current$country$rows
  assert(identical(d$iso3,expected$iso3)&&isTRUE(all.equal(as.numeric(d$axis1),as.numeric(v$coordinates[,1]),tolerance=1e-10))&&
         isTRUE(all.equal(as.numeric(d$axis2),as.numeric(v$coordinates[,2]),tolerance=1e-10)),"Plot rows do not match validated model coordinates")
  tmp<-tempfile(fileext=".csv");on.exit(unlink(tmp),add=TRUE)
  csv_write(tmp,i2_projection_rows(v,f))
  assert(identical(sha_file(tmp),sha_file(file.path(run,"data/pca_country_coordinates.csv"))),"Plot metadata or coordinate CSV differs from its model source")
  if(!isTRUE(v$quality$passed)) {
    q<-v$quality;var<-q$metrics$reference_variance_retained
    note<-if(is.finite(var))sprintf("The two-dimensional view retains %.1f%% of reference variation; the display policy requires at least %.0f%%. ",100*var,100*q$policy$min_reference_variance_retained) else ""
    # Keep the detailed 17-check ledger in the audit rather than reproducing it in the email.
    if(is.finite(var)&&var>=q$policy$min_reference_variance_retained)note<-"The numerical fit is retained in the audit. "
    return(list(ready=FALSE,reason=paste0("Map withheld. ",note,"Source, comparability, or projection-quality checks remain unmet; audit coordinates are not a published position map."),feature=f,projection=v))
  }
  l<-read.csv(file.path(run,"audit/analytics/projection_figure_ledger.csv"),stringsAsFactors=FALSE)
  l<-l[l$method_id=="M05",,drop=FALSE]
  if(nrow(l)!=1L||l$state!="executed")return(list(ready=FALSE,reason="Map withheld: the projection passed numerical checks, but its image or label-layout validation failed.",feature=f,projection=v))
  assert(identical(sha_file(file.path(run,l$image_path)),l$sha256),"PCA figure hash changed")
  layout<-read.csv(file.path(run,"data/pca_label_layout.csv"),stringsAsFactors=FALSE)
  assert(identical(layout$iso3,d$iso3)&&all(layout$label_placed),"Map label coverage failed")
  assert(png_size(read_bytes(file.path(run,l$image_path)))["width"]<=840,"Map image exceeds Outlook width cap")
  receipt<-list(contract="D1-I2-O3-PCA-display-v1",producer_id=I2_O3_PRODUCER,
    source_snapshot_id=snap$snapshot_id,source_as_of_cutoff=snap$as_of_cutoff,analysis_cutoff=cutoff,
    feature_artifact_sha256=sha_file(file.path(run,feature_path)),projection_artifact_sha256=sha_file(file.path(run,model_path)),
    reference_id=f$fitted_reference_id,model_id=v$model$model_id,projection_policy_sha256=sha_object(v$quality$policy),
    coordinates_sha256=sha_file(file.path(run,"data/pca_country_coordinates.csv")),image_sha256=l$sha256,
    release_scope="descriptive lexical geometry only",no_inferential_or_alignment_claim=TRUE,primary_is_not_selected_by_daily_best_fit=TRUE)
  list(ready=TRUE,feature=f,projection=v,receipt=receipt,image_ref=as.list(l[1,]),
    reason="The frozen PCA display passed its source, comparability, and projection-quality checks. Lexical similarity is not political agreement or a policy-position score.")
}
i2_build_o3 <- function(p,cp,run,cutoff) {
  assess<-i2_o3_assessment(cp,run,cutoff)
  p$reason<-assess$reason
  if(!isTRUE(assess$ready)){p$state<-"withheld";return(p)}
  f<-assess$feature;v<-assess$projection
  ref<-"audit/analytics/O3_release_receipt.json";json_write(file.path(run,ref),assess$receipt)
  immutable_write(file.path(run,"figures",I2_O3_IMAGE),read_bytes(file.path(run,assess$image_ref$image_path)))
  p$state<-"ready";p$model_id<-I2_O3_PRODUCER;p$model_role<-"primary";p$release_status<-"released_descriptive_display"
  p$definition_id<-"D1-I2-O3-PCA-display-v1"
  p$payload<-list(kind="country_discourse_map",method_id="M05",image_name=I2_O3_IMAGE,
    image_sha256=assess$receipt$image_sha256,reference_id=f$fitted_reference_id,
    metrics=v$quality$metrics,mode=v$comparison_mode,reference_event_cutoff=f$reference$event_cutoff,
    current_event_date=cp$brief$date,observations=nrow(v$coordinates),intervals="none; deterministic descriptive projection",
    receipt_path=ref,receipt_sha256=sha_file(file.path(run,ref)))
  paths<-c("audit/history/snapshot.rds","audit/analytics/artifacts/M02.rds","audit/analytics/artifacts/M05.rds",
           "data/pca_country_coordinates.csv","data/pca_display_checks.csv","data/pca_label_layout.csv",ref)
  p$evidence_refs<-lapply(paths,function(path)list(path=path,sha256=sha_file(file.path(run,path))))
  p$quality_checks<-setNames(lapply(D1_REQUIRED_CHECKS,function(check)list(state="pass",evidence_path=ref,evidence_sha256=p$payload$receipt_sha256)),D1_REQUIRED_CHECKS)
  p$model_provenance<-list(method_ledger_path="audit/analytics/method_ledger.csv",method_ledger_sha256=sha_file(file.path(run,"audit/analytics/method_ledger.csv")),
    released_model_count=1L,release_scope="descriptive_geometry_only",automatic_model_promotion=FALSE)
  p
}
i2_validate_ready_packet <- function(p,cp,run,cutoff) {
  assert(identical(p$slot_id,"O3")&&identical(p$model_id,I2_O3_PRODUCER)&&identical(p$model_role,"primary")&&identical(p$release_status,"released_descriptive_display"),"Only the validated M05 O3 display contract can be ready")
  a<-i2_o3_assessment(cp,run,cutoff)
  assert(isTRUE(a$ready),"Forged ready flag: recomputed source/projection/layout checks withhold this map")
  q<-p$payload
  assert(identical(q$kind,"country_discourse_map")&&identical(q$method_id,"M05")&&identical(q$image_name,I2_O3_IMAGE),"Wrong O3 payload/producer/image")
  assert(identical(q$metrics,a$projection$quality$metrics)&&identical(q$reference_id,a$feature$fitted_reference_id)&&identical(q$mode,a$projection$comparison_mode),"Published map metric/reference substitution")
  assert(identical(sort(names(q)),sort(c("kind","method_id","image_name","image_sha256","reference_id","metrics","mode","reference_event_cutoff","current_event_date","observations","intervals","receipt_path","receipt_sha256"))),"Unrecognized ready payload field")
  assert(identical(q$current_event_date,cp$brief$date)&&identical(q$reference_event_cutoff,a$feature$reference$event_cutoff)&&q$observations==nrow(a$projection$coordinates),"Published scope/date/count differs from the accepted artifact")
  expected_path<-"audit/analytics/O3_release_receipt.json"
  assert(identical(q$receipt_path,expected_path)&&identical(sha_file(file.path(run,expected_path)),q$receipt_sha256),"Missing/corrupt O3 release receipt")
  actual<-json_read(file.path(run,expected_path))
  assert(identical(json_minimal(actual),json_minimal(a$receipt)),"O3 receipt not derived from the current source and artifacts")
  assert(identical(q$image_sha256,a$receipt$image_sha256)&&identical(sha_file(file.path(run,"figures",q$image_name)),q$image_sha256),"Inline map bytes differ from accepted audit render")
  assert(identical(p$reason,a$reason),"Unsupported O3 narrative substituted")
  invisible(TRUE)
}
i2_inline_manifest <- function(packets,run) {
  p<-packets[["O3"]]
  if(!identical(p$state,"ready"))return(list())
  q<-p$payload;size<-png_size(read_bytes(file.path(run,"figures",q$image_name)))
  list(list(slot_id="O3",name=q$image_name,path=paste0("figures/",q$image_name),sha256=q$image_sha256,width=unname(size["width"]),height=unname(size["height"])))
}
i2_render_o3 <- function(p) {
  q<-p$payload;m<-q$metrics
  caption<-sprintf("%d available countries | reference date: %s | %s. The first two components retain %.1f%% of reference variation. No historical observations, confidence regions, or movement arrows are added.",q$observations,q$reference_event_cutoff,if(q$mode=="cross_sectional_bootstrap")"cross-sectional reference fit (same-day)" else "projection into a frozen reference",100*m$reference_variance_retained)
  html<-c(sprintf('<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0"><tr><td align="center"><img src="figures/%s" width="840" alt="Country discourse map: descriptive lexical PCA, not political alignment" style="display:block;width:100%%;max-width:840px;height:auto;border:0;"></td></tr></table>',I2_O3_IMAGE),p_html(html_escape(caption),11))
  list(html=html,plain=caption,image=I2_O3_IMAGE)
}
i2_rebuild_projection_images <- function(root,run,cp) {
  i2_run_projection_figures(root,run)
  for(im in cp$analytics$inline_images) {
    assert(identical(im$name,I2_O3_IMAGE)&&identical(im$slot_id,"O3"),"Unregistered rebuild image")
    from<-file.path(run,"audit/figures",im$name)
    assert(identical(sha_file(from),im$sha256),"Frozen display image not reproduced exactly")
    immutable_write(file.path(run,relative_path(im$path)),read_bytes(from))
  }
  invisible(TRUE)
}
