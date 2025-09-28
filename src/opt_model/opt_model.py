# src/opt_model/opt_model.py
import gurobipy as gp
from gurobipy import GRB

class OptModel:

    def __init__(self, data: dict):
        self.data = data
        self.model = None

    def build_and_solve(self):
        # Extract data
        bus_df = self.data["bus_params"]
        der_df = self.data["DER_production"]
        load_df = self.data["appliance_params"]["load"]
        der_appliance_df = self.data["appliance_params"]["DER"]
        usage_pref_df = self.data["usage_preference"]

        # print(der_df)
        # print(load_df)
        # print(load_df)
        # print(usage_pref)
        # print(bus_df)

        # Get parameters
        prices = bus_df["energy_price_DKK_per_kWh"].iloc[0]
        import_tariff = bus_df["import_tariff_DKK/kWh"].iloc[0]
        export_tariff = bus_df["export_tariff_DKK/kWh"].iloc[0]
        max_import = bus_df["max_import_kW"].iloc[0]
        max_export = bus_df["max_export_kW"].iloc[0]

        max_pv_power = der_appliance_df[0]["max_power_kW"]
        pv_profile = der_df["hourly_profile_ratio"].iloc[0]
        hours = range(len(prices))

        max_load = load_df[0]["max_load_kWh_per_hour"]
        load_prefs = usage_pref_df["load_preferences"].iloc[0]
        min_total_energy = load_prefs[0]["min_total_energy_per_day_hour_equivalent"]


        # PV max production
        pv_max = [max_pv_power * ratio for ratio in pv_profile]

        # Model
        m = gp.Model("Consumer_Flexibility")

        # Decision variables
        p_load = m.addVars(hours, name="p_load", lb=0, ub=max_load)
        p_pv = m.addVars(hours, name="p_pv", lb=0, ub=max_pv_power)
        p_pv_curt = m.addVars(hours, name="p_pv_curt", lb=0)
        p_import = m.addVars(hours, name="p_import", lb=0, ub=max_import)
        p_export = m.addVars(hours, name="p_export", lb=0, ub=max_export)

        # Constraints
        #Power Balance
        m.addConstrs((p_load[t] == p_pv[t] + p_import[t] - p_export[t]) for t in hours)
        #PV production limit
        m.addConstrs((p_pv[t] + p_pv_curt[t] == pv_max[t]) for t in hours)


        # Total load energy requirement
        m.addConstr(gp.quicksum(p_load[t] for t in hours) >= min_total_energy)

        # Objective
        total_cost = gp.quicksum(p_import[t] * (prices[t] + import_tariff)- p_export[t] * (prices[t] - export_tariff) for t in hours)
        m.setObjective(total_cost, GRB.MINIMIZE)

        # Solve
        m.optimize()

        # Print results
        if m.status == GRB.OPTIMAL:
            optimal_objective = m.ObjVal
            #optimal_production_variables = [production_variables[g].x for g in GENERATORS] 
            #balance_dual = balance_constraint.Pi
            #capacity_optimal_duals = [capacity_constraints[g].Pi for g in GENERATORS]

        #     optimal_objective = m.ObjVal
        #     #optimal_dual_1 = p_load.Pi
        #     optimal_dual_2 = p_pv_curt.Pi
        #     # print(f"optimal value of dual for {constraint_1.constrName}: {optimal_dual_1}")
        #     print(f"optimal value of dual for {constraint_2.constrName}: {optimal_dual_2}")
        
        # else:
        #     print(f"optimization of {model.ModelName} was not successful")
            
        print(f"PV {p_pv}")
        # print(f"optimal objective: {optimal_objective}")

        self.model = m


