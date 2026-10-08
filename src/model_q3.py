"""Quadratic consumer models for the Q2(c) benchmark and Question 3.

Each formulation is a subclass of the team's FlexibleConsumerModel. Q3 adds a
daily energy constraint; Q3Battery adds storage and a cyclic terminal state.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import gurobipy as gp
import numpy as np
import pandas as pd
from gurobipy import GRB

from .data_loader import InputData
from .model import FlexibleConsumerModel


@dataclass
class Q3Results:
    """Hourly decisions and daily cost components from a quadratic model."""

    question: str
    label: str
    hourly: pd.DataFrame
    total_cost: float
    net_utility: float
    procurement_cost: float
    pv_cost: float
    disutility: float
    total_load: float
    energy_dual: float
    has_min_energy: bool
    with_battery: bool

    @property
    def objective(self) -> float:
        """Objective in the minimization convention used by the Q3 models."""
        return self.total_cost

    @property
    def duals(self) -> dict[str, float]:
        """Daily constraint duals, compatible with the team's result interface."""
        return {"min_energy": self.energy_dual} if self.has_min_energy else {}

    def metrics(self) -> dict[str, float | str | bool]:
        """Return daily quantities for CSV tables."""
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
            result.update({
                "battery_charge_kWh": float(self.hourly["charge"].sum()),
                "battery_discharge_kWh": float(self.hourly["discharge"].sum()),
                "battery_final_soc_kWh": float(self.hourly["soc"].iloc[-1]),
                "charge_discharge_overlap_kWh": float(
                    np.minimum(self.hourly["charge"], self.hourly["discharge"]).sum()
                ),
            })
        return result

    def save(self, folder: Path | str, tag: str = "") -> None:
        """Save hourly decisions and metrics, optionally tagged by scenario."""
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        stem = f"{self.label}{'_' + tag if tag else ''}"
        self.hourly.to_csv(folder / f"{stem}_hourly.csv", index_label="hour")
        pd.DataFrame([self.metrics()]).to_csv(folder / f"{stem}_metrics.csv", index=False)

    def __str__(self) -> str:
        return (
            f"cost: {self.total_cost:.2f} DKK | load: {self.total_load:.2f} kWh"
            f" | energy dual: {self.energy_dual:.3f} DKK/kWh"
        )


class FlexibleConsumerModel_Q2Quadratic(FlexibleConsumerModel):
    """Quadratic-disutility model without a minimum daily requirement."""

    def __init__(self, data: InputData, name: str = "q2c_quadratic", verbose: bool = False):
        super().__init__(data, name=name, verbose=verbose)
        self.label = name

    def _add_storage(self) -> None:
        """Extension point for the battery subclass."""

    def _storage_balance(self, t: int):
        """Battery discharge minus charge in the hourly power balance."""
        return 0.0

    def _add_daily_requirement(self) -> None:
        """Extension point for the daily minimum-energy subclass."""

    def build(self) -> "FlexibleConsumerModel_Q2Quadratic":
        """Build the common quadratic objective and hourly constraints."""
        d, m, T = self.data, self.m, self.T
        if d.reference_load is None or d.quadratic_disutility is None:
            raise ValueError("The quadratic model requires a reference load and cQ.")

        self.var["import"] = m.addVars(T, lb=0.0, name="import")
        self.var["export"] = m.addVars(T, lb=0.0, name="export")
        self.var["pv"] = m.addVars(T, lb=0.0, name="pv")
        self.var["load"] = m.addVars(T, lb=-GRB.INFINITY, name="load")
        imp, exp = self.var["import"], self.var["export"]
        pv, load = self.var["pv"], self.var["load"]

        self._add_storage()
        self.con["load_min"] = m.addConstrs((load[t] >= d.load_min_kWh for t in T), name="load_min")
        self.con["load_max"] = m.addConstrs((load[t] <= d.load_max_kWh for t in T), name="load_max")
        self.con["pv_max"] = m.addConstrs(
            (pv[t] <= float(d.pv_available[t]) for t in T), name="pv_max"
        )
        self.con["balance"] = m.addConstrs(
            (pv[t] + imp[t] + self._storage_balance(t) == load[t] + exp[t] for t in T),
            name="balance",
        )
        self._add_daily_requirement()

        import_price = d.energy_price + d.import_tariff
        export_price = d.energy_price - d.export_tariff
        m.setObjective(
            gp.quicksum(
                import_price[t] * imp[t] - export_price[t] * exp[t]
                + d.pv_marginal_cost * pv[t]
                + d.quadratic_disutility * (load[t] - float(d.reference_load[t])) ** 2
                for t in T
            ),
            GRB.MINIMIZE,
        )
        m.update()
        return self

    def _extract_results(self, status: str) -> Q3Results:
        """Extract the schedule, hourly duals, and cost components."""
        d, T = self.data, list(self.T)
        hourly = pd.DataFrame(index=pd.Index(T, name="hour"))
        hourly["price"] = d.energy_price
        hourly["import_price"] = d.energy_price + d.import_tariff
        hourly["export_price"] = d.energy_price - d.export_tariff
        hourly["pv_available"] = d.pv_available
        hourly["reference_load"] = d.reference_load
        for name, variables in self.var.items():
            hourly[name] = [variables[t].X for t in T]
        for name in ("balance", "load_min", "load_max", "pv_max"):
            hourly[f"dual_{name}"] = [self.con[name][t].Pi for t in T]

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
        has_min_energy = "min_energy" in self.con
        return Q3Results(
            question=d.question,
            label=self.label,
            hourly=hourly,
            total_cost=total_cost,
            net_utility=-total_cost,
            procurement_cost=procurement,
            pv_cost=pv_cost,
            disutility=disutility,
            total_load=float(hourly["load"].sum()),
            energy_dual=float(self.con["min_energy"].Pi) if has_min_energy else 0.0,
            has_min_energy=has_min_energy,
            with_battery="charge" in self.var,
        )


class FlexibleConsumerModel_Q3(FlexibleConsumerModel_Q2Quadratic):
    """Quadratic consumer with the minimum daily energy constraint."""

    def __init__(self, data: InputData, name: str = "q3", verbose: bool = False):
        super().__init__(data, name=name, verbose=verbose)

    def _add_daily_requirement(self) -> None:
        d = self.data
        if d.min_daily_energy_kWh is None:
            raise ValueError("The minimum daily energy parameter is missing.")
        self.con["min_energy"] = self.m.addConstr(
            gp.quicksum(self.var["load"][t] for t in self.T) >= d.min_daily_energy_kWh,
            name="min_energy",
        )


class FlexibleConsumerModel_Q3Battery(FlexibleConsumerModel_Q3):
    """Question 3 consumer with a battery and cyclic terminal state of charge."""

    def __init__(self, data: InputData, name: str = "q3_battery", verbose: bool = False):
        super().__init__(data, name=name, verbose=verbose)

    def _add_storage(self) -> None:
        d, m, T = self.data, self.m, self.T
        required = (
            d.battery_capacity_kWh,
            d.battery_max_charge_kW,
            d.battery_max_discharge_kW,
            d.battery_charging_efficiency,
            d.battery_discharging_efficiency,
            d.battery_initial_soc_kWh,
        )
        if any(value is None for value in required):
            raise ValueError("Battery parameters are missing; use the Q3_battery case.")

        charge = m.addVars(T, lb=0.0, ub=d.battery_max_charge_kW, name="charge")
        discharge = m.addVars(T, lb=0.0, ub=d.battery_max_discharge_kW, name="discharge")
        soc = m.addVars(T, lb=0.0, ub=d.battery_capacity_kWh, name="soc")
        self.var.update(charge=charge, discharge=discharge, soc=soc)
        self.con["soc_initial"] = m.addConstr(
            soc[0] == d.battery_initial_soc_kWh
            + d.battery_charging_efficiency * charge[0]
            - discharge[0] / d.battery_discharging_efficiency,
            name="soc_initial",
        )
        self.con["soc_dynamics"] = m.addConstrs(
            (
                soc[t] == soc[t - 1]
                + d.battery_charging_efficiency * charge[t]
                - discharge[t] / d.battery_discharging_efficiency
                for t in range(1, d.n_hours)
            ),
            name="soc_dynamics",
        )
        self.con["soc_terminal"] = m.addConstr(
            soc[d.n_hours - 1] == d.battery_initial_soc_kWh,
            name="soc_terminal",
        )

    def _storage_balance(self, t: int):
        return self.var["discharge"][t] - self.var["charge"][t]
