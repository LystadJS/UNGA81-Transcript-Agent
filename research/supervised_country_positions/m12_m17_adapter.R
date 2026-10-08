# Synthetic-only entry point to the existing I6 M12/M17 research kernels.
# Neither an independent classifier nor a daily/publication integration.
# Usage (repository root):
#   Rscript research/supervised_country_positions/m12_m17_adapter.R M17 \
#     PRIVATE_SYNTHETIC_INPUT.rds PRIVATE_SYNTHETIC_RESULT.rds

stop_if <- function(condition, message) {
  if (isTRUE(condition)) stop(message, call. = FALSE)
}

run_supervised_synthetic <- function(method_id, input) {
  stop_if(!identical(method_id, "M12") && !identical(method_id, "M17"),
          "Only existing M12/M17 kernels are allowed")
  stop_if(!is.list(input) ||
            !identical(input$schema, "un.country-positions.kernel-input.v1") ||
            !identical(input$dataset_kind, "synthetic_engineering") ||
            !identical(input$publication_eligible, FALSE) ||
            !identical(input$source_schema, "un.review.v1"),
          "Expected an unpublished, explicitly synthetic, source-bound input")
  stop_if(!is.list(input$kernel) ||
            !identical(input$kernel$dataset_kind, "synthetic_engineering"),
          "Real/unreviewed labelled data may not be passed to the kernel")
  stop_if(!is.character(input$codebook_version) ||
            length(input$codebook_version) != 1L ||
            !identical(input$codebook_version, "1.0.0"),
          "Incompatible proposition codebook version")
  stop_if(!is.character(input$source_manifest_sha256) ||
            length(input$source_manifest_sha256) != 1L ||
            !grepl("^[a-f0-9]{64}$", input$source_manifest_sha256),
          "Missing source-frame hash; a synthetic hash is never evidence of actual bytes")
  if (identical(method_id, "M12")) {
    stop_if(!is.character(input$kernel$issue_id) ||
              length(input$kernel$issue_id) != 1L ||
              !nzchar(input$kernel$issue_id),
            "M12 requires a defined single issue_id")
  }
  if (identical(method_id, "M17")) {
    stop_if(!is.character(input$kernel$proposition_id) ||
              length(input$kernel$proposition_id) != 1L ||
              !nzchar(input$kernel$proposition_id) ||
              !is.character(input$kernel$target) ||
              !nzchar(input$kernel$target),
            "M17 requires a named proposition and policy target")
  }

  # Import the unchanged implementation. It enforces country/content/time
  # separation, frozen feature order, admissible outcomes and fitted guards.
  kernel_path <- file.path("research", "engines.R")
  stop_if(!file.exists(kernel_path),
          "Run the adapter from the UNGA81 repository root")
  environment <- new.env(parent = globalenv())
  # engines.R's historical top-level import relies on sys.frame(1)$ofile,
  # which is NULL when source() runs inside this adapter function. Execute the
  # *unchanged* parsed expressions in order and resolve the one known companion
  # import explicitly; refuse new/upstream import patterns rather than guessing.
  expressions <- parse(file = kernel_path, keep.source = FALSE)
  imports <- which(vapply(expressions, function(expr) {
    is.call(expr) && identical(expr[[1L]], as.name("source"))
  }, logical(1)))
  stop_if(length(imports) != 1L ||
            !grepl("engines_more.R",
                   paste(deparse(expressions[[imports]]), collapse = ""), fixed = TRUE),
          "Unexpected original I6 companion import; integration review required")
  companion <- file.path(dirname(kernel_path), "engines_more.R")
  stop_if(!file.exists(companion), "Original I7 companion source missing")
  for (i in seq_along(expressions)) {
    if (i == imports) {
      sys.source(companion, envir = environment, keep.source = FALSE)
    } else {
      eval(expressions[[i]], envir = environment)
    }
  }
  fitted <- environment$i6_compute(method_id, input$kernel)
  stop_if(!identical(fitted$publication_eligible, FALSE) ||
            !identical(fitted$daily_adapter_integrated, FALSE) ||
            !identical(fitted$dataset_kind, "synthetic_engineering"),
          "Original I6 release guard changed unexpectedly")
  list(
    schema = "un.country-positions.kernel-result.v1",
    method_id = method_id,
    source_schema = input$source_schema,
    codebook_version = input$codebook_version,
    source_manifest_sha256 = input$source_manifest_sha256,
    dataset_kind = "synthetic_engineering",
    evaluation_role = "engineering_only",
    publication_eligible = FALSE,
    daily_adapter_integrated = FALSE,
    calibrated_on_real_data = FALSE,
    results = fitted
  )
}

main <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  stop_if(length(args) != 3L,
          "Usage: Rscript m12_m17_adapter.R M12|M17 INPUT.rds PRIVATE_OUTPUT.rds")
  method <- args[[1L]]
  input_file <- normalizePath(args[[2L]], mustWork = TRUE)
  output_file <- args[[3L]]
  stop_if(file.exists(output_file), "Refusing to overwrite an existing output")
  repository <- normalizePath(".", winslash = "/", mustWork = TRUE)
  target <- normalizePath(dirname(output_file), winslash = "/", mustWork = TRUE)
  stop_if(identical(repository, target) ||
            startsWith(target, paste0(repository, "/")),
          "Trained research results must be written outside the public repository")
  data <- readRDS(input_file)
  result <- run_supervised_synthetic(method, data)
  saveRDS(result, file = output_file, version = 3)
  cat("Synthetic-only result saved; publication_eligible=FALSE\n")
}

if (sys.nframe() == 0L) main()
