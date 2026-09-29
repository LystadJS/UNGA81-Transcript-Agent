# Full-width, unsent MIME drafts. Exactly five analytical slots; none can be
# promoted by a user checkbox or by a reference clustering diagnostic.

make_packets <- function(config) {
  topic_names <- vapply(config$fixed_topics, `[[`, character(1), "label")
  reasons <- c(
    if (length(topic_names)) paste0("Requested topics: ", paste(topic_names, collapse = "; "),
      ". Literal phrase candidates are available in the application audit view. No validated issue-presence classifier is released in this prototype.") else
      "No tracked issues were requested. Full-corpus discovery still runs.",
    "Insufficient comparable history to assess emergence. Current-corpus text groupings remain audit-only.",
    "Map withheld. The prototype has no D1-approved fixed-reference projection release.",
    "No comparable prior observation is available to establish rhetorical movement.",
    "No comparable prior network is available to establish discourse-network changes."
  )
  lapply(seq_along(SLOT_TITLES), function(i) list(id = names(SLOT_TITLES)[[i]],
    title = unname(SLOT_TITLES[[i]]), status = "unavailable", released = FALSE,
    reason = reasons[[i]], payload = NULL, evidence_layer = "NO_RELEASED_ANALYTICAL_CLAIM"))
}

validate_packets <- function(packets, reference = TRUE) {
  ids <- vapply(packets, `[[`, character(1), "id")
  if (!identical(ids, names(SLOT_TITLES))) user_error("The five-output publication contract failed.", "publication_failed")
  if (reference && any(vapply(packets, function(p) isTRUE(p$released) || !is.null(p$payload), logical(1)))) {
    user_error("A reference-backend result cannot be published as validated analysis.", "publication_failed")
  }
  TRUE
}

base64_encode <- function(text) {
  bytes <- as.integer(if (is.raw(text)) text else charToRaw(enc2utf8(text)))
  if (!length(bytes)) return("")
  n <- length(bytes)
  padded <- c(bytes, rep(0L, (3L - n %% 3L) %% 3L))
  mat <- matrix(padded, ncol = 3L, byrow = TRUE)
  indices <- cbind(bitwShiftR(mat[, 1L], 2L),
    bitwShiftL(bitwAnd(mat[, 1L], 3L), 4L) + bitwShiftR(mat[, 2L], 4L),
    bitwShiftL(bitwAnd(mat[, 2L], 15L), 2L) + bitwShiftR(mat[, 3L], 6L),
    bitwAnd(mat[, 3L], 63L))
  alphabet <- strsplit("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/", "", fixed = TRUE)[[1L]]
  out <- alphabet[as.vector(t(indices)) + 1L]
  pad <- (3L - n %% 3L) %% 3L
  if (pad) out[(length(out) - pad + 1L):length(out)] <- "="
  paste0(out, collapse = "")
}

wrap_base64 <- function(x) {
  if (!nzchar(x)) return("")
  starts <- seq.int(1L, nchar(x), by = 76L)
  paste(substring(x, starts, pmin(starts + 75L, nchar(x))), collapse = "\r\n")
}

country_extracts <- function(statements, evidence, max_quotes = 2L) {
  data <- statements[statements$status == "available", , drop = FALSE]
  data$display_country <- ifelse(nzchar(data$country), data$country, "Unattributed transcript")
  order_index <- match(data$region, REGION_ORDER)
  order_index[is.na(order_index)] <- length(REGION_ORDER) + 1L
  data <- data[order(order_index, data$region, tolower(data$display_country), data$speech_date, data$statement_id), , drop = FALSE]
  lapply(seq_len(nrow(data)), function(i) {
    s <- data[i, , drop = FALSE]
    relevant <- evidence[evidence$statement_id == s$statement_id, , drop = FALSE]
    if (nrow(relevant)) {
      relevant <- relevant[!duplicated(relevant$quote), , drop = FALSE]
      quotes <- head(relevant$quote, max_quotes)
    } else {
      quotes <- head(split_passages(s$text)$quote, max_quotes)
    }
    list(country = s$display_country, region = s$region, speaker = s$speaker,
         speech_date = s$speech_date, statement_id = s$statement_id,
         source_file = s$source_file, body_sha256 = s$body_sha256,
         source_url = s$source_url, quotes = quotes)
  })
}

render_email <- function(config, statements, tracked, packets, run_id) {
  validate_packets(packets)
  is_demo <- identical(config$source, "demo")
  label <- if (is_demo) "PRACTICE DATA — NOT A UN ASSESSMENT" else "PROTOTYPE — SOURCE EXTRACTS, NOT VALIDATED ANALYSIS"
  available <- sum(statements$status == "available")
  unavailable <- sum(statements$status == "missing_text")
  other <- nrow(statements) - available - unavailable
  coverage <- sprintf("%d available texts; %d missing-text entries; %d excluded or duplicate entries. Scope is the supplied files, not all UN members.", available, unavailable, other)
  extracts <- country_extracts(statements, tracked$evidence)
  h <- html_escape
  slot_html <- vapply(packets, function(p) paste0(
    '<section data-output-id="', p$id, '" style="padding:16px 0;border-bottom:1px solid #D6DEE7">',
    '<h2 style="margin:0 0 8px;font:700 19px Georgia,serif;color:#062135">', p$id, '. ', h(p$title), '</h2>',
    '<p style="margin:0;font:14px/1.5 Arial,sans-serif;color:#465365">', h(p$reason), '</p></section>'
  ), character(1))
  groups <- unique(vapply(extracts, `[[`, character(1), "region"))
  country_html <- vapply(groups, function(region) {
    selected <- extracts[vapply(extracts, function(x) identical(x$region, region), logical(1))]
    cards <- vapply(selected, function(x) {
      source_link <- if (grepl("^https://[^[:space:]]+$", x$source_url)) paste0('<a href="', h(x$source_url),
        '" style="color:#002D74">Source</a> · ') else ""
      paste0('<article class="country-card" style="margin:0 0 16px;padding:14px 0;border-bottom:1px solid #D6DEE7">',
        '<h3 style="margin:0 0 8px;font:700 19px Georgia,serif;color:#062135">', h(x$country), '</h3>',
        '<p style="margin:0 0 10px;font:12px Arial,sans-serif;color:#465365">', h(x$speaker),
        if (nzchar(x$speaker)) ' · ' else '', h(x$speech_date), ' · SOURCE EXTRACTS</p>',
        paste0('<blockquote style="margin:8px 0;padding:0 0 0 12px;border-left:3px solid #D6DEE7;font:14px/1.55 Arial,sans-serif">',
          h(x$quotes), '</blockquote>', collapse = ''),
        '<p style="margin:8px 0 0;font:10px/1.5 Arial,sans-serif;color:#667085;overflow-wrap:anywhere">',
        source_link, h(x$source_file), ' · ', h(x$statement_id), '</p></article>')
    }, character(1))
    paste0('<h2 class="region-heading" style="margin:24px 0 4px;padding:9px 12px;background:#002D74;color:white;font:700 17px Arial,sans-serif">',
           h(region), '</h2>', paste0(cards, collapse = ''))
  }, character(1))
  html <- paste0('<!doctype html><html lang="en"><head><meta charset="UTF-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    '<meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; style-src &#39;unsafe-inline&#39;; img-src data:; base-uri &#39;none&#39; form-action &#39;none&#39;">',
    '<title>UN transcript readout — prototype</title>',
    '<style>@page{size:Letter;margin:.55in}body{margin:0}.country-card{break-inside:avoid}.region-heading{break-after:avoid;page-break-after:avoid}p,blockquote{orphans:3;widows:3}section{break-inside:avoid}@media print{.outer{padding:0!important}a{color:#002D74}}</style></head>',
    '<body style="margin:0;background:white;color:#202B38">',
    '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="width:100%;border-collapse:collapse"><tr><td style="background:#002D74;padding:20px 26px;color:white">',
    '<div style="font:700 12px Arial,sans-serif;letter-spacing:1.5px">UN TRANSCRIPT INTELLIGENCE</div>',
    '<div style="margin-top:6px;font:28px Georgia,serif">Daily Readout</div>',
    '</td></tr><tr><td class="outer" style="padding:22px 26px">',
    '<p style="font:700 12px Arial,sans-serif;color:#80551B;background:#FFF6E7;padding:10px;border-left:3px solid #A87B37">', h(label), '</p>',
    '<p style="font:14px Arial,sans-serif">Reporting period: ', h(config$start_date), ' to ', h(config$end_date), '</p>',
    '<p style="font:13px/1.5 Arial,sans-serif;color:#465365">', h(coverage), '</p>',
    '<h2 style="font:700 19px Georgia,serif;color:#062135">Readout status</h2>',
    '<p style="font:14px/1.55 Arial,sans-serif">This draft contains exact source extracts. Topic matching is preliminary; learned groupings remain in the audit view. No stance, alignment, or emergence claim has been released. Review source context before use.</p>',
    paste0(slot_html, collapse = ''),
    '<h2 class="region-heading" style="margin:25px 0 8px;font:700 22px Georgia,serif;color:#062135">Country source extracts</h2>',
    if (!length(extracts)) '<p>No source text passed the reporting-period checks. Missing text is not evidence of silence on an issue.</p>' else paste0(country_html, collapse = ''),
    '<p style="border-top:2px solid #002D74;padding-top:12px;font:10px/1.5 Arial,sans-serif;color:#667085">',
    'Unsent draft · No external AI processing · ', h(run_id), ' · ', h(config$requested_at_utc),
    '<br>Country and regional labels are supplied metadata, not independently verified registry matches. The prototype is not the approved D1 production release.</p>',
    '</td></tr></table></body></html>')
  plain_slots <- vapply(packets, function(p) paste(paste0(p$id, ". ", p$title), p$reason, sep = "\n"), character(1))
  plain_cards <- vapply(extracts, function(x) paste(c(paste(x$region, x$country, sep = " | "),
    paste(x$speech_date, x$speaker, sep = " | "), "SOURCE EXTRACTS", x$quotes,
    paste("Source:", x$source_file), paste("Statement ID:", x$statement_id)), collapse = "\n"), character(1))
  plain <- paste(c("UN TRANSCRIPT INTELLIGENCE | Daily Readout", label,
    paste("Reporting period:", config$start_date, "to", config$end_date), coverage,
    "Exact source extracts; not a validated analytical readout. Learned groupings remain audit-only.",
    plain_slots, "COUNTRY SOURCE EXTRACTS", plain_cards, paste("Unsent draft |", run_id)), collapse = "\n\n")
  boundary <- paste0("readout_", substr(sha256_text(c(run_id, plain)), 1L, 24L))
  subject <- paste("[PROTOTYPE] UN transcript readout", config$start_date, "to", config$end_date)
  eml <- paste0(paste(c("MIME-Version: 1.0", "X-Unsent: 1",
    paste0("Subject: ", subject),
    paste0('Content-Type: multipart/alternative; boundary="', boundary, '"'), "", paste0("--", boundary),
    "Content-Type: text/plain; charset=UTF-8", "Content-Transfer-Encoding: base64", "",
    wrap_base64(base64_encode(plain)), paste0("--", boundary),
    "Content-Type: text/html; charset=UTF-8", "Content-Transfer-Encoding: base64", "",
    wrap_base64(base64_encode(html)), paste0("--", boundary, "--"), ""), collapse = "\r\n"))
  list(html = html, text = plain, eml = eml)
}

find_browser <- function() {
  override <- Sys.getenv("UN_READOUT_BROWSER", "")
  if (nzchar(override) && file.exists(override)) return(normalizePath(override))
  names <- c("chromium", "chromium-browser", "google-chrome", "msedge")
  paths <- unname(Sys.which(names))
  paths <- paths[nzchar(paths)]
  candidates <- c(paths,
    file.path(Sys.getenv("PROGRAMFILES"), "Google/Chrome/Application/chrome.exe"),
    file.path(Sys.getenv("PROGRAMFILES(X86)"), "Microsoft/Edge/Application/msedge.exe"),
    file.path(Sys.getenv("PROGRAMFILES"), "Microsoft/Edge/Application/msedge.exe"),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
  candidates <- candidates[file.exists(candidates)]
  if (length(candidates)) normalizePath(candidates[[1L]]) else ""
}

render_pdf <- function(html_path, output_path, job_dir, helper_path = "") {
  browser <- find_browser()
  if (!nzchar(browser)) return(list(status = "unavailable", engine = "none", reason = "No local Chrome, Edge, or Chromium was found. Print the saved HTML to PDF in a browser."))
  if (requireNamespace("pagedown", quietly = TRUE)) {
    args <- "--disable-dev-shm-usage"
    if (identical(Sys.getenv("UN_READOUT_BROWSER_NO_SANDBOX"), "1")) args <- c(args, "--no-sandbox", "--no-zygote", "--single-process")
    ok <- tryCatch({
      pagedown::chrome_print(input = html_path, output = output_path, browser = browser,
        wait = 0.5, timeout = 40, extra_args = args, outline = FALSE,
        options = list(printBackground = TRUE, preferCSSPageSize = TRUE))
      TRUE
    }, error = function(e) {write_utf8(conditionMessage(e), file.path(job_dir, "pdf-native-error.log")); FALSE})
    if (ok && file.exists(output_path) && file.info(output_path)$size > 1000L) {
      return(list(status = "created", engine = "pagedown", reason = "Local R/browser PDF export completed."))
    }
  }
  # Optional fallback: never install Python, Playwright, or browser binaries here.
  python <- unname(Sys.which(c("python3", "python")))
  python <- python[nzchar(python)]
  if (length(python) && nzchar(helper_path) && file.exists(helper_path)) {
    log <- file.path(job_dir, "pdf.log")
    result <- tryCatch(system2(python[[1L]], c(shQuote(normalizePath(helper_path)),
      shQuote(normalizePath(html_path)), shQuote(output_path), shQuote(browser)),
      stdout = log, stderr = log, timeout = 45), error = function(e) 1L)
    if (identical(result, 0L) && file.exists(output_path) && file.info(output_path)$size > 1000L &&
        identical(rawToChar(readBin(output_path, "raw", n = 5L)), "%PDF-")) {
      return(list(status = "created", engine = "optional_python_playwright", reason = "PDF created with the installed local-browser fallback; no remote service was used."))
    }
  }
  list(status = "unavailable", engine = "none", reason = "Automatic PDF export is unavailable. Install approved pagedown/browser dependencies, or print the saved HTML from your browser.")
}
