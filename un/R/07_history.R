# D1-I1: append-only, content-addressed historical store.
# Only committed directories are visible. No training labels are promoted here.
D1_HISTORY_SCHEMA <- "d1-history-rds-v1"
sha_object <- function(x) sha_raw(serialize(x,NULL,version=3))
utc_now <- function() format(Sys.time(), "%Y-%m-%dT%H:%M:%OS6Z", tz = "UTC")
parse_utc <- function(x) {
  assert(is.character(x) && length(x) == 1L && !is.na(x) &&
           grepl("^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\\.[0-9]{1,6})?Z$", x), "Expected an explicit UTC timestamp")
  value <- as.POSIXct(x, format = "%Y-%m-%dT%H:%M:%OSZ", tz = "UTC")
  assert(!is.na(value), "Invalid UTC timestamp")
  # as.POSIXct can normalize invalid calendar dates; check the calendar portion.
  assert(format(value, "%Y-%m-%dT%H:%M", tz = "UTC") == substr(x, 1, 16), "Invalid calendar timestamp")
  as.numeric(value)
}
relative_path <- function(path) {
  assert(is.character(path) && length(path) == 1L && nzchar(path) &&
           !grepl("^/|^[A-Za-z]:|(^|[/\\\\])\\.\\.([/\\\\]|$)|[\r\n]", path), "Unsafe relative artifact path")
  path
}
immutable_write <- function(path, bytes) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  if (file.exists(path)) {
    assert(identical(sha_file(path), sha_raw(bytes)), "Immutable artifact conflicts with existing bytes")
    return(invisible(path))
  }
  tmp <- tempfile(".pending_", tmpdir = dirname(path)); on.exit(unlink(tmp), add = TRUE)
  writeBin(bytes, tmp)
  assert(identical(sha_file(tmp), sha_raw(bytes)), "Artifact write verification failed")
  assert(file.rename(tmp, path), "Cannot commit immutable file within its directory")
  invisible(path)
}
object_write <- function(store, value, kind = "objects") {
  assert(kind %in% c("objects", "labels", "snapshots"), "Unknown historical object kind")
  bytes <- serialize(value, NULL, version = 3)
  hash <- sha_raw(bytes)
  rel <- paste0(kind, "/", substr(hash, 1, 2), "/", hash, ".rds")
  immutable_write(file.path(store, rel), bytes)
  list(path = rel, sha256 = hash)
}
object_read <- function(store, ref) {
  assert(is.list(ref) && grepl("^[0-9a-f]{64}$", str1(ref$sha256)), "Invalid historical object reference")
  path <- file.path(store, relative_path(ref$path))
  assert(file.exists(path) && identical(sha_file(path), ref$sha256), paste("Historical artifact missing or corrupt:", ref$path))
  readRDS(path)
}
history_lock <- function(store) {
  dir.create(store, recursive = TRUE, showWarnings = FALSE)
  lock <- file.path(store, ".write-lock")
  assert(dir.create(lock, showWarnings = FALSE), "Historical store is locked. Inspect owner.json; do not delete a live owner's lock.")
  token <- sha_text(paste(Sys.getpid(), Sys.info()[["nodename"]], utc_now(), tempfile(), sep = "|"))
  json_write(file.path(lock, "owner.json"), list(token = token, pid = Sys.getpid(),
             host = Sys.info()[["nodename"]], started_at = utc_now(), automatic_stale_lock_removal = FALSE))
  list(path = lock, token = token)
}
history_unlock <- function(lock) {
  if (dir.exists(lock$path)) {
    owner <- json_read(file.path(lock$path, "owner.json"))
    assert(identical(owner$token, lock$token), "Refusing to release a different owner's history lock")
    unlink(lock$path, recursive = TRUE)
  }
  invisible(TRUE)
}
history_init <- function(store) {
  dir.create(store, recursive = TRUE, showWarnings = FALSE)
  schema <- list(schema = D1_HISTORY_SCHEMA, backend = "append_only_RDS_CSV", clock = "UTC",
                 queries = "event cutoff AND recorded/first-seen cutoff", is_database_ACID = FALSE)
  immutable_write(file.path(store, "SCHEMA.json"), charToRaw(paste0(json_minimal(schema), "\n")))
  for (d in c("objects", "labels", "blobs", "snapshots", "commits"))
    dir.create(file.path(store, d), showWarnings = FALSE)
  invisible(store)
}
history_commits <- function(store) {
  if (!dir.exists(store)) return(list())
  assert(identical(json_read(file.path(store, "SCHEMA.json"))$schema, D1_HISTORY_SCHEMA), "History schema version mismatch")
  paths <- sort(list.dirs(file.path(store, "commits"), recursive = FALSE, full.names = TRUE), method = "radix")
  # Staging directories are deliberately invisible, including after an interrupted write.
  paths <- paths[!startsWith(basename(paths), ".")]
  out <- list(); previous <- ""; previous_time <- -Inf
  for (i in seq_along(paths)) {
    p <- paths[i]; hash_path <- file.path(p, "COMMITTED")
    assert(file.exists(hash_path), paste("Invalid visible history commit:", basename(p)))
    hash <- trimws(read_text(hash_path))
    assert(grepl("^[0-9a-f]{64}$", hash) && identical(sha_file(file.path(p, "commit.rds")), hash), "Historical commit hash mismatch")
    c <- readRDS(file.path(p, "commit.rds"))
    assert(identical(c$schema, D1_HISTORY_SCHEMA) && c$sequence == i &&
             identical(c$previous_commit_sha256, previous), "Historical commit chain has a gap or wrong predecessor")
    assert(parse_utc(c$recorded_at) >= previous_time, "Historical commit clock moved backward")
    assert(identical(basename(p), sprintf("%012d_%s", i, substr(hash, 1, 16))), "Historical commit identity mismatch")
    c$commit_sha256 <- hash; c$commit_path <- paste0("commits/", basename(p))
    out[[i]] <- c; previous <- hash; previous_time <- parse_utc(c$recorded_at)
  }
  out
}
observation_enrich <- function(s, source_mode, acquired_at, index = NULL) {
  parse_utc(acquired_at)
  # Caller-provided dates are provenance, not a trusted first-availability clock.
  s$reported_available_at <- str1(s$available_at)
  s$acquired_at <- acquired_at
  s$meeting_id <- str1(s$meeting_id)
  s$statement_number <- str1(as.character(s$statement_number %||% ""))
  s$agenda_item <- str1(s$agenda_item)
  s$genre <- str1(s$genre, if (source_mode == "replay") "general_debate_supplied" else "unspecified")
  s$genre_basis <- str1(s$genre_basis, if (source_mode == "replay") "bundled archive label; not independently verified" else "source metadata or unspecified")
  s$language <- str1(s$language, "unspecified")
  s$translation_version <- str1(s$translation_version, "unspecified")
  s$event_time <- str1(s$event_time, s$date)
  s$event_time_precision <- str1(s$event_time_precision, "date")
  locator <- str1(s$observation_key)
  method <- "explicit_observation_key"
  if (!nzchar(locator) && nzchar(s$meeting_id) && nzchar(s$statement_number)) {
    locator <- paste(s$meeting_id, s$statement_number, sep = "#"); method <- "meeting_and_statement_number"
  }
  if (!nzchar(locator) && nzchar(str1(s$source_file))) {
    locator <- gsub("\\\\", "/", s$source_file); method <- "source_file_and_date"
  }
  if (!nzchar(locator)) {
    locator <- s$text_sha256; method <- "content_addressed_unlinked_revision"
  }
  s$observation_id <- paste0("obs_", sha_text(json_minimal(list(country = s$iso3, date = s$date,
                genre = s$genre, meeting = s$meeting_id, locator = locator))))
  s$identity_method <- method
  s$source_mode <- source_mode
  s$eligibility_class <- if(source_mode=="replay") "replay_fixture" else if(grepl("fixture|synthetic",s$source_type,ignore.case=TRUE)) "engineering_fixture" else "observed_input"
  s
}
observation_object <- function(s) {
  assert(nzchar(str1(s$observation_id)), "Observation was not enriched before historical ingestion")
  assert(identical(sha_text(s$text), s$text_sha256), "Historical text hash does not match source text")
  metadata <- s[intersect(c("iso3", "country", "speaker", "title", "date", "region", "meeting_id",
                   "statement_number", "agenda_item", "genre", "genre_basis", "language", "translation_version",
                   "event_time", "event_time_precision", "source_type", "source_file", "source_url",
                   "source_sha256", "text_sha256", "flags", "source_mode", "eligibility_class", "identity_method"), names(s))]
  version <- sha_object(list(schema = D1_HISTORY_SCHEMA, observation_id = s$observation_id,
                       metadata = metadata, sentences = s$sentences))
  passages <- list(); cursor <- 1L
  for (unit in s$sentences) {
    found <- regexpr(unit$text, substring(s$text, cursor), fixed = TRUE)[1]
    start <- if (found < 0) NA_integer_ else cursor + as.integer(found) - 1L
    end <- if (is.na(start)) NA_integer_ else start + nchar(unit$text) - 1L
    if (!is.na(end)) cursor <- end + 1L
    passages[[length(passages) + 1L]] <- list(passage_id = paste0(version, ":", unit$id),
      observation_id = s$observation_id, observation_version_id = version, source_sentence_id = unit$id,
      text = unit$text, start_char = start, end_char = end, offsets_exact = !is.na(start),
      source_pointer = str1(unit$pointer), source_url = str1(unit$url, str1(s$source_url)),
      start_seconds = unit$start %||% NULL, end_seconds = unit$end %||% NULL,
      language = s$language, translation_version = s$translation_version,
      near_duplicate_group = "", near_duplicate_status = "not_assessed")
  }
  list(schema = D1_HISTORY_SCHEMA, kind = "statement", observation_id = s$observation_id,
       observation_version_id = version, metadata = metadata, text = s$text,
       exact_duplicate_group = sha_text(s$text), normalized_duplicate_group = sha_text(norm(s$text)),
       duplicate_definition = "exact UTF-8 text hash; normalized hash retained separately", passages = passages)
}
history_index <- function(store, as_of, event_cutoff, latest = TRUE, max_objects = 100000L) {
  cutoff <- parse_utc(as_of); parse_source_date(event_cutoff)
  columns <- c("observation_id", "observation_version_id", "iso3", "country", "event_date", "genre",
               "meeting_id", "statement_number", "text_sha256", "source_sha256", "source_mode", "eligibility_class", "identity_method",
               "object_path", "object_sha256", "first_seen_at", "recorded_at", "commit_sequence")
  commits <- history_commits(store); rows <- list()
  for (commit in commits) {
    if (parse_utc(commit$recorded_at) > cutoff) next
    for (entry in commit$observations) {
      if (parse_utc(entry$first_seen_at) > cutoff || entry$event_date > event_cutoff) next
      entry$recorded_at <- commit$recorded_at; entry$commit_sequence <- commit$sequence
      rows[[length(rows) + 1L]] <- entry
    }
  }
  d <- rows_frame(rows, columns)
  assert(nrow(d) <= max_objects, "Historical query exceeds configured record cap; use an indexed backend before expanding this corpus")
  if (!nrow(d)) return(d)
  # Read back exact selected object hashes even when a prior run claimed successful ingestion.
  d <- d[order(as.numeric(d$commit_sequence), d$observation_version_id, method = "radix"), , drop = FALSE]
  # Re-observation of identical bytes does not create a later first-seen time or a new revision.
  first <- d[!duplicated(d$observation_version_id), , drop = FALSE]
  versions <- if(latest) d[!duplicated(d$observation_id,fromLast=TRUE),,drop=FALSE] else first
  # A later reversion to earlier bytes is a current observation, while the version's
  # first-seen time remains its original acquisition time.
  versions$first_seen_at <- first$first_seen_at[match(versions$observation_version_id,first$observation_version_id)]
  for (i in seq_len(nrow(versions))) {
    obj <- object_read(store, list(path = versions$object_path[i], sha256 = versions$object_sha256[i]))
    assert(identical(obj$observation_version_id, versions$observation_version_id[i]) &&
             identical(obj$metadata$text_sha256, versions$text_sha256[i]), "Historical index/object identity mismatch")
  }
  rownames(versions) <- NULL
  versions
}
history_ingest <- function(root, run, cfg, observations, cp, clock = utc_now, fault = NULL) {
  store <- file.path(root, relative_path(cfg$analytics$history_dir)); history_init(store)
  lock <- history_lock(store); on.exit(history_unlock(lock), add = TRUE)
  commits <- history_commits(store); now <- clock(); parse_utc(now)
  if (length(commits)) assert(parse_utc(now) >= parse_utc(tail(commits, 1)[[1]]$recorded_at), "History clock regression rejected")
  entries <- list(); label_entries <- list(); raw_entries <- list()
  label_codebook_hash <- sha_object(cp$codebook)
  for (s in observations) {
    assert(parse_utc(s$acquired_at) <= parse_utc(now), "Source availability lies after the commit clock")
    obj <- observation_object(s); ref <- object_write(store, obj)
    entries[[length(entries) + 1L]] <- list(observation_id = obj$observation_id,
      observation_version_id = obj$observation_version_id, iso3 = s$iso3, country = s$country,
      event_date = s$date, genre = s$genre, meeting_id = s$meeting_id, statement_number = s$statement_number,
      text_sha256 = s$text_sha256, source_sha256 = s$source_sha256, source_mode = s$source_mode, eligibility_class=s$eligibility_class,
      identity_method = s$identity_method, object_path = ref$path, object_sha256 = ref$sha256, first_seen_at = s$acquired_at)
  }
  # Same identity with different bytes inside one acquisition is ambiguous, not an ordered revision.
  ids <- vapply(entries, function(e) e$observation_id, character(1))
  vers <- vapply(entries, function(e) e$observation_version_id, character(1))
  for (id in unique(ids)) assert(length(unique(vers[ids == id])) == 1L,
      "Two conflicting versions of the same statement occur in one collection; resolve identity before committing")
  entries <- entries[!duplicated(vers)]
  for (s in cp$speeches) {
    a <- cp$analyses[[s$iso3]]
    origin <- switch(str1(a$verification$status), inherited_review = "inherited_snapshot",
              extractive_provisional = "rule_generated", model_reviewed = "model_generated",
              model_hold = "model_generated_held", failed = "not_assessed", "unclassified_automatic")
    observed <- entries[vapply(entries, function(e) identical(e$iso3, s$iso3), logical(1))]
    versions_used <- as.list(vapply(observed, function(e) e$observation_version_id, character(1)))
    for (issue in a$issues) {
      def <- Filter(function(b) identical(b$issue_id, issue$issue_id), cp$codebook)
      assert(length(def) == 1L, "Label issue does not match archived codebook")
      lab <- list(schema = D1_HISTORY_SCHEMA, kind = "country_window_issue_label", country = s$iso3,
        event_date = s$date, observation_versions = versions_used, text_sha256 = s$text_sha256,
        issue_id = issue$issue_id, target_proposition_id = "", value = issue$status,
        rationale = issue$rationale, evidence = issue$evidence, label_origin = origin,
        codebook_version = def[[1]]$version, codebook_sha256 = label_codebook_hash,
        annotator_or_model_version = str1(a$verification$cache_key, cp$brief$analysis_mode),
        adjudication_status = "not_human_adjudicated", is_gold = FALSE,
        training_eligible = FALSE, source_mode = cp$brief$source,
        mixed_version_fixture = identical(cp$brief$source, "replay"))
      ref <- object_write(store, lab, "labels")
      label_entries[[length(label_entries) + 1L]] <- list(label_id = ref$sha256, path = ref$path,
          sha256 = ref$sha256, country = s$iso3, issue_id = issue$issue_id,
          first_seen_at = now, is_gold = FALSE, origin = origin)
    }
  }
  manifest_path <- file.path(run, "audit/source_manifest.json")
  if (file.exists(manifest_path)) for (src in json_read(manifest_path)) {
    from <- file.path(run, relative_path(src$path)); bytes <- read_bytes(from)
    assert(identical(sha_raw(bytes), src$sha256), "Raw source archive changed before historical ingestion")
    assert(length(bytes) <= cfg$analytics$max_raw_blob_bytes, "Historical raw source exceeds configured byte cap")
    rel <- paste0("blobs/", substr(src$sha256, 1, 2), "/", src$sha256, ".bin")
    immutable_write(file.path(store, rel), bytes)
    raw_entries[[length(raw_entries) + 1L]] <- list(path = rel, sha256 = src$sha256, source = src$source,
       recorded_at = now, source_retrieved_at = str1(src$retrieved_at, now), run_source_path = src$path)
  }
  if (identical(fault, "before_commit")) stop("Injected pre-commit interruption for engineering validation")
  commit <- list(schema = D1_HISTORY_SCHEMA, sequence = length(commits) + 1L,
      previous_commit_sha256 = if (length(commits)) tail(commits, 1)[[1]]$commit_sha256 else "",
      recorded_at = now, report_event_date = cp$brief$date, run_id = basename(run),
      source_mode = cp$brief$source, code_version = UNBRIEF_VERSION,
      observations = entries, labels = label_entries, raw_sources = raw_entries,
      coverage = cp$brief$collection, event_date_does_not_imply_availability = TRUE)
  bytes <- serialize(commit, NULL, version = 3); hash <- sha_raw(bytes)
  parent <- file.path(store, "commits"); stage <- tempfile(".pending_", tmpdir = parent)
  dir.create(stage); on.exit(if(dir.exists(stage)) unlink(stage, recursive = TRUE), add = TRUE)
  writeBin(bytes, file.path(stage, "commit.rds")); write_text(file.path(stage, "COMMITTED"), hash)
  assert(identical(sha_file(file.path(stage, "commit.rds")), hash), "Commit write verification failed")
  dest <- file.path(parent, sprintf("%012d_%s", commit$sequence, substr(hash, 1, 16)))
  assert(!dir.exists(dest) && file.rename(stage, dest), "Cannot make historical commit visible")
  idx <- history_index(store, now, cp$brief$date, max_objects = cfg$analytics$max_store_objects_per_query)
  snapshot <- list(schema = D1_HISTORY_SCHEMA, kind = "as_of_snapshot", event_cutoff = cp$brief$date,
                  as_of_cutoff = now, commit_tip_sha256 = hash, observations = idx,
                  codebook_sha256 = label_codebook_hash, source_mode = cp$brief$source,
                  training_gold_count = 0L, gold_policy = "automatic/inherited labels are never promoted")
  snap_ref <- object_write(store, snapshot, "snapshots")
  snapshot$snapshot_id <- snap_ref$sha256
  dir.create(file.path(run, "audit/history"), recursive = TRUE, showWarnings = FALSE)
  saveRDS(snapshot, file.path(run, "audit/history/snapshot.rds"), version = 3)
  json_write(file.path(run, "audit/history/receipt.json"), list(schema = D1_HISTORY_SCHEMA,
      snapshot_id = snap_ref$sha256, snapshot_store_path = snap_ref$path, commit_tip_sha256 = hash,
      recorded_at = now, event_cutoff = cp$brief$date, current_statements = length(entries),
      as_of_statement_versions = nrow(idx), labels_stored = length(label_entries), human_gold_labels = 0L,
      raw_source_objects = length(raw_entries), codebook_mixed_fixture = cp$brief$source == "replay"))
  csv_write(file.path(run, "data/history_observations.csv"), idx)
  # A run is self-contained for future audit and rebuilding even if the active store moves.
  saveRDS(lapply(observations, observation_object), file.path(run, "audit/history/current_observations.rds"), version = 3)
  snapshot
}
history_labels <- function(store, as_of, event_cutoff, origin = NULL) {
  cutoff <- parse_utc(as_of); parse_source_date(event_cutoff); out <- list(); seen <- character()
  for (commit in history_commits(store)) {
    if (parse_utc(commit$recorded_at) > cutoff) next
    for (ref in commit$labels) {
      if (ref$label_id %in% seen || parse_utc(ref$first_seen_at) > cutoff) next
      lab <- object_read(store, ref)
      if (lab$event_date > event_cutoff || !is.null(origin) && !lab$label_origin %in% origin) next
      lab$available_at <- ref$first_seen_at; lab$recorded_at <- commit$recorded_at
      lab$label_id <- ref$label_id; out[[length(out) + 1L]] <- lab; seen <- c(seen, ref$label_id)
    }
  }
  out
}
history_verify <- function(store, verify_blobs = TRUE) {
  commits <- history_commits(store); hashes <- character(); checked <- 0L
  for (commit in commits) {
    for (ref in c(lapply(commit$observations, function(e)list(path=e$object_path,sha256=e$object_sha256)), commit$labels)) {
      if (ref$sha256 %in% hashes) next
      object_read(store, ref); hashes <- c(hashes, ref$sha256); checked <- checked + 1L
    }
    if (verify_blobs) for (ref in commit$raw_sources) {
      path <- file.path(store, relative_path(ref$path))
      assert(identical(sha_file(path), ref$sha256), "Raw historical blob hash mismatch")
    }
  }
  list(passed = TRUE, schema = D1_HISTORY_SCHEMA, commits = length(commits), unique_objects_verified = checked,
       raw_blobs_verified = verify_blobs, no_commit_is_training_or_release_approval = TRUE)
}
