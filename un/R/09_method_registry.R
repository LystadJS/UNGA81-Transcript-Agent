# D1-I1: exhaustive method and prerequisite accounting, not a claim of 42 fitted models.
D1_TERMINAL_STATES <- c("executed", "reused", "blocked_data", "blocked_labels", "blocked_history",
  "blocked_dependency", "blocked_authorization", "blocked_resources", "blocked_version", "blocked_regime",
  "not_due", "failed", "withheld_quality", "not_implemented")
D1_GATE_COLUMNS <- c("method_id", "gate", "state", "blocker_class", "reason", "evidence_path", "evidence_sha256")
D1_LEDGER_COLUMNS <- c("method_id", "method", "family", "publication_role", "implementation_status",
  "terminal_status", "reason", "failed_or_unestablished_gates", "input_sha256", "artifact_ref", "artifact_sha256",
  "artifact_created_at", "started_at", "ended_at", "runtime_seconds", "peak_ram_if_measured", "execution_stage",
  "fit_cadence", "fit_status", "model_release_status", "error_log")
read_d1_registry <- function(root) {
  assert(identical(sha_file(file.path(root,"config/method_registry.csv")),sha_file(file.path(root,"design/D1/config/method_registry.csv"))),"Do not weaken D1 prerequisites in place; create a reviewed registry revision")
  r <- read.csv(file.path(root, "config/method_registry.csv"), stringsAsFactors = FALSE,
                check.names = FALSE, fileEncoding = "UTF-8", na.strings = character())
  required <- c("method_id", "method", "family", "learning_type", "email_slots", "r_packages", "fit_cadence",
                "required_gates", "publication_role", "daily_policy", "implementation_status", "note")
  assert(all(required %in% names(r)) && nrow(r) == 42L && !anyDuplicated(r$method_id), "D1 requires exactly 42 unique registrations")
  assert(identical(r$method_id, sprintf("M%02d", 1:42)), "Method registry identity/order changed")
  assert(all(r$publication_role %in% c("production_candidate", "challenger", "diagnostic", "research_only")), "Unknown publication role")
  assert(all(vapply(strsplit(r$email_slots, "|", fixed = TRUE), function(x)all(x %in% paste0("O",1:5)), logical(1))), "Method routes outside five email outputs")
  for(g in strsplit(r$required_gates,"|",fixed=TRUE))assert(all(nzchar(g))&&!anyDuplicated(g),"Empty or duplicate method prerequisites")
  r
}
readiness_context <- function(cp, snapshot, cfg, root) {
  obs <- snapshot$observations
  current <- cp$observations
  current_iso <- vapply(current, function(s)s$iso3, character(1))
  earlier <- if (nrow(obs)) obs[obs$event_date < cp$brief$date & obs$eligibility_class == "observed_input", , drop = FALSE] else obs
  current_genres <- unique(vapply(current, function(s)s$genre, character(1)))
  matched <- if (nrow(earlier)) earlier[earlier$iso3 %in% current_iso & earlier$genre %in% current_genres & earlier$genre != "unspecified", , drop = FALSE] else earlier
  book <- validate_issue_book(json_read(file.path(root, "config/issue_codebook.json")))
  list(schema = "D1-I1-readiness-v1", snapshot_id = snapshot$snapshot_id,
       as_of_cutoff = snapshot$as_of_cutoff, event_cutoff = cp$brief$date,
       available_country_texts = length(cp$speeches), statement_records = length(current),
       all_current_text_hashes_verified = all(vapply(current, function(s)identical(sha_text(s$text),s$text_sha256),logical(1))),
       active_codebook_is_consistent = TRUE, active_codebook_sha256 = sha_text(json_minimal(book)),
       inherited_label_book_sha256 = sha_text(json_minimal(cp$codebook)),
       inherited_mixed_fixture = cp$brief$source == "replay", fresh_semantic_recode_performed = FALSE,
       prior_nonreplay_statement_versions = nrow(earlier), prior_country_genre_candidates = nrow(matched),
       prior_candidates_are_not_accepted_comparisons = TRUE,
       human_adjudicated_gold_labels = 0L, gold_label_import_adapter_implemented = FALSE,
       external_ai_authorized = isTRUE(cfg$allow_external_ai),
       source_scope = cp$brief$collection$coverage_note,
       missing_source_count = NULL, collection_problem_records = length(cp$brief$collection$errors),
       missing_source_count_note = "Collection errors are not an exact count of missing country texts.",
       released_model_count = 0L, numerical_feature_artifacts = 0L, trained_reference_artifacts = 0L,
       network_artifacts = 0L, accepted_driftmap_supported_regime_artifacts = 0L,
       runtime_memory_benchmark_performed = FALSE, feature_or_model_artifact_not_inferred_from_registry = TRUE)
}
gate_decision <- function(gate, context) {
  newer<-i2_context_feature_decision(gate,context);if(!is.null(newer))return(newer)
  state <- "unestablished"; cls <- "data"; reason <- paste("No accepted artifact establishes", gate)
  if (gate == "source_text") {
    state <- if(context$statement_records > 0 && isTRUE(context$all_current_text_hashes_verified)) "pass" else "fail"
    reason <- sprintf("%d current statement records; text hashes checked. Metadata-only records do not qualify.", context$statement_records)
  } else if (gate == "codebook_consistent") {
    state <- if(isTRUE(context$active_codebook_is_consistent)) "pass" else "fail"; cls <- "version"
    reason <- "The active 13-category codebook is validated; this does not make inherited labels homogeneous."
  } else if (grepl("^gold", gate)) {
    state <- "fail"; cls <- "labels"; reason <- "No human-adjudicated gold label set is imported; automatic and inherited labels are not gold."
  } else if (gate == "embedding_provider_authorized") {
    state <- if(isTRUE(context$external_ai_authorized)) "pass" else "fail"; cls <- "authorization"
    reason <- if(state=="pass") "External processing is explicitly enabled in the run configuration; provider/model validation is separate." else "External AI processing is not authorized in this configuration."
  } else if (gate %in% c("historical_text_corpus", "historical_passage_corpus", "same_country_history")) {
    count <- if(gate=="same_country_history") context$prior_country_genre_candidates else context$prior_nonreplay_statement_versions
    state <- if(count==0L) "fail" else "unestablished"; cls <- "history"
    reason <- sprintf("%d prior candidate observations outside replay; no accepted comparable historical feature series is released.", count)
  } else if (gate %in% c("repeated_country_sequences", "long_country_sequences", "longitudinal_series", "historical_features", "historical_outcomes")) {
    cls <- "history"; reason <- "No validated repeated-observation series or outcome set has been constructed; non-speaking days are not zeros."
  } else if (gate %in% c("embedding_version", "frozen_vocabulary", "reference_cutoff", "representation_consistent", "measurement_invariance")) {
    cls <- "version"; reason <- "No compatible frozen encoder/vocabulary/reference artifact is registered for inference."
  } else if (gate %in% c("neural_resource_benchmark")) {
    cls <- "resources"; reason <- "No measured checkpoint/tokenizer/VRAM/RAM resource benchmark is accepted."
  } else if (gate %in% c("driftmap_supported_regime", "resampling_unit_valid")) {
    cls <- "regime"; reason <- "No pinned, accepted supported-regime and resampling-unit validation is available; inference remains withheld."
  } else if (grepl("validation|diagnostic|calibration|stability|backtest|full_rank|anchor", gate)) {
    cls <- "quality"; reason <- "No accepted task-specific evaluation artifact establishes this requirement; a successful script or Boolean flag is insufficient."
  } else if (gate %in% c("directed_relational_events", "risk_set", "adoption_events", "lagged_exposures", "preexisting_network")) {
    cls <- "data"; reason <- "The required observed event/risk-set/exposure data are not present; shared text is not an observed diplomatic action."
  }
  list(state = state, blocker_class = cls, reason = reason)
}
unique_current_observations <- function(cp) {
  observations <- cp$observations
  ids <- vapply(observations,function(s)s$observation_id,character(1))
  versions <- vapply(observations,function(s)observation_object(s)$observation_version_id,character(1))
  for(id in unique(ids))assert(length(unique(versions[ids==id]))==1L,"Conflicting current versions are not ordered implicitly")
  observations[!duplicated(versions)]
}
m01_rule_candidates <- function(cp, root) {
  book <- validate_issue_book(json_read(file.path(root, "config/issue_codebook.json")))
  decisions <- evidence <- list()
  for (s in unique_current_observations(cp)) {
    obj <- observation_object(s)
    for (issue in book) {
      hits <- Filter(function(u)grepl(issue$extractive_regex, u$text, ignore.case = TRUE, perl = TRUE), s$sentences)
      decisions[[length(decisions)+1L]] <- list(observation_id=s$observation_id,
        observation_version_id=obj$observation_version_id, iso3=s$iso3, issue_id=issue$issue_id,
        state=if(length(hits))"candidate_hit" else "no_hit_unresolved", matching_passages=length(hits),
        codebook_version=issue$version, source_sha256=s$source_sha256, text_sha256=s$text_sha256,
        is_semantically_adjudicated=FALSE, is_absence_decision=FALSE)
      for (h in hits) evidence[[length(evidence)+1L]] <- list(observation_id=s$observation_id,
        observation_version_id=obj$observation_version_id, iso3=s$iso3, issue_id=issue$issue_id,
        passage_id=paste0(obj$observation_version_id,":",h$id), sentence_id=h$id, quote=h$text,
        source_url=str1(h$url,str1(s$source_url)), source_sha256=s$source_sha256)
    }
  }
  list(schema="D1-M01-candidates-v1", method_id="M01", method_role="diagnostic", is_fitted_model=FALSE,
       publication_eligible=FALSE, definition_sha256=sha_text(json_minimal(book)),
       decisions=decisions, evidence=evidence,
       note="Lexicon evidence retrieval only. A match is a candidate; no match is unresolved, not absence.")
}
validate_m01 <- function(result, cp, root) {
  observations <- unique_current_observations(cp)
  book <- validate_issue_book(json_read(file.path(root,"config/issue_codebook.json")))
  assert(identical(result$method_id,"M01") && identical(result$publication_eligible,FALSE), "M01 cannot be a published classifier")
  assert(length(result$decisions)==length(observations)*length(book), "M01 did not account for every statement/issue pair")
  key<-vapply(result$decisions,function(r)paste(r$observation_id,r$issue_id,sep="|"),character(1))
  assert(!anyDuplicated(key),"M01 duplicate statement/issue decisions")
  for (r in result$decisions) assert(r$state%in%c("candidate_hit","no_hit_unresolved") &&
       identical(r$is_absence_decision,FALSE),"M01 fabricated a negative decision")
  for (ev in result$evidence) {
    s<-Filter(function(s)identical(s$observation_id,ev$observation_id),observations)
    assert(length(s)==1L,"Candidate evidence does not resolve to one statement")
    validate_evidence(list(list(sentence_id=ev$sentence_id,quote=ev$quote)),s[[1]]$sentences)
  }
  invisible(TRUE)
}
d1_adapters <- function() list(M01=list(version="d1-i1-rules-1",required_packages="base",
    execute=m01_rule_candidates, validate=validate_m01),
    M02=list(version="d1-i2-tfidf-1",required_packages=c("Matrix","stats"),managed=TRUE),
    M05=list(version="d1-i2-pca-1",required_packages=c("Matrix","stats"),managed=TRUE),
    M06=list(version="d1-i2-pcoa-1",required_packages=c("Matrix","stats"),managed=TRUE),
    M07=list(version="d1-hc-1",required_packages=c("Matrix","stats","cluster"),managed=TRUE),
    M09=list(version="d1-pam-1",required_packages=c("Matrix","stats","cluster"),managed=TRUE))
validate_method_ledger <- function(ledger, gates, registry, run, cutoff) {
  assert(nrow(ledger)==42L && !anyDuplicated(ledger$method_id) && identical(ledger$method_id,registry$method_id), "Every D1 method needs exactly one ordered terminal summary row")
  assert(all(ledger$terminal_status%in%D1_TERMINAL_STATES) && all(nzchar(ledger$reason)), "Incomplete or invalid method accounting")
  assert(!anyDuplicated(paste(gates$method_id,gates$gate)),"Duplicate prerequisite evaluation")
  proof_cache<-new.env(parent=emptyenv())
  for (i in seq_len(nrow(registry))) {
    required<-strsplit(registry$required_gates[i],"|",fixed=TRUE)[[1]]
    g<-gates[gates$method_id==registry$method_id[i],,drop=FALSE]
    assert(setequal(g$gate,required),"A method prerequisite was silently skipped")
    assert(all(g$state%in%c("pass","fail","unestablished")),"Invalid prerequisite state")
    for(j in seq_len(nrow(g)))assert(identical(sha_file(file.path(run,relative_path(g$evidence_path[j]))),g$evidence_sha256[j]),"Gate evidence hash mismatch")
    for(j in seq_len(nrow(g))) {
      key<-g$evidence_sha256[j]
      if(!exists(key,envir=proof_cache,inherits=FALSE))assign(key,json_read(file.path(run,g$evidence_path[j])),envir=proof_cache)
      proof<-get(key,envir=proof_cache,inherits=FALSE)
      if(identical(proof$schema,"D1-I1-readiness-v1")) {
        context_key<-paste0("context_validated_",key)
        if(!exists(context_key,envir=proof_cache,inherits=FALSE)) {
          i2_validate_context(proof,run);assign(context_key,TRUE,envir=proof_cache)
        }
        assert(identical(g$state[j],gate_decision(g$gate[j],proof)$state),"Gate state contradicts its archived evidence")
      }
      if(identical(proof$schema,"D1-PAM-method-proof-v1")) {
        check_key<-paste0("validated_",key)
        if(!exists(check_key,envir=proof_cache,inherits=FALSE))assign(check_key,pam_validate_proof(proof,run),envir=proof_cache)
        expected<-get(check_key,envir=proof_cache,inherits=FALSE)[[g$gate[j]]]
        assert(identical(g$state[j],expected$state)&&identical(g$reason[j],expected$reason),"PAM gate contradicts its source/numerical proof")
      }
      if(identical(proof$schema,"D1-HC-method-proof-v1")) {
        check_key<-paste0("validated_",key)
        if(!exists(check_key,envir=proof_cache,inherits=FALSE))assign(check_key,hc_validate_proof(proof,run),envir=proof_cache)
        expected<-get(check_key,envir=proof_cache,inherits=FALSE)[[g$gate[j]]]
        assert(identical(g$state[j],expected$state)&&identical(g$reason[j],expected$reason),"Hierarchical gate contradicts its source/numerical proof")
      }
      if(identical(proof$schema,"D1-I2-method-proof-v1")) {
        check_key<-paste0("validated_",key)
        if(!exists(check_key,envir=proof_cache,inherits=FALSE))assign(check_key,i2_validate_method_proof(proof,run),envir=proof_cache)
        expected<-get(check_key,envir=proof_cache,inherits=FALSE)[[g$gate[j]]]
        assert(identical(g$state[j],expected$state)&&identical(g$reason[j],expected$reason),"Staged gate flag contradicts its numerical/source proof")
      }
    }
    row<-ledger[i,,drop=FALSE]
    if (row$terminal_status%in%c("executed","reused") || (row$terminal_status=="withheld_quality" && nzchar(row$artifact_ref))) {
      if(row$terminal_status=="withheld_quality") {
        diagnostic_gate<-if(row$method_id%in%c("M07","M09"))"cluster_stability" else "projection_diagnostics"
        assert(row$method_id%in%c("M05","M06","M07","M09")&&g$state[g$gate==diagnostic_gate]=="fail"&&
          all(g$state[g$gate!=diagnostic_gate]=="pass"),"Withheld fit lacks passed preflight or failed measured diagnostics")
      } else assert(all(g$state=="pass"),"A method ran with an unestablished prerequisite")
      assert(row$method_id%in%names(d1_adapters())&&row$implementation_status=="implemented","Execution claimed without a registered executable adapter")
      assert(nzchar(row$artifact_ref) && identical(sha_file(file.path(run,relative_path(row$artifact_ref))),row$artifact_sha256),"Executed/reused method has no valid artifact")
      assert(parse_utc(row$artifact_created_at)<=parse_utc(cutoff),"Future artifact reused before its availability")
    } else assert(!nzchar(row$artifact_ref)&&!nzchar(row$artifact_sha256)&&!nzchar(row$artifact_created_at),"Unexecuted method must not imply a produced artifact")
    assert(parse_utc(row$ended_at)>=parse_utc(row$started_at)&&parse_utc(row$ended_at)<=parse_utc(cutoff),"Invalid method execution interval/cutoff")
    if(row$terminal_status=="executed" || (row$terminal_status=="withheld_quality"&&nzchar(row$artifact_ref)))assert(parse_utc(row$artifact_created_at)>=parse_utc(row$started_at)&&parse_utc(row$artifact_created_at)<=parse_utc(row$ended_at),"New artifact timestamp outside execution interval")
    if(row$terminal_status=="reused")assert(parse_utc(row$artifact_created_at)<=parse_utc(row$started_at),"Reused artifact did not exist at execution start")
  }
  invisible(TRUE)
}
run_method_accounting <- function(root,run,cfg,cp,snapshot,adapters=d1_adapters(),clock=utc_now) {
  registry<-read_d1_registry(root);assert(all(names(adapters)%in%registry$method_id),"Unregistered adapter")
  options(unbrief.root=root);cp$config<-cfg
  context<-readiness_context(cp,snapshot,cfg,root)
  # Model execution happens after source ingestion; all candidate artifacts must still be
  # available by the report's final analytic cutoff, which is recorded below.
  context_path<-"audit/analytics/readiness_context.json";json_write(file.path(run,context_path),context)
  context_hash<-sha_file(file.path(run,context_path))
  registry_path<-"audit/analytics/method_registry.csv";csv_write(file.path(run,registry_path),registry)
  input_hash<-sha_object(list(observations=lapply(cp$observations,observation_object),
                        codebook=json_read(file.path(root,"config/issue_codebook.json"))))
  ledger<-gates<-stages<-dependencies<-list()
  for (i in seq_len(nrow(registry))) {
    m<-registry[i,,drop=FALSE];id<-m$method_id;start<-clock()
    req<-strsplit(m$required_gates,"|",fixed=TRUE)[[1]]
    gr<-lapply(req,function(g){d<-gate_decision(g,context);c(list(method_id=id,gate=g),d,
                    list(evidence_path=context_path,evidence_sha256=context_hash))})
    bad<-Filter(function(g)!identical(g$state,"pass"),gr)
    adapter<-adapters[[id]];implemented<-!is.null(adapter)
    packages<-if(implemented)adapter$required_packages else strsplit(m$r_packages,"|",fixed=TRUE)[[1]]
    available<-vapply(packages,function(p)p=="base"||requireNamespace(p,quietly=TRUE),logical(1))
    for(j in seq_along(packages))dependencies[[length(dependencies)+1L]]<-list(method_id=id,package=packages[j],
      installed=available[j],usage=if(implemented)"actual_adapter_dependency" else "design_candidate_not_an_installed_lock",version=if(available[j])as.character(utils::packageVersion(packages[j])) else "")
    status<-"not_implemented";reason<-"No executable adapter is registered in this D1-I4 checkpoint; all design prerequisites were evaluated separately."
    artifact_ref<-artifact_hash<-artifact_time<-error_log<-"";stage<-"eligibility";fit_status<-"not_implemented"
    staged<-NULL
    if(implemented && isTRUE(adapter$managed)) {
      staged<-if(id=="M07")hc_run_managed(id,cp,root,run,snapshot,context,available,clock) else if(id=="M09")pam_run_managed(id,cp,root,run,snapshot,context,available,clock) else i2_run_managed(id,cp,root,run,snapshot,context,available,clock)
      status<-staged$status;reason<-staged$reason;stage<-staged$stage;fit_status<-staged$fit_status
      artifact_ref<-staged$artifact_ref;artifact_hash<-staged$artifact_hash;artifact_time<-staged$artifact_time;error_log<-staged$error_log
      gr<-staged$gr;bad<-Filter(function(g)!identical(g$state,"pass"),gr)
      if(id=="M02"&&!is.null(staged$value)) {
        context<-i2_update_context(context,staged$value,run)
        context_path<-"audit/analytics/readiness_context_after_features.json"
        json_write(file.path(run,context_path),context);context_hash<-sha_file(file.path(run,context_path))
      }
    } else if(implemented && length(bad)) {
      cls<-bad[[1]]$blocker_class;status<-switch(cls,quality="withheld_quality",paste0("blocked_",cls))
      reason<-paste(vapply(bad,function(g)paste0(g$gate,": ",g$reason),character(1)),collapse="; ")
      fit_status<-"blocked"
    } else if(implemented && !all(available)) {
      status<-"blocked_dependency";reason<-paste("Missing actual adapter packages:",paste(packages[!available],collapse=", "));fit_status<-"blocked"
    } else if(implemented) {
      stage<-"transform";fit_status<-"not_a_fit";log_ref<-paste0("audit/analytics/errors/",id,".txt")
      result<-tryCatch({
        fingerprint<-sha_text(paste(id,adapter$version,input_hash,
                     sha_object(vapply(list.files(file.path(root,"R"),pattern="^[0-9].*\\.R$",full.names=TRUE),sha_file,character(1))),R.version.string,sep="|"))
        cache<-file.path(root,relative_path(cfg$analytics$method_cache_dir),id,paste0(fingerprint,".rds"))
        hashpath<-paste0(cache,".sha256")
        if(file.exists(cache)||file.exists(hashpath)) {
          assert(file.exists(cache)&&file.exists(hashpath)&&identical(sha_file(cache),trimws(read_text(hashpath))),"Method cache is incomplete or corrupt; not silently recomputed")
          cached<-readRDS(cache)
          assert(identical(cached$key,fingerprint)&&identical(cached$input_sha256,input_hash),"Method cache identity mismatch")
          assert(parse_utc(cached$created_at)<=parse_utc(clock()),"Method cache creation time is in the future")
          adapter$validate(cached$result,cp,root);value<-cached$result;artifact_time<-cached$created_at
          status<-"reused";reason<-"Exact input/code/version cache reused; artifact hash, identity, time and evidence revalidated."
        } else {
          value<-adapter$execute(cp,root);adapter$validate(value,cp,root);artifact_time<-clock()
          cached<-list(key=fingerprint,input_sha256=input_hash,created_at=artifact_time,result=value)
          bytes<-serialize(cached,NULL,version=3);immutable_write(cache,bytes)
          immutable_write(hashpath,charToRaw(paste0(sha_raw(bytes),"\n")))
          status<-"executed";reason<-"Source-bound diagnostic transform executed and its evidence validated; not a trained or released classifier."
        }
        artifact_ref<-paste0("audit/analytics/artifacts/",id,".rds")
        bytes<-serialize(value,NULL,version=3);immutable_write(file.path(run,artifact_ref),bytes);artifact_hash<-sha_raw(bytes)
        if(id=="M01") {
          csv_write(file.path(run,"data/m01_candidates.csv"),value$decisions,
                    c("observation_id","observation_version_id","iso3","issue_id","state","matching_passages","codebook_version","source_sha256","text_sha256","is_semantically_adjudicated","is_absence_decision"))
          csv_write(file.path(run,"data/m01_evidence.csv"),value$evidence,
                    c("observation_id","observation_version_id","iso3","issue_id","passage_id","sentence_id","quote","source_url","source_sha256"))
        }
        TRUE
      },error=function(e){
        write_text(file.path(run,log_ref),conditionMessage(e));FALSE
      })
      if(!isTRUE(result)){status<-"failed";reason<-"Adapter/cache validation failed; see its preserved error log. Other registrations were still assessed.";error_log<-log_ref;artifact_ref<-artifact_hash<-artifact_time<-""}
    }
    gates<-c(gates,gr)
    end<-clock()
    row<-list(method_id=id,method=m$method,family=m$family,publication_role=m$publication_role,
      implementation_status=if(implemented)"implemented" else "not_implemented",terminal_status=status,reason=reason,
      failed_or_unestablished_gates=paste(vapply(bad,function(g)g$gate,character(1)),collapse="|"),input_sha256=input_hash,
      artifact_ref=artifact_ref,artifact_sha256=artifact_hash,artifact_created_at=artifact_time,started_at=start,ended_at=end,
      runtime_seconds=max(0,parse_utc(end)-parse_utc(start)),peak_ram_if_measured="not_measured",execution_stage=stage,
      fit_cadence=m$fit_cadence,fit_status=fit_status,model_release_status=if(!is.null(staged))staged$model_release_status else if(implemented&&m$publication_role=="diagnostic")"diagnostic_only" else "unreleased",error_log=error_log)
    ledger[[i]]<-row
    stages[[i]]<-list(method_id=id,stage=stage,terminal_status=status,started_at=start,ended_at=end,
                       artifact_ref=artifact_ref,artifact_sha256=artifact_hash,reason=reason)
    # Incremental checkpoint preserves every completed assessment if the process stops later.
    csv_write(file.path(run,"audit/analytics/method_ledger_in_progress.csv"),ledger,D1_LEDGER_COLUMNS)
  }
  ledger<-rows_frame(ledger,D1_LEDGER_COLUMNS);gates<-rows_frame(gates,D1_GATE_COLUMNS)
  analytic_cutoff<-clock()
  validate_method_ledger(ledger,gates,registry,run,analytic_cutoff)
  csv_write(file.path(run,"audit/analytics/method_ledger.csv"),ledger)
  csv_write(file.path(run,"audit/analytics/gate_ledger.csv"),gates)
  csv_write(file.path(run,"audit/analytics/dependency_ledger.csv"),dependencies,c("method_id","package","installed","usage","version"))
  csv_write(file.path(run,"audit/analytics/stage_ledger.csv"),stages,c("method_id","stage","terminal_status","started_at","ended_at","artifact_ref","artifact_sha256","reason"))
  unlink(file.path(run,"audit/analytics/method_ledger_in_progress.csv"))
  list(registry=registry,context=context,ledger=ledger,gates=gates,as_of_cutoff=analytic_cutoff,
       snapshot_id=snapshot$snapshot_id,method_count=nrow(ledger),gate_count=nrow(gates))
}
