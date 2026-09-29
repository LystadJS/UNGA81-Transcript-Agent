# D1-I2: frozen PCA (primary) and Euclidean PCoA (audit challenger).
# No axis has a political interpretation. PCoA is not an independent confirmation:
# with these Euclidean features it should agree geometrically with centered PCA.
I2_PROJECTION_SCHEMA <- "D1-I2-projection-v1"
i2_projection_signature <- function() i2_implementation_signature(c("i2_squared_distances","i2_pca_fit","i2_pcoa_fit","i2_pcoa_project_distances","i2_project","i2_geometry_metrics","i2_projection_checks"))
i2_dense <- function(x,feature_policy) {
  i2_limit(prod(dim(x))<=feature_policy$max_dense_cells,"Dense decomposition cell cap exceeded; do not materialize the entire historical corpus")
  m<-as.matrix(x);assert(is.numeric(m)&&all(is.finite(m)),"Non-finite numeric features")
  m
}
i2_squared_distances <- function(x,y=x) {
  # Works for rectangular out-of-sample distances and sparse matrices.
  d<-outer(as.numeric(Matrix::rowSums(x*x)),as.numeric(Matrix::rowSums(y*y)),"+")-2*as.matrix(Matrix::tcrossprod(x,y))
  d[]<-pmax(0,d)
  if(identical(x,y)) { d<-(d+t(d))/2;diag(d)<-0 } # exact self-distance; remove roundoff before sqrt
  dimnames(d)<-list(rownames(x),rownames(y));d
}
i2_sign_columns <- function(m) {
  if(!ncol(m))return(numeric())
  vapply(seq_len(ncol(m)),function(j)if(m[which.max(abs(m[,j])),j]<0)-1 else 1,numeric(1))
}
i2_pca_fit <- function(x,policy,feature_policy) {
  x<-i2_dense(x,feature_policy)
  if(nrow(x)<3L||ncol(x)<2L)i2_abort("data","PCA requires at least three usable reference countries and two features")
  fit<-stats::prcomp(x,center=TRUE,scale.=FALSE,rank.=2L,retx=TRUE)
  values<-fit$sdev^2*(nrow(x)-1L);scale<-max(values)
  if(!is.finite(scale)||scale<=0||sum(values>scale*policy$rank_relative_tolerance)<2L)i2_abort("data","Reference matrix has fewer than two nonzero principal components")
  signs<-i2_sign_columns(fit$rotation)
  rotation<-sweep(fit$rotation,2,signs,"*")
  list(kind="PCA",feature_names=colnames(x),country_ids=rownames(x),center=fit$center,
       rotation=rotation,values=values,coordinates=sweep(x,2,fit$center,"-")%*%rotation,
       negative_eigenvalue_mass=0,numerical_rank=sum(values>scale*policy$rank_relative_tolerance),
       scale_features=FALSE,axis_orientation="largest absolute loading positive; lexical tie order")
}
i2_pcoa_fit <- function(d,policy) {
  assert(is.matrix(d)&&is.numeric(d)&&nrow(d)==ncol(d)&&all(is.finite(d))&&all(d>=0),"PCoA requires a finite, nonnegative square distance matrix")
  assert(max(abs(diag(d)))<1e-10&&max(abs(d-t(d)))<1e-10,"PCoA distances must be symmetric with zero diagonal")
  if(nrow(d)<3L)i2_abort("data","PCoA requires at least three usable reference countries")
  d2<-d^2;means<-rowMeans(d2);grand<-mean(d2)
  b<--0.5*(sweep(sweep(d2,1,means,"-"),2,means,"-")+grand)
  e<-eigen(b,symmetric=TRUE);pos<-sum(pmax(e$values,0));neg<-sum(abs(pmin(e$values,0)))
  mass<-if(pos>0)neg/pos else NA_real_
  if(!is.finite(mass)||mass>policy$pcoa_negative_eigenvalue_tolerance)i2_abort("quality","Non-Euclidean or degenerate PCoA distances: no automatic correction is permitted")
  if(sum(e$values>max(e$values)*policy$rank_relative_tolerance)<2L)i2_abort("data","Reference distances have fewer than two positive principal coordinates")
  vectors<-e$vectors[,1:2,drop=FALSE];vectors<-sweep(vectors,2,i2_sign_columns(vectors),"*")
  coords<-sweep(vectors,2,sqrt(e$values[1:2]),"*")
  rownames(vectors)<-rownames(coords)<-rownames(d)
  list(kind="PCoA",country_ids=rownames(d),vectors=vectors,values=e$values,coordinates=coords,
    reference_squared_distance_means=means,reference_squared_distance_grand_mean=grand,
    negative_eigenvalue_mass=mass,numerical_rank=sum(e$values>max(e$values)*policy$rank_relative_tolerance),
    correction="none",distance="Euclidean chord distance on L2-normalized country TF-IDF",
    axis_orientation="largest absolute reference eigenvector entry positive")
}
i2_pcoa_project_distances <- function(model,dnew) {
  assert(identical(model$kind,"PCoA")&&is.matrix(dnew)&&ncol(dnew)==length(model$country_ids)&&all(is.finite(dnew))&&all(dnew>=0),"Invalid out-of-sample distances")
  assert(identical(colnames(dnew),model$country_ids),"PCoA reference anchor order changed")
  # Gower double-centering against the frozen reference, NOT against the new batch.
  d2<-dnew^2
  cross_gram<--0.5*(sweep(sweep(d2,1,rowMeans(d2),"-"),2,model$reference_squared_distance_means,"-")+model$reference_squared_distance_grand_mean)
  z<-sweep(cross_gram%*%model$vectors,2,sqrt(model$values[1:2]),"/")
  rownames(z)<-rownames(dnew);colnames(z)<-c("axis1","axis2");z
}
i2_project <- function(model,x,reference_x,feature_policy) {
  assert(identical(colnames(x),colnames(reference_x)),"Feature names/order differ from frozen projection basis")
  if(model$kind=="PCA") {
    assert(identical(colnames(x),model$feature_names),"PCA feature identity mismatch")
    z<-sweep(i2_dense(x,feature_policy),2,model$center,"-")%*%model$rotation
  } else {
    assert(identical(rownames(reference_x),model$country_ids),"PCoA anchor identity mismatch")
    z<-i2_pcoa_project_distances(model,sqrt(i2_squared_distances(x,reference_x)))
  }
  colnames(z)<-c("axis1","axis2");z
}
i2_geometry_metrics <- function(x,z,model,policy) {
  valid<-apply(z,1,function(r)all(is.finite(r)))
  x<-x[valid,,drop=FALSE];z<-z[valid,,drop=FALSE]
  n<-nrow(x);d<-sqrt(i2_squared_distances(x));e<-as.matrix(stats::dist(z));mask<-upper.tri(d)
  high<-d[mask];low<-e[mask];den<-sum(high^2)
  corr<-if(length(high)>=3&&stats::sd(high)>1e-12&&stats::sd(low)>1e-12)suppressWarnings(stats::cor(high,low,method="spearman")) else NA_real_
  k<-if(n>=4L)min(5L,max(1L,floor((n-1L)/3L))) else NA_integer_
  local<-rep(NA_real_,n)
  if(!is.na(k))for(i in seq_len(n)) {
    ids<-setdiff(seq_len(n),i)
    # Report ties rather than using seed-driven random selection.
    a<-ids[order(d[i,ids],rownames(x)[ids],method="radix")][seq_len(k)]
    b<-ids[order(e[i,ids],rownames(x)[ids],method="radix")][seq_len(k)]
    local[i]<-length(intersect(a,b))/k
  }
  lambda<-pmax(model$values,0);tot<-sum(lambda);third<-if(length(lambda)>=3L)lambda[3] else 0
  list(n_current=n,n_reference=length(model$country_ids),n_pairs=length(high),
    reference_variance_retained=if(tot>0)sum(lambda[1:2])/tot else NA_real_,
    current_pairwise_energy_retained=if(den>1e-14)sum(low^2)/den else NA_real_,
    raw_distance_stress=if(den>1e-14)sqrt(sum((high-low)^2)/den) else NA_real_,
    distance_spearman=corr,neighbor_overlap=if(any(is.finite(local)))mean(local,na.rm=TRUE) else NA_real_,
    neighbor_k=k,neighbor_tie_policy="distance then ISO3; no randomized tie-breaking",
    second_to_third_eigengap=if(lambda[2]>0)(lambda[2]-third)/lambda[2] else NA_real_,
    negative_eigenvalue_mass=model$negative_eigenvalue_mass,numerical_rank=model$numerical_rank,
    no_rescaling_in_distance_stress=TRUE,diagnostics_are_not_semantic_validation=TRUE)
}
i2_projection_checks <- function(features,model,coords,collection,policy) {
  f<-features;units<-f$current_units;ref<-f$reference
  m<-i2_geometry_metrics(f$current$country$x,coords,model,policy)
  checks<-list();add<-function(id,pass,observed,criterion) {
    checks[[length(checks)+1L]]<<-list(check=id,state=if(isTRUE(pass))"pass" else "fail",observed=observed,criterion=criterion)
  }
  add("reference_sample",m$n_reference>=policy$min_reference_countries,m$n_reference,paste(">=",policy$min_reference_countries,"usable reference countries"))
  add("current_sample",m$n_current>=policy$min_current_countries,m$n_current,paste(">=",policy$min_current_countries,"usable current countries"))
  add("readable_country_count",nrow(f$current$country$x)<=policy$max_display_countries,nrow(f$current$country$x),paste("<=",policy$max_display_countries))
  add("reference_variance",is.finite(m$reference_variance_retained)&&m$reference_variance_retained>=policy$min_reference_variance_retained,m$reference_variance_retained,paste(">=",policy$min_reference_variance_retained))
  add("current_energy",is.finite(m$current_pairwise_energy_retained)&&m$current_pairwise_energy_retained>=policy$min_current_pairwise_energy_retained,m$current_pairwise_energy_retained,paste(">=",policy$min_current_pairwise_energy_retained))
  add("distance_stress",is.finite(m$raw_distance_stress)&&m$raw_distance_stress<=policy$max_raw_distance_stress,m$raw_distance_stress,paste("<=",policy$max_raw_distance_stress,"without stretching coordinates"))
  add("distance_rank_fidelity",is.finite(m$distance_spearman)&&m$distance_spearman>=policy$min_distance_spearman,m$distance_spearman,paste(">=",policy$min_distance_spearman))
  add("neighbor_fidelity",is.finite(m$neighbor_overlap)&&m$neighbor_overlap>=policy$min_neighbor_overlap,m$neighbor_overlap,paste(">=",policy$min_neighbor_overlap))
  add("subspace_eigengap",is.finite(m$second_to_third_eigengap)&&m$second_to_third_eigengap>=policy$min_second_to_third_eigengap,m$second_to_third_eigengap,paste(">=",policy$min_second_to_third_eigengap))
  add("euclidean_geometry",is.finite(m$negative_eigenvalue_mass)&&m$negative_eigenvalue_mass<=policy$pcoa_negative_eigenvalue_tolerance,m$negative_eigenvalue_mass,paste("negative mass <=",policy$pcoa_negative_eigenvalue_tolerance))
  both<-c(units,ref$units)
  lang<-tolower(vapply(both,function(u)u$language,character(1)));genre<-unique(vapply(both,function(u)u$genre,character(1)))
  add("metadata_comparability",all(lang%in%c("en","english"))&&length(genre)==1L&&!genre%in%c("","unspecified"),paste(unique(lang),paste(genre,collapse="|"),collapse="; "),"known English source metadata and one genre across reference/current")
  classes<-unique(vapply(both,function(u)u$eligibility_class,character(1)))
  add("observed_source_scope",identical(classes,"observed_input"),paste(classes,collapse="|"),"reference AND current must be observed_input; replay/engineering is audit-only")
  nflags<-sum(vapply(both,function(u)length(unlist(u$flags)),integer(1)))+length(collection$errors)
  add("source_flags",nflags==0L,nflags,"zero source flags/collection errors for automatic map publication")
  cur<-f$current$statement$rows;rr<-ref$features$statement$rows
  add("nonzero_coverage",all(cur$nonzero)&&all(rr$nonzero),sum(!cur$nonzero)+sum(!rr$nonzero),"all contributing current and reference statements have nonzero features")
  oo<-cur$oov_fraction
  add("oov_coverage",length(oo)>0L&&all(is.finite(oo))&&max(oo)<=policy$max_statement_oov_fraction,if(length(oo)&&all(is.finite(oo)))max(oo) else NA_real_,paste("maximum current eligible-token OOV <=",policy$max_statement_oov_fraction))
  minwords<-min(c(cur$eligible_tokens,rr$eligible_tokens))
  add("text_support",is.finite(minwords)&&minwords>=policy$min_statement_eligible_tokens,minwords,paste("each contributing statement >=",policy$min_statement_eligible_tokens,"eligible tokens"))
  crossdup<-function(us){h<-vapply(us,function(u)u$text_sha256,character(1));is<-vapply(us,function(u)u$iso3,character(1));sum(vapply(split(is,h),function(x)length(unique(x))>1L,logical(1)))}
  du<-crossdup(units)+crossdup(ref$units)
  add("duplicate_coverage",du==0L,du,"zero exact text shared by distinct countries within either snapshot")
  d<-rows_frame(checks,c("check","state","observed","criterion"))
  list(metrics=m,checks=d,passed=all(d$state=="pass"),policy=policy,
       display_release_only=TRUE,no_claim_of_political_alignment_or_inferential_validity=TRUE)
}
i2_projection_model <- function(features,id,root,clock=utc_now) {
  pp<-i2_policy(root,"projection");ref<-features$reference;fp<-ref$policy
  rows<-ref$features$country$rows
  good<-rows$nonzero&as.numeric(rows$zero_statements)==0L
  x<-ref$features$country$x[good,,drop=FALSE]
  if(nrow(x)<3L)i2_abort("data","Fewer than three complete nonzero reference country vectors; no artificial coordinates created")
  fitted<-if(id=="M05")i2_pca_fit(x,pp,fp) else i2_pcoa_fit(sqrt(i2_squared_distances(x)),pp)
  fitted$reference_id<-ref$reference_id;fitted$reference_indices<-which(good)
  fitted$policy<-pp;fitted$policy_hash<-sha_object(pp);fitted$fitted_at<-clock()
  fitted$feature_names<-colnames(x);fitted$environment<-i2_env_signature();fitted$implementation_signature<-i2_projection_signature()
  fitted$model_id<-sha_object(fitted)
  fitted
}
i2_validate_projection_model <- function(model,features,policy) {
  ref<-features$reference
  assert(identical(model$model_id,sha_object(model[setdiff(names(model),"model_id")]))&&
    identical(model$reference_id,ref$reference_id)&&identical(model$policy,policy),"Frozen projection identity/policy mismatch")
  assert(identical(model$environment,i2_env_signature())&&identical(model$implementation_signature,i2_projection_signature())&&identical(model$policy_hash,sha_object(policy)),"Frozen projection runtime/implementation/policy mismatch")
  ids<-which(ref$features$country$rows$nonzero&as.numeric(ref$features$country$rows$zero_statements)==0L)
  assert(identical(ids,model$reference_indices),"Frozen reference coverage changed")
  x<-i2_dense(ref$features$country$x[ids,,drop=FALSE],ref$policy);center<-colMeans(x);xc<-sweep(x,2,center,"-")
  spectrum<-eigen(tcrossprod(xc),symmetric=TRUE,only.values=TRUE)$values
  tol<-1e-8*max(1,max(abs(spectrum)))
  positive<-sort(pmax(spectrum,0),decreasing=TRUE);mv<-sort(pmax(model$values,0),decreasing=TRUE)
  # prcomp can have only min(n,p) singular values; remaining eigenvalues are zero.
  mv<-c(mv,rep(0,max(0,length(positive)-length(mv))))
  assert(length(mv)==length(positive)&&max(abs(mv-positive))<=tol,"Frozen eigenvalues fail independent Gram-spectrum check")
  assert(identical(model$country_ids,rownames(x))&&identical(model$feature_names,colnames(x)),"Projection source/feature labels changed")
  if(model$kind=="PCA") {
    assert(max(abs(model$center-center))<1e-10,"PCA no longer uses frozen reference center")
    z<-xc%*%model$rotation
    assert(max(abs(crossprod(model$rotation)-diag(2)))<1e-8,"PCA loadings are not orthonormal")
    assert(max(abs(crossprod(xc,z)-sweep(model$rotation,2,model$values[1:2],"*")))<tol,"PCA loading/eigenvalue equation fails")
  } else {
    d2<-i2_squared_distances(x);b<-tcrossprod(xc)
    assert(max(abs(model$reference_squared_distance_means-rowMeans(d2)))<tol&&abs(model$reference_squared_distance_grand_mean-mean(d2))<tol,"PCoA centering constants changed")
    assert(max(abs(crossprod(model$vectors)-diag(2)))<1e-8,"PCoA eigenvectors are not orthonormal")
    assert(max(abs(b%*%model$vectors-sweep(model$vectors,2,model$values[1:2],"*")))<tol,"PCoA eigen equation fails")
    z<-sweep(model$vectors,2,sqrt(model$values[1:2]),"*")
  }
  assert(max(abs(z-model$coordinates))<tol,"Stored reference coordinates are inconsistent")
  assert(parse_utc(model$fitted_at)>=parse_utc(ref$frozen_at),"Projection fit predates its reference")
  invisible(TRUE)
}
i2_projection_execute <- function(features,cp,root,run,id,clock=utc_now) {
  assert(id%in%c("M05","M06"),"Unsupported projection adapter")
  pp<-i2_policy(root,"projection");fp<-features$reference$policy
  home<-file.path(root,relative_path(cp$config$analytics$projection_reference_dir));dir.create(home,recursive=TRUE,showWarnings=FALSE)
  key<-sha_object(list(method=id,reference_id=features$fitted_reference_id,policy=pp,environment=i2_env_signature(),implementation=I2_PROJECTION_SCHEMA,code=i2_projection_signature()))
  file<-file.path(home,paste0(id,"_",key,".rds"));hashpath<-paste0(file,".sha256")
  if(file.exists(file)||file.exists(hashpath)) {
    assert(file.exists(file)&&file.exists(hashpath)&&identical(sha_file(file),trimws(read_text(hashpath))),"Projection cache corrupt; not silently refitted")
    model<-readRDS(file);i2_validate_projection_model(model,features,pp)
    assert(parse_utc(model$fitted_at)<=parse_utc(clock()),"Future projection model rejected")
    op<-"reused_reference_fit"
  } else {
    model<-i2_projection_model(features,id,root,clock);i2_validate_projection_model(model,features,pp)
    immutable_write(file,serialize(model,NULL,version=3));immutable_write(hashpath,charToRaw(paste0(sha_file(file),"\n")))
    op<-"fitted_reference_model"
  }
  refx<-features$reference$features$country$x[model$reference_indices,,drop=FALSE]
  now<-features$current$country
  z<-matrix(NA_real_,nrow(now$x),2,dimnames=list(rownames(now$x),c("axis1","axis2")))
  good<-now$rows$nonzero&as.numeric(now$rows$zero_statements)==0L
  if(any(good))z[good,]<-i2_project(model,now$x[good,,drop=FALSE],refx,fp)
  checks<-i2_projection_checks(features,model,z,cp$brief$collection,pp)
  list(schema=I2_PROJECTION_SCHEMA,method_id=id,model=model,reference_operation=op,
    feature_artifact_sha256=sha_object(features),source_snapshot_id=features$source_snapshot_id,
    input_identity=features$input_identity,coordinates=z,quality=checks,
    comparison_mode=if(setequal(vapply(features$current_units,function(u)u$observation_version_id,character(1)),
                               vapply(features$reference$units,function(u)u$observation_version_id,character(1))))"cross_sectional_bootstrap" else "fixed_reference_projection",
    created_at=clock(),publication_role=if(id=="M05")"primary_candidate" else "audit_challenger")
}
i2_validate_projection <- function(v,features,cp,root) {
  assert(identical(v$schema,I2_PROJECTION_SCHEMA)&&v$method_id%in%c("M05","M06"),"Invalid projection artifact")
  assert(identical(v$feature_artifact_sha256,sha_object(features))&&identical(v$input_identity,features$input_identity)&&
    identical(v$source_snapshot_id,features$source_snapshot_id),"Projection and feature/source identities differ")
  pp<-i2_policy(root,"projection");i2_validate_projection_model(v$model,features,pp)
  assert(v$model$kind==if(v$method_id=="M05")"PCA" else "PCoA","Projection adapter/type mismatch")
  new<-features$current$country;good<-new$rows$nonzero&as.numeric(new$rows$zero_statements)==0L
  z<-matrix(NA_real_,nrow(new$x),2,dimnames=list(rownames(new$x),c("axis1","axis2")))
  refx<-features$reference$features$country$x[v$model$reference_indices,,drop=FALSE]
  if(any(good))z[good,]<-i2_project(v$model,new$x[good,,drop=FALSE],refx,features$reference$policy)
  assert(isTRUE(all.equal(v$coordinates,z,tolerance=1e-10)),"Projection coordinates fail frozen-reference recomputation")
  q<-i2_projection_checks(features,v$model,z,cp$brief$collection,pp)
  assert(identical(q,v$quality),"Projection-quality gate record differs from recomputed diagnostics")
  assert(parse_utc(v$created_at)>=parse_utc(v$model$fitted_at),"Projection result predates its model")
  invisible(TRUE)
}
i2_projection_rows <- function(v,features) {
  d<-features$current$country$rows;d$axis1<-v$coordinates[,1];d$axis2<-v$coordinates[,2]
  d$reference_id<-features$fitted_reference_id;d$model_id<-v$model$model_id
  d$display_state<-if(v$method_id=="M05"&&v$quality$passed)"eligible_primary" else "audit_only"
  total<-sum(pmax(v$model$values,0));d$axis1_fraction<-v$model$values[1]/total;d$axis2_fraction<-v$model$values[2]/total
  d$projection<-v$model$kind;d$mode<-v$comparison_mode
  d
}
i2_write_projection_tables <- function(v,features,run) {
  prefix<-if(v$method_id=="M05")"pca" else "pcoa"
  d<-i2_projection_rows(v,features);total<-sum(pmax(v$model$values,0))
  csv_write(file.path(run,paste0("data/",prefix,"_country_coordinates.csv")),d)
  csv_write(file.path(run,paste0("data/",prefix,"_display_checks.csv")),v$quality$checks)
  csv_write(file.path(run,paste0("data/",prefix,"_spectrum.csv")),data.frame(component=seq_along(v$model$values),eigenvalue=v$model$values,share=pmax(v$model$values,0)/total))
  json_write(file.path(run,paste0("audit/analytics/",prefix,"_diagnostics.json")),v$quality)
  if(v$model$kind=="PCA")csv_write(file.path(run,"data/pca_loadings.csv"),data.frame(term=v$model$feature_names,PC1=v$model$rotation[,1],PC2=v$model$rotation[,2]))
  else csv_write(file.path(run,"data/pcoa_reference_eigenvectors.csv"),data.frame(iso3=v$model$country_ids,axis1=v$model$vectors[,1],axis2=v$model$vectors[,2]))
}
