#' @importFrom httr GET content http_error status_code
#' @importFrom jsonlite fromJSON toJSON
NULL

#' Download index
#' 
#' Downloads the index.json file from the EasyGeSe GitHub repository and caches it locally.
#' 
#' @param force If TRUE, force re-download even if cache exists
#'
#' @return Path to the cached index file
#' @export
download_index <- function(force = FALSE) {
  cache_dir <- get_cache_dir()
  cache_file <- file.path(cache_dir, "index.json")
  
  # Use cached version if available and not forcing refresh
  if (file.exists(cache_file) && !force) {
    return(cache_file)
  }
  
  tryCatch({
    message("Downloading index file...")
    response <- httr::GET(INDEX_URL)
    
    if (httr::http_error(response)) {
      stop(paste("HTTP error:", httr::status_code(response)))
    }
    
    # Save to cache
    index_content <- httr::content(response, "text")
    writeLines(index_content, cache_file)
    
    message(paste("Index file cached at", cache_file))
    return(cache_file)
  },
  error = function(e) {
    message(paste("Error downloading index:", e$message))
    if (file.exists(cache_file)) {
      message("Using existing cached index")
      return(cache_file)
    }
    stop(e)
  })
}


#' Load index
#'
#' Loads the index.json file from the EasyGeSe GitHub repository or from local cache.
#' 
#' @param force_refresh If TRUE, force re-download of index
#'
#' @return The loaded index as a list
#' @export
load_index <- function(force_refresh = FALSE) {
  cache_file <- download_index(force = force_refresh)
  
  tryCatch({
    index <- jsonlite::fromJSON(cache_file)
    return(index)
  },
  error = function(e) {
    stop(paste("Error loading index:", e$message))
  })
}



