load_readout <- function(root, envir = parent.frame()) {
  for (name in c("core.R", "sources.R", "analysis.R", "email.R", "bridge.R", "runner.R")) {
    sys.source(file.path(root, "R", name), envir = envir)
  }
  invisible(TRUE)
}
