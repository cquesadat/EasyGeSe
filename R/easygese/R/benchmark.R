#' @importFrom httr GET content http_error status_code
#' @importFrom jsonlite fromJSON
#' @importFrom utils read.csv write.csv
NULL

#' Download benchmark data
#'
#' Downloads benchmark result files (results_raw.csv and results_summary.csv)
#' from the EasyGeSe GitHub repository to the local cache.
#' 
#' @param output_dir Directory to save downloaded files. If NULL, uses the default cache directory.
#' @param force If TRUE, force re-download even if cache exists for each file.
#'
#' @return Path to the cache directory containing the downloaded files.
#' @export
download_benchmark_data <- function(output_dir = NULL, force = FALSE) {
  # Base GitHub URL (derived from INDEX_URL in utils.R)
  # Ensure INDEX_URL is accessible within the package scope
  base_url <- gsub("index\\.json$", "", INDEX_URL) 
  
  # Use user-specified directory or default cache directory
  cache_dir_path <- if (is.null(output_dir)) get_cache_dir() else output_dir
  
  benchmark_files_info <- list(
    list(name = "results_raw.csv", url = paste0(base_url, "results_raw.csv")),
    list(name = "results_summary.csv", url = paste0(base_url, "results_summary.csv"))
  )
  
  for (file_info in benchmark_files_info) {
    message(paste("Ensuring", file_info$name, "is cached..."))
    # download_cached_file will download if not present or if force is TRUE
    # Pass the custom output directory if specified
    if (is.null(output_dir)) {
      download_cached_file(file_info$url, file_info$name, force = force)
    } else {
      download_cached_file(file_info$url, file_info$name, output_dir = output_dir, force = force)
    }
  }
  
  message(paste("Benchmark files are available in the directory:", cache_dir_path))
  return(invisible(cache_dir_path))
}


#' Load benchmark results
#'
#' Loads benchmark results from local cache, downloading if necessary.
#' 
#' @param species Character string. The name of the species to load.
#'                Can be a single string or a vector of strings.
#'                Common aliases (e.g., "lentils" for "lentil", "corn" for "maize")
#'                are also accepted. See `list_species()` for available canonical names. 
#' @param traits Traits to filter by (e.g., "BaMMV", "DF", "DTF"). Case-sensitive.
#' @param models Models to filter by (e.g., "BayesA", "GBLUP", "XGBoost"). Case-sensitive.
#' @param summarize Whether to use summarized results (TRUE) or raw results (FALSE).
#' @param download If TRUE, force re-download of the specific benchmark file being loaded.
#' @param download_dir Directory to save downloaded files. If NULL, uses the default cache directory.
#'
#' @return Data frame containing the benchmark results, filtered as specified.
#' @export
load_benchmark_results <- function(
  species = NULL,
  traits = NULL,
  models = NULL,
  summarize = TRUE,
  download = FALSE, # This now acts as force_refresh for the specific file
  download_dir = NULL
) {
  # Determine which file to use
  filename <- if (summarize) "results_summary.csv" else "results_raw.csv"
  
  # Base GitHub URL (derived from INDEX_URL in utils.R)
  base_url <- gsub("index\\.json$", "", INDEX_URL)
  file_url <- paste0(base_url, filename)
  
  # Ensure the file is in the cache and get its path
  # The 'download' parameter here maps to 'force' in download_cached_file
  # Pass the custom download directory if specified
  cached_file_path <- download_cached_file(file_url, filename, output_dir = download_dir, force = download)
  
  message(paste("Loading", filename, "from cache:", cached_file_path, "..."))
  df <- read.csv(cached_file_path)
  
  # Resolve species names if provided
  if (!is.null(species)) {
    index <- load_index() # Load main index for canonical names
    canonical_species_names <- names(index)
    # species_alias_map will be loaded by resolve_species_name_internal if NULL
    
    # Helper function to resolve a single species name
    resolve_one_species <- function(s_input) {
      resolve_species_name_internal(s_input, canonical_species_names, species_alias_map = NULL)
    }
    
    # Apply resolution to all provided species inputs
    # Ensure species is treated as a character vector for sapply
    resolved_species <- sapply(as.character(species), resolve_one_species, USE.NAMES = FALSE)
  } else {
    resolved_species <- NULL
  }
  
  # Helper for case-insensitive column matching (remains useful)
  get_col <- function(name) {
    cols <- colnames(df)
    idx <- which(tolower(cols) == tolower(name))
    if (length(idx) > 0) return(cols[idx[1]])
    return(NULL)
  }
  
  # Apply filters if provided
  species_col <- get_col("species") # Column name in the CSV
  trait_col <- get_col("trait")     # Column name in the CSV
  model_col <- get_col("model")     # Column name in the CSV
  
  if (!is.null(resolved_species) && !is.null(species_col)) {
    # Filter by the resolved canonical species names
    df <- df[df[[species_col]] %in% resolved_species, ]
  }
  
  # Trait and model filtering remains case-sensitive as per original requirement
  if (!is.null(traits) && !is.null(trait_col)) {
    df <- df[df[[trait_col]] %in% as.character(traits), ]
  }
  
  if (!is.null(models) && !is.null(model_col)) {
    df <- df[df[[model_col]] %in% as.character(models), ]
  }
  
  if (nrow(df) == 0) {
    warning("Filtering resulted in an empty data frame. Check your filter criteria and the content of the benchmark file.")
  }
  
  return(df)
}

