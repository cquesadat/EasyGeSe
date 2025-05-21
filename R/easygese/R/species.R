#' @importFrom httr GET content http_error status_code
#' @importFrom jsonlite fromJSON
#' @importFrom utils read.csv
#' @importFrom knitr kable
NULL

#' List species
#'
#' Lists all available species in the EasyGeSe dataset.
#' 
#' @param verbose If TRUE, prints a nicely formatted list
#' @param detailed If TRUE, displays extended metadata in tabular format
#'
#' @return List of species names (sorted, case-preserved)
#' @export
list_species <- function(verbose = TRUE, detailed = TRUE) {
  index <- load_index()
  species_list <- sort(names(index))
  
  if (!verbose) {
    return(species_list)
  }
  
  message("EasyGeSe Genomic Datasets\n")
  
  if (detailed && requireNamespace("knitr", quietly = TRUE)) {
    # Prepare data for table
    rows <- list()
    for (species in species_list) {
      entry <- index[[species]]
      metadata <- entry$metadata %||% list()
      
      # Get metadata or use placeholders
      n_markers <- metadata$n_markers %||% "?"
      n_genotypes <- metadata$n_genotypes %||% "?"
      n_traits <- metadata$n_traits %||% "?"
      
      rows[[length(rows) + 1]] <- c(
        species,
        n_markers,
        n_genotypes,
        n_traits
      )
    }
    
    # Create and print table
    df <- as.data.frame(do.call(rbind, rows))
    colnames(df) <- c("Species", "Markers", "Genotypes", "Traits")
    print(knitr::kable(df))
  } else if (detailed) {
    message("Install 'knitr' package for detailed view: install.packages('knitr')")
    detailed <- FALSE
  }
  
  if (!detailed) {
    for (sp in species_list) {
      message(paste(" -", sp))
    }
  }
  
  message("\nUsage examples:")
  message("  library(easygese)")
  if (length(species_list) > 0) {
    example_species <- species_list[min(2, length(species_list))]
    message(paste0("  data <- load_species('", example_species, "')  # Load dataset"))
    message(paste0("  download_data('", example_species, "')         # Download for offline use"))
  }
  
  return(invisible(species_list))
}


#' Download data 
#'
#' Downloads the X (genotype), Y (phenotype), and Z (CV splits) datasets for a specified species.
#' 
#' @param species Species name to download
#' @param output_dir Directory to save files. Defaults to user cache directory
#'
#' @return Path to directory containing the downloaded files
#' @export
download_data <- function(species, output_dir = NULL) {
  index <- load_index()
  if (!species %in% names(index)) {
    stop(paste("Species '", species, "' not found in the index", sep = ""))
  }
  
  # Set up the output directory
  if (is.null(output_dir)) {
    output_dir <- get_cache_dir()
  } else {
    if (!dir.exists(output_dir)) {
      dir.create(output_dir, recursive = TRUE)
    }
  }
  
  entry <- index[[species]]
  
  # Define filenames with species prefix
  x_filename <- paste0(species, "X.csv")
  y_filename <- paste0(species, "Y.csv")
  z_filename <- paste0(species, "Z.json")
  
  # Check if files already exist
  x_exists <- file.exists(file.path(output_dir, x_filename))
  y_exists <- file.exists(file.path(output_dir, y_filename))
  z_exists <- file.exists(file.path(output_dir, z_filename))
  
  if (x_exists && y_exists && z_exists) {
    message(paste("All files for", species, "already exist in", output_dir))
    return(output_dir)
  }
  
  message(paste("Downloading", species, "data files..."))
  
  # Download only missing files
  if (!x_exists) {
    message(paste("Downloading", x_filename, "..."))
    response <- httr::GET(entry$X)
    if (httr::http_error(response)) {
      stop(paste("Error downloading X data:", httr::status_code(response)))
    }
    writeBin(httr::content(response, "raw"), file.path(output_dir, x_filename))
  }
  
  if (!y_exists) {
    message(paste("Downloading", y_filename, "..."))
    response <- httr::GET(entry$Y)
    if (httr::http_error(response)) {
      stop(paste("Error downloading Y data:", httr::status_code(response)))
    }
    writeBin(httr::content(response, "raw"), file.path(output_dir, y_filename))
  }
  
  if (!z_exists) {
    message(paste("Downloading", z_filename, "..."))
    response <- httr::GET(entry$Z)
    if (httr::http_error(response)) {
      stop(paste("Error downloading Z data:", httr::status_code(response)))
    }
    writeBin(httr::content(response, "raw"), file.path(output_dir, z_filename))
  }
  
  message(paste("Downloaded", species, "data to", output_dir))
  return(output_dir)
}


#' Load species
#' 
#' Loads the X (genotype), Y (phenotype), and Z (CV splits) datasets for a specified species.
#'
#' @param species Name of the species to load
#' @param download If TRUE, download data to local storage
#' @param download_dir Directory to save files if downloading. Defaults to user cache directory
#'
#' @return A list containing X, Y, and Z data
#' @export
load_species <- function(species, download = FALSE, download_dir = NULL) {
  index <- load_index() # Uses refactored load_index
  canonical_species_names <- names(index)
  # species_alias_map can be loaded directly by resolve_species_name_internal if passed as NULL
  
  # Resolve species name
  species <- resolve_species_name_internal(species, canonical_species_names, species_alias_map = NULL) 
  
  # Define filenames with the resolved (canonical) species prefix
  x_filename <- paste0(species, "X.csv")
  y_filename <- paste0(species, "Y.csv")
  z_filename <- paste0(species, "Z.json")
  
  # Determine directory to use
  data_dir <- if (is.null(download_dir)) get_cache_dir() else download_dir
  
  # Check if files exist in the specified directory
  files_exist <- dir.exists(data_dir) &&
    file.exists(file.path(data_dir, x_filename)) &&
    file.exists(file.path(data_dir, y_filename)) &&
    file.exists(file.path(data_dir, z_filename))
  
  # If files exist locally, load them directly
  if (files_exist) {
    message(paste("Loading data from", data_dir, "..."))
    X <- read.csv(file.path(data_dir, x_filename), row.names = 1)
    attr(X, "_is_easygese_X") <- TRUE
    
    Y <- read.csv(file.path(data_dir, y_filename), row.names = 1)
    attr(Y, "_is_easygese_Y") <- TRUE
    
    # Load Z as raw JSON first
    Z_raw <- jsonlite::fromJSON(file.path(data_dir, z_filename))
    # Process Z to ensure traits contain proper dataframes
    Z <- process_z_object(Z_raw)
  }
  # If files don't exist and download is requested, download them
  else if (download) {
    message(paste("Files not found in", data_dir, ". Downloading..."))
    download_data(species, output_dir = data_dir)
    
    # Now load from the downloaded files
    X <- read.csv(file.path(data_dir, x_filename), row.names = 1)
    attr(X, "_is_easygese_X") <- TRUE
    
    Y <- read.csv(file.path(data_dir, y_filename), row.names = 1)
    attr(Y, "_is_easygese_Y") <- TRUE
    
    # Load Z as raw JSON first
    Z_raw <- jsonlite::fromJSON(file.path(data_dir, z_filename))
    # Process Z to ensure traits contain proper dataframes
    Z <- process_z_object(Z_raw)
  }
  # If files don't exist and download not requested, try online loading
  else {
    tryCatch({
      # Get the URLs from the index
      entry <- index[[species]]
      
      message("Loading data from online sources...")
      # Load X (genotype) data directly from URL
      X <- read.csv(entry$X, row.names = 1)
      attr(X, "_is_easygese_X") <- TRUE
      
      # Load Y (phenotype) data directly from URL
      Y <- read.csv(entry$Y, row.names = 1)
      attr(Y, "_is_easygese_Y") <- TRUE
      
      # Load Z (CV splits) data directly from URL
      response <- httr::GET(entry$Z)
      if (httr::http_error(response)) {
        stop(paste("HTTP error:", httr::status_code(response)))
      }
      Z_raw <- jsonlite::fromJSON(httr::content(response, "text"))
      # Process Z to ensure traits contain proper dataframes
      Z <- process_z_object(Z_raw)
    },
    error = function(e) {
      stop(paste("Failed to load data from online source:", e$message,
                 "\nNo local data found at", data_dir, "and online loading failed."))
    })
  }
  
  # Print citation info
  if (!is.null(index[[species]]$citation)) {
    message(paste("\nCitation for", species, "dataset:"))
    message(index[[species]]$citation)
  }
  
  # Return as a named list (different from Python which returns a tuple)
  result <- list(X = X, Y = Y, Z = Z)
  return(result)
}

#' Process Z object 
#' 
#' This function processes the raw Z object loaded from JSON to ensure that each trait is represented 
#' as a proper dataframe, handling varying lengths due to missing values.
#'
#' @param z_raw Raw Z object loaded from JSON
#' @return Processed Z object with proper dataframes
#' @noRd
process_z_object <- function(z_raw) {
  Z <- list()
  Z[["_is_easygese_Z"]] <- TRUE
  
  # Get trait names (skip metadata fields)
  trait_names <- names(z_raw)[!startsWith(names(z_raw), "_")]
  
  # Define the 25 columns (5 splits × 5 CV folds)
  expected_columns <- c()
  for (cv in 1:5) {
    for (split in 1:5) {
      expected_columns <- c(expected_columns, paste0("Split", split, "CV", cv))
    }
  }
  
  # Process each trait
  for (trait in trait_names) {
    trait_data <- z_raw[[trait]]
    
    # Get all genotype names (rows)
    genotype_names <- names(trait_data)
    
    # Create an empty data frame with genotypes as rows and CV splits as columns
    df <- data.frame(matrix(ncol=length(expected_columns), nrow=length(genotype_names)))
    colnames(df) <- expected_columns
    rownames(df) <- genotype_names
    
    # Fill data row by row
    for (geno in genotype_names) {
      for (col in expected_columns) {
        df[geno, col] <- trait_data[[geno]][[col]]
      }
    }
    
    Z[[trait]] <- df
  }
  
  return(Z)
}