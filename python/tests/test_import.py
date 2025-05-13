# test_import.py
try:
    from easygese import (
        list_species, load_species, list_traits, 
        get_cv_indices, download_data, load_benchmark_results
    )
    print("All imports successful!")
except ImportError as e:
    print(f"Import failed: {e}")