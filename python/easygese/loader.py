import json
import pandas as pd
import requests
from pathlib import Path
import io
from requests.exceptions import RequestException
from typing import List, Optional, Union
from appdirs import user_cache_dir

# Remote location of index file
INDEX_URL = "https://raw.githubusercontent.com/cquesadat/EasyGeSe/main/datasets/index.json"

# For development
DEV_CACHE_DIR = Path(__file__).parent / "data"
if not DEV_CACHE_DIR.exists():
    DEV_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# For released package (platform-appropriate user cache directory)
USER_CACHE_DIR = Path(user_cache_dir("easygese", "easygese"))

# Select which one to use (development vs production)
DEFAULT_CACHE_DIR = DEV_CACHE_DIR  # Switch to USER_CACHE_DIR for release

def download_index(force=False):
    """
    Download and cache the index.json file.
    
    Parameters:
    - force (bool): If True, force re-download even if cache exists
    
    Returns:
    - Path to the cached index file
    """
    cache_file = DEFAULT_CACHE_DIR / "index.json"
    
    # If cached and not forced, skip download
    if cache_file.exists() and not force:
        print("Using cached index file")
        return cache_file
        
    # Download fresh copy
    try:
        print("Downloading index file...")
        response = requests.get(INDEX_URL, timeout=10)
        response.raise_for_status()
        
        # Create the cache directory if needed
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to cache
        with open(cache_file, "w") as f:
            json.dump(response.json(), f, indent=2)
            
        print(f"Index file cached at {cache_file}")
        return cache_file
    except RequestException as e:
        print(f"Failed to download index: {e}")
        if cache_file.exists():
            print("Using existing cached index")
            return cache_file
        raise

def load_index(use_cache=True, force_refresh=False, local_fallback=True, local_path=None):
    """
    Load the index.json from cache, remote GitHub repo, or local fallback.
    
    Parameters:
    - use_cache (bool): If True, try to use cached index file first
    - force_refresh (bool): If True, force re-download of index
    - local_fallback (bool): If True, attempt to load from local path when remote fails
    - local_path (str): Optional path to local index.json. If None, will check common locations
    
    Returns:
    - The loaded index as a dictionary
    """
    cache_file = DEFAULT_CACHE_DIR / "index.json"
    
    # Try cache first if requested
    if use_cache and not force_refresh and cache_file.exists():
        try:
            with open(cache_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print("Cached index file is corrupt. Downloading fresh copy.")
    
    # Download or refresh if needed
    if force_refresh or not cache_file.exists():
        try:
            download_index(force=force_refresh)
            with open(cache_file, "r") as f:
                return json.load(f)
        except Exception as e:
            if not local_fallback:
                raise RuntimeError("Failed to download index and local fallback disabled.") from e
    
    # Try remote if not already tried
    if not use_cache:
        try:
            response = requests.get(INDEX_URL, timeout=10)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            if not local_fallback:
                raise RuntimeError("Failed to load index from remote.") from e
    
    # Fall back to local paths if all else fails
    if local_fallback:
        if local_path:
            local_file = Path(local_path)
        else:
            possible_paths = [
                Path(__file__).parent.parent.parent.parent / "datasets" / "index.json", 
                Path.home() / ".easygese" / "index.json",
                cache_file  # Try the cache one more time
            ]
            
            for path in possible_paths:
                if path.exists():
                    local_file = path
                    break
            else:
                raise FileNotFoundError(
                    "Remote load failed and no local index.json found in standard locations."
                )
                
        with local_file.open("r") as f:
            return json.load(f)
               
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
                                         Defaults to ~/.easygese/data/species/
    
    Returns:
    - Path object: Directory containing the downloaded files
    """
    index = load_index()
    if species not in index:
        raise ValueError(f"Species '{species}' not found in index.")
        
    # Set up the output directory
    if output_dir is None:
        output_dir = DEFAULT_CACHE_DIR / species
    else:
        output_dir = Path(output_dir) / species
        
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

def load_species(species, use_local=True, data_dir=None):
    """
    Load the X, Y, and Z datasets for a given species. It outputs three
    different objects, the function should be called as:
    X, Y, Z = load_species('species_name')
    
    Parameters:
    - species (str): Name of the species to load
    - use_local (bool): If True, attempt to load from local files first
    - data_dir (str or Path, optional): Directory to look for data files
                                       Defaults to ~/.easygese/data/species/
    """
    index = load_index()
    if species not in index:
        raise ValueError(f"Species '{species}' not found in index.")

    entry = index[species]
    
    # Check for local files
    if data_dir is None:
        data_dir = DEFAULT_CACHE_DIR / species
    else:
        data_dir = Path(data_dir) / species
    
    local_files_exist = (data_dir.exists() and
                        (data_dir / "X.csv").exists() and
                        (data_dir / "Y.csv").exists() and
                        (data_dir / "Z.json").exists())
    
    if use_local and local_files_exist:
        print(f"Loading {species} from local files at {data_dir}")
        
        # Load X from file
        X = pd.read_csv(data_dir / "X.csv", index_col=0)
        
        # Load Y from file
        Y = pd.read_csv(data_dir / "Y.csv", index_col=0)
        Y.attrs["_is_easygese_Y"] = True
        
        # Load Z from file
        with open(data_dir / "Z.json", "r") as f:
            Z = json.load(f)
        Z["_is_easygese_Z"] = True
    else:
        # Original remote loading code
        print("Please cite:")
        print(entry["citation"])

        response_X = requests.get(entry["X"])
        response_X.raise_for_status()  
        X = pd.read_csv(io.StringIO(response_X.text), index_col=0)  

        response_Y = requests.get(entry["Y"])
        response_Y.raise_for_status()
        Y = pd.read_csv(io.StringIO(response_Y.text), index_col=0)
        Y.attrs["_is_easygese_Y"] = True

        response_Z = requests.get(entry["Z"])
        response_Z.raise_for_status()
        Z = response_Z.json()
        Z["_is_easygese_Z"] = True 

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

def download_benchmark_data(force=False, output_dir=None):
    """
    Download benchmark result files to local cache.
    
    Parameters:
    - force (bool): If True, force re-download even if cache exists
    - output_dir (str or Path, optional): Directory to save files.
                                         Defaults to package cache directory.
    
    Returns:
    - Path object: Directory containing the downloaded files
    """
    # Base GitHub URL (derived from index URL)
    base_url = "/".join(INDEX_URL.split("/")[:-1]) + "/"
    
    # Set up the output directory
    if output_dir is None:
        output_dir = DEFAULT_CACHE_DIR / "benchmarks"
    else:
        output_dir = Path(output_dir)
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Define benchmark files to download
    benchmark_files = {
        "results_raw.csv": base_url + "results_raw.csv",
        "results_summary.csv": base_url + "results_summary.csv"
    }
    
    files_downloaded = []
    
    for filename, url in benchmark_files.items():
        output_file = output_dir / filename
        
        # Skip if cached and not forced
        if output_file.exists() and not force:
            print(f"Using cached {filename}")
            continue
            
        # Download the file
        try:
            print(f"Downloading {filename}...")
            response = requests.get(url)
            response.raise_for_status()
            
            with open(output_file, "wb") as f:
                f.write(response.content)
                
            files_downloaded.append(filename)
        except RequestException as e:
            print(f"Failed to download {filename}: {e}")
            if not output_file.exists():
                print(f"Warning: {filename} not available locally")
    
    if files_downloaded:
        print(f"Downloaded {len(files_downloaded)} benchmark files to {output_dir}")
    
    return output_dir

def load_benchmark_results(
    file_path: str = None,
    species: Optional[Union[str, List[str]]] = None,
    traits: Optional[Union[str, List[str]]] = None,
    models: Optional[Union[str, List[str]]] = None,
    summarize: bool = True,
    validate_combinations: bool = True,
    use_cache: bool = True,
    force_download: bool = False
) -> pd.DataFrame:
    """
    Load benchmark results from a CSV file.
    
    Parameters:
    -----------
    file_path : str, optional
        Path to the CSV file containing the benchmark results.
        If None, uses the default package data files.
    species : str or list of str, optional
        Species to filter by (e.g., "barley", "bean", "lentil").
    traits : str or list of str, optional
        Traits to filter by (e.g., "BaMMV", "DF", "DTF").
    models : str or list of str, optional
        Models to filter by (e.g., "BayesA", "GBLUP", "XGBoost").
    summarize : bool
        Whether to summarize results by averaging over CV splits.
    validate_combinations : bool
        Whether to validate that requested species-trait combinations exist.
    use_cache : bool
        If True, try to use cached benchmark files first.
    force_download : bool
        If True, force re-download of benchmark files.
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame containing the benchmark results, filtered as specified.
    """
        # Determine which file to use based on the summarize parameter
    filename = "results_summary.csv" if summarize else "results_raw.csv"
    
    # If a specific file path was provided, use it directly
    if file_path is not None:
        path_to_use = Path(file_path)
    else:
        # Try to use cached files if requested
        cache_dir = DEFAULT_CACHE_DIR / "benchmarks"
        cache_file = cache_dir / filename
        
        if use_cache:
            # Download if forced or if file doesn't exist
            if force_download or not cache_file.exists():
                download_benchmark_data(force=force_download)
            
            # If cache file exists after potential download, use it
            if cache_file.exists():
                path_to_use = cache_file
                print(f"Using cached benchmark file: {filename}")
            else:
                # Fall back to package data directory
                path_to_use = Path(__file__).parent / "data" / filename
                print(f"Using package benchmark file: {filename}")
        else:
            # Use package data directory if not using cache
            path_to_use = Path(__file__).parent / "data" / filename
            print(f"Using package benchmark file: {filename}")
    
    # Check if the file exists
    if not path_to_use.exists():
        raise FileNotFoundError(f"Benchmark file not found: {path_to_use}")
    
    # Load the CSV file
    df = pd.read_csv(path_to_use)
    
    # Store original data for validation
    original_df = df.copy()
    
    # Convert single values to lists for consistent filtering
    if isinstance(species, str):
        species = [species]
    if isinstance(traits, str):
        traits = [traits]
    if isinstance(models, str):
        models = [models]
    
    # Validate species-trait combinations if requested
    if validate_combinations and species is not None and traits is not None:
        # Get all valid species-trait combinations in the data
        valid_combos = set(zip(original_df['species'], original_df['trait']))
        
        # Check if requested combinations exist
        requested_combos = [(sp, trait) for sp in species for trait in traits]
        valid_requested = [combo in valid_combos for combo in requested_combos]
        
        if not all(valid_requested):
            invalid_combos = [combo for i, combo in enumerate(requested_combos) if not valid_requested[i]]
            print(f"Warning: The following species-trait combinations don't exist in the data:")
            for sp, trait in invalid_combos:
                print(f"  - {sp}: {trait}")
            
            # Show available traits for each requested species
            print("\nAvailable traits per species:")
            for sp in species:
                available_traits = original_df[original_df['species'] == sp]['trait'].unique()
                print(f"  - {sp}: {', '.join(available_traits)}")
    
    # Apply filters if provided
    if species is not None:
        df = df[df['species'].isin(species)]
    if traits is not None:
        df = df[df['trait'].isin(traits)]
    if models is not None:
        df = df[df['model'].isin(models)]
    
    # If we're not using the pre-summarized file, summarize now if requested
    if summarize and 'CV_split' in df.columns:
        # Group by species, trait, model and compute mean and std for correlation and RMSE
        df = df.groupby(['species', 'trait', 'model']).agg({
            'correlation': ['mean', 'std'],
            'RMSE': ['mean', 'std']
        }).reset_index()
        
        # Flatten multi-level column names
        df.columns = ['species', 'trait', 'model', 
                     'correlation_mean', 'correlation_std', 
                     'RMSE_mean', 'RMSE_std']
    
    return df