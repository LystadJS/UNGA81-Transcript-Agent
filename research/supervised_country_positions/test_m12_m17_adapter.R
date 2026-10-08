# Synthetic-only regression of the existing I6 research kernel entry points.
# Run from repository root with R, glmnet and all existing I6 requirements.
source("research/supervised_country_positions/m12_m17_adapter.R")
if (!requireNamespace("glmnet", quietly = TRUE)) {
  stop("Missing glmnet; R adapter validation NOT RUN", call. = FALSE)
}
set.seed(20261008)
part <- function(prefix, split_time, classes) {
  n <- 120L
  y <- rep(classes, length.out = n)
  x <- matrix(rnorm(n * 4L), nrow = n, ncol = 4L)
  x[, 1L] <- x[, 1L] + 0.4 * match(y, classes)
  rownames(x) <- paste0(prefix, "-observation-", seq_len(n))
  colnames(x) <- paste0("synthetic-f", 1:4)
  list(
    x = x, y = y, time = split_time + seq_len(n)/1e5,
    country = paste0(prefix, "-actor-", seq_len(n)),
    text_hash = paste0(prefix, "-hash-", seq_len(n))
  )
}
packet <- function(kernel) list(
  schema = "un.country-positions.kernel-input.v1",
  source_schema = "un.review.v1",
  dataset_kind = "synthetic_engineering",
  publication_eligible = FALSE,
  codebook_version = "1.0.0",
  source_manifest_sha256 = paste(rep("a", 64L), collapse = ""),
  kernel = kernel
)

binary <- list(
  dataset_kind = "synthetic_engineering", issue_id = "ai_governance",
  train = part("m12train", 1, c(0,1)),
  calibration = part("m12cal", 2, c(0,1)),
  test = part("m12test", 3, c(0,1))
)
m12 <- run_supervised_synthetic("M12", packet(binary))
stopifnot(
  identical(m12$method_id, "M12"),
  identical(m12$publication_eligible, FALSE),
  identical(m12$daily_adapter_integrated, FALSE),
  identical(m12$calibrated_on_real_data, FALSE),
  length(m12$results$value$scores) == 120L
)
cat("PASS: unchanged M12 on synthetic engineering input\n")

labels <- c("support", "oppose", "conditional", "descriptive")
stance <- list(
  dataset_kind = "synthetic_engineering",
  proposition_id = "ai_binding", target = "binding international AI obligations",
  representation_id = "synthetic-frozen-feature-v1",
  train = part("m17train", 1, labels),
  calibration = part("m17cal", 2, labels),
  test = part("m17test", 3, labels)
)
m17 <- run_supervised_synthetic("M17", packet(stance))
stopifnot(
  identical(m17$method_id, "M17"),
  identical(m17$publication_eligible, FALSE),
  is.matrix(m17$results$value$scores),
  nrow(m17$results$value$scores) == 120L,
  identical(sort(m17$results$value$classes), sort(labels))
)
cat("PASS: unchanged M17 on synthetic engineering input\n")

bad <- packet(binary)
bad$dataset_kind <- "real"
caught <- tryCatch(run_supervised_synthetic("M12", bad), error = function(e) e)
stopifnot(inherits(caught, "error"))
cat("PASS: empirical data rejected\n")

bad2 <- packet(stance)
bad2$kernel$test$country[[1L]] <- bad2$kernel$train$country[[1L]]
caught <- tryCatch(run_supervised_synthetic("M17", bad2), error = function(e) e)
stopifnot(inherits(caught, "error"))
cat("PASS: source-country overlap rejected\n")
