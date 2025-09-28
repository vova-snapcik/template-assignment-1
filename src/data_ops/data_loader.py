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

from utils import load_dataset



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


    def __init__(self, input_path: str, question_name: str):
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
        self.question_name = question_name

        # Data storage
        self.data = {}
        self.aux_data = {}
        

    def _load_dataset(self):
        """Helper function to load all CSV or json files, using the appropriate method based on file extension.
        
        example usage: 
        call the load_dataset() function from utils.py to load all files in the input_path directory
        save all data as class attributes (e.g. self.demand, self.wind, etc.), structured as pandas DataFrames or Series (or other format as prefered)
        """
        self.data = load_dataset(self.input_path, self.question_name)
        return self.data


    def _load_data_file(self, file_name: str):
        """
        Placeholder function 
        Helper function to load a specific CSV or json file, using the appropriate method based on file extension.. Raises FileNotFoundError if missing.
        
        example usage: 
        define and call a load_data_file() function from utils.py to load a specific file in the input_path directory
        save all data as class attributes (e.g. self.demand, self.wind, etc.), structured as pandas DataFrames or Series (or other format as prefered)"""
        file_path = self.input_path / self.question_name / file_name

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()
        if suffix == ".json":
            with open(file_path, "r") as f:
                return json.load(f)
        elif suffix == ".csv":
            return pd.read_csv(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    def load_aux_data(self, filename: str):
        """
        Placeholder Helper function to Load auxiliary metadata for the scenario/question from a YAML/json file or other formats
        
        Example application: 
        define and call a load_aux_data() function from utils.py to load a specific auxiliary file in the input_path directory
        Save the content as s class attributes, in a dictionary, pd datframe or other: self.aux_data
        Attach key values as class attributes (flattened).
        """
        file_path = self.input_path / self.question_name / filename

        if not file_path.exists():
            raise FileNotFoundError(f"Aux file not found: {file_path}")

        suffix = file_path.suffix.lower()
        if suffix == ".yaml" or suffix == ".yml":
            with open(file_path, "r") as f:
                self.aux_data = yaml.safe_load(f)
        elif suffix == ".json":
            with open(file_path, "r") as f:
                self.aux_data = json.load(f)
        else:
            raise ValueError(f"Unsupported aux file type: {suffix}")

        return self.aux_data
    
    def load_dataset_as_df(self):
        """
        Load all JSON/CSV files under question_name and convert them to pandas DataFrames
        if possible.
        """
        data_dict = self._load_dataset()
        df_dict = {}

        for name, content in data_dict.items():
            # Only convert lists of dicts to DataFrames
            if isinstance(content, list):
                df_dict[name] = pd.DataFrame(content)
            else:
                df_dict[name] = content  # keep as-is if not a list of dicts

        return df_dict