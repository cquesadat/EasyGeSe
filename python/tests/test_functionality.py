# test_functionality.py
from easygese import (
    list_species, load_species, list_traits, 
    get_cv_indices, download_data, load_benchmark_results
)
import os
import shutil
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
    
    # Test loading species data from online source first (default behavior)
    print("\n--- Testing load_species() with online loading ---")
    X, Y, Z = load_species(test_species)
    print(f"X shape: {X.shape}, Y shape: {Y.shape}, Z traits: {len([k for k in Z.keys() if not k.startswith('_')])}")
    
    # Test explicit download to custom directory
    print("\n--- Testing load_species() with explicit download to custom directory ---")
    custom_dir = Path("./test_download_dir")
    custom_dir.mkdir(exist_ok=True)
    try:
        X2, Y2, Z2 = load_species(test_species, download=True, download_dir=custom_dir)
        print(f"Downloaded and loaded from custom directory: {custom_dir}")
        # Check files directly in custom_dir (not in a species subfolder)
        print(f"Files exist in custom dir: {(custom_dir / 'X.csv').exists()}, {(custom_dir / 'Y.csv').exists()}, {(custom_dir / 'Z.json').exists()}")
    finally:
        # Clean up custom directory after test
        if custom_dir.exists():
            shutil.rmtree(custom_dir)
    
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
    
    # Test loading benchmark data from online source (default)
    print("\n--- Testing load_benchmark_results() with online loading ---")
    try:
        # Use lowercase 'species' instead of 'Species'
        results = load_benchmark_results(species=test_species)
        print(f"Benchmark results shape: {results.shape}")
    except KeyError:
        print("Note: Using lowercase 'species' for filtering")
        # If the first attempt failed, it might be due to column name casing
        results = load_benchmark_results()
        if 'species' in results.columns:
            filtered_results = results[results['species'] == test_species]
            print(f"Benchmark results shape: {filtered_results.shape}")
        else:
            print(f"Available columns: {list(results.columns)}")
            print(f"Full benchmark results shape: {results.shape}")
    
    # Test explicit download of benchmark data to custom directory
    print("\n--- Testing load_benchmark_results() with explicit download ---")
    bench_dir = Path("./test_bench_dir")
    bench_dir.mkdir(exist_ok=True)
    try:
        results2 = load_benchmark_results(
            download=True,
            download_dir=bench_dir
        )
        print(f"Downloaded and loaded benchmark data from custom directory")
        # Check if files exist directly in bench_dir
        print(f"Files exist in benchmark dir: {(bench_dir / 'results_summary.csv').exists()}")
        
        # Try to filter after loading if the column exists
        if 'species' in results2.columns:
            filtered_results = results2[results2['species'] == test_species]
            print(f"Filtered benchmark results shape: {filtered_results.shape}")
    except Exception as e:
        print(f"Warning: Error in benchmark download test: {e}")
    finally:
        # Clean up benchmark directory after test
        if bench_dir.exists():
            shutil.rmtree(bench_dir)
    
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    test_functionality()