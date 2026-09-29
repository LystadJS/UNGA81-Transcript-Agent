# Browser front end only. The same job runner is callable from scripts/run_demo.R.
required <- c("shiny", "callr", "jsonlite", "digest", "htmltools", "zip")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop("Run Setup first. Missing packages: ", paste(missing, collapse = ", "), call. = FALSE)

root <- normalizePath(getwd(), winslash = "/")
source(file.path(root, "R", "load.R"), local = TRUE)
load_readout(root, environment())
options(shiny.maxRequestSize = 100 * 1024^2, shiny.sanitize.errors = TRUE)

# Local decorative icons; visible labels supply accessible names.
readout_icon <- function(name) {
  shiny::tags$span(class = "ui-icon", `aria-hidden` = "true",
    shiny::HTML(paste(readLines(file.path(root, "www", paste0(name, ".svg")), warn = FALSE), collapse = "")))
}

make_ui <- function() {
  shiny::fluidPage(
    shiny::tags$head(
      shiny::tags$title("UN Readout | Transcript Intelligence"),
      shiny::tags$meta(name = "viewport", content = "width=device-width, initial-scale=1"),
      shiny::tags$link(rel = "stylesheet", href = "app.css"),
      shiny::tags$script(src = "app.js")
    ),
    shiny::tags$header(class = "masthead",
      shiny::tags$img(class = "brand-mark", src = "seal.png", alt = "U.S. Mission to the United Nations"),
      shiny::tags$div(shiny::tags$div(class = "eyebrow light", "U.S. MISSION TO THE UNITED NATIONS"),
                      shiny::tags$div(class = "brand-title", "Daily Readout")),
      shiny::tags$div(class = "header-status", "Local processing", shiny::tags$span("/"), "Unsent drafts only")
    ),
    shiny::tags$main(class = "app-shell",
      shiny::tags$div(class = "page-intro",
        shiny::tags$div(shiny::tags$div(class = "eyebrow", "YOUR BRIEFING, YOUR ISSUES"),
          shiny::tags$h1("What would you like to follow?"),
          shiny::tags$p("Add your topics. The readout also checks the full transcript collection for other themes.")),
        shiny::tags$span(class = "status-badge", "D1-I4 integrated · audit-gated")
      ),
      shiny::tags$div(class = "workspace",
        shiny::tags$aside(class = "setup-card", `aria-label` = "Readout settings",
          shiny::tags$div(class = "card-heading", shiny::tags$span(class = "step-number", readout_icon("settings")), shiny::tags$h2("Set up your readout")),
          shiny::dateRangeInput("dates", "Reporting date",
                                start = as.Date(format(Sys.time(), "%Y-%m-%d", tz = "America/New_York")) - 1L,
                                end = as.Date(format(Sys.time(), "%Y-%m-%d", tz = "America/New_York")) - 1L,
                                format = "M d, yyyy", separator = "to"),
          shiny::selectizeInput("topics", "Issues I want to track", choices = DEFAULT_TOPICS,
            selected = DEFAULT_TOPICS, multiple = TRUE, width = "100%",
            options = list(create = TRUE, persist = FALSE, plugins = list("remove_button"),
              maxItems = 20L, placeholder = "Type an issue, then press Enter")),
          shiny::tags$p(class = "field-help", "Type any topic and press Enter. Remove a topic with its ×. Up to 20 topics; none is also allowed."),
          shiny::tags$p(class = "micro-note", "Matching uses exact wording and approved related phrases, not automatic paraphrase interpretation."),
          shiny::tags$details(class = "optional-panel",
            shiny::tags$summary("Refine matching", shiny::tags$span("Optional")),
            shiny::selectInput("refine_topic", "Topic to refine", choices = DEFAULT_TOPICS),
            shiny::textAreaInput("include_phrases", "Also look for", value = "", rows = 3L,
              placeholder = "One related phrase per line"),
            shiny::textAreaInput("exclude_phrases", "Ignore a passage containing", value = "", rows = 2L,
              placeholder = "One excluded phrase per line"),
            shiny::tags$p(class = "field-help", "Exclusions affect only matching passages, never the full-corpus discovery step. Artificial Intelligence includes the explicit alias AI."),
            shiny::actionButton("save_refinement", "Apply to this topic", class = "btn-subtle")
          ),
          shiny::tags$div(class = "source-block",
            shiny::radioButtons("source", "Transcripts", choices = c("Practice with sample speeches" = "demo",
              "Use my transcript files" = "upload", "Use the installed pipeline" = "d1"), selected = "d1"),
            shiny::conditionalPanel("input.source == 'upload'",
              shiny::fileInput("transcripts", label = NULL, multiple = TRUE, accept = c(".txt", ".zip", ".csv"),
                buttonLabel = "Choose files", placeholder = "TXT, ZIP of TXT, or statement CSV"),
              shiny::tags$p(class = "field-help", "Dates and country labels come from source metadata. Undated files are reported separately, not silently assigned to a day.")),
            shiny::uiOutput("source_note")
          ),
          shiny::actionButton("generate", shiny::tagList(readout_icon("document"), "Generate readout"), class = "btn-primary generate-button"),
          shiny::actionButton("cancel", "Cancel this run", class = "btn-subtle cancel-button"),
          shiny::tags$p(class = "privacy-note", "Nothing is emailed automatically. This prototype makes no external AI calls."),
          shiny::tags$details(class = "optional-panel preferences",
            shiny::tags$summary("Save my topics"),
            shiny::actionButton("save_preferences", "Save in this browser", class = "btn-subtle"),
            shiny::actionButton("restore_preferences", "Restore saved topics", class = "btn-subtle"),
            shiny::tags$p(class = "field-help", "Anyone using this browser profile can restore these topics. Transcript text is not saved in browser storage."))
        ),
        shiny::tags$section(class = "results-card", `aria-label` = "Readout results",
          shiny::tags$div(class = "card-heading", shiny::tags$span(class = "step-number", readout_icon("document")), shiny::tags$h2("Review your readout")),
          shiny::uiOutput("progress_panel"),
          shiny::uiOutput("empty_state"),
          shiny::uiOutput("results_header"),
          shiny::uiOutput("stale_notice"),
          shiny::conditionalPanel("output.has_result",
            shiny::tags$div(class = "export-toolbar",
              shiny::downloadButton("download_eml", shiny::tagList(readout_icon("mail"), "Save email"), icon = NULL, class = "btn-primary"),
              shiny::uiOutput("pdf_button", inline = TRUE),
              shiny::downloadButton("download_html", shiny::tagList(readout_icon("document"), "Save HTML"), icon = NULL, class = "btn-subtle")),
            shiny::tabsetPanel(id = "results_tab", type = "tabs",
              shiny::tabPanel(shiny::tagList(readout_icon("mail"), "Email preview"), value = "preview", shiny::uiOutput("email_preview")),
              shiny::tabPanel(shiny::tagList(readout_icon("search"), "Topic matches"), value = "tracked",
                shiny::tags$p(class = "tab-note", "Preliminary literal matches. A non-match is unresolved, not evidence that a topic is absent."),
                shiny::tableOutput("tracked_table"), shiny::selectInput("evidence_topic", "Show supporting passages for", choices = character()),
                shiny::uiOutput("evidence_cards")),
              shiny::tabPanel(shiny::tagList(readout_icon("themes"), "Suggested themes"), value = "themes", shiny::uiOutput("theme_note"), shiny::tableOutput("themes_table")),
              shiny::tabPanel(shiny::tagList(readout_icon("coverage"), "Coverage"), value = "coverage", shiny::uiOutput("coverage_note"), shiny::tableOutput("coverage_table"))
            ),
            shiny::tags$details(class = "optional-panel analyst-panel",
              shiny::tags$summary("Evidence and diagnostics"),
              shiny::tags$p("Research candidates are not D1-released models. Passing an engineering check does not authorize publication."),
              shiny::tableOutput("diagnostics_table"),
              shiny::downloadButton("download_evidence", "Source evidence CSV", class = "btn-subtle"),
              shiny::downloadButton("download_request", "Run settings JSON", class = "btn-subtle"),
              shiny::downloadButton("download_audit", "Full audit ZIP", class = "btn-subtle"),
              shiny::verbatimTextOutput("run_receipt")
            )
          )
        )
      ),
      shiny::tags$footer(class = "page-footer", "D1-I4 integrated interface · Five-output publication boundary retained · Unsent drafts only")
    )
  )
}

make_server <- function(root) {
  force(root)
  function(input, output, session) {
    state <- shiny::reactiveValues(running = FALSE, result = NULL, process = NULL, job_dir = NULL,
      refinements = list(), progress = list(state = "idle", percent = 0, message = ""), error = NULL)
    runtime <- Sys.getenv("UN_READOUT_RUNTIME", file.path(root, "runtime", "runs"))
    dir.create(runtime, recursive = TRUE, showWarnings = FALSE, mode = "0700")
    set_busy <- function(busy) session$sendCustomMessage("setBusy", list(busy = busy))
    notify <- function(message, type = "message") shiny::showNotification(message, type = type, duration = 8)

    output$source_note <- shiny::renderUI({
      if (input$source == "demo") return(shiny::tags$div(class = "source-notice", "Practice sample: 18 fictional training statements, dated 24 September 2026. These are not UN speeches."))
      if (input$source == "d1") return(shiny::tags$div(class = "source-notice", if (inspect_d1()$ready) "D1-I4 connected. One reporting date per installed-pipeline run; outputs remain unsent and audit-gated." else inspect_d1()$reason))
      shiny::tags$div(class = "source-notice subtle", "Source-file mode runs the separate prototype backend. It does not modify the existing D1 historical store.")
    })
    shiny::observeEvent(input$topics, {
      labels <- input$topics %||% character()
      old <- shiny::isolate(input$refine_topic)
      selected <- if (length(old) == 1L && old %in% labels) old else head(labels, 1L)
      shiny::updateSelectInput(session, "refine_topic", choices = labels, selected = selected)
    }, ignoreNULL = FALSE)
    shiny::observeEvent(input$refine_topic, {
      label <- input$refine_topic
      detail <- state$refinements[[label]] %||% list(include = if (identical(label, "Artificial Intelligence")) "AI" else character(), exclude = character())
      shiny::updateTextAreaInput(session, "include_phrases", value = paste(detail$include, collapse = "\n"))
      shiny::updateTextAreaInput(session, "exclude_phrases", value = paste(detail$exclude, collapse = "\n"))
    })
    shiny::observeEvent(input$save_refinement, {
      tryCatch({
        label <- input$refine_topic
        if (!nzchar(label %||% "")) user_error("Add a topic before refining it.")
        detail <- list(include = normalize_phrases(strsplit(input$include_phrases %||% "", "\n")[[1L]]),
          exclude = normalize_phrases(strsplit(input$exclude_phrases %||% "", "\n")[[1L]]))
        candidate <- state$refinements
        candidate[[label]] <- detail
        make_topics(input$topics, candidate)
        state$refinements <- candidate
        notify(paste0("Matching updated for ", label, ". Generate a new readout to apply it."))
      }, error = function(e) notify(conditionMessage(e), "error"))
    })
    shiny::observeEvent(input$save_preferences, {
      tryCatch({
        topics <- make_topics(input$topics, state$refinements)
        session$sendCustomMessage("savePreferences", list(schema = "un.readout.preferences.v1", topics = topics))
      }, error = function(e) notify(conditionMessage(e), "error"))
    })
    shiny::observeEvent(input$restore_preferences, session$sendCustomMessage("restorePreferences", list()))
    shiny::observeEvent(input$preference_status, {
      notify(input$preference_status$message, if (isTRUE(input$preference_status$ok)) "message" else "warning")
    })
    shiny::observeEvent(input$saved_preferences, {
      tryCatch({
        pref <- input$saved_preferences
        if (!identical(pref$schema, "un.readout.preferences.v1") || !is.list(pref$topics)) user_error("The saved topic format is not supported.")
        labels <- vapply(pref$topics, `[[`, character(1), "label")
        refs <- setNames(lapply(pref$topics, function(x) list(include = unlist(x$include), exclude = unlist(x$exclude))), labels)
        approved <- make_topics(labels, refs)
        state$refinements <- refs
        shiny::updateSelectizeInput(session, "topics", choices = unique(c(DEFAULT_TOPICS, labels)), selected = labels, server = FALSE)
        notify("Saved topics restored. Generate a new readout to use them.")
      }, error = function(e) notify("Saved topics could not be restored. Add your topics again.", "error"))
    })

    shiny::observeEvent(input$generate, {
      if (isTRUE(state$running)) return()
      state$result <- NULL
      tryCatch({
        config <- new_config(input$dates[[1L]], input$dates[[2L]], input$topics, state$refinements, input$source)
        if (config$source == "d1" && !inspect_d1()$ready) user_error(inspect_d1()$reason)
        if (config$source == "upload" && (is.null(input$transcripts) || !nrow(input$transcripts))) user_error("Choose transcript files, or switch to the practice sample.")
        job_dir <- tempfile(paste0("run_", format(Sys.time(), "%Y%m%d_%H%M%S"), "_"), tmpdir = runtime)
        dir.create(job_dir, mode = "0700")
        inputs <- character()
        names <- character()
        if (config$source == "upload") {
          incoming <- file.path(job_dir, "incoming")
          dir.create(incoming, mode = "0700")
          for (i in seq_len(nrow(input$transcripts))) {
            ext <- tolower(tools::file_ext(input$transcripts$name[[i]]))
            if (!ext %in% c("txt", "csv", "zip")) user_error("Only TXT, CSV, and ZIP transcript files are supported.")
            dest <- file.path(incoming, sprintf("input_%03d.%s", i, ext))
            if (!file.copy(input$transcripts$datapath[[i]], dest)) user_error("A selected file could not be copied into this run.")
            inputs <- c(inputs, dest)
            names <- c(names, input$transcripts$name[[i]])
          }
        }
        state$result <- NULL
        state$error <- NULL
        state$job_dir <- normalizePath(job_dir)
        state$progress <- list(state = "running", percent = 1, message = "Starting a separate analysis job.")
        state$process <- callr::r_bg(function(root, config, job_dir, inputs, names) {
          source(file.path(root, "R", "load.R"))
          load_readout(root, globalenv())
          run_readout(config, job_dir, root, inputs, names)
        }, args = list(root = root, config = config, job_dir = state$job_dir, inputs = inputs, names = names),
        libpath = .libPaths(), stdout = file.path(job_dir, "worker.stdout.log"),
        stderr = file.path(job_dir, "worker.stderr.log"), supervise = TRUE)
        state$running <- TRUE
        set_busy(TRUE)
      }, error = function(e) {
        state$error <- conditionMessage(e)
        state$progress <- list(state = "failed", percent = 0, message = conditionMessage(e))
        set_busy(FALSE)
      })
    })
    shiny::observe({
      shiny::invalidateLater(500, session)
      if (!isTRUE(state$running) || is.null(state$process)) return()
      path <- file.path(state$job_dir, "progress.rds")
      progress <- if (file.exists(path)) tryCatch(readRDS(path), error = function(e) NULL) else NULL
      if (!is.null(progress)) state$progress <- progress
      if (!state$process$is_alive()) {
        tryCatch({
          result <- state$process$get_result()
          if (is.null(result) || !file.exists(file.path(state$job_dir, "result.rds"))) user_error("The job ended without a completed result.")
          state$result <- result
          topics <- vapply(result$config$fixed_topics, `[[`, character(1), "label")
          shiny::updateSelectInput(session, "evidence_topic", choices = topics, selected = head(topics, 1L))
        }, error = function(e) {
          saved <- tryCatch(readRDS(file.path(state$job_dir, "error.rds")), error = function(e) NULL)
          message <- saved$message %||% "The analysis job stopped. The run log is preserved for the installation owner."
          state$error <- message
          state$progress <- list(state = "failed", percent = 0, message = message)
        })
        state$running <- FALSE
        state$process <- NULL
        set_busy(FALSE)
      }
    })
    shiny::observeEvent(input$cancel, {
      if (isTRUE(state$running) && !is.null(state$process)) {
        state$process$kill_tree()
        state$process <- NULL
        state$running <- FALSE
        state$result <- NULL
        state$progress <- list(state = "cancelled", percent = 0, message = "Run cancelled. Partial files are retained for audit and are not offered as a completed report.")
        write_utf8(utc_now(), file.path(state$job_dir, "CANCELLED.txt"))
        set_busy(FALSE)
      }
    })
    session$onSessionEnded(function() {
      process <- shiny::isolate(state$process)
      if (!is.null(process) && process$is_alive()) process$kill_tree()
    })

    output$has_result <- shiny::reactive(!is.null(state$result))
    shiny::outputOptions(output, "has_result", suspendWhenHidden = FALSE)
    output$progress_panel <- shiny::renderUI({
      p <- state$progress
      if (p$state == "idle") return(NULL)
      shiny::tags$div(class = paste("progress-panel", p$state), `aria-live` = "polite",
        shiny::tags$p(p$message),
        if (p$state == "running") shiny::tags$div(class = "progress-track", role = "progressbar",
          `aria-valuemin` = 0, `aria-valuemax` = 100, `aria-valuenow` = p$percent,
          shiny::tags$div(class = "progress-fill", style = paste0("width:", p$percent, "%"))))
    })
    output$empty_state <- shiny::renderUI({
      if (!is.null(state$result) || isTRUE(state$running)) return(NULL)
      shiny::tags$div(class = "empty-state",
        shiny::tags$div(class = "empty-icon", readout_icon("document")),
        shiny::tags$h3("Your readout will appear here"),
        shiny::tags$p("Choose a period, add your topics, and generate a draft."),
        shiny::tags$div(class = "outcome-grid",
          shiny::tags$div(shiny::tags$strong("Your topics"), shiny::tags$p("Source-linked wording matches.")),
          shiny::tags$div(shiny::tags$strong("Other themes"), shiny::tags$p("Full-corpus candidates, kept separate.")),
          shiny::tags$div(shiny::tags$strong("A ready-to-review draft"), shiny::tags$p("Full-width email with coverage notes."))),
        shiny::tags$p(class = "empty-footnote", "The practice sample is synthetic. Installed-pipeline mode uses the integrated D1-I4 checkpoint and retains its publication gates."))
    })
    output$results_header <- shiny::renderUI({
      result <- state$result
      shiny::req(result)
      n <- sum(result$statements$status == "available")
      shiny::tags$div(class = "result-summary",
        shiny::tags$div(class = "result-metric", shiny::tags$strong(n), shiny::tags$span("available texts")),
        shiny::tags$div(class = "result-metric", shiny::tags$strong(length(result$config$fixed_topics)), shiny::tags$span("tracked topics")),
        shiny::tags$div(class = "result-scope", shiny::tags$strong(paste(result$config$start_date, "to", result$config$end_date)),
          shiny::tags$span(if (result$config$source == "demo") "Practice data · not a UN assessment" else if (result$config$source == "d1") "D1-I4 installed pipeline · audit-gated" else "Prototype source extracts · review required")))
    })
    output$stale_notice <- shiny::renderUI({
      shiny::req(state$result)
      r <- state$result$config
      current <- tryCatch(new_config(input$dates[[1L]], input$dates[[2L]], input$topics, state$refinements, input$source), error = function(e) NULL)
      changed <- is.null(current) || !identical(to_json(current$fixed_topics), to_json(r$fixed_topics)) ||
        !identical(current$start_date, r$start_date) || !identical(current$end_date, r$end_date) || !identical(current$source, r$source)
      if (changed) shiny::tags$p(class = "source-notice", "Settings have changed. These are the previous completed results; generate a new readout to apply your changes.") else NULL
    })
    output$pdf_button <- shiny::renderUI({
      shiny::req(state$result)
      if (state$result$pdf$status == "created") shiny::downloadButton("download_pdf", shiny::tagList(readout_icon("download"), "Save PDF"), icon = NULL, class = "btn-subtle") else
        shiny::tags$span(class = "pdf-notice", title = state$result$pdf$reason, "PDF unavailable · print saved HTML")
    })
    output$email_preview <- shiny::renderUI({
      shiny::req(state$result)
      html <- read_utf8(state$result$files$html, max_bytes = 20 * 1024^2)
      shiny::tags$iframe(class = "email-frame", title = "Unsent readout preview", srcdoc = html, sandbox = "", referrerpolicy = "no-referrer")
    })
    output$tracked_table <- shiny::renderTable({
      shiny::req(state$result)
      data <- state$result$tracked$summary
      data <- data[, c("topic", "texts_with_matches", "eligible_texts", "unresolved_texts"), drop = FALSE]
      names(data) <- c("Your topic", "Texts with matches", "Available texts", "Unresolved texts")
      data
    }, striped = FALSE, bordered = FALSE, spacing = "m", sanitize.text.function = htmltools::htmlEscape)
    output$evidence_cards <- shiny::renderUI({
      shiny::req(state$result)
      ev <- state$result$tracked$evidence
      ev <- ev[ev$topic == (input$evidence_topic %||% ""), , drop = FALSE]
      if (!nrow(ev)) return(shiny::tags$p(class = "tab-note", "No literal phrase match was found. This does not establish that the issue was absent."))
      shiny::tagList(lapply(seq_len(min(nrow(ev), 15L)), function(i) {
        e <- ev[i, , drop = FALSE]
        shiny::tags$article(class = "evidence-card", shiny::tags$strong(if (nzchar(e$country)) e$country else "Unattributed transcript"),
          shiny::tags$blockquote(e$quote), shiny::tags$p(class = "evidence-source", paste0(e$source_file, " · ", e$statement_id,
            " · characters ", e$start_char, "–", e$end_char)))
      }), if (nrow(ev) > 15L) shiny::tags$p(class = "field-help", "Showing 15 passages. The source evidence CSV contains all matches."))
    })
    output$theme_note <- shiny::renderUI({
      shiny::req(state$result)
      shiny::tags$div(class = "source-notice", shiny::tags$strong("Research candidates — not included in the email"),
        shiny::tags$p(state$result$discovery$reason), shiny::tags$p("Suggested terms describe text groups, not a measured trend, policy position, or diplomatic coalition."))
    })
    output$themes_table <- shiny::renderTable({
      shiny::req(state$result)
      d <- state$result$discovery$candidates
      if (!nrow(d)) return(NULL)
      d <- d[, c("suggested_terms", "texts", "attributed_countries"), drop = FALSE]
      names(d) <- c("Suggested wording", "Texts", "Attributed countries")
      d
    }, sanitize.text.function = htmltools::htmlEscape, spacing = "m")
    output$coverage_note <- shiny::renderUI({
      shiny::req(state$result)
      s <- state$result$statements
      shiny::tags$p(class = "tab-note", paste(sum(s$status == "available"), "available texts;", sum(s$status == "missing_text"),
        "missing-text entries;", sum(!s$status %in% c("available", "missing_text")),
        "other exclusions. Missing text is never coded as issue absence. Non-English or language-unknown texts do not enter this prototype's discovery model."))
    })
    output$coverage_table <- shiny::renderTable({
      shiny::req(state$result)
      d <- state$result$statements[, c("country", "speech_date", "status", "language", "source_file"), drop = FALSE]
      names(d) <- c("Country (source)", "Date (source)", "Status", "Language", "Source file")
      head(d, 100L)
    }, sanitize.text.function = htmltools::htmlEscape, spacing = "s")
    output$diagnostics_table <- shiny::renderTable({ shiny::req(state$result); state$result$discovery$diagnostics }, digits = 3L)
    output$run_receipt <- shiny::renderText({
      shiny::req(state$result)
      r <- state$result
      paste("Run:", r$run_id, "\nEngine:", r$engine, "\nRequest SHA-256:", r$request_sha256,
        "\nFeature SHA-256:", r$feature_hash %||% "See adapter receipt", "\nPDF:", r$pdf$status,
        "\nD1 checkpoint execution:", if (identical(r$engine, "d1")) "VERIFIED ADAPTER RUN" else "NOT USED",
        "\nEmail sent: NO")
    })
    download <- function(key, ext) shiny::downloadHandler(
      filename = function() paste0("UN_Readout_", state$result$config$end_date, ".", ext),
      content = function(file) { shiny::req(state$result); path <- state$result$files[[key]]; shiny::req(nzchar(path), file.exists(path)); file.copy(path, file, overwrite = TRUE) })
    output$download_eml <- download("eml", "eml")
    output$download_html <- download("html", "html")
    output$download_pdf <- download("pdf", "pdf")
    output$download_evidence <- download("evidence", "csv")
    output$download_request <- download("request", "json")
    output$download_audit <- shiny::downloadHandler(
      filename = function() paste0("UN_Readout_Audit_", state$result$run_id, ".zip"),
      content = function(file) {
        shiny::req(state$result)
        paths <- list.files(state$job_dir, recursive = TRUE, all.files = FALSE, full.names = FALSE)
        paths <- paths[!grepl("(^|/)(browser-profile|incoming)(/|$)", paths)]
        zip::zipr(file, files = paths, root = state$job_dir, include_directories = FALSE)
      })
  }
}

shiny::shinyApp(ui = make_ui(), server = make_server(root))
