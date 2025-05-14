# tests/testthat/test-functionality.R
test_that("Basic functionality works", {
  # Test listing species
  species_list <- list_species(verbose = FALSE)
  expect_type(species_list, "character")
  expect_gt(length(species_list), 0)
  
  # Test with a small dataset
  test_species <- species_list[2]  # Use the second species
  
  # Test download functionality (in temp directory)
  temp_dir <- tempfile("easygese_test")
  dir.create(temp_dir, recursive = TRUE)
  
  tryCatch({
    # Test downloading data
    species_dir <- download_data(test_species, output_dir = temp_dir)
    x_file <- file.path(species_dir, paste0(test_species, "X.csv"))
    y_file <- file.path(species_dir, paste0(test_species, "Y.csv"))
    z_file <- file.path(species_dir, paste0(test_species, "Z.json"))
    
    expect_true(file.exists(x_file))
    expect_true(file.exists(y_file))
    expect_true(file.exists(z_file))
    
    # Test loading data
    data <- load_species(test_species, download = TRUE, download_dir = temp_dir)
    expect_type(data, "list")
    expect_named(data, c("X", "Y", "Z"))
    
    # Test trait listing
    y_traits <- list_traits(data$Y)
    expect_type(y_traits, "character")
    expect_gt(length(y_traits), 0)
    
    z_traits <- list_traits(data$Z)
    expect_type(z_traits, "character")
    expect_gt(length(z_traits), 0)
    
    # Test CV indices
    trait <- z_traits[1]
    cv_indices <- get_cv_indices(data$Z, trait)
    expect_s3_class(cv_indices, "data.frame")
    expect_gt(nrow(cv_indices), 0)
    expect_gt(ncol(cv_indices), 0)
    
    # Test loading benchmark results
    results <- load_benchmark_results(summarize = TRUE)
    expect_s3_class(results, "data.frame")
    expect_gt(nrow(results), 0)
    
    # Test downloading benchmark data
    bench_dir <- file.path(temp_dir, "benchmark")
    dir.create(bench_dir, recursive = TRUE)
    download_benchmark_data(output_dir = bench_dir)
    expect_true(file.exists(file.path(bench_dir, "results_summary.csv")))
    
  }, finally = {
    # Clean up temporary directory
    unlink(temp_dir, recursive = TRUE)
  })
})