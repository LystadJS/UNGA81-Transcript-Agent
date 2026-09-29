# Permanent watchlist and region-first display policy. All operations are native R.
FIXED_ISSUE_IDS <- c("iran", "cuba", "ukraine", "ai")
FIXED_ISSUE_LABELS <- c("Iran", "Cuba", "Ukraine", "AI")
REGION_ORDER <- c("Africa", "Asia-Pacific", "Europe & Eurasia", "Near East", "Western Hemisphere")
validate_issue_book <- function(book) {
  ids <- vapply(book, function(x) str1(x$issue_id), character(1))
  assert(length(ids)>=4 && !anyDuplicated(ids) && all(grepl("^[a-z][a-z0-9_]*$",ids)), "Invalid or duplicate issue IDs")
  fixed <- Filter(function(x)isTRUE(x$fixed),book)
  assert(identical(vapply(fixed,function(x)x$issue_id,character(1)),FIXED_ISSUE_IDS), "Permanent issues must be Iran, Cuba, Ukraine, AI in that order")
  assert(identical(vapply(fixed,function(x)x$label,character(1)),FIXED_ISSUE_LABELS), "Permanent issue labels changed")
  assert(identical(as.integer(vapply(fixed,function(x)x$fixed_order,numeric(1))),1:4), "Fixed issue order is invalid")
  assert(identical(head(ids,4),FIXED_ISSUE_IDS),"Fixed topics must lead the codebook")
  for(x in book) {
    assert(nzchar(str1(x$definition)) && nzchar(str1(x$extractive_regex)),"Issue definition/lexicon is missing")
    assert(is.logical(x$fixed) && length(x$fixed)==1 && !is.na(x$fixed),"Invalid fixed-issue flag")
    assert(is.numeric(x$fixed_order) && length(x$fixed_order)==1 && is.finite(x$fixed_order),"Invalid fixed-issue order")
    assert(isTRUE(x$fixed)||x$fixed_order==0,"Additional topics must have fixed_order=0")
  }
  book
}
bind_issue_schema <- function(schema,book) {
  ids<-as.list(vapply(book,function(x)x$issue_id,character(1)))
  walk<-function(x) {
    if(!is.list(x))return(x)
    if(!is.null(x$issue_id)&&is.list(x$issue_id)&&!is.null(x$issue_id$enum))x$issue_id$enum<-ids
    lapply(x,walk)
  }
  walk(schema)
}
region_sequence <- function(regions,cfg) {
  x<-unique(as.character(regions));preferred<-unlist(cfg$display$region_order %||% as.list(REGION_ORDER),use.names=FALSE)
  c(intersect(preferred,x),sort(setdiff(x,c(preferred,"Unmapped")),method="radix"),intersect("Unmapped",x))
}
country_sort_key <- function(x) {
  # UTF-8 radix ordering is deterministic and does not depend on the host locale.
  # Trim/casefold only; canonical country names and source regions are not rewritten.
  tolower(trimws(enc2utf8(x)))
}
order_country_readouts <- function(speeches,cfg) {
  if(!length(speeches))return(speeches)
  regions<-vapply(speeches,function(s)str1(s$region,"Unmapped"),character(1))
  assert(all(nzchar(regions)),"Blank country region; supply a region or Unmapped")
  names<-vapply(speeches,function(s)s$country,character(1));ids<-vapply(speeches,function(s)s$iso3,character(1))
  speeches[order(match(regions,region_sequence(regions,cfg)),country_sort_key(names),ids,method="radix")]
}
upgrade_replay_topics <- function(analyses,speeches,legacy_book,current_book) {
  # The old 10-category snapshot is immutable. Only three new, narrower codes are
  # scanned provisionally. No-hit is UNCERTAIN, never retrospective proof of absence.
  # Ukraine keeps its original broader v1 decision, labeled explicitly in the audit.
  legacy_ids<-vapply(legacy_book,function(x)x$issue_id,character(1))
  display_book<-lapply(current_book,function(issue) {
    at<-match(issue$issue_id,legacy_ids)
    if(!is.na(at)) {
      old<-legacy_book[[at]]
      old$label<-issue$label;old$short_label<-issue$short_label
      old$fixed<-issue$fixed;old$fixed_order<-issue$fixed_order
      old
    } else {issue$version<-"2.1-provisional-replay-scan";issue}
  })
  for(s in speeches) {
    old<-analyses[[s$iso3]];old_ids<-vapply(old$issues,function(x)x$issue_id,character(1))
    decisions<-lapply(display_book,function(issue) {
      at<-match(issue$issue_id,old_ids)
      if(!is.na(at))return(old$issues[[at]])
      hit<-Filter(function(z)grepl(issue$extractive_regex,z$text,ignore.case=TRUE,perl=TRUE),s$sentences)
      list(issue_id=issue$issue_id,status=if(length(hit))"present" else "uncertain",
        evidence=lapply(head(hit,3),function(z)list(sentence_id=z$id,quote=z$text)),
        rationale=if(length(hit))"Provisional full-text lexicon match for a newly added fixed topic. Exact passage retained; no new semantic model review was performed." else "New fixed topic was not coded in the inherited snapshot. No lexicon match; absence is NOT established.")
    })
    old$issues<-decisions;old$verification$fixed_topic_overlay<-"Iran, Cuba, AI: provisional scan; Ukraine: inherited v1 decision. Not a new semantic review."
    analyses[[s$iso3]]<-old
    validate_analysis(old,s,display_book,inherited=TRUE)
  }
  list(analyses=analyses,codebook=display_book)
}
fixed_scan_note <- function(brief) {
  if(identical(brief$fixed_topic_mode,"provisional_scan_plus_inherited_ukraine"))
    "Archived example: Iran, Cuba and AI counts are provisional text matches, with unmatched cases unresolved. Ukraine retains the original broader v1 code. Fresh daily runs review all four against the full text."
  else if(identical(brief$analysis_mode,"extractive"))
    "Provisional keyword coding: no-match is unresolved, not established absence."
  else ""
}
fixed_watchlist_html <- function(freq,n,brief) {
  at<-match(FIXED_ISSUE_IDS,freq$issue_id);assert(!anyNA(at),"Fixed topic is missing from output")
  f<-freq[at,]
  rows<-vapply(seq_len(4),function(i) {
    count<-if(n)sprintf("%d / %d",f$n_present[i],n) else "No country texts"
    unknown<-if(n)as.character(f$n_unknown[i]) else "Not assessed"
    sprintf('<tr><td style="padding:8px 10px;border-bottom:1px solid #D6DEE7;font-size:13px;font-weight:bold;color:#002D74;">%s</td><td style="padding:8px 10px;border-bottom:1px solid #D6DEE7;font-size:13px;color:#202B38;">%s</td><td style="padding:8px 10px;border-bottom:1px solid #D6DEE7;font-size:13px;color:#202B38;">%s</td></tr>',FIXED_ISSUE_LABELS[i],count,unknown)
  },character(1))
  paste0(section_html("Fixed topics | daily watchlist"),'<table class="fixed-watchlist" role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;border-top:2px solid #002D74;margin:0 0 8px 0;"><tr style="background:#F6F8FA;"><td style="padding:7px 10px;font-size:10px;font-weight:bold;color:#002D74;">ISSUE</td><td style="padding:7px 10px;font-size:10px;font-weight:bold;color:#002D74;">COUNTRIES WITH PRESENCE</td><td style="padding:7px 10px;font-size:10px;font-weight:bold;color:#002D74;">UNRESOLVED</td></tr>',paste(rows,collapse=""),'</table>',p_html("Always shown, including zero counts. Presence is not support; unresolved cases are not counted as absent. Broader Middle East and AI & digital categories remain separate and may overlap.",10),if(nzchar(fixed_scan_note(brief)))p_html(html_escape(fixed_scan_note(brief)),11) else "")
}
region_heading_html <- function(region,n) {
  sprintf('<table class="region-section" role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0" style="width:100%%;margin:24px 0 12px 0;background:#E7F1F8;border-top:2px solid #002D74;"><tr><td style="padding:10px 12px;"><div class="region-title" style="font-family:Georgia,serif;font-size:21px;line-height:26px;font-weight:bold;color:#062135;">%s</div><div style="font-family:Arial,Helvetica,sans-serif;font-size:10px;line-height:15px;color:#52606D;">%d %s | ALPHABETICAL</div></td></tr></table>',html_escape(region),n,if(n==1)"COUNTRY" else "COUNTRIES")
}
