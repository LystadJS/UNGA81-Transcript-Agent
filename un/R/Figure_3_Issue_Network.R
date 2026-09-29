#!/usr/bin/env Rscript
if (!l10n_info()[["UTF-8"]]) { invisible(try(Sys.setlocale("LC_CTYPE", if (.Platform$OS.type == "windows") "English_United States.utf8" else "C.UTF-8"), silent=TRUE)) }
# Standalone base-R co-occurrence network; fixed coordinates enable stable day-to-day layout.
args <- commandArgs(trailingOnly=TRUE);if(length(args)!=1) stop("Usage: Rscript Figure_3_Issue_Network.R RUN_DIRECTORY")
root <- normalizePath(args[1],mustWork=TRUE)
d <- read.csv(file.path(root,"data/country_issue_long.csv"),check.names=FALSE,fileEncoding="UTF-8",na.strings="")
meta <- read.csv(file.path(root,"data/countries.csv"),check.names=FALSE,fileEncoding="UTF-8")
issues <- read.csv(file.path(root,"data/issues.csv"),check.names=FALSE,fileEncoding="UTF-8")
settings <- read.csv(file.path(root,"data/plot_settings.csv"),stringsAsFactors=FALSE)
get_setting <- function(k,default) {v<-settings$value[settings$key==k];if(length(v))as.numeric(v) else default}
max_edges <- get_setting("network_max_edges",14);min_j <- get_setting("network_min_jaccard",.35);min_n <- get_setting("network_min_copresent",2)
stopifnot(!anyDuplicated(paste(d$iso3,d$issue_id)),nrow(d)==nrow(meta)*nrow(issues))
ids <- issues$issue_id;M <- matrix(NA_real_,nrow=nrow(meta),ncol=length(ids),dimnames=list(meta$iso3,ids))
if(nrow(d)) for(i in seq_len(nrow(d))) M[d$iso3[i],d$issue_id[i]] <- d$code[i]
pairs <- combn(seq_along(ids),2);rows <- list()
for(k in seq_len(ncol(pairs))) {
  i<-pairs[1,k];j<-pairs[2,k];valid<-!is.na(M[,i])&!is.na(M[,j]);a<-M[valid,i];b<-M[valid,j]
  both<-sum(a==1&b==1);either<-sum(a==1|b==1)
  rows[[k]]<-data.frame(from=ids[i],to=ids[j],n_copresent=both,n_union=either,n_pair_observed=sum(valid),pair_complete=all(valid)&&nrow(meta)>0,jaccard=if(either&&all(valid)&&nrow(meta)>0)both/either else NA_real_)
}
all_edges<-do.call(rbind,rows);all_edges$selected<-FALSE;all_edges$selection_reason<-"not_selected"
cand<-which(!is.na(all_edges$jaccard)&all_edges$jaccard>=min_j&all_edges$n_copresent>=min_n)
cand<-cand[order(-all_edges$jaccard[cand],-all_edges$n_copresent[cand],all_edges$from[cand],all_edges$to[cand])]
# Maximum-spanning forest restricted to eligible positive edges; never invent connectivity.
group<-setNames(seq_along(ids),ids);chosen<-integer()
for(k in cand) {a<-all_edges$from[k];b<-all_edges$to[k];if(group[a]!=group[b]){chosen<-c(chosen,k);old<-group[b];group[group==old]<-group[a];all_edges$selection_reason[k]<-"eligible_backbone"}}
for(k in cand) if(length(chosen)<max_edges && !k %in% chosen){chosen<-c(chosen,k);all_edges$selection_reason[k]<-"additional_high_overlap"}
# If a user chooses fewer links than forest edges, preserve only the strongest within the cap.
chosen<-head(chosen,max_edges);all_edges$selected[chosen]<-TRUE
all_edges$selection_reason[!all_edges$selected]<-ifelse(all_edges$pair_complete[!all_edges$selected],"not_selected","unresolved_pair_excluded")
write.csv(all_edges,file.path(root,"data/issue_cooccurrence_all.csv"),row.names=FALSE,na="")
write.csv(all_edges[chosen,],file.path(root,"data/issue_network_edges.csv"),row.names=FALSE,na="")
angle<-pi/2 - 2*pi*(seq_along(ids)-1)/length(ids)
nodes<-data.frame(issue_id=ids,label=issues$label,short_label=issues$short_label,fixed=issues$fixed,n_unknown=colSums(is.na(M)),n_present=colSums(M==1,na.rm=TRUE),x=.79*cos(angle),y=.79*sin(angle),label_x=1.16*cos(angle),label_y=1.16*sin(angle))
write.csv(nodes,file.path(root,"data/issue_network_nodes.csv"),row.names=FALSE,fileEncoding="UTF-8")
context<-read.csv(file.path(root,"data/plot_context.csv"),fileEncoding="UTF-8",stringsAsFactors=FALSE)$note[1]
dir.create(file.path(root,"figures"),showWarnings=FALSE)
png(file.path(root,"figures/Figure_3_Issue_Cooccurrence_Network.png"),width=840,height=795,res=96,pointsize=12,bg="white")
par(mar=c(7.2,1,3.5,1),family="sans",xaxs="i",yaxs="i")
plot.new();plot.window(xlim=c(-1.6,1.6),ylim=c(-1.45,1.45),asp=1)
for(k in chosen) {
 e<-all_edges[k,];a<-nodes[match(e$from,nodes$issue_id),];b<-nodes[match(e$to,nodes$issue_id),]
 segments(a$x,a$y,b$x,b$y,lwd=1+4*e$jaccard,col=adjustcolor("#52758F",alpha.f=.27+.22*e$jaccard))
}
for(i in seq_len(nrow(nodes))) {
 radius<-.13*sqrt(nodes$n_present[i]/max(1,max(nodes$n_present)))
 if(radius==0)radius<-.018
 theta<-seq(0,2*pi,length.out=80)
 polygon(nodes$x[i]+radius*cos(theta),nodes$y[i]+radius*sin(theta),col=if(nodes$n_present[i]){if(nodes$fixed[i])"#16466D" else "#527A99"} else "#E4E9EE",border="white",lwd=2)
 label<-paste0(nodes$short_label[i],"\n",nodes$n_present[i],if(nodes$n_unknown[i]>0)" *" else "")
 text(nodes$label_x[i],nodes$label_y[i],label,cex=.79,col="#18364D",font=2)
}
mtext("Issues discussed in the same national statements",side=3,line=1.5,adj=.02,font=2,cex=1.1,col="#062135")
mtext(sprintf("Node area: countries mentioning issue  |  %d displayed links: Jaccard overlap",length(chosen)),side=1,line=1.2,cex=.82,col="#52606D")
mtext(sprintf("Links: fully coded pairs only, overlap >= %.2f and >= %d co-present countries.",min_j,min_n),side=1,line=2.6,cex=.7,col="#667085")
mtext("* = unresolved decisions. Gray minimum-size marker = zero observed presence; not proven absence.",side=1,line=3.8,cex=.75,col="#667085")
mtext(context,side=1,line=5.05,cex=.60,col="#667085")
mtext("Co-occurrence is not agreement or causation; broad and narrow categories can overlap.",side=1,line=6.05,cex=.64,col="#667085")
invisible(dev.off());cat("Issue network executed successfully:",nrow(nodes),"nodes;",length(chosen),"selected links\n")
