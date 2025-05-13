# test_functionality.py
from easygese import (
    list_species, load_species, list_traits, 
    get_cv_indices, download_data, load_benchmark_results
)
import os
from pathlib import Path
from appdirs import user_cache_dir

def test_functionality():
    # Test listing species
    print("\n--- Testing list_species() ---")
    species_list = list_species(verbose=False)
    print(f"Found {len(species_list)} species: {', '.join(species_list[:3])}...")
    
    # Test downloading a small dataset
    print("\n--- Testing download_data() ---")
    test_species = species_list[1] 
    species_dir = download_data(test_species)
    print(f"Downloaded data to: {species_dir}")
    print(f"Files exist: {(species_dir / 'X.csv').exists()}, {(species_dir / 'Y.csv').exists()}, {(species_dir / 'Z.json').exists()}")
    
    # Test loading species data
    print("\n--- Testing load_species() ---")
    X, Y, Z = load_species(test_species)
    print(f"X shape: {X.shape}, Y shape: {Y.shape}, Z traits: {len([k for k in Z.keys() if not k.startswith('_')])}")
    
    # Test listing traits
    print("\n--- Testing list_traits() ---")
    y_traits = list_traits(Y)
    z_traits = list_traits(Z)
    print(f"Y traits: {len(y_traits)}, first trait: {y_traits[0]}")
    print(f"Z traits: {len(z_traits)}, first trait: {z_traits[0]}")
    
    # Test getting CV indices
    print("\n--- Testing get_cv_indices() ---")
    trait = z_traits[0]
    cv_indices = get_cv_indices(Z, trait)
    print(f"CV indices shape for trait {trait}: {cv_indices.shape}")
    
    # Test loading benchmark data
    print("\n--- Testing load_benchmark_results() ---")
    results = load_benchmark_results(species=test_species)
    print(f"Benchmark results shape: {results.shape}")
    
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    test_functionality()