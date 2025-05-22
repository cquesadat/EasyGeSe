from pathlib import Path
import requests
import pandas as pd
import json
from typing import List, Optional, Union, Dict, Any
from appdirs import user_cache_dir

# Remote location of index file
INDEX_URL = "https://raw.githubusercontent.com/cquesadat/EasyGeSe/main/datasets/index.json"
SPECIES_ALIASES_URL = "https://raw.githubusercontent.com/cquesadat/EasyGeSe/main/datasets/species_aliases.json"

# Use a single, consistent cache directory
CACHE_DIR = Path(user_cache_dir("easygese", "easygese"))
# Create cache directory if it doesn't exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# --- Generic Cache and Load Utilities ---
def _download_cached_file(file_url: str, local_filename: str, force: bool = False) -> Path:
    """
    Download a file and cache it locally.
    Returns the path to the cached file.
    """
    cache_file_path = CACHE_DIR / local_filename
    
    if cache_file_path.exists() and not force:
        return cache_file_path
        
    try:
        print(f"Downloading {local_filename} from {file_url}...")
        response = requests.get(file_url, timeout=10)
        response.raise_for_status()
        
        with open(cache_file_path, "wb") as f: # Use "wb" for binary content
            f.write(response.content)
            
        print(f"{local_filename} cached at {cache_file_path}")
        return cache_file_path
    except Exception as e:
        print(f"Error downloading {local_filename} from {file_url}: {e}")
        if cache_file_path.exists():
            print(f"Using existing cached {local_filename}.")
            return cache_file_path
        raise # Re-raise if download fails and no cache available

def _load_cached_json(file_url: str, local_filename: str, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Load a JSON file from cache (downloading if necessary).
    """
    cached_file_path = _download_cached_file(file_url, local_filename, force=force_refresh)
    try:
        with open(cached_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON from {cached_file_path}: {e}")
        raise

# --- Specific Loaders for Index and Aliases ---
def download_index(force: bool = False) -> Path:
    """
    Download and cache the index.json file.
    """
    return _download_cached_file(INDEX_URL, "index.json", force=force)

def load_index(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Load the index.json from cache or remote.
    """
    return _load_cached_json(INDEX_URL, "index.json", force_refresh=force_refresh)

def load_species_aliases(force_refresh: bool = False) -> Dict[str, str]:
    """
    Load the species_aliases.json from cache or remote.
    """
    return _load_cached_json(SPECIES_ALIASES_URL, "species_aliases.json", force_refresh=force_refresh)

# --- Species Name Resolution ---
def _resolve_species_name(
    species_input: str,
    canonical_species_names: List[str],
    species_alias_map: Optional[Dict[str, str]] = None
) -> str:
    """Internal helper to resolve species name using aliases."""
    if not isinstance(species_input, str):
        raise TypeError("species_input must be a string.")
        
    if species_alias_map is None:
        species_alias_map = load_species_aliases()
        
    user_input_lower = species_input.lower()
    
    if user_input_lower in species_alias_map:
        canonical_name = species_alias_map[user_input_lower]
        if canonical_name in canonical_species_names:
            return canonical_name
        else:
            # This case indicates an inconsistency between alias file and main index
            print(f"Warning: Alias '{species_input}' mapped to '{canonical_name}', "
                  "which is not a recognized canonical species. "
                  "Check species_aliases.json and index.json consistency.")
            # Fall through to the general error if the mapped name is not valid

    available_options = ", ".join(sorted([f"'{opt}'" for opt in canonical_species_names]))
    raise ValueError(
        f"Invalid species name: '{species_input}'. Available options are: {available_options}."
    )

# --- Existing Functions (Refactored) ---
def list_species(verbose: bool = True, detailed: bool = True) -> List[str]:
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
            
            rows = []
            for sp_name in species_list: # Changed 'species' to 'sp_name' to avoid conflict
                entry = index[sp_name]
                metadata = entry.get("metadata", {})
                n_markers = metadata.get("n_markers", "?")
                n_genotypes = metadata.get("n_genotypes", "?")
                n_traits = metadata.get("n_traits", "?")
                rows.append([sp_name, n_markers, n_genotypes, n_traits])
            
            headers = ["Species", "Markers", "Genotypes", "Traits"]
            table = tabulate(rows, headers=headers, tablefmt="pretty", colalign=("left", "right", "right", "right"))
            print(table)
        except ImportError:
            print("Install 'tabulate' package for detailed view: pip install tabulate")
            detailed = False # type: ignore
            
    if not detailed:
        for sp in species_list:
            print(f" - {sp}")
            
    print("\nUsage examples:")
    print("  from easygese import load_species")
    if species_list:
        example_species_name = species_list[0] if len(species_list) > 0 else "your_species" # More robust example
        print(f"  X, Y, Z = load_species('{example_species_name}')  # Load dataset")
        print(f"  download_data('{example_species_name}')           # Download for offline use")
    return species_list


def download_data(species: str, output_dir: Optional[Union[str, Path]] = None) -> Path:
    """
    Download raw data files for a species to a local directory.
    Files are saved with species prefix (e.g., beanX.csv).
    
    Parameters:
    - species (str): Species name to download
    - output_dir (str or Path, optional): Directory to save files.
                                         Defaults to user cache directory
    
    Returns:
    - Path object: Directory containing the downloaded files
    """
    index_data = load_index()
    canonical_species_names = list(index_data.keys())
    # species_alias_map will be loaded by _resolve_species_name if None
    resolved_species_name = _resolve_species_name(species, canonical_species_names, None)
        
    # Set up the output directory (keeps existing custom output_dir logic)
    if output_dir is None:
        current_output_dir = CACHE_DIR
    else:
        current_output_dir = Path(output_dir)
        
    current_output_dir.mkdir(parents=True, exist_ok=True)
    
    entry = index_data[resolved_species_name]
    
    # Define filenames with resolved species prefix
    x_filename = f"{resolved_species_name}X.csv"
    y_filename = f"{resolved_species_name}Y.csv"
    z_filename = f"{resolved_species_name}Z.json"
    
    files_to_download = {
        x_filename: entry["X"],
        y_filename: entry["Y"],
        z_filename: entry["Z"]
    }
    
    all_exist = True
    for filename_key in files_to_download:
        if not (current_output_dir / filename_key).exists():
            all_exist = False
            break
            
    if all_exist: # No force parameter here, if files exist, we assume they are fine
        print(f"All files for {resolved_species_name} already exist in {current_output_dir}")
        return current_output_dir

    print(f"Downloading {resolved_species_name} data files to {current_output_dir}...")
    
    for filename, url in files_to_download.items():
        file_path = current_output_dir / filename
        if not file_path.exists(): # Download only if missing
            print(f"Downloading {filename}...")
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                with open(file_path, "wb") as f:
                    f.write(response.content)
            except Exception as e:
                print(f"Error downloading {filename} from {url}: {e}")
                # Decide if to raise or continue
    
    print(f"Downloaded {resolved_species_name} data to {current_output_dir}")
    return current_output_dir

def load_species(species: str, download: bool = False, download_dir: Optional[Union[str, Path]] = None):
    """
    Load the X, Y, and Z datasets for a given species. It outputs three
    different objects, the function should be called as:
    X, Y, Z = load_species('species_name')
    
    Parameters:
    - species (str): Name of the species to load
    - download (bool): If True, download data to local storage
    - download_dir (str or Path, optional): Directory to save files if downloading.
                                           Defaults to user cache directory
    """
    index_data = load_index()
    canonical_species_names = list(index_data.keys())
    # species_alias_map will be loaded by _resolve_species_name if None
    resolved_species_name = _resolve_species_name(species, canonical_species_names, None)

    # Define filenames with resolved species prefix
    x_filename = f"{resolved_species_name}X.csv"
    y_filename = f"{resolved_species_name}Y.csv"
    z_filename = f"{resolved_species_name}Z.json"
    
    # Determine directory to use (keeps existing custom download_dir logic)
    data_dir_path = Path(download_dir) if download_dir else CACHE_DIR
    
    files_exist = (data_dir_path.exists() and
                  (data_dir_path / x_filename).exists() and
                  (data_dir_path / y_filename).exists() and
                  (data_dir_path / z_filename).exists())
    
    X, Y, Z = None, None, None

    if files_exist:
        print(f"Loading data for {resolved_species_name} from {data_dir_path}...")
        X = pd.read_csv(data_dir_path / x_filename, index_col=0)
        X.attrs["_is_easygese_X"] = True
        Y = pd.read_csv(data_dir_path / y_filename, index_col=0)
        Y.attrs["_is_easygese_Y"] = True
        with open(data_dir_path / z_filename, "r", encoding="utf-8") as f:
            Z = json.load(f)
        Z["_is_easygese_Z"] = True # type: ignore
    
    elif download:
        print(f"Files for {resolved_species_name} not found in {data_dir_path}. Downloading...")
        # download_data will use data_dir_path if provided, or CACHE_DIR if download_dir was None
        download_data(resolved_species_name, output_dir=data_dir_path)
        
        X = pd.read_csv(data_dir_path / x_filename, index_col=0)
        X.attrs["_is_easygese_X"] = True
        Y = pd.read_csv(data_dir_path / y_filename, index_col=0)
        Y.attrs["_is_easygese_Y"] = True
        with open(data_dir_path / z_filename, "r", encoding="utf-8") as f:
            Z = json.load(f)
        Z["_is_easygese_Z"] = True # type: ignore
    
    else: # Try online loading
        try:
            entry = index_data[resolved_species_name]
            print(f"Loading data for {resolved_species_name} from online sources...")
            X = pd.read_csv(entry["X"], index_col=0)
            X.attrs["_is_easygese_X"] = True
            Y = pd.read_csv(entry["Y"], index_col=0)
            Y.attrs["_is_easygese_Y"] = True
            response_z = requests.get(entry["Z"], timeout=10)
            response_z.raise_for_status()
            Z = json.loads(response_z.text)
            Z["_is_easygese_Z"] = True # type: ignore
        except Exception as e:
            print(f"Failed to load data for {resolved_species_name} from online source: {e}")
            print(f"No local data found at {data_dir_path} and online loading failed.")
            raise
    
    if "citation" in index_data[resolved_species_name]:
        print(f"\nCitation for {resolved_species_name} dataset:")
        print(index_data[resolved_species_name]["citation"])
    
    return X, Y, Z

def list_traits(obj: Union[pd.DataFrame, Dict[str, Any]]) -> List[str]:
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

def get_cv_indices(z: Dict[str, Any], trait: str) -> pd.DataFrame:
    """
    Return a pandas DataFrame with cross-validation splits for a specific trait.
    """
    if not isinstance(z, dict) or z.get("_is_easygese_Z") is not True:
        raise TypeError("The provided object is not a valid EasyGeSe Z object")
        
    if trait not in z or trait.startswith("_"):
        available_traits = [k for k in z.keys() if not k.startswith("_")]
        raise ValueError(f"Trait '{trait}' not found. Available traits: {', '.join(available_traits)}")
    
    trait_data = z[trait] 
    df = pd.DataFrame.from_dict(trait_data, orient='index') # type: ignore
    df.index.name = "Genotype"
    return df


def download_benchmark_data(force: bool = False) -> Path:
    """
    Download benchmark result files (results_raw.csv and results_summary.csv)
    to the central cache directory.
    """
    base_url = "/".join(INDEX_URL.split("/")[:-1]) + "/" # Derive base URL
    
    benchmark_files_info = {
        "results_raw.csv": base_url + "results_raw.csv",
        "results_summary.csv": base_url + "results_summary.csv"
    }
    
    for filename, url in benchmark_files_info.items():
        print(f"Ensuring benchmark file {filename} is cached...")
        _download_cached_file(url, filename, force=force)
    
    print(f"Benchmark files are available in the cache directory: {CACHE_DIR}")
    return CACHE_DIR

def load_benchmark_results(
    species: Optional[Union[str, List[str]]] = None,
    traits: Optional[Union[str, List[str]]] = None,
    models: Optional[Union[str, List[str]]] = None,
    summarize: bool = True,
    download: bool = False # This now acts as 'force_refresh' for the specific file
):
    """
    Load benchmark results from local cache, downloading if necessary.
    The 'download_dir' parameter is removed; files are always handled in the central cache.
    """
    filename = "results_summary.csv" if summarize else "results_raw.csv"
    base_url = "/".join(INDEX_URL.split("/")[:-1]) + "/"
    file_url = base_url + filename
    
    # Ensure the file is in the cache and get its path
    # 'download' parameter maps to 'force' in _download_cached_file
    cached_file_path = _download_cached_file(file_url, filename, force=download)
    
    print(f"Loading {filename} from cache: {cached_file_path}...")
    df = pd.read_csv(cached_file_path)
    
    # Resolve species names if provided for filtering
    resolved_species_filter: Optional[List[str]] = None
    if species is not None:
        index_data = load_index()
        canonical_species_names = list(index_data.keys())
        # species_alias_map will be loaded by _resolve_species_name if None

        if isinstance(species, str):
            resolved_species_filter = [_resolve_species_name(species, canonical_species_names, None)]
        elif isinstance(species, list):
            resolved_species_filter = [
                _resolve_species_name(s, canonical_species_names, None) for s in species
            ]
        else:
            raise TypeError("'species' must be a string or a list of strings.")

    # Convert single string traits/models to lists for consistent filtering
    if isinstance(traits, str):
        traits = [traits]
    if isinstance(models, str):
        models = [models]
    
    # Apply filters - use case-insensitive column names from CSV
    columns_lower = {col.lower(): col for col in df.columns}
    
    if resolved_species_filter is not None and "species" in columns_lower:
        df = df[df[columns_lower["species"]].isin(resolved_species_filter)]
    if traits is not None and "trait" in columns_lower:
        df = df[df[columns_lower["trait"]].isin(traits)] # Trait names are case-sensitive
    if models is not None and "model" in columns_lower:
        df = df[df[columns_lower["model"]].isin(models)] # Model names likely case-sensitive
    
    if df.empty:
        print("Warning: Filtering resulted in an empty DataFrame. Check your filter criteria.")
        
    return df

# Ensure __init__.py reflects any changes to exported functions if necessary.
# For example, load_species_aliases is internal and should not be in __init__.py.
# download_index and load_index are kept as they are part of the public API.