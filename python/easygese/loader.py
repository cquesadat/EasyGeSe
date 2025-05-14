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
    Files are saved with species prefix (e.g., beanX.csv).
    
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
        output_dir = CACHE_DIR
    else:
        output_dir = Path(output_dir)
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    entry = index[species]
    
    # Define filenames with species prefix
    x_filename = f"{species}X.csv"
    y_filename = f"{species}Y.csv"
    z_filename = f"{species}Z.json"
    
    # Check if files already exist
    x_exists = (output_dir / x_filename).exists()
    y_exists = (output_dir / y_filename).exists()
    z_exists = (output_dir / z_filename).exists()
    
    if x_exists and y_exists and z_exists:
        print(f"All files for {species} already exist in {output_dir}")
        return output_dir
    
    print(f"Downloading {species} data files...")
    
    # Download only missing files
    if not x_exists:
        print(f"Downloading {x_filename}...")
        response = requests.get(entry["X"])
        response.raise_for_status()
        with open(output_dir / x_filename, "wb") as f:
            f.write(response.content)
    
    if not y_exists:
        print(f"Downloading {y_filename}...")
        response = requests.get(entry["Y"])
        response.raise_for_status()
        with open(output_dir / y_filename, "wb") as f:
            f.write(response.content)
    
    if not z_exists:
        print(f"Downloading {z_filename}...")
        response = requests.get(entry["Z"])
        response.raise_for_status()
        with open(output_dir / z_filename, "wb") as f:
            f.write(response.content)
    
    print(f"Downloaded {species} data to {output_dir}")
    return output_dir

def load_species(species, download=False, download_dir=None):
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
    index = load_index()
    if species not in index:
        raise ValueError(f"Species '{species}' not found in the index")

    # Define filenames with species prefix
    x_filename = f"{species}X.csv"
    y_filename = f"{species}Y.csv"
    z_filename = f"{species}Z.json"
    
    # Determine directory to use
    data_dir = Path(download_dir) if download_dir else CACHE_DIR
    
    # Check if files exist in the specified directory
    files_exist = (data_dir.exists() and
                  (data_dir / x_filename).exists() and
                  (data_dir / y_filename).exists() and
                  (data_dir / z_filename).exists())
    
    # If files exist locally, load them directly
    if files_exist:
        print(f"Loading data from {data_dir}...")
        X = pd.read_csv(data_dir / x_filename, index_col=0)
        X.attrs["_is_easygese_X"] = True
        
        Y = pd.read_csv(data_dir / y_filename, index_col=0)
        Y.attrs["_is_easygese_Y"] = True
        
        with open(data_dir / z_filename, "r") as f:
            Z = json.load(f)
        Z["_is_easygese_Z"] = True
    
    # If files don't exist and download is requested, download them
    elif download:
        print(f"Files not found in {data_dir}. Downloading...")
        download_data(species, output_dir=data_dir)
        
        # Now load from the downloaded files
        X = pd.read_csv(data_dir / x_filename, index_col=0)
        X.attrs["_is_easygese_X"] = True
        
        Y = pd.read_csv(data_dir / y_filename, index_col=0)
        Y.attrs["_is_easygese_Y"] = True
        
        with open(data_dir / z_filename, "r") as f:
            Z = json.load(f)
        Z["_is_easygese_Z"] = True
    
    # If files don't exist and download not requested, try online loading
    else:
        try:
            # Get the URLs from the index
            entry = index[species]
            
            print("Loading data from online sources...")
            # Load X (genotype) data directly from URL
            X = pd.read_csv(entry["X"], index_col=0)
            X.attrs["_is_easygese_X"] = True
            
            # Load Y (phenotype) data directly from URL
            Y = pd.read_csv(entry["Y"], index_col=0)
            Y.attrs["_is_easygese_Y"] = True
            
            # Load Z (CV splits) data directly from URL
            response = requests.get(entry["Z"])
            response.raise_for_status()
            Z = json.loads(response.text)
            Z["_is_easygese_Z"] = True
            
        except Exception as e:
            print(f"Failed to load data from online source: {e}")
            print(f"No local data found at {data_dir} and online loading failed.")
            raise
    
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
    # Validate that this is a proper EasyGeSe Z object
    if not isinstance(z, dict) or z.get("_is_easygese_Z") is not True:
        raise TypeError("The provided object is not a valid EasyGeSe Z object")
        
    # Check if the trait exists
    if trait not in z or trait.startswith("_"):
        available_traits = [k for k in z.keys() if not k.startswith("_")]
        raise ValueError(f"Trait '{trait}' not found. Available traits: {', '.join(available_traits)}")
    
    # Get the trait data and convert to DataFrame
    trait_data = z[trait] 
    df = pd.DataFrame.from_dict(trait_data, orient='index')
    df.index.name = "Genotype"
    return df

def download_benchmark_data(output_dir=None, force=False):
    """
    Download benchmark result files to local storage.
    
    Parameters:
    - output_dir (str or Path, optional): Directory to save files.
                                         Defaults to user cache directory
    - force (bool): If True, force re-download even if cache exists
    
    Returns:
    - Path object: Directory containing the downloaded files
    """
    # Base GitHub URL (derived from index URL)
    base_url = "/".join(INDEX_URL.split("/")[:-1]) + "/"
    
    # Set up the output directory
    if output_dir is None:
        output_dir = CACHE_DIR
    else:
        output_dir = Path(output_dir)
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Define benchmark files to download
    benchmark_files = {
        "results_raw.csv": base_url + "results_raw.csv",
        "results_summary.csv": base_url + "results_summary.csv"
    }
    
    # Check if files already exist
    all_exist = True
    for filename in benchmark_files:
        if not (output_dir / filename).exists():
            all_exist = False
            break
    
    if all_exist and not force:
        print(f"All benchmark files already exist in {output_dir}")
        return output_dir
    
    # Download files (only missing ones if not forcing)
    for filename, url in benchmark_files.items():
        output_file = output_dir / filename
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
    
    return output_dir

def load_benchmark_results(
    species=None,
    traits=None,
    models=None,
    summarize=True,
    download=False,
    download_dir=None
):
    """
    Load benchmark results, checking local files first before online sources.
    
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
    download : bool
        If True, explicitly download data to local storage.
    download_dir : str or Path, optional
        Directory to save files if downloading. Defaults to cache directory.
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame containing the benchmark results, filtered as specified.
    """
    # Determine which file to use
    filename = "results_summary.csv" if summarize else "results_raw.csv"
    
    # Base GitHub URL (derived from index URL)
    base_url = "/".join(INDEX_URL.split("/")[:-1]) + "/"
    file_url = base_url + filename
    
    # Determine directory to use
    data_dir = Path(download_dir) if download_dir else CACHE_DIR
    
    # Check if file exists locally
    file_path = data_dir / filename
    file_exists = file_path.exists()
    
    # If file exists locally, load it directly
    if file_exists:
        print(f"Loading {filename} from {data_dir}...")
        df = pd.read_csv(file_path)
    
    # If file doesn't exist and download is requested, download it
    elif download:
        print(f"File not found in {data_dir}. Downloading...")
        download_benchmark_data(output_dir=data_dir)
        
        # Now load the downloaded file
        df = pd.read_csv(data_dir / filename)
    
    # If file doesn't exist and download not requested, try online loading
    else:
        try:
            print(f"Loading {filename} from online source...")
            df = pd.read_csv(file_url)
        except Exception as e:
            print(f"Failed to load from online source: {e}")
            print(f"No local file found at {file_path} and online loading failed.")
            raise
    
    # Convert single values to lists for consistent filtering
    if isinstance(species, str):
        species = [species]
    if isinstance(traits, str):
        traits = [traits]
    if isinstance(models, str):
        models = [models]
    
    # Apply filters if provided - use case-insensitive column names
    columns_lower = {col.lower(): col for col in df.columns}
    
    if species is not None and "species" in columns_lower:
        df = df[df[columns_lower["species"]].isin(species)]
    if traits is not None and "trait" in columns_lower:
        df = df[df[columns_lower["trait"]].isin(traits)]
    if models is not None and "model" in columns_lower:
        df = df[df[columns_lower["model"]].isin(models)]
    
    return df