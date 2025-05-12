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

# Download data for offline use
from easygese import download_data
download_data("bean")

# Load benchmark results for a species
from easygese import load_benchmark_results
results = load_benchmark_results(species="bean")
```

## Data Access

EasyGeSe loads data from remote sources by default but provides flexible caching options:

```python
# Download species data locally for offline use
download_data("barley")

# Load using locally cached data
X, Y, Z = load_species("barley", use_local=True)

# Specify custom directory for data
X, Y, Z = load_species("barley", use_local=True, data_dir="/path/to/data")
``` 
## Benchmark results 

Access pre-computed model benchmark results across multiple species and tratis. Quiddities of the benchmarking process are described in detail in the paper

```python
# Get all benchmark results
results = load_benchmark_results()

# Filter results by species, traits, and/or models
bean_results = load_benchmark_results(species="bean")
model_comparison = load_benchmark_results(models=["GBLUP", "XGBoost"])
trait_results = load_benchmark_results(species="barley", traits=["BaMMV"])

# Download benchmark data for offline use
download_benchmark_data()
``` 

## Functions

| Function | Description |
|----------|-------------|
| `list_species()` | Lists available species datasets |
| `load_species(species)` | Loads X, Y, Z data matrices for a species |
| `list_traits(obj)` | Lists available traits from Y or Z object |
| `get_cv_indices(z, trait)` | Returns cross-validation indices for a specific trait |
| `download_data(species, output_dir=None)` | Downloads species data files to local storage |
| `download_benchmark_data(force=False, output_dir=None)` | Downloads benchmark data files |
| `load_benchmark_results(...)` | Loads benchmark results with filtering options |
| `download_index(force=False)` | Downloads and caches the species index file |

See function docstrings for detailed parameter information.

## Citation

When using this package for research, please cite both the EasyGeSe database and the original data sources as printed when loading species data.

To add citation when published