# Input adapters: UTF-8 TXT (with metadata), ZIP of TXT, and statement CSV.
# ZIP members are streamed into generated safe names; paths are never extracted.

empty_statements <- function() {
  data.frame(statement_id = character(), country = character(), country_id = character(),
             region = character(), speaker = character(), speech_date = character(),
             language = character(), text = character(), source_url = character(),
             source_file = character(), source_sha256 = character(), body_sha256 = character(),
             declared_status = character(), stringsAsFactors = FALSE)
}

parse_transcript <- function(path, display_name = basename(path)) {
  text <- gsub("\r\n?", "\n", read_utf8(path), perl = TRUE)
  lines <- strsplit(text, "\n", fixed = TRUE)[[1L]]
  if (!length(lines)) lines <- ""
  metadata <- list()
  body_start <- 1L
  started <- FALSE
  recognized <- c("country", "country_name", "country_id", "iso3", "region", "region_source",
                  "speaker", "speaker_name", "date", "speech_date", "event_date", "language",
                  "source_url", "transcript_url", "status", "transcript_status", "statement_id",
                  "meeting", "title", "session", "body", "retrieved_at", "source_type",
                  "transcription_type", "speaker_title", "metadata")
  # An explicit block terminator takes precedence. At most 80 metadata lines.
  for (i in seq_len(min(length(lines), 80L))) {
    line <- trimws(lines[[i]])
    if (grepl("^(---+\\s*TRANSCRIPT\\s*---+|\\[TRANSCRIPT\\]|TRANSCRIPT:|===+\\s*TRANSCRIPT.*)$", line, ignore.case = TRUE)) {
      body_start <- i + 1L
      started <- TRUE
      break
    }
    if (line %in% c("---", "[METADATA]", "=== METADATA ===")) {
      started <- TRUE
      body_start <- i + 1L
      next
    }
    if (!nzchar(line) && started) {
      body_start <- i + 1L
      next
    }
    match <- regexec("^([A-Za-z][A-Za-z _-]{0,40}):[ \\t]*(.*)$", lines[[i]], perl = TRUE)
    parts <- regmatches(lines[[i]], match)[[1L]]
    if (length(parts) == 3L) {
      key <- tolower(gsub("[ -]+", "_", trimws(parts[[2L]])))
      if (key %in% recognized) {
        metadata[[key]] <- trimws(parts[[3L]])
        body_start <- i + 1L
        started <- TRUE
        next
      }
    }
    break
  }
  body <- if (body_start <= length(lines)) paste(lines[body_start:length(lines)], collapse = "\n") else ""
  field <- function(keys, default = "") {
    for (key in keys) if (!is.null(metadata[[key]]) && nzchar(metadata[[key]])) return(metadata[[key]])
    default
  }
  raw_hash <- sha256_file(path)
  country <- field(c("country", "country_name"))
  data.frame(
    statement_id = field("statement_id", paste0("txt_", substr(raw_hash, 1L, 20L))),
    country = country,
    country_id = field(c("country_id", "iso3"), if (nzchar(country)) paste0("source_name:", tolower(country)) else ""),
    region = field(c("region", "region_source"), "Unmapped"),
    speaker = field(c("speaker", "speaker_name")),
    speech_date = field(c("speech_date", "event_date", "date")),
    language = field("language", "unknown"), text = body,
    source_url = field(c("source_url", "transcript_url")),
    source_file = display_name, source_sha256 = raw_hash,
    body_sha256 = sha256_text(body), declared_status = field(c("transcript_status", "status")),
    stringsAsFactors = FALSE
  )
}

read_statement_csv <- function(path, display_name = basename(path)) {
  if (file.info(path)$size > 50 * 1024^2) user_error("The statement CSV exceeds 50 MB.")
  data <- tryCatch(utils::read.csv(path, colClasses = "character", check.names = FALSE,
                                   na.strings = character(), fileEncoding = "UTF-8"),
                   error = function(e) user_error("The CSV could not be read. Use the included statement template."))
  if (anyDuplicated(names(data))) user_error("The CSV has duplicate column names.")
  required <- c("statement_id", "country", "speech_date", "text")
  if (!all(required %in% names(data))) user_error("The CSV needs statement_id, country, speech_date, and text columns.")
  if (nrow(data) > 2500L) user_error("Upload at most 2,500 statement rows per run.")
  out <- empty_statements()
  defaults <- c(country_id = "", region = "Unmapped", speaker = "", language = "unknown",
                source_url = "", declared_status = "")
  for (key in names(defaults)) if (!key %in% names(data)) data[[key]] <- rep(defaults[[key]], nrow(data))
  data$source_file <- rep(display_name, nrow(data))
  data$source_sha256 <- rep(sha256_file(path), nrow(data))
  data$body_sha256 <- vapply(data$text, sha256_text, character(1))
  data$country_id[!nzchar(data$country_id) & nzchar(data$country)] <-
    paste0("source_name:", tolower(data$country[!nzchar(data$country_id) & nzchar(data$country)]))
  if (any(!nzchar(data$statement_id)) || anyDuplicated(data$statement_id)) user_error("Statement IDs must be nonempty and unique within a CSV.")
  data[, names(out), drop = FALSE]
}

safe_zip_members <- function(path) {
  info <- tryCatch(utils::unzip(path, list = TRUE), error = function(e) user_error("The ZIP could not be read."))
  if (nrow(info) > 10000L) user_error("The ZIP contains too many entries.")
  names <- info$Name
  if (any(grepl("(^[/\\\\]|^[A-Za-z]:|(^|[/\\\\])\\.\\.([/\\\\]|$)|[[:cntrl:]])", names, perl = TRUE))) {
    user_error("The ZIP has unsafe file paths. Recreate it from transcript text files.", "unsafe_zip")
  }
  if (anyDuplicated(tolower(names))) user_error("The ZIP has duplicate member names.", "unsafe_zip")
  selected <- grepl("\\.txt$", names, ignore.case = TRUE) & !grepl("(^|/)__MACOSX/", names)
  info <- info[selected, , drop = FALSE]
  if (!nrow(info)) user_error("No .txt transcripts were found inside the ZIP.")
  if (nrow(info) > 2500L || any(info$Length > 2 * 1024^2) || sum(info$Length) > 100 * 1024^2) {
    user_error("The ZIP exceeds the transcript limits: 2 MB per text, 100 MB total, or 2,500 texts.")
  }
  info
}

load_inputs <- function(paths, display_names, archive_dir) {
  dir.create(archive_dir, recursive = TRUE, showWarnings = FALSE, mode = "0700")
  out <- list()
  total_decoded <- 0
  if (sum(file.info(paths)$size, na.rm = TRUE) > 100 * 1024^2) user_error("The total upload exceeds 100 MB.")
  ignored <- list()
  counter <- 0L
  for (i in seq_along(paths)) {
    path <- paths[[i]]
    label <- display_names[[i]]
    ext <- tolower(tools::file_ext(label))
    if (!ext %in% c("txt", "csv", "zip")) user_error("Upload .txt, .csv, or .zip files only.")
    if (file.info(path)$size > 100 * 1024^2) user_error("The upload exceeds 100 MB.")
    safe_name <- sprintf("upload_%03d.%s", i, ext)
    archived <- file.path(archive_dir, safe_name)
    if (!file.copy(path, archived, overwrite = FALSE)) user_error("An uploaded source could not be archived.")
    if (ext == "zip") {
      info <- safe_zip_members(archived)
      for (j in seq_len(nrow(info))) {
        counter <- counter + 1L
        member <- info$Name[[j]]
        total_decoded <- total_decoded + info$Length[[j]]
        if (total_decoded > 100 * 1024^2 || counter > 2500L) user_error("The combined archives exceed the 100 MB / 2,500 text limit.")
        con <- unz(archived, member, open = "rb")
        bytes <- tryCatch(readBin(con, "raw", n = 2 * 1024^2 + 1L), finally = close(con))
        if (length(bytes) > 2 * 1024^2 || length(bytes) != info$Length[[j]]) user_error("A ZIP entry failed its size check.")
        dest <- file.path(archive_dir, sprintf("text_%05d.txt", counter))
        writeBin(bytes, dest)
        out[[length(out) + 1L]] <- parse_transcript(dest, paste0(label, " :: ", member))
      }
    } else if (ext == "txt") {
      out[[length(out) + 1L]] <- parse_transcript(archived, label)
    } else {
      out[[length(out) + 1L]] <- read_statement_csv(archived, label)
    }
  }
  if (!length(out)) user_error("Choose transcript files, or switch to the practice sample.")
  combined <- do.call(rbind, out)
  if (nrow(combined) > 2500L) user_error("The combined input exceeds 2,500 statement rows.")
  combined
}

scope_statements <- function(data, config) {
  if (!nrow(data)) user_error("No transcript records were found.")
  data$status <- "available"
  missing_text <- !nzchar(trimws(data$text)) |
    tolower(data$declared_status) %in% c("not_yet_spoken", "not yet spoken", "pending", "missing", "not_available", "placeholder")
  data$status[missing_text] <- "missing_text"
  date_ok <- vapply(data$speech_date, valid_date, logical(1))
  data$status[!date_ok & !missing_text] <- "invalid_or_missing_date"
  out_of_range <- date_ok & (data$speech_date < config$start_date | data$speech_date > config$end_date)
  data$status[out_of_range & !missing_text] <- "outside_reporting_period"
  duplicate_key <- paste(data$country_id, data$speech_date, data$body_sha256, sep = "|")
  available_index <- which(data$status == "available")
  duplicate_index <- available_index[duplicated(duplicate_key[available_index])]
  data$status[duplicate_index] <- "duplicate_source"
  # Same ID with different source contents is not silently merged.
  ids <- data$statement_id[data$status == "available"]
  if (anyDuplicated(ids)) user_error("Two distinct source records share a statement ID. Resolve the IDs before running.")
  data$region[is.na(data$region) | !nzchar(data$region)] <- "Unmapped"
  data$discovery_eligible <- data$status == "available" & tolower(trimws(data$language)) %in% c("en", "eng", "english")
  data
}

split_passages <- function(text) {
  # Exact character spans remain attached to every displayed quotation.
  positions <- gregexpr("[^.!?\n]+[.!?]?", text, perl = TRUE)[[1L]]
  lens <- attr(positions, "match.length")
  rows <- list()
  for (i in seq_along(positions)) {
    if (positions[[i]] < 0L) next
    full <- substr(text, positions[[i]], positions[[i]] + lens[[i]] - 1L)
    first <- regexpr("[^[:space:]]", full, perl = TRUE)[[1L]]
    if (first < 0L) next
    quote <- trimws(full)
    start <- positions[[i]] + first - 1L
    rows[[length(rows) + 1L]] <- data.frame(passage_id = length(rows) + 1L,
      start_char = start, end_char = start + nchar(quote) - 1L, quote = quote, stringsAsFactors = FALSE)
  }
  if (!length(rows)) return(data.frame(passage_id = integer(), start_char = integer(), end_char = integer(), quote = character()))
  do.call(rbind, rows)
}
