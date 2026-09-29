# Local-only application launcher. Does not install dependencies or send email.
args <- commandArgs(trailingOnly = TRUE)
root <- normalizePath(if (length(args)) args[[1L]] else ".", winslash = "/")
setwd(root)
lib <- file.path(root, "library")
if (dir.exists(lib)) .libPaths(c(lib, .libPaths()))
needed <- c("shiny", "callr", "jsonlite", "digest", "htmltools", "zip")
missing <- needed[!vapply(needed, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop("First run Setup.bat. Missing R packages: ", paste(missing, collapse = ", "), call. = FALSE)
if (packageVersion("shiny") < "1.8.1") stop("This app requires Shiny 1.8.1 or later.", call. = FALSE)
options(shiny.host = "127.0.0.1")
cat("Opening the local readout interface. Keep this window open while using the app.\n")
shiny::runApp(appDir = root, host = "127.0.0.1", launch.browser = TRUE)
