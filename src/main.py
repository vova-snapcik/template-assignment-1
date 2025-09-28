#%% Imports


from data_ops import DataLoader
from pathlib import Path
import pandas as pd

from opt_model import OptModel

#%% Main function
def main():
    # Resolve the data directory relative to this file
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root  / "data"  # adjust if needed

    # Load all data for question_1a
    loader = DataLoader(input_path=str(data_dir), question_name="question_1a")
    all_data = loader._load_dataset()
    print("Loaded data files:", list(all_data.keys()))

    # Convert all loaded datasets to pandas DataFrames if possible
    df_data = {}
    for name, content in all_data.items():
        if isinstance(content, list):
            # Convert list of dicts to DataFrame
            df_data[name] = pd.DataFrame(content)
        else:
            # Keep as-is if not a list (e.g., None or single dict)
            df_data[name] = content

    optmodel = OptModel(df_data)

    # print(df_data)
    
    optmodel.build_and_solve()

    # Example: access one DataFrame
    # DER_production_df = df_data.get("DER_production")
    # appliacnce_params_df = df_data.get("appliacnce_params")
    # consumer_params_df = df_data.get("consumer_params")
    # usage_preference_df = df_data.get("usage_preference")
    # bus_params_df = df_data.get("bus_params")


    # print(DER_production_df)
    # print(appliacnce_params_df)
    # print(consumer_params_df)
    # print(usage_preference_df)
    # print(bus_params_df)


    # Return all DataFrames
    # return DER_production_df, df_data

#%% Run main and capture data
if __name__ == "__main__":
    # DER_production_df, df_data = main()
    main()
    # Now you can print outside the function
    # print("\nDER_production DataFrame:\n", DER_production_df)
    # print("All dataset keys:", list(df_data.keys()))

