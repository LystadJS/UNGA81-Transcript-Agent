#!/usr/bin/env Rscript
# Synthetic engineering checks only. No country data or models are analyzed.
args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args)) normalizePath(args[1], mustWork = TRUE) else normalizePath(".", mustWork = TRUE)
source(file.path(root, "config", "email_policy.R"), encoding = "UTF-8")
source(file.path(root, "R", "validate_contract.R"), encoding = "UTF-8")
registry <- read_method_registry(file.path(root, "config", "method_registry.csv"))
results <- list()
check <- function(name, code, reject = FALSE) {
  e <- tryCatch({force(code); NULL}, error = identity)
  pass <- if (reject) inherits(e, "error") else is.null(e)
  results[[length(results) + 1L]] <<- data.frame(test = name, passed = pass,
      note = if (inherits(e, "error")) conditionMessage(e) else "passed", stringsAsFactors = FALSE)
  cat(if (pass) "PASS" else "FAIL", name, "\n")
}
check("complete D1 registry", validate_design(registry, email_policy))
bad <- registry[-1, ]; check("missing method rejected", validate_design(bad, email_policy), TRUE)
bad <- registry; bad$method_id[2] <- bad$method_id[1]; check("duplicate method rejected", validate_design(bad, email_policy), TRUE)
bad <- registry; bad$email_slots[1] <- "O6"; check("method cannot route to sixth slot", validate_design(bad, email_policy), TRUE)
bad <- registry; bad$implementation_status[1] <- "executed"; check("design cannot claim completed model", validate_design(bad, email_policy), TRUE)
bad <- registry; bad$required_gates[1] <- ""; check("missing data gate rejected", validate_design(bad, email_policy), TRUE)
p <- email_policy; p$slot_ids <- c(p$slot_ids, "O6"); check("sixth policy slot rejected", validate_design(registry, p), TRUE)
p <- email_policy; p$fixed_topics <- rev(p$fixed_topics); check("fixed topic reordering rejected", validate_design(registry, p), TRUE)
p <- email_policy; p$region_order <- rev(p$region_order); check("region policy preserved", validate_design(registry, p), TRUE)
p <- email_policy; p$old_issue_figures_inline <- TRUE; check("legacy extra charts rejected", validate_design(registry, p), TRUE)
p <- email_policy; p$allow_automatic_send <- TRUE; check("sending remains disabled", validate_design(registry, p), TRUE)
p <- email_policy; p$keep_country_summaries <- FALSE; check("country readouts retained", validate_design(registry, p), TRUE)
p <- email_policy; p$max_image_width <- 1400L; check("oversized inline image rejected", validate_design(registry, p), TRUE)
empty <- build_five_slot_bundle(list(), email_policy)
check("empty input yields exactly five named slots", contract_assert(identical(names(empty), paste0("O",1:5)), "wrong slots"))
check("cold start carries no fake numerical values", contract_assert(all(vapply(empty, function(x)x$state == "not_ready" && is.null(x$payload), logical(1))), "fake payload"))
check("duplicate packet rejected", build_five_slot_bundle(list(empty[[1]], empty[[1]]), email_policy), TRUE)
bad <- empty[[1]]; bad$slot_id <- "O6"; check("sixth packet rejected", build_five_slot_bundle(list(bad), email_policy), TRUE)
bad <- empty[[1]]; bad$reason <- ""; check("missing unavailability reason rejected", validate_packet(bad, email_policy), TRUE)
bad <- empty[[1]]; bad$payload <- list(value = 0); check("unavailable is not numerical zero", validate_packet(bad, email_policy), TRUE)
# Synthetic counts are testing the schema; they are not the user's speech counts.
counts <- data.frame(issue_id = email_policy$fixed_topics, n_present = c(1,0,2,1),
                     n_absent = c(0,0,0,1), n_uncertain = c(1,2,0,0), n_available = 2)
packet <- list(slot_id = "O1", state = "ready", source_snapshot_id = "synthetic_fixture",
    model_id = "engineering_fixture", definition_id = "test_only", as_of_cutoff = "2026-09-25T00:00:00Z",
    release_status = "released", model_role = "champion", evidence_refs = "synthetic_evidence",
    quality_checks = setNames(rep(list(TRUE), length(email_policy$required_quality_checks)), email_policy$required_quality_checks),
    payload = list(topics = counts), is_forecast = FALSE)
check("ready synthetic fixed-topic packet", validate_packet(packet, email_policy))
bad <- packet; bad$payload$topics$n_present[1] <- -1; check("negative counts rejected", validate_packet(bad, email_policy), TRUE)
bad <- packet; bad$payload$topics$n_present[1] <- 0.5; check("fractional country counts rejected", validate_packet(bad, email_policy), TRUE)
bad <- packet; bad$payload$topics$n_uncertain[2] <- 0; check("unresolved cannot disappear from denominator", validate_packet(bad, email_policy), TRUE)
bad <- packet; bad$payload$topics <- bad$payload$topics[4:1, ]; check("packet fixed topic order preserved", validate_packet(bad, email_policy), TRUE)
for (gate in email_policy$required_quality_checks) {
 bad <- packet; bad$quality_checks[[gate]] <- FALSE
 check(paste("failed gate rejected:",gate), validate_packet(bad, email_policy), TRUE)
}
bad <- packet; bad$evidence_refs <- character(); check("unsupported result rejected", validate_packet(bad, email_policy), TRUE)
bad <- packet; bad$release_status <- "research_only"; check("research output withheld", validate_packet(bad, email_policy), TRUE)
bad <- packet; bad$model_role <- "challenger"; check("challenger cannot bypass primary selection", validate_packet(bad, email_policy), TRUE)
bad <- packet; bad$is_forecast <- TRUE; check("forecast is not an observed result", validate_packet(bad, email_policy), TRUE)
bad <- packet; bad$as_of_cutoff <- "tomorrow"; check("invalid cutoff rejected", validate_packet(bad, email_policy), TRUE)
filled <- build_five_slot_bundle(list(packet), email_policy)
check("one ready output retains all five slots", contract_assert(length(filled)==5L && filled[[2]]$state=="not_ready", "missing placeholder"))
ledger <- data.frame(method_id=registry$method_id, terminal_status="not_implemented", reason="Design only; no model adapter implemented.", artifact_ref="", stringsAsFactors=FALSE)
check("complete truthful nonexecution ledger", validate_daily_method_ledger(ledger,registry,email_policy))
check("silent missing method rejected", validate_daily_method_ledger(ledger[-1,],registry,email_policy), TRUE)
bad <- ledger; bad$reason[1] <- ""; check("unexplained skip rejected", validate_daily_method_ledger(bad,registry,email_policy), TRUE)
bad <- ledger; bad$terminal_status[1] <- "executed"; check("execution without artifact rejected", validate_daily_method_ledger(bad,registry,email_policy), TRUE)
report <- do.call(rbind, results)
dir.create(file.path(root,"validation"),showWarnings=FALSE)
utils::write.csv(report,file.path(root,"validation","contract_tests.csv"),row.names=FALSE,na="")
cat(sprintf("Executed successfully: %d/%d engineering checks passed. No models trained or scored.\n",sum(report$passed),nrow(report)))
if (any(!report$passed)) quit(status=1L)
