import json
import pandas as pd
import requests

# Default location of the index file
INDEX_URL = "https://raw.githubusercontent.com/cquesadat/EasyGeSe/main/easygese/index.json"

def load_index(local_fallback=True):
    try:
        response = requests.get(INDEX_URL)
        response.raise_for_status()
        return response.json()
    except Exception:
        if local_fallback:
            with open("easygese/index.json") as f:
                return json.load(f)
        else:
            raise RuntimeError("Failed to load index.json from remote.")

def load_species(species):
    index = load_index()
    if species not in index:
        raise ValueError(f"Species '{species}' not found in index.")
    
    entry = index[species]
    print("Please cite:")
    print(entry["citation"])

    X = pd.read_csv(entry["X"])
    Y = pd.read_csv(entry["Y"])
    Z = requests.get(entry["Z"]).json()
    return {"X": X, "Y": Y, "Z": Z}