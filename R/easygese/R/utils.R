#' @importFrom rappdirs user_cache_dir
NULL

# Constants
#' @noRd
INDEX_URL <- "https://raw.githubusercontent.com/cquesadat/EasyGeSe/main/datasets/index.json"
SPECIES_ALIASES_URL <- "https://raw.githubusercontent.com/cquesadat/EasyGeSe/main/datasets/species_aliases.json" # Adjust if your path is different

#' Get cache directory
#' 
#' This function retrieves the path to the cache directory for the easygese package. If the directory does not exist, it creates it.
#'
#' @return Path to cache directory
#' @noRd
get_cache_dir <- function() {
  cache_dir <- file.path(rappdirs::user_cache_dir("easygese", "easygese"))
  if (!dir.exists(cache_dir)) {
    dir.create(cache_dir, recursive = TRUE)
  }
  return(cache_dir)
}

#' Download a file and cache it locally
#'
#' @param file_url URL of the file to download.
#' @param local_filename Name of the file to save in the cache directory.
#' @param output_dir Directory to save the file. If NULL, uses the default cache directory.
#' @param force If TRUE, force re-download even if cache exists.
#' @return Path to the cached file.
#' @noRd
download_cached_file <- function(file_url, local_filename, output_dir = NULL, force = FALSE) {
  # Use specified directory or default cache directory
  cache_dir <- if (is.null(output_dir)) get_cache_dir() else output_dir
  
  # Create directory if it doesn't exist
  if (!dir.exists(cache_dir)) {
    dir.create(cache_dir, recursive = TRUE)
  }
  
  cache_file_path <- file.path(cache_dir, local_filename)
  
  if (file.exists(cache_file_path) && !force) {
    return(invisible(cache_file_path))
  }
  
  tryCatch({
    message(paste("Downloading", local_filename, "from", file_url, "..."))
    response <- httr::GET(file_url)
    
    # Use stop_for_status for more robust error checking
    httr::stop_for_status(response, task = paste("download", local_filename)) 
    
    # Save to cache
    # Use writeBin for potentially non-text files, though for JSON content("raw") is safer
    writeBin(httr::content(response, "raw"), cache_file_path) 
    
    message(paste(local_filename, "cached at", cache_file_path))
    return(invisible(cache_file_path))
  },
  error = function(e) {
    # Provide a more informative error message
    error_message <- paste("Error downloading", local_filename, "from", file_url, ":", e$message)
    message(error_message)
    if (file.exists(cache_file_path)) {
      message(paste("Using existing cached", local_filename))
      return(invisible(cache_file_path))
    }
    # Re-throw the error if download fails and no cache exists
    stop(error_message, call. = FALSE) 
  })
}

#' Load a JSON file from cache (downloading if necessary)
#'
#' @param file_url URL of the JSON file.
#' @param local_filename Name of the file in the cache directory.
#' @param force_refresh If TRUE, force re-download of the file.
#' @return The loaded JSON content as an R list/object.
#' @noRd
load_cached_json_file <- function(file_url, local_filename, force_refresh = FALSE) {
  cached_file_path <- download_cached_file(file_url, local_filename, force = force_refresh)
  
  tryCatch({
    return(jsonlite::fromJSON(cached_file_path))
  },
  error = function(e) {
    stop(paste("Error loading JSON from", cached_file_path, ":", e$message), call. = FALSE)
  })
}

#' Load species aliases
#'
#' Loads the species_aliases.json file.
#' @param force_refresh If TRUE, force re-download of the aliases file.
#' @return A named list/vector of species aliases.
#' @noRd
load_species_aliases <- function(force_refresh = FALSE) {
  return(load_cached_json_file(SPECIES_ALIASES_URL, "species_aliases.json", force_refresh = force_refresh))
}

#' Resolve species name using aliases and canonical list
#'
#' This function resolves user-provided species names to their canonical forms using
#' an alias mapping system. Alias resolution is case-insensitive, but a warning will
#' be issued if the resolved canonical name differs from the user input (indicating
#' an alias was used).
#'
#' @param species_input User-provided species name (single character string).
#' @param canonical_species_names A character vector of valid canonical species names.
#' @param species_alias_map A named list/vector where names are lowercase aliases 
#'                          and values are canonical names. If NULL, it will be loaded
#'                          automatically from the species aliases file.
#' 
#' @details
#' The function performs the following steps:
#' \itemize{
#'   \item Converts user input to lowercase for case-insensitive matching
#'   \item Searches for the lowercase input in the alias map
#'   \item Returns the canonical name if found
#'   \item Issues a warning if the canonical name differs from user input
#'   \item Throws an error if no match is found, listing available options
#' }
#' 
#' @return The canonical species name (character string) if successfully resolved.
#' 
#' @examples
#' \dontrun{
#' # These would all resolve to "lentil" (with warnings for aliases)
#' resolve_species_name_internal("lentils", canonical_names, alias_map)  # alias
#' resolve_species_name_internal("Lentil", canonical_names, alias_map)   # case difference
#' resolve_species_name_internal("lentil", canonical_names, alias_map)   # exact match
#' }
#' 
#' @seealso \code{\link{load_species_aliases}} for loading the alias mapping
#' 
#' @noRd
resolve_species_name_internal <- function(species_input, canonical_species_names, species_alias_map = NULL) {
  if (!is.character(species_input) || length(species_input) != 1) {
    stop("species_input must be a single string.", call. = FALSE)
  }
  
  if (is.null(species_alias_map)) {
    species_alias_map <- load_species_aliases()
  }
  
  user_input_lower <- tolower(species_input)
  
  if (user_input_lower %in% names(species_alias_map)) {
    
    canonical_name <- species_alias_map[[user_input_lower]]
    
    if (species_input != canonical_name) {
      warning(paste0("Using canonical name '", canonical_name, "' for alias '", species_input, "'. ", 
                     "For a list of canonical species names, use list_species()."), call. = FALSE)
    }
    return(canonical_name)
  }
  
  pretty_available_options <- paste(shQuote(sort(canonical_species_names)), collapse = ", ")
  stop(paste0("Invalid species name: '", species_input, "'. Available options are: ", pretty_available_options, "."), call. = FALSE)
}

#' Null-safe accessor
#' @noRd
`%||%` <- function(x, y) {
  if (is.null(x)) y else x
}