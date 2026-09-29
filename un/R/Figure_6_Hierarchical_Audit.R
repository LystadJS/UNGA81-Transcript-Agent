#!/usr/bin/env Rscript
# Standalone, deterministic R graphics; no network or model fitting.
# Usage: Rscript R/Figure_6_Hierarchical_Audit.R RUN_DIRECTORY
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1L) stop("Supply one archived run directory")
run <- normalizePath(args[1], winslash = "/", mustWork = TRUE)
if (!requireNamespace("Matrix", quietly = TRUE)) stop("Matrix is required to read the frozen feature dimensions")
v <- readRDS(file.path(run, "audit/analytics/artifacts/M07.rds"))
stopifnot(identical(v$schema, "D1-HC-result-v1"), identical(v$publication_eligible, FALSE))
n <- v$numerical; p <- v$policy
cnd <- n$candidates[n$candidates$selected_primary, , drop = FALSE]
cs <- n$cluster_stability[n$cluster_stability$candidate_id == n$selected_id, , drop = FALSE]
out <- file.path(run, "audit/figures/Figure_6_Hierarchical_Clustering_Audit.png")
dir.create(dirname(out), recursive = TRUE, showWarnings = FALSE)
tmp <- tempfile(fileext = ".png")
grDevices::png(tmp, width = 1120, height = 960, res = 110,
  type = if (capabilities("cairo")) "cairo" else getOption("bitmapType"))
layout(matrix(c(1, 1, 2, 3), 2, 2, byrow = TRUE), heights = c(1.65, 1))
par(oma = c(4.5, 0.3, 4.5, 0.7), family = "sans", fg = "#202B38", bg = "white")
par(mar = c(4.7, 4.6, 1.3, 1.5), mgp = c(2.5, .7, 0), tcl = -.2, las = 1)
plot(n$trees[[p$primary_linkage]], hang = -1, main = "", sub = "", xlab = "",
     ylab = "Merge dissimilarity (average linkage)", ylim = c(0, max(n$trees[[p$primary_linkage]]$height)*1.08), cex = .8, col = "#002D74")
rect.hclust(n$trees[[p$primary_linkage]], k = n$selected_k, border = "#9CB5C6")
mtext(sprintf("%d countries | %d frozen terms | audit cut k = %d | mean silhouette %.3f",
  nrow(n$distance), ncol(readRDS(file.path(run, "audit/analytics/artifacts/M02.rds"))$current$country$x),
  n$selected_k, cnd$mean_silhouette), side = 3, line = -.2, adj = 0, cex = .83, col = "#526171")
par(mar = c(4.3, 4.6, 2.8, 1.7), mgp = c(2.5, .7, 0), tcl = -.2)
cols <- c(average = "#002D74", complete = "#597BA5", ward.D2 = "#8B6A49")
styles <- c(average = 1, complete = 2, ward.D2 = 3)
r <- range(c(n$candidates$mean_silhouette, p$min_mean_silhouette, 0))
plot(NA, xlim = range(n$candidates$k), ylim = r + c(-.02, .06),
  xlab = "Number of clusters (k)", ylab = "Mean silhouette", bty = "l", xaxt = "n")
axis(1, at = sort(unique(n$candidates$k)))
abline(h = p$min_mean_silhouette, lty = 3, col = "#B2BAC2")
for (method in names(cols)) {
  z <- n$candidates[n$candidates$linkage == method, ]
  lines(z$k, z$mean_silhouette, type = "b", pch = if (method == "average") 16 else 1,
        lty = styles[method], lwd = 1.4, col = cols[method])
}
points(n$selected_k, cnd$mean_silhouette, pch = 21, bg = "#002D74", col = "white", cex = 1.4)
title(main = "Linkage / cut sensitivity", adj = 0, cex.main = 1.05, col.main = "#062135")
legend("topright", legend = c("Average", "Complete", "Ward.D2"), col = cols, lty = styles,
       lwd = 1.3, bty = "n", cex = .78)
par(mar = c(4.3, 4.5, 2.8, 4.5), mgp = c(2.5, .7, 0), tcl = -.2)
y <- rev(seq_len(nrow(cs)))
plot(NA, xlim = c(0, 1.02), ylim = c(.5, max(y) + .5), yaxt = "n", bty = "l",
  xlab = "Mean subset Jaccard", ylab = "")
axis(2, at = y, labels = paste0("C", cs$cluster, " (n=", cs$size, ")"), las = 1)
abline(v = p$min_cluster_mean_jaccard, lty = 3, col = "#9EAAB6")
segments(0, y, cs$mean_jaccard, y, col = "#CAD8E4", lwd = 3)
points(cs$mean_jaccard, y, pch = 16, cex = 1.2, col = "#002D74")
if (anyNA(cs$mean_jaccard)) text(.3, y[is.na(cs$mean_jaccard)], "not evaluable", cex=.78, col="#667085")
text(1.03, y, labels = sprintf("%d/%d", cs$evaluable, cs$planned), pos = 4, xpd = NA, cex = .77, col = "#526171")
title(main = "Roster-deletion stability", adj = 0, cex.main = 1.05, col.main = "#062135")
mtext("Evaluable", side = 3, line = .4, adj = 1.16, cex = .72, col = "#526171")
mtext("Hierarchical clustering | frozen TF-IDF", side = 3, outer = TRUE, line = 2.5,
      adj = .035, font = 2, cex = 1.35, col = "#062135")
mtext("AUDIT ONLY - descriptive lexical structure, not political alignment", side = 3,
      outer = TRUE, line = 1, adj = .035, cex = .87, col = "#8B5A32")
mtext(sprintf("%d subsets retaining %d%% of countries. Fixed vocabulary, IDF and k within each candidate; no confidence intervals.",
  p$replicates, 100 * p$subsample_fraction), side = 1, outer = TRUE, line = 1.2, adj = .035, cex = .8, col = "#526171")
mtext("Dashed thresholds are predeclared engineering screens, not empirical validity. All failed and unevaluable replicates are archived.",
  side = 1, outer = TRUE, line = 2.5, adj = .035, cex = .77, col = "#526171")
mtext(if (n$selection_size_admissible) "Cluster-size screen passed; this remains an unreleased audit result." else "No average-linkage cut passed the size screen. The displayed cut is exploratory only.",
  side = 1, outer = TRUE, line = 3.7, adj = .035, cex = .77, col = "#8B5A32")
grDevices::dev.off()
bytes <- readBin(tmp, "raw", n = file.info(tmp)$size)
if (file.exists(out)) {
  if (!identical(bytes, readBin(out, "raw", n = file.info(out)$size))) stop("Existing audit figure differs; do not overwrite a frozen image")
} else if (!file.copy(tmp, out)) stop("Could not commit hierarchy image")
unlink(tmp)
cat("Executed successfully: hierarchical audit PNG; no inline email image added.\n")
