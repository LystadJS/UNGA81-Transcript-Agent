# One isolated job per run; Shiny launches this in a child R process via callr.
# CLI/tests can invoke the same function synchronously without Shiny.

run_readout <- function(config, job_dir, root, paths = character(), display_names = basename(paths), make_pdf = TRUE) {
  if (file.exists(file.path(job_dir, "result.rds"))) user_error("This run folder already has a result. Create a new run instead.")
  dir.create(job_dir, recursive = TRUE, showWarnings = FALSE, mode = "0700")
  job_dir <- normalizePath(job_dir, winslash = "/")
  run_id <- basename(job_dir)
  set_progress(job_dir, "validation", 5, "Checking the reporting period and topic definitions.")
  tryCatch({
    # Validate the same contract again in the child process, not only at the UI.
    rebuilt <- new_config(config$start_date, config$end_date,
      vapply(config$fixed_topics, `[[`, character(1), "label"),
      setNames(lapply(config$fixed_topics, function(x) list(include = unlist(x$include), exclude = unlist(x$exclude))),
        vapply(config$fixed_topics, `[[`, character(1), "label")), config$source)
    if (!identical(to_json(rebuilt$fixed_topics), to_json(config$fixed_topics))) user_error("The topic request is invalid.")
    if (!isTRUE(config$discover_themes) || isTRUE(config$external_processing) || config$email_delivery != "draft_only") {
      user_error("The request does not match the no-send, full-corpus prototype contract.")
    }
    write_json(config, file.path(job_dir, "request.json"))
    saveRDS(config, file.path(job_dir, "request.rds"))
    if (config$source == "d1") {
      result <- run_d1_adapter(config, job_dir, paths, display_names)
      atomic_rds(result, file.path(job_dir, "result.rds"))
      set_progress(job_dir, "complete", 100, "D1 draft is ready for review.", "complete")
      return(result)
    }
    if (config$source == "demo") {
      paths <- file.path(root, "examples", "synthetic_statements.csv")
      display_names <- "SYNTHETIC_TRAINING_DATA.csv"
    }
    set_progress(job_dir, "sources", 12, "Archiving source files and checking transcript metadata.")
    statements <- load_inputs(paths, display_names, file.path(job_dir, "sources"))
    statements <- scope_statements(statements, config)
    write_safe_csv(statements[, setdiff(names(statements), "text"), drop = FALSE],
                   file.path(job_dir, "coverage.csv"))
    saveRDS(statements, file.path(job_dir, "statements.rds"))
    set_progress(job_dir, "tracked", 32, "Finding exact wording for your topics and retaining source quotations.")
    tracked <- match_topics(statements, config$fixed_topics)
    set_progress(job_dir, "features", 48, "Building the separate full-corpus research representation.")
    features <- build_reference_features(statements)
    saveRDS(features, file.path(job_dir, "prototype_features.rds"))
    set_progress(job_dir, "discovery", 58, "Checking text groups and their stability; research results remain audit-only.")
    discovery <- fit_reference_discovery(features, statements)
    saveRDS(discovery, file.path(job_dir, "discovery.rds"))
    write_safe_csv(tracked$summary, file.path(job_dir, "tracked_issue_candidates.csv"))
    write_safe_csv(tracked$evidence, file.path(job_dir, "source_evidence.csv"))
    write_safe_csv(discovery$candidates, file.path(job_dir, "theme_candidates_AUDIT_ONLY.csv"))
    write_safe_csv(discovery$diagnostics, file.path(job_dir, "clustering_diagnostics_AUDIT_ONLY.csv"))
    validate_evidence(tracked$evidence, statements)
    packets <- make_packets(config)
    validate_packets(packets)
    write_json(packets, file.path(job_dir, "report_packets.json"))
    set_progress(job_dir, "email", 78, "Building the unsent email and checking its five analytical sections.")
    email <- render_email(config, statements, tracked, packets, run_id)
    write_utf8(email$html, file.path(job_dir, "readout.html"))
    write_utf8(email$text, file.path(job_dir, "readout.txt"))
    write_utf8(email$eml, file.path(job_dir, "readout.eml"))
    html_slots <- regmatches(email$html, gregexpr('data-output-id="O[1-5]"', email$html))[[1L]]
    if (length(html_slots) != 5L) user_error("The email did not pass the five-section check.", "publication_failed")
    set_progress(job_dir, "export", 89, "Preparing exports and recording the run's source fingerprints.")
    pdf <- if (make_pdf) render_pdf(file.path(job_dir, "readout.html"), file.path(job_dir, "readout.pdf"), job_dir, file.path(root, "scripts", "print_pdf.py")) else
      list(status = "not_requested", reason = "PDF creation was not requested for this run.")
    writeLines(capture.output(sessionInfo()), file.path(job_dir, "sessionInfo.txt"))
    provenance <- list(app_version = MVP_VERSION, engine = "prototype_reference_not_D1",
      run_id = run_id, request_sha256 = sha256_file(file.path(job_dir, "request.json")),
      code_sha256 = readout_code_hash(root), completed_at_utc = utc_now(),
      source_files = as.list(display_names), feature_hash = features$fingerprint,
      feature_namespace = "prototype_tfidf_v1", discovery_uses_all_eligible_texts = TRUE,
      analytical_outputs_released = 0L, sent = FALSE, external_processing = FALSE,
      approved_D1_integration = "not_executed_checkpoint_bytes_unavailable_at_build")
    write_json(provenance, file.path(job_dir, "provenance.json"))
    inventory <- list.files(job_dir, recursive = TRUE, full.names = TRUE)
    inventory <- inventory[!dir.exists(inventory) & !grepl("progress\\.rds$", inventory)]
    manifest <- data.frame(path = substring(inventory, nchar(job_dir) + 2L),
      sha256 = vapply(inventory, sha256_file, character(1)), stringsAsFactors = FALSE)
    utils::write.csv(manifest, file.path(job_dir, "manifest.csv"), row.names = FALSE)
    files <- list(html = file.path(job_dir, "readout.html"), eml = file.path(job_dir, "readout.eml"),
      text = file.path(job_dir, "readout.txt"), pdf = if (pdf$status == "created") file.path(job_dir, "readout.pdf") else "",
      evidence = file.path(job_dir, "source_evidence.csv"), coverage = file.path(job_dir, "coverage.csv"),
      request = file.path(job_dir, "request.json"))
    result <- list(run_id = run_id, engine = "prototype_reference_not_D1", config = config,
      statements = statements, tracked = tracked, discovery = discovery, packets = packets,
      pdf = pdf, files = files, provenance = provenance, feature_hash = features$fingerprint,
      completed_at_utc = utc_now(), request_sha256 = provenance$request_sha256)
    atomic_rds(result, file.path(job_dir, "result.rds"))
    message <- if (sum(statements$status == "available") == 0L) "Coverage-only draft ready. No transcript text passed the date and source checks." else
      "Prototype draft ready. Review the source extracts; analytical candidates are not released."
    set_progress(job_dir, "complete", 100, message, "complete")
    result
  }, error = function(e) {
    code <- e$code %||% "run_failed"
    message <- if (inherits(e, "readout_user_error")) conditionMessage(e) else
      "The run stopped before completion. Your inputs are preserved; the technical log has details."
    write_utf8(paste(utc_now(), class(e)[[1L]], conditionMessage(e), sep = "\n"), file.path(job_dir, "error.log"))
    atomic_rds(list(message = message, code = code), file.path(job_dir, "error.rds"))
    set_progress(job_dir, "failed", 0, message, "failed")
    stop(e)
  })
}
