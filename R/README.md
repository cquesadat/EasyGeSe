# EasyGeSe R Package

A simple R tool for loading benchmark datasets for genomic selection.

## Installation

Install directly from GitHub with devtools:

```r
# Install devtools if not already installed
install.packages("devtools")

# Install easygese
devtools::install_github("cquesadat/EasyGeSe", subdir = "R/easygese")
```

## Quick Start

```r
library(easygese)

# See available species with detailed information
list_species(detailed = TRUE)

# Load datasets for a specific species
data <- load_species("bean")

# Extract components from the data
X <- data$X  # Genotypic data (markers)
Y <- data$Y  # Phenotypic data (traits)
Z <- data$Z  # Cross-validation splits

# Explore available traits
traits_y <- list_traits(Y)  # or list_traits(Z)

# Get CV indices for a specific trait
cv_indices <- get_cv_indices(Z, traits_y[1])
```

## Data Access

EasyGeSe loads data from remote sources by default but provides flexible caching options:

```r
# Load data (tries online sources first, falls back to local cache)
data <- load_species("bean")

# Explicitly download data to default cache directory
data <- load_species("bean", download = TRUE)

# Explicitly download to a custom directory
data <- load_species("bean", download = TRUE, download_dir = "./my_data")

# Download data separately for offline use
download_data("barley") # default cache 
download_data("barley", output_dir = "./my_data") # custom directory
``` 

## Benchmark Results 

Access pre-computed model benchmark results across multiple species and traits. Details of the benchmarking process are described in the paper:

```r
# Get all benchmark results (loads from online by default)
results <- load_benchmark_results()

# Filter results by species, traits, and/or models
bean_results <- load_benchmark_results(species = "bean")
model_comparison <- load_benchmark_results(models = c("GBLUP", "XGBoost"))
trait_results <- load_benchmark_results(species = "barley", traits = "DF")

# Explicitly download benchmark data
results <- load_benchmark_results(download = TRUE)

# Download to custom directory
results <- load_benchmark_results(download = TRUE, download_dir = "./my_data")

# Use raw results instead of summary results
raw_results <- load_benchmark_results(summarize = FALSE)
``` 

## Functions

| Function | Description |
|----------|-------------|
| `list_species()` | Lists available species datasets |
| `load_species(species, download = FALSE, download_dir = NULL)` | Loads X, Y, Z data matrices for a species |
| `list_traits(obj)` | Lists available traits from Y or Z object |
| `get_cv_indices(z, trait)` | Returns cross-validation indices for a specific trait |
| `load_benchmark_results(...)` | Loads benchmark results with filtering options |
| `download_index(force = FALSE)` | Downloads and caches the species index file |
| `download_data(species, output_dir = NULL)` | Downloads species data files to local storage |
| `download_benchmark_data(output_dir = NULL, force = FALSE)` | Downloads benchmark data files |

See function documentation (`?function_name`) for detailed parameter information.

## Citation

When using this package for research, please cite both the EasyGeSe database and the original data sources as printed when loading species data.

[Citation will be added when published]