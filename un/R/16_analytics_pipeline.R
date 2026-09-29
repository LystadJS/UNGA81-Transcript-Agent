# D1-I2 integration. The historical store and ledgers are a separate stage from
# summary generation and email presentation; research failures cannot add sections.
prepare_analytics <- function(root,run,cfg) {
  validate_analytics_config(cfg)
  cp<-readRDS(file.path(run,"checkpoint.rds"))
  assert(is.list(cp$observations),"Ungrouped source observations must be preserved before analytics")
  snapshot<-history_ingest(root,run,cfg,cp$observations,cp)
  accounting<-run_method_accounting(root,run,cfg,cp,snapshot)
  i2_run_projection_figures(root,run)
  hc_run_figure(root,run)
  pam_run_figure(root,run)
  packets<-d1_build_packets(cp,accounting,snapshot,run)
  cp$analytics<-list(design="D1",implementation="I2",hierarchical_extension="D1-HC-1",pam_extension="D1-PAM-1",as_of_cutoff=accounting$as_of_cutoff,
    source_as_of_cutoff=snapshot$as_of_cutoff,source_snapshot_id=snapshot$snapshot_id,
    history_commit_tip_sha256=snapshot$commit_tip_sha256,method_count=42L,gate_count=accounting$gate_count,
    report_packets=packets,inline_images=i2_inline_manifest(packets,run),
    model_artifacts=as.list(accounting$ledger$artifact_ref[nzchar(accounting$ledger$artifact_ref)]),
    released_model_count=sum(vapply(packets,function(p)p$state=="ready",logical(1))),
    current_scope="foundations + M01 + frozen M02 + PCA M05 / PCoA M06 + audit-only hierarchical M07 + PAM M09 + I5 lexical research M08/M31/M32/M33/M34/M36",no_method_registration_is_a_fit=TRUE)
  json_write(file.path(run,"audit/analytics/report_packets.json"),packets)
  saveRDS(packets,file.path(run,"audit/analytics/report_packets.rds"),version=3)
  saveRDS(cp,file.path(run,"checkpoint.rds"),version=3)
  csv_write(file.path(run,"audit/analytics/publication_decisions.csv"),lapply(packets,function(p)list(slot_id=p$slot_id,title=p$title,state=p$state,reason=p$reason,model_id=p$model_id,release_status=p$release_status,as_of_cutoff=p$as_of_cutoff)),c("slot_id","title","state","reason","model_id","release_status","as_of_cutoff"))
  cat(sprintf("ANALYTICS: %d statements archived; 42 methods accounted; %d prerequisite checks; exactly five report packets.\n",length(cp$observations),accounting$gate_count))
  invisible(cp$analytics)
}
D1_AUDIT_SCRIPTS<-c("Figure_1_Issue_Frequency.R","Figure_2_Regional_Heatmap.R","Figure_3_Issue_Network.R")
run_audit_figures<-function(root,run,runner=NULL) {
  dir.create(file.path(run,"audit/figures"),recursive=TRUE,showWarnings=FALSE)
  dir.create(file.path(run,"figures"),showWarnings=FALSE);dir.create(file.path(run,"logs"),showWarnings=FALSE)
  rows<-list()
  for(i in seq_along(D1_AUDIT_SCRIPTS)) {
    f<-D1_AUDIT_SCRIPTS[i];log<-file.path(run,"logs",paste0(f,".log"))
    code<-tryCatch({if(is.null(runner))system2(file.path(R.home("bin"),"Rscript"),args=vapply(c("--vanilla",file.path(root,"R",f),run),shQuote,character(1)),stdout=log,stderr=log) else runner(f,run,log)},error=function(e){write_text(log,conditionMessage(e));1L})
    src<-file.path(run,"figures",FIGURE_FILES[i]);dest<-file.path(run,"audit/figures",FIGURE_FILES[i])
    success<-identical(as.integer(code),0L)&&file.exists(src)
    if(success) {
      immutable_write(dest,read_bytes(src));assert(identical(sha_file(src),sha_file(dest)),"Audit figure copy mismatch");unlink(src)
    } else if(file.exists(src)) {
      immutable_write(paste0(dest,".failed-output"),read_bytes(src));unlink(src)
    }
    rows[[i]]<-list(script=f,state=if(success)"executed" else "failed",artifact_ref=if(success)paste0("audit/figures/",FIGURE_FILES[i]) else "",sha256=if(success)sha_file(dest) else "",log=paste0("logs/",basename(log)),inline_in_email=FALSE)
  }
  csv_write(file.path(run,"audit/analytics/audit_figure_ledger.csv"),rows,c("script","state","artifact_ref","sha256","log","inline_in_email"))
  invisible(rows)
}
append_d1_audit<-function(run,cp) {
  path<-file.path(run,"audit.html");html<-read_text(path)
  ledger<-read.csv(file.path(run,"audit/analytics/method_ledger.csv"),stringsAsFactors=FALSE,colClasses="character",na.strings=character(),fileEncoding="UTF-8")
  gates<-read.csv(file.path(run,"audit/analytics/gate_ledger.csv"),stringsAsFactors=FALSE,colClasses="character",na.strings=character(),fileEncoding="UTF-8")
  block<-c('<h1>Design D1 — clustering checkpoint</h1>',
    '<p>42 registrations are accounted for. M01, M02, M05, M06, M07, M08, M09, M31, M32, M33, M34 and M36 have executable adapters. I5 networks are lexical only; stance and temporal comparisons are unavailable. Clustering and network methods remain audit-only. The other 30 adapters remain unimplemented. Historical automatic labels are not training gold.</p>',
    '<p><a href="audit/analytics/method_ledger.csv">Method ledger</a> · <a href="audit/analytics/gate_ledger.csv">Prerequisite ledger</a> · <a href="data/history_observations.csv">As-of observation index</a> · <a href="data/m01_evidence.csv">M01 source evidence</a></p>',
    '<table><tr><th>Method</th><th>Actual state</th><th>Reason</th></tr>')
  for(i in seq_len(nrow(ledger))) {
    row<-ledger[i,];g<-gates[gates$method_id==row$method_id,,drop=FALSE]
    more<-paste(vapply(seq_len(nrow(g)),function(j)paste0(html_escape(g$gate[j]),": ",html_escape(g$state[j])," — ",html_escape(g$reason[j])),character(1)),collapse="<br>")
    block<-c(block,sprintf('<tr><td>%s — %s</td><td>%s</td><td>%s<details><summary>Every required gate</summary>%s</details></td></tr>',html_escape(row$method_id),html_escape(row$method),html_escape(row$terminal_status),html_escape(row$reason),more))
  }
  block<-c(block,'</table><h2>Five publication decisions</h2>')
  for(p in cp$analytics$report_packets)block<-c(block,sprintf('<h3>%s — %s</h3><p>%s: %s</p>',p$slot_id,html_escape(p$title),html_escape(p$state),html_escape(p$reason)))
  block<-c(block,'<h2>Legacy issue charts — audit only</h2><p>These charts retain the inherited/provisional coding qualifications; they are not additional analytical outputs in the email.</p>')
  for(f in FIGURE_FILES)if(file.exists(file.path(run,"audit/figures",f)))block<-c(block,sprintf('<p><img src="audit/figures/%s" alt="Audit-only issue chart" style="max-width:100%%;height:auto"></p>',f))
  block<-c(block,'<h2>Frozen TF-IDF and projection diagnostics</h2><p>PCA is the primary display candidate. PCoA is an audit challenger in the same Euclidean geometry, not independent confirmation. No reference is re-estimated during transformation.</p>')
  for(prefix in c("pca","pcoa")) {
    check_path<-file.path(run,paste0("data/",prefix,"_display_checks.csv"))
    if(file.exists(check_path)) {
      checks<-read.csv(check_path,stringsAsFactors=FALSE,na.strings=character())
      block<-c(block,paste0('<h3>',toupper(prefix),' — every release check</h3><table><tr><th>Check</th><th>State</th><th>Observed</th><th>Criterion</th></tr>'))
      for(j in seq_len(nrow(checks)))block<-c(block,paste0('<tr><td>',html_escape(checks$check[j]),'</td><td>',html_escape(checks$state[j]),'</td><td>',html_escape(as.character(checks$observed[j])),'</td><td>',html_escape(checks$criterion[j]),'</td></tr>'))
      block<-c(block,'</table>')
    }
  }
  for(f in c(I2_O3_IMAGE,"Figure_5_PCoA_Audit.png"))if(file.exists(file.path(run,"audit/figures",f)))block<-c(block,sprintf('<p><img src="audit/figures/%s" alt="Audit-only lexical projection" style="max-width:100%%;height:auto"></p>',f))
  block<-c(block,hc_audit_block(run),pam_audit_block(run))
  html<-sub("</body></html>",paste0(paste(block,collapse="\n"),"\n</body></html>"),html,fixed=TRUE)
  write_text(path,html)
}
validate_analytics_output<-function(root,run,cp) {
  a<-cp$analytics;validate_analytics_config(cp$config)
  assert(identical(a$design,"D1")&&identical(a$implementation,"I2"),"Analytics checkpoint version mismatch")
  registry<-read_d1_registry(root)
  ledger<-read.csv(file.path(run,"audit/analytics/method_ledger.csv"),stringsAsFactors=FALSE,colClasses="character",na.strings=character(),fileEncoding="UTF-8")
  gates<-read.csv(file.path(run,"audit/analytics/gate_ledger.csv"),stringsAsFactors=FALSE,colClasses="character",na.strings=character(),fileEncoding="UTF-8")
  validate_method_ledger(ledger,gates,registry,run,a$as_of_cutoff)
  d1_validate_packets(a$report_packets,run,cp,a$as_of_cutoff)
  stored<-readRDS(file.path(run,"audit/analytics/report_packets.rds"))
  assert(identical(stored,a$report_packets),"Rendered packets differ from archived packets")
  snapshot<-readRDS(file.path(run,"audit/history/snapshot.rds"))
  assert(identical(snapshot$snapshot_id,a$source_snapshot_id),"Packet/source snapshot mismatch")
  obs<-snapshot$observations
  if(nrow(obs))assert(all(vapply(obs$recorded_at,parse_utc,numeric(1))<=parse_utc(snapshot$as_of_cutoff))&&all(obs$event_date<=cp$brief$date),"Snapshot leaks future observations")
  list(methods_accounted=nrow(ledger),prerequisite_checks=nrow(gates),
       methods_executed=sum(ledger$terminal_status=="executed"),methods_reused=sum(ledger$terminal_status=="reused"),
       methods_not_implemented=sum(ledger$terminal_status=="not_implemented"),five_output_packet_contract="passed",
       ungrouped_statements_preserved=length(cp$observations),released_models=sum(vapply(a$report_packets,function(p)p$state=="ready",logical(1))),
       fitted_candidates_quality_withheld=sum(ledger$terminal_status=="withheld_quality"&nzchar(ledger$artifact_ref)),
       implemented_adapters=sum(ledger$implementation_status=="implemented"),
       projection_accuracy="Numerical reconstruction verified; no semantic, political-alignment or inferential validity is implied")
}
account_preparation_failure<-function(root,run,cfg,message) {
  # A collection/preparation exception must still leave one explicit row per method.
  registry<-read_d1_registry(root);now<-utc_now()
  ref<-"audit/analytics/preparation_failure.json"
  json_write(file.path(run,ref),list(stage="preparation",error=message,recorded_at=now,
               source_snapshot_available=FALSE,models_executed=0L,no_email_sent=TRUE))
  hash<-sha_file(file.path(run,ref));ledger<-gates<-list()
  for(i in seq_len(nrow(registry))) {
    m<-registry[i,];id<-m$method_id
    ledger[[i]]<-list(method_id=id,method=m$method,family=m$family,publication_role=m$publication_role,
       implementation_status=if(id%in%names(d1_adapters()))"implemented" else "not_implemented",
       terminal_status="blocked_data",reason="Preparation failed before an eligible analytical snapshot could be built; no model execution claimed.",
       failed_or_unestablished_gates=m$required_gates,input_sha256="",artifact_ref="",artifact_sha256="",artifact_created_at="",
       started_at=now,ended_at=now,runtime_seconds=0,peak_ram_if_measured="not_measured",execution_stage="upstream_preparation",
       fit_cadence=m$fit_cadence,fit_status="blocked",model_release_status="unreleased",error_log=ref)
    for(g in strsplit(m$required_gates,"|",fixed=TRUE)[[1]])gates[[length(gates)+1L]]<-list(method_id=id,gate=g,
      state="unestablished",blocker_class="data",reason="Upstream preparation failed; no inference from an incomplete source set.",evidence_path=ref,evidence_sha256=hash)
  }
  d<-rows_frame(ledger,D1_LEDGER_COLUMNS);g<-rows_frame(gates,D1_GATE_COLUMNS)
  validate_method_ledger(d,g,registry,run,now)
  csv_write(file.path(run,"audit/analytics/method_ledger.csv"),d)
  csv_write(file.path(run,"audit/analytics/gate_ledger.csv"),g)
  csv_write(file.path(run,"audit/analytics/stage_ledger.csv"),ledger,c("method_id","terminal_status","reason","started_at","ended_at","execution_stage"))
  invisible(TRUE)
}
