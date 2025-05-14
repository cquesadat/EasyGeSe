# tests/testthat/test-import.R
test_that("All functions are properly exported", {
  # Check that essential functions are available
  functions_to_check <- c("list_species", "load_species", "list_traits", 
                        "get_cv_indices", "download_data", "load_benchmark_results",
                        "download_index", "download_benchmark_data")
  
  for (fn in functions_to_check) {
    expect_true(exists(fn, envir = asNamespace("easygese")), 
                info = paste("Function", fn, "should be exported"))
  }
})