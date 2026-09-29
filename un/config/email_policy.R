# Design D1: display/routing policy only. Sourcing this file runs no models.
email_policy <- list(
  design_version = "D1",
  slot_ids = c("O1", "O2", "O3", "O4", "O5"),
  slot_names = c("Fixed-topic monitor", "Emerging issues", "Country discourse map",
                 "Rhetorical movement", "Discourse-network changes"),
  fixed_topics = c("iran", "cuba", "ukraine", "ai"),
  region_order = c("Africa", "Asia-Pacific", "Europe & Eurasia", "Near East", "Western Hemisphere"),
  country_grouping = "region_then_alphabetical",
  keep_country_summaries = TRUE,
  extra_analytics = FALSE,
  old_issue_figures_inline = FALSE,
  max_image_width = 840L,
  max_analytical_images = 3L,
  allow_forecasts = FALSE,
  allow_automatic_send = FALSE,
  required_quality_checks = c("source", "time_cutoff", "version", "definition", "coverage",
                              "validation", "uncertainty", "neutrality"),
  render_states = c("ready", "not_ready", "not_updated", "failed", "withheld"),
  method_terminal_states = c("executed", "reused", "blocked_data", "blocked_labels", "blocked_history",
     "blocked_dependency", "blocked_authorization", "blocked_resources", "blocked_version",
     "blocked_regime", "not_due", "failed", "withheld_quality", "not_implemented")
)
