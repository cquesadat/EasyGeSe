import json
import pandas as pd
import requests
from pathlib import Path
import io
from requests.exceptions import RequestException

# Remote location of index file
INDEX_URL = "https://raw.githubusercontent.com/cquesadat/EasyGeSe/main/datasets/index.json"

def load_index(local_fallback=True, local_path=None):
    """
    Load the index.json from the remote GitHub repo or from the local fallback.
    
    Parameters:
    - local_fallback (bool): If True, attempt to load from local path when remote fails
    - local_path (str): Optional path to local index.json. If None, will check common locations
    """
    try:
        response = requests.get(INDEX_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        if local_fallback:
            if local_path:
                local_file = Path(local_path)
            else:
                possible_paths = [
                    Path(__file__).parent.parent.parent.parent / "datasets" / "index.json", 
                    Path.home() / ".easygese" / "index.json",  
                ]
                
                for path in possible_paths:
                    if path.exists():
                        local_file = path
                        break
                else:
                    raise FileNotFoundError(
                        "Remote load failed and no local index.json found in standard locations."
                    ) from e
                    
            with local_file.open("r") as f:
                return json.load(f)
        else:
            raise RuntimeError("Failed to load index.json from remote.") from e
               
def list_species(verbose=True):
    """
    List available species datasets.

    Parameters:
    - verbose (bool): If True, prints a nicely formatted list. 
                      If False, returns just the list of species names.

    Returns:
    - list of species names (sorted, case-preserved)
    """
    index = load_index()
    species_list = sorted(index.keys())

    if verbose:
        print("Available datasets in EasyGeSe:\n")
        for sp in species_list:
            print(f" - {sp}")
        print(f"\nUse `load_species('<name>')` to load one.\n")
    else:
        return species_list

def load_species(species):
    """
    Load the X, Y, and Z datasets for a given species. It outputs three
    different objects, the function should be called as:
    X, Y, Z = load_species('species_name')
    """
    index = load_index()
    if species not in index:
        raise ValueError(f"Species '{species}' not found in index.")

    entry = index[species]
    print("Please cite:")
    print(entry["citation"])

    response_X = requests.get(entry["X"])
    response_X.raise_for_status()  
    X = pd.read_csv(io.StringIO(response_X.text), index_col = 0)  

    response_Y = requests.get(entry["Y"])
    response_Y.raise_for_status()
    Y = pd.read_csv(io.StringIO(response_Y.text), index_col = 0)
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