#!/usr/bin/env Rscript
if (!l10n_info()[["UTF-8"]]) { invisible(try(Sys.setlocale("LC_CTYPE", if (.Platform$OS.type == "windows") "English_United States.utf8" else "C.UTF-8"), silent=TRUE)) }
# Standalone base-R figure. Input: run directory with data/*.csv. No packages.
args <- commandArgs(trailingOnly=TRUE)
if (length(args)!=1) stop("Usage: Rscript Figure_1_Issue_Frequency.R RUN_DIRECTORY")
root <- normalizePath(args[1],mustWork=TRUE)
d <- read.csv(file.path(root,"data/country_issue_long.csv"),check.names=FALSE,fileEncoding="UTF-8",na.strings="")
meta <- read.csv(file.path(root,"data/countries.csv"),check.names=FALSE,fileEncoding="UTF-8")
issues <- read.csv(file.path(root,"data/issues.csv"),check.names=FALSE,fileEncoding="UTF-8")
stopifnot(!anyDuplicated(paste(d$iso3,d$issue_id)),nrow(d)==nrow(meta)*nrow(issues),all(is.na(d$code)|d$code %in% c(0,1)))
N <- nrow(meta)
out <- data.frame(issue_id=issues$issue_id,issue=issues$label,fixed=issues$fixed,fixed_order=issues$fixed_order,coding_version=issues$version,n_present=0L,n_absent=0L,n_unknown=0L,n_countries=N,share=NA_real_)
for(i in seq_len(nrow(out))) {
  x <- d$code[d$issue_id==out$issue_id[i]]
  out$n_present[i] <- sum(x==1,na.rm=TRUE);out$n_absent[i] <- sum(x==0,na.rm=TRUE);out$n_unknown[i] <- sum(is.na(x))
  if(N>0) out$share[i] <- out$n_present[i]/N
}
out <- out[order(!out$fixed,ifelse(out$fixed,out$fixed_order,0),-out$n_present,out$issue,method="radix"),]
context<-read.csv(file.path(root,"data/plot_context.csv"),fileEncoding="UTF-8",stringsAsFactors=FALSE)$note[1]
dir.create(file.path(root,"figures"),showWarnings=FALSE)
write.csv(out,file.path(root,"data/issue_frequency.csv"),row.names=FALSE,na="",fileEncoding="UTF-8")
png(file.path(root,"figures/Figure_1_Issue_Frequency.png"),width=840,height=max(570,242+34*nrow(out)),res=96,pointsize=12,bg="white")
par(mar=c(7.2,17.4,3.2,1.7),family="sans",xaxs="i",yaxs="i",fg="#263746",col.axis="#52606D",col.lab="#263746")
y <- rev(seq_len(nrow(out)))
plot.new();plot.window(xlim=c(0,max(1,N)*1.32),ylim=c(.25,nrow(out)+.75))
for(x in pretty(c(0,max(1,N)),n=5)) if(x>=0 && x<=max(1,N)) abline(v=x,col="#E7EDF2",lwd=.8)
rect(0,y-.28,out$n_present,y+.28,col=ifelse(out$fixed,"#16466D","#527A99"),border=NA)
if(any(out$fixed)&&any(!out$fixed))abline(h=nrow(out)-sum(out$fixed)+.5,col="#A7BCCB",lty=2,lwd=.8)
axis(1,at=pretty(c(0,max(1,N)),5),lwd=0,lwd.ticks=.6,cex.axis=.88)
axis(2,at=y,labels=out$issue,las=1,tick=FALSE,cex.axis=.86,col.axis="#263746")
labels <- if(N) sprintf("%d/%d  (%d%%)",out$n_present,N,round(100*out$share)) else rep("No data",nrow(out))
labels<-paste0(labels,ifelse(out$n_unknown>0," *",""))
text(pmax(out$n_present,0)+max(1,N)*.018,y,labels,pos=4,cex=.82,xpd=NA,col="#263746",font=2)
mtext("Countries addressing each issue",side=3,adj=0,line=1.5,font=2,cex=1.1,col="#062135")
mtext("Number of countries in this day's retrieved corpus",side=1,line=2.6,cex=.88)
if(any(out$n_unknown>0)) { mtext(sprintf("* = unresolved (%d decisions); observed presence is not confirmed absence elsewhere.",sum(out$n_unknown)),side=1,line=3.55,cex=.65,col="#667085")
} else { mtext("Non-exclusive categories. Presence does not indicate agreement or support.",side=1,line=3.55,cex=.72,col="#667085") }
mtext("Fixed topics first: Iran, Cuba, Ukraine, AI. Additional topics ranked by frequency.",side=1,line=4.55,cex=.65,col="#667085")
mtext(context,side=1,line=5.6,cex=.60,col="#667085")
invisible(dev.off())
cat("Frequency figure executed successfully:",N,"countries;",nrow(out),"issues\n")
