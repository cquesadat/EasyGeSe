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
  # INDEX_URL is defined in utils.R
  return(download_cached_file(INDEX_URL, "index.json", force = force))
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
  # INDEX_URL is defined in utils.R
  return(load_cached_json_file(INDEX_URL, "index.json", force_refresh = force_refresh))
}



