# I7 bounded research kernels; invoked only behind i6_compute's synthetic guard.
i7_ids <- c('M14','M18','M19','M20','M28','M29','M30','M35','M42')
i7_backend <- function(p) {
  i6_need(p)
  expected <- c(gbm='2.3.1',topicmodels='0.2.17',stm='1.3.8',depmixS4='1.5.4',blockmodels='1.1.5',posterior='1.7.0')
  i6_assert(as.character(packageVersion(p))==expected[[p]],paste('Untested backend version:',p,'expected',expected[[p]]))
}
i7_serial <- function(fun) {
  i6_need('RhpcBLASctl')
  old_blas<-RhpcBLASctl::blas_get_num_procs();old_omp<-RhpcBLASctl::omp_get_max_threads()
  on.exit({RhpcBLASctl::blas_set_num_threads(old_blas);RhpcBLASctl::omp_set_num_threads(old_omp)})
  RhpcBLASctl::blas_set_num_threads(1);RhpcBLASctl::omp_set_num_threads(1);fun()
}
i7_counts <- function(x) {
  x<-i6_matrix(x);i6_assert(all(x>=0 & x==floor(x))&&all(rowSums(x)>0)&&sum(x)<=1000000,'Nonempty integer document counts within token budget required');x
}
i7_topics <- function(id,d) {
  x<-i7_counts(d$train);a<-i7_counts(d$observed);b<-i7_counts(d$heldout)
  i6_assert(identical(colnames(x),colnames(a))&&identical(dimnames(a),dimnames(b))&&!length(intersect(rownames(x),rownames(a))),'Frozen vocabulary and disjoint train/evaluation documents required')
  i6_assert(length(d$k)==1&&d$k%in%2:8&&d$k<min(dim(x)),'Bounded topic count required')
  if(id=='M18') {
    i7_backend('topicmodels')
    f<-topicmodels::LDA(x,k=d$k,method='VEM',control=list(seed=30092026L,alpha=.1,estimate.alpha=FALSE,verbose=0))
    beta<-topicmodels::posterior(f)$terms
    theta<-topicmodels::posterior(f,newdata=a)$topics
    convergence<-NA
  } else {
    i7_backend('stm')
    # Deliberately fixed numeric prevalence design; no arbitrary formulas or content model.
    m<-i6_matrix(d$train_meta);n<-i6_matrix(d$eval_meta)
    i6_assert(identical(rownames(m),rownames(x))&&identical(rownames(n),rownames(a))&&identical(colnames(m),colnames(n))&&ncol(m)<=3,'Aligned bounded numeric prevalence metadata required')
    i6_assert(qr(cbind(1,m))$rank==ncol(m)+1&&all(apply(m,2,sd)>0),'Identifiable prevalence design required')
    nm<-paste0('cov',seq_len(ncol(m)));colnames(m)<-colnames(n)<-nm
    meta<-as.data.frame(m);newmeta<-as.data.frame(n);form<-reformulate(nm)
    docs<-function(z)lapply(seq_len(nrow(z)),function(i){j<-which(z[i,]>0);rbind(j,z[i,j])})
    f<-stm::stm(docs(x),colnames(x),K=d$k,prevalence=form,data=meta,init.type='Random',seed=30092026L,max.em.its=300,verbose=FALSE)
    beta<-exp(f$beta$logbeta[[1]])
    theta<-stm::fitNewDocuments(f,docs(a),newData=newmeta,origData=meta,prevalence=form,prevalencePrior='Covariate',verbose=FALSE)$theta
    convergence<-f$convergence
    i6_assert(isTRUE(convergence$converged),'Structural topic fit did not converge')
  }
  prob<-theta%*%beta
  i6_assert(all(is.finite(prob))&&all(prob>=0)&&all(abs(rowSums(prob)-1)<1e-6),'Invalid topic probabilities')
  baseline<-(colSums(x)+1)/(sum(x)+ncol(x))
  list(model=f,topic_word=beta,document_topic=theta,heldout_perplexity=exp(-sum(b*log(pmax(prob,1e-15)))/sum(b)),baseline_perplexity=exp(-sum(sweep(b,2,log(baseline),'*'))/sum(b)),convergence=convergence,vocabulary=colnames(x),scope='document completion: infer on observed words, score disjoint heldout words; topic labels require review')
}
i7_embedding_topics <- function(d) {
  i6_need('dbscan');x<-i6_unit(d$x);counts<-i7_counts(d$counts)
  i6_assert(identical(rownames(x),rownames(counts))&&is.character(d$representation_id)&&length(d$representation_id)==1&&nzchar(d$representation_id),'Aligned passages and pinned embedding basis required')
  f<-dbscan::hdbscan(x,minPts=5);groups<-sort(unique(f$cluster[f$cluster>0]))
  if(!length(groups))return(list(cluster=f$cluster,noise=rownames(x),descriptors=list(),exemplars=list(),scope='all passages are density noise'))
  cts<-t(vapply(groups,function(g)colSums(counts[f$cluster==g,,drop=FALSE]),numeric(ncol(counts))))
  # Class TF-IDF: class-normalized counts times log(1 + average class size / total term count).
  score<-sweep(cts/rowSums(cts),2,log1p(mean(rowSums(cts))/pmax(1,colSums(cts))),'*')
  rownames(score)<-as.character(groups)
  descriptors<-lapply(seq_along(groups),function(j)colnames(counts)[head(order(score[j,],decreasing=TRUE),5)])
  exemplars<-lapply(groups,function(g){ix<-which(f$cluster==g);center<-colMeans(x[ix,,drop=FALSE]);rownames(x)[head(ix[order(as.numeric(x[ix,,drop=FALSE]%*%center),decreasing=TRUE)],3)]})
  names(descriptors)<-names(exemplars)<-as.character(groups)
  list(cluster=setNames(f$cluster,rownames(x)),noise=rownames(x)[f$cluster==0],class_tfidf=score,descriptors=descriptors,exemplars=exemplars,scope='embedding density topics with source passage IDs; no political or probability interpretation')
}
i7_sequences <- function(z,categorical=FALSE,dynamic=FALSE) {
  i6_assert(is.data.frame(z)&&all(c('id','time','y')%in%names(z))&&nrow(z)>=10&&nrow(z)<=5000&&!anyNA(z),'Complete bounded sequence table required')
  i6_assert(is.character(z$id)&&all(nzchar(z$id))&&is.numeric(z$time)&&all(is.finite(z$time))&&is.numeric(z$y)&&all(is.finite(z$y)),'Valid sequence identities, numeric times and observations required')
  ids<-unique(z$id);i6_assert(identical(z$id,rep(ids,as.integer(table(factor(z$id,levels=ids))))),'Sequence rows must be contiguous')
  for(g in ids)i6_assert(all(diff(z$time[z$id==g])>0),'Strictly ordered observations within sequence required')
  if(categorical)i6_assert('item2'%in%names(z)&&all(z$y%in%0:1)&&all(z$item2%in%0:1),'Two invariant binary measurement items required')
  if(dynamic)i6_assert(all(c('lag','available')%in%names(z))&&is.numeric(z$lag)&&all(is.finite(z$lag))&&all(is.finite(z$available))&&all(z$available<z$time),'Transition covariates must precede observations')
  as.integer(table(factor(z$id,levels=ids)))
}
i7_states <- function(id,d) {
  i7_backend('depmixS4');catg<-id=='M29';dyn<-id=='M30';tr<-d$train;te<-d$test
  nt<-i7_sequences(tr,catg,dyn);ne<-i7_sequences(te,catg,dyn)
  i6_assert(max(tr$time)<min(te$time),'Training parameters must be estimated before every evaluation observation')
  i6_assert(length(d$states)==1&&d$states%in%2:4&&nrow(tr)>=30*d$states,'Bounded state count and adequate sequence length required')
  if(catg)i6_assert(identical(d$measurement,'invariant_binary_items'),'Time-invariant measurement contract required')
  build<-function(z,nn)depmixS4::depmix(if(catg)list(y~1,item2~1)else y~1,data=z,nstates=d$states,transition=if(dyn)~lag else ~1,family=if(catg)list(binomial(),binomial())else gaussian(),ntimes=nn)
  fit_warnings<-character()
  f<-withCallingHandlers(depmixS4::fit(build(tr,nt),verbose=FALSE,emcontrol=depmixS4::em.control(maxit=500,tol=1e-7)),warning=function(w){
    msg<-conditionMessage(w)
    # EM uses fractional posterior weights in binomial updates; retain this known warning.
    if(grepl('non-integer #successes',msg,fixed=TRUE)){fit_warnings<<-unique(c(fit_warnings,msg));invokeRestart('muffleWarning')}else stop(msg,call.=FALSE)
  })
  i6_assert(is.finite(depmixS4::forwardbackward(f)$logLike)&&!grepl('maximum|iteration limit',f@message,ignore.case=TRUE),'Hidden-state training did not converge')
  new<-depmixS4::setpars(build(te,ne),depmixS4::getpars(f))
  fb<-depmixS4::forwardbackward(new);p<-fb$alpha/rowSums(fb$alpha)
  i6_assert(all(is.finite(p))&&all(p>=0)&&all(abs(rowSums(p)-1)<1e-7),'Invalid filtered state probabilities')
  list(model=f,filtered=p,test_loglik=fb$logLike,fit_message=f@message,fit_warnings=fit_warnings,sequence_start='evaluation sequences restart from learned prior; no implicit training continuity',scope=if(catg)'latent transition with two time-invariant conditionally independent binary items; invariance imposed, not empirically established' else if(dyn)'Gaussian Markov-switching mixture with lagged-covariate transition probabilities' else 'Gaussian hidden Markov states; forward filtering only; no future-smoothed evaluation output')
}
i7_blocks <- function(d) {
  i7_backend('blockmodels');a<-i6_matrix(d$adj,12)
  i6_assert(nrow(a)==ncol(a)&&nrow(a)<=150&&identical(rownames(a),colnames(a))&&all(a%in%0:1)&&all(diag(a)==0)&&isTRUE(all.equal(a,t(a)))&&identical(d$edge_type,'observed_binary'),'Complete undirected binary network required; similarities/unknown edges cannot become Bernoulli trials')
  i6_assert(any(a==1)&&sum(a)<length(a)-nrow(a),'Degenerate network')
  f<-blockmodels::BM_bernoulli('SBM_sym',a,verbosity=0,plotting='',explore_min=2,explore_max=4,ncores=1)
  f$estimate();k<-which.max(f$ICL);membership<-f$memberships[[k]]$Z
  i6_assert(nrow(membership)==nrow(a)&&all(is.finite(membership)),'Invalid block membership')
  list(membership=membership,blocks=max.col(membership,ties.method='first'),ICL=f$ICL,selected=k,parameters=f$model_parameters[[k]],scope='Bernoulli stochastic block model; complete observed binary graph only; clusters do not establish alliances')
}
i7_bayes_hazard <- function(d) {
  i7_backend('posterior')
  # Reuse the first-event interval contract, including censoring and exposure chronology.
  invisible(i6_hazard(d));x<-cbind(intercept=1,i6_matrix(d$x));n<-nrow(x)
  i6_assert(length(d$group)==n&&!anyNA(d$group)&&all(nzchar(d$group)),'Pooling groups required')
  groups<-sort(unique(d$group));g<-match(d$group,groups);q<-ncol(x);h<-length(groups);p<-q+h
  i6_assert(h>=2&&h<=12&&q<=5&&n<=1500&&all(table(g)>=10),'Bounded adequately populated pooling groups required')
  # Fixed N(0,1) group prior: partial pooling with prespecified scale, not estimated heterogeneity.
  lp<-function(b){eta<-as.numeric(x%*%b[seq_len(q)])+b[q+g];haz<-exp(pmin(eta,700));eventlog<-log(-expm1(-haz));sum(ifelse(d$y==1,eventlog,-haz))-sum(b[seq_len(q)]^2)/8-sum(b[q+seq_len(h)]^2)/2}
  mode<-optim(rep(0,p),function(b)-lp(b),method='BFGS',hessian=TRUE)
  i6_assert(mode$convergence==0&&all(is.finite(mode$hessian)),'Posterior mode failed')
  proposal<-tryCatch(chol(solve(mode$hessian))* (2.38/sqrt(p)),error=function(e)stop('Posterior proposal is not positive definite'))
  draws<-array(NA_real_,c(3000,4,p),dimnames=list(NULL,NULL,c(colnames(x),paste0('group:',groups))));accept<-numeric(4)
  for(ch in 1:4){b<-mode$par+as.numeric(rnorm(p)%*%proposal);cur<-lp(b);hits<-0
    for(it in 1:5000){cand<-b+as.numeric(rnorm(p)%*%proposal);nxt<-lp(cand);if(is.finite(nxt)&&log(runif(1))<nxt-cur){b<-cand;cur<-nxt;if(it>2000)hits<-hits+1};if(it>2000)draws[it-2000,ch,]<-b};accept[ch]<-hits/3000}
  diag<-as.data.frame(posterior::summarise_draws(posterior::as_draws_array(draws),'mean','sd','rhat','ess_bulk','ess_tail'))
  ok<-all(is.finite(as.matrix(diag[,-1])))&&all(diag$rhat<1.01)&&all(diag$ess_bulk>=400)&all(diag$ess_tail>=400)
  flat<-matrix(draws,ncol=p);ix<-seq(1,nrow(flat),length.out=200);pred<-vapply(ix,function(j){eta<-as.numeric(x%*%flat[j,seq_len(q)])+flat[j,q+g];sum(rbinom(n,1,-expm1(-exp(pmin(eta,700)))))},numeric(1))
  list(draws=draws,diagnostics=diag,sampler_pass=ok,quality_state=if(ok)'synthetic_diagnostics_pass'else 'withheld_sampler_diagnostics',acceptance=accept,observed_events=sum(d$y),replicated_event_quantiles=quantile(pred,c(.025,.5,.975)),priors=list(beta_sd=2,group_sd=1,group_scale_estimated=FALSE),scope='associational cloglog first-event hazard with fixed-scale Gaussian partial pooling; diagnostics do not authorize publication')
}
i7_compute <- function(id,d) {
  if(id%in%c('M18','M19'))return(i7_serial(function()i7_topics(id,d)))
  if(id=='M20')return(i7_embedding_topics(d))
  if(id%in%c('M28','M29','M30'))return(i7_states(id,d))
  if(id=='M35')return(i7_blocks(d))
  if(id=='M42')return(i7_bayes_hazard(d))
  stop('No I7 numerical implementation')
}
