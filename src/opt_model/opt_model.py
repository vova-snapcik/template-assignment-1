# src/opt_model/opt_model.py
import gurobipy as gp
from gurobipy import GRB
from pathlib import Path

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
        min_total_energy_hour = load_prefs[0]["min_total_energy_per_day_hour_equivalent"]
        


        # PV max production
        pv_max = [max_pv_power * ratio for ratio in pv_profile]
        #min total energy requirement

        # Model
        m = gp.Model("Consumer_Flexibility")

        # Decision variables
        p_load = m.addVars(hours, name="p_load", lb=0, ub=max_load)
        p_pv = m.addVars(hours, name="p_pv", lb=0, ub=pv_max)
        p_pv_curt = m.addVars(hours, name="p_pv_curt", lb=0, ub=pv_max)
        p_import = m.addVars(hours, name="p_import", lb=0, ub=max_import)
        p_export = m.addVars(hours, name="p_export", lb=0, ub=max_export)
        min_total_energy = min_total_energy_hour * max_pv_power  # Convert to kWh/day

        # Constraints
        self.constraints = {}  
        #Power balance constraint
        for t in hours:
            self.constraints[f"power_balance[{t}]"] = m.addConstr(
                p_load[t] == p_pv[t] + p_import[t] - p_export[t],
                name=f"power_balance[{t}]"
            )



        # Minimum daily energy constraint 
        self.constraints["energy_min"] = m.addConstr(
            gp.quicksum(p_load[t] for t in hours) >= min_total_energy,
            name="energy_min"
        )

        # Objective function: Minimize total cost
        total_cost = gp.quicksum(p_import[t] * (prices[t] + import_tariff)- p_export[t] * (prices[t] - export_tariff) for t in hours)
        m.setObjective(total_cost, GRB.MINIMIZE)

        # Solve
        m.optimize()

        # Print results
        if m.status == GRB.OPTIMAL:

            #Store results
            results = {
            "obj": m.ObjVal,
            "p_load": [p_load[t].X for t in hours],
            "p_import": [p_import[t].X for t in hours],
            "p_export": [p_export[t].X for t in hours],
            "p_pv": [p_pv[t].X for t in hours],
            "duals": [constr.Pi for constr in m.getConstrs()]
            }

        
            #Print the     
            total_load = sum(p_load[t].X for t in hours)
            total_import = sum(p_import[t].X for t in hours)
            total_pv = sum(p_pv[t].X for t in hours)
            total_export = sum(p_export[t].X for t in hours)
            total_pv_used = total_pv - total_export
                
            print("\n -- Energy Summary -- ")
            print(f"Total energy consumed by load: {total_load:.4f} kWh/day")
            print(f"Imported from grid: {total_import:.4f} kWh/day")
            print(f"From PV:  {total_pv_used:.4f} kWh/day")

            #Print lambda and eta dual values
            for t in hours:
                lam = self.constraints[f"power_balance[{t}]"].Pi
                print(f"lambda[{t}] = {lam:.4f}")

            eta = self.constraints["energy_min"].Pi
            print(f"eta (min daily energy) = {eta:.4f}")

            return results
        else:
            print(f"Optimization of {m.ModelName} was not successful")
            return None


    

    

        # --- Q1.b: Multi-Objective (Epsilon-Constraint Method) ---

    def build_and_solve_multi_objective(self, mode="cost_only", epsilon_discomfort=None):

        # --- 1. Extract and Prepare Data ---
        bus_df = self.data["bus_params"]
        der_df = self.data["DER_production"]
        load_df = self.data["appliance_params"]["load"]
        der_appliance_df = self.data["appliance_params"]["DER"]
        usage_pref_df = self.data["usage_preferences"]
        der_storage_df = self.data["appliance_params"]["storage"]


        prices = bus_df["energy_price_DKK_per_kWh"].iloc[0]
        import_tariff = bus_df["import_tariff_DKK/kWh"].iloc[0]
        export_tariff = bus_df["export_tariff_DKK/kWh"].iloc[0]
        max_import = bus_df["max_import_kW"].iloc[0]
        max_export = bus_df["max_export_kW"].iloc[0]
        

        max_pv_power = der_appliance_df[0]["max_power_kW"]
        pv_profile = der_df["hourly_profile_ratio"].iloc[0]
        
        hours = range(len(prices))

        max_load = load_df[0]["max_load_kWh_per_hour"]

        # Reference Load (P_ref_t) - Used for discomfort calculation
        p_ref_profile = usage_pref_df["load_preferences"].iloc[0][0]["hourly_profile_ratio"]
        p_ref = [max_load * ratio for ratio in p_ref_profile]

        pv_max = [max_pv_power * ratio for ratio in pv_profile]

        # --- 2. Model Setup ---
        m = gp.Model("Consumer_Q1b_EpsilonConstraint")
        m.params.NonConvex = 2  # Required for quadratic constraints

        # --- 3. Decision Variables ---
        p_load = m.addVars(hours, name="p_load", lb=0, ub=max_load)
        p_pv = m.addVars(hours, name="p_pv", lb=0, ub=pv_max)
        #p_pv_curt = m.addVars(hours, name="p_pv_curt", lb=0)
        p_import = m.addVars(hours, name="p_import", lb=0, ub=max_import)
        p_export = m.addVars(hours, name="p_export", lb=0, ub=max_export)

        # --- 4. Constraints (Mandatory for Q1.ii) ---
        
        # PV production limit
        #m.addConstrs((p_pv[t] + p_pv_curt[t] == pv_max[t]) for t in hours)

        # --- 5. Define Objective Functions (Expressions) ---
        # J_cost: Procurement Cost
        J_cost = gp.quicksum(
            p_import[t] * (prices[t] + import_tariff) - p_export[t] * (prices[t] - export_tariff) for t in hours)

        # J_discomfort: Squared deviation from reference load
        J_discomfort = gp.quicksum((p_load[t] - p_ref[t]) * (p_load[t] - p_ref[t]) for t in hours)

        # --- 6. Solve based on Mode ---
        if mode == "cost_only":
            # PHASE 1: Find Epsilon_max (Max Discomfort at Min Cost)
            # Power Balance
            m.addConstrs((p_load[t] == p_pv[t] + p_import[t] - p_export[t]) for t in hours)
            m.setObjective(J_cost, GRB.MINIMIZE)
            m.optimize()

            if m.status == GRB.OPTIMAL:
                epsilon_max = J_discomfort.getValue()
                print(f"Phase 1: Max Discomfort (epsilon_max) found: {epsilon_max:.4f} kW^2/day")
                return epsilon_max
            else:
                print("Cost-only optimization failed.")
                return None

        elif mode == "epsilon" and epsilon_discomfort is not None:
            # PHASE 2: Epsilon-Constraint Run

            # Primary Objective: Minimize Cost
            # Power Balance

            m.addConstrs((p_load[t] == p_pv[t] + p_import[t] - p_export[t]) for t in hours)
            m.setObjective(J_cost, GRB.MINIMIZE)

            # Constraint: Discomfort must be less than epsilon
            m.addConstr(J_discomfort <= epsilon_discomfort, name="Epsilon_Constraint")
            #m.addConstr(p_load >= 27.9410, name="Epsilon_Constraint")

            m.optimize()
            print(gp.quicksum(pv_max[t] for t in hours))

            if m.status == GRB.OPTIMAL:
                # Return actual discomfort achieved, min cost, and load profile
                #actual_discomfort = J_discomfort.getValue()
                #load_profile = [p_load[t].X for t in hours]
                total_load = sum(p_load[t].X for t in hours)
                total_import = sum(p_import[t].X for t in hours)
                total_pv = sum(p_pv[t].X for t in hours)
                total_export = sum(p_export[t].X for t in hours)
                total_pv_used = total_pv - total_export
                    

            

            if m.status == GRB.OPTIMAL:
                # Return actual discomfort achieved, min cost, and load profile
                actual_discomfort = J_discomfort.getValue()
                load_profile = [p_load[t].X for t in hours]
                return (actual_discomfort, m.ObjVal, load_profile)
            
                
            else:
                return None
        elif mode == "battery" and epsilon_discomfort is not None:
            storage_capacity = der_storage_df[0]["storage_capacity_kWh"]
            max_ch_power_ratio = der_storage_df[0]["max_charging_power_ratio"]
            max_dis_power_ratio = der_storage_df[0]["max_discharging_power_ratio"]
            charging_efficiency = der_storage_df[0]["charging_efficiency"]
            discharging_efficiency = der_storage_df[0]["discharging_efficiency"]

            # Add variables for battery
            p_ch = m.addVars(hours, name="p_ch", lb=0,
                            ub=max_ch_power_ratio * storage_capacity)
            p_dis = m.addVars(hours, name="p_dis", lb=0,
                            ub=max_dis_power_ratio * storage_capacity)
            E_bat = m.addVars(hours, name="E_bat", lb=0, ub=storage_capacity)

            constraints = {}

            # Initial energy in the battery
            E0 = storage_capacity * 0.5

            # Power Balance with battery
            constraints["init_soc"] = m.addConstr(
                E_bat[0] == E0 + (p_ch[0] * charging_efficiency
                                - p_dis[0] / discharging_efficiency),
                name="init_soc"
            )
            #End SoC constraint
            constraints["terminal_soc"] = m.addConstr(
                E_bat[len(hours) - 1] == E0,
                name="terminal_soc"
            )
            #SoC balance constraints
            constraints["soc_balance"] = {
                t: m.addConstr(
                    E_bat[t] == E_bat[t - 1] + (p_ch[t] * charging_efficiency
                                                - p_dis[t] / discharging_efficiency),
                    name=f"soc_balance[{t}]"
                )
                for t in range(1, len(hours))
            }

            #Adding variables for positive and negative deviations to get dual values
            s_pos = m.addVars(hours, name="s_pos", lb=0)
            s_neg = m.addVars(hours, name="s_neg", lb=0)

            #Discomfort constraints
            for t in hours:
                m.addConstr(
                    p_load[t] - p_ref[t] == s_pos[t] - s_neg[t],
                    name=f"discomfort_balance[{t}]"
                )

            J_discomfort = gp.quicksum(s_pos[t] + s_neg[t] for t in hours)

            # Power balance with battery constraint
            constraints["power_balance"] = {
                t: m.addConstr(
                    p_load[t] == p_pv[t] + p_import[t] - p_export[t]
                                + p_dis[t] - p_ch[t],
                    name=f"power_balance[{t}]"
                )
                for t in hours
            }

            m.setObjective(J_cost, GRB.MINIMIZE)

            # Constraint: Discomfort must be less than epsilon
            constraints["epsilon"] = m.addConstr(
                J_discomfort <= epsilon_discomfort,
                name="Epsilon_Constraint"
            )

            m.optimize()

            if m.status == GRB.OPTIMAL:
                print("\n -- Energy Summary -- ")
                total_load = sum(p_load[t].X for t in hours)
                total_import = sum(p_import[t].X for t in hours)
                total_export = sum(p_export[t].X for t in hours)
                total_pv = sum(p_pv[t].X for t in hours)
                total_battery_discharge = sum(p_dis[t].X for t in hours)
                total_battery_charge = sum(p_ch[t].X for t in hours)
                total_pv_used = total_pv - total_export

                print(f"Total energy consumed by load: {total_load:.4f} kWh/day")
                print(f"Imported from grid: {total_import:.4f} kWh/day")
                print(f"From PV: {total_pv_used:.4f} kWh/day")
                print(f" Battery discharge: {total_battery_discharge:.4f} kWh/day")
                print(f"Battery charge: {total_battery_charge:.4f} kWh/day")


                #Power balance duals
                for t, constr in constraints["power_balance"].items():
                    try:
                        print(f"lambda[{t}] = {constr.Pi:.4f}")
                    except AttributeError:
                        print(f"lambda[{t}] = (no dual value)")

                # SOC dynamics duals
                for t, constr in constraints["soc_balance"].items():
                    print(f"soc_balance[{t}] dual = {constr.Pi:.4f}")

                # Initial / terminal SOC multipliers
                print(f"init_soc dual = {constraints['init_soc'].Pi:.4f}")
                print(f"terminal_soc dual = {constraints['terminal_soc'].Pi:.4f}")


                return m.ObjVal
            else:
                return None
