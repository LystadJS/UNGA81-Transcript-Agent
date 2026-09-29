# D1-I2 publication boundary. Only the source-bound M05 descriptive O3 factory
# can release a map; flags alone cannot promote any numerical model.
D1_SLOT_IDS <- paste0("O", 1:5)
D1_SLOT_TITLES <- c("Fixed-topic monitor", "Emerging issues", "Country discourse map",
                    "Rhetorical movement", "Discourse-network changes")
D1_REQUIRED_CHECKS <- c("source", "time_cutoff", "version", "definition", "coverage", "validation", "uncertainty", "neutrality")
D1_READY_PRODUCERS <- "M05:tfidf-pca-display-v1"
validate_analytics_config <- function(cfg) {
  a <- cfg$analytics
  assert(is.list(a) && identical(a$design,"D1") && identical(a$implementation,"I2"), "Use the D1-I2 configuration; old configs are not silently upgraded")
  assert(identical(a$engine,"base_r_registry") && identical(a$history_backend,"rds_append_only_v1"),"Unimplemented orchestration/history backend selected")
  assert(identical(a$allow_ready_packets,FALSE) && identical(a$allow_automatic_promotion,FALSE),"Direct/automatic model promotion is not permitted; only a validated task-specific publication contract can release a result")
  for(k in c("history_dir","method_cache_dir","feature_reference_dir","projection_reference_dir"))relative_path(a[[k]])
  assert(a$feature_reference_mode%in%c("bootstrap_then_frozen","frozen_only"),"Invalid feature-reference mode")
  assert(grepl("^[A-Za-z0-9_-]+$",str1(a$feature_reference_namespace)),"Unsafe/missing feature-reference namespace")
  assert(is.numeric(a$max_store_objects_per_query)&&a$max_store_objects_per_query>0&&
         is.numeric(a$max_raw_blob_bytes)&&a$max_raw_blob_bytes>0,"Invalid historical store resource caps")
  invisible(TRUE)
}
d1_build_packets <- function(cp, accounting, snapshot, run) {
  n <- length(cp$speeches); context <- accounting$context
  reasons <- c(
    if(!n)"No qualifying country text is available for assessment." else "No released issue classifier is available. Rule candidates and inherited codes remain in the audit; they are not published presence or absence decisions.",
    if(!context$prior_nonreplay_statement_versions) "Insufficient comparable history to assess emergence; topic-discovery models are not yet released." else "Historical texts exist, but comparable topic baselines and validated discovery models are not yet available.",
    "Map withheld: no frozen representation and validated projection are available. No artificial coordinates are generated.",
    if(!context$prior_country_genre_candidates) "No comparable prior observation is established. Movement models and representation checks are not yet released." else "Potential prior observations exist, but compatible representation and genre/issue comparisons have not passed validation.",
    "No comparable prior network is established. Edge definitions, matched coverage, and network-change models are not yet released.")
  paths <- c("audit/history/snapshot.rds","audit/analytics/readiness_context.json","audit/analytics/method_ledger.csv")
  refs <- lapply(paths,function(p)list(path=p,sha256=sha_file(file.path(run,p))))
  packets <- lapply(seq_along(D1_SLOT_IDS),function(i) {
    list(slot_id=D1_SLOT_IDS[i],title=D1_SLOT_TITLES[i],state="not_ready",reason=reasons[i],payload=NULL,
      source_snapshot_id=snapshot$snapshot_id,source_as_of_cutoff=snapshot$as_of_cutoff,
      as_of_cutoff=accounting$as_of_cutoff,model_id="",model_role="none",definition_id="D1-I2-publication-v1",
      release_status="unreleased",is_forecast=FALSE,evidence_refs=refs,
      quality_checks=setNames(lapply(D1_REQUIRED_CHECKS,function(check)list(
        state=if(check%in%c("coverage","uncertainty","neutrality","time_cutoff","definition"))"pass_for_unavailable_state" else "not_established_for_publication",
        evidence_path=paths[if(check=="source")1L else if(check=="validation")3L else 2L],
        evidence_sha256=refs[[if(check=="source")1L else if(check=="validation")3L else 2L]]$sha256)),D1_REQUIRED_CHECKS),
      model_provenance=list(method_ledger_path=paths[3],method_ledger_sha256=refs[[3]]$sha256,
                            released_model_count=0L,automatic_promotion=FALSE))
  })
  names(packets)<-D1_SLOT_IDS
  if(n>0L)packets[["O3"]]<-i2_build_o3(packets[["O3"]],cp,run,accounting$as_of_cutoff)
  d1_validate_packets(packets,run,cp,accounting$as_of_cutoff)
  packets
}
d1_validate_packets <- function(packets, run, cp, cutoff) {
  assert(is.list(packets)&&length(packets)==5L,"Exactly five analytical packets are required")
  ids<-unname(vapply(packets,function(p)str1(p$slot_id),character(1)))
  assert(identical(ids,D1_SLOT_IDS)&&!anyDuplicated(ids),"Missing, duplicate, reordered or sixth analytical output rejected")
  snapshot<-readRDS(file.path(run,"audit/history/snapshot.rds"))
  for(i in seq_along(packets)) {
    p<-packets[[i]]
    assert(identical(p$source_snapshot_id,snapshot$snapshot_id)&&identical(p$source_as_of_cutoff,snapshot$as_of_cutoff),"Packet source snapshot identity/cutoff mismatch")
    assert(identical(p$title,D1_SLOT_TITLES[i]),"Analytical title cannot create a disguised extra section")
    assert(p$state%in%c("ready","not_ready","not_updated","failed","withheld"),"Invalid packet state")
    assert(parse_utc(p$as_of_cutoff)<=parse_utc(cutoff) && parse_utc(p$source_as_of_cutoff)<=parse_utc(p$as_of_cutoff),"Packet uses future provenance")
    assert(!isTRUE(p$is_forecast),"Forecast publication is disabled")
    if(p$state=="ready") {
      assert(p$model_id%in%D1_READY_PRODUCERS,"No ready producer for this task; flags alone cannot release a result")
      i2_validate_ready_packet(p,cp,run,cutoff)
    } else {
      assert(nzchar(str1(p$reason)) && is.null(p$payload),"Unavailable packets need a reason and cannot carry stale numerical payloads")
      assert(identical(p$release_status,"unreleased") && identical(p$model_role,"none") && !nzchar(p$model_id),"Unavailable packet falsely claims a released model")
    }
    assert(identical(names(p$quality_checks),D1_REQUIRED_CHECKS),"Publication check schema mismatch")
    assert(length(p$evidence_refs)>0,"Publication decision lacks provenance")
    for(ref in p$evidence_refs)assert(identical(sha_file(file.path(run,relative_path(ref$path))),ref$sha256),"Publication evidence is missing or changed")
    for(check in p$quality_checks)assert(identical(sha_file(file.path(run,relative_path(check$evidence_path))),check$evidence_sha256),"Publication check is not bound to an actual artifact")
  }
  invisible(TRUE)
}
d1_render_packets <- function(cp,run,cfg) {
  a<-cp$analytics
  assert(is.list(a)&&identical(a$design,"D1")&&identical(a$implementation,"I2"),"Five-slot analytics checkpoint missing")
  d1_validate_packets(a$report_packets,run,cp,a$as_of_cutoff)
  # No directory scans, no automatic inclusion of arbitrary model figures.
  assert(identical(a$inline_images,i2_inline_manifest(a$report_packets,run)),"Unregistered, missing or changed inline analytical image")
  html<-plain<-images<-character();n<-length(cp$speeches)
  for(i in seq_along(a$report_packets)) {
    p<-a$report_packets[[i]];title<-paste0(i,". ",p$title)
    html<-c(html,sprintf('<table class="analytics-slot" id="analytics-%s" role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0" style="width:100%%;margin:0 0 16px 0;border-top:2px solid #002D74;"><tr><td style="padding:10px 0 0 0;"><div class="analytics-title" style="font-family:Georgia,serif;font-size:19px;line-height:25px;font-weight:bold;color:#062135;margin:0 0 6px 0;">%s</div><div class="analytics-state" style="font-family:Arial,Helvetica,sans-serif;font-size:10px;line-height:15px;color:#667085;margin:0 0 5px 0;">%s</div>',p$slot_id,html_escape(title),toupper(gsub("_"," ",p$state,fixed=TRUE))))
    plain<-c(plain,toupper(title),paste("STATUS:",gsub("_"," ",p$state,fixed=TRUE)))
    if(p$slot_id=="O1") {
      topics<-c("Iran","Cuba","Ukraine","AI")
      status<-if(n)"Not assessed by a released model" else "No qualifying country text"
      html<-c(html,'<table class="fixed-watchlist" role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;background:#F6F8FA;margin-bottom:8px;">')
      for(j in seq_along(topics))html<-c(html,sprintf('<tr><td class="fixed-topic" style="width:20%%;padding:7px 9px;border-bottom:1px solid #D6DEE7;font-size:13px;font-weight:bold;color:#002D74;">%s</td><td style="padding:7px 9px;border-bottom:1px solid #D6DEE7;font-size:12px;line-height:18px;color:#202B38;">%s</td></tr>',topics[j],status))
      html<-c(html,"</table>",p_html(html_escape(sprintf("%d country texts available. Unassessed is not absent; missing source texts are reported separately in the coverage note.",n)),11))
      plain<-c(plain,paste(topics,status,sep=": "),sprintf("Available country texts: %d. Unassessed is not absent.",n))
    }
    if(p$state=="ready") {
      plot<-i2_render_o3(p);html<-c(html,plot$html);plain<-c(plain,plot$plain);images<-c(images,plot$image)
    }
    html<-c(html,p_html(html_escape(p$reason),12),"</td></tr></table>")
    plain<-c(plain,p$reason,"")
  }
  list(html=html,plain=plain,images=images)
}
