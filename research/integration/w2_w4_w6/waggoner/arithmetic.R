# Independent base-R arithmetic and synthetic table parity oracle.
# No packages, source loading, fitting, network requests or publication permission.
# This is not an alternate empirical producer or a schema-authentication service.

us_norm <- function(x) {
  scale <- max(abs(x))
  if (scale == 0) 0 else scale * sqrt(sum((x / scale)^2))
}

us_point <- function(country, us) {
  stopifnot(is.numeric(country), is.numeric(us), length(country) >= 2L, length(country) <= 1024L,
            length(country) == length(us), all(is.finite(c(country, us))),
            all(abs(c(country, us)) <= 1e100))
  relative <- country - us
  list(relative_vector = relative, distance = us_norm(relative))
}

us_transition <- function(c0, c1, u0, u1) {
  stopifnot(length(c0) == length(c1))
  a <- us_point(c0, u0)
  b <- us_point(c1, u1)
  dc <- c1 - c0
  du <- u1 - u0
  dr <- dc - du
  total <- a$relative_vector + b$relative_vector
  qc <- sum(total * dc)
  qu <- -sum(total * du)
  denom <- a$distance + b$distance
  gc <- if (denom > 0) sum((total / denom) * dc) else NA_real_
  gu <- if (denom > 0) -sum((total / denom) * du) else NA_real_
  list(gap_change = b$distance - a$distance,
       country_displacement = us_norm(dc),
       us_displacement = us_norm(du),
       relative_displacement = us_norm(dr),
       squared_gap_country_contribution = qc,
       squared_gap_us_contribution = qu,
       gap_country_contribution = gc, gap_us_contribution = gu,
       decomposition_status = if (denom > 0) "ready" else "undefined_zero_gaps")
}

# Only the test harness invokes this local TSV boundary. It writes fictional
# vectors and reviewed synthetic metadata into a fresh temporary directory.
run_synthetic_tables <- function(directory) {
  read_table <- function(name) {
    read.delim(file.path(directory, name), check.names = FALSE,
               stringsAsFactors = FALSE, na.strings = "", quote = "")
  }
  write_table <- function(x, name) {
    write.table(x, file.path(directory, name), sep = "\t", quote = FALSE,
                row.names = FALSE, na = "")
  }
  options(digits = 17)
  rows <- read_table("source.tsv")
  periods <- read_table("periods.tsv")
  config <- read_table("scope.tsv")
  stopifnot(nrow(config) == 1L, identical(config$split, "synthetic"),
            identical(config$baseline, "USA"), identical(config$support_mode, "common"),
            identical(config$weight_policy, "w4_equal_meeting_within_genre_equal_genre_v1"))
  countries <- strsplit(config$countries, ",", fixed = TRUE)[[1L]]
  genres <- strsplit(config$genres, ",", fixed = TRUE)[[1L]]
  stopifnot("USA" %in% countries, !anyDuplicated(countries), !anyDuplicated(periods$id),
            all(grepl("^(syn-|fictional-)", rows$id)), !anyDuplicated(rows$id),
            all(periods$start <= periods$end),
            all(head(periods$end, -1L) < tail(periods$start, -1L)))
  vector_names <- grep("^v[0-9]+$", names(rows), value = TRUE)
  stopifnot(length(vector_names) >= 2L)
  exclusion <- function(r) {
    if (r$source_status != "available") return(r$source_status)
    if (r$capacity != "national") return("non_national_capacity")
    if (r$attribution_status != "synthetic_verified" || is.na(r$country_iso3)) return("attribution_unverified")
    if (!(r$genre %in% genres) || r$language != config$language ||
        r$source_type != config$source_type || r$topic_id != config$topic_id) return("scope_excluded")
    NA_character_
  }
  excluded <- vapply(seq_len(nrow(rows)), function(i) exclusion(rows[i, , drop = FALSE]), character(1))
  profiles <- list()
  weights <- data.frame(profile_id = character(), observation_id = character(), weight = numeric())
  summary <- data.frame(id = character(), country_iso3 = character(), period = character(),
                        state = character(), reason = character(), stringsAsFactors = FALSE)
  for (country in countries) for (period in periods$id) {
    candidates <- which(!is.na(rows$country_iso3) & rows$country_iso3 == country & rows$period == period)
    selected <- candidates[is.na(excluded[candidates])]
    state <- "ready"
    reason <- NA_character_
    if (!length(candidates)) { state <- "empty"; reason <- "country_missing" }
    else if (!length(selected)) {
      reasons <- excluded[candidates]
      state <- if (any(reasons %in% c("failed", "inventory_failed"))) "failed" else "withheld"
      reason <- if ("attribution_unverified" %in% reasons) "attribution_unverified" else
        if ("unverified" %in% reasons) "source_unverified" else
          if (state == "failed") "source_failed" else "no_eligible_country_sources"
    } else if (!setequal(unique(rows$genre[selected]), genres)) {
      state <- "withheld"; reason <- "scope_incompatible"
    }
    id <- paste(country, period, sep = "/")
    v <- rep(NA_real_, length(vector_names))
    if (state == "ready") {
      all_weights <- numeric(length(selected))
      selected_rows <- rows[selected, , drop = FALSE]
      for (genre in genres) {
        meetings <- unique(selected_rows$meeting_id[selected_rows$genre == genre])
        for (meeting in meetings) {
          ix <- which(selected_rows$genre == genre & selected_rows$meeting_id == meeting)
          all_weights[ix] <- 1 / length(genres) / length(meetings) / length(ix)
        }
      }
      values <- as.matrix(selected_rows[, vector_names, drop = FALSE])
      stopifnot(all(is.finite(values)), abs(sum(all_weights) - 1) <= 1e-10)
      v <- colSums(values * all_weights)
      weights <- rbind(weights, data.frame(profile_id = id, observation_id = selected_rows$id, weight = all_weights))
    }
    profiles[[id]] <- list(vector = v, state = state, reason = reason)
    summary <- rbind(summary, data.frame(id = id, country_iso3 = country, period = period, state = state, reason = reason))
  }
  comparisons <- data.frame(id = character(), state = character(), reason = character(), distance = numeric())
  transitions <- list()
  for (country in countries) {
    for (period in periods$id) {
      id <- paste(country, period, sep = "/")
      cp <- profiles[[id]]
      up <- profiles[[paste("USA", period, sep = "/")]]
      ready <- cp$state == "ready" && up$state == "ready"
      reason <- if (ready) NA_character_ else if (up$state != "ready") "baseline_missing" else cp$reason
      comparisons <- rbind(comparisons, data.frame(id = id, state = if (ready) "ready" else "withheld", reason = reason,
                           distance = if (ready) us_point(cp$vector, up$vector)$distance else NA_real_))
    }
    for (i in seq.int(2L, nrow(periods))) {
      before <- periods$id[i - 1L]
      after <- periods$id[i]
      c0 <- profiles[[paste(country, before, sep = "/")]]
      c1 <- profiles[[paste(country, after, sep = "/")]]
      u0 <- profiles[[paste("USA", before, sep = "/")]]
      u1 <- profiles[[paste("USA", after, sep = "/")]]
      ready <- all(vapply(list(c0,c1,u0,u1), function(x) x$state == "ready", logical(1)))
      metrics <- if (ready) us_transition(c0$vector, c1$vector, u0$vector, u1$vector) else
        list(gap_change=NA_real_,country_displacement=NA_real_,us_displacement=NA_real_,relative_displacement=NA_real_,
             squared_gap_country_contribution=NA_real_,squared_gap_us_contribution=NA_real_,
             gap_country_contribution=NA_real_,gap_us_contribution=NA_real_,decomposition_status=NA_character_)
      transitions[[length(transitions) + 1L]] <- as.data.frame(c(list(country_iso3=country,before=before,after=after,
        state=if(ready) "ready" else "withheld",reason=if(ready) NA_character_ else "endpoint_unavailable"),metrics), stringsAsFactors=FALSE)
    }
  }
  write_table(summary,"r_profiles.tsv")
  write_table(weights,"r_weights.tsv")
  write_table(comparisons,"r_comparisons.tsv")
  write_table(do.call(rbind,transitions),"r_transitions.tsv")
  invisible(TRUE)
}

if (sys.nframe() == 0L) {
  args <- commandArgs(trailingOnly = TRUE)
  stopifnot(length(args) == 1L, dir.exists(args[[1L]]))
  run_synthetic_tables(args[[1L]])
  cat("PASS: independent base-R synthetic profiles, weights, states and trajectories\n")
}
