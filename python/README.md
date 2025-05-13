# EasyGeSe Python Package

A simple Python tool for loading benchmark datasets for genomic selection.

## Installation

Install directly from GitHub with pip:

```bash
pip install git+https://github.com/cquesadat/EasyGeSe.git#subdirectory=python
```

## Quick Start

```python
from easygese import load_species, list_species, list_traits, get_cv_indices

# See available species with detailed information
list_species(detailed=True)

# Load datasets for a specific species
X, Y, Z = load_species("bean")

# X: Genotypic data (markers)
# Y: Phenotypic data (traits)
# Z: Cross-validation splits

# Explore available traits
traits = list_traits(Y)  # or list_traits(Z)

# Get CV indices for a specific trait
cv_indices = get_cv_indices(Z, traits[0])
```

## Data Access

EasyGeSe loads data from remote sources by default but provides flexible caching options:

```python
# Load data (tries online sources first, falls back to local cache)
X, Y, Z = load_species("bean")

# Explicitly download data to default cache directory
X, Y, Z = load_species("bean", download=True)

# Explicitly download to a custom directory
X, Y, Z = load_species("bean", download=True, download_dir="./my_data")

# Download data separately for offline use
download_data("barley") # default cache 
download_data("barley", output_dir="./my_data") #custom directory
``` 
## Benchmark results 

Access pre-computed model benchmark results across multiple species and tratis. Quiddities of the benchmarking process are described in detail in the paper

```python
# Get all benchmark results (loads from online by default)
results = load_benchmark_results()

# Filter results by species, traits, and/or models
bean_results = load_benchmark_results(species="bean")
model_comparison = load_benchmark_results(models=["GBLUP", "XGBoost"])
trait_results = load_benchmark_results(species="barley", traits=["DF"])

# Explicitly download benchmark data
results = load_benchmark_results(download=True)

# Download to custom directory
results = load_benchmark_results(download=True, download_dir="./my_data")

# Use raw results instead of summary results
raw_results = load_benchmark_results(summarize=False)
``` 

## Functions

| Function | Description |
|----------|-------------|
| `list_species()` | Lists available species datasets |
| `load_species(species, download=False, download_dir=None)` | Loads X, Y, Z data matrices for a species |
| `list_traits(obj)` | Lists available traits from Y or Z object |
| `get_cv_indices(z, trait)` | Returns cross-validation indices for a specific trait |
| `load_benchmark_results(...)` | Loads benchmark results with filtering options |
| `download_index(force=False)` | Downloads and caches the species index file |
| `download_data(species, output_dir=None)` | Downloads species data files to local storage |
| `download_benchmark_data(force=False)` | Downloads benchmark data files |
See function docstrings for detailed parameter information.

## Citation

When using this package for research, please cite both the EasyGeSe database and the original data sources as printed when loading species data.

To add citation when published