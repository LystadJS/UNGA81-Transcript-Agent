# M07 only: hierarchical clustering of the FULL frozen country TF-IDF vectors.
# Vocabulary, IDF, statement pooling and source texts are never refitted here.
# Country subsampling measures conditional roster sensitivity, not confidence.
HC_SCHEMA <- "D1-HC-result-v1"
HC_IMAGE <- "Figure_6_Hierarchical_Clustering_Audit.png"

hc_policy <- function(root) {
  path <- file.path(root, "config/hierarchical_policy.json")
  frozen <- file.path(root, "design/D1-HC/hierarchical_policy.json")
  assert(identical(sha_file(path), sha_file(frozen)),
         "Hierarchical policy changed without a preserved design revision")
  p <- json_read(path)
  assert(identical(p$schema, "D1-HC-1") && identical(p$method_id, "M07") &&
         identical(p$publication_mode, "audit_only"), "Unsupported hierarchical policy")
  assert(identical(p$primary_linkage, "average") &&
         identical(unlist(p$sensitivity_linkages), c("complete", "ward.D2")),
         "Linkages must match the hierarchical-only design")
  p
}

# Fixed RNG settings are local to this operation. Restore the caller's RNG state.
hc_with_seed <- function(seed, fun) {
  old_kind <- RNGkind()
  had_seed <- exists(".Random.seed", envir = .GlobalEnv, inherits = FALSE)
  if (had_seed) old_seed <- get(".Random.seed", envir = .GlobalEnv)
  on.exit({
    do.call(RNGkind, as.list(old_kind))
    if (had_seed) assign(".Random.seed", old_seed, envir = .GlobalEnv)
    else if (exists(".Random.seed", envir = .GlobalEnv, inherits = FALSE))
      rm(".Random.seed", envir = .GlobalEnv)
  }, add = TRUE)
  RNGkind("Mersenne-Twister", "Inversion", "Rejection")
  set.seed(as.integer(seed))
  fun()
}

hc_canonical <- function(groups, ids) {
  assert(length(groups) == length(ids) && !anyNA(groups) && !anyDuplicated(ids),
         "Invalid hierarchical partition identity")
  old <- unique(groups)
  first <- vapply(old, function(g) sort(ids[groups == g], method = "radix")[1], character(1))
  setNames(match(groups, old[order(first, method = "radix")]), ids)
}

hc_ari <- function(a, b) {
  assert(length(a) == length(b) && !anyNA(a) && !anyNA(b), "Invalid ARI inputs")
  if (length(a) < 2L) return(NA_real_)
  choose2 <- function(x) x * (x - 1) / 2
  tab <- table(a, b)
  observed <- sum(choose2(tab))
  rows <- sum(choose2(rowSums(tab))); cols <- sum(choose2(colSums(tab)))
  expected <- rows * cols / choose2(length(a))
  denom <- (rows + cols) / 2 - expected
  if (abs(denom) < 1e-14) {
    same <- identical(unname(outer(a, a, "==")), unname(outer(b, b, "==")))
    return(if (same) 1 else NA_real_)
  }
  (observed - expected) / denom
}

hc_best_jaccard <- function(reference, sampled, min_members = 2L) {
  groups <- sort(unique(reference))
  do.call(rbind, lapply(groups, function(g) {
    members <- names(reference)[reference == g]
    present <- intersect(members, names(sampled))
    eligible <- length(present) >= min_members
    score <- if (eligible) max(vapply(unique(sampled), function(h) {
      other <- names(sampled)[sampled == h]
      length(intersect(present, other)) / length(union(present, other))
    }, numeric(1))) else NA_real_
    data.frame(cluster = as.integer(g), sampled_members = length(present),
               evaluable = eligible, jaccard = score)
  }))
}

hc_distance <- function(x, policy) {
  assert(inherits(x, "Matrix") || is.matrix(x), "Features must be a numeric matrix")
  ids <- rownames(x)
  assert(!is.null(ids) && length(ids) == nrow(x) && all(nzchar(ids)) &&
         !anyDuplicated(ids), "Feature rows require unique country identifiers")
  i2_limit(nrow(x) <= policy$max_countries && nrow(x)^2 <= policy$max_pairwise_cells,
           "Hierarchical pairwise resource cap exceeded before dense distance construction")
  assert(ncol(x) > 0L, "No frozen features")
  sq <- as.numeric(Matrix::rowSums(x * x))
  assert(all(is.finite(sq)) && all(sq >= 0), "Nonfinite TF-IDF features")
  keep <- sq > policy$tolerance^2
  if (sum(keep) < policy$min_countries_fit)
    i2_abort("data", "Fewer than four nonzero country vectors; no hierarchical fit")
  assert(all(abs(sq[keep] - 1) <= 1e-8), "M07 requires the frozen L2-normalized country vectors")
  x <- x[keep, , drop = FALSE]
  x <- x[order(rownames(x), method = "radix"), , drop = FALSE]
  # Do not cluster PCA coordinates. This Gram matrix uses every frozen term.
  gram <- as.matrix(Matrix::tcrossprod(x))
  d2 <- outer(diag(gram), diag(gram), "+") - 2 * gram
  assert(all(is.finite(d2)) && min(d2) >= -1e-8, "Invalid squared Euclidean distances")
  d <- sqrt(pmax(d2, 0)); diag(d) <- 0
  dimnames(d) <- list(rownames(x), rownames(x))
  assert(max(abs(d - t(d))) <= 1e-10, "Asymmetric distance construction")
  if (max(d) <= policy$tolerance)
    i2_abort("data", "All usable country vectors coincide; no nontrivial hierarchy")
  list(distance = d, excluded = ids[!keep], ids = rownames(x))
}

hc_cut <- function(tree, k, d) {
  group <- hc_canonical(stats::cutree(tree, k = k), rownames(d))
  widths <- as.numeric(cluster::silhouette(as.integer(group), stats::as.dist(d))[, "sil_width"])
  assert(length(widths) == nrow(d) && all(is.finite(widths)), "Undefined silhouette")
  size <- table(group)
  list(groups = group, silhouette = setNames(widths, names(group)),
       mean_silhouette = mean(widths), min_size = min(size),
       max_fraction = max(size) / length(group))
}

# This numerical function may also receive synthetic engineering features.
# Publication/provenance is enforced separately and cannot be inferred from a fit.
hc_compute <- function(x, policy, refitter = stats::hclust) {
  input <- hc_distance(x, policy); d <- input$distance; ids <- input$ids; n <- length(ids)
  ks <- as.integer(unlist(policy$k_candidates)); ks <- ks[ks >= 2L & ks < n]
  assert(length(ks) > 0L && !anyDuplicated(ks), "No valid predeclared k candidates")
  methods <- c(policy$primary_linkage, unlist(policy$sensitivity_linkages))
  B <- as.integer(policy$replicates); m <- max(2L, floor(n * policy$subsample_fraction))
  assert(B >= 2L && m < n, "Invalid roster-deletion plan")
  samples <- hc_with_seed(policy$seed, function()
    lapply(seq_len(B), function(i) sort(sample.int(n, m, replace = FALSE))))
  plan <- do.call(rbind, lapply(seq_len(B), function(i)
    data.frame(replicate = i, iso3 = ids[samples[[i]]], stringsAsFactors = FALSE)))
  fits <- trees <- list(); candidates <- partitions <- list()
  # Full-data fit candidates are fixed before the stability calculations.
  for (method in methods) {
    tree <- stats::hclust(stats::as.dist(d), method = method)
    tree$call <- NULL
    trees[[method]] <- tree
    for (k in ks) {
      key <- paste(method, k, sep = "__")
      f <- hc_cut(tree, k, d); fits[[key]] <- f
      admissible <- f$min_size >= policy$min_cluster_size && f$max_fraction <= policy$max_cluster_fraction
      candidates[[length(candidates) + 1L]] <- data.frame(candidate_id = key, linkage = method, k = k,
        n = n, mean_silhouette = f$mean_silhouette, min_cluster_size = f$min_size,
        largest_cluster_fraction = f$max_fraction, size_admissible = admissible,
        cophenetic_correlation = suppressWarnings(stats::cor(as.numeric(as.dist(d)), as.numeric(stats::cophenetic(tree)))),
        stringsAsFactors = FALSE)
      partitions[[length(partitions) + 1L]] <- data.frame(candidate_id = key, iso3 = ids,
        cluster = as.integer(f$groups), silhouette = as.numeric(f$silhouette), stringsAsFactors = FALSE)
    }
  }
  candidates <- do.call(rbind, candidates); partitions <- do.call(rbind, partitions)
  primary <- which(candidates$linkage == policy$primary_linkage)
  pool <- primary[candidates$size_admissible[primary]]
  selection_admissible <- length(pool) > 0L
  if (!selection_admissible) pool <- primary
  selected <- pool[order(-candidates$mean_silhouette[pool], candidates$k[pool], method = "radix")][1]
  selected_id <- candidates$candidate_id[selected]; selected_k <- candidates$k[selected]
  candidates$selected_primary <- seq_len(nrow(candidates)) == selected
  ledgers <- jaccards <- replicate_memberships <- list()
  include <- together <- matrix(0L, n, n, dimnames = list(ids, ids))
  # Every planned linkage x k x replicate has one record, including failures.
  for (method in methods) for (b in seq_len(B)) {
    index <- samples[[b]]; subd <- d[index, index, drop = FALSE]
    error <- ""
    tree <- tryCatch(refitter(stats::as.dist(subd), method = method),
                     error = function(e) { error <<- conditionMessage(e); NULL })
    for (k in ks) {
      key <- paste(method, k, sep = "__"); state <- "executed"; note <- error
      z <- NULL; ari <- NA_real_
      if (is.null(tree)) state <- "failed"
      else if (k >= length(index)) { state <- "blocked_support"; note <- "k must be smaller than sampled-country count" }
      else {
        z <- tryCatch(hc_canonical(stats::cutree(tree, k = k), ids[index]),
          error = function(e) { note <<- conditionMessage(e); NULL })
        if (is.null(z)) state <- "failed" else ari <- hc_ari(fits[[key]]$groups[index], z)
      }
      ledgers[[length(ledgers) + 1L]] <- data.frame(candidate_id = key, linkage = method, k = k,
        replicate = b, sample_n = length(index), status = state, ari = ari, error = note, stringsAsFactors = FALSE)
      if (!is.null(z)) {
        j <- hc_best_jaccard(fits[[key]]$groups, z, policy$min_sampled_cluster_members)
        replicate_memberships[[length(replicate_memberships) + 1L]] <- data.frame(
          candidate_id = key, replicate = b, iso3 = names(z), cluster = as.integer(z), stringsAsFactors = FALSE)
        if (identical(key, selected_id)) {
          include[index, index] <- include[index, index] + 1L
          together[index, index] <- together[index, index] + outer(z, z, "==")
        }
      } else {
        g <- fits[[key]]$groups
        j <- data.frame(cluster = sort(unique(g)), sampled_members =
          vapply(sort(unique(g)), function(i) sum(g[index] == i), integer(1)),
          evaluable = FALSE, jaccard = NA_real_)
      }
      jaccards[[length(jaccards) + 1L]] <- cbind(data.frame(candidate_id = key, replicate = b, status = state), j)
    }
  }
  ledger <- do.call(rbind, ledgers); jaccard <- do.call(rbind, jaccards)
  membership <- if (length(replicate_memberships)) do.call(rbind, replicate_memberships) else
    data.frame(candidate_id = character(), replicate = integer(), iso3 = character(), cluster = integer())
  # Missing/failed replicates never inflate success or evaluability rates.
  cluster_stats <- list()
  for (key in candidates$candidate_id) {
    l <- ledger[ledger$candidate_id == key, , drop = FALSE]
    for (g in sort(unique(fits[[key]]$groups))) {
      j <- jaccard[jaccard$candidate_id == key & jaccard$cluster == g, , drop = FALSE]
      scores <- j$jaccard[is.finite(j$jaccard) & j$evaluable]
      cluster_stats[[length(cluster_stats) + 1L]] <- data.frame(candidate_id = key, cluster = g,
        size = sum(fits[[key]]$groups == g), planned = B, evaluable = length(scores),
        evaluable_fraction = length(scores) / B,
        mean_jaccard = if (length(scores)) mean(scores) else NA_real_,
        min_jaccard = if (length(scores)) min(scores) else NA_real_,
        dissolved = sum(scores <= policy$dissolution_jaccard),
        recovered = sum(scores >= policy$recovery_jaccard))
    }
    row <- which(candidates$candidate_id == key)
    candidates$successful_replicates[row] <- sum(l$status == "executed" & is.finite(l$ari))
    candidates$planned_replicates[row] <- B
    candidates$mean_ari[row] <- if (any(is.finite(l$ari))) mean(l$ari[is.finite(l$ari)]) else NA_real_
  }
  cluster_stats <- do.call(rbind, cluster_stats)
  comparisons <- do.call(rbind, lapply(unlist(policy$sensitivity_linkages), function(method)
    data.frame(reference = selected_id, alternative = paste(method, selected_k, sep = "__"),
      k = selected_k, adjusted_rand = hc_ari(fits[[selected_id]]$groups,
        fits[[paste(method, selected_k, sep = "__")]]$groups))))
  consensus <- together / include; consensus[include == 0L] <- NA_real_
  list(distance = d, excluded_iso3 = input$excluded, trees = trees,
    candidates = candidates, partitions = partitions, selected_id = selected_id,
    selected_k = selected_k, selection_size_admissible = selection_admissible,
    selected_groups = fits[[selected_id]]$groups, resample_plan = plan,
    resample_ledger = ledger, resample_memberships = membership,
    cluster_resample_jaccard = jaccard, cluster_stability = cluster_stats,
    linkage_sensitivity = comparisons, coassignment = consensus,
    pair_opportunities = include, pair_together = together,
    distance_tie_fraction = 1 - length(unique(as.numeric(as.dist(d)))) / length(as.dist(d)))
}

hc_quality <- function(numerical, feature, collection, policy) {
  cnd <- numerical$candidates[numerical$candidates$selected_primary, , drop = FALSE]
  cs <- numerical$cluster_stability[numerical$cluster_stability$candidate_id == numerical$selected_id, , drop = FALSE]
  checks <- list()
  add <- function(name, pass, observed, criterion) {
    checks[[length(checks) + 1L]] <<- data.frame(check = name,
      state = if (isTRUE(pass)) "pass" else "fail", observed = as.character(observed),
      criterion = criterion, stringsAsFactors = FALSE)
  }
  finite_min <- function(x) if (length(x) && all(is.finite(x))) min(x) else NA_real_
  u <- feature$current_units; ru <- feature$reference$units
  all_units <- c(u, ru)
  known <- vapply(all_units, function(x) identical(x$language, "en") &&
    nzchar(x$genre) && x$genre != "unspecified", logical(1))
  observed <- vapply(all_units, function(x) identical(x$eligibility_class, "observed_input"), logical(1))
  flags <- sum(vapply(all_units, function(x) length(unlist(x$flags)), integer(1)))
  stat <- feature$current$statement$rows
  duplicates <- any(vapply(split(vapply(u, `[[`, character(1), "iso3"),
    vapply(u, `[[`, character(1), "text_sha256")), function(x) length(unique(x)) > 1L, logical(1)))
  add("complete_nonzero_coverage", !length(numerical$excluded_iso3) && all(stat$nonzero),
      sum(!stat$nonzero), "No excluded country or zero contributing statement")
  add("distinct_country_texts", !duplicates && !any(as.numeric(as.dist(numerical$distance)) <= policy$tolerance),
      sum(as.numeric(as.dist(numerical$distance)) <= policy$tolerance), "No cross-country exact text/vector duplicates")
  add("observed_source_scope", all(observed), paste(sum(observed), length(observed), sep = "/"),
      "Reference and current sources are observed_input, not replay/engineering")
  add("known_language_genre", all(known) && length(unique(vapply(all_units, `[[`, character(1), "genre"))) == 1L,
      paste(unique(vapply(all_units, `[[`, character(1), "language")), collapse = "|"), "One declared English genre")
  add("source_quality", flags == 0L && length(collection$errors) == 0L,
      flags + length(collection$errors), "No source flags or collection errors")
  maxoov <- if (nrow(stat) && all(is.finite(stat$oov_fraction))) max(stat$oov_fraction) else NA_real_
  add("vocabulary_coverage", is.finite(maxoov) && maxoov <= policy$max_oov_fraction,
      maxoov, paste("Maximum statement OOV <=", policy$max_oov_fraction))
  add("statement_support", all(stat$eligible_tokens >= policy$min_eligible_tokens),
      min(stat$eligible_tokens), paste("At least", policy$min_eligible_tokens, "eligible tokens per statement"))
  add("cluster_size", numerical$selection_size_admissible, cnd$min_cluster_size,
      paste("Min size >=", policy$min_cluster_size, "; max share <=", policy$max_cluster_fraction))
  add("silhouette", cnd$mean_silhouette >= policy$min_mean_silhouette, cnd$mean_silhouette,
      paste("Mean silhouette >=", policy$min_mean_silhouette))
  success <- cnd$successful_replicates / cnd$planned_replicates
  add("replicate_delivery", success >= policy$min_success_fraction, success,
      paste("Successful finite-ARI fraction >=", policy$min_success_fraction))
  add("partition_stability", is.finite(cnd$mean_ari) && cnd$mean_ari >= policy$min_mean_ari,
      cnd$mean_ari, paste("Mean subset ARI >=", policy$min_mean_ari))
  j <- finite_min(cs$mean_jaccard)
  add("clusterwise_stability", is.finite(j) && j >= policy$min_cluster_mean_jaccard,
      j, paste("Every cluster mean subset Jaccard >=", policy$min_cluster_mean_jaccard))
  support <- finite_min(cs$evaluable_fraction)
  add("clusterwise_evaluability", is.finite(support) && support >= policy$min_cluster_evaluable_fraction,
      support, paste("Every cluster evaluable fraction >=", policy$min_cluster_evaluable_fraction))
  checks <- do.call(rbind, checks)
  list(checks = checks, passed = all(checks$state == "pass"), publication_eligible = FALSE,
       release_status = "audit_only", empirical_validation_completed = FALSE,
       interpretation = "Engineering screening only; passing is not empirical release approval")
}

hc_execute <- function(feature, cp, root, clock = utc_now) {
  i2_validate_features(feature, cp, root)
  p <- hc_policy(root)
  fingerprint <- sha_object(feature)
  numerical <- hc_compute(feature$current$country$x, p)
  collection <- if (is.null(cp)) list(errors = list()) else cp$brief$collection
  quality <- hc_quality(numerical, feature, collection, p)
  assert(identical(sha_object(feature), fingerprint), "M07 mutated frozen feature input")
  value <- list(schema = HC_SCHEMA, method_id = "M07", policy = p, policy_sha256 = sha_object(p),
    feature_sha256 = fingerprint, fitted_reference_id = feature$fitted_reference_id,
    source_snapshot_id = feature$source_snapshot_id, source_as_of_cutoff = feature$source_as_of_cutoff,
    event_cutoff = feature$event_cutoff, created_at = clock(),
    runtime = list(R = as.character(getRversion()), cluster = as.character(packageVersion("cluster")),
                   Matrix = as.character(packageVersion("Matrix"))),
    numerical = numerical, quality = quality, collection = collection,
    source_index = feature$current$country$rows,
    fit_status = "fitted_current_hierarchy_on_frozen_features", publication_eligible = FALSE)
  value$result_id <- sha_object(value)
  value
}

hc_validate <- function(value, feature, root, cp = NULL, recompute = TRUE) {
  assert(identical(value$schema, HC_SCHEMA) && identical(value$method_id, "M07"), "Wrong M07 schema")
  assert(identical(value$result_id, sha_object(value[setdiff(names(value), "result_id")])), "M07 result hash mismatch")
  p <- hc_policy(root)
  assert(identical(value$runtime, list(R=as.character(getRversion()), cluster=as.character(packageVersion("cluster")), Matrix=as.character(packageVersion("Matrix")))), "Hierarchical runtime identity mismatch")
  assert(identical(value$policy, p) && identical(value$policy_sha256, sha_object(p)), "M07 policy mismatch")
  i2_validate_features(feature, cp, root)
  assert(identical(value$feature_sha256, sha_object(feature)) &&
    identical(value$fitted_reference_id, feature$fitted_reference_id) &&
    identical(value$source_snapshot_id, feature$source_snapshot_id), "M07 source/reference binding mismatch")
  assert(identical(value$source_as_of_cutoff, feature$source_as_of_cutoff) &&
    identical(value$event_cutoff, feature$event_cutoff) &&
    parse_utc(value$created_at) >= parse_utc(feature$created_at), "M07 time binding invalid")
  assert(identical(value$source_index, feature$current$country$rows), "M07 country metadata changed")
  if (!is.null(cp)) assert(identical(value$collection, cp$brief$collection), "M07 collection context changed")
  assert(identical(value$publication_eligible, FALSE) &&
    identical(value$quality$publication_eligible, FALSE) && identical(value$quality$release_status, "audit_only"),
    "M07 cannot publish through a readiness flag")
  if (recompute) {
    expected <- hc_compute(feature$current$country$x, p)
    assert(identical(expected, value$numerical), "M07 numerical/resample artifact fails independent recomputation")
  }
  expected_quality <- hc_quality(value$numerical, feature, value$collection, p)
  assert(identical(expected_quality, value$quality), "M07 quality does not match its numerical/source evidence")
  invisible(TRUE)
}

hc_write_tables <- function(value, run) {
  n <- value$numerical
  out <- file.path(run, "audit/hierarchical"); dir.create(out, recursive = TRUE, showWarnings = FALSE)
  for (name in c("candidates", "partitions", "resample_plan", "resample_ledger", "resample_memberships",
                 "cluster_resample_jaccard", "cluster_stability", "linkage_sensitivity"))
    csv_write(file.path(out, paste0(name, ".csv")), n[[name]])
  csv_write(file.path(out, "quality_checks.csv"), value$quality$checks)
  meta <- value$source_index
  meta$cluster <- as.integer(n$selected_groups[match(meta$iso3, names(n$selected_groups))])
  meta$included <- meta$iso3 %in% names(n$selected_groups)
  meta$exclusion_reason <- ifelse(meta$included, "", "Zero frozen feature vector; not assigned")
  meta$reference_id <- value$fitted_reference_id; meta$source_snapshot_id <- value$source_snapshot_id
  csv_write(file.path(out, "country_assignments.csv"), meta)
  for (name in c("distance", "coassignment", "pair_opportunities", "pair_together"))
    csv_write(file.path(out, paste0(name, ".csv")), data.frame(iso3 = rownames(n[[name]]), n[[name]], check.names = FALSE))
  json_write(file.path(out, "summary.json"), list(method_id = "M07", selected_candidate = n$selected_id,
    selected_k = n$selected_k, engineering_screen_passed = value$quality$passed,
    publication_eligible = FALSE, release_status = "audit_only", feature_sha256 = value$feature_sha256,
    reference_id = value$fitted_reference_id, result_id = value$result_id,
    interpretation = "Lexical groups, not political blocs. Roster-deletion sensitivity is not a confidence interval."))
}
