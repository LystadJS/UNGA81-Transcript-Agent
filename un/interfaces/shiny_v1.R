# UN Readout <-> D1-I4 integration adapter v1.
# This file is deliberately additive. It does not alter the legacy fixed-topic
# codebook or D1 publication rules used by archived/CLI runs.

un_readout_capabilities <- function() {
  list(
    request_schema = "un.readout.request.v1",
    dynamic_topics = TRUE,
    full_corpus_discovery = TRUE,
    immutable_requests = TRUE,
    publication_gates = TRUE,
    exactly_five_outputs = TRUE,
    no_send = TRUE,
    honors_no_external_processing = TRUE,
    legacy_codebook_unchanged = TRUE,
    adapter_version = "1.0.0-d1-i4"
  )
}

.d1_source_modules <- function(root) {
  env <- new.env(parent = globalenv())
  old <- getwd(); setwd(root); on.exit(setwd(old), add = TRUE)
  files <- list.files(file.path(root, "R"), pattern = "^[0-9].*\\.R$", full.names = TRUE)
  for (f in files) sys.source(f, envir = env)
  for (f in list.files(file.path(root, "R"), pattern = "^Figure_.*\\.R$", full.names = TRUE)) parse(f, encoding = "UTF-8")
  env
}

.d1_statement_frame <- function(cp) {
  rows <- lapply(cp$speeches, function(s) {
    data.frame(
      statement_id = paste0(s$date, "_", s$iso3), country = s$country,
      country_id = s$iso3, region = s$region, speaker = s$speaker,
      speech_date = s$date, language = s$language %||% "en", text = s$text,
      source_url = s$source_url %||% "", source_file = s$source_file %||% "",
      source_sha256 = s$source_sha256, body_sha256 = s$text_sha256,
      declared_status = "available", status = "available",
      discovery_eligible = tolower(s$language %||% "en") %in% c("en", "eng", "english"),
      stringsAsFactors = FALSE
    )
  })
  if (!length(rows)) return(empty_statements())
  do.call(rbind, rows)
}

.d1_adapter_paths <- function(root, request_sha256) {
  stem <- paste0("runtime/shiny/", substr(request_sha256, 1L, 20L))
  list(history = file.path(stem, "history"), cache = file.path(stem, "cache/methods"),
       features = file.path(stem, "models/tfidf_references"), projections = file.path(stem, "models/projection_references"))
}

.d1_html_topic_table <- function(tracked) {
  h <- html_escape
  if (!nrow(tracked$summary)) {
    rows <- '<tr><td colspan="2" style="padding:8px 10px;border-bottom:1px solid #D6DEE7;font-size:12px;color:#202B38;">No tracked issues were requested. Full-corpus discovery still ran.</td></tr>'
  } else {
    rows <- paste(vapply(seq_len(nrow(tracked$summary)), function(i) {
      z <- tracked$summary[i, , drop = FALSE]
      status <- sprintf("%d / %d texts contain literal candidate wording; %d unresolved", z$texts_with_matches, z$eligible_texts, z$unresolved_texts)
      sprintf('<tr><td class="fixed-topic" style="width:28%%;padding:7px 9px;border-bottom:1px solid #D6DEE7;font-size:13px;font-weight:bold;color:#002D74;">%s</td><td style="padding:7px 9px;border-bottom:1px solid #D6DEE7;font-size:12px;line-height:18px;color:#202B38;">%s</td></tr>', h(z$topic), h(status))
    }, character(1)), collapse = "\n")
  }
  paste0('<table class="fixed-watchlist" role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;background:#F6F8FA;margin-bottom:8px;">\n', rows, '\n</table>')
}

.d1_patch_email <- function(run_dir, tracked, config, job_dir) {
  html_path <- file.path(run_dir, "daily_briefing.html")
  text_path <- file.path(run_dir, "daily_briefing.txt")
  if (!file.exists(html_path) || !file.exists(text_path)) user_error("The D1 run did not produce its briefing files.", "d1_output_missing")
  html <- paste(readLines(html_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n")
  table <- .d1_html_topic_table(tracked)
  pattern <- '(?s)<table class="fixed-watchlist".*?</table>'
  if (!grepl(pattern, html, perl = TRUE)) user_error("The D1 email template no longer exposes the expected tracked-issue table.", "d1_template_changed")
  html <- sub(pattern, table, html, perl = TRUE)
  html <- sub("1\\. Fixed-topic monitor", "1. Tracked-issue monitor", html, fixed = FALSE)
  note <- '<div style="font-family:Arial,Helvetica,sans-serif;font-size:11px;line-height:17px;color:#202B38;margin:0 0 9px 0;"><strong>User-selected topics.</strong> Counts are literal candidate matches with retained source evidence. A non-match is unresolved, not absence. These rows do not bypass the D1 classifier/publication gate.</div>'
  html <- sub(pattern, paste0(table, "\n", note), html, perl = TRUE)
  plain <- readLines(text_path, warn = FALSE, encoding = "UTF-8")
  start <- grep("^1\\. FIXED-TOPIC MONITOR$", plain)
  stop <- grep("^2\\. EMERGING ISSUES$", plain)
  custom <- if (nrow(tracked$summary)) vapply(seq_len(nrow(tracked$summary)), function(i) {
    z <- tracked$summary[i, , drop = FALSE]
    sprintf("%s: %d/%d texts contain literal candidate wording; %d unresolved", z$topic, z$texts_with_matches, z$eligible_texts, z$unresolved_texts)
  }, character(1)) else "No tracked issues requested."
  replacement <- c("1. TRACKED-ISSUE MONITOR", "STATUS: not ready", custom,
                   "User-selected rows are evidence-retrieval candidates only. Non-match is unresolved, not absence; D1 publication gates are unchanged.", "")
  if (length(start) == 1L && length(stop) == 1L && stop > start) plain <- c(plain[seq_len(start - 1L)], replacement, plain[stop:length(plain)])
  plain <- paste(plain, collapse = "\n")
  out_html <- file.path(job_dir, "readout.html")
  out_txt <- file.path(job_dir, "readout.txt")
  out_eml <- file.path(job_dir, "readout.eml")
  write_utf8(html, out_html); write_utf8(plain, out_txt)
  boundary <- paste0("unreadout_", substr(sha256_text(c(html, plain)), 1L, 24L))
  subject <- paste0("UN Transcript Readout | ", config$end_date, " | Draft")
  eml <- paste(c("MIME-Version: 1.0", "X-Unsent: 1", paste0("Subject: ", subject),
    paste0('Content-Type: multipart/alternative; boundary="', boundary, '"'), "", paste0("--", boundary),
    "Content-Type: text/plain; charset=UTF-8", "Content-Transfer-Encoding: base64", "", wrap_base64(base64_encode(plain)),
    paste0("--", boundary), "Content-Type: text/html; charset=UTF-8", "Content-Transfer-Encoding: base64", "",
    wrap_base64(base64_encode(html)), paste0("--", boundary, "--"), ""), collapse = "\r\n")
  write_utf8(eml, out_eml)
  list(html = out_html, text = out_txt, eml = out_eml)
}

un_readout_run <- function(request, request_path, request_sha256, pipeline_root, job_dir,
                           input_paths = character(), input_names = character(), progress = function(...) NULL) {
  stopifnot(identical(sha256_file(request_path), request_sha256))
  if (!identical(request$schema_version, "un.readout.request.v1")) user_error("Unsupported readout request schema.", "d1_request_schema")
  if (!isTRUE(request$discover_themes) || isTRUE(request$external_processing) || request$email_delivery != "draft_only") user_error("The request violates the D1 no-send/no-external-AI interface contract.", "d1_request_contract")
  if (request$start_date != request$end_date) user_error("Installed-pipeline mode produces one daily readout at a time. Choose a single reporting date.", "d1_daily_only")
  if (length(input_paths)) user_error("Installed-pipeline mode uses the pipeline's own source collector. Use 'my transcript files' for uploaded TXT/CSV/ZIP sources.", "d1_source_contract")
  day <- request$start_date
  progress("d1_source", 12, "Running the installed transcript pipeline on the full daily corpus.")
  d1 <- .d1_source_modules(pipeline_root)
  old <- getwd(); setwd(pipeline_root); on.exit(setwd(old), add = TRUE)
  replay <- dir.exists(file.path(pipeline_root, "examples", day))
  source_mode <- if (replay) "replay" else "live"
  cfg_path <- if (replay) file.path(pipeline_root, "config", "config.example.json") else file.path(pipeline_root, "config", "config.extractive.json")
  cfg <- d1$load_config(cfg_path)
  isolated <- .d1_adapter_paths(pipeline_root, request_sha256)
  cfg$analytics$history_dir <- isolated$history
  cfg$analytics$method_cache_dir <- isolated$cache
  cfg$analytics$feature_reference_dir <- isolated$features
  cfg$analytics$projection_reference_dir <- isolated$projections
  cfg$generation$fail_on_review_required <- FALSE
  d1_run <- file.path(job_dir, "d1_run")
  # finalize_run() maintains a legacy output/latest.json pointer. The interface
  # run lives outside output/, so preserve and restore that shared legacy pointer.
  latest_path <- file.path(pipeline_root, "output", "latest.json")
  latest_existed <- file.exists(latest_path)
  latest_raw <- if (latest_existed) readBin(latest_path, "raw", n = file.info(latest_path)$size) else raw()
  restore_latest <- function() {
    if (latest_existed) { con <- file(latest_path, "wb"); writeBin(latest_raw, con); close(con) }
    else if (file.exists(latest_path)) unlink(latest_path)
  }
  on.exit(restore_latest(), add = TRUE)
  dir.create(d1_run, recursive = TRUE, showWarnings = FALSE)
  dir.create(file.path(d1_run, "logs"), showWarnings = FALSE)
  dir.create(file.path(d1_run, "figures"), showWarnings = FALSE)
  budget <- new.env(parent = emptyenv()); budget$used <- 0L
  d1$prepare_run(pipeline_root, d1_run, cfg, source_mode, day, "", request$requested_at_utc, budget)
  progress("d1_analytics", 45, "Running D1 method accounting and unsupervised diagnostics on the full corpus.")
  d1$prepare_analytics(pipeline_root, d1_run, cfg)
  d1$run_audit_figures(pipeline_root, d1_run)
  d1$finalize_run(pipeline_root, d1_run, cfg)
  restore_latest()
  cp <- readRDS(file.path(d1_run, "checkpoint.rds"))
  statements <- .d1_statement_frame(cp)
  progress("tracked", 68, "Applying your tracked topics without changing the discovery corpus.")
  tracked <- match_topics(statements, request$fixed_topics)
  validate_evidence(tracked$evidence, statements)
  write_safe_csv(tracked$summary, file.path(job_dir, "tracked_issue_candidates.csv"))
  write_safe_csv(tracked$evidence, file.path(job_dir, "source_evidence.csv"))
  write_safe_csv(statements[, setdiff(names(statements), "text"), drop = FALSE], file.path(job_dir, "coverage.csv"))
  progress("discovery", 76, "Preparing audit-only suggested themes from the same full corpus.")
  features <- build_reference_features(statements)
  discovery <- fit_reference_discovery(features, statements)
  discovery$reason <- paste0("Interface research view only; D1 O2 remains governed by its publication packet. ", discovery$reason)
  discovery$released <- FALSE
  d1_packets <- readRDS(file.path(d1_run, "audit", "analytics", "report_packets.rds"))
  packets <- unname(lapply(d1_packets, function(p) list(id = p$slot_id, title = if (p$slot_id == "O1") "Tracked issues" else p$title,
    status = p$state, released = FALSE, reason = p$reason, payload = NULL, evidence_layer = "D1_PUBLICATION_GATE_RETAINED")))
  validate_packets(packets, reference = FALSE)
  progress("email", 86, "Building the D1 country readout with your tracked-issue rows.")
  email_files <- .d1_patch_email(d1_run, tracked, request, job_dir)
  pdf <- render_pdf(email_files$html, file.path(job_dir, "readout.pdf"), job_dir, file.path(pipeline_root, "ui", "scripts", "print_pdf.py"))
  if (pdf$status != "created" && file.exists(file.path(d1_run, "daily_briefing.pdf"))) {
    file.copy(file.path(d1_run, "daily_briefing.pdf"), file.path(job_dir, "readout.pdf"), overwrite = TRUE)
    pdf <- list(status = "created", engine = "d1_existing_pdf", reason = "Copied the D1-generated PDF.")
  }
  ledger <- tryCatch(utils::read.csv(file.path(d1_run, "audit", "analytics", "method_ledger.csv"), stringsAsFactors = FALSE), error = function(e) data.frame())
  diag <- if (nrow(ledger)) ledger[ledger$method_id %in% c("M02", "M07", "M09"), c("method_id", "method", "terminal_status", "reason", "model_release_status"), drop = FALSE] else data.frame()
  if (!nrow(discovery$diagnostics) && nrow(diag)) discovery$diagnostics <- diag
  manifest <- list(request_sha256 = request_sha256, adapter_version = "1.0.0-d1-i4", d1_source_mode = source_mode,
                   d1_project_version = cfg$project_version %||% "2.5.0-d1-i4-checkpoint", d1_run = normalizePath(d1_run, winslash = "/"),
                   legacy_codebook_unchanged = TRUE, discovery_scope = "all eligible D1 speech text", d1_o2_released = FALSE,
                   email_sent = FALSE, external_ai_used_by_adapter = FALSE)
  write_json(manifest, file.path(job_dir, "d1_integration_receipt.json"))
  files <- list(html = email_files$html, eml = email_files$eml, text = email_files$text,
    pdf = if (pdf$status == "created") file.path(job_dir, "readout.pdf") else "",
    evidence = file.path(job_dir, "source_evidence.csv"), coverage = file.path(job_dir, "coverage.csv"), request = request_path,
    d1_receipt = file.path(job_dir, "d1_integration_receipt.json"))
  list(request_sha256 = request_sha256, packets = packets, config = request, statements = statements,
       tracked = tracked, discovery = discovery, files = files, pdf = pdf, engine = "d1",
       feature_hash = features$fingerprint, d1_run = d1_run,
       integration = list(adapter_version = "1.0.0-d1-i4", source_mode = source_mode, legacy_codebook_unchanged = TRUE))
}
