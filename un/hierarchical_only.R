#!/usr/bin/env Rscript
# Reuse an archived M02 feature artifact. No source collection or other model fits.
main <- function() {
  self <- sub("^--file=", "", commandArgs()[grepl("^--file=", commandArgs())][1])
  root <- normalizePath(dirname(self), winslash = "/", mustWork = TRUE)
  opt <- list(input = "", output = "", minimal = "false")
  for (a in commandArgs(trailingOnly = TRUE)) {
    if (a == "--help") {
      cat("Rscript hierarchical_only.R --input=ARCHIVED_RUN --output=NEW_DIRECTORY --minimal=true|false\n")
      return(invisible(NULL))
    }
    if (!grepl("^--[^=]+=", a)) stop("Use --name=value arguments")
    k <- sub("^--([^=]+)=.*$", "\\1", a)
    if (!k %in% names(opt)) stop("Unknown argument: ", k)
    opt[[k]] <- sub("^--[^=]+=", "", a)
  }
  if (!opt$minimal %in% c("true", "false")) stop("Invalid --minimal value")
  options(unbrief.minimal = identical(opt$minimal, "true"), unbrief.root = root)
  libfile <- file.path(root, "config/library_path.txt")
  if (file.exists(libfile)) .libPaths(c(readLines(libfile, warn = FALSE)[1], .libPaths()))
  for (f in list.files(file.path(root, "R"), pattern = "^[0-9].*\\.R$", full.names = TRUE)) source(f)
  need_packages(c("Matrix", "cluster"))
  input <- normalizePath(opt$input, winslash = "/", mustWork = TRUE)
  assert(nzchar(opt$output) && !dir.exists(opt$output) && !file.exists(opt$output), "Use a new output directory")
  assert(file.exists(file.path(input, "SHA256SUMS.txt")), "Input must have a recorded archive hash manifest")
  for (line in readLines(file.path(input, "SHA256SUMS.txt"), warn = FALSE)) {
    assert(grepl("^[0-9a-f]{64}  ", line), "Malformed input hash manifest")
    rel <- relative_path(substring(line, 67))
    assert(identical(sha_file(file.path(input, rel)), substr(line, 1, 64)), paste("Input integrity failed:", rel))
  }
  fpath <- file.path(input, "audit/analytics/artifacts/M02.rds")
  feature <- readRDS(fpath)
  cp <- readRDS(file.path(input, "checkpoint.rds"))
  i2_validate_features(feature, cp, root)
  hash_before <- sha_file(fpath)
  assert(dir.create(opt$output, recursive = TRUE), "Could not create output")
  run <- normalizePath(opt$output, winslash = "/", mustWork = TRUE)
  tryCatch({
    dir.create(file.path(run, "audit/analytics/artifacts"), recursive = TRUE)
    immutable_write(file.path(run, "audit/analytics/artifacts/M02.rds"), read_bytes(fpath))
    value <- hc_execute(feature, cp, root)
    hc_validate(value, feature, root, cp)
    immutable_write(file.path(run, "audit/analytics/artifacts/M07.rds"), serialize(value, NULL, version = 3))
    hc_write_tables(value, run)
    figure <- hc_run_figure(root, run)
    assert(figure$state == "executed", "Audit figure failed; inspect log")
    write_text(file.path(run, "audit.html"), c('<!doctype html><html><head><meta charset="utf-8"><title>Hierarchical audit</title><style>body{font:15px Arial;color:#202B38;padding:24px}table{border-collapse:collapse}td,th{border-bottom:1px solid #D6DEE7;padding:8px;text-align:left}</style></head><body>', hc_audit_block(run), '</body></html>'))
    assert(identical(sha_file(fpath), hash_before), "Original frozen M02 bytes changed")
    json_write(file.path(run, "validation.json"), list(computations = "executed_and_recomputed_in_R",
      M02_byte_unchanged = TRUE, M07 = "audit_only", PAM_executed = FALSE,
      engineering_screen_passed = value$quality$passed,
      planned_replicates = nrow(value$numerical$resample_ledger),
      success_replicates = sum(value$numerical$resample_ledger$status == "executed")))
    write_text(file.path(run, "R_sessionInfo.txt"), capture.output(sessionInfo()))
    paths <- sort(list.files(run, recursive = TRUE, full.names = TRUE), method = "radix")
    write_text(file.path(run, "SHA256SUMS.txt"), paste(vapply(paths, sha_file, character(1)), substring(paths, nchar(run) + 2), sep = "  "))
    cat("Executed successfully: hierarchical-only audit; original frozen M02 unchanged; PAM not run.\n")
  }, error = function(e) {
    json_write(file.path(run, "FAILED.json"), list(error = conditionMessage(e), M07 = "not_delivered", no_email_sent = TRUE))
    stop(e)
  })
}
tryCatch(main(), error = function(e) { message(conditionMessage(e)); quit(status = 1L) })
