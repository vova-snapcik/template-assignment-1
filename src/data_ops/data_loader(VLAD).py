# -----------------------------
# Load Data
# -----------------------------
import json
import csv
import pandas as pd
from pathlib import Path

from pathlib import Path
from dataclasses import dataclass
from logging import Logger
import pandas as pd
import xarray as xr
import numpy as np
import yaml


class DataLoader:
    """
    Loads energy system input data for a given configuration/question from structured CSV and json files
    and an auxiliary configuration metadata file.
    
    Example usage:
    open interactive window in VSCode,
    >>> cd ../../
    run the script data_loader.py in the interactive window,
    >>> data = DataLoader(input_path='..')
    """
    #question: str
    #input_path: Path

    def __init__(self, input_path: str, question: str):
        """
        Post-initialization to load and validate all required datasets (placeholder function)

        example usage:
        self.input_path = Path(self.input_path).resolve()
        
        # Load metadata (auxiliary scenario data)
        self.load_aux_data('question1a_scenario1_aux_data.yaml')
        
        # Load CSV and json datasets
        self.data()
        """
        self.input_path = Path(input_path).resolve()
        self.question = question
        self.data_path = self.input_path / "data" / self.question

        # Attributes to hold loaded data
        self.consumers = pd.DataFrame()
        self.appliances = pd.DataFrame()
        self.usage_preferences = pd.DataFrame()
        self.der_production = pd.DataFrame()
        self.bus_data = pd.DataFrame()

        self.load_dataset()

    def load_dataset(self, question_name: str):
        """Helper function to load all CSV or json files, using the appropriate method based on file extension.
        
        example usage: 
        call the load_dataset() function from utils.py to load all files in the input_path directory
        save all data as class attributes (e.g. self.demand, self.wind, etc.), structured as pandas DataFrames or Series (or other format as prefered)
        """
        print(f"Loading dataset for question: {self.question}")

        # Load files and convert to pd.DataFrame
        try:
            self.consumers = pd.DataFrame(self._load_data_file(question_name, 'consumers.json'))

            appliances_raw = self._load_data_file(question_name, "appliances_params.json")
            appliances_list = []
            for category, items in appliances_raw.items():
                if items:
                    for item in items:
                        item['category'] = category
                        appliances_list.append(item)
            self.appliances = pd.DataFrame(appliances_list)

            usage_prefs_raw = self._load_data_file(question_name, "usage_preferences.json")
            normalized_load_prefs = pd.json_normalize(
                usage_prefs_raw,
                record_path=['load_preferences'],
                meta=['consumer_id'],
                record_prefix='load_pref_'
            )
            self.usage_preferences = normalized_load_prefs

            self.der_production = pd.DataFrame(self._load_data_file(question_name, 'der_production.json'))
            self.bus_data = pd.DataFrame(self._load_data_file(question_name, 'bus_data.json'))
            print("All data files loaded successfully.")
        except FileNotFoundError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


    def _load_data_file(self, question_name: str, file_name: str):
        """
        Placeholder function 
        Helper function to load a specific CSV or json file, using the appropriate method based on file extension.. Raises FileNotFoundError if missing.
        
        example usage: 
        define and call a load_data_file() function from utils.py to load a specific file in the input_path directory
        save all data as class attributes (e.g. self.demand, self.wind, etc.), structured as pandas DataFrames or Series (or other format as prefered)"""
        file_path = self.data_path / file_name

        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} not found.")

        try:
            if file_path.suffix.lower() == '.json':
                with open(file_path, 'r') as f:
                    return json.load(f)
            elif file_path.suffix.lower() == '.csv':
                with open(file_path, 'r') as f:
                    return list(csv.DictReader(f))
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
        except Exception as e:
            raise IOError(f"Error loading {file_path}: {e}")

    def load_aux_data(self, question_name: str, filename: str):
        """
        Placeholder Helper function to Load auxiliary metadata for the scenario/question from a YAML/json file or other formats
        
        Example application: 
        define and call a load_aux_data() function from utils.py to load a specific auxiliary file in the input_path directory
        Save the content as s class attributes, in a dictionary, pd datframe or other: self.aux_data
        Attach key values as class attributes (flattened).
        """
        pass