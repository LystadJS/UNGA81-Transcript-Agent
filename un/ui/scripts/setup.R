# Explicit one-time dependency installation. No system security policy is changed.
args <- commandArgs(trailingOnly = TRUE)
root <- normalizePath(if (length(args)) args[[1L]] else ".", winslash = "/")
if (getRversion() < "4.3.0") stop("R 4.3 or later is required. The backend was tested on R 4.6.1.", call. = FALSE)
lib <- file.path(root, "library")
dir.create(lib, recursive = TRUE, showWarnings = FALSE)
.libPaths(c(lib, .libPaths()))
repo <- Sys.getenv("UN_READOUT_CRAN", "https://cloud.r-project.org")
options(repos = c(CRAN = repo), timeout = 240)
needed <- c("shiny", "callr", "jsonlite", "digest", "htmltools", "zip")
missing <- needed[!vapply(needed, requireNamespace, logical(1), quietly = TRUE)]
cat("This installs R packages into:", lib, "\nRepository:", repo,
    "\nUse only where your organization permits this software and repository.\n")
if (length(missing)) install.packages(missing, lib = lib, dependencies = NA)
if (!requireNamespace("pagedown", quietly = TRUE)) {
  tryCatch(install.packages("pagedown", lib = lib, dependencies = NA),
    error = function(e) warning("Optional PDF dependencies were not installed. Email/HTML remain available."))
}
missing <- needed[!vapply(needed, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop("Setup incomplete. Packages still missing: ", paste(missing, collapse = ", "), call. = FALSE)
if (packageVersion("shiny") < "1.8.1") stop("Shiny 1.8.1 or later is required. Update through the approved repository.", call. = FALSE)
installed <- installed.packages()[, c("Package", "Version", "LibPath"), drop = FALSE]
utils::write.csv(installed, file.path(root, "config", "packages-installed.local.csv"), row.names = FALSE)
writeLines(capture.output(sessionInfo()), file.path(root, "config", "setup-session.local.txt"))
cat("Setup completed. Open Start.bat (Windows) or run Rscript scripts/launch.R from this folder.\n")
