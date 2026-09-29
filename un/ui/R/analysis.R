# Reference-only analytical backend. This does NOT reuse or replace D1 M02/M07/M09.
# A current-run vocabulary is frozen once on the complete eligible corpus.
# Every research output remains audit-only, including when engineering checks pass.

empty_evidence <- function() data.frame(topic_id = character(), topic = character(),
  statement_id = character(), country = character(), country_id = character(),
  source_file = character(), body_sha256 = character(), passage_id = integer(),
  start_char = integer(), end_char = integer(), matched_phrases = character(),
  quote = character(), stringsAsFactors = FALSE)

match_topics <- function(statements, topics) {
  available <- statements[statements$status == "available", , drop = FALSE]
  rows <- list()
  summary <- list()
  for (topic in topics) {
    includes <- unique(c(topic$label, unlist(topic$include, use.names = FALSE)))
    excludes <- unlist(topic$exclude, use.names = FALSE)
    topic_rows <- list()
    for (i in seq_len(nrow(available))) {
      source <- available[i, , drop = FALSE]
      passages <- split_passages(source$text)
      for (j in seq_len(nrow(passages))) {
        quote <- passages$quote[[j]]
        if (length(excludes) && any(vapply(excludes, function(p) phrase_hit(quote, p), logical(1)))) next
        terms <- includes[vapply(includes, function(p) phrase_hit(quote, p), logical(1))]
        if (!length(terms)) next
        topic_rows[[length(topic_rows) + 1L]] <- data.frame(
          topic_id = topic$id, topic = topic$label,
          statement_id = source$statement_id, country = source$country, country_id = source$country_id,
          source_file = source$source_file, body_sha256 = source$body_sha256,
          passage_id = passages$passage_id[[j]], start_char = passages$start_char[[j]],
          end_char = passages$end_char[[j]], matched_phrases = paste(terms, collapse = " | "),
          quote = quote, stringsAsFactors = FALSE)
      }
    }
    ev <- if (length(topic_rows)) do.call(rbind, topic_rows) else empty_evidence()
    rows[[length(rows) + 1L]] <- ev
    country_ids <- unique(available$country_id[nzchar(available$country_id)])
    matched_ids <- unique(ev$country_id[nzchar(ev$country_id)])
    summary[[length(summary) + 1L]] <- data.frame(
      topic = topic$label, texts_with_matches = length(unique(ev$statement_id)),
      eligible_texts = nrow(available), unresolved_texts = nrow(available) - length(unique(ev$statement_id)),
      attributed_countries_with_matches = length(matched_ids),
      available_attributed_countries = length(country_ids),
      quote_count = nrow(ev), interpretation = "literal_candidate_matches_not_semantic_presence",
      stringsAsFactors = FALSE)
  }
  empty_summary <- data.frame(topic = character(), texts_with_matches = integer(), eligible_texts = integer(),
    unresolved_texts = integer(), attributed_countries_with_matches = integer(),
    available_attributed_countries = integer(), quote_count = integer(), interpretation = character())
  list(summary = if (length(summary)) do.call(rbind, summary) else empty_summary,
       evidence = if (length(rows)) do.call(rbind, rows) else empty_evidence(),
       released = FALSE, producer = "prototype_literal_v1")
}

STOP_WORDS <- strsplit(paste(
  "a an and are as at be been being but by can could did do does for from had has have he her hers",
  "him his how i in into is it its me more most my no not of on one or our ours out over she should",
  "so some than that the their them then there these they this those to too under up us very was",
  "we were what when where which who will with would you your country countries nation nations",
  "united assembly president excellency excellencies delegation delegates international global",
  "today thank thanks general speech statement people also must need support call reaffirm"
), " ")[[1L]]

tokenize_document <- function(text) {
  text <- tolower(enc2utf8(text))
  raw_tokens <- regmatches(text, gregexpr("[\\p{L}][\\p{L}\\p{N}'-]{1,39}", text, perl = TRUE))[[1L]]
  if (!length(raw_tokens)) return(character())
  # Bigrams use original adjacent tokens, not stopword-deleted adjacency.
  bigrams <- character()
  if (length(raw_tokens) > 1L) {
    keep <- !head(raw_tokens, -1L) %in% STOP_WORDS & !tail(raw_tokens, -1L) %in% STOP_WORDS
    bigrams <- paste(head(raw_tokens, -1L), tail(raw_tokens, -1L))[keep]
  }
  unigrams <- raw_tokens[!raw_tokens %in% STOP_WORDS & nchar(raw_tokens) > 2L]
  c(unigrams, bigrams)
}

build_reference_features <- function(statements, max_terms = 5000L, max_docs = 500L) {
  d <- statements[statements$discovery_eligible, , drop = FALSE]
  d <- d[order(d$statement_id), , drop = FALSE]
  reference_identity <- paste("prototype_tfidf_v1", d$statement_id, d$body_sha256, sep = "|")
  fingerprint <- sha256_text(reference_identity)
  if (nrow(d) > max_docs) {
    return(list(status = "blocked_resource_limit", reason = "The reference backend is limited to 500 eligible texts; no subset was silently substituted.",
                fingerprint = fingerprint, n = nrow(d), ids = d$statement_id))
  }
  if (nrow(d) < 3L) return(list(status = "insufficient_data", reason = "At least three English-language texts are needed for reference geometry.",
                               fingerprint = fingerprint, n = nrow(d), ids = d$statement_id))
  tokens <- lapply(d$text, tokenize_document)
  df <- table(unlist(lapply(tokens, unique), use.names = FALSE))
  valid <- names(df)[df >= 2L]
  valid <- valid[order(-as.integer(df[valid]), valid)]
  vocabulary <- sort(head(valid, max_terms))
  if (length(vocabulary) < 3L) return(list(status = "insufficient_vocabulary", reason = "Too few repeated content terms for text grouping.",
                                         fingerprint = fingerprint, n = nrow(d), ids = d$statement_id))
  counts <- lapply(tokens, function(x) table(factor(x, levels = vocabulary)))
  # At most 500 x 5,000 cells; the limit is explicit, not an all-passage distance matrix.
  x <- do.call(rbind, lapply(counts, as.numeric))
  dimnames(x) <- list(d$statement_id, vocabulary)
  tf <- log1p(x)
  idf <- log((1 + nrow(d)) / (1 + as.numeric(df[vocabulary]))) + 1
  tfidf <- sweep(tf, 2L, idf, "*")
  norm <- sqrt(rowSums(tfidf^2))
  nonzero <- norm > 0
  tfidf[nonzero, ] <- tfidf[nonzero, , drop = FALSE] / norm[nonzero]
  tfidf <- tfidf[nonzero, , drop = FALSE]
  corpus_fingerprint <- sha256_text(c(reference_identity, vocabulary, sprintf("%.17g", idf)))
  list(status = "ready_for_audit", fingerprint = corpus_fingerprint,
       source_fingerprint = fingerprint, n = nrow(d), ids = rownames(tfidf),
       excluded_zero_ids = d$statement_id[!nonzero], vocabulary = vocabulary, idf = idf,
       x = tfidf, namespace = "prototype_tfidf_v1",
       freeze_policy = "per_run_only_not_the_existing_D1_M02_reference")
}

adjusted_rand <- function(a, b) {
  stopifnot(length(a) == length(b))
  n <- length(a)
  if (n < 2L) return(NA_real_)
  choose2 <- function(x) x * (x - 1) / 2
  tab <- table(a, b)
  index <- sum(choose2(tab))
  aa <- sum(choose2(rowSums(tab)))
  bb <- sum(choose2(colSums(tab)))
  expected <- aa * bb / choose2(n)
  max_index <- (aa + bb) / 2
  if (abs(max_index - expected) < 1e-12) return(if (all(outer(a, a, "==") == outer(b, b, "=="))) 1 else 0)
  (index - expected) / (max_index - expected)
}

fit_reference_discovery <- function(features, statements, seed = 20260928L) {
  withheld <- function(reason, status = "withheld") list(status = status, reason = reason,
    released = FALSE, candidates = data.frame(), diagnostics = data.frame(), feature_hash = features$fingerprint)
  if (features$status != "ready_for_audit") return(withheld(features$reason, features$status))
  x <- features$x
  n <- nrow(x)
  if (n < 12L) return(withheld("At least 12 eligible, nonempty feature vectors are needed for this prototype's clustering diagnostics.", "insufficient_data"))
  if (!requireNamespace("cluster", quietly = TRUE)) return(withheld("The recommended R package 'cluster' is not installed.", "blocked_dependency"))
  cosine <- tcrossprod(x)
  cosine[] <- pmax(-1, pmin(1, cosine))
  distances <- cosine
  distances[] <- sqrt(pmax(0, 2 * (1 - cosine)))
  diag(distances) <- 0
  rownames(distances) <- colnames(distances) <- rownames(x)
  dis <- stats::as.dist(distances)
  hc <- stats::hclust(dis, method = "average")
  k_values <- seq.int(2L, min(6L, floor(n / 3L)))
  fits <- list()
  diagnostics <- list()
  for (method in c("hierarchical", "PAM")) {
    for (k in k_values) {
      fit <- if (method == "hierarchical") {
        list(clustering = stats::cutree(hc, k = k))
      } else {
        cluster::pam(dis, k = k, diss = TRUE, keep.diss = FALSE, keep.data = FALSE)
      }
      groups <- fit$clustering
      sil <- mean(cluster::silhouette(groups, dis)[, "sil_width"])
      key <- paste(method, k, sep = "_")
      fits[[key]] <- fit
      diagnostics[[length(diagnostics) + 1L]] <- data.frame(method = method, k = k,
        silhouette = sil, min_cluster_size = min(table(groups)),
        stability_ari = NA_real_, selected = FALSE, engineering_pass = FALSE, publication_eligible = FALSE)
    }
  }
  diagnostics <- do.call(rbind, diagnostics)
  selected <- integer()
  set.seed(seed)
  for (method in c("hierarchical", "PAM")) {
    rows <- which(diagnostics$method == method)
    candidates <- rows[diagnostics$min_cluster_size[rows] >= 3L]
    if (!length(candidates)) candidates <- rows
    ix <- candidates[order(-diagnostics$silhouette[candidates], diagnostics$k[candidates])][[1L]]
    selected <- c(selected, ix)
    diagnostics$selected[[ix]] <- TRUE
    k <- diagnostics$k[[ix]]
    full <- fits[[paste(method, k, sep = "_")]]$clustering
    # Roster-deletion sensitivity is NOT a confidence interval or gold-label validation.
    aris <- vapply(seq_len(12L), function(iter) {
      keep <- sort(sample.int(n, max(k + 2L, floor(n * 0.8))))
      sd <- stats::as.dist(distances[keep, keep, drop = FALSE])
      new <- if (method == "hierarchical") stats::cutree(stats::hclust(sd, method = "average"), k = k) else
        cluster::pam(sd, k = k, diss = TRUE, keep.diss = FALSE, keep.data = FALSE)$clustering
      adjusted_rand(full[keep], new)
    }, numeric(1))
    diagnostics$stability_ari[[ix]] <- mean(aris, na.rm = TRUE)
    diagnostics$engineering_pass[[ix]] <- diagnostics$silhouette[[ix]] >= 0.15 &&
      diagnostics$stability_ari[[ix]] >= 0.75 && diagnostics$min_cluster_size[[ix]] >= 3L
  }
  ix <- selected[diagnostics$method[selected] == "PAM"][[1L]]
  selected_fit <- fits[[paste("PAM", diagnostics$k[[ix]], sep = "_")]]
  groups <- selected_fit$clustering
  candidate_rows <- list()
  for (group in sort(unique(groups))) {
    members <- which(groups == group)
    specificity <- colMeans(x[members, , drop = FALSE]) - colMeans(x)
    top <- colnames(x)[order(-specificity, colnames(x))][seq_len(min(5L, ncol(x)))]
    medoid_index <- members[which.min(rowSums(distances[members, members, drop = FALSE]))]
    source <- statements[match(rownames(x)[medoid_index], statements$statement_id), , drop = FALSE]
    example <- split_passages(source$text)
    quote <- if (nrow(example)) example$quote[[1L]] else source$text
    member_sources <- statements[match(rownames(x)[members], statements$statement_id), , drop = FALSE]
    candidate_rows[[length(candidate_rows) + 1L]] <- data.frame(
      candidate = paste0("Group ", group), suggested_terms = paste(top, collapse = " / "),
      texts = length(members), attributed_countries = length(unique(member_sources$country_id[nzchar(member_sources$country_id)])),
      representative_statement_id = source$statement_id, representative_excerpt = quote,
      engineering_pass = diagnostics$engineering_pass[[ix]], publication_eligible = FALSE,
      stringsAsFactors = FALSE)
  }
  # PCA scores from centered document Gram matrix; equivalent score geometry, no dense term covariance.
  centered <- scale(x, center = TRUE, scale = FALSE)
  eig <- eigen(tcrossprod(centered), symmetric = TRUE)
  positive <- pmax(0, eig$values)
  pca <- eig$vectors[, 1:2, drop = FALSE] %*% diag(sqrt(positive[1:2]), 2L)
  rownames(pca) <- rownames(x)
  pcoa <- tryCatch(stats::cmdscale(dis, k = 2L, eig = TRUE), error = function(e) NULL)
  assignments <- data.frame(statement_id = rownames(x), group = unname(groups), stringsAsFactors = FALSE)
  list(status = "audit_only", released = FALSE,
       reason = "Current-corpus research candidates only. No released producer, comparable history, or emergence validation is present.",
       candidates = do.call(rbind, candidate_rows), diagnostics = diagnostics,
       assignments = assignments, feature_hash = features$fingerprint,
       pca = pca, pca_explained = positive[1:2] / sum(positive), pcoa = pcoa,
       policy = "No reference-backend method is a D1 producer; engineering checks never release email content.")
}

validate_evidence <- function(evidence, statements) {
  if (!nrow(evidence)) return(TRUE)
  for (i in seq_len(nrow(evidence))) {
    e <- evidence[i, , drop = FALSE]
    index <- match(e$statement_id, statements$statement_id)
    if (is.na(index)) user_error("An evidence link refers to an unknown source.", "evidence_failed")
    s <- statements[index, , drop = FALSE]
    if (s$status != "available" || e$body_sha256 != s$body_sha256 ||
        !identical(substr(s$text, e$start_char, e$end_char), e$quote)) {
      user_error("A quotation did not match its source. The draft was withheld.", "evidence_failed")
    }
  }
  TRUE
}
