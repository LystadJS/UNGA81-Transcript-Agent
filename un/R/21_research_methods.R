# I5 bounded lexical research methods. No method in this module can publish O1-O5.
I5_IDS <- c("M08", "M31", "M32", "M33", "M34", "M36")
# Version 2 materializes ALTREP vectors: inspecting/writing a table must not change
# its content identity merely by forcing a lazy R representation.
i5_hash <- function(value) sha_raw(serialize(value,NULL,version=2))
i5_policy <- function() list(schema="D1-I5-research-v1", seed=29092026L,
  k=2:6, resolutions=c(.5,1,1.5), seeds=c(11L,23L,37L), starts=25L,
  iterations=100L, replicates=30L, retain=.8, min_size=3L,
  min_silhouette=.15, min_ari=.75, min_success=.9,
  min_countries=6L, max_countries=250L, max_cells=2500000L,
  cosine_threshold=.2, eigengap=1e-8, publication_eligible=FALSE)

i5_matrix <- function(x, p=i5_policy()) {
  if(!is.matrix(x) || !is.numeric(x) || !all(is.finite(x))) i2_abort("data","Features must be a finite numeric matrix")
  if(nrow(x)<p$min_countries) i2_abort("data","At least six countries are needed")
  if(nrow(x)>p$max_countries || length(x)>p$max_cells) i2_abort("resources","I5 matrix limits exceeded")
  assert(ncol(x)>0L && !is.null(rownames(x)) && all(nzchar(rownames(x))) && !anyDuplicated(rownames(x)),"Missing/duplicate country identifiers")
  assert(all(x>=0),"I5 accepts nonnegative TF-IDF, not arbitrary embeddings or signed stance data")
  assert(all(abs(rowSums(x*x)-1)<1e-7),"Every country vector must be nonzero and L2 normalized; never impute missing vectors")
  x
}

i5_adjacency <- function(x, p=i5_policy()) {
  a<-tcrossprod(x);a[]<-pmin(1,pmax(0,a));diag(a)<-0
  a[a<p$cosine_threshold]<-0
  a
}
i5_graph <- function(a) {
  assert(is.matrix(a)&&nrow(a)==ncol(a)&&all(is.finite(a))&&all(a>=0)&&
    max(abs(a-t(a)))<1e-10&&all(diag(a)==0),"Invalid undirected nonnegative graph")
  igraph::graph_from_adjacency_matrix(a,mode="undirected",weighted=TRUE,diag=FALSE)
}
i5_kmeans <- function(x,k,seed,p) hc_with_seed(seed,function() {
  if(nrow(unique(x))<k)stop("Fewer distinct vectors than requested clusters")
  fit<-withCallingHandlers(stats::kmeans(x,centers=k,nstart=p$starts,iter.max=p$iterations,algorithm="Lloyd"),
    warning=function(w)stop(paste("K-means fit warning:",conditionMessage(w)),call.=FALSE))
  assert(fit$iter<=p$iterations && (is.null(fit$ifault)||fit$ifault==0L),"K-means did not converge")
  setNames(as.integer(fit$cluster),rownames(x))
})
i5_partition <- function(id,x,a,parameter,seed,p) {
  if(id=="M08")return(i5_kmeans(x,as.integer(parameter),seed,p))
  g<-i5_graph(a)
  if(igraph::ecount(g)==0L)stop("No eligible edges")
  if(id=="M34") {
    k<-as.integer(parameter);degree<-rowSums(a)
    assert(all(degree>0),"Spectral clustering withheld with isolated nodes; no silent node removal")
    assert(igraph::components(g)$no<=k,"Requested spectral dimension is smaller than the number of components")
    e<-eigen(a/sqrt(outer(degree,degree)),symmetric=TRUE)
    assert(k<nrow(a) && e$values[k]-e$values[k+1L]>p$eigengap,"Spectral subspace boundary is degenerate")
    u<-e$vectors[,seq_len(k),drop=FALSE];rownames(u)<-rownames(x)
    norms<-sqrt(rowSums(u*u));assert(all(norms>1e-12),"Undefined spectral row normalization")
    return(i5_kmeans(u/norms,k,seed,p))
  }
  hc_with_seed(seed,function() {
    fit<-if(id=="M32")igraph::cluster_louvain(g,weights=igraph::E(g)$weight,resolution=parameter) else {
      assert(id=="M33","Unknown community method")
      igraph::cluster_leiden(g,objective_function="modularity",weights=igraph::E(g)$weight,
        resolution=parameter,n_iterations=10L)
    }
    setNames(as.integer(igraph::membership(fit)),rownames(x))
  })
}

i5_compute <- function(id,x,p=i5_policy()) {
  assert(id%in%I5_IDS,"Unknown I5 method")
  if(id!="M08" && utils::packageVersion("igraph") < "2.1.0") i2_abort("dependency","I5 graph methods require igraph >= 2.1.0")
  x<-i5_matrix(x,p);a<-i5_adjacency(x,p)
  if(id=="M31")return(list(kind="lexical_similarity_only",adjacency=a,
    pairwise_coverage=matrix(TRUE,nrow(x),nrow(x),dimnames=list(rownames(x),rownames(x))),
    edge_definition=paste("Undirected cosine >=",p$cosine_threshold,"on full frozen country TF-IDF; no self edges"),
    stance_layer=list(status="blocked_labels",reason="No proposition-specific human-reviewed stance data; lexical edges are not stance agreement"),
    diplomatic_interaction_layer=list(status="blocked_data",reason="No observed relational events")))
  if(id=="M36") {
    g<-i5_graph(a);w<-igraph::E(g)$weight
    return(list(kind="single_snapshot_lexical_network_metrics",adjacency=a,
      nodes=data.frame(iso3=rownames(x),degree=as.numeric(igraph::degree(g)),
        strength=as.numeric(igraph::strength(g,weights=w)),
        betweenness=as.numeric(igraph::betweenness(g,directed=FALSE,weights=if(length(w))1/w else numeric(),normalized=FALSE))),
      components=igraph::components(g)$no,edge_count=igraph::ecount(g),
      density=igraph::edge_density(g,loops=FALSE),path_length_definition="Inverse positive cosine edge weight",
      temporal_change=list(status="blocked_history",reason="No matched prior graph; single-snapshot metrics only")))
  }
  dis<-stats::dist(x);parameters<-if(id%in%c("M08","M34"))p$k[p$k<nrow(x)] else p$resolutions
  candidates<-fits<-list();idx<-0L
  for(parameter in parameters)for(seed in p$seeds) {
    idx<-idx+1L;key<-paste(parameter,seed,sep="_");error<-""
    groups<-tryCatch(i5_partition(id,x,a,parameter,seed,p),error=function(e){error<<-conditionMessage(e);NULL})
    k<-if(is.null(groups))0L else length(unique(groups));sil<-NA_real_
    if(k>1L&&k<nrow(x))sil<-mean(cluster::silhouette(groups,dis)[,"sil_width"])
    modularity<-if(!is.null(groups)&&id!="M08"&&sum(a)>0)igraph::modularity(i5_graph(a),groups,weights=igraph::E(i5_graph(a))$weight) else NA_real_
    candidates[[idx]]<-data.frame(candidate=key,parameter=parameter,seed=seed,groups=k,
      min_size=if(is.null(groups))0L else min(table(groups)),silhouette=sil,modularity=modularity,
      state=if(is.null(groups))"failed" else "executed",reason=error,selected=FALSE)
    fits[[key]]<-groups
  }
  candidates<-do.call(rbind,candidates)
  valid<-which(candidates$state=="executed" & is.finite(candidates$silhouette))
  if(!length(valid))i2_abort("data",paste("No evaluable",id,"partition:",paste(unique(candidates$reason),collapse="; ")))
  admissible<-valid[candidates$min_size[valid]>=p$min_size]
  pool<-if(length(admissible))admissible else valid
  # A common full-feature silhouette score selects across all preregistered candidates.
  selected<-pool[order(-candidates$silhouette[pool],candidates$parameter[pool],candidates$seed[pool])][1]
  candidates$selected[selected]<-TRUE;winner<-candidates[selected,];groups<-fits[[winner$candidate]]
  samples<-hc_with_seed(p$seed,function()replicate(p$replicates,sort(sample.int(nrow(x),floor(nrow(x)*p$retain))),simplify=FALSE))
  repeats<-lapply(seq_along(samples),function(i){
    keep<-samples[[i]];error<-""
    refit<-tryCatch(i5_partition(id,x[keep,,drop=FALSE],a[keep,keep,drop=FALSE],winner$parameter,p$seed+i,p),error=function(e){error<<-conditionMessage(e);NULL})
    # Degenerate restricted partitions are not evidence of stable nontrivial clusters.
    evaluable<-!is.null(refit)&&length(unique(refit))>1L&&length(unique(groups[keep]))>1L
    data.frame(replicate=i,n=length(keep),state=if(evaluable)"executed" else "not_evaluable",
      ari=if(evaluable)hc_ari(groups[keep],refit) else NA_real_,reason=if(evaluable)"" else if(nzchar(error))error else "Degenerate partition")
  })
  repeats<-do.call(rbind,repeats);success<-mean(repeats$state=="executed")
  ari<-if(any(is.finite(repeats$ari)))mean(repeats$ari[is.finite(repeats$ari)]) else NA_real_
  quality<-isTRUE(length(admissible)>0L&&winner$silhouette>=p$min_silhouette&&success>=p$min_success&&ari>=p$min_ari)
  list(kind="research_partition",adjacency=if(id=="M08")NULL else a,candidates=candidates,
    partitions=fits,selected_id=winner$candidate,groups=groups,
    assignments=data.frame(iso3=names(groups),group=unname(groups)),resample_plan=samples,
    resamples=repeats,successful_fraction=success,mean_ari=ari,engineering_pass=quality,
    explanation="Roster-deletion sensitivity is not uncertainty coverage, political validation, or permission to publish")
}

i5_source_quality <- function(f,collection) {
  u<-c(f$current_units,f$reference$units)
  all(vapply(u,function(z)identical(z$eligibility_class,"observed_input")&&identical(z$language,"en")&&
    nzchar(z$genre)&&z$genre!="unspecified"&&!length(unlist(z$flags)),logical(1)))&&
    length(unique(vapply(u,`[[`,character(1),"genre")))==1L&&!length(collection$errors)&&
    all(f$current$statement$rows$nonzero)&&all(f$current$statement$rows$oov_fraction<=.35)&&
    all(f$current$statement$rows$eligible_tokens>=30L)&&
    !any(vapply(split(vapply(f$current_units,`[[`,character(1),"iso3"),vapply(f$current_units,`[[`,character(1),"text_sha256")),function(v)length(unique(v))>1L,logical(1)))
}
i5_execute <- function(id,f,root,collection=list(errors=list()),clock=utc_now) {
  i2_validate_features(f,root=root)
  p<-i5_policy();s<-dim(f$current$country$x)
  if(prod(s)>p$max_cells||s[1]>p$max_countries)i2_abort("resources","I5 refuses oversized dense features before allocation")
  n<-i5_compute(id,as.matrix(f$current$country$x),p)
  out<-list(schema=p$schema,method_id=id,policy=p,feature_sha256=sha_object(f),
    snapshot_id=f$source_snapshot_id,reference_id=f$fitted_reference_id,collection=collection,
    created_at=clock(),numerical=n,source_quality_pass=isTRUE(i5_source_quality(f,collection)),
    publication_eligible=FALSE,model_release_status="audit_only",
    environment=list(R=as.character(getRversion()),igraph=if(id=="M08")"unused" else as.character(utils::packageVersion("igraph"))))
  out$result_id<-i5_hash(out);out
}
i5_validate <- function(v,f,root,recompute=TRUE) {
  i2_validate_features(f,root=root)
  assert(v$method_id%in%I5_IDS&&identical(v$schema,i5_policy()$schema)&&identical(v$policy,i5_policy()),"I5 identity or policy mismatch")
  assert(identical(v$publication_eligible,FALSE)&&identical(v$model_release_status,"audit_only"),"I5 cannot publish")
  assert(identical(v$feature_sha256,sha_object(f))&&identical(v$snapshot_id,f$source_snapshot_id)&&identical(v$reference_id,f$fitted_reference_id),"I5 feature/source binding mismatch")
  assert(identical(v$result_id,i5_hash(v[setdiff(names(v),"result_id")])),"I5 content fingerprint mismatch")
  assert(identical(v$environment,list(R=as.character(getRversion()),igraph=if(v$method_id=="M08")"unused" else as.character(utils::packageVersion("igraph")))),"I5 runtime changed; reproduce with its recorded environment")
  assert(identical(v$source_quality_pass,isTRUE(i5_source_quality(f,v$collection))),"Forged I5 source quality")
  assert(parse_utc(v$created_at)>=parse_utc(f$created_at),"I5 result precedes its feature artifact")
  if(recompute)assert(identical(v$numerical,i5_compute(v$method_id,as.matrix(f$current$country$x),v$policy)),"I5 numerical result differs from independent recomputation")
  invisible(TRUE)
}

i5_gates <- function(id,v,f,error="") {
  mk<-function(ok,cls,reason)list(state=if(isTRUE(ok))"pass" else "fail",blocker_class=cls,reason=reason)
  feature<-!is.null(f);g<-list()
  if(id=="M08")g$numeric_features<-mk(feature,"data","Full frozen M02 country vectors required")
  else if(id%in%c("M31","M36")) {
    g$pairwise_coverage<-mk(feature&&!is.null(v),"data","One explicit full country roster; missing vectors block execution")
    g$edge_definition<-mk(!is.null(v),"version","Versioned lexical cosine threshold; no stance or diplomatic-event edges inferred")
    g[[if(id=="M31")"representation_consistent" else "matched_node_set"]]<-mk(feature&&!is.null(v),"version","All nodes use the same current frozen M02 basis; no temporal comparison claimed")
  } else g$valid_nonnegative_graph<-mk(feature&&!is.null(v),"data","Finite symmetric nonnegative graph with zero diagonal; lexical layer only")
  if(id%in%c("M08","M32","M33","M34"))g[[if(id=="M08")"cluster_stability" else "network_stability"]]<-
    mk(!is.null(v)&&isTRUE(v$numerical$engineering_pass)&&isTRUE(v$source_quality_pass),"quality",
      if(is.null(v))paste("No evaluated partition.",error) else if(isTRUE(v$numerical$engineering_pass)&&isTRUE(v$source_quality_pass))"Engineering and source checks passed; remains audit-only" else "Engineering/source screens failed; candidate retained only for audit")
  g
}
i5_run_managed <- function(id,cp,root,run,snapshot,context,available,clock=utc_now) {
  f<-v<-NULL;artifact_ref<-artifact_hash<-artifact_time<-error_log<-error<-"";status<-"failed"
  tryCatch({
    if(!all(available))i2_abort("dependency","I5 method packages unavailable; see dependency ledger")
    f<-i2_read_feature_dependency(run)
    if(is.null(f))i2_abort("data","No M02 feature artifact")
    i2_validate_features(f,cp,root);assert(identical(f$source_snapshot_id,snapshot$snapshot_id),"I5 snapshot mismatch")
    v<-i5_execute(id,f,root,cp$brief$collection,clock);i5_validate(v,f,root)
    gr<-i5_gates(id,v,f)
    status<-if(all(vapply(gr,function(z)z$state=="pass",logical(1))))"executed" else "withheld_quality"
    artifact_ref<-paste0("audit/analytics/artifacts/",id,".rds");bytes<-serialize(v,NULL,version=3)
    immutable_write(file.path(run,artifact_ref),bytes);artifact_hash<-sha_raw(bytes);artifact_time<-v$created_at
    for(name in c("candidates","assignments","resamples","nodes"))if(!is.null(v$numerical[[name]]))
      csv_write(file.path(run,"audit/research",paste0(id,"_",name,".csv")),v$numerical[[name]])
    if(!is.null(v$numerical$adjacency))csv_write(file.path(run,"audit/research",paste0(id,"_adjacency.csv")),data.frame(iso3=rownames(v$numerical$adjacency),v$numerical$adjacency,check.names=FALSE))
  },error=function(e){
    error<<-conditionMessage(e);kind<-class(e)[startsWith(class(e),"d1_i2_")]
    status<<-if(length(kind))paste0("blocked_",sub("d1_i2_","",kind[1])) else "failed"
    # A rejected dependency must not subsequently be asserted to be valid proof.
    f<<-NULL;v<<-NULL;artifact_ref<<-artifact_hash<<-artifact_time<<-""
    error_log<<-paste0("audit/analytics/errors/",id,".txt");write_text(file.path(run,error_log),error)
  })
  gr<-i5_gates(id,v,f,error);ref<-paste0("audit/analytics/method_proofs/",id,".json")
  proof<-list(schema="D1-I5-proof-v1",method_id=id,context=context,artifact_ref=artifact_ref,artifact_sha256=artifact_hash,
    feature_artifact_ref=if(is.null(f))"" else "audit/analytics/artifacts/M02.rds",feature_artifact_sha256=if(is.null(f))"" else sha_object(f),error=error,gates=gr)
  json_write(file.path(run,ref),proof)
  rows<-lapply(names(gr),function(g)c(list(method_id=id,gate=g),gr[[g]],list(evidence_path=ref,evidence_sha256=sha_file(file.path(run,ref)))))
  list(status=status,reason=if(is.null(v))paste("No I5 result:",error) else paste(id,"lexical research computation retained;",if(status=="withheld_quality")"quality screens failed;" else "", "audit-only, not diplomatic alignment"),
    stage=if(is.null(v))"preflight_or_fit_failed" else "fit_and_source_bound_validation",fit_status=if(is.null(v))"blocked" else "current_snapshot_research",
    artifact_ref=artifact_ref,artifact_hash=artifact_hash,artifact_time=artifact_time,error_log=error_log,gr=rows,value=v,model_release_status="audit_only")
}
i5_validate_proof <- function(proof,run,root=getOption("unbrief.root",getwd())) {
  id<-proof$method_id;assert(id%in%I5_IDS,"Invalid I5 proof method");f<-v<-NULL
  if(nzchar(proof$feature_artifact_ref)) {
    assert(identical(proof$feature_artifact_ref,"audit/analytics/artifacts/M02.rds"),"Invalid I5 feature path")
    path<-file.path(run,proof$feature_artifact_ref);assert(identical(sha_file(path),proof$feature_artifact_sha256),"I5 dependency tampering")
    f<-readRDS(path);i2_validate_features(f,root=root);assert(identical(f$source_snapshot_id,proof$context$snapshot_id),"I5 proof snapshot mismatch")
  }
  if(nzchar(proof$artifact_ref)) {
    assert(!is.null(f)&&identical(proof$artifact_ref,paste0("audit/analytics/artifacts/",id,".rds")),"Invalid I5 artifact path")
    path<-file.path(run,proof$artifact_ref);assert(identical(sha_file(path),proof$artifact_sha256),"I5 artifact tampering")
    v<-readRDS(path);assert(identical(v$method_id,id),"I5 method substitution");i5_validate(v,f,root)
  }
  expected<-i5_gates(id,v,f,str1(proof$error));assert(identical(expected,proof$gates),"I5 proof contradicts recomputed evidence");expected
}
