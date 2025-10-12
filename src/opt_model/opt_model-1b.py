# src/opt_model/opt_model.py
import gurobipy as gp
from gurobipy import GRB
from pathlib import Path

class OptModel1b:

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

        # ... after m.optimize()

        # To see the load profile:
        print(f"Load Profile: {[p_load[t].X for t in hours]}")

        # To see the values of the other variables to fully interpret the load:
        # print(f"Import Profile: {[p_import[t].X for t in hours]}")
        # print(f"Export Profile: {[p_export[t].X for t in hours]}")
        # print(f"PV Curtailed Profile: {[p_pv_curt[t].X for t in hours]}")

        self.model = m

        # --- Q1.b: Multi-Objective (Epsilon-Constraint Method) ---

    def build_and_solve_multi_objective(self, mode="cost_only", epsilon_discomfort=None):

        # --- 1. Extract and Prepare Data ---
        bus_df = self.data["bus_params"]
        der_df = self.data["DER_production"]
        load_df = self.data["appliance_params"]["load"]
        der_appliance_df = self.data["appliance_params"]["DER"]
        usage_pref_df = self.data["usage_preferences"]

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
        p_pv = m.addVars(hours, name="p_pv", lb=0, ub=max_pv_power)
        p_pv_curt = m.addVars(hours, name="p_pv_curt", lb=0)
        p_import = m.addVars(hours, name="p_import", lb=0, ub=max_import)
        p_export = m.addVars(hours, name="p_export", lb=0, ub=max_export)

        # --- 4. Constraints (Mandatory for Q1.ii) ---
        # Power Balance
        m.addConstrs((p_load[t] == p_pv[t] + p_import[t] - p_export[t]) for t in hours)
        # PV production limit
        m.addConstrs((p_pv[t] + p_pv_curt[t] == pv_max[t]) for t in hours)

        # --- 5. Define Objective Functions (Expressions) ---
        # J_cost: Procurement Cost
        J_cost = gp.quicksum(
            p_import[t] * (prices[t] + import_tariff) - p_export[t] * (prices[t] - export_tariff) for t in hours)

        # J_discomfort: Squared deviation from reference load
        J_discomfort = gp.quicksum((p_load[t] - p_ref[t]) * (p_load[t] - p_ref[t]) for t in hours)

        # --- 6. Solve based on Mode ---
        if mode == "cost_only":
            # PHASE 1: Find Epsilon_max (Max Discomfort at Min Cost)
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
            m.setObjective(J_cost, GRB.MINIMIZE)

            # Constraint: Discomfort must be less than epsilon
            m.addConstr(J_discomfort <= epsilon_discomfort, name="Epsilon_Constraint")

            m.optimize()

            if m.status == GRB.OPTIMAL:
                # Return actual discomfort achieved, min cost, and load profile
                actual_discomfort = J_discomfort.getValue()
                load_profile = [p_load[t].X for t in hours]
                return (actual_discomfort, m.ObjVal, load_profile)
            else:
                return None

        else:
            raise ValueError("Invalid mode specified for multi-objective solving.")
        











         
            
        elif mode == "battery" and epsilon_discomfort is not None:
            storage_capacity = der_storage_df[0]["storage_capacity_kWh"]
            max_ch_power_ratio = der_storage_df[0]["max_charging_power_ratio"]
            max_dis_power_ratio = der_storage_df[0]["max_discharging_power_ratio"]
            charging_efficiency = der_storage_df[0]["charging_efficiency"]
            discharging_efficiency = der_storage_df[0]["discharging_efficiency"]

            #Add variables for battery
            p_ch = m.addVars(hours, name="p_ch", lb=0, ub=max_ch_power_ratio*storage_capacity)
            p_dis = m.addVars(hours, name="p_dis", lb=0, ub=max_dis_power_ratio*storage_capacity)
            E_bat = m.addVars(hours, name="E_bat", lb=0, ub=storage_capacity)
            s_pos = m.addVars(hours, name="s_pos", lb=0)
            s_neg = m.addVars(hours, name="s_neg", lb=0)
            constraints = {}
            #initial energy in the battery
            E0 = storage_capacity*0.5 

            #Power Balance with battery
            # m.addConstr(E_bat[0] == E0 + (p_ch[0]*charging_efficiency - p_dis[0]/discharging_efficiency))

            constraints["init_soc"] = m.addConstr(
                E_bat[0] == E0 + (p_ch[0]*charging_efficiency - p_dis[0]/discharging_efficiency),
                name="init_soc"
            )
            #m.addConstr(E_bat[len(hours)-1] == E0, name="terminal_soc")

            constraints["terminal_soc"] = m.addConstr(E_bat[len(hours)-1] == E0, name="terminal_soc")

            # for t in hours:
            #     # if t == 0:
            #     #     m.addConstr(E_bat[t] == storage_capacity*0.5) #+ (p_ch[t] * charging_efficiency - p_dis[t] / discharging_efficiency))
            #     # elif t == 23:
            #     #     m.addConstr(E_bat[t] == storage_capacity*0.5) #+ (p_ch[t] * charging_efficiency - p_dis[t] / discharging_efficiency))
            #     # else:
            #     #     m.addConstr(E_bat[t] == E_bat[t-1] + (p_ch[t] * charging_efficiency - p_dis[t] / discharging_efficiency))
            #     m.addConstr(E_bat[t] == E_bat[t-1] + (p_ch[t] * charging_efficiency - p_dis[t] / discharging_efficiency))

            # for t in range(1, len(hours)):
            #     m.addConstr(E_bat[t] == E_bat[t-1] + (p_ch[t]*charging_efficiency - p_dis[t]/discharging_efficiency))

            constraints["soc_balance"] = {
                t: m.addConstr(
                    E_bat[t] == E_bat[t-1] + (p_ch[t]*charging_efficiency - p_dis[t]/discharging_efficiency),
                    name=f"soc_balance[{t}]"
                ) for t in range(1, len(hours))
            }

            #Set new power balance with battery
            #m.addConstrs((p_load[t] == p_pv[t] + p_import[t] - p_export[t]+p_dis[t] - p_ch[t]) for t in hours)

            constraints["power_balance"] = {
                t: m.addConstr(
                    p_load[t] == p_pv[t] + p_import[t] - p_export[t] + p_dis[t] - p_ch[t],
                    name=f"power_balance[{t}]"
                ) for t in hours
            }

            m.setObjective(J_cost, GRB.MINIMIZE)


            # Constraint: Discomfort must be less than epsilon
            #m.addConstr(J_discomfort <= epsilon_discomfort, name="Epsilon_Constraint")
            #constraints["epsilon"] = m.addConstr(J_discomfort <= epsilon_discomfort, name="Epsilon_Constraint")
            constraints["epsilon_abs"] = m.addConstr(
                gp.quicksum(s_pos[t] + s_neg[t] for t in hours) <= epsilon_discomfort,
                name="EpsilonAbs"
            )
            J_cost = gp.quicksum(
                p_import[t] * (prices[t] + import_tariff) - p_export[t] * (prices[t] - export_tariff)
                for t in hours
            )
            m.optimize()

            if m.status == GRB.OPTIMAL:
                # Return actual discomfort achieved, min cost, and load profile
                #actual_discomfort = J_discomfort.getValue()
                #load_profile = [p_load[t].X for t in hours]
                    # Power balance duals λ_t
                # for t, constr in constraints["power_balance"].items():
                #     try:
                #         print(f"lambda[{t}] = {constr.Pi:.4f}")
                #     except AttributeError:
                #         print(f"lambda[{t}] = (no dual, constraint redundant or presolved out)")

                # # SOC dynamics duals
                # for t, constr in constraints["soc_balance"].items():
                #     print(f"soc_balance[{t}] dual = {constr.Pi:.4f}")

                # # Initial / terminal SOC multipliers
                # print(f"init_soc dual = {constraints['init_soc'].Pi:.4f}")
                # print(f"terminal_soc dual = {constraints['terminal_soc'].Pi:.4f}")

                # # Quadratic epsilon constraint → use QCPi, not Pi
                # print(f"epsilon dual = {constraints['epsilon'].QCPi:.4f}")
                print("\n=== PRIMAL SOLUTION ===")
                # Decision variable values
                
                print("Hour | Load  | Import | Export | PV     | Charge | Discharge | SoC")
                for t in hours:
                    print(f"{t:02d}   | "
                        f"{p_load[t].X:6.2f} | "
                        f"{p_import[t].X:6.2f} | "
                        f"{p_export[t].X:6.2f} | "
                        f"{p_pv[t].X:6.2f} | "
                        f"{p_ch[t].X:6.2f} | "
                        f"{p_dis[t].X:6.2f} | "
                        f"{E_bat[t].X:6.2f}")

                print(f"\nTotal cost = {m.ObjVal:.4f} DKK/day")

                print("\n=== DUAL SOLUTION ===")
                for t, constr in constraints["power_balance"].items():
                    try:
                        print(f"lambda[{t}] = {constr.Pi:.4f}")
                    except:
                        print(f"lambda[{t}] = not available")

                for t, constr in constraints["soc_balance"].items():
                    try:
                        print(f"soc_balance[{t}] = {constr.Pi:.4f}")
                    except:
                        print(f"soc_balance[{t}] = not available")

                try:
                    print(f"init_soc dual = {constraints['init_soc'].Pi:.4f}")
                except:
                    print("init_soc dual not available")

                try:
                    print(f"terminal_soc dual = {constraints['terminal_soc'].Pi:.4f}")
                except:
                    print("terminal_soc dual not available")

                try:
                    print(f"epsilon dual = {constraints['epsilon'].QCPi:.4f}")
                except:
                    print("epsilon dual not available")


                
                # total_load = sum(p_load[t].X for t in hours)
                # total_import = sum(p_import[t].X for t in hours)
                # total_battery_discharge = sum(p_dis[t].X for t in hours)
                # total_battery_charge = sum(p_ch[t].X for t in hours)
                # total_pv = sum(p_pv[t].X for t in hours)
                # total_export = sum(p_export[t].X for t in hours)
                # total_pv_used = total_pv - total_export

                # # Print energy summary
                # print("\n=== Energy Summary ===")
                # print(f"Total energy consumed by load: {total_load:.4f} kWh/day")
                # print(f"  ├─ From grid (import): {total_import:.4f} kWh/day")
                # print(f"  ├─ From PV:             {total_pv_used:.4f} kWh/day")
                # print(f"  ├─ Export:             {total_export:.4f} kWh/day")
                # print(f"  └─ Battery discharge:   {total_battery_discharge:.4f} kWh/day")
                # print(f"  └─ Battery charge:   {total_battery_charge:.4f} kWh/day")
                # print("\n=== Optimal Dual Values ===")
                #for constr in m.getConstrs():
                #    print(f"{constr.ConstrName} dual: {constr.Pi}")
                return m.ObjVal
                #return (actual_discomfort, m.ObjVal, load_profile)
            else:
                return None



        elif mode == "battery" and epsilon_discomfort is not None:
            # --- params and data already extracted above ---

            # Turn OFF NonConvex since we’re now fully linear
            m = gp.Model("Consumer_Q1c_Battery_LP")  # replace the earlier model object
            # m.params.Method = 1  # (optional) force dual-simplex if you like
            # m.params.Presolve = 2  # (optional) aggressive presolve

            # --- Decision variables ---
            p_load = m.addVars(hours, name="p_load", lb=0, ub=max_load)
            p_pv = m.addVars(hours, name="p_pv", lb=0, ub=pv_max)
            p_import = m.addVars(hours, name="p_import", lb=0, ub=max_import)
            p_export = m.addVars(hours, name="p_export", lb=0, ub=max_export)

            # Battery
            storage_capacity = der_storage_df[0]["storage_capacity_kWh"]
            max_ch_power_ratio = der_storage_df[0]["max_charging_power_ratio"]
            max_dis_power_ratio = der_storage_df[0]["max_discharging_power_ratio"]
            charging_efficiency = der_storage_df[0]["charging_efficiency"]
            discharging_efficiency = der_storage_df[0]["discharging_efficiency"]

            p_ch = m.addVars(hours, name="p_ch", lb=0, ub=max_ch_power_ratio*storage_capacity)
            p_dis = m.addVars(hours, name="p_dis", lb=0, ub=max_dis_power_ratio*storage_capacity)
            E_bat = m.addVars(hours, name="E_bat", lb=0, ub=storage_capacity)

            # L1 deviation (linear) auxiliary vars
            # d_t = p_load - p_ref = s_pos - s_neg; |d_t| = s_pos + s_neg
            s_pos = m.addVars(hours, name="s_pos", lb=0)
            s_neg = m.addVars(hours, name="s_neg", lb=0)

            # Reference profile from data
            p_ref_profile = usage_pref_df["load_preferences"].iloc[0][0]["hourly_profile_ratio"]
            p_ref = [max_load * ratio for ratio in p_ref_profile]

            # --- Constraints ---
            constraints = {}

            # Power balance with battery
            constraints["power_balance"] = {
                t: m.addConstr(
                    p_load[t] == p_pv[t] + p_import[t] - p_export[t] + p_dis[t] - p_ch[t],
                    name=f"power_balance[{t}]"
                ) for t in hours
            }

            # Battery SOC dynamics + boundary
            E0 = storage_capacity * 0.5  # initial SOC at 50%
            constraints["init_soc"] = m.addConstr(
                E_bat[0] == E0 + (p_ch[0]*charging_efficiency - p_dis[0]/discharging_efficiency),
                name="init_soc"
            )
            constraints["soc_balance"] = {
                t: m.addConstr(
                    E_bat[t] == E_bat[t-1] + (p_ch[t]*charging_efficiency - p_dis[t]/discharging_efficiency),
                    name=f"soc_balance[{t}]"
                ) for t in range(1, len(p_ref))
            }
            constraints["terminal_soc"] = m.addConstr(
                E_bat[len(p_ref)-1] == E0, name="terminal_soc"
            )

            # L1 deviation definition: p_load - p_ref = s_pos - s_neg
            constraints["deviation_def"] = {
                t: m.addConstr(p_load[t] - p_ref[t] == s_pos[t] - s_neg[t], name=f"deviation_def[{t}]")
                for t in hours
            }

            # Linear epsilon constraint on absolute deviation
            # Choose epsilon_discomfort as sum of |deviation| tolerance (kWh)
            constraints["epsilon_abs"] = m.addConstr(
                gp.quicksum(s_pos[t] + s_neg[t] for t in hours) <= epsilon_discomfort,
                name="EpsilonAbs"
            )

            # --- Objective: minimize procurement cost (unchanged) ---
            J_cost = gp.quicksum(
                p_import[t] * (prices[t] + import_tariff) - p_export[t] * (prices[t] - export_tariff)
                for t in hours
            )
            m.setObjective(J_cost, GRB.MINIMIZE)

            # --- Solve ---
            m.optimize()

            # --- Print results (primal + duals) ---
            if m.status == GRB.OPTIMAL:
                print("\n=== PRIMAL SOLUTION (LP) ===")
                print("Hour | Load  | Import | Export | PV     | Charge | Discharge | SoC | |dev|")
                for t in hours:
                    abs_dev = s_pos[t].X + s_neg[t].X
                    print(f"{t:02d}   | "
                        f"{p_load[t].X:6.2f} | "
                        f"{p_import[t].X:6.2f} | "
                        f"{p_export[t].X:6.2f} | "
                        f"{p_pv[t].X:6.2f} | "
                        f"{p_ch[t].X:6.2f} | "
                        f"{p_dis[t].X:6.2f} | "
                        f"{E_bat[t].X:6.2f} | "
                        f"{abs_dev:6.2f}")

                print(f"\nTotal cost = {m.ObjVal:.4f} DKK/day")
                print(f"Total |deviation| = {sum(s_pos[t].X + s_neg[t].X for t in hours):.4f} kWh")

                print("\n=== DUALS (shadow prices) ===")
                # Power balance duals λ_t
                for t, constr in constraints["power_balance"].items():
                    try:
                        print(f"lambda[{t}] (power balance) = {constr.Pi:.6f}")
                    except:
                        print(f"lambda[{t}] (power balance) = not available")

                # SOC dynamics and boundary
                try:
                    print(f"init_soc dual = {constraints['init_soc'].Pi:.6f}")
                except:
                    print("init_soc dual = not available")

                for t, constr in constraints["soc_balance"].items():
                    try:
                        print(f"soc_balance[{t}] dual = {constr.Pi:.6f}")
                    except:
                        print(f"soc_balance[{t}] dual = not available")

                try:
                    print(f"terminal_soc dual = {constraints['terminal_soc'].Pi:.6f}")
                except:
                    print("terminal_soc dual = not available")

                # Epsilon (absolute deviation) dual
                try:
                    print(f"epsilon_abs dual = {constraints['epsilon_abs'].Pi:.6f}")
                except:
                    print("epsilon_abs dual = not available")

                # Deviation definition duals (helpful to see tightness vs slackness)
                # These act like KKT stationarity links between p_load and s_pos/s_neg
                for t, constr in constraints["deviation_def"].items():
                    try:
                        print(f"deviation_def[{t}] dual = {constr.Pi:.6f}")
                    except:
                        print(f"deviation_def[{t}] dual = not available")

                return m.ObjVal
            else:
                return None

            

            
       

           

        else:
            raise ValueError("Invalid mode specified for multi-objective solving.")

