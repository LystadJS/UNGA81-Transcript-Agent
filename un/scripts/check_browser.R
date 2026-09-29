#!/usr/bin/env Rscript
# Optional native-R browser QA. Requires chromote + a local Chrome/Edge/Chromium browser.
args<-commandArgs(trailingOnly=TRUE);if(length(args)!=1)stop("Usage: Rscript scripts/check_browser.R OUTPUT_RUN_DIRECTORY")
self<-sub("^--file=","",commandArgs()[grepl("^--file=",commandArgs())][1]);root<-normalizePath(file.path(dirname(self),".."),winslash="/",mustWork=TRUE)
source(file.path(root,"R/00_core.R"));if(file.exists(file.path(root,"config/library_path.txt"))){lib<-readLines(file.path(root,"config/library_path.txt"),warn=FALSE)[1];if(dir.exists(lib)).libPaths(c(lib,.libPaths()))}
need_packages(c("chromote","jsonlite","base64enc"));run<-normalizePath(args[1],winslash="/",mustWork=TRUE)
html<-read_text(file.path(run,"daily_briefing_preview.html"));expected<-json_read(file.path(run,"brief.json"))$country_count
main<-function(){
  b<-chromote::ChromoteSession$new();on.exit(b$parent$close(),add=TRUE)
  out<-file.path(run,"render_checks");dir.create(out,showWarnings=FALSE);metrics<-list()
  b$Page$enable();b$Runtime$enable()
  for(width in c(390,720,1280,1600)) {
    b$Emulation$setDeviceMetricsOverride(width=width,height=1050,deviceScaleFactor=1,mobile=FALSE)
    tree<-b$Page$getFrameTree();b$Page$setDocumentContent(frameId=tree$frameTree$frame$id,html=html)
    b$Runtime$evaluate(expression="document.fonts.ready.then(()=>Promise.all([...document.images].map(x=>x.decode().catch(()=>{}))))",awaitPromise=TRUE,returnByValue=TRUE)
    expression<-"JSON.stringify({viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,fixed:[...document.querySelectorAll('.fixed-watchlist .fixed-topic')].map(x=>x.textContent),slots:[...document.querySelectorAll('.analytics-slot')].map(x=>x.id),regions:document.querySelectorAll('.region-title').length,countries:document.querySelectorAll('.country-title').length,images:[...document.images].map(x=>({ok:x.complete&&x.naturalWidth>0,width:x.getBoundingClientRect().width})),overflow:[...document.querySelectorAll('table,div,img')].filter(x=>x.getBoundingClientRect().right>innerWidth+1).length})"
    result<-b$Runtime$evaluate(expression=expression,returnByValue=TRUE);q<-jsonlite::fromJSON(result$result$value,simplifyVector=FALSE)
    assert(identical(unlist(q$fixed,use.names=FALSE),c("Iran","Cuba","Ukraine","AI")),"Fixed-topic order mismatch")
    assert(identical(unlist(q$slots,use.names=FALSE),paste0("analytics-O",1:5)),"Five-output section mismatch")
    assert(length(q$images)==1L,"I1 must embed only the seal, not audit figures")
    assert(q$viewport==width&&q$scrollWidth<=width+1&&q$countries==expected&&q$overflow==0&&all(vapply(q$images,function(x)x$ok,logical(1))),"Browser layout check failed")
    shot<-b$Page$captureScreenshot(format="png",captureBeyondViewport=FALSE);atomic_bytes(file.path(out,paste0("width_",width,".png")),base64enc::base64decode(shot$data));metrics<-c(metrics,list(q))
  }
  json_write(file.path(out,"metrics.json"),list(passed=TRUE,viewports=metrics,browser=b$Browser$getVersion(),native_outlook="not tested"));cat("Browser checks passed at four widths. Native Outlook remains a separate check.\n")
}
main()
