# M09 only: PAM / k-medoids on the FULL frozen country TF-IDF distance matrix.
# Uses the same Euclidean chord geometry as M07. Audit-only: never an email producer.
PAM_SCHEMA <- "D1-PAM-result-v1"
PAM_IMAGE <- "Figure_7_PAM_Clustering_Audit.png"

pam_policy <- function(root) {
  path <- file.path(root, "config/pam_policy.json")
  frozen <- file.path(root, "design/D1-PAM/pam_policy.json")
  assert(identical(sha_file(path), sha_file(frozen)),
         "PAM policy changed without a preserved design revision")
  p <- json_read(path)
  assert(identical(p$schema, "D1-PAM-1") && identical(p$method_id, "M09") &&
         identical(p$publication_mode, "audit_only"), "Unsupported PAM policy")
  p
}

pam_fit_cut <- function(d, k) {
  fit <- cluster::pam(stats::as.dist(d), k = as.integer(k), diss = TRUE,
                      cluster.only = FALSE, keep.diss = FALSE, keep.data = FALSE,
                      do.swap = TRUE, pamonce = 0, trace.lev = 0)
  groups <- hc_canonical(fit$clustering, rownames(d))
  sil <- as.numeric(cluster::silhouette(as.integer(groups), stats::as.dist(d))[, "sil_width"])
  names(sil) <- names(groups)
  sizes <- table(groups)
  medoid_ids <- rownames(d)[as.integer(fit$id.med)]
  list(groups = groups, silhouette = sil, mean_silhouette = mean(sil),
       min_size = min(sizes), max_fraction = max(sizes) / length(groups),
       medoids = medoid_ids, objective = as.numeric(fit$objective[2]))
}

pam_compute <- function(x, policy, refitter = pam_fit_cut) {
  input <- hc_distance(x, policy); d <- input$distance; ids <- input$ids; n <- length(ids)
  ks <- as.integer(unlist(policy$k_candidates)); ks <- ks[ks >= 2L & ks < n]
  assert(length(ks) > 0L && !anyDuplicated(ks), "No valid predeclared PAM k candidates")
  B <- as.integer(policy$replicates); m <- max(2L, floor(n * policy$subsample_fraction))
  assert(B >= 2L && m < n, "Invalid PAM roster-deletion plan")
  samples <- hc_with_seed(policy$seed, function()
    lapply(seq_len(B), function(i) sort(sample.int(n, m, replace = FALSE))))
  plan <- do.call(rbind, lapply(seq_len(B), function(i)
    data.frame(replicate = i, iso3 = ids[samples[[i]]], stringsAsFactors = FALSE)))
  fits <- list(); candidates <- partitions <- list()
  for (k in ks) {
    key <- paste0("pam__", k)
    f <- pam_fit_cut(d, k); fits[[key]] <- f
    admissible <- f$min_size >= policy$min_cluster_size && f$max_fraction <= policy$max_cluster_fraction
    candidates[[length(candidates) + 1L]] <- data.frame(candidate_id = key, k = k, n = n,
      mean_silhouette = f$mean_silhouette, min_cluster_size = f$min_size,
      largest_cluster_fraction = f$max_fraction, size_admissible = admissible,
      objective = f$objective, stringsAsFactors = FALSE)
    partitions[[length(partitions) + 1L]] <- data.frame(candidate_id = key, iso3 = ids,
      cluster = as.integer(f$groups), silhouette = as.numeric(f$silhouette),
      is_medoid = ids %in% f$medoids, stringsAsFactors = FALSE)
  }
  candidates <- do.call(rbind, candidates); partitions <- do.call(rbind, partitions)
  pool <- which(candidates$size_admissible)
  selection_admissible <- length(pool) > 0L
  if (!selection_admissible) pool <- seq_len(nrow(candidates))
  selected <- pool[order(-candidates$mean_silhouette[pool], candidates$k[pool], method = "radix")][1]
  selected_id <- candidates$candidate_id[selected]; selected_k <- candidates$k[selected]
  candidates$selected_primary <- seq_len(nrow(candidates)) == selected
  ledgers <- jaccards <- memberships <- medoid_rows <- list()
  include <- together <- matrix(0L, n, n, dimnames = list(ids, ids))
  for (b in seq_len(B)) {
    index <- samples[[b]]; subd <- d[index, index, drop = FALSE]
    for (k in ks) {
      key <- paste0("pam__", k); state <- "executed"; note <- ""; z <- NULL; med <- character(); ari <- NA_real_
      if (k >= length(index)) { state <- "blocked_support"; note <- "k must be smaller than sampled-country count" }
      else {
        f <- tryCatch(refitter(subd, k), error = function(e) { note <<- conditionMessage(e); NULL })
        if (is.null(f)) state <- "failed" else { z <- f$groups; med <- f$medoids; ari <- hc_ari(fits[[key]]$groups[index], z) }
      }
      ledgers[[length(ledgers)+1L]] <- data.frame(candidate_id=key,k=k,replicate=b,
        sample_n=length(index),status=state,ari=ari,error=note,stringsAsFactors=FALSE)
      if (!is.null(z)) {
        memberships[[length(memberships)+1L]] <- data.frame(candidate_id=key,replicate=b,
          iso3=names(z),cluster=as.integer(z),is_medoid=names(z)%in%med,stringsAsFactors=FALSE)
        j <- hc_best_jaccard(fits[[key]]$groups,z,policy$min_sampled_cluster_members)
        medoid_rows[[length(medoid_rows)+1L]] <- data.frame(candidate_id=key,replicate=b,
          medoid=med,retained_from_full=med %in% fits[[key]]$medoids,stringsAsFactors=FALSE)
        if (identical(key,selected_id)) {
          include[index,index] <- include[index,index] + 1L
          together[index,index] <- together[index,index] + outer(z,z,"==")
        }
      } else {
        g <- fits[[key]]$groups
        j <- data.frame(cluster=sort(unique(g)), sampled_members=vapply(sort(unique(g)),function(i)sum(g[index]==i),integer(1)),
                        evaluable=FALSE,jaccard=NA_real_)
      }
      jaccards[[length(jaccards)+1L]] <- data.frame(candidate_id=key,replicate=b,j,stringsAsFactors=FALSE)
    }
  }
  ledger <- do.call(rbind,ledgers); jaccard <- do.call(rbind,jaccards)
  membership <- if(length(memberships)) do.call(rbind,memberships) else data.frame()
  medoids <- if(length(medoid_rows)) do.call(rbind,medoid_rows) else data.frame()
  agg <- lapply(candidates$candidate_id,function(key){
    z <- ledger[ledger$candidate_id==key,,drop=FALSE]; finite <- is.finite(z$ari)
    js <- jaccard[jaccard$candidate_id==key,,drop=FALSE]
    data.frame(candidate_id=key,planned_replicates=nrow(z),successful_replicates=sum(finite),
      mean_ari=if(any(finite))mean(z$ari[finite]) else NA_real_,
      min_ari=if(any(finite))min(z$ari[finite]) else NA_real_,stringsAsFactors=FALSE)
  })
  candidates <- merge(candidates,do.call(rbind,agg),by="candidate_id",sort=FALSE)
  candidates <- candidates[match(paste0("pam__",ks),candidates$candidate_id),,drop=FALSE]
  cs <- do.call(rbind,lapply(candidates$candidate_id,function(key){
    j <- jaccard[jaccard$candidate_id==key,,drop=FALSE]
    do.call(rbind,lapply(sort(unique(j$cluster)),function(cl){q<-j[j$cluster==cl,,drop=FALSE];ev<-q$evaluable&is.finite(q$jaccard)
      data.frame(candidate_id=key,cluster=cl,planned=nrow(q),evaluable=sum(ev),evaluable_fraction=mean(ev),
        mean_jaccard=if(any(ev))mean(q$jaccard[ev])else NA_real_,min_jaccard=if(any(ev))min(q$jaccard[ev])else NA_real_) }))
  }))
  medoid_stability <- if(nrow(medoids)) do.call(rbind,lapply(candidates$candidate_id,function(key){
    q<-medoids[medoids$candidate_id==key,,drop=FALSE]
    data.frame(candidate_id=key,medoid_slots=nrow(q),retained_slots=sum(q$retained_from_full),
      retention_fraction=if(nrow(q))mean(q$retained_from_full)else NA_real_)
  })) else data.frame(candidate_id=candidates$candidate_id,medoid_slots=0L,retained_slots=0L,retention_fraction=NA_real_)
  consensus <- together / include; consensus[include==0] <- NA_real_
  list(distance=d,excluded_iso3=input$excluded,candidates=candidates,partitions=partitions,
       selected_id=selected_id,selected_k=selected_k,selection_size_admissible=selection_admissible,
       selected_groups=fits[[selected_id]]$groups,selected_medoids=fits[[selected_id]]$medoids,
       resample_plan=plan,resample_ledger=ledger,resample_memberships=membership,
       cluster_resample_jaccard=jaccard,cluster_stability=cs,medoid_stability=medoid_stability,
       coassignment=consensus,pair_opportunities=include,pair_together=together,
       distance_tie_fraction=1-length(unique(as.numeric(stats::as.dist(d))))/length(stats::as.dist(d)))
}

pam_quality <- function(numerical, feature, collection, policy) {
  cnd <- numerical$candidates[numerical$candidates$selected_primary,,drop=FALSE]
  cs <- numerical$cluster_stability[numerical$cluster_stability$candidate_id==numerical$selected_id,,drop=FALSE]
  ms <- numerical$medoid_stability[numerical$medoid_stability$candidate_id==numerical$selected_id,,drop=FALSE]
  checks <- list(); add <- function(name,pass,observed,criterion) checks[[length(checks)+1L]] <<- data.frame(
    check=name,state=if(isTRUE(pass))"pass" else "fail",observed=as.character(observed),criterion=criterion,stringsAsFactors=FALSE)
  finite_min <- function(x) if(length(x)&&all(is.finite(x)))min(x)else NA_real_
  u<-feature$current_units;ru<-feature$reference$units;all_units<-c(u,ru)
  known<-vapply(all_units,function(x)identical(x$language,"en")&&nzchar(x$genre)&&x$genre!="unspecified",logical(1))
  observed<-vapply(all_units,function(x)identical(x$eligibility_class,"observed_input"),logical(1))
  flags<-sum(vapply(all_units,function(x)length(unlist(x$flags)),integer(1)))
  stat<-feature$current$statement$rows
  duplicates<-any(vapply(split(vapply(u,`[[`,character(1),"iso3"),vapply(u,`[[`,character(1),"text_sha256")),function(x)length(unique(x))>1L,logical(1)))
  add("complete_nonzero_coverage",!length(numerical$excluded_iso3)&&all(stat$nonzero),sum(!stat$nonzero),"No excluded country or zero contributing statement")
  add("distinct_country_texts",!duplicates&&!any(as.numeric(stats::as.dist(numerical$distance))<=policy$tolerance),sum(as.numeric(stats::as.dist(numerical$distance))<=policy$tolerance),"No cross-country exact text/vector duplicates")
  add("observed_source_scope",all(observed),paste(sum(observed),length(observed),sep="/"),"Reference and current sources are observed_input, not replay/engineering")
  add("known_language_genre",all(known)&&length(unique(vapply(all_units,`[[`,character(1),"genre")))==1L,paste(unique(vapply(all_units,`[[`,character(1),"language")),collapse="|"),"One declared English genre")
  add("source_quality",flags==0L&&length(collection$errors)==0L,flags+length(collection$errors),"No source flags or collection errors")
  maxoov<-if(nrow(stat)&&all(is.finite(stat$oov_fraction)))max(stat$oov_fraction)else NA_real_
  add("vocabulary_coverage",is.finite(maxoov)&&maxoov<=policy$max_oov_fraction,maxoov,paste("Maximum statement OOV <=",policy$max_oov_fraction))
  add("statement_support",all(stat$eligible_tokens>=policy$min_eligible_tokens),min(stat$eligible_tokens),paste("At least",policy$min_eligible_tokens,"eligible tokens per statement"))
  add("cluster_size",numerical$selection_size_admissible,cnd$min_cluster_size,paste("Min size >=",policy$min_cluster_size,"; max share <=",policy$max_cluster_fraction))
  add("silhouette",cnd$mean_silhouette>=policy$min_mean_silhouette,cnd$mean_silhouette,paste("Mean silhouette >=",policy$min_mean_silhouette))
  success<-cnd$successful_replicates/cnd$planned_replicates
  add("replicate_delivery",success>=policy$min_success_fraction,success,paste("Successful finite-ARI fraction >=",policy$min_success_fraction))
  add("partition_stability",is.finite(cnd$mean_ari)&&cnd$mean_ari>=policy$min_mean_ari,cnd$mean_ari,paste("Mean subset ARI >=",policy$min_mean_ari))
  j<-finite_min(cs$mean_jaccard);add("clusterwise_stability",is.finite(j)&&j>=policy$min_cluster_mean_jaccard,j,paste("Every cluster mean subset Jaccard >=",policy$min_cluster_mean_jaccard))
  support<-finite_min(cs$evaluable_fraction);add("clusterwise_evaluability",is.finite(support)&&support>=policy$min_cluster_evaluable_fraction,support,paste("Every cluster evaluable fraction >=",policy$min_cluster_evaluable_fraction))
  mr<-if(nrow(ms))ms$retention_fraction[1]else NA_real_;add("medoid_stability",is.finite(mr)&&mr>=policy$min_medoid_retention_fraction,mr,paste("Full-sample medoid retention fraction >=",policy$min_medoid_retention_fraction))
  checks<-do.call(rbind,checks)
  list(checks=checks,passed=all(checks$state=="pass"),publication_eligible=FALSE,release_status="audit_only",
       empirical_validation_completed=FALSE,interpretation="Engineering screening only; passing is not empirical release approval")
}

pam_execute <- function(feature, cp, root, clock=utc_now) {
  i2_validate_features(feature,cp,root);p<-pam_policy(root);fingerprint<-sha_object(feature)
  numerical<-pam_compute(feature$current$country$x,p);collection<-if(is.null(cp))list(errors=list())else cp$brief$collection
  quality<-pam_quality(numerical,feature,collection,p);assert(identical(sha_object(feature),fingerprint),"M09 mutated frozen feature input")
  value<-list(schema=PAM_SCHEMA,method_id="M09",policy=p,policy_sha256=sha_object(p),feature_sha256=fingerprint,
    fitted_reference_id=feature$fitted_reference_id,source_snapshot_id=feature$source_snapshot_id,
    source_as_of_cutoff=feature$source_as_of_cutoff,event_cutoff=feature$event_cutoff,created_at=clock(),
    runtime=list(R=as.character(getRversion()),cluster=as.character(packageVersion("cluster")),Matrix=as.character(packageVersion("Matrix"))),
    numerical=numerical,quality=quality,collection=collection,source_index=feature$current$country$rows,
    fit_status="fitted_current_pam_on_frozen_features",publication_eligible=FALSE)
  value$result_id<-sha_object(value);value
}

pam_validate <- function(value,feature,root,cp=NULL,recompute=TRUE) {
  assert(identical(value$schema,PAM_SCHEMA)&&identical(value$method_id,"M09"),"Wrong M09 schema")
  assert(identical(value$result_id,sha_object(value[setdiff(names(value),"result_id")])),"M09 result hash mismatch")
  p<-pam_policy(root);assert(identical(value$runtime,list(R=as.character(getRversion()),cluster=as.character(packageVersion("cluster")),Matrix=as.character(packageVersion("Matrix")))),"PAM runtime identity mismatch")
  assert(identical(value$policy,p)&&identical(value$policy_sha256,sha_object(p)),"M09 policy mismatch")
  i2_validate_features(feature,cp,root)
  assert(identical(value$feature_sha256,sha_object(feature))&&identical(value$fitted_reference_id,feature$fitted_reference_id)&&identical(value$source_snapshot_id,feature$source_snapshot_id),"M09 source/reference binding mismatch")
  assert(identical(value$source_as_of_cutoff,feature$source_as_of_cutoff)&&identical(value$event_cutoff,feature$event_cutoff)&&parse_utc(value$created_at)>=parse_utc(feature$created_at),"M09 time binding invalid")
  assert(identical(value$source_index,feature$current$country$rows),"M09 country metadata changed")
  if(!is.null(cp))assert(identical(value$collection,cp$brief$collection),"M09 collection context changed")
  assert(identical(value$publication_eligible,FALSE)&&identical(value$quality$publication_eligible,FALSE)&&identical(value$quality$release_status,"audit_only"),"M09 cannot publish through a readiness flag")
  if(recompute){expected<-pam_compute(feature$current$country$x,p);assert(identical(expected,value$numerical),"M09 numerical/resample artifact fails independent recomputation")}
  expected_quality<-pam_quality(value$numerical,feature,value$collection,p);assert(identical(expected_quality,value$quality),"M09 quality does not match numerical/source evidence")
  invisible(TRUE)
}

pam_write_tables <- function(value,run) {
  n<-value$numerical;out<-file.path(run,"audit/pam");dir.create(out,recursive=TRUE,showWarnings=FALSE)
  for(name in c("candidates","partitions","resample_plan","resample_ledger","resample_memberships","cluster_resample_jaccard","cluster_stability","medoid_stability"))csv_write(file.path(out,paste0(name,".csv")),n[[name]])
  csv_write(file.path(out,"quality_checks.csv"),value$quality$checks)
  meta<-value$source_index;meta$cluster<-as.integer(n$selected_groups[match(meta$iso3,names(n$selected_groups))]);meta$is_medoid<-meta$iso3%in%n$selected_medoids;meta$included<-meta$iso3%in%names(n$selected_groups);meta$exclusion_reason<-ifelse(meta$included,"","Zero frozen feature vector; not assigned");meta$reference_id<-value$fitted_reference_id;meta$source_snapshot_id<-value$source_snapshot_id
  csv_write(file.path(out,"country_assignments.csv"),meta)
  for(name in c("distance","coassignment","pair_opportunities","pair_together"))csv_write(file.path(out,paste0(name,".csv")),data.frame(iso3=rownames(n[[name]]),n[[name]],check.names=FALSE))
  json_write(file.path(out,"summary.json"),list(method_id="M09",selected_candidate=n$selected_id,selected_k=n$selected_k,selected_medoids=n$selected_medoids,engineering_screen_passed=value$quality$passed,publication_eligible=FALSE,release_status="audit_only",feature_sha256=value$feature_sha256,reference_id=value$fitted_reference_id,result_id=value$result_id,interpretation="Lexical medoid groups, not political blocs. Roster-deletion sensitivity is not a confidence interval."))
}
