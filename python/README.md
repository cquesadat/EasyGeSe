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

# See available species
list_species()

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

EasyGeSe loads data from remote sources by default. We are developing a local alternative. 

## Functions

| Function | Description |
|----------|-------------|
| `list_species()` | Lists available species datasets |
| `load_species(species)` | Loads X, Y, Z data matrices for a species |
| `list_traits(obj)` | Lists available traits from Y or Z object |
| `get_cv_indices(z, trait)` | Returns cross-validation indices for a specific trait |

See function docstrings for detailed parameter information.

## Citation

When using this package for research, please cite both the EasyGeSe database and the original data sources as printed when loading species data.

To add citation when published