#!/usr/bin/env Rscript
# Standalone base-R figure; input is one source-bound coordinate CSV.
# Usage: Rscript R/Figure_4_Country_Discourse_Map.R RUN_DIRECTORY
args<-commandArgs(trailingOnly=TRUE)
if(length(args)!=1L)stop("Supply a completed run directory")
run<-normalizePath(args[1],winslash="/",mustWork=TRUE)
d<-read.csv(file.path(run,"data/pca_country_coordinates.csv"),stringsAsFactors=FALSE,fileEncoding="UTF-8")
required<-c("iso3","country","region","date","axis1","axis2","axis1_fraction","axis2_fraction","display_state","mode","projection")
stopifnot(all(required%in%names(d)),!anyDuplicated(d$iso3))
d<-d[is.finite(d$axis1)&is.finite(d$axis2),,drop=FALSE]
if(nrow(d)<3L)stop("Insufficient finite coordinates for an audit plot")
outdir<-file.path(run,"audit/figures");dir.create(outdir,recursive=TRUE,showWarnings=FALSE)
file<-file.path(outdir,"Figure_4_Country_Discourse_Map.png")
tmp<-tempfile(fileext=".png")
palette<-c("Africa"="#287D8E","Asia-Pacific"="#597BA5","Europe & Eurasia"="#002D74","Near East"="#8B6A49","Western Hemisphere"="#80689D","Unmapped"="#707B86")
shapes<-c("Africa"=16,"Asia-Pacific"=17,"Europe & Eurasia"=15,"Near East"=18,"Western Hemisphere"=8,"Unmapped"=3)
d$region[!d$region%in%names(palette)]<-"Unmapped"
audit<-!all(d$display_state=="eligible_primary")||"pca"=="pcoa"
grDevices::png(tmp,width=840,height=720,res=110,type=if(capabilities("cairo"))"cairo" else getOption("bitmapType"))
par(oma=c(1.8,0,0,0),mar=c(6.3,4.8,4.8,1.3),mgp=c(2.6,.6,0),tcl=-.2,las=1,family="sans",bg="white",fg="#202B38",col.axis="#526171",cex.axis=.87)
rx<-range(d$axis1);ry<-range(d$axis2)
sx<-max(diff(rx),.01);sy<-max(diff(ry),.01)
xlim<-rx+c(-.23,.23)*sx;ylim<-ry+c(-.22,.22)*sy
plot(d$axis1,d$axis2,type="n",asp=1,xlim=xlim,ylim=ylim,bty="n",xlab=sprintf("PC1 (%.1f%% reference variation)",100*d$axis1_fraction[1]),ylab=sprintf("PC2 (%.1f%%)",100*d$axis2_fraction[1]),cex.lab=.95)
abline(h=axTicks(2),v=axTicks(1),col="#EDF1F4",lwd=.65)
abline(h=0,v=0,col="#CCD5DF",lty=3,lwd=.8)
title(main="Country discourse map - PCA",adj=0,col.main="#062135",cex.main=1.16,line=2.75)
mtext(sprintf("%d available country texts | %s | two-dimensional lexical projection",nrow(d),d$date[1]),side=3,line=1.25,adj=0,cex=.81,col="#526171")
mtext(if(audit)"AUDIT ONLY - not approved for the email" else "DESCRIPTIVE DISPLAY - not political alignment or stance",side=3,line=.15,adj=0,cex=.81,col=if(audit)"#8B5A32" else "#002D74")
# Deterministic label placement in device coordinates. Coordinates never move.
usr<-par("usr");padx<-strwidth(" ",cex=.74);pady<-strheight("M",cex=.74)*.2
w<-strwidth(d$iso3,cex=.75)+padx;h<-strheight(d$iso3,cex=.75)+pady
boxes<-matrix(numeric(),0,4);placed<-matrix(NA_real_,nrow(d),2)
inside<-function(b)b[1]>usr[1]&&b[2]<usr[2]&&b[3]>usr[3]&&b[4]<usr[4]
collides<-function(b)if(!nrow(boxes))FALSE else any(b[1]<boxes[,2]&b[2]>boxes[,1]&b[3]<boxes[,4]&b[4]>boxes[,3])
angles<-c(pi/4,3*pi/4,-pi/4,-3*pi/4,0,pi,pi/2,-pi/2)
for(i in order(d$iso3,method="radix")) {
  found<-FALSE
  for(mult in c(1,1.7,2.5,3.5,5,7,9)) {
    for(a in angles) {
      x<-d$axis1[i]+cos(a)*w[i]*mult;y<-d$axis2[i]+sin(a)*h[i]*mult
      box<-c(x-w[i]/2,x+w[i]/2,y-h[i]/2,y+h[i]/2)
      covers_point<-any(d$axis1>box[1]&d$axis1<box[2]&d$axis2>box[3]&d$axis2<box[4])
      if(inside(box)&&!collides(box)&&!covers_point){found<-TRUE;break}
    }
    if(found)break
  }
  if(found){placed[i,]<-c(x,y);boxes<-rbind(boxes,box)}
}
good<-complete.cases(placed)
segments(d$axis1[good],d$axis2[good],placed[good,1],placed[good,2],col="#B8C3CF",lwd=.55)
points(d$axis1,d$axis2,pch=unname(shapes[d$region]),col=unname(palette[d$region]),cex=1.05)
text(placed[good,1],placed[good,2],labels=d$iso3[good],cex=.75,col="#202B38")
regions<-names(palette)[names(palette)%in%unique(d$region)]
legend("bottom",legend=regions,col=unname(palette[regions]),pch=unname(shapes[regions]),bty="n",ncol=3,cex=.8,inset=c(0,-.31),xpd=NA,y.intersp=1.15)
mtext("Countries are observations, not inferred coalitions. No confidence regions or movement arrows are shown.",side=1,line=.2,outer=TRUE,adj=.5,cex=.66,col="#667085")
grDevices::dev.off()
bytes<-readBin(tmp,"raw",n=file.info(tmp)$size)
if(file.exists(file)){old<-readBin(file,"raw",n=file.info(file)$size);if(!identical(bytes,old))stop("Existing frozen audit image differs; preserve its original render environment")} else {if(!file.copy(tmp,file))stop("Could not commit figure")}
unlink(tmp)
layout<-data.frame(iso3=d$iso3,label_x=placed[,1],label_y=placed[,2],label_placed=good)
write.csv(layout,file.path(run,"data/pca_label_layout.csv"),row.names=FALSE,fileEncoding="UTF-8")
cat(sprintf("Executed successfully: PCA PNG, %d/%d labels placed without label-box overlap.\n",sum(good),nrow(d)))
if(!all(good))quit(status=2L)
