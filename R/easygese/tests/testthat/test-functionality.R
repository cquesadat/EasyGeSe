library(testthat)
library(easygese) # Assuming resolve_species_name_internal is an internal function here
# No need for httr or mockery for this simplified version

# Path to your local test aliases file
# Make sure this file exists at: t:/myGit/EasyGeSe/R/easygese/tests/testthat/testdata/species_aliases_test.json
LOCAL_ALIASES_PATH <- test_path("testdata", "species_aliases_test.json")

# Define a simple list of canonical names that your alias file maps to
MOCK_CANONICAL_NAMES <- c("lentil", "bean", "wheatG", "maize") # Adjust if your test aliases map to others

context("Species Name Resolution (Simplified)")

test_that("resolve_species_name_internal works correctly with local alias data", {
  # Check if the local alias file exists first
  if (!file.exists(LOCAL_ALIASES_PATH)) {
    skip(paste("Local alias file not found, skipping this test:", LOCAL_ALIASES_PATH))
  }
  
  # Load the alias map directly from your local JSON file
  species_alias_map <- jsonlite::fromJSON(LOCAL_ALIASES_PATH)

  # Test cases based on your species_aliases_test.json content
  # Example: if species_aliases_test.json contains:
  # {
  #   "lentils": "lentil",
  #   "lens culinaris": "lentil",
  #   "common bean": "bean",
  #   "bread wheat": "wheatG",
  #   "corn": "maize"
  # }

  # Exact match (should return itself if canonical)
  expect_equal(easygese:::resolve_species_name_internal("lentil", MOCK_CANONICAL_NAMES, species_alias_map = species_alias_map), "lentil")
  
  # Alias matches (these depend on your species_aliases_test.json)
  expect_equal(easygese:::resolve_species_name_internal("lentils", MOCK_CANONICAL_NAMES, species_alias_map = species_alias_map), "lentil")
  # Add more alias tests based on your file:
  # expect_equal(easygese:::resolve_species_name_internal("lens culinaris", MOCK_CANONICAL_NAMES, species_alias_map = species_alias_map), "lentil")
  # expect_equal(easygese:::resolve_species_name_internal("common bean", MOCK_CANONICAL_NAMES, species_alias_map = species_alias_map), "bean")
  expect_equal(easygese:::resolve_species_name_internal("corn", MOCK_CANONICAL_NAMES, species_alias_map = species_alias_map), "maize") # Assuming "corn" maps to "maize"
  expect_equal(easygese:::resolve_species_name_internal("wheat", MOCK_CANONICAL_NAMES, species_alias_map = species_alias_map), "wheatG") # Assuming "wheat" maps to "wheatG"


  # Case insensitivity (if your function is designed to be case-insensitive for aliases)
  expect_equal(easygese:::resolve_species_name_internal("LENTILS", MOCK_CANONICAL_NAMES, species_alias_map = species_alias_map), "lentil")
  # expect_equal(easygese:::resolve_species_name_internal("CORN", MOCK_CANONICAL_NAMES, species_alias_map = species_alias_map), "maize")

  # Non-existent species
  sorted_mock_options <- paste(shQuote(sort(MOCK_CANONICAL_NAMES)), collapse = ", ")
  expected_error_msg_potato <- paste0("Invalid species name: 'potato'. Available options are: ", sorted_mock_options, ".")
  expect_error(
    easygese:::resolve_species_name_internal("potato", MOCK_CANONICAL_NAMES, species_alias_map = species_alias_map),
    regexp = expected_error_msg_potato, # Use regexp for flexibility if message varies slightly
    fixed = TRUE # If the message is exact
  )

  # What if an alias exists but its target is NOT in MOCK_CANONICAL_NAMES?
  # (This depends on how resolve_species_name_internal handles this scenario)
  # Example: if species_aliases_test.json has "alien_fruit": "kryptonite_pear"
  # and "kryptonite_pear" is not in MOCK_CANONICAL_NAMES.
  # species_alias_map_extended <- c(species_alias_map, list(alien_fruit = "kryptonite_pear"))
  # expect_error(
  #   easygese:::resolve_species_name_internal("alien_fruit", MOCK_CANONICAL_NAMES, species_alias_map = species_alias_map_extended),
  #   "Some error about alias target not being a canonical name" # Adjust expected error
  # )
})

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
    
  }, finally = {
    # Clean up temporary directory
    unlink(temp_dir, recursive = TRUE)
  })
})

# You can add more test_that blocks if you want to test other aspects of 
# resolve_species_name_internal in isolation.
