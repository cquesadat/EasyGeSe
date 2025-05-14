#' List traits
#' 
#' This function retrieves the names of traits from either a Z object (list) or a Y object (data frame).
#'
#' @param obj Z object (list) or Y object (data frame)
#'
#' @return Vector of trait names
#' @export
list_traits <- function(obj) {
  if (is.list(obj) && !is.null(obj[["_is_easygese_Z"]])) {
    return(names(obj)[!startsWith(names(obj), "_")])
  } else if (is.data.frame(obj) && !is.null(attr(obj, "_is_easygese_Y"))) {
    return(colnames(obj))
  } else {
    stop("Expected a valid Y (data frame) or Z (list) object from EasyGeSe.")
  }
}


#' Get CV indices
#' 
#' This function retrieves the cross-validation indices for a specific trait from a Z object.
#'
#' @param z The Z object (loaded from JSON)
#' @param trait Name of the trait
#'
#' @return Data frame with 0/1 values for splits
#' @export
get_cv_indices <- function(z, trait) {
  # Check if this is a valid EasyGeSe Z object
  if (!is.list(z) || is.null(z[["_is_easygese_Z"]])) {
    stop("The provided object is not a valid EasyGeSe Z object")
  }
  
  if (!trait %in% names(z)) {
    stop(paste("Trait '", trait, "' not found. Available traits: ", 
               paste(names(z)[!startsWith(names(z), "_")], collapse = ", "), sep = ""))
  }
  
  # Since our Z object now contains properly formatted dataframes,
  # we just need to return the trait dataframe directly
  return(z[[trait]])
}