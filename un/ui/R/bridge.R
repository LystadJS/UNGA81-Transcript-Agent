# Versioned D1 boundary. No private config is overwritten; no undocumented legacy
# flags are guessed. A checkpoint without the reviewed v1 interface is blocked.

inspect_d1 <- function(root = Sys.getenv("UN_D1_PIPELINE_ROOT", ""),
                       approved_hash = Sys.getenv("UN_D1_ADAPTER_SHA256", "")) {
  if (!nzchar(root)) {
    candidate <- normalizePath(file.path(getwd(), ".."), winslash = "/", mustWork = FALSE)
    if (file.exists(file.path(candidate, "run_daily.R"))) root <- candidate
  }
  if (nzchar(root) && !nzchar(approved_hash)) {
    pin <- file.path(root, "config", "shiny_adapter.sha256")
    if (file.exists(pin)) approved_hash <- trimws(readLines(pin, warn = FALSE)[[1L]])
  }
  answer <- list(ready = FALSE, status = "not_configured", root = root,
    reason = "The installed D1 checkpoint has not been connected to this interface.")
  if (!nzchar(root)) return(answer)
  if (!dir.exists(root)) {
    answer$status <- "missing_folder"
    answer$reason <- "The configured D1 folder is unavailable. Ask the installation owner to check it."
    return(answer)
  }
  required <- c("run_daily.R", "R/16_analytics_pipeline.R", "R/15_publish_packets.R")
  if (!all(file.exists(file.path(root, required)))) {
    answer$status <- "unrecognized_checkpoint"
    answer$reason <- "The configured folder does not contain the documented D1 entry points."
    return(answer)
  }
  adapter <- file.path(root, "interfaces", "shiny_v1.R")
  if (!file.exists(adapter)) {
    answer$status <- "integration_patch_required"
    answer$reason <- "D1 was found, but it does not expose the reviewed custom-topic interface. No legacy watchlist or release policy was changed."
    return(answer)
  }
  actual <- sha256_file(adapter)
  if (!grepl("^[0-9a-f]{64}$", approved_hash) || !identical(actual, approved_hash)) {
    answer$status <- "adapter_not_approved"
    answer$reason <- "The D1 interface has not passed the installation owner's code-hash approval."
    return(answer)
  }
  answer$ready <- TRUE
  answer$status <- "hash_approved_pending_runtime_handshake"
  answer$adapter <- normalizePath(adapter)
  answer$adapter_sha256 <- actual
  answer$reason <- "The approved D1 interface will be checked again for request compatibility before a run."
  answer
}

validate_d1_capabilities <- function(caps) {
  required <- c("dynamic_topics", "full_corpus_discovery", "immutable_requests",
    "publication_gates", "exactly_five_outputs", "no_send", "honors_no_external_processing")
  if (!is.list(caps) || !identical(caps$request_schema, "un.readout.request.v1") ||
      !all(vapply(required, function(k) isTRUE(caps[[k]]), logical(1)))) {
    user_error("The installed D1 adapter does not support all required safeguards. The run was not started.", "d1_capability_mismatch")
  }
  TRUE
}

assert_inside <- function(path, root) {
  full <- normalizePath(path, mustWork = TRUE, winslash = "/")
  base <- paste0(normalizePath(root, mustWork = TRUE, winslash = "/"), "/")
  if (.Platform$OS.type == "windows") { full <- tolower(full); base <- tolower(base) }
  if (!startsWith(full, base)) user_error("An adapter returned an output outside its assigned run folder.", "adapter_path_violation")
  TRUE
}

run_d1_adapter <- function(config, job_dir, paths, display_names) {
  state <- inspect_d1()
  if (!state$ready) user_error(state$reason, state$status)
  environment <- new.env(parent = globalenv())
  sys.source(state$adapter, envir = environment)
  if (!is.function(environment$un_readout_capabilities) || !is.function(environment$un_readout_run)) {
    user_error("The D1 interface entry points are missing.", "d1_interface_missing")
  }
  caps <- environment$un_readout_capabilities()
  validate_d1_capabilities(caps)
  # A new adapter must explicitly bind this complete immutable request to results.
  request_hash <- sha256_file(file.path(job_dir, "request.json"))
  result <- environment$un_readout_run(
    request = config, request_path = file.path(job_dir, "request.json"),
    request_sha256 = request_hash, pipeline_root = state$root, job_dir = job_dir,
    input_paths = paths, input_names = display_names,
    progress = function(stage, percent, message) set_progress(job_dir, stage, percent, message)
  )
  required <- c("request_sha256", "packets", "config", "statements", "tracked", "discovery", "files", "pdf", "engine")
  if (!is.list(result) || !all(required %in% names(result)) ||
      !identical(result$request_sha256, request_hash) || !identical(result$engine, "d1")) {
    user_error("The D1 result receipt does not match this request. No output was released.", "d1_receipt_failed")
  }
  validate_packets(result$packets, reference = FALSE)
  if (!identical(to_json(result$config$fixed_topics), to_json(config$fixed_topics))) {
    user_error("The D1 result changed the requested topic definitions.", "d1_topic_mismatch")
  }
  if (isTRUE(result$discovery$released)) {
    # Merely returning TRUE is not a release contract. This bridge v0.1 permits no
    # automatic analytical releases until the actual D1 contract is inspected.
    user_error("D1 analytical-release verification is not implemented in this bridge version.", "d1_release_unverified")
  }
  if (any(vapply(result$packets, function(p) isTRUE(p$released) || !is.null(p$payload), logical(1)))) {
    user_error("This bridge version cannot verify a released D1 analytical packet.", "d1_release_unverified")
  }
  for (path in unlist(result$files, use.names = FALSE)) if (nzchar(path)) assert_inside(path, job_dir)
  validate_evidence(result$tracked$evidence, result$statements)
  result$integration <- list(adapter_sha256 = state$adapter_sha256, runtime_handshake = "passed")
  result
}
