# Managed, source-bound M07 execution. M09/PAM is implemented separately in R/20_pam_accounting.R.
hc_gates <- function(value, feature, error = "") {
  list(
    distance_matrix = list(state = if (is.null(feature)) "unestablished" else "pass",
      blocker_class = "data", reason = if (is.null(feature)) "No verified M02 frozen feature artifact."
      else paste("Euclidean chord distance from all frozen features; reference", feature$fitted_reference_id)),
    cluster_stability = list(state = if (is.null(value)) "unestablished" else if (value$quality$passed) "pass" else "fail",
      blocker_class = "quality", reason = if (is.null(value)) paste("No valid hierarchy/stability artifact.", error)
      else if (value$quality$passed) "Engineering cluster checks passed; M07 remains audit-only pending independent release validation."
      else paste("Fitted hierarchy retained; failed checks:", paste(value$quality$checks$check[value$quality$checks$state != "pass"], collapse = ", "))))
}

hc_run_managed <- function(id, cp, root, run, snapshot, context, available, clock = utc_now) {
  assert(identical(id, "M07"), "Only hierarchical clustering is implemented in this adapter")
  feature <- value <- NULL
  artifact_ref <- artifact_hash <- artifact_time <- error_log <- error <- ""
  status <- "failed"; stage <- "preflight"; fit_status <- "no_valid_fit_delivered"
  tryCatch({
    if (!all(available)) i2_abort("dependency", "M07 requires Matrix, stats and cluster")
    path <- file.path(run, "audit/analytics/artifacts/M02.rds")
    if (!file.exists(path)) i2_abort("data", "M02 did not produce a frozen feature artifact")
    candidate <- readRDS(path); i2_validate_features(candidate, cp, root)
    assert(identical(candidate$source_snapshot_id, snapshot$snapshot_id), "M07 dependency uses another snapshot")
    feature <- candidate
    stage <- "fit_current_hierarchy_and_roster_sensitivity"
    value <- hc_execute(feature, cp, root, clock)
    hc_validate(value, feature, root, cp)
    artifact_ref <- "audit/analytics/artifacts/M07.rds"
    bytes <- serialize(value, NULL, version = 3)
    immutable_write(file.path(run, artifact_ref), bytes)
    artifact_hash <- sha_raw(bytes); artifact_time <- value$created_at
    hc_write_tables(value, run)
    status <- if (value$quality$passed) "executed" else "withheld_quality"
    fit_status <- value$fit_status
  }, error = function(e) {
    error <<- conditionMessage(e)
    kinds <- class(e)[startsWith(class(e), "d1_i2_")]
    kind <- if (length(kinds)) sub("^d1_i2_", "", kinds[1]) else ""
    status <<- if (kind %in% c("data", "resources", "dependency", "version")) paste0("blocked_", kind) else "failed"
    if (nzchar(artifact_ref) && file.exists(file.path(run, artifact_ref))) {
      target <- file.path(run, "audit/analytics/errors/M07_invalid_candidate.rds")
      dir.create(dirname(target), recursive = TRUE, showWarnings = FALSE)
      assert(file.rename(file.path(run, artifact_ref), target), "Could not preserve invalid M07 incident")
    }
    artifact_ref <<- artifact_hash <<- artifact_time <<- ""; value <<- NULL
    error_log <<- "audit/analytics/errors/M07.txt"
    write_text(file.path(run, error_log), error)
  })
  gr <- hc_gates(value, feature, error)
  reason <- if (is.null(value)) paste("No valid M07 result:", error) else gr$cluster_stability$reason
  proof_path <- "audit/analytics/method_proofs/M07.json"
  proof <- list(schema = "D1-HC-method-proof-v1", method_id = "M07", context = context,
    collection = cp$brief$collection, artifact_ref = artifact_ref, artifact_sha256 = artifact_hash,
    feature_artifact_ref = if (is.null(feature)) "" else "audit/analytics/artifacts/M02.rds",
    feature_artifact_sha256 = if (is.null(feature)) "" else sha_object(feature),
    error = error, terminal_status = status, actual_stage = stage,
    fit_status = fit_status, publication_eligible = FALSE, gates = gr)
  json_write(file.path(run, proof_path), proof)
  gate_rows <- lapply(names(gr), function(g) c(list(method_id = id, gate = g), gr[[g]],
    list(evidence_path = proof_path, evidence_sha256 = sha_file(file.path(run, proof_path)))))
  list(status = status, reason = reason, stage = stage, fit_status = fit_status,
    artifact_ref = artifact_ref, artifact_hash = artifact_hash, artifact_time = artifact_time,
    error_log = error_log, gr = gate_rows, value = value, model_release_status = "audit_only")
}

hc_validate_proof <- function(proof, run, root = getOption("unbrief.root", getwd())) {
  assert(identical(proof$method_id, "M07") && identical(proof$publication_eligible, FALSE), "Wrong hierarchical proof")
  feature <- value <- NULL
  if (nzchar(proof$feature_artifact_ref)) {
    assert(identical(proof$feature_artifact_ref, "audit/analytics/artifacts/M02.rds"), "Wrong M07 feature path")
    path <- file.path(run, proof$feature_artifact_ref)
    assert(identical(sha_file(path), proof$feature_artifact_sha256), "M07 dependency hash mismatch")
    feature <- readRDS(path); i2_validate_features(feature, root = root)
    assert(identical(feature$source_snapshot_id, proof$context$snapshot_id), "M07 proof uses another snapshot")
  }
  if (nzchar(proof$artifact_ref)) {
    assert(identical(proof$artifact_ref, "audit/analytics/artifacts/M07.rds") && !is.null(feature), "Wrong M07 result path")
    assert(identical(sha_file(file.path(run, proof$artifact_ref)), proof$artifact_sha256), "M07 artifact hash mismatch")
    value <- readRDS(file.path(run, proof$artifact_ref))
    hc_validate(value, feature, root)
    assert(identical(json_minimal(value$collection), json_minimal(proof$collection)), "M07 source quality proof mismatch")
  }
  expected <- hc_gates(value, feature, str1(proof$error))
  assert(identical(names(expected), names(proof$gates)), "M07 prerequisite list changed")
  for (g in names(expected)) assert(identical(expected[[g]], proof$gates[[g]]), "M07 readiness contradicts recomputed evidence")
  expected
}

hc_run_figure <- function(root, run) {
  output <- "audit/figures/Figure_6_Hierarchical_Clustering_Audit.png"
  if (!file.exists(file.path(run, "audit/analytics/artifacts/M07.rds"))) {
    row <- list(script = "Figure_6_Hierarchical_Audit.R", state = "blocked_data", artifact_ref = "", sha256 = "", log = "", inline_in_email = FALSE)
  } else {
    dir.create(file.path(run, "logs"), recursive = TRUE, showWarnings = FALSE)
    log <- "logs/Figure_6_Hierarchical_Audit.R.log"
    status <- tryCatch(system2(file.path(R.home("bin"), "Rscript"),
      vapply(c("--vanilla", file.path(root, "R/Figure_6_Hierarchical_Audit.R"), run), shQuote, character(1)),
      stdout = file.path(run, log), stderr = file.path(run, log)), error = function(e) {
        write_text(file.path(run, log), conditionMessage(e)); 1L
      })
    ok <- identical(as.integer(status), 0L) && file.exists(file.path(run, output))
    row <- list(script = "Figure_6_Hierarchical_Audit.R", state = if (ok) "executed" else "failed",
      artifact_ref = if (ok) output else "", sha256 = if (ok) sha_file(file.path(run, output)) else "",
      log = log, inline_in_email = FALSE)
  }
  csv_write(file.path(run, "audit/analytics/hierarchical_figure_ledger.csv"), list(row), names(row))
  invisible(row)
}

hc_audit_block <- function(run) {
  path <- file.path(run, "audit/analytics/artifacts/M07.rds")
  if (!file.exists(path)) return('<h2>Hierarchical clustering — unavailable</h2><p>See M07 in the method ledger.</p>')
  v <- readRDS(path); n <- v$numerical
  checks <- v$quality$checks
  # Undefined diagnostics remain NA in data; use an explicit text label only here.
  observed_text <- ifelse(is.na(checks$observed), "Not evaluable", checks$observed)
  rows <- vapply(seq_len(nrow(checks)), function(i) sprintf('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>',
    html_escape(checks$check[i]), html_escape(checks$state[i]), html_escape(observed_text[i]), html_escape(checks$criterion[i])), character(1))
  c('<h2>M07 hierarchical clustering — audit only</h2>',
    '<p>The full frozen TF-IDF vectors are used, not PCA/PCoA coordinates. Average linkage is the primary descriptive candidate; complete and Ward.D2 are hierarchical sensitivity checks. These are lexical groups, not geopolitical blocs.</p>',
    sprintf('<p>Selected audit cut: %s. Every candidate and all %d planned resampling records are retained. Conditional country-roster subsampling is not a confidence interval; cluster numbers do not persist across days.</p>', html_escape(n$selected_id), nrow(n$resample_ledger)),
    '<p><a href="audit/hierarchical/country_assignments.csv">Country assignments</a> · <a href="audit/hierarchical/candidates.csv">All linkage/k candidates</a> · <a href="audit/hierarchical/cluster_stability.csv">Clusterwise stability</a> · <a href="audit/hierarchical/resample_ledger.csv">Replicate accounting</a></p>',
    '<table><tr><th>Check</th><th>State</th><th>Observed</th><th>Criterion</th></tr>', rows, '</table>',
    if (file.exists(file.path(run, "audit/figures", HC_IMAGE))) sprintf('<img src="audit/figures/%s" alt="Audit-only hierarchical dendrogram and stability diagnostics" style="max-width:100%%;height:auto">', HC_IMAGE) else
      '<p>Audit figure unavailable; inspect the figure ledger.</p>')
}
