from pathlib import Path
import requests
import pandas as pd
import json
from typing import List, Optional, Union
from appdirs import user_cache_dir

# Remote location of index file
INDEX_URL = "https://raw.githubusercontent.com/cquesadat/EasyGeSe/main/datasets/index.json"

# Use a single, consistent cache directory
CACHE_DIR = Path(user_cache_dir("easygese", "easygese"))
# Create cache directory if it doesn't exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def download_index(force=False):
    """
    Download and cache the index.json file.
    
    Parameters:
    - force (bool): If True, force re-download even if cache exists
    
    Returns:
    - Path to the cached index file
    """
    cache_file = CACHE_DIR / "index.json"
    
    # Use cached version if available and not forcing refresh
    if cache_file.exists() and not force:
        return cache_file
        
    try:
        print("Downloading index file...")
        response = requests.get(INDEX_URL, timeout=10)
        response.raise_for_status()
        
        # Save to cache
        with open(cache_file, "w") as f:
            f.write(response.text)
            
        print(f"Index file cached at {cache_file}")
        return cache_file
    except Exception as e:
        print(f"Error downloading index: {e}")
        if cache_file.exists():
            print("Using existing cached index")
            return cache_file
        raise

def load_index(force_refresh=False):
    """
    Load the index.json from cache or remote GitHub repo.
    
    Parameters:
    - force_refresh (bool): If True, force re-download of index
    
    Returns:
    - The loaded index as a dictionary
    """
    cache_file = download_index(force=force_refresh)
    
    try:
        with open(cache_file, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading index: {e}")
        raise
               
def list_species(verbose=True, detailed=True):
    """
    List available species datasets with metadata.

    Parameters:
    - verbose (bool): If True, prints a nicely formatted list.
                     If False, returns just the list of species names.
    - detailed (bool): If True, displays extended metadata in tabular format.

    Returns:
    - list of species names (sorted, case-preserved)
    """
    index = load_index()
    species_list = sorted(index.keys())

    if not verbose:
        return species_list
        
    print("EasyGeSe Genomic Datasets\n")
    
    if detailed:
        try:
            from tabulate import tabulate
            
            # Prepare data for table
            rows = []
            for species in species_list:
                entry = index[species]
                metadata = entry.get("metadata", {})
                
                # Get metadata or use placeholders
                n_markers = metadata.get("n_markers", "?")
                n_genotypes = metadata.get("n_genotypes", "?")
                n_traits = metadata.get("n_traits", "?")
                
                rows.append([
                    species, 
                    n_markers,
                    n_genotypes,
                    n_traits
                ])
            
            # Create and print table
            headers = ["Species", "Markers", "Genotypes", "Traits"]
            table = tabulate(rows, headers=headers, tablefmt="pretty", colalign=("left", "right", "right", "right"))
            print(table)
        except ImportError:
            print("Install 'tabulate' package for detailed view: pip install tabulate")
            detailed = False
            
    if not detailed:
        for sp in species_list:
            print(f" - {sp}")
            
    print("\nUsage examples:")
    print("  from easygese import load_species")
    if species_list:
        example_species = species_list[1]
        print(f"  X, Y, Z = load_species('{example_species}')  # Load dataset")
        print(f"  download_data('{example_species}')           # Download for offline use")


def download_data(species, output_dir=None):
    """
    Download raw data files for a species to a local directory.
    
    Parameters:
    - species (str): Species name to download
    - output_dir (str or Path, optional): Directory to save files.
                                         Defaults to user cache directory
    
    Returns:
    - Path object: Directory containing the downloaded files
    """
    index = load_index()
    if species not in index:
        raise ValueError(f"Species '{species}' not found in the index")
        
    # Set up the output directory
    if output_dir is None:
        output_dir = CACHE_DIR / species
    else:
        output_dir = Path(output_dir)
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    entry = index[species]
    print(f"Downloading {species} data files...")
    
    # Download X (genotype) data
    print("Downloading X (genotype) data...")
    response = requests.get(entry["X"])
    response.raise_for_status()
    with open(output_dir / "X.csv", "wb") as f:
        f.write(response.content)
    
    # Download Y (phenotype) data
    print("Downloading Y (phenotype) data...")
    response = requests.get(entry["Y"])
    response.raise_for_status()
    with open(output_dir / "Y.csv", "wb") as f:
        f.write(response.content)
    
    # Download Z (CV splits) data
    print("Downloading Z (CV splits) data...")
    response = requests.get(entry["Z"])
    response.raise_for_status()
    with open(output_dir / "Z.json", "wb") as f:
        f.write(response.content)
    
    print(f"Downloaded {species} data to {output_dir}")
    return output_dir

def load_species(species, use_remote=True):
    """
    Load the X, Y, and Z datasets for a given species. It outputs three
    different objects, the function should be called as:
    X, Y, Z = load_species('species_name')
    
    Parameters:
    - species (str): Name of the species to load
    - use_remote (bool): If True, always download from remote, otherwise try local cache first
    """
    index = load_index()
    if species not in index:
        raise ValueError(f"Species '{species}' not found in the index")

    species_dir = CACHE_DIR / species
    local_files_exist = (species_dir.exists() and
                        (species_dir / "X.csv").exists() and
                        (species_dir / "Y.csv").exists() and
                        (species_dir / "Z.json").exists())
    
    # Download data if needed
    if use_remote or not local_files_exist:
        download_data(species)
    
    # Load the data
    X = pd.read_csv(species_dir / "X.csv", index_col=0)
    X.attrs["_is_easygese_X"] = True
    
    Y = pd.read_csv(species_dir / "Y.csv", index_col=0)
    Y.attrs["_is_easygese_Y"] = True
    
    with open(species_dir / "Z.json", "r") as f:
        Z = json.load(f)
    Z["_is_easygese_Z"] = True
    
    # Print citation info
    if "citation" in index[species]:
        print(f"\nCitation for {species} dataset:")
        print(index[species]["citation"])
    
    return X, Y, Z

def list_traits(obj):
    """
    List available traits from either:
    - Z object (dict), where keys are trait names
    - Y object (DataFrame), where columns are traits

    Parameters:
    - obj: dict or pd.DataFrame

    Returns:
    - list of trait names
    """
    if isinstance(obj, dict) and obj.get("_is_easygese_Z", False):
        return [k for k in obj.keys() if not k.startswith("_")] 
    elif isinstance(obj, pd.DataFrame) and obj.attrs.get("_is_easygese_Y", False):
        return list(obj.columns)
    else:
        raise TypeError("Expected a valid Y (DataFrame) or Z (dict) object from EasyGeSe.")

def get_cv_indices(z, trait):
    """
    Return a pandas DataFrame with 5x5 cross-validation splits for a specific trait.
    Rows = genotypes, Columns = split labels (e.g. Split1CV1, Split2CV1, ...). If you don't
    remember the trait name, use `list_traits(z)` to find it.
    
    Parameters:
    - z: the Z object (loaded from JSON)
    - trait: string, name of the trait

    Returns:
    - pd.DataFrame with 0/1 values for splits
    """
    if trait not in z:
        raise ValueError(f"Trait '{trait}' not found. Available traits: {', '.join(z.keys())}")
    
    trait_data = z[trait] 
    df = pd.DataFrame.from_dict(trait_data, orient='index')
    df.index.name = "Genotype"
    return df

def download_benchmark_data(force=False):
    """
    Download benchmark result files to local cache.
    
    Parameters:
    - force (bool): If True, force re-download even if cache exists
    
    Returns:
    - Path object: Directory containing the downloaded files
    """
    # Base GitHub URL (derived from index URL)
    base_url = "/".join(INDEX_URL.split("/")[:-1]) + "/"
    
    # Set up the output directory
    benchmark_dir = CACHE_DIR / "benchmarks"
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    
    # Define benchmark files to download
    benchmark_files = {
        "results_raw.csv": base_url + "results_raw.csv",
        "results_summary.csv": base_url + "results_summary.csv"
    }
    
    for filename, url in benchmark_files.items():
        output_file = benchmark_dir / filename
        if output_file.exists() and not force:
            print(f"Using cached {filename}")
            continue
            
        print(f"Downloading {filename}...")
        try:
            response = requests.get(url)
            response.raise_for_status()
            with open(output_file, "wb") as f:
                f.write(response.content)
        except Exception as e:
            print(f"Error downloading {filename}: {e}")
    
    return benchmark_dir

def load_benchmark_results(
    species=None,
    traits=None,
    models=None,
    summarize=True
):
    """
    Load benchmark results, downloading if necessary.
    
    Parameters:
    -----------
    species : str or list of str, optional
        Species to filter by (e.g., "barley", "bean", "lentil").
    traits : str or list of str, optional
        Traits to filter by (e.g., "BaMMV", "DF", "DTF").
    models : str or list of str, optional
        Models to filter by (e.g., "BayesA", "GBLUP", "XGBoost").
    summarize : bool
        Whether to use summarized results (True) or raw results (False).
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame containing the benchmark results, filtered as specified.
    """
    # Determine which file to use
    filename = "results_summary.csv" if summarize else "results_raw.csv"
    benchmark_dir = CACHE_DIR / "benchmarks"
    file_path = benchmark_dir / filename
    
    # Download if needed
    if not file_path.exists():
        benchmark_dir = download_benchmark_data()
        file_path = benchmark_dir / filename
    
    # Load the CSV file
    df = pd.read_csv(file_path)
    
    # Convert single values to lists for consistent filtering
    if isinstance(species, str):
        species = [species]
    if isinstance(traits, str):
        traits = [traits]
    if isinstance(models, str):
        models = [models]
    
    # Apply filters if provided
    if species is not None:
        df = df[df["Species"].isin(species)]
    if traits is not None:
        df = df[df["Trait"].isin(traits)]
    if models is not None:
        df = df[df["Model"].isin(models)]
    
    return df