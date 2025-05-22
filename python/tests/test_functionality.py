# filepath: t:\myGit\EasyGeSe\python\tests\test_functionality.py
import unittest
from unittest.mock import patch, MagicMock 
import shutil 
from pathlib import Path
import pandas as pd 

from easygese import (
    load_species,
    load_index,
    load_species_aliases,
    _resolve_species_name,
    CACHE_DIR, 
    INDEX_URL, 
    SPECIES_ALIASES_URL
)

# Mock data for aliases and index
# Ensure these reflect the structure your functions expect
MOCK_SPECIES_ALIASES_DATA = {
    "lentil": "lentil", "lentils": "lentil", "lens culinaris": "lentil",
    "bean": "bean", "beans": "bean", "common bean": "bean",
    "wheatg": "wheatG", "wheat": "wheatG", "bread wheat": "wheatG", # Assuming 'wheatg' is a valid alias
    "maize": "maize", "corn": "maize",
    # Add other canonical names that should resolve to themselves if not covered by an explicit alias
    "barley": "barley", 
    "oyster": "oyster",
    "pig": "pig",
    "pine": "pine",
    "rice": "rice",
    "soybean": "soybean"
}

MOCK_INDEX_DATA = {
    "lentil": {"X": "url_lentil_x.csv", "Y": "url_lentil_y.csv", "Z": "url_lentil_z.json", "metadata": {"n_traits": 2}},
    "bean": {"X": "url_bean_x.csv", "Y": "url_bean_y.csv", "Z": "url_bean_z.json", "metadata": {"n_traits": 1}},
    "wheatG": {"X": "url_wheatg_x.csv", "Y": "url_wheatg_y.csv", "Z": "url_wheatg_z.json", "metadata": {"n_traits": 3}},
    "maize": {"X": "url_maize_x.csv", "Y": "url_maize_y.csv", "Z": "url_maize_z.json", "metadata": {"n_traits": 1}},
    "barley": {"X": "url_barley_x.csv", "Y": "url_barley_y.csv", "Z": "url_barley_z.json", "metadata": {}},
    "oyster": {"X": "url_oyster_x.csv", "Y": "url_oyster_y.csv", "Z": "url_oyster_z.json", "metadata": {}},
    "pig": {"X": "url_pig_x.csv", "Y": "url_pig_y.csv", "Z": "url_pig_z.json", "metadata": {}},
    "pine": {"X": "url_pine_x.csv", "Y": "url_pine_y.csv", "Z": "url_pine_z.json", "metadata": {}},
    "rice": {"X": "url_rice_x.csv", "Y": "url_rice_y.csv", "Z": "url_rice_z.json", "metadata": {}},
    "soybean": {"X": "url_soybean_x.csv", "Y": "url_soybean_y.csv", "Z": "url_soybean_z.json", "metadata": {}}
}

class TestEasyGeSeSimplified(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Clean cache directory once, in case any function attempts to interact with it.
        if CACHE_DIR.exists():
            shutil.rmtree(CACHE_DIR)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        # Optional: clean up cache after all tests.
        if CACHE_DIR.exists():
            shutil.rmtree(CACHE_DIR)

    # The target for patch should be where 'requests.get' is looked up by your loader functions.
    # This assumes 'requests.get' is used within 'easygese.loader'.
    @patch('easygese.loader.requests.get')
    def test_load_index_and_aliases_mocked(self, mock_requests_get):
        """Test loading index and aliases using mocked network calls."""
        
        def side_effect_requests_get(url, timeout=None):
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock() 
            
            if url == INDEX_URL:
                mock_response.json.return_value = MOCK_INDEX_DATA
                mock_response.status_code = 200
            elif url == SPECIES_ALIASES_URL:
                mock_response.json.return_value = MOCK_SPECIES_ALIASES_DATA
                mock_response.status_code = 200
            else:
                mock_response.status_code = 404
                # Simulate requests.Response.raise_for_status() behavior for bad status
                mock_response.raise_for_status.side_effect = Exception(f"Mocked HTTPError 404 for {url}")
            return mock_response

        mock_requests_get.side_effect = side_effect_requests_get

        index = load_index(force_refresh=True) 
        self.assertIsInstance(index, dict)
        self.assertEqual(index, MOCK_INDEX_DATA)
        self.assertIn("lentil", index)

        aliases = load_species_aliases(force_refresh=True)
        self.assertIsInstance(aliases, dict)
        self.assertEqual(aliases, MOCK_SPECIES_ALIASES_DATA)
        self.assertIn("lentils", aliases) 
        self.assertEqual(aliases["lentils"], "lentil")

    def test_resolve_species_name_logic(self):
        """Test _resolve_species_name directly with mock data."""
        canonical_names = list(MOCK_INDEX_DATA.keys())
        
        # Exact matches (case-insensitive for input species)
        self.assertEqual(_resolve_species_name("lentil", canonical_names, MOCK_SPECIES_ALIASES_DATA), "lentil")
        self.assertEqual(_resolve_species_name("Lentil", canonical_names, MOCK_SPECIES_ALIASES_DATA), "lentil")
        self.assertEqual(_resolve_species_name("WHEATG", canonical_names, MOCK_SPECIES_ALIASES_DATA), "wheatG")

        # Alias matches (input species case-insensitive, aliases in map are lowercase)
        self.assertEqual(_resolve_species_name("lentils", canonical_names, MOCK_SPECIES_ALIASES_DATA), "lentil")
        self.assertEqual(_resolve_species_name("LENS CULINARIS", canonical_names, MOCK_SPECIES_ALIASES_DATA), "lentil")
        self.assertEqual(_resolve_species_name("wheat", canonical_names, MOCK_SPECIES_ALIASES_DATA), "wheatG")
        self.assertEqual(_resolve_species_name("Corn", canonical_names, MOCK_SPECIES_ALIASES_DATA), "maize")
        
        # Non-existent species
        with self.assertRaisesRegex(ValueError, "Invalid species name: 'potato'. Available options are:"):
            _resolve_species_name("potato", canonical_names, MOCK_SPECIES_ALIASES_DATA)
        
        with self.assertRaisesRegex(ValueError, "Invalid species name: 'unknownplant'. Available options are:"):
            _resolve_species_name("unknownplant", canonical_names, MOCK_SPECIES_ALIASES_DATA)

    @patch('easygese.loader.pd.read_csv') # Mock reading of X, Y files
    @patch('easygese.loader.json.load')   # Mock reading of Z files (if json.load is used with a file object)
    @patch('easygese.loader.requests.get') # Mock network calls for index, aliases, and X,Y,Z files
    def test_load_species_uses_resolution(self, mock_requests_get, mock_json_load, mock_pd_read_csv):
        """Test load_species uses resolution for errors and can proceed with mocks."""
        
        # Configure mock for requests.get (covers index, aliases, and X,Y,Z file "downloads")
        def side_effect_requests_get(url, timeout=None, stream=False): # Add stream for Z file download
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            if url == INDEX_URL:
                mock_response.json.return_value = MOCK_INDEX_DATA
                mock_response.status_code = 200
            elif url == SPECIES_ALIASES_URL:
                mock_response.json.return_value = MOCK_SPECIES_ALIASES_DATA
                mock_response.status_code = 200
            # Simulate returning content for X, Y, Z file URLs from MOCK_INDEX_DATA
            elif url in [MOCK_INDEX_DATA["lentil"]["X"], MOCK_INDEX_DATA["lentil"]["Y"], MOCK_INDEX_DATA["lentil"]["Z"]]:
                mock_response.status_code = 200
                if url.endswith(".csv"):
                    mock_response.content = b"id,col1\ngen1,1" # Dummy CSV content
                elif url.endswith(".json"):
                    # For json.load to work with a file-like object from response.raw
                    mock_response.raw = MagicMock() 
                    mock_response.raw.read.return_value = b'{"dummy_z_key": "dummy_z_value"}'
                    # If json.loads(response.text) is used:
                    # mock_response.text = '{"dummy_z_key": "dummy_z_value"}'
            else:
                mock_response.status_code = 404
                mock_response.raise_for_status.side_effect = Exception(f"Mocked HTTPError 404 for {url}")
            return mock_response
        mock_requests_get.side_effect = side_effect_requests_get
        
        # Configure mock for pd.read_csv
        mock_pd_read_csv.return_value = pd.DataFrame({'id': ["gen1"], 'col1': [1]})
        
        # Configure mock for json.load (if Z files are loaded this way)
        mock_json_load.return_value = {"dummy_z_key": "dummy_z_value"}

        # Test with an invalid species name
        with self.assertRaisesRegex(ValueError, "Invalid species name: 'potato'. Available options are:"):
            load_species("potato", download=False) # download=False still loads index/aliases

        # Test with a valid alias. This will try to "load" data.
        try:
            # "Lentils" -> "lentil". load_species will use MOCK_INDEX_DATA["lentil"] URLs.
            # requests.get will be mocked for these URLs.
            # pd.read_csv and json.load will be mocked for file reading.
            X, Y, Z = load_species("Lentils", download=False) 
            self.assertIsInstance(X, pd.DataFrame)
            self.assertIsInstance(Y, pd.DataFrame)
            self.assertIsInstance(Z, dict) 
        except ValueError as e:
            self.fail(f"load_species failed for a valid alias 'Lentils' with mocks: {e}")
        except Exception as e:
            self.fail(f"load_species for 'Lentils' raised an unexpected error with mocks: {e}")

if __name__ == '__main__':
    unittest.main()