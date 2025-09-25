from pathlib import Path
import numpy as np
import pandas as pd
import gurobipy as gp
from gurobipy import GRB
import xarray as xr

from src.data_ops import data_loader


class OptModel:
    """
    Builds and solves an optimization problem using Gurobi based on input data provided by DataLoader.
    """
    def __init__(self, data_loader):
        """
        Initialize the optimization model with data from DataLoader.

        Args:
            data_loader (DataLoader): An instance of DataLoader containing input data.
        """
        self.data = data_loader
        self.model = gp.Model("ProcurementCostMinimization")
        self.H = 24  # Number of hours in the planning horizon

        self.variables = {}
        self.constraints = {}
        self.objective = None

    def build_model(self, consumer_id):
        """
        Builds the optimization model for a specific consumer.
        """
        try:
            consumer_data = self.data.consumers[self.data.consumers['consumer_id'] == consumer_id].iloc[0]
            usage_prefs = self.data.usage_preferences[self.data.usage_preferences['consumer_id'] == consumer_id].iloc[0]
            appliances_data = self.data.appliances


