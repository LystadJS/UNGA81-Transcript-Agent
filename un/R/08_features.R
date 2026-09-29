# D1-I2: immutable, source-bound TF-IDF references and sparse daily transforms.
# This is a bag-of-words representation. It does not measure agreement or stance.
I2_FEATURE_SCHEMA <- "D1-I2-tfidf-v1"
i2_stopwords <- function() strsplit(paste(
  "a an the this that these those i me my we us our ours you your yours he him his she her hers it its they them their theirs",
  "am is are was were be been being have has had having do does did doing and or but if then else when while as of at by for with about against between into through during before after above below to from up down in out on off over under again further once here there where why how all any both each few more most other some such only own same so than too very can will just now",
  "mr mrs ms madam mister excellency excellencies president secretary general assembly united nations thank thanks")," ")[[1]]
i2_abort <- function(kind, message) stop(structure(list(message=message,call=NULL),class=c(paste0("d1_i2_",kind),"error","condition")))
i2_limit <- function(ok,message) if(!isTRUE(ok))i2_abort("resources",message)
i2_policy <- function(root, which=c("feature","projection")) {
  which<-match.arg(which);name<-paste0(which,"_policy.json")
  path<-file.path(root,"config",name);frozen<-file.path(root,"design/D1-I2",name)
  assert(identical(sha_file(path),sha_file(frozen)),"Policy changed without an explicit design revision; do not tune gates on the reporting sample")
  p<-json_read(path)
  assert(identical(p$schema,if(which=="feature")I2_FEATURE_SCHEMA else "D1-I2-projection-display-v1"),"Unsupported feature/projection policy")
  p
}
i2_tokenize <- function(text, policy) {
  visible(text)
  z<-tolower(enc2utf8(text))
  # Unicode letters, no stemming/transliteration or inferred translation. Keep negation.
  tokens<-regmatches(z,gregexpr("\\p{L}+",z,perl=TRUE))[[1]]
  if(!length(tokens)||identical(tokens,character()))return(character())
  tokens[nchar(tokens,type="chars")>=policy$min_term_chars & !tokens%in%i2_stopwords()]
}
i2_implementation_signature <- function(functions) sha_object(lapply(functions,function(name)paste(deparse(body(get(name,mode="function")),width.cutoff=500L),collapse="\n")))
i2_env_signature <- function() list(R=as.character(getRversion()),Matrix=as.character(utils::packageVersion("Matrix")),
  LC_CTYPE=Sys.getlocale("LC_CTYPE"),PCRE=unname(extSoftVersion()["PCRE"]),stopwords_sha256=sha_object(i2_stopwords()),
  feature_implementation=i2_implementation_signature(c("i2_tokenize","i2_fit_vocabulary","i2_weight_units","i2_pool_countries","i2_transform")))
i2_feature_units <- function(cp,snapshot=NULL) {
  ss<-unique_current_observations(cp)
  if(!length(ss))return(list())
  versions<-vapply(ss,function(s)observation_object(s)$observation_version_id,character(1))
  ss<-ss[order(versions,method="radix")]
  units<-lapply(ss,function(s) {
    obj<-observation_object(s)
    assert(identical(sha_text(s$text),s$text_sha256),"Changed source text before feature transform")
    if(!is.null(snapshot)) {
      rows<-snapshot$observations[snapshot$observations$observation_version_id==obj$observation_version_id,,drop=FALSE]
      assert(nrow(rows)==1L && rows$event_date==s$date && rows$text_sha256==s$text_sha256,"Current text is not in the frozen as-of snapshot")
      assert(parse_utc(s$acquired_at)<=parse_utc(snapshot$as_of_cutoff)&&s$date<=cp$brief$date,"Feature input leaks future event/availability information")
    }
    list(observation_id=s$observation_id,observation_version_id=obj$observation_version_id,
      iso3=s$iso3,country=s$country,region=s$region,date=s$date,genre=s$genre,language=s$language,
      translation_version=s$translation_version,eligibility_class=s$eligibility_class,
      source_type=s$source_type,source_sha256=s$source_sha256,text_sha256=s$text_sha256,
      acquired_at=s$acquired_at,flags=as.list(unlist(s$flags)),source_url=str1(s$source_url),text=s$text)
  })
  units
}
i2_units_key <- function(units) sha_object(lapply(units,function(u)u[setdiff(names(u),"acquired_at")]))
i2_scope_key <- function(units) {
  fields<-c("eligibility_class","genre","language","translation_version")
  signature<-setNames(lapply(fields,function(f)sort(unique(vapply(units,function(u)str1(u[[f]]),character(1))),method="radix")),fields)
  list(key=sha_object(signature),signature=signature)
}
i2_token_lists <- function(units,policy) {
  need_packages("Matrix")
  i2_limit(length(units)<=policy$max_statements,"Statement cap exceeded; use a larger-corpus implementation before raising this bound")
  i2_limit(sum(vapply(units,function(u)nchar(u$text),numeric(1)))<=policy$max_source_chars,"Input-character cap exceeded")
  lapply(units,function(u)i2_tokenize(u$text,policy))
}
i2_fit_vocabulary <- function(units,policy) {
  tokens<-i2_token_lists(units,policy)
  hashes<-vapply(units,function(u)u$text_sha256,character(1));keep<-!duplicated(hashes)
  n<-sum(keep)
  if(n<policy$min_reference_unique_texts)i2_abort("data","At least two distinct reference texts are needed for a TF-IDF reference")
  df<-table(unlist(lapply(tokens[keep],unique),use.names=FALSE))
  df<-df[df>=policy$min_document_frequency & df/n<=policy$max_document_fraction]
  if(!length(df))i2_abort("data","No terms survive the frozen document-frequency policy")
  # Deterministic feature selection; tie-breaks use byte-stable lexical order.
  df<-df[order(-as.integer(df),names(df),method="radix")];df<-head(df,policy$max_terms)
  df<-df[order(names(df),method="radix")]
  list(vocabulary=names(df),document_frequency=as.integer(df),idf=1+log((1+n)/(1+as.integer(df))),
       n_unique_texts=as.integer(n),reference_unique_text_hashes=sort(unique(hashes),method="radix"))
}
i2_weight_units <- function(units,vocabulary,policy) {
  tokens<-i2_token_lists(units,policy);vocab<-vocabulary$vocabulary
  assert(length(vocab)==length(vocabulary$idf)&&!anyDuplicated(vocab)&&all(is.finite(vocabulary$idf)),"Invalid frozen vocabulary or IDF")
  ii<-jj<-integer();xx<-numeric();rows<-list()
  for(i in seq_along(tokens)) {
    counts<-table(tokens[[i]]);j<-match(names(counts),vocab);known<-!is.na(j)
    if(any(known)){ii<-c(ii,rep.int(i,sum(known)));jj<-c(jj,j[known]);xx<-c(xx,(1+log(as.numeric(counts[known])))*vocabulary$idf[j[known]])}
    total<-length(tokens[[i]]);oov<-sum(counts[!known])
    rows[[i]]<-c(units[[i]][c("observation_id","observation_version_id","iso3","country","region","date","genre","language","eligibility_class","text_sha256")],
       list(eligible_tokens=total,known_tokens=total-oov,oov_tokens=oov,oov_fraction=if(total)oov/total else NA_real_))
  }
  i2_limit(length(xx)<=policy$max_sparse_nonzero,"Sparse nonzero cap exceeded")
  ids<-vapply(units,function(u)u$observation_version_id,character(1))
  x<-Matrix::sparseMatrix(i=ii,j=jj,x=xx,dims=c(length(units),length(vocab)),dimnames=list(ids,vocab))
  norms<-sqrt(Matrix::rowSums(x*x));valid<-is.finite(norms)&norms>0
  x<-Matrix::Diagonal(x=ifelse(valid,1/pmax(norms,.Machine$double.xmin),0))%*%x
  dimnames(x)<-list(ids,vocab)
  stats<-rows_frame(rows,c("observation_id","observation_version_id","iso3","country","region","date","genre","language","eligibility_class","text_sha256","eligible_tokens","known_tokens","oov_tokens","oov_fraction"))
  for(k in c("eligible_tokens","known_tokens","oov_tokens","oov_fraction"))stats[[k]]<-suppressWarnings(as.numeric(stats[[k]]))
  stats$nonzero<-valid
  list(x=x,rows=stats)
}
i2_pool_countries <- function(statements,units,policy) {
  isos<-sort(unique(vapply(units,function(u)u$iso3,character(1))),method="radix")
  i2_limit(length(isos)<=policy$max_countries,"Country cap exceeded")
  ii<-jj<-integer();xx<-numeric();meta<-list()
  for(i in seq_along(isos)) {
    ids<-which(statements$rows$iso3==isos[i]);ids<-ids[!duplicated(statements$rows$text_sha256[ids])]
    ii<-c(ii,rep.int(i,length(ids)));jj<-c(jj,ids);xx<-c(xx,rep.int(1/length(ids),length(ids)))
    u<-units[[ids[1]]]
    meta[[i]]<-list(iso3=isos[i],country=u$country,region=u$region,date=u$date,
      n_statements=length(ids),zero_statements=sum(!statements$rows$nonzero[ids]),
      observation_versions=paste(statements$rows$observation_version_id[ids],collapse="|"),
      language=paste(sort(unique(statements$rows$language[ids]),method="radix"),collapse="|"),
      genre=paste(sort(unique(statements$rows$genre[ids]),method="radix"),collapse="|"))
  }
  pool<-Matrix::sparseMatrix(i=ii,j=jj,x=xx,dims=c(length(isos),nrow(statements$x)))
  x<-pool%*%statements$x;nr<-sqrt(Matrix::rowSums(x*x));ok<-is.finite(nr)&nr>0
  x<-Matrix::Diagonal(x=ifelse(ok,1/pmax(nr,.Machine$double.xmin),0))%*%x
  dimnames(x)<-list(isos,colnames(statements$x))
  rows<-rows_frame(meta,c("iso3","country","region","date","n_statements","zero_statements","observation_versions","language","genre"));rows$nonzero<-ok
  list(x=x,rows=rows)
}
i2_transform <- function(units,vocabulary,policy) {
  s<-i2_weight_units(units,vocabulary,policy);c<-i2_pool_countries(s,units,policy)
  sim<-as.matrix(Matrix::tcrossprod(c$x));sim[]<-pmax(-1,pmin(1,sim))
  # An empty feature vector is missing evidence, never zero similarity.
  bad<-!c$rows$nonzero;if(any(bad)){sim[bad,]<-NA_real_;sim[,bad]<-NA_real_}
  dimnames(sim)<-list(c$rows$iso3,c$rows$iso3)
  list(statement=s,country=c,cosine=sim,raw_unit_count=length(units))
}
i2_validate_reference <- function(ref,policy,environment=TRUE,recompute=TRUE) {
  assert(identical(ref$schema,I2_FEATURE_SCHEMA)&&identical(ref$policy,policy),"Frozen TF-IDF schema/policy mismatch")
  assert(identical(ref$policy_hash,sha_object(policy)),"Reference policy fingerprint mismatch")
  if(environment)assert(identical(ref$environment,i2_env_signature()),"Frozen tokenizer/R/Matrix environment differs; create a new reference namespace rather than silently refitting")
  assert(identical(ref$reference_id,sha_object(ref[setdiff(names(ref),"reference_id")])),"Frozen reference content fingerprint mismatch")
  assert(all(vapply(ref$units,function(u)identical(sha_text(u$text),u$text_sha256)&&parse_utc(u$acquired_at)<=parse_utc(ref$source_as_of_cutoff)&&u$date<=ref$event_cutoff,logical(1))),"Reference text/time integrity failed")
  assert(parse_utc(ref$frozen_at)>=parse_utc(ref$source_as_of_cutoff),"Reference fitted before its known inputs were archived")
  if(recompute) {
    expect<-i2_fit_vocabulary(ref$units,policy)
    assert(identical(expect,ref$vocabulary),"Frozen IDF/DF/vocabulary does not match reference texts")
    calc<-i2_transform(ref$units,ref$vocabulary,policy)
    assert(identical(calc,ref$features),"Reference feature matrix differs from deterministic source transform")
  }
  invisible(TRUE)
}
i2_reference <- function(cp,root,run,snapshot,clock=utc_now) {
  p<-i2_policy(root,"feature");u<-i2_feature_units(cp,snapshot)
  if(!length(u))i2_abort("data","No source text for frozen feature construction")
  scope<-i2_scope_key(u);a<-cp$config$analytics
  ns<-a$feature_reference_namespace
  assert(grepl("^[A-Za-z0-9_-]+$",ns),"Unsafe feature-reference namespace")
  home<-file.path(root,relative_path(a$feature_reference_dir),ns,scope$key)
  dir.create(home,recursive=TRUE,showWarnings=FALSE)
  lock<-history_lock(home);on.exit(history_unlock(lock),add=TRUE)
  active<-file.path(home,"ACTIVE.rds");hashpath<-paste0(active,".sha256")
  if(file.exists(active)||file.exists(hashpath)) {
    assert(file.exists(active)&&file.exists(hashpath)&&identical(sha_file(active),trimws(read_text(hashpath))),"Frozen-reference pointer missing/corrupt; no silent rebootstrap")
    pointer<-readRDS(active);ref<-object_read(home,pointer)
    i2_validate_reference(ref,p)
    assert(identical(ref$scope,scope),"Reference provenance/genre/language namespace mismatch")
    if(ref$event_cutoff>cp$brief$date||parse_utc(ref$source_as_of_cutoff)>parse_utc(snapshot$as_of_cutoff)||parse_utc(ref$frozen_at)>parse_utc(clock()))i2_abort("version","Active reference is newer than this run's information set; select the correct historical namespace")
    operation<-"reused_frozen_reference"
  } else {
    if(!identical(a$feature_reference_mode,"bootstrap_then_frozen"))i2_abort("version","No frozen reference is selected; auto-bootstrap is disabled")
    v<-i2_fit_vocabulary(u,p);f<-i2_transform(u,v,p)
    ref<-list(schema=I2_FEATURE_SCHEMA,policy=p,policy_hash=sha_object(p),scope=scope,environment=i2_env_signature(),
      units=u,source_snapshot_id=snapshot$snapshot_id,source_as_of_cutoff=snapshot$as_of_cutoff,event_cutoff=cp$brief$date,
      frozen_at=clock(),vocabulary=v,features=f,reference_is_human_gold=FALSE,
      exact_same_day_bootstrap_is_not_a_historical_validation=TRUE)
    ref$reference_id<-sha_object(ref);i2_validate_reference(ref,p)
    pointer<-object_write(home,ref,"objects")
    immutable_write(active,serialize(pointer,NULL,version=3));immutable_write(hashpath,charToRaw(paste0(sha_file(active),"\n")))
    operation<-"fitted_frozen_reference"
  }
  list(reference=ref,operation=operation,units=u)
}
i2_feature_execute <- function(cp,root,run,snapshot,clock=utc_now) {
  selected<-i2_reference(cp,root,run,snapshot,clock)
  r<-selected$reference;u<-selected$units;f<-i2_transform(u,r$vocabulary,r$policy)
  list(schema=I2_FEATURE_SCHEMA,method_id="M02",reference=r,reference_operation=selected$operation,
       input_identity=i2_units_key(u),current_units=u,current=f,source_snapshot_id=snapshot$snapshot_id,
       source_as_of_cutoff=snapshot$as_of_cutoff,event_cutoff=cp$brief$date,
       fitted_reference_id=r$reference_id,created_at=clock(),definition="Frozen TF-IDF cosine similarity; not stance or probability")
}
i2_validate_features <- function(v,cp=NULL,root=NULL) {
  assert(identical(v$schema,I2_FEATURE_SCHEMA)&&identical(v$method_id,"M02"),"Wrong feature artifact")
  p<-if(is.null(root))v$reference$policy else i2_policy(root,"feature")
  i2_validate_reference(v$reference,p)
  assert(identical(v$fitted_reference_id,v$reference$reference_id),"Reference identity mismatch")
  assert(identical(i2_units_key(v$current_units),v$input_identity),"Current source identity mismatch")
  if(!is.null(cp))assert(identical(i2_units_key(i2_feature_units(cp)),v$input_identity),"Feature artifact belongs to another source set")
  assert(all(vapply(v$current_units,function(u)identical(sha_text(u$text),u$text_sha256)&&parse_utc(u$acquired_at)<=parse_utc(v$source_as_of_cutoff)&&u$date<=v$event_cutoff,logical(1)))&&
    parse_utc(v$created_at)>=parse_utc(v$source_as_of_cutoff),"Current feature text/availability/event cutoff integrity failed")
  assert(v$reference$event_cutoff<=v$event_cutoff && parse_utc(v$reference$source_as_of_cutoff)<=parse_utc(v$source_as_of_cutoff)&&
         parse_utc(v$created_at)>=parse_utc(v$reference$frozen_at),"Feature/reference time ordering failed")
  expected<-i2_transform(v$current_units,v$reference$vocabulary,p)
  assert(identical(expected,v$current),"TF-IDF transform or cosine data were changed")
  invisible(TRUE)
}
i2_write_feature_tables <- function(v,run) {
  voc<-v$reference$vocabulary
  csv_write(file.path(run,"data/tfidf_vocabulary.csv"),data.frame(term=voc$vocabulary,document_frequency=voc$document_frequency,
    idf=voc$idf,reference_unique_texts=voc$n_unique_texts,reference_id=v$fitted_reference_id))
  csv_write(file.path(run,"data/tfidf_statement_quality.csv"),v$current$statement$rows)
  csv_write(file.path(run,"data/tfidf_country_index.csv"),v$current$country$rows)
  mat<-v$current$cosine
  csv_write(file.path(run,"data/tfidf_cosine_similarity.csv"),data.frame(iso3=rownames(mat),mat,check.names=FALSE))
  saveRDS(v$current$statement$x,file.path(run,"data/tfidf_statement_matrix.rds"),version=3)
  saveRDS(v$current$country$x,file.path(run,"data/tfidf_country_matrix.rds"),version=3)
  saveRDS(v$reference,file.path(run,"audit/analytics/tfidf_reference.rds"),version=3)
  csv_write(file.path(run,"data/tfidf_reference_sources.csv"),lapply(v$reference$units,function(u)u[setdiff(names(u),c("text","flags"))]),setdiff(names(v$reference$units[[1]]),c("text","flags")))
}
