# Executable live Shiny/controller acceptance test. A skipped dependency check
# is reported distinctly from a passing UI test.
args <- commandArgs(trailingOnly = TRUE)
root <- normalizePath(if (length(args)) args[[1L]] else ".", winslash = "/")
setwd(root)
lib <- file.path(root, "library")
if (dir.exists(lib)) .libPaths(c(lib, .libPaths()))
needed <- c("shiny", "callr", "jsonlite", "digest", "htmltools", "zip")
missing <- needed[!vapply(needed, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) {
  writeLines(c("NOT EXECUTED", paste("Missing packages:", paste(missing, collapse = ", "))),
             file.path(root, "validation", "shiny_runtime_status.txt"))
  cat("NOT EXECUTED: live Shiny acceptance. Missing packages:", paste(missing, collapse = ", "), "\n")
  quit(status = 3L)
}
env <- new.env(parent = globalenv())
sys.source(file.path(root, "app.R"), envir = env)
shiny::testServer(env$make_server(root), {
  session$setInputs(dates = as.Date(c("2026-09-23", "2026-09-25")), source = "demo", topics = c("Climate finance", "Food security"))
  session$setInputs(generate = 1L)
  stopifnot(isTRUE(state$running))
  first_pid <- state$process$get_pid()
  session$setInputs(generate = 2L)
  stopifnot(identical(state$process$get_pid(), first_pid))
  deadline <- Sys.time() + 90
  while (isTRUE(state$running) && Sys.time() < deadline) {
    Sys.sleep(0.1)
    session$elapse(500)
    session$flushReact()
  }
  stopifnot(!isTRUE(state$running), !is.null(state$result),
    identical(state$result$tracked$summary$topic, c("Climate finance", "Food security")),
    sum(state$result$statements$status == "available") == 18L,
    length(state$result$packets) == 5L,
    file.exists(state$result$files$eml))
  session$setInputs(generate = 3L)
  stopifnot(isTRUE(state$running))
  session$setInputs(cancel = 1L)
  stopifnot(!isTRUE(state$running), is.null(state$result), identical(state$progress$state, "cancelled"))
})
writeLines(c("PASSED: live Shiny testServer acceptance", capture.output(sessionInfo())),
           file.path(root, "validation", "shiny_runtime_status.txt"))
cat("PASSED: Shiny server generation, duplicate-click protection, and cancellation.\n")
