"""
Placeholder for main function to execute the model runner. This function creates a single/multiple instance of the Runner class, prepares input data,
and runs a single/multiple simulation.

Suggested structure:
- Import necessary modules and functions.
- Define a main function to encapsulate the workflow (e.g. Create an instance of your the Runner class, Run a single simulation or multiple simulations, Save results and generate plots if necessary.)
- Prepare input data for a single simulation or multiple simulations.
- Execute main function when the script is run directly.
"""

from data_ops import DataLoader
from pathlib import Path


def main():
    # Resolve the data directory relative to this file so the script
    # works regardless of the current working directory when executed.
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"

    loader = DataLoader(input_path=str(data_dir), question_name="question_1a")

    all_data = loader._load_dataset()
    print("Loaded data files:", list(all_data.keys()))

    # Example: access one dataset
    appliance_params = all_data.get("appliance_params")
    print("\nAppliance Params Example:\n", appliance_params)


if __name__ == "__main__":
    main()