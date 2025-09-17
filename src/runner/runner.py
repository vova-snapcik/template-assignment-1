from pathlib import Path
from typing import Dict, List


class Runner:
    """
    Handles configuration setting, data loading and preparation, model(s) execution, results saving and ploting
    """

    def __init__(self) -> None:
        """Initialize the Runner."""

    def _load_config(self) -> None:
        """Load configuration (placeholder method)"""
    # Extract simulation configuration and hyperparameter values (e.g. question, scenarios for sensitivity analysis, duration of simulation, solver name, etc.) and store them as class attributes (e.g. self.scenario_list, self.solver_name, etc.)
    
    def _create_directories(self) -> None:
        """Create required directories for each simulation configuration. (placeholder method)"""

    def prepare_data_single_simulation(self, question_name) -> None:
        """Prepare input data for a single simulation (placeholder method)"""
        # Prepare input data using DataProcessor for a given simulation configuration and store it as class attributes (e.g. self.data)

    def prepare_data_all_simulations(self) -> None:
        """Prepare input data for multiple scenarios/sensitivity analysis/questions (placeholder method)"""
        # Extend data_loader to handle multiple scenarios/questions
        # Prepare data using data_loader for multiple scenarios/questions
        
    def run_single_simulation(self,Args) -> None:
        """
        Run a single simulation for a given question and simulation path (placeholder method).

        Args (examples):
            question: The question name for the simulation
            simulation_path: The path to the simulation data

        """
        # Initialize Optimization Model for the given question and simulation path
        # Run the model
        pass
    def run_all_simulations(self) -> None:
        """Run all simulations for the configured scenarios (placeholder method)."""
        pass