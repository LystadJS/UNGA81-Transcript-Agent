# UN Readout MVP: validation, immutable job inputs, literal issue definitions.
# All source text is data. Nothing in an uploaded file is evaluated as R or HTML.
`%||%` <- function(x, y) if (is.null(x) || length(x) == 0L) y else x

MVP_VERSION <- "0.2.0-d1-i4"
REGION_ORDER <- c(
  "Africa", "Asia-Pacific", "Europe & Eurasia", "Near East",
  "Western Hemisphere", "Unmapped"
)
DEFAULT_TOPICS <- c("Iran", "Cuba", "Ukraine", "Artificial Intelligence")
SLOT_TITLES <- c(
  O1 = "Tracked issues", O2 = "Emerging themes",
  O3 = "Country discourse map", O4 = "Rhetorical movement",
  O5 = "Discourse-network changes"
)

user_error <- function(message, code = "input_error") {
  stop(structure(list(message = message, call = NULL, code = code),
                 class = c("readout_user_error", "error", "condition")))
}

utc_now <- function() format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC")

sha256_file <- function(path) {
  stopifnot(length(path) == 1L, file.exists(path))
  if (requireNamespace("digest", quietly = TRUE)) {
    return(digest::digest(file = path, algo = "sha256", serialize = FALSE))
  }
  if (nzchar(Sys.which("sha256sum"))) {
    value <- system2(Sys.which("sha256sum"), shQuote(normalizePath(path)),
                     stdout = TRUE, stderr = TRUE)
  } else if (.Platform$OS.type == "windows" && nzchar(Sys.which("certutil"))) {
    value <- system2(Sys.which("certutil"),
                     c("-hashfile", shQuote(normalizePath(path)), "SHA256"),
                     stdout = TRUE, stderr = TRUE)
  } else {
    user_error("The SHA-256 dependency is missing. Run Setup before continuing.",
               "missing_hash_dependency")
  }
  hits <- regmatches(value, regexpr("[0-9a-fA-F]{64}", value, perl = TRUE))
  hits <- hits[nchar(hits) == 64L]
  if (length(hits) != 1L) user_error("A source file could not be fingerprinted.", "hash_failed")
  tolower(hits[[1L]])
}

sha256_text <- function(x) {
  path <- tempfile("hash-")
  on.exit(unlink(path), add = TRUE)
  con <- file(path, "wb")
  writeBin(charToRaw(enc2utf8(paste(x, collapse = "\n"))), con)
  close(con)
  sha256_file(path)
}

write_utf8 <- function(text, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  con <- file(path, "wb")
  on.exit(close(con), add = TRUE)
  writeBin(charToRaw(enc2utf8(paste(text, collapse = "\n"))), con)
  invisible(path)
}

read_utf8 <- function(path, max_bytes = 2 * 1024^2) {
  n <- file.info(path)$size
  if (is.na(n) || n > max_bytes) user_error("A transcript is too large (2 MB maximum per text file).")
  raw <- readBin(path, "raw", n = n)
  if (any(raw == as.raw(0))) user_error("A transcript contains binary data. Upload UTF-8 text.")
  value <- rawToChar(raw)
  value <- iconv(value, from = "UTF-8", to = "UTF-8", sub = NA)
  if (is.na(value)) user_error("A transcript is not valid UTF-8. Save it as UTF-8 text and upload it again.")
  sub("^\ufeff", "", value)
}

# Dependency-free JSON writer for configuration/provenance, never a parser.
json_quote <- function(x) {
  vapply(enc2utf8(x), function(value) {
    if (is.na(value)) return("null")
    codes <- utf8ToInt(value)
    escaped <- vapply(codes, function(ch) {
      if (ch == 34L) return('\\"')
      if (ch == 92L) return("\\\\")
      if (ch < 32L) return(sprintf("\\u%04x", ch))
      intToUtf8(ch)
    }, character(1))
    paste0('"', paste0(escaped, collapse = ""), '"')
  }, character(1), USE.NAMES = FALSE)
}

to_json <- function(x) {
  if (is.null(x)) return("null")
  if (inherits(x, "Date")) x <- as.character(x)
  if (is.data.frame(x)) {
    x <- lapply(seq_len(nrow(x)), function(i) as.list(x[i, , drop = FALSE]))
  }
  if (is.list(x)) {
    values <- vapply(x, to_json, character(1))
    if (!is.null(names(x)) && all(nzchar(names(x)))) {
      return(paste0("{", paste0(json_quote(names(x)), ":", values, collapse = ","), "}"))
    }
    return(paste0("[", paste0(values, collapse = ","), "]"))
  }
  if (length(x) != 1L) return(paste0("[", paste0(vapply(as.list(x), to_json, character(1)), collapse = ","), "]"))
  if (is.na(x)) return("null")
  if (is.logical(x)) return(if (x) "true" else "false")
  if (is.numeric(x)) return(if (is.finite(x)) format(x, scientific = FALSE, trim = TRUE, digits = 16L) else "null")
  json_quote(as.character(x))
}

write_json <- function(x, path) write_utf8(to_json(x), path)

atomic_rds <- function(x, path) {
  tmp <- paste0(path, ".", Sys.getpid(), ".tmp")
  saveRDS(x, tmp, version = 3)
  # Windows cannot rename over an existing destination. Readers tolerate the gap.
  if (file.exists(path)) unlink(path)
  if (!file.rename(tmp, path)) user_error("A run status could not be saved.", "write_failed")
  invisible(path)
}

set_progress <- function(job_dir, stage, percent, message, state = "running") {
  atomic_rds(list(stage = stage, percent = percent, message = message,
                 state = state, updated_at = utc_now()), file.path(job_dir, "progress.rds"))
}

clean_label <- function(x) {
  if (length(x) != 1L || is.na(x)) user_error("Each topic needs a name.")
  x <- trimws(gsub("[[:space:]]+", " ", enc2utf8(x)))
  if (!nzchar(x) || nchar(x) > 100L) user_error("Use 1 to 100 characters for each topic.")
  if (grepl("[[:cntrl:]]", x)) user_error("Topic names cannot contain control characters.")
  x
}

normalize_phrases <- function(x) {
  if (is.null(x) || !length(x)) return(character())
  x <- trimws(as.character(x))
  x <- x[nzchar(x)]
  if (length(x) > 30L) user_error("Use at most 30 related or excluded phrases per topic.")
  unique(vapply(x, clean_label, character(1)))
}

make_topics <- function(labels, refinements = list()) {
  labels <- vapply(labels %||% character(), clean_label, character(1), USE.NAMES = FALSE)
  labels <- labels[!duplicated(tolower(labels))]
  if (length(labels) > 20L) user_error("Track up to 20 topics in one readout.")
  # No topics is allowed: discover themes without a watchlist.
  lapply(labels, function(label) {
    detail <- refinements[[label]] %||% list()
    defaults <- if (tolower(label) == "artificial intelligence") "AI" else character()
    aliases <- normalize_phrases(detail$include %||% defaults)
    excluded <- normalize_phrases(detail$exclude)
    terms <- unique(c(label, aliases))
    if (any(tolower(terms) %in% tolower(excluded))) {
      user_error(paste0("A phrase is both included and excluded for \"", label, "\"."))
    }
    list(id = paste0("topic_", substr(sha256_text(tolower(label)), 1L, 12L)),
         label = label, include = as.list(aliases), exclude = as.list(excluded),
         matching = "literal_phrase_with_boundaries_v1", semantic_expansion = FALSE)
  })
}

valid_date <- function(x) {
  if (length(x) != 1L || is.na(x) || !grepl("^\\d{4}-\\d{2}-\\d{2}$", x)) return(FALSE)
  d <- suppressWarnings(as.Date(x, format = "%Y-%m-%d"))
  !is.na(d) && identical(format(d, "%Y-%m-%d"), x)
}

new_config <- function(start_date, end_date, labels, refinements = list(), source = "demo") {
  start_date <- as.character(start_date)
  end_date <- as.character(end_date)
  if (!valid_date(start_date) || !valid_date(end_date)) user_error("Choose valid start and end dates.")
  if (start_date > end_date) user_error("The end date must be on or after the start date.")
  if (as.integer(as.Date(end_date) - as.Date(start_date)) > 31L) user_error("Choose a reporting window of 32 days or less.")
  if (!source %in% c("demo", "upload", "d1")) user_error("Choose a supported transcript source.")
  list(schema_version = "un.readout.request.v1", app_version = MVP_VERSION,
       start_date = start_date, end_date = end_date, timezone = "America/New_York",
       fixed_topics = make_topics(labels, refinements), discover_themes = TRUE,
       discovery_scope = "all_eligible_source_texts_independent_of_fixed_topics",
       source = source, external_processing = FALSE, email_delivery = "draft_only",
       requested_at_utc = utc_now())
}

html_escape <- function(x) {
  x <- gsub("&", "&amp;", as.character(x), fixed = TRUE)
  x <- gsub("<", "&lt;", x, fixed = TRUE)
  x <- gsub(">", "&gt;", x, fixed = TRUE)
  x <- gsub('"', "&quot;", x, fixed = TRUE)
  gsub("'", "&#39;", x, fixed = TRUE)
}

regex_escape <- function(x) {
  chars <- strsplit(x, "", fixed = TRUE)[[1L]]
  metachar <- strsplit("\\.^$|?*+()[]{}", "", fixed = TRUE)[[1L]]
  paste0(ifelse(chars %in% metachar, paste0("\\", chars), chars), collapse = "")
}

phrase_pattern <- function(x) {
  paste0("(?<![\\p{L}\\p{N}_])", regex_escape(x), "(?![\\p{L}\\p{N}_])")
}

phrase_hit <- function(text, phrase) {
  # Short uppercase acronyms are case-sensitive; ordinary labels are not.
  acronym <- grepl("^[A-Z]{2,3}$", phrase)
  grepl(phrase_pattern(phrase), text, ignore.case = !acronym, perl = TRUE)
}

readout_code_hash <- function(root) {
  files <- sort(list.files(file.path(root, "R"), "\\.R$", full.names = TRUE))
  sha256_text(paste(basename(files), vapply(files, sha256_file, character(1)), sep = ":"))
}

# Spreadsheet programs may execute formula-looking CSV text. Export a visibly
# apostrophe-prefixed value while preserving exact originals in archived source
# bytes and statements.rds. Numeric columns remain numeric.
csv_safe <- function(data) {
  stopifnot(is.data.frame(data))
  for (name in names(data)) {
    if (is.character(data[[name]])) {
      dangerous <- !is.na(data[[name]]) &
        grepl("^[[:space:]]*[=+@-]|^[\\t\\r\\n]", data[[name]], perl = TRUE)
      data[[name]][dangerous] <- paste0("'", data[[name]][dangerous])
    }
  }
  data
}

write_safe_csv <- function(data, path) {
  utils::write.csv(csv_safe(data), path, row.names = FALSE, fileEncoding = "UTF-8")
}
