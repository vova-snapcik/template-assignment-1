"""Convex quadratic models used in Question 3.

The module keeps Question 3 separate from the generic starter model.  It supports
the unconstrained Q2(c) benchmark, the minimum-daily-energy model, and the same
model with a battery and a cyclic end-of-horizon state of charge.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import gurobipy as gp
import numpy as np
import pandas as pd
from gurobipy import GRB

from .data_loader import InputData


@dataclass
class Q3Results:
    """Solved Question 3 schedule and its daily economic metrics."""

    label: str
    hourly: pd.DataFrame
    total_cost: float
    net_utility: float
    procurement_cost: float
    pv_cost: float
    disutility: float
    total_load: float
    energy_dual: float
    with_battery: bool

    def metrics(self) -> dict[str, float | str | bool]:
        """Return scalar results suitable for CSV tables."""
        deviation = self.hourly["load"] - self.hourly["reference_load"]
        result: dict[str, float | str | bool] = {
            "case": self.label,
            "with_battery": self.with_battery,
            "total_cost_DKK": self.total_cost,
            "net_utility_DKK": self.net_utility,
            "procurement_cost_DKK": self.procurement_cost,
            "pv_cost_DKK": self.pv_cost,
            "disutility_DKK": self.disutility,
            "total_load_kWh": self.total_load,
            "absolute_deviation_kWh": float(np.abs(deviation).sum()),
            "above_reference_kWh": float(np.maximum(deviation, 0.0).sum()),
            "below_reference_kWh": float(np.maximum(-deviation, 0.0).sum()),
            "energy_dual_DKK_per_kWh": self.energy_dual,
            "total_import_kWh": float(self.hourly["import"].sum()),
            "total_export_kWh": float(self.hourly["export"].sum()),
            "pv_used_kWh": float(self.hourly["pv"].sum()),
        }
        if self.with_battery:
            result.update(
                {
                    "battery_charge_kWh": float(self.hourly["charge"].sum()),
                    "battery_discharge_kWh": float(self.hourly["discharge"].sum()),
                    "battery_final_soc_kWh": float(self.hourly["soc"].iloc[-1]),
                    "charge_discharge_overlap_kWh": float(
                        np.minimum(self.hourly["charge"], self.hourly["discharge"]).sum()
                    ),
                }
            )
        return result

    def save(self, folder: Path | str) -> None:
        """Save the hourly schedule and scalar metrics as CSV files."""
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        self.hourly.to_csv(folder / f"{self.label}_hourly.csv", index_label="hour")
        pd.DataFrame([self.metrics()]).to_csv(folder / f"{self.label}_metrics.csv", index=False)


class Q3Model:
    """Build and solve the Q2(c), Q3, or Q3-with-battery convex QP."""

    def __init__(
        self,
        data: InputData,
        *,
        enforce_min_energy: bool,
        with_battery: bool = False,
        label: str = "q3",
        verbose: bool = False,
    ) -> None:
        self.data = data
        self.enforce_min_energy = enforce_min_energy
        self.with_battery = with_battery
        self.label = label
        self.T = range(data.n_hours)
        self.m = gp.Model(label)
        self.m.Params.OutputFlag = 1 if verbose else 0
        self.var: dict[str, gp.tupledict] = {}
        self.con: dict[str, gp.tupledict | gp.Constr] = {}

    def build(self) -> "Q3Model":
        """Declare variables, objective, hourly balance, and intertemporal constraints."""
        d, m, T = self.data, self.m, self.T
        if d.reference_load is None or d.quadratic_disutility is None:
            raise ValueError("Question 3 requires a reference load and a quadratic disutility coefficient.")

        self.var["import"] = m.addVars(T, lb=0.0, name="import")
        self.var["export"] = m.addVars(T, lb=0.0, name="export")
        self.var["pv"] = m.addVars(T, lb=0.0, name="pv")
        self.var["load"] = m.addVars(T, lb=-GRB.INFINITY, name="load")

        imp = self.var["import"]
        exp = self.var["export"]
        pv = self.var["pv"]
        load = self.var["load"]

        self.con["load_min"] = m.addConstrs(
            (load[t] >= d.load_min_kWh for t in T), name="load_min"
        )
        self.con["load_max"] = m.addConstrs(
            (load[t] <= d.load_max_kWh for t in T), name="load_max"
        )
        self.con["pv_max"] = m.addConstrs(
            (pv[t] <= float(d.pv_available[t]) for t in T), name="pv_max"
        )

        charge = discharge = soc = None
        if self.with_battery:
            required = (
                d.battery_capacity_kWh,
                d.battery_max_charge_kW,
                d.battery_max_discharge_kW,
                d.battery_charging_efficiency,
                d.battery_discharging_efficiency,
                d.battery_initial_soc_kWh,
            )
            if any(value is None for value in required):
                raise ValueError("Battery parameters are missing; load the Q3_battery data case.")

            charge = m.addVars(T, lb=0.0, ub=d.battery_max_charge_kW, name="charge")
            discharge = m.addVars(T, lb=0.0, ub=d.battery_max_discharge_kW, name="discharge")
            soc = m.addVars(T, lb=0.0, ub=d.battery_capacity_kWh, name="soc")
            self.var.update(charge=charge, discharge=discharge, soc=soc)

            self.con["soc_initial"] = m.addConstr(
                soc[0]
                == d.battery_initial_soc_kWh
                + d.battery_charging_efficiency * charge[0]
                - discharge[0] / d.battery_discharging_efficiency,
                name="soc_initial",
            )
            self.con["soc_dynamics"] = m.addConstrs(
                (
                    soc[t]
                    == soc[t - 1]
                    + d.battery_charging_efficiency * charge[t]
                    - discharge[t] / d.battery_discharging_efficiency
                    for t in range(1, d.n_hours)
                ),
                name="soc_dynamics",
            )
            # Cyclic policy: the next day starts with the same energy as the current day.
            self.con["soc_terminal"] = m.addConstr(
                soc[d.n_hours - 1] == d.battery_initial_soc_kWh,
                name="soc_terminal",
            )

        self.con["balance"] = m.addConstrs(
            (
                pv[t]
                + imp[t]
                + (discharge[t] if discharge is not None else 0.0)
                == load[t]
                + exp[t]
                + (charge[t] if charge is not None else 0.0)
                for t in T
            ),
            name="balance",
        )

        if self.enforce_min_energy:
            if d.min_daily_energy_kWh is None:
                raise ValueError("The minimum daily energy parameter is missing.")
            self.con["min_energy"] = m.addConstr(
                gp.quicksum(load[t] for t in T) >= d.min_daily_energy_kWh,
                name="min_energy",
            )

        import_price = d.energy_price + d.import_tariff
        export_price = d.energy_price - d.export_tariff
        m.setObjective(
            gp.quicksum(
                import_price[t] * imp[t]
                - export_price[t] * exp[t]
                + d.pv_marginal_cost * pv[t]
                + d.quadratic_disutility * (load[t] - float(d.reference_load[t])) ** 2
                for t in T
            ),
            GRB.MINIMIZE,
        )
        m.update()
        return self

    def solve(self) -> Q3Results:
        """Optimize the model and extract schedules, costs, and the daily-energy shadow price."""
        self.m.optimize()
        if self.m.Status != GRB.OPTIMAL:
            raise RuntimeError(f"{self.label} ended with Gurobi status {self.m.Status}.")

        d = self.data
        T = list(self.T)
        hourly = pd.DataFrame(index=pd.Index(T, name="hour"))
        hourly["price"] = d.energy_price
        hourly["import_price"] = d.energy_price + d.import_tariff
        hourly["export_price"] = d.energy_price - d.export_tariff
        hourly["pv_available"] = d.pv_available
        hourly["reference_load"] = d.reference_load
        for name, variables in self.var.items():
            hourly[name] = [variables[t].X for t in T]

        procurement = float(
            np.sum(hourly["import_price"] * hourly["import"])
            - np.sum(hourly["export_price"] * hourly["export"])
        )
        pv_cost = float(d.pv_marginal_cost * hourly["pv"].sum())
        disutility = float(
            d.quadratic_disutility
            * np.square(hourly["load"] - hourly["reference_load"]).sum()
        )
        total_cost = procurement + pv_cost + disutility
        energy_dual = float(self.con["min_energy"].Pi) if self.enforce_min_energy else 0.0

        return Q3Results(
            label=self.label,
            hourly=hourly,
            total_cost=total_cost,
            net_utility=-total_cost,
            procurement_cost=procurement,
            pv_cost=pv_cost,
            disutility=disutility,
            total_load=float(hourly["load"].sum()),
            energy_dual=energy_dual,
            with_battery=self.with_battery,
        )
