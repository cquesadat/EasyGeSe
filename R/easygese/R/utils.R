#' @importFrom rappdirs user_cache_dir
NULL

# Constants
#' @noRd
INDEX_URL <- "https://raw.githubusercontent.com/cquesadat/EasyGeSe/main/datasets/index.json"


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

#' Null-safe accessor
#' @noRd
`%||%` <- function(x, y) {
  if (is.null(x)) y else x
}