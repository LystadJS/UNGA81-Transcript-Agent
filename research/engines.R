# I6 experimental computational kernels. Not loaded by the daily pipeline.
# These are engineering implementations, NOT released D1 adapters or validation claims.
i6_ids <- c('M03','M04','M10','M11','M12','M13','M15','M17','M21','M22','M23','M24','M25','M27','M37','M39','M40','M41')
i6_assert <- function(ok,msg) if(!isTRUE(ok))stop(msg,call.=FALSE)
i6_seed <- function(fun) {
  had<-exists('.Random.seed',.GlobalEnv,inherits=FALSE)
  if(had)old<-get('.Random.seed',.GlobalEnv)
  on.exit(if(had)assign('.Random.seed',old,.GlobalEnv) else if(exists('.Random.seed',.GlobalEnv,inherits=FALSE))rm('.Random.seed',envir=.GlobalEnv))
  set.seed(30092026L);fun()
}
i6_need <- function(p) i6_assert(requireNamespace(p,quietly=TRUE),paste('Missing research dependency:',p))
i6_matrix <- function(x,min_rows=2L) {
  i6_assert(is.matrix(x)&&is.numeric(x)&&all(is.finite(x))&&nrow(x)>=min_rows&&ncol(x)>0,'Finite numeric matrix required')
  i6_assert(length(x)<=2000000&&nrow(x)<=5000,'Research resource limit exceeded')
  i6_assert(!is.null(rownames(x))&&!anyNA(rownames(x))&&!anyDuplicated(rownames(x))&&all(nzchar(rownames(x))),'Unique row identifiers required')
  i6_assert(!is.null(colnames(x))&&!anyNA(colnames(x))&&!anyDuplicated(colnames(x))&&all(nzchar(colnames(x))),'Unique feature identifiers required')
  x
}
i6_unit <- function(x) {x<-i6_matrix(x);n<-sqrt(rowSums(x*x));i6_assert(all(n>1e-12),'Zero feature vector');x/n}
i6_binary <- function(y) i6_assert(is.numeric(y)&&all(y%in%c(0,1))&&length(unique(y))==2,'Both binary outcome classes required')
i6_logloss <- function(p,y) {p<-pmin(1-1e-8,pmax(1e-8,p));-mean(y*log(p)+(1-y)*log(1-p))}
i6_glm <- function(x,y,link='logit') {
  x<-cbind(intercept=1,x);i6_assert(qr(x)$rank==ncol(x)&&nrow(x)>10*ncol(x),'Full rank, adequately sized low-dimensional design required')
  f<-withCallingHandlers(stats::glm.fit(x,y,family=stats::binomial(link)),warning=function(w)stop(conditionMessage(w),call.=FALSE))
  i6_assert(isTRUE(f$converged)&&all(is.finite(f$coefficients))&&max(abs(f$coefficients))<20,'Unstable/separated fit')
  list(beta=f$coefficients,link=link,fit=f)
}
i6_split <- function(d,multiclass=FALSE) {
  ids<-countries<-hashes<-list()
  for(s in c('train','calibration','test')) {
    z<-d[[s]];x<-i6_matrix(z$x);i6_assert(length(z$y)==nrow(x),'Outcome length mismatch')
    i6_assert(length(z$time)==nrow(x)&&all(is.finite(z$time)),'Numeric UTC time per observation required')
    i6_assert(length(z$country)==nrow(x)&&!anyNA(z$country)&&all(nzchar(z$country))&&length(z$text_hash)==nrow(x)&&!anyNA(z$text_hash)&&all(nzchar(z$text_hash)),'Country and content grouping required')
    ids[[s]]<-rownames(x);countries[[s]]<-z$country;hashes[[s]]<-z$text_hash
    i6_assert(!anyNA(z$y),'Missing outcome cannot become a negative label')
    if(!multiclass)i6_binary(z$y)
  }
  for(a in c('train','calibration'))for(b in c('calibration','test'))if(a!=b) {
    i6_assert(!length(intersect(ids[[a]],ids[[b]]))&&!length(intersect(hashes[[a]],hashes[[b]]))&&!length(intersect(countries[[a]],countries[[b]])),'Country/text leakage across partitions')
  }
  i6_assert(max(d$train$time)<min(d$calibration$time)&&max(d$calibration$time)<min(d$test$time),'Temporal leakage')
  i6_assert(identical(colnames(d$train$x),colnames(d$calibration$x))&&identical(colnames(d$train$x),colnames(d$test$x)),'Feature order changed')
  invisible(TRUE)
}
i6_classifier <- function(id,d) {
  multi<-id=='M17';i6_split(d,multi);tr<-d$train;ca<-d$calibration;te<-d$test
  if(id%in%c('M15','M17'))i6_assert(is.character(d$representation_id)&&length(d$representation_id)==1&&nzchar(d$representation_id),'Pinned representation required')
  if(multi) {
    classes<-c('support','oppose','conditional','descriptive')
    i6_assert(nzchar(d$proposition_id)&&nzchar(d$target),'Named proposition/target required')
    i6_assert(all(vapply(list(tr,ca,te),function(z)setequal(unique(z$y),classes),logical(1))),'Four reviewed stance classes required; insufficient evidence must be excluded and retained as abstention separately')
    i6_need('glmnet');f<-glmnet::glmnet(tr$x,factor(tr$y,levels=classes),family='multinomial',alpha=.5,lambda=.05,standardize=TRUE)
    raw<-function(x){a<-predict(f,x,type='response',s=.05);a[,,1,drop=TRUE]}
    pc<-raw(ca$x);pt<-raw(te$x);truth<-match(ca$y,colnames(pc))
    soften<-function(p,t){z<-log(pmax(p,1e-12))/t;z<-exp(z-apply(z,1,max));z/rowSums(z)}
    temp<-optimize(function(t)-mean(log(pmax(soften(pc,t)[cbind(seq_along(truth),truth)],1e-12))),c(.25,4))$minimum
    p<-soften(pt,temp);choice<-colnames(p)[max.col(p,ties.method='first')];choice[apply(p,1,max)<.6]<-'abstain'
    return(list(scores=p,predicted=choice,temperature=temp,coverage=mean(choice!='abstain'),test_logloss=-mean(log(pmax(p[cbind(seq_along(te$y),match(te$y,colnames(p)))],1e-12))),classes=colnames(p),model=f,proposition_id=d$proposition_id,target=d$target))
  }
  if(id%in%c('M11','M37')) {
    f<-i6_glm(tr$x,tr$y);raw<-function(x)plogis(cbind(1,x)%*%f$beta)
  } else if(id=='M14') {
    i7_backend('gbm');f<-gbm::gbm.fit(x=as.data.frame(tr$x),y=tr$y,distribution='bernoulli',n.trees=150,interaction.depth=2,n.minobsinnode=10,shrinkage=.03,bag.fraction=1,verbose=FALSE)
    raw<-function(x)as.numeric(predict(f,newdata=as.data.frame(x),n.trees=150,type='response'))
  } else if(id=='M13') {
    i6_need('ranger');f<-ranger::ranger(x=as.data.frame(tr$x),y=factor(tr$y,levels=0:1),probability=TRUE,num.trees=200,min.node.size=5,num.threads=1,seed=30092026)
    raw<-function(x)predict(f,data=as.data.frame(x),num.threads=1)$predictions[,'1']
  } else {
    i6_need('glmnet');f<-glmnet::glmnet(tr$x,tr$y,family='binomial',alpha=.5,lambda=.05,standardize=TRUE)
    raw<-function(x)as.numeric(predict(f,x,type='response',s=.05))
  }
  pc<-as.numeric(raw(ca$x));pt<-as.numeric(raw(te$x));cal<-i6_glm(matrix(qlogis(pmin(1-1e-6,pmax(1e-6,pc))),ncol=1),ca$y)
  p<-plogis(cbind(1,qlogis(pmin(1-1e-6,pmax(1e-6,pt))))%*%cal$beta);p<-as.numeric(p)
  choice<-ifelse(p>=.7,'positive',ifelse(p<=.3,'negative','abstain'))
  list(scores=p,predicted=choice,coverage=mean(choice!='abstain'),test_brier=mean((p-te$y)^2),test_logloss=i6_logloss(p,te$y),baseline_logloss=i6_logloss(rep(mean(tr$y),length(te$y)),te$y),model=f,calibration=cal$beta,target=if(id=='M37')'conditional_on_next_comparable_observation' else 'one_issue_binary_head',policy=if(id=='M14')list(trees=150,depth=2,shrinkage=.03,min_node=10,bag_fraction=1,tuning='fixed policy; no test-based selection',positive=.7,negative=.3)else list(alpha=.5,lambda=.05,positive=.7,negative=.3))
}
i6_embedding <- function(d) {
  x<-i6_unit(d$passages);i6_assert(length(d$statement_id)==nrow(x)&&length(d$country)==nrow(x),'Passage metadata mismatch')
  i6_assert(is.character(d$model_sha256)&&grepl('^[a-f0-9]{64}$',d$model_sha256)&&nzchar(d$tokenizer_id),'Pinned local encoder/tokenizer identity required')
  pooled<-function(x,groups){ids<-sort(unique(groups));y<-t(vapply(ids,function(id)colMeans(x[groups==id,,drop=FALSE]),numeric(ncol(x))));rownames(y)<-ids;i6_unit(y)}
  sx<-pooled(x,d$statement_id);sc<-vapply(rownames(sx),function(id){z<-unique(d$country[d$statement_id==id]);i6_assert(length(z)==1,'Statement has multiple countries');z},character(1))
  list(statement=sx,country=pooled(sx,sc),model_sha256=d$model_sha256,tokenizer_id=d$tokenizer_id,scope='validated cached vectors and explicit pooling only; encoder inference is not implemented')
}
i6_history <- function(d) {
  a<-i6_unit(d$before);b<-i6_unit(d$after);i6_assert(identical(dimnames(a),dimnames(b)),'Matched country/feature identities required')
  i6_assert(identical(d$before_representation,d$after_representation)&&nzchar(d$before_representation),'Representation mismatch')
  for(k in c('country','genre','issue','language'))i6_assert(identical(d$before_meta[[k]],d$after_meta[[k]])&&length(d$before_meta[[k]])==nrow(a)&&all(nzchar(d$before_meta[[k]])),paste('Noncomparable',k))
  i6_assert(all(d$after_time>d$before_time)&&length(d$after_time)==nrow(a)&&length(d$before_time)==nrow(a),'No new comparable observation')
  data.frame(id=rownames(a),cosine_distance=pmax(0,pmin(2,1-rowSums(a*b))),chord_distance=sqrt(rowSums((a-b)^2)))
}
i6_procrustes <- function(d) {
  a<-i6_matrix(d$before);b<-i6_matrix(d$after);i6_assert(identical(dimnames(a),dimnames(b)),'Matched maps required')
  i6_assert(nzchar(d$representation)&&identical(d$representation,d$after_representation),'Compatible representation required')
  anchors<-match(d$anchors,rownames(a));i6_assert(!anyNA(anchors)&&!anyDuplicated(anchors)&&length(anchors)>ncol(a),'Independent anchors required')
  ac<-colMeans(a[anchors,,drop=FALSE]);bc<-colMeans(b[anchors,,drop=FALSE]);aa<-sweep(a[anchors,,drop=FALSE],2,ac);bb<-sweep(b[anchors,,drop=FALSE],2,bc)
  i6_assert(qr(aa)$rank==ncol(a)&&qr(bb)$rank==ncol(b),'Rank-deficient anchors')
  sv<-svd(crossprod(bb,aa));rotation<-sv$u%*%t(sv$v);aligned<-sweep(sweep(b,2,bc)%*%rotation,2,ac,'+')
  list(aligned=aligned,rotation=rotation,translation=ac-bc%*%rotation,scale_ratio=sqrt(sum(bb^2)/sum(aa^2)),scaling_applied=FALSE,anchor_rmse=sqrt(mean((aligned[anchors,,drop=FALSE]-a[anchors,,drop=FALSE])^2)),displacement=sqrt(rowSums((aligned-a)^2)))
}
i6_correspondence <- function(d) {
  i6_need('clue');a<-d$before;b<-d$after;i6_assert(!is.null(names(a))&&!is.null(names(b))&&!anyDuplicated(names(a))&&!anyDuplicated(names(b))&&!anyNA(a)&&!anyNA(b),'Named unique complete memberships required')
  shared<-intersect(names(a),names(b));i6_assert(length(shared)>=3,'Insufficient shared entities');a<-as.character(a[shared]);b<-as.character(b[shared]);ta<-sort(unique(a));tb<-sort(unique(b));overlap<-table(factor(a,ta),factor(b,tb));n<-max(nrow(overlap),ncol(overlap));padded<-matrix(0,n,n);padded[seq_along(ta),seq_along(tb)]<-overlap
  assignment<-as.integer(clue::solve_LSAP(padded,maximum=TRUE));matchb<-ifelse(assignment[seq_along(ta)]<=length(tb),tb[pmin(assignment[seq_along(ta)],length(tb))],NA_character_)
  zero<-vapply(seq_along(ta),function(i)assignment[i]>ncol(overlap)||overlap[i,assignment[i]]==0,logical(1));matchb[zero]<-NA_character_
  list(overlap=overlap,matched=data.frame(before=ta,after=matchb),splits=ta[rowSums(overlap>0)>1],merges=tb[colSums(overlap>0)>1],shared=shared,departed=setdiff(names(d$before),shared),arrived=setdiff(names(d$after),shared),note='Overlap records coverage and splits/merges; not political transitions')
}
i6_umap <- function(d) {
  i6_need('uwot');x<-i6_matrix(d$x,10);i6_assert(nzchar(d$representation_id),'Frozen basis required')
  f<-uwot::umap(x,n_neighbors=min(10,nrow(x)-1),n_components=2,n_threads=1,n_sgd_threads=1,ret_model=TRUE,n_epochs=100,init='pca',verbose=FALSE)
  coordinates<-f$embedding;path<-tempfile(fileext='.umap');on.exit(unlink(path))
  invisible(uwot::save_uwot(f,path,unload=TRUE));bytes<-readBin(path,'raw',n=file.info(path)$size)
  list(coordinates=coordinates,model_archive=bytes,feature_names=colnames(x),scope='nonlinear sensitivity only; no diplomatic distances')
}
i6_umap_transform <- function(value,x) {
  i6_need('uwot');x<-i6_matrix(x);i6_assert(identical(colnames(x),value$feature_names)&&is.raw(value$model_archive),'Saved feature basis/archive required')
  path<-tempfile(fileext='.umap');writeBin(value$model_archive,path);on.exit(unlink(path));model<-uwot::load_uwot(path);on.exit(uwot::unload_uwot(model),add=TRUE)
  i6_seed(function()uwot::umap_transform(x,model,n_threads=1,n_sgd_threads=1,verbose=FALSE))
}
i6_hazard <- function(d) {
  x<-i6_matrix(d$x);i6_binary(d$y);i6_assert(length(d$y)==nrow(x)&&length(d$start)==nrow(x)&&length(d$stop)==nrow(x)&&all(is.finite(d$start))&&all(is.finite(d$stop))&&all(d$start<d$stop),'Valid risk intervals required')
  i6_assert(length(d$exposure_available)==nrow(x)&&all(d$exposure_available<d$start),'Exposure must be known strictly before interval')
  i6_assert(length(d$country)==nrow(x)&&!anyNA(d$country)&&all(nzchar(d$country))&&length(d$censor_reason)==nrow(x)&&!anyNA(d$censor_reason)&&all(nzchar(d$censor_reason[d$y==0])),'Observation/censoring contract required')
  for(g in unique(d$country)) {
    ix<-which(d$country==g);ix<-ix[order(d$start[ix])];hits<-which(d$y[ix]==1)
    i6_assert(length(hits)<=1&&(!length(hits)||hits==length(ix)),'First-event risk continues after adoption')
    if(length(ix)>1)i6_assert(all(head(d$stop[ix],-1)<=tail(d$start[ix],-1)),'Overlapping risk intervals')
  }
  # Equal-duration intervals avoid silently omitting a duration offset.
  i6_assert(diff(range(d$stop-d$start))<1e-8,'Kernel requires equal-duration intervals')
  f<-i6_glm(x,d$y,'cloglog');list(coefficients=f$beta,fit=f$fit,interpretation='associational first-observed-event discrete hazard; not causal diffusion')
}
i6_sar <- function(d) {
  w<-i6_matrix(d$w);x<-i6_matrix(d$x);y<-d$y;n<-nrow(w)
  i6_assert(ncol(w)==n&&nrow(x)==n&&length(y)==n&&all(is.finite(y))&&all(w>=0)&&all(diag(w)==0)&&identical(rownames(w),colnames(w))&&identical(rownames(w),rownames(x)),'Aligned nonnegative preexisting graph required')
  i6_assert(d$network_available<d$outcome_time,'Contemporaneous network cannot be preexisting')
  sums<-rowSums(w);w[sums>0,]<-w[sums>0,,drop=FALSE]/sums[sums>0];x<-cbind(1,x);i6_assert(qr(x)$rank==ncol(x)&&n>ncol(x)+5,'Invalid SAR design')
  objective<-function(rho,details=FALSE){m<-diag(n)-rho*w;z<-as.numeric(m%*%y);fit<-lm.fit(x,z);variance<-sum(fit$residuals^2)/n;if(variance<=1e-12)return(Inf);loss<-n/2*log(variance)-as.numeric(determinant(m,logarithm=TRUE)$modulus);if(details)list(rho=rho,coefficients=fit$coefficients,variance=variance,objective=loss) else loss}
  fit<-optimize(objective,c(-.95,.95));i6_assert(is.finite(fit$objective)&&abs(fit$minimum)<.949,'Boundary/degenerate SAR fit');c(objective(fit$minimum,TRUE),list(interpretation='Gaussian network-lag association; not contagion or causation'))
}
i6_relational <- function(d) {
  x<-i6_matrix(d$x);i6_binary(d$chosen);i6_assert(length(d$chosen)==nrow(x)&&length(d$event)==nrow(x)&&length(d$sender)==nrow(x)&&length(d$receiver)==nrow(x),'Risk-set dimensions mismatch')
  i6_assert(length(d$covariate_available)==nrow(x)&&length(d$event_time)==nrow(x)&&all(is.finite(d$covariate_available))&&all(is.finite(d$event_time))&&all(d$sender!=d$receiver)&&all(d$covariate_available<d$event_time),'Invalid dyad or future information')
  i6_assert(!anyNA(d$event)&&all(nzchar(d$event))&&!anyNA(d$sender)&&!anyNA(d$receiver)&&all(nzchar(d$sender))&&all(nzchar(d$receiver)),'Event and actor identities required')
  groups<-split(seq_len(nrow(x)),d$event)
  for(ix in groups)i6_assert(length(ix)>=2&&sum(d$chosen[ix])==1&&length(unique(d$event_time[ix]))==1&&!anyDuplicated(paste(d$sender[ix],d$receiver[ix],sep=':')),'One observed directed event and unique eligible alternatives at one time per risk set required')
  logsum<-function(z){m<-max(z);m+log(sum(exp(z-m)))}
  loss<-function(beta)sum(vapply(groups,function(ix){z<-as.numeric(x[ix,,drop=FALSE]%*%beta);logsum(z)-sum(z*d$chosen[ix])},numeric(1)))
  f<-optim(rep(0,ncol(x)),loss,method='BFGS',hessian=TRUE,control=list(maxit=300,reltol=1e-9));ev<-eigen(f$hessian,symmetric=TRUE,only.values=TRUE)$values
  i6_assert(f$convergence==0&&all(is.finite(f$par))&&min(ev)>1e-6&&max(abs(f$par))<20,'Unidentified/separated relational-event fit')
  list(coefficients=setNames(f$par,colnames(x)),standard_errors=sqrt(diag(solve(f$hessian))),loglik=-f$value,scope='ordinal conditional-choice relational events; waiting times not modeled')
}
i6_compute <- function(id,d) {
  i6_assert(id%in%i6_ids,'Method kernel not implemented in I6; see catalog')
  i6_assert(identical(d$dataset_kind,'synthetic_engineering'),'I6 kernels currently accept explicitly synthetic engineering fixtures only; reviewed-data deployment requires integration and acceptance')
  value<-i6_seed(function(){
    if(id=='M03')return(i6_embedding(d))
    if(id=='M04'){x<-i6_unit(d$x);r<-i6_unit(d$references);i6_assert(ncol(x)==ncol(r)&&identical(colnames(x),colnames(r))&&nzchar(d$representation_id)&&identical(d$representation_id,d$reference_representation_id),'Same pinned embedding basis required');return(list(cosine=x%*%t(r),interpretation='prototype relevance scores, not probabilities'))}
    if(id%in%c('M11','M12','M13','M14','M15','M17','M37'))return(i6_classifier(id,d))
    if(id=='M10')return(i6_umap(d))
    if(id=='M21'){i6_need('dbscan');x<-i6_matrix(d$x,10);f<-dbscan::hdbscan(x,minPts=5);return(list(cluster=f$cluster,membership=f$membership_prob,outlier=f$outlier_scores,noise=which(f$cluster==0),stability=f$cluster_scores,scope='noise retained; membership is not political confidence'))}
    if(id=='M22')return(i6_history(d))
    if(id=='M23'){i6_need('isotree');x<-i6_matrix(d$train_x,20);y<-i6_matrix(d$score_x);i6_assert(identical(colnames(x),colnames(y))&&max(d$train_time)<min(d$score_time),'Frozen features and historical-only fit required');f<-isotree::isolation.forest(x,ntrees=100,sample_size=min(256,nrow(x)),ndim=1,nthreads=1,seed=30092026,missing_action='fail');return(list(score=predict(f,y),scope='unfamiliarity score only; no diplomatic significance claim'))}
    if(id=='M24'){i6_need('changepoint');y<-d$y;i6_assert(is.numeric(y)&&all(is.finite(y))&&length(y)>=20&&length(d$time)==length(y)&&all(diff(d$time)>0)&&identical(d$index,'observation'),'Ordered observation-index series required; never impute daily zeros');i6_assert(identical(d$dependence,'independent_gaussian'),'Only preregistered independent Gaussian mean-change kernel supported');f<-changepoint::cpt.mean(y,method='PELT',penalty='MBIC',minseglen=5);return(list(change_after_observation=changepoint::cpts(f),scope='descriptive candidates; dependence/backtest acceptance still required'))}
    if(id=='M25')return(i6_procrustes(d))
    if(id=='M27')return(i6_correspondence(d))
    if(id=='M39')return(i6_hazard(d))
    if(id=='M40')return(i6_sar(d))
    if(id=='M41')return(i6_relational(d))
    if(id%in%i7_ids)return(i7_compute(id,d))
    stop('No numerical implementation')
  })
  list(schema='un.i6.engineering.v1',method_id=id,publication_eligible=FALSE,daily_adapter_integrated=FALSE,dataset_kind=d$dataset_kind,value=value,R=as.character(getRversion()),RNGkind=RNGkind(),seed=30092026L)
}

source(file.path(dirname(normalizePath(sys.frame(1)$ofile)), 'engines_more.R'))
i6_ids <- sort(c(i6_ids,i7_ids))
