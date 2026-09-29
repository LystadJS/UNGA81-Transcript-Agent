# Reproducible synthetic end-to-end run. No Shiny or remote model is required.
args <- commandArgs(trailingOnly = TRUE)
root <- normalizePath(if (length(args)) args[[1L]] else ".", winslash = "/")
source(file.path(root, "R", "load.R"))
load_readout(root, globalenv())
config <- new_config("2026-09-23", "2026-09-25", DEFAULT_TOPICS, source = "demo")
out <- tempfile("demo_", tmpdir = file.path(root, "runtime"))
dir.create(dirname(out), recursive = TRUE, showWarnings = FALSE)
result <- run_readout(config, out, root)
cat("Synthetic demo complete.\nEML:", result$files$eml, "\nHTML:", result$files$html,
    "\nPDF:", if (nzchar(result$files$pdf)) result$files$pdf else result$pdf$reason,
    "\nD1 integration: not executed\n")
