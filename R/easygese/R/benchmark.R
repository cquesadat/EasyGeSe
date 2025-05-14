#' @importFrom httr GET content http_error status_code
#' @importFrom jsonlite fromJSON
#' @importFrom utils read.csv write.csv
NULL

#' Download benchmark data
#'
#' Downloads benchmark result files from the EasyGeSe GitHub repository.
#' 
#' @param output_dir Directory to save files. Defaults to user cache directory
#' @param force If TRUE, force re-download even if cache exists
#'
#' @return Path to directory containing the downloaded files
#' @export
download_benchmark_data <- function(output_dir = NULL, force = FALSE) {
  # Base GitHub URL (derived from index URL)
  base_url <- gsub("index\\.json$", "", INDEX_URL)
  
  # Set up the output directory
  if (is.null(output_dir)) {
    output_dir <- get_cache_dir()
  } else {
    if (!dir.exists(output_dir)) {
      dir.create(output_dir, recursive = TRUE)
    }
  }
  
  # Define benchmark files to download
  benchmark_files <- c(
    "results_raw.csv" = paste0(base_url, "results_raw.csv"),
    "results_summary.csv" = paste0(base_url, "results_summary.csv")
  )
  
  # Check if files already exist
  all_exist <- TRUE
  for (filename in names(benchmark_files)) {
    if (!file.exists(file.path(output_dir, filename))) {
      all_exist <- FALSE
      break
    }
  }
  
  if (all_exist && !force) {
    message(paste("All benchmark files already exist in", output_dir))
    return(output_dir)
  }
  
  # Download files (only missing ones if not forcing)
  for (filename in names(benchmark_files)) {
    output_file <- file.path(output_dir, filename)
    if (file.exists(output_file) && !force) {
      message(paste("Using cached", filename))
      next
    }
    
    message(paste("Downloading", filename, "..."))
    tryCatch({
      response <- httr::GET(benchmark_files[filename])
      if (httr::http_error(response)) {
        stop(paste("HTTP error:", httr::status_code(response)))
      }
      writeBin(httr::content(response, "raw"), output_file)
    },
    error = function(e) {
      message(paste("Error downloading", filename, ":", e$message))
    })
  }
  
  return(output_dir)
}


#' Load benchmark results
#'
#' Loads benchmark results from the EasyGeSe GitHub repository.
#' 
#' @param species Species to filter by (e.g., "barley", "bean", "lentil")
#' @param traits Traits to filter by (e.g., "BaMMV", "DF", "DTF")
#' @param models Models to filter by (e.g., "BayesA", "GBLUP", "XGBoost")
#' @param summarize Whether to use summarized results (TRUE) or raw results (FALSE)
#' @param download If TRUE, explicitly download data to local storage
#' @param download_dir Directory to save files if downloading
#'
#' @return Data frame containing the benchmark results, filtered as specified
#' @export
load_benchmark_results <- function(
  species = NULL,
  traits = NULL,
  models = NULL,
  summarize = TRUE,
  download = FALSE,
  download_dir = NULL
) {
  # Determine which file to use
  filename <- if (summarize) "results_summary.csv" else "results_raw.csv"
  
  # Base GitHub URL (derived from index URL)
  base_url <- gsub("index\\.json$", "", INDEX_URL)
  file_url <- paste0(base_url, filename)
  
  # Determine directory to use
  data_dir <- if (is.null(download_dir)) get_cache_dir() else download_dir
  
  # Check if file exists locally
  file_path <- file.path(data_dir, filename)
  file_exists <- file.exists(file_path)
  
  # If file exists locally, load it directly
  if (file_exists) {
    message(paste("Loading", filename, "from", data_dir, "..."))
    df <- read.csv(file_path)
  }
  # If file doesn't exist and download is requested, download it
  else if (download) {
    message(paste("File not found in", data_dir, ". Downloading..."))
    download_benchmark_data(output_dir = data_dir)
    
    # Now load the downloaded file
    df <- read.csv(file.path(data_dir, filename))
  }
  # If file doesn't exist and download not requested, try online loading
  else {
    tryCatch({
      message(paste("Loading", filename, "from online source..."))
      df <- read.csv(file_url)
    },
    error = function(e) {
      stop(paste("Failed to load from online source:", e$message,
                "\nNo local file found at", file_path, "and online loading failed."))
    })
  }
  
  # Helper for case-insensitive column matching
  get_col <- function(name) {
    cols <- colnames(df)
    idx <- which(tolower(cols) == tolower(name))
    if (length(idx) > 0) return(cols[idx[1]])
    return(NULL)
  }
  
  # Apply filters if provided
  species_col <- get_col("species")
  trait_col <- get_col("trait")
  model_col <- get_col("model")
  
  if (!is.null(species) && !is.null(species_col)) {
    if (is.character(species) && length(species) == 1) {
      df <- df[df[[species_col]] == species, ]
    } else {
      df <- df[df[[species_col]] %in% species, ]
    }
  }
  
  if (!is.null(traits) && !is.null(trait_col)) {
    if (is.character(traits) && length(traits) == 1) {
      df <- df[df[[trait_col]] == traits, ]
    } else {
      df <- df[df[[trait_col]] %in% traits, ]
    }
  }
  
  if (!is.null(models) && !is.null(model_col)) {
    if (is.character(models) && length(models) == 1) {
      df <- df[df[[model_col]] == models, ]
    } else {
      df <- df[df[[model_col]] %in% models, ]
    }
  }
  
  return(df)
}

