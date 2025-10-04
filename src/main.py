#%% Imports

from data_ops import DataLoader
from pathlib import Path
import pandas as pd

from opt_model import OptModel
from utils import run_epsilon_constraint

# --- Main function to control execution ---
def main(question_flag="1.c"):
    # Set data file prefix based on the flag
    if question_flag == "1.a":
        data_prefix = "question_1a"
        print("--- Running: Question 1.a (Min Cost w/ Min Energy Target) ---")
    elif question_flag == "1.b":
        data_prefix = "question_1b"  # Assuming Q1.ii uses the same data set
        print("--- Running: Question 1.b (Multi-Objective Epsilon-Constraint) ---")
    elif question_flag == "1.c":
        data_prefix = "question_1c"  # Assuming Q1.ii uses the same data set
        print("--- Running: Question 1.c (Installing battery) ---")
    else:
        print(f"Unknown question flag: {question_flag}. Exiting.")
        return

    # Resolve the data directory
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"

    # Load data
    loader = DataLoader(input_path=str(data_dir), question_name=data_prefix)
    all_data = loader._load_dataset()

    # Convert to DataFrames
    df_data = {}
    for name, content in all_data.items():
        if isinstance(content, list):
            df_data[name] = pd.DataFrame(content)
        else:
            df_data[name] = content

    # Execute the selected problem
    if question_flag == "1.a":
        # Run original single-objective problem
        optmodel = OptModel(df_data)
        optmodel.build_and_solve()

    elif question_flag == "1.b":
        # Run new multi-objective problem
        #run_epsilon_constraint(df_data)
        current_model = OptModel(df_data)
        result = current_model.build_and_solve_multi_objective(
            mode="epsilon",
            epsilon_discomfort=run_epsilon_constraint(df_data))
        
    
    elif question_flag == "1.c":
        # Placeholder for Q1.c implementation
        current_model = OptModel(df_data)
        result = current_model.build_and_solve_multi_objective(
            mode="battery",
            epsilon_discomfort=24)
        


# %% Execution
if __name__ == "__main__":
    # To switch exercises, simply change the flag below:
    # Use "1.a" for the original cost minimization problem
    # Use "1.b" for the new epsilon-constraint problem
    # Use "1.c" for the battery installation problem (not yet implemented)

    main(question_flag="1.b")

    """
#Ignore this for now, just used for 1a previously

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



"""