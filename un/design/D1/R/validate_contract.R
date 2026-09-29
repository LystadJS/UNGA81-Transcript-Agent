# Native-R design and publication-contract checks.
# This file does NOT fit a model, collect data, send mail, or patch v2.1.
# Upstream evidence/quality flags must be established by real validators:
# structural checking of TRUE flags does not prove semantic accuracy.
contract_assert <- function(ok, message) {
  if (!is.logical(ok) || length(ok) != 1L || is.na(ok) || !ok) stop(message, call. = FALSE)
  invisible(TRUE)
}
scalar_nonempty <- function(x) is.character(x) && length(x) == 1L && !is.na(x) && nzchar(trimws(x))
read_method_registry <- function(path) {
  contract_assert(file.exists(path), paste("Registry not found:", path))
  utils::read.csv(path, stringsAsFactors = FALSE, check.names = FALSE,
                  fileEncoding = "UTF-8", na.strings = character())
}
validate_design <- function(registry, policy) {
  required <- c("method_id", "method", "family", "learning_type", "email_slots", "r_packages",
                "fit_cadence", "required_gates", "publication_role", "daily_policy",
                "implementation_status", "note")
  contract_assert(is.data.frame(registry) && all(required %in% names(registry)), "Registry schema mismatch")
  contract_assert(nrow(registry) == 42L && !anyDuplicated(registry$method_id), "Expected 42 unique method registrations")
  contract_assert(identical(sort(registry$method_id), sprintf("M%02d", 1:42)), "Missing/unrecognized method")
  contract_assert(identical(policy$slot_ids, paste0("O", 1:5)), "Email must have exactly O1-O5 in order")
  contract_assert(length(policy$slot_names) == 5L && !anyDuplicated(policy$slot_names), "Invalid slot names")
  contract_assert(identical(policy$fixed_topics, c("iran", "cuba", "ukraine", "ai")), "Fixed topics must remain Iran, Cuba, Ukraine, AI")
  contract_assert(identical(policy$country_grouping, "region_then_alphabetical"), "Regional alphabetical ordering changed")
  contract_assert(identical(policy$region_order, c("Africa", "Asia-Pacific", "Europe & Eurasia", "Near East", "Western Hemisphere")), "Region policy changed")
  contract_assert(isTRUE(policy$keep_country_summaries), "Country summaries must remain")
  contract_assert(identical(policy$extra_analytics, FALSE) && identical(policy$old_issue_figures_inline, FALSE), "Extra analytical output enabled")
  contract_assert(identical(policy$allow_automatic_send, FALSE), "Design must not enable automatic sending")
  contract_assert(is.numeric(policy$max_image_width) && policy$max_image_width > 0 && policy$max_image_width <= 840, "Invalid image display width")
  contract_assert(policy$max_analytical_images <= 3 && policy$max_analytical_images >= 0, "Image limit exceeded")
  for (field in required) contract_assert(all(!is.na(registry[[field]]) & nzchar(registry[[field]])), paste("Blank registry field:", field))
  for (i in seq_len(nrow(registry))) {
    slots <- strsplit(registry$email_slots[i], "|", fixed = TRUE)[[1]]
    contract_assert(all(slots %in% policy$slot_ids) && !anyDuplicated(slots), "Registry routes to an unrecognized/duplicate slot")
    contract_assert(registry$publication_role[i] %in% c("production_candidate", "challenger", "diagnostic", "research_only"), "Invalid model role")
  }
  contract_assert(all(registry$implementation_status == "design_only"), "This design package must not claim models were implemented")
  contract_assert(all(grepl("otherwise_log_blocker", registry$daily_policy, fixed = TRUE)), "Method accounting must include blockers")
  invisible(TRUE)
}
validate_topic_counts <- function(topics, policy) {
  required <- c("issue_id", "n_present", "n_absent", "n_uncertain", "n_available")
  contract_assert(is.data.frame(topics) && all(required %in% names(topics)), "Fixed-topic count schema mismatch")
  contract_assert(nrow(topics) == 4L && identical(topics$issue_id, policy$fixed_topics), "Four fixed topics missing or reordered")
  for (field in required[-1]) {
    x <- topics[[field]]
    contract_assert(is.numeric(x) && all(is.finite(x) & x >= 0 & x == floor(x)), paste("Invalid count:", field))
  }
  contract_assert(length(unique(topics$n_available)) == 1L, "Available-source denominator differs across fixed issues")
  contract_assert(all(topics$n_present + topics$n_absent + topics$n_uncertain == topics$n_available), "Present/absent/uncertain counts fail reconciliation")
  invisible(TRUE)
}
validate_packet <- function(packet, policy) {
  contract_assert(is.list(packet) && scalar_nonempty(packet$slot_id) && packet$slot_id %in% policy$slot_ids, "Unrecognized analytical slot")
  contract_assert(scalar_nonempty(packet$state) && packet$state %in% policy$render_states, "Invalid render state")
  if (packet$state != "ready") {
    contract_assert(scalar_nonempty(packet$reason), "Unavailable output requires a specific reason")
    contract_assert(is.null(packet$payload) || !length(packet$payload), "Unavailable output must not carry stale numerical payload")
    return(invisible(TRUE))
  }
  for (field in c("source_snapshot_id", "model_id", "definition_id", "as_of_cutoff"))
    contract_assert(scalar_nonempty(packet[[field]]), paste("Missing provenance:", field))
  contract_assert(!is.na(as.POSIXct(packet$as_of_cutoff, format = "%Y-%m-%dT%H:%M:%SZ", tz = "UTC")), "Invalid UTC cutoff")
  contract_assert(identical(packet$release_status, "released"), "Only released results may enter email")
  contract_assert(packet$model_role %in% c("champion", "validated_ensemble"), "Challenger/research/diagnostic output cannot enter email directly")
  contract_assert(is.character(packet$evidence_refs) && length(packet$evidence_refs) > 0L && all(!is.na(packet$evidence_refs) & nzchar(packet$evidence_refs)), "Source evidence required")
  contract_assert(is.list(packet$quality_checks) && identical(sort(names(packet$quality_checks)), sort(policy$required_quality_checks)), "Quality-check schema mismatch")
  contract_assert(all(vapply(packet$quality_checks, isTRUE, logical(1))), "At least one publication gate failed")
  contract_assert(is.list(packet$payload) && length(packet$payload) > 0L, "Ready packet requires a payload")
  contract_assert(is.logical(packet$is_forecast) && length(packet$is_forecast) == 1L && !is.na(packet$is_forecast), "Forecast flag missing")
  contract_assert(!packet$is_forecast || isTRUE(policy$allow_forecasts), "Forecast publication is disabled in D1")
  if (packet$slot_id == "O1") validate_topic_counts(packet$payload$topics, policy)
  invisible(TRUE)
}
build_five_slot_bundle <- function(packets, policy) {
  contract_assert(is.list(packets), "Packets must be a list")
  ids <- vapply(packets, function(p) { contract_assert(scalar_nonempty(p$slot_id), "Missing slot ID"); p$slot_id }, character(1))
  contract_assert(!anyDuplicated(ids) && all(ids %in% policy$slot_ids), "Duplicate or sixth analytical output rejected")
  out <- lapply(seq_along(policy$slot_ids), function(i) {
    id <- policy$slot_ids[i]; at <- match(id, ids)
    packet <- if (is.na(at)) list(slot_id = id, state = "not_ready", reason = "No eligible released analytical result supplied.", payload = NULL) else packets[[at]]
    validate_packet(packet, policy)
    packet$title <- policy$slot_names[i]
    packet
  })
  names(out) <- policy$slot_ids
  out
}
validate_daily_method_ledger <- function(ledger, registry, policy) {
  contract_assert(is.data.frame(ledger) && all(c("method_id", "terminal_status", "reason", "artifact_ref") %in% names(ledger)), "Ledger schema mismatch")
  contract_assert(!anyDuplicated(ledger$method_id) && identical(sort(ledger$method_id), sort(registry$method_id)), "Every method needs exactly one daily summary record")
  contract_assert(all(ledger$terminal_status %in% policy$method_terminal_states), "Unknown method terminal status")
  nonexecuted <- !ledger$terminal_status %in% c("executed", "reused")
  contract_assert(all(!is.na(ledger$reason[nonexecuted]) & nzchar(ledger$reason[nonexecuted])), "Blocker or non-run reason missing")
  contract_assert(all(!is.na(ledger$artifact_ref[!nonexecuted]) & nzchar(ledger$artifact_ref[!nonexecuted])), "Executed/reused rows must identify real artifacts")
  # Artifact existence, hashes, actual model fits and clock checks are upstream integration obligations.
  invisible(TRUE)
}
