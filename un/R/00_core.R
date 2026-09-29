if (!l10n_info()[["UTF-8"]]) invisible(try(Sys.setlocale("LC_CTYPE", if(.Platform$OS.type=="windows") "English_United States.utf8" else "C.UTF-8"),silent=TRUE))
# Core I/O. Packages are preferred; explicit offline replay has base-R adapters.
UNBRIEF_VERSION <- "2.4.0-d1-hc-only"
`%||%` <- function(x, y) if (is.null(x) || length(x) == 0L) y else x
assert <- function(ok, message) if (!isTRUE(ok)) stop(message, call. = FALSE)
str1 <- function(x, default = "") if (is.character(x) && length(x) == 1L && !is.na(x)) x else default
word_count <- function(x) length(strsplit(trimws(x), "[[:space:]]+", perl = TRUE)[[1]])
norm <- function(x) tolower(trimws(gsub("[[:space:]]+", " ", enc2utf8(x), perl = TRUE)))
visible <- function(x) {
  x <- enc2utf8(as.character(x %||% ""))
  assert(!anyNA(x) && !any(grepl("\ufffd|[\u0001-\u0008\u000b\u000c\u000e-\u001f]", x, perl=TRUE)), "Invalid Unicode/control character in text")
  x
}
need_packages <- function(packages) {
  missing <- packages[!vapply(packages, requireNamespace, logical(1), quietly = TRUE)]
  assert(!length(missing), paste("Install the required R packages with Rscript setup.R:", paste(missing, collapse=", ")))
}
read_bytes <- function(path) { assert(file.exists(path), paste("Missing file:",path)); readBin(path,"raw",n=file.info(path)$size) }
read_text <- function(path) enc2utf8(rawToChar(read_bytes(path)))
atomic_bytes <- function(path, value) {
  dir.create(dirname(path),recursive=TRUE,showWarnings=FALSE)
  temp <- tempfile("._",tmpdir=dirname(path)); on.exit(unlink(temp),add=TRUE)
  writeBin(if(is.raw(value)) value else charToRaw(enc2utf8(value)),temp)
  # Windows rename cannot replace an existing file; preserve the old copy until commit succeeds.
  backup <- paste0(path,".previous")
  if(file.exists(path)) { if(file.exists(backup)) unlink(backup); assert(file.rename(path,backup),"Cannot preserve existing output") }
  ok <- file.rename(temp,path)
  if(!ok && file.exists(backup)) file.rename(backup,path)
  assert(ok,paste("Cannot commit output:",path)); if(file.exists(backup)) unlink(backup)
  invisible(path)
}
write_text <- function(path,x) atomic_bytes(path,paste0(paste(x,collapse="\n"),"\n"))
sha_file <- function(path) {
  if(requireNamespace("digest",quietly=TRUE) && !isTRUE(getOption("unbrief.minimal"))) return(digest::digest(file=path,algo="sha256"))
  assert("sha256sum" %in% getNamespaceExports("tools"),"Install digest or use R >=4.6 for SHA-256")
  unname(tools::sha256sum(path))
}
sha_raw <- function(bytes) {p<-tempfile();on.exit(unlink(p));writeBin(bytes,p);sha_file(p)}
sha_text <- function(x) sha_raw(charToRaw(enc2utf8(x)))

# Strict, bounded RFC-8259 subset adapter for offline replay only. Live processing requires jsonlite.
# It rejects duplicate object keys, non-finite numbers, trailing tokens, unpaired surrogates and NUL.
json_parse_minimal <- function(text) {
  text <- sub("^\ufeff","",enc2utf8(text)); chars <- strsplit(text,"",fixed=TRUE)[[1]]; pos<-1L; n<-length(chars)
  peek <- function() if(pos<=n) chars[pos] else ""
  skip <- function() {while(pos<=n && chars[pos] %in% c(" ","\n","\r","\t")) pos<<-pos+1L}
  take_hex <- function() { assert(pos+3L<=n,"Incomplete JSON Unicode escape"); z<-paste(chars[pos:(pos+3L)],collapse=""); assert(grepl("^[0-9A-Fa-f]{4}$",z),"Invalid Unicode escape");pos<<-pos+4L;strtoi(z,16L) }
  string <- function() {
    assert(peek()=='"',"Expected JSON string");pos<<-pos+1L;out<-character();start<-pos
    repeat {
      assert(pos<=n,"Unterminated JSON string");ch<-chars[pos]
      if(ch %in% c('"','\\')) {
        if(pos>start) out<-c(out,paste(chars[start:(pos-1L)],collapse=""))
        pos<<-pos+1L
        if(ch=='"') return(paste(out,collapse=""))
        assert(pos<=n,"Incomplete escape"); esc<-chars[pos];pos<<-pos+1L
        if(esc=="u") {
          cp<-take_hex()
          if(cp>=0xD800 && cp<=0xDBFF) {
            assert(pos+1<=n && paste(chars[pos:(pos+1)],collapse="")=="\\u","Missing low surrogate")
            pos<<-pos+2L;low<-take_hex();assert(low>=0xDC00 && low<=0xDFFF,"Invalid low surrogate")
            cp<-0x10000+(cp-0xD800)*1024L+(low-0xDC00)
          } else assert(!(cp>=0xDC00 && cp<=0xDFFF),"Unpaired low surrogate")
          assert(cp>0L,"NUL not supported in R strings");out<-c(out,intToUtf8(cp))
        } else {
          m<-c('"'='"','\\'='\\','/'='/',b='\b',f='\f',n='\n',r='\r',t='\t')
          assert(esc %in% names(m),"Invalid JSON escape");out<-c(out,unname(m[esc]))
        }
        start<-pos
      } else {assert(utf8ToInt(ch)[1]>=32L,"Raw control in JSON string");pos<<-pos+1L}
    }
  }
  value <- function(depth=0L) {
    assert(depth<100L,"JSON nesting too deep");skip();ch<-peek()
    if(ch=='"') return(string())
    if(ch %in% c("{","[")) {
      object<-ch=="{";end<-if(object)"}" else "]";pos<<-pos+1L;skip();out<-list();keys<-character()
      if(peek()==end) {pos<<-pos+1L;if(object) names(out)<-character();return(out)}
      repeat {
        skip();if(object){key<-string();assert(!key %in% keys,"Duplicate JSON key");keys<-c(keys,key);skip();assert(peek()==":","Expected colon");pos<<-pos+1L}
        v<-value(depth+1L);out[length(out)+1L]<-list(v)
        skip();ch<-peek();pos<<-pos+1L
        if(ch==end)break
        assert(ch==",","Expected comma or closing delimiter")
      }
      if(object)names(out)<-keys
      return(out)
    }
    if(ch %in% c("t","f","n")) {
      tok<-switch(ch,t="true",f="false",n="null");len<-nchar(tok)
      assert(pos+len-1L<=n && paste(chars[pos:(pos+len-1L)],collapse="")==tok,"Invalid JSON literal")
      pos<<-pos+len;return(switch(tok,true=TRUE,false=FALSE,null=NULL))
    }
    assert(ch %in% c("-",as.character(0:9)),"Unexpected JSON token")
    start<-pos;while(pos<=n && grepl("[0-9eE+.-]",chars[pos]))pos<<-pos+1L
    tok<-paste(chars[start:(pos-1L)],collapse="")
    assert(grepl("^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$",tok),"Invalid JSON number")
    z<-as.numeric(tok);assert(is.finite(z),"Non-finite JSON number");z
  }
  result<-value();skip();assert(pos>n,"Trailing JSON tokens");result
}
json_string <- function(x) {
  x<-enc2utf8(as.character(x));cp<-utf8ToInt(x)
  out<-vapply(cp,function(z){if(z==34)'\\"' else if(z==92)'\\\\' else if(z<32)sprintf('\\u%04x',z) else intToUtf8(z)},character(1))
  paste0('"',paste(out,collapse=""),'"')
}
json_minimal <- function(x) {
  if(is.null(x))return("null")
  if(is.data.frame(x))x<-lapply(seq_len(nrow(x)),function(i)as.list(x[i,,drop=FALSE]))
  if(is.list(x)) {
    if(!is.null(names(x))){assert(!anyDuplicated(names(x)),"Duplicate output keys");return(paste0("{",paste(paste0(vapply(names(x),json_string,character(1)),":",vapply(x,json_minimal,character(1))),collapse=","),"}"))}
    return(paste0("[",paste(vapply(x,json_minimal,character(1)),collapse=","),"]"))
  }
  if(length(x)!=1L)return(json_minimal(as.list(x)))
  if(is.na(x))return("null")
  if(is.character(x))return(json_string(x))
  if(is.logical(x))return(if(x)"true" else "false")
  assert(is.numeric(x)&&is.finite(x),"Unsupported JSON value");format(x,scientific=FALSE,trim=TRUE,digits=16)
}
json_text <- function(x) {
  if(requireNamespace("jsonlite",quietly=TRUE)&&!isTRUE(getOption("unbrief.minimal"))) as.character(jsonlite::toJSON(x,auto_unbox=TRUE,null="null",na="null",digits=16)) else json_minimal(x)
}
json_read <- function(path) {
  if(requireNamespace("jsonlite",quietly=TRUE)&&!isTRUE(getOption("unbrief.minimal"))) jsonlite::fromJSON(read_text(path),simplifyVector=FALSE) else json_parse_minimal(read_text(path))
}
json_raw <- function(raw) {
  if(requireNamespace("jsonlite",quietly=TRUE)&&!isTRUE(getOption("unbrief.minimal"))) jsonlite::fromJSON(rawToChar(raw),simplifyVector=FALSE) else json_parse_minimal(rawToChar(raw))
}
json_write <- function(path,x) write_text(path,json_text(x))
rows_frame <- function(rows,columns) {
  if(!length(rows))return(as.data.frame(setNames(rep(list(character()),length(columns)),columns),stringsAsFactors=FALSE))
  do.call(rbind,lapply(rows,function(r) as.data.frame(setNames(lapply(columns,function(k){v<-r[[k]];if(is.null(v)||!length(v))"" else if(length(v)==1&&!is.list(v))v else json_text(v)}),columns),stringsAsFactors=FALSE)))
}
csv_write <- function(path,rows,columns=NULL) {
  dir.create(dirname(path),recursive=TRUE,showWarnings=FALSE)
  frame<-if(is.data.frame(rows))rows else rows_frame(rows,columns)
  write.csv(frame,path,row.names=FALSE,na="",fileEncoding="UTF-8")
}
b64 <- function(raw) {
  if(requireNamespace("base64enc",quietly=TRUE)&&!isTRUE(getOption("unbrief.minimal")))return(base64enc::base64encode(raw))
  if(!length(raw))return("")
  tab<-strsplit("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/","",fixed=TRUE)[[1]]
  v<-as.integer(raw);pad<-(3-length(v)%%3)%%3;v<-c(v,rep(0L,pad));m<-matrix(v,nrow=3)
  idx<-rbind(bitwShiftR(m[1,],2),bitwOr(bitwShiftL(bitwAnd(m[1,],3),4),bitwShiftR(m[2,],4)),bitwOr(bitwShiftL(bitwAnd(m[2,],15),2),bitwShiftR(m[3,],6)),bitwAnd(m[3,],63))
  out<-tab[as.vector(idx)+1L];if(pad)out[(length(out)-pad+1L):length(out)]<-"=";paste(out,collapse="")
}
unb64 <- function(x) {
  if(requireNamespace("base64enc",quietly=TRUE)&&!isTRUE(getOption("unbrief.minimal")))return(base64enc::base64decode(x))
  x<-gsub("[\r\n ]","",x);if(!nzchar(x))return(raw());assert(nchar(x)%%4==0,"Invalid base64 size")
  pad<-nchar(x)-nchar(sub("=+$","",x));assert(pad<=2L,"Invalid base64 padding")
  z<-strsplit(x,"",fixed=TRUE)[[1]];assert(!any(z[seq_len(length(z)-pad)]=="="),"Unexpected base64 padding")
  tab<-strsplit("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/","",fixed=TRUE)[[1]];v<-match(z,tab)-1L;v[z=="="]<-0L;assert(!anyNA(v),"Invalid base64 character")
  m<-matrix(v,nrow=4);a<-as.vector(rbind(bitwOr(bitwShiftL(m[1,],2),bitwShiftR(m[2,],4)),bitwOr(bitwShiftL(bitwAnd(m[2,],15),4),bitwShiftR(m[3,],2)),bitwOr(bitwShiftL(bitwAnd(m[3,],3),6),m[4,])))
  as.raw(head(a,length(a)-pad))
}
source_url <- function(url) {
  url<-str1(url);if(startsWith(url,"/"))url<-paste0("https://transcripts.un.org",url)
  assert(grepl("^https://transcripts\\.un\\.org(/|$)",url)&&!grepl("[\r\n#]",url),"Source URL outside allowed UN host")
  url
}
load_registry <- function(path) {
  d<-read.csv(path,stringsAsFactors=FALSE,check.names=FALSE,fileEncoding="UTF-8-BOM");assert(!anyDuplicated(d$iso3),"Duplicate country registry code");d
}
resolve_country <- function(registry,...) {
  wanted<-norm(unlist(list(...)));wanted<-wanted[nzchar(wanted)]
  idx<-which(vapply(seq_len(nrow(registry)),function(i)any(wanted %in% norm(c(registry$iso3[i],registry$country[i],strsplit(registry$aliases[i],"|",fixed=TRUE)[[1]]))),logical(1)))
  if(length(idx)==1)as.list(registry[idx,]) else NULL
}
new_archive <- function(run) {e<-new.env(parent=emptyenv());e$run<-run;e$records<-list();e}
archive_store <- function(archive,bytes,source,kind="json") {
  hash<-sha_raw(bytes);rel<-paste0("raw/",hash,".",kind);path<-file.path(archive$run,rel)
  if(file.exists(path))assert(identical(sha_file(path),hash),"Archived hash mismatch") else atomic_bytes(path,bytes)
  row<-list(source=source,sha256=hash,path=rel,bytes=length(bytes),retrieved_at=utc_now());archive$records[[length(archive$records)+1L]]<-row
  json_write(file.path(archive$run,"audit/source_manifest.json"),archive$records);row
}
http_raw <- function(url,settings,body=NULL,headers=list()) {
  need_packages(c("httr2","jsonlite"))
  assert(grepl("^https://(transcripts\\.un\\.org|api\\.openai\\.com)/",url),"HTTP host not allowlisted")
  req<-httr2::request(url) |> httr2::req_user_agent("UNBriefR/2.0 public-source research") |>
    httr2::req_timeout(settings$timeout_seconds) |> httr2::req_options(followlocation=FALSE,maxfilesize_large=settings$max_response_bytes %||% 25000000) |>
    httr2::req_error(is_error=function(resp)FALSE)
  if(length(headers))req<-do.call(httr2::req_headers,c(list(req),headers))
  if(!is.null(body))req<-httr2::req_body_raw(req,body,type="application/json")
  for(attempt in seq_len(settings$max_attempts)) {
    resp<-tryCatch(httr2::req_perform(req),error=function(e)e)
    code<-if(inherits(resp,"error"))NA_integer_ else httr2::resp_status(resp)
    if(!is.na(code)&&code==200L) {bytes<-httr2::resp_body_raw(resp);assert(length(bytes)>0&&length(bytes)<=(settings$max_response_bytes %||% 25000000),"Empty or oversized response");return(bytes)}
    retry<-is.na(code)||code %in% c(408,429,500,502,503,504)
    assert(retry&&attempt<settings$max_attempts,paste("Request failed; HTTP",if(is.na(code))"transport error" else code,". Response body and credentials omitted."))
    after<-if(is.na(code))NA_real_ else suppressWarnings(as.numeric(httr2::resp_header(resp,"retry-after")))
    wait<-if(length(after)&&is.finite(after))max(0,after) else 2^(attempt-1)
    assert(wait<=60,"Server requested long retry; defer to next run");Sys.sleep(wait)
  }
  stop("Request did not complete")
}
