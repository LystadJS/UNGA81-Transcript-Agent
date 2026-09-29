#!/usr/bin/env Rscript
if (!l10n_info()[["UTF-8"]]) { invisible(try(Sys.setlocale("LC_CTYPE", if (.Platform$OS.type == "windows") "English_United States.utf8" else "C.UTF-8"), silent=TRUE)) }
# Standalone base-R regional prevalence heatmap. Regions are columns for legibility.
args <- commandArgs(trailingOnly=TRUE);if(length(args)!=1) stop("Usage: Rscript Figure_2_Regional_Heatmap.R RUN_DIRECTORY")
root <- normalizePath(args[1],mustWork=TRUE)
d <- read.csv(file.path(root,"data/country_issue_long.csv"),check.names=FALSE,fileEncoding="UTF-8",na.strings="")
meta <- read.csv(file.path(root,"data/countries.csv"),fileEncoding="UTF-8",check.names=FALSE)
issues <- read.csv(file.path(root,"data/issues.csv"),fileEncoding="UTF-8",check.names=FALSE)
stopifnot(nrow(d)==nrow(meta)*nrow(issues),!anyDuplicated(paste(d$iso3,d$issue_id)))
regions <- read.csv(file.path(root,"data/region_order.csv"),fileEncoding="UTF-8",stringsAsFactors=FALSE)$region
stopifnot(setequal(regions,unique(meta$region)),!anyDuplicated(regions))
if(!length(regions)) regions <- "No countries"
freq <- vapply(issues$issue_id,function(id)sum(d$code[d$issue_id==id]==1,na.rm=TRUE),numeric(1))
issues <- issues[order(!issues$fixed,ifelse(issues$fixed,issues$fixed_order,0),-freq,issues$label,method="radix"),]
out <- list()
for(r in regions) for(i in seq_len(nrow(issues))) {
  x <- d$code[d$region==r & d$issue_id==issues$issue_id[i]];N <- sum(meta$region==r)
  out[[length(out)+1L]] <- data.frame(region=r,issue_id=issues$issue_id[i],issue=issues$label[i],n_present=sum(x==1,na.rm=TRUE),n_countries=N,n_unknown=sum(is.na(x)),share=if(N)sum(x==1,na.rm=TRUE)/N else NA_real_)
}
out <- do.call(rbind,out);write.csv(out,file.path(root,"data/regional_issue_matrix.csv"),row.names=FALSE,na="",fileEncoding="UTF-8")
context<-read.csv(file.path(root,"data/plot_context.csv"),fileEncoding="UTF-8",stringsAsFactors=FALSE)$note[1]
dir.create(file.path(root,"figures"),showWarnings=FALSE)
png(file.path(root,"figures/Figure_2_Regional_Issue_Heatmap.png"),width=840,height=max(600,242+36*nrow(issues)),res=96,pointsize=12,bg="white")
par(mar=c(6.9,17.4,5.8,1.1),family="sans",xaxs="i",yaxs="i")
plot.new();plot.window(xlim=c(.5,length(regions)+.5),ylim=c(.5,nrow(issues)+.5))
pal <- colorRampPalette(c("#F2F6F9","#C4DDEE","#6BADD2","#24678F","#062F54"))(101)
for(k in seq_len(nrow(out))) {
  row <- out[k,];x <- match(row$region,regions);y <- nrow(issues)+1-match(row$issue_id,issues$issue_id);v <- row$share
  fill <- if(is.na(v))"#EEEEEE" else pal[1+round(v*100)]
  rect(x-.49,y-.49,x+.49,y+.49,col=fill,border="white",lwd=2)
  label <- if(is.na(v))"No data" else sprintf("%d%%\n%d/%d%s",round(v*100),row$n_present,row$n_countries,if(row$n_unknown>0)" *" else "")
  text(x,y,label,cex=.83,col=if(!is.na(v)&&v>=.58)"white" else "#18364D",font=if(!is.na(v)&&v>=.58)2 else 1)
}
if(any(issues$fixed)&&any(!issues$fixed))abline(h=nrow(issues)-sum(issues$fixed)+.5,col="#7E9EB5",lty=2,lwd=1)
axis(2,at=rev(seq_len(nrow(issues))),labels=issues$label,las=1,tick=FALSE,cex.axis=.84,col.axis="#263746")
lab <- c("Africa"="Africa","Europe & Eurasia"="Europe &\nEurasia","Western Hemisphere"="Western\nHemisphere","Asia-Pacific"="Asia-\nPacific","Near East"="Near\nEast","Unmapped"="Unmapped","No countries"="No\ncountries")
axis(3,at=seq_along(regions),labels=ifelse(is.na(unname(lab[regions])),regions,unname(lab[regions])),tick=FALSE,cex.axis=.85,line=.3,col.axis="#263746")
mtext("Issue presence within each regional sample",side=3,line=4.1,adj=0,font=2,cex=1.08,col="#062135")
mtext("Cells: share of countries, then count / regional sample size",side=1,line=.8,cex=.82,col="#52606D")
mtext("Small regional samples are descriptive, not representative. * = unresolved decisions.",side=1,line=2.05,cex=.71,col="#667085")
mtext("Color scale: 0% (pale) to 100% (navy).",side=1,line=3.5,cex=.72,col="#667085")
mtext(context,side=1,line=4.8,cex=.60,col="#667085")
invisible(dev.off());cat("Regional heatmap executed successfully:",nrow(out),"cells\n")
