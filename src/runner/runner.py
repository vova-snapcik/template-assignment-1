from pathlib import Path
from typing import Dict, List
from copy import deepcopy
from opt_model import OptModel


class Runner:
    """
    Handles configuration setting, data loading and preparation, model(s) execution, results saving and ploting
    """

    def __init__(self, df_data, scenarios) -> None:
        self.df_data = df_data
        self.scenarios = scenarios
        self.results = {}

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

    def run_scenario_analysis(self):
        results = {}
        for name, sc in self.scenarios.items():
            modified_data = deepcopy(self.df_data)
            bus_df = modified_data["bus_params"]

            # Apply scenario-specific modifications
            #Modify prices if specified in the scenario
            if "prices" in sc:
                bus_df["electricity_prices"] = sc["prices"]
            
            #Modify tariffs if specified in the scenario
            if "import_tariff" in sc:
                bus_df["import_tariff"] = sc["import_tariff"]
            if "export_tariff" in sc:
                bus_df["export_tariff"] = sc["export_tariff"]
            if "epsilon" in sc:
                bus_df["epsilon"] = sc["epsilon"]

                

            
            # Apply scenario modifications to modified_data
            # e.g., modified_data['some_param'] *= sc['multiplier']
            model = OptModel(modified_data)
            res = model.build_and_solve()
            results[name] = res  
        self.results = results
        return results
        """Run scenario analysis for the configured scenarios (placeholder method)."""
        pass

    def run_scenario_analysis_battery(self):
        results = {}
        for name, sc in self.scenarios.items():
            modified_data = deepcopy(self.df_data)
            bus_df = modified_data["bus_params"]

            # Apply scenario-specific modifications
            #Modify prices if specified in the scenario
            if "prices" in sc:
                bus_df["electricity_prices"] = sc["prices"]
            
            #Modify tariffs if specified in the scenario
            if "import_tariff" in sc:
                bus_df["import_tariff"] = sc["import_tariff"]
            if "export_tariff" in sc:
                bus_df["export_tariff"] = sc["export_tariff"]
            if "epsilon" in sc:
                bus_df["epsilon"] = sc["epsilon"]

                

            
            # Apply scenario modifications to modified_data
            # e.g., modified_data['some_param'] *= sc['multiplier']
            model = OptModel(modified_data)
            res = model.build_and_solve_multi_objective()
            results[name] = res  
        self.results = results
        return results
