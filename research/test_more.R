args<-commandArgs(TRUE);if(length(args)).libPaths(c(args[1],.libPaths()))
source('research/engines.R')
if(requireNamespace('RhpcBLASctl',quietly=TRUE)){RhpcBLASctl::blas_set_num_threads(1);RhpcBLASctl::omp_set_num_threads(1)}
records<-list();test<-function(name,expr){e<-tryCatch({force(expr);NULL},error=function(e)conditionMessage(e));records[[length(records)+1]]<<-data.frame(test=name,passed=is.null(e),error=if(is.null(e))''else e);cat(if(is.null(e))'PASS'else 'FAIL',name,if(!is.null(e))e,'\n')}
reject<-function(expr)stopifnot(tryCatch({force(expr);FALSE},error=function(e)TRUE))
kind<-function(d){d$dataset_kind<-'synthetic_engineering';d}
set.seed(203)
mat<-function(n,p=2,prefix='r'){z<-matrix(rnorm(n*p),n,p);dimnames(z)<-list(paste0(prefix,1:n),paste0('x',1:p));z}
part<-function(prefix,offset){x<-mat(300,prefix=prefix);list(x=x,y=rbinom(300,1,plogis(1.3*x[,1]-.5*x[,2])),time=1:300+offset,country=paste0(prefix,1:300),text_hash=paste0(prefix,'h',1:300))}
d<-kind(list(train=part('a',0),calibration=part('b',1000),test=part('c',2000)))
test('M14 heldout calibrated boosting beats prevalence',{v<-i6_compute('M14',d);stopifnot(!v$publication_eligible,!v$daily_adapter_integrated,v$value$test_logloss<v$value$baseline_logloss,length(v$value$scores)==300)})
test('M14 temporal leakage rejected',{z<-d;z$train$time[1]<-9999;reject(i6_compute('M14',z))})
test('M14 country leakage rejected',{z<-d;z$test$country[1]<-z$train$country[1];reject(i6_compute('M14',z))})
ct<-function(n,prefix){z<-matrix(rpois(n*20,1),n,20);for(i in 1:n)z[i,if(i%%2)1:10 else 11:20]<-z[i,if(i%%2)1:10 else 11:20]+rpois(10,9);dimnames(z)<-list(paste0(prefix,1:n),paste0('w',1:20));z}
x<-ct(60,'tr');a<-ct(20,'ev');b<-ct(20,'ev')
td<-kind(list(train=x,observed=a,heldout=b,k=2,train_meta=matrix(rep(0:1,30),60,1,dimnames=list(rownames(x),'trend')),eval_meta=matrix(rep(0:1,10),20,1,dimnames=list(rownames(a),'trend'))))
for(id in c('M18','M19')) {
  test(paste(id,'document completion beats unigram'),{v<-i6_compute(id,td)$value;stopifnot(v$heldout_perplexity<v$baseline_perplexity,all(abs(rowSums(v$document_topic)-1)<1e-6))})
  test(paste(id,'fractional counts rejected'),{z<-td;z$train[1,1]<-.5;reject(i6_compute(id,z))})
  test(paste(id,'evaluation identity overlap rejected'),{z<-td;rownames(z$train)[1]<-rownames(z$observed)[1];reject(i6_compute(id,z))})
  test(paste(id,'vocabulary reorder rejected'),{z<-td;z$observed<-z$observed[,20:1];reject(i6_compute(id,z))})
}
test('M19 metadata identity mismatch rejected',{z<-td;rownames(z$train_meta)[1]<-'wrong';reject(i6_compute('M19',z))})
test('M19 unidentified prevalence rejected',{z<-td;z$train_meta[,1]<-1;reject(i6_compute('M19',z))})
ex<-mat(60,3);ex[,1]<-rep(c(-5,5),each=30);ex[,2:3]<-ex[,2:3]*.03
ed<-kind(list(x=ex,counts=ct(60,'r'),representation_id='synthetic-encoder-v1'))
test('M20 cluster descriptors and evidence IDs',{v<-i6_compute('M20',ed)$value;stopifnot(length(v$descriptors)==2,all(unlist(v$exemplars)%in%rownames(ex)),all(is.finite(v$class_tfidf)),length(v$cluster)==60)})
test('M20 passage alignment rejected',{z<-ed;rownames(z$counts)[1]<-'wrong';reject(i6_compute('M20',z))})
test('M20 no encoder identity rejected',{z<-ed;z$representation_id<-'';reject(i6_compute('M20',z))})
seqdata<-function(offset){n<-240;state<-rep(0,n);lag<-rnorm(n);for(i in 2:n)state[i]<-rbinom(1,1,plogis(-1+2*state[i-1]+.3*lag[i]));data.frame(id=rep(c('a','b'),each=120),time=rep(1:120,2)+offset,y=-2+4*state+rnorm(n),lag=lag,available=rep(1:120,2)+offset-1,item2=rbinom(n,1,.15+.7*state))}
sd<-kind(list(train=seqdata(0),test=seqdata(200),states=2,measurement='invariant_binary_items'))
for(id in c('M28','M29','M30')) {
  z<-sd;if(id=='M29'){z$train$y<-as.numeric(z$train$y>0);z$test$y<-as.numeric(z$test$y>0)}
  test(paste(id,'normalized filtered states'),{v<-i6_compute(id,z)$value;stopifnot(all(abs(rowSums(v$filtered)-1)<1e-8),is.finite(v$test_loglik))})
  test(paste(id,'future observations cannot alter earlier filtering'),{v<-i6_compute(id,z)$value;zz<-z;zz$test$y[81:120]<-if(id=='M29')1-zz$test$y[81:120]else zz$test$y[81:120]+3;w<-i6_compute(id,zz)$value;stopifnot(isTRUE(all.equal(v$filtered[1:80,],w$filtered[1:80,],tolerance=1e-9)))})
  test(paste(id,'future training rejected'),{zz<-z;zz$train$time<-zz$train$time+500;reject(i6_compute(id,zz))})
  test(paste(id,'duplicate observation time rejected'),{zz<-z;zz$test$time[2]<-zz$test$time[1];reject(i6_compute(id,zz))})
}
test('M30 contemporaneous transition covariates rejected',{z<-sd;z$test$available<-z$test$time;reject(i6_compute('M30',z))})
test('M29 measurement drift contract rejected',{z<-sd;z$measurement<-'changing';reject(i6_compute('M29',z))})
adj<-matrix(0,40,40);for(i in 1:39)for(j in (i+1):40)adj[i,j]<-adj[j,i]<-rbinom(1,1,if((i<=20)==(j<=20)).8 else .03);dimnames(adj)<-list(paste0('n',1:40),paste0('n',1:40));bd<-kind(list(adj=adj,edge_type='observed_binary'))
test('M35 recovers planted block membership',{v<-i6_compute('M35',bd)$value;stopifnot(length(unique(v$blocks))==2,mean(outer(v$blocks,v$blocks,'==')==outer(rep(1:2,each=20),rep(1:2,each=20),'=='))>.95)})
test('M35 cosine network rejected',{z<-bd;z$adj[1,2]<-z$adj[2,1]<-.5;reject(i6_compute('M35',z))})
test('M35 unknown edges rejected',{z<-bd;z$adj[1,2]<-NA;reject(i6_compute('M35',z))})
test('M35 inconsistent directed edges rejected',{z<-bd;z$adj[1,2]<-1-z$adj[2,1];reject(i6_compute('M35',z))})
hx<-mat(360,1);group<-rep(c('A','B','C'),each=120);hy<-rbinom(360,1,-expm1(-exp(-1+.7*hx[,1]+rep(c(-.4,0,.4),each=120))))
hd<-kind(list(x=hx,y=hy,start=rep(1,360),stop=rep(2,360),exposure_available=rep(0,360),country=paste0('actor',1:360),censor_reason=rep('end_of_observation',360),group=group))
test('M42 partial pooling sampler diagnostics and simulated effect',{v<-i6_compute('M42',hd)$value;print(v$diagnostics);stopifnot(v$sampler_pass,abs(v$diagnostics$mean[2]-.7)<.4,all(v$acceptance>.1&v$acceptance<.7),length(v$replicated_event_quantiles)==3)})
test('M42 exposure from future rejected',{z<-hd;z$exposure_available[1]<-2;reject(i6_compute('M42',z))})
test('M42 insufficient pooling groups rejected',{z<-hd;z$group[]<-'one';reject(i6_compute('M42',z))})
test('M42 continued risk after adoption rejected',{z<-hd;z$country[1:2]<-'same';z$y[1:2]<-1;reject(i6_compute('M42',z))})
for(id in i7_ids)test(paste(id,'real data remain blocked'),reject(i6_compute(id,list(dataset_kind='real'))))
test('M18 heldout values cannot alter fitted topics or inferred proportions',{v<-i6_compute('M18',td)$value;z<-td;z$heldout<-z$heldout*2;w<-i6_compute('M18',z)$value;stopifnot(identical(v$topic_word,w$topic_word),identical(v$document_topic,w$document_topic))})
test('M19 heldout values cannot alter fitted topics or inferred proportions',{v<-i6_compute('M19',td)$value;z<-td;z$heldout<-z$heldout*2;w<-i6_compute('M19',z)$value;stopifnot(identical(v$topic_word,w$topic_word),identical(v$document_topic,w$document_topic))})
test('M28 serialized fitted model retains parameters',{v<-i6_compute('M28',sd)$value;w<-unserialize(serialize(v,NULL));stopifnot(identical(depmixS4::getpars(v$model),depmixS4::getpars(w$model)))})
test('M14 random state is restored',{old<-.Random.seed;invisible(i6_compute('M14',d));stopifnot(identical(old,.Random.seed))})
test('M35 node identity order rejected',{z<-bd;colnames(z$adj)<-rev(colnames(z$adj));reject(i6_compute('M35',z))})
test('M20 zero embedding rejected',{z<-ed;z$x[1,]<-0;reject(i6_compute('M20',z))})
test('M42 unequal interval durations rejected',{z<-hd;z$stop[1]<-3;reject(i6_compute('M42',z))})
test('Unimplemented methods fail explicitly',{for(id in c('M16','M26','M38'))reject(i6_compute(id,kind(list())))})
result<-do.call(rbind,records);out<-Sys.getenv('I7_TEST_REPORT',tempfile(fileext='.csv'));write.csv(result,out,row.names=FALSE);cat(nrow(result),'checks;',sum(!result$passed),'failures\n');if(any(!result$passed))quit(status=1)
