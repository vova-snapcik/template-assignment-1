# data_visualizer.py
#import matplotlib
#matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
import os
import numpy as np

def plot_single_scenario(results, scenario_name="Scenario", save_dir=None):
    #plt.ion()
    
    # """Plot primal variables and duals for one scenario using OO style."""
    # print(f"[DEBUG] Called plot_single_scenario for {scenario_name}")
    # print(f"[DEBUG] save_dir = {save_dir}")
    # print("RESULTS:")
    # print(results)
    hours = range(len(results["p_load"]))

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot on the axis object
    ax.plot(hours, results["p_import"], label="Import", marker="o")
    ax.plot(hours, results["p_export"], label="Export", marker="s")
    ax.plot(hours, results["p_pv"], label="PV", marker="^")
    ax.plot(hours, results["p_load"], label="Load", marker="x")

    # Labels and title
    ax.set_xlabel("Hour")
    ax.set_ylabel("Energy (kWh)")
    ax.set_title(f"Scenario: {scenario_name}")
    ax.legend(loc="upper left")
    print(save_dir)

    # Save if requested
    # if save_dir is not None:
    #     os.makedirs(save_dir, exist_ok=True)
    #     file_path = Path(save_dir) / f"{scenario_name}.png"
    #     fig.savefig(file_path, dpi=300, bbox_inches="tight")
    #     print(f"[DEBUG] Saved plot to {file_path}, exists={file_path.exists()}")

    if save_dir is not None:
        
        os.makedirs(save_dir, exist_ok=True)
        file_path = (save_dir) / f"{scenario_name}.png"
        fig.savefig(file_path, dpi=300, bbox_inches="tight")
        print(file_path)
        # print(f"[DEBUG] Saved plot to {file_path}")
        # print(f"[DEBUG] File exists? {file_path.exists()}")

    


    # Show the figure
    # plt.show(block=True)
    # input("Press Enter to exit...")
