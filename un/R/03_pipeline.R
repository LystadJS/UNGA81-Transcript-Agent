# Run preparation and versioned, immutable per-date outputs.
load_config <- function(path) {
  cfg<-json_read(path);assert(cfg$schema_version==1,"Unsupported configuration schema")
  assert(cfg$timezone=="America/New_York","This version uses America/New_York reporting dates")
  assert(cfg$analysis_mode %in% c("openai","extractive"),"Unknown analysis_mode")
  assert(cfg$storage$output_dir=="output","This version requires output_dir=output")
  assert(cfg$live$base_url=="https://transcripts.un.org"&&cfg$model$endpoint=="https://api.openai.com/v1/responses","Unexpected API host")
  for(k in c("max_calls_per_run","max_output_tokens","max_input_chars_per_country"))assert(is.numeric(cfg$model[[k]])&&cfg$model[[k]]>0&&cfg$model[[k]]==floor(cfg$model[[k]]),paste("Invalid model limit",k))
  assert(cfg$email$max_image_width>0&&cfg$email$max_image_width<=840,"Figure display width must be <=840")
  for(k in c("output_dir","cache_dir"))assert(!grepl("^/|^[A-Za-z]:|(^|[/\\\\])\\.\\.([/\\\\]|$)",cfg$storage[[k]]),"Storage paths must stay within workflow")
  cfg$display<-cfg$display %||% list(group_by="region",region_order=as.list(REGION_ORDER),country_order="alphabetical",fixed_issue_order=as.list(FIXED_ISSUE_IDS))
  assert(identical(cfg$display$group_by,"region")&&identical(cfg$display$country_order,"alphabetical"),"Readouts must group by region and alphabetize within each region")
  assert(identical(unlist(cfg$display$fixed_issue_order,use.names=FALSE),FIXED_ISSUE_IDS),"Fixed topics must be Iran, Cuba, Ukraine, AI in that order")
  regions<-unlist(cfg$display$region_order,use.names=FALSE)
  assert(is.character(regions)&&length(regions)>0&&!anyDuplicated(regions)&&all(nzchar(regions)),"Invalid regional display order")
  validate_analytics_config(cfg)
  cfg
}
verify_replay_sources <- function(sample,speeches) {
  archive<-file.path(sample,"original_sources.zip");info<-safe_zip(archive)
  dir<-tempfile();dir.create(dir);on.exit(unlink(dir,recursive=TRUE))
  utils::unzip(archive,exdir=dir)
  for(s in speeches){path<-file.path(dir,s$source_file);assert(file.exists(path)&&identical(sha_file(path),s$source_sha256),paste("Original source hash mismatch:",s$country))}
  invisible(length(speeches))
}
prepare_run <- function(root,run,cfg,source,day,input="",prepared_at="",budget=NULL,fetch=http_raw) {
  registry<-load_registry(file.path(root,"config/countries.csv"));book_path<-if(source=="replay")file.path("examples",day,"legacy_codebook.json") else "config/issue_codebook.json";book<-json_read(file.path(root,book_path));current_book<-validate_issue_book(json_read(file.path(root,"config/issue_codebook.json")));archive<-new_archive(run)
  json_write(file.path(run,"config_used.json"),cfg);json_write(file.path(run,"audit/codebook.json"),book)
  code_paths<-c("run_daily.R","rebuild.R","history_tool.R","reference_tool.R",paste0("R/",list.files(file.path(root,"R"),pattern="\\.R$")),paste0("prompts/",list.files(file.path(root,"prompts"))),paste0("schemas/",list.files(file.path(root,"schemas"))),"templates/email_head.html","assets/USUN_Seal.png","config/countries.csv","config/issue_codebook.json","config/hierarchical_policy.json","design/D1-HC/hierarchical_policy.json")
  code_paths<-unique(c(code_paths,book_path,"config/method_registry.csv","config/email_contract.json","config/email_policy.R","config/data_contracts.json","config/dispatch_policy.json","config/feature_policy.json","config/projection_policy.json","design/D1-I2/feature_policy.json","design/D1-I2/projection_policy.json"))
  csv_write(file.path(run,"code_manifest.csv"),data.frame(path=code_paths,sha256=vapply(file.path(root,code_paths),sha_file,character(1))))
  analyses<-list();speeches<-list();observations<-list();collection<-list()
  if(source=="replay") {
    sample<-file.path(root,"examples",day);assert(dir.exists(sample),"No bundled replay for this date")
    speeches<-json_read(file.path(sample,"speeches.json"));analyses<-json_read(file.path(sample,"analyses.json"));snapshot<-json_read(file.path(sample,"snapshot.json"))
    for(p in c("speeches.json","analyses.json","snapshot.json","legacy_codebook.json","legacy_codebook_original.csv"))archive_store(archive,read_bytes(file.path(sample,p)),p)
    assert(length(speeches)==snapshot$country_count,"Replay country count mismatch")
    verify_replay_sources(sample,speeches)
    archive_store(archive,read_bytes(file.path(sample,"original_sources.zip")),"original_sources.zip","zip")
    acquired<-utc_now()
    observations<-lapply(speeches,function(s)observation_enrich(normalized_speech(s,registry),"replay",acquired))
    for(s in speeches){assert(s$date==day,"Replay date mismatch");normalized_speech(s,registry);validate_analysis(analyses[[s$iso3]],s,book,inherited=TRUE)}
    upgraded<-upgrade_replay_topics(analyses,speeches,book,current_book)
    analyses<-upgraded$analyses;book<-upgraded$codebook
    collection<-list(status="REPLAY",source_mode="replay",errors=list(),excluded=list(),coverage_note=snapshot$source,coding_note="Replay: the original 10 issue decisions and summaries are preserved. Iran, Cuba and AI use a provisional full-text lexicon scan; no-hit remains unresolved. Ukraine retains its original v1 Russia-Ukraine scope. This mixed-version example is not a fresh semantic review and must not be pooled with fresh v2.1 coding without recoding.")
  } else {
    if(source=="local"){assert(nzchar(input),"--input is required for local mode");result<-collect_local(input,day,registry,archive)} else result<-collect_live(day,registry,archive,cfg,fetch)
    acquired<-utc_now()
    observations<-lapply(result$speeches,function(s)observation_enrich(s,source,acquired))
    json_write(file.path(run,"audit/observations.json"),observations)
    grouped<-group_countries(observations);speeches<-grouped$speeches;collection<-result$collection;collection$duplicates<-grouped$duplicates
    assert(length(speeches)<=cfg$generation$max_countries,"Country count exceeds configured limit")
    if(source=="live"&&!length(speeches)&&(collection$in_scope_meetings %||% 0)>0)collection$errors<-c(collection$errors,list(list(error="In-scope meetings found but no qualifying country statements extracted; inspect exclusions.")))
    json_write(file.path(run,"audit/speeches.json"),speeches);json_write(file.path(run,"audit/collection.json"),collection)
    if(length(speeches)&&cfg$analysis_mode=="openai") {
      assert(isTRUE(cfg$allow_external_ai),"External AI disabled. Sources archived; authorize public-source processing or use extractive mode")
      assert(nzchar(Sys.getenv("OPENAI_API_KEY")),"OPENAI_API_KEY missing; sources archived")
    }
    client<-new_model_client(root,cfg,run,fetch,budget)
    for(j in seq_along(speeches)) {
      s<-speeches[[j]];cat(sprintf("Analyze %d/%d: %s\n",j,length(speeches),s$country))
      a<-tryCatch({x<-if(cfg$analysis_mode=="extractive")extractive_analysis(s,book) else model_analyze(client,s,book);validate_analysis(x,s,book)},error=function(e)e)
      if(inherits(a,"error")){message<-conditionMessage(a);collection$errors<-c(collection$errors,list(list(source=s$country,error=message,stage="analysis")));a<-failed_analysis(book,message)}
      analyses[[s$iso3]]<-a;json_write(file.path(run,"audit/analyses_checkpoint.json"),analyses)
    }
    if(length(collection$errors))collection$status<-"PARTIAL"
  }
  speeches<-order_country_readouts(speeches,cfg)
  json_write(file.path(run,"audit/observations.json"),observations)
  json_write(file.path(run,"audit/codebook.json"),book)
  status<-if(source=="replay")"REPLAY" else if(!length(speeches)&&!length(collection$errors))"EMPTY" else "AUTOMATED_CHECKS_PASSED"
  if(source!="replay") {
    flagged<-any(vapply(speeches,function(s){a<-analyses[[s$iso3]];length(s$flags)>0||length(a$flags)>0||a$verification$status!="model_reviewed"||any(vapply(a$issues,function(i)i$status=="uncertain",logical(1)))},logical(1)))
    if(length(collection$errors)||flagged)status<-"REVIEW_REQUIRED"
  }
  if(length(collection$errors)&&!isTRUE(cfg$generation$allow_partial_draft))stop("Partial draft disabled; inspect archived errors")
  rows<-list()
  for(s in speeches)for(issue in book) {
    a<-Filter(function(i)i$issue_id==issue$issue_id,analyses[[s$iso3]]$issues)[[1]]
    rows<-c(rows,list(list(country=s$country,iso3=s$iso3,region=s$region,issue_id=issue$issue_id,issue=issue$label,short_label=issue$short_label,fixed=isTRUE(issue$fixed),fixed_order=issue$fixed_order %||% 0,coding_version=issue$version,code=switch(a$status,present=1,absent=0,uncertain=""),status=a$status,rationale=a$rationale,evidence=json_text(a$evidence),source_sha256=s$source_sha256,text_sha256=s$text_sha256,analysis_status=analyses[[s$iso3]]$verification$status)))
  }
  csv_write(file.path(run,"data/country_issue_long.csv"),rows,c("country","iso3","region","issue_id","issue","short_label","fixed","fixed_order","coding_version","code","status","rationale","evidence","source_sha256","text_sha256","analysis_status"))
  csv_write(file.path(run,"data/countries.csv"),speeches,c("iso3","country","speaker","title","date","region","source_type","source_url","source_sha256","text_sha256"))
  csv_write(file.path(run,"data/issues.csv"),book,c("issue_id","label","short_label","definition","version","fixed","fixed_order"))
  regions<-region_sequence(vapply(speeches,function(x)x$region,character(1)),cfg)
  csv_write(file.path(run,"data/region_order.csv"),data.frame(region=regions,display_order=seq_along(regions)))
  csv_write(file.path(run,"data/plot_settings.csv"),lapply(names(cfg$generation),function(k)list(key=k,value=cfg$generation[[k]])),c("key","value"))
  json_write(file.path(run,"audit/speeches.json"),speeches);json_write(file.path(run,"audit/analyses.json"),analyses);json_write(file.path(run,"audit/collection.json"),collection)
  if(!nzchar(prepared_at))prepared_at<-format(Sys.time(),"%Y-%m-%dT%H:%M:%SZ",tz="UTC")
  brief<-list(date=day,source=source,analysis_mode=if(source=="replay")"inherited_snapshot" else cfg$analysis_mode,status=status,country_count=length(speeches),issue_count=length(book),coding_cells=length(rows),prepared_at=prepared_at,code_version=UNBRIEF_VERSION,fixed_issue_order=as.list(FIXED_ISSUE_IDS),country_grouping="region_then_alphabetical",fixed_topic_mode=if(source=="replay")"provisional_scan_plus_inherited_ukraine" else cfg$analysis_mode,collection=collection)
  plot_note<-if(source=="replay")"Replay: Iran/Cuba/AI are provisional scans; Ukraine is inherited. No-hit is unresolved." else if(cfg$analysis_mode=="extractive")"Provisional lexicon coding. No-hit is unresolved, not established absence." else "Automated full-text coding. Model review is not human review."
  csv_write(file.path(run,"data/plot_context.csv"),data.frame(source=source,note=plot_note))
  json_write(file.path(run,"brief.json"),brief);json_write(file.path(run,"checkpoint.json"),list(stage="prepared",status=status,countries=length(speeches)))
  # Save an R-native checkpoint. Reproducible replay does not require repeated model calls.
  saveRDS(list(brief=brief,speeches=speeches,observations=observations,analyses=analyses,config=cfg,codebook=book),file.path(run,"checkpoint.rds"),version=3)
  cat(sprintf("PREPARED: %d countries; %s\n",length(speeches),status));invisible(brief)
}
