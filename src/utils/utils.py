"placeholder for various utils functions"

# src/utils/utils.py
import json
import csv
import pandas as pd
from pathlib import Path

def load_dataset(base_path: Path, question_name: str):
    """
    Load all JSON or CSV files from the given question directory.
    Returns a dict where keys are filenames (without extension) and values are parsed content.
    """
    question_path = Path(base_path) / question_name
    result = {}

    if not question_path.exists():
        raise FileNotFoundError(f"Question directory not found: {question_path}")

    for file_path in question_path.glob("*"):
        if file_path.is_file():
            stem = file_path.stem
            suffix = file_path.suffix.lower()
            try:
                if suffix == ".json":
                    with open(file_path, "r") as f:
                        result[stem] = json.load(f)
                elif suffix == ".csv":
                    result[stem] = pd.read_csv(file_path)
                else:
                    with open(file_path, "r") as f:
                        result[stem] = f.read()
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

    return result


# example function to save model results in a specified directory
def save_model_results():
    """Placeholder for save_model_results function."""
    pass

# example function to plot data from a specified directory
def plot_data():
    """Placeholder for plot_data function."""
    pass