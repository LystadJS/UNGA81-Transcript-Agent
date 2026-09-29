a<-commandArgs(FALSE);self<-sub('^--file=','',a[grepl('^--file=',a)][1]);root<-normalizePath(dirname(self),winslash='/',mustWork=TRUE)
lib<-file.path(root,'library');dir.create(lib,showWarnings=FALSE);.libPaths(c(lib,.libPaths()))
p<-c('digest','glmnet','uwot','dbscan','ranger','isotree','changepoint','clue')
missing<-p[!vapply(p,requireNamespace,logical(1),quietly=TRUE)]
if(length(missing))install.packages(missing,lib=lib,repos='https://cloud.r-project.org')
stopifnot(all(vapply(p,requireNamespace,logical(1),quietly=TRUE)))
cat('Research dependencies available in an isolated project library.\n')
