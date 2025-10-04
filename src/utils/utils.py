"placeholder for various utils functions"

# src/utils/utils.py
import json
import csv
import numpy as np
import pandas as pd
from pathlib import Path
from opt_model import OptModel

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


# --- Helper Function for Multi-Objective Logic (Q1.ii) ---
def run_epsilon_constraint(df_data):
    """Executes the two-phase epsilon-constraint procedure."""

    # Phase 1: Find Max Discomfort (Epsilon_max)
    optmodel = OptModel(df_data)
    epsilon_max = optmodel.build_and_solve_multi_objective(mode="cost_only")

    if epsilon_max is None:
        print("Optimization failed during Phase 1. Cannot proceed.")
        return

    # Phase 2: Generate Pareto Front
    num_points = 10  # Number of points to generate on the Pareto front
    epsilon_min = 0.0  # Assumed minimum discomfort (perfect reference match)

    # Create a grid of epsilon values
    epsilon_values = np.linspace(epsilon_min, epsilon_max, num_points)

    pareto_solutions = []

    print(f"\n--- Phase 2: Solving {num_points} Epsilon-Constraint Problems ---")

    for k, epsilon in enumerate(epsilon_values):
        print(f"  Solving for Epsilon[{k + 1}/{num_points}] = {epsilon:.4f}")

        # Instantiate a new model for each run to ensure clean optimization
        current_model = OptModel(df_data)

        result = current_model.build_and_solve_multi_objective(
            mode="epsilon",
            epsilon_discomfort=epsilon
        )

        if result:
            actual_discomfort, min_cost, _ = result
            pareto_solutions.append({
                'epsilon_target': epsilon,
                'actual_discomfort': actual_discomfort,
                'min_cost': min_cost
            })

    # Results Summary
    print("\n-------------------------------------------------------------")
    print("      Pareto Frontier Results (Discomfort vs. Cost)      ")
    print("-------------------------------------------------------------")
    print("Target $\epsilon$ | Actual Discomfort | Min Cost (DKK)")
    print("-------------------------------------------------------------")
    for sol in pareto_solutions:
        print(f"{sol['epsilon_target']:^11.4f} | {sol['actual_discomfort']:^17.4f} | {sol['min_cost']:^13.4f}")
    print("-------------------------------------------------------------")