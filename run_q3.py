"""Reproduce all numerical results and figures for Assignment 1, Question 3.

Run from the project folder with::

    python run_q3.py

Outputs and report-ready figures are written to ``results/Q3``.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.data_loader import InputData, load_question
from src.model_q3 import Q3Model, Q3Results
from src.scenarios import scale_prices


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results" / "Q3"
REPORT_FIGURES = RESULTS / "figures"


def solve_case(
    data: InputData,
    label: str,
    *,
    enforce_min_energy: bool,
    with_battery: bool = False,
) -> Q3Results:
    """Build, solve, and save one reproducible Question 3 case."""
    result = Q3Model(
        data,
        enforce_min_energy=enforce_min_energy,
        with_battery=with_battery,
        label=label,
    ).build().solve()
    result.save(RESULTS)
    return result


def save_figure(fig: plt.Figure, name: str) -> None:
    """Save a figure both with the numerical outputs and with the LaTeX report."""
    for folder in (RESULTS, REPORT_FIGURES):
        folder.mkdir(parents=True, exist_ok=True)
        fig.savefig(folder / name, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_base_comparison(unconstrained: Q3Results, constrained: Q3Results) -> None:
    """Plot the Q2(c) benchmark and the minimum-energy schedule against the reference."""
    h = unconstrained.hourly.index
    fig, ax = plt.subplots(figsize=(9.5, 4.2))
    ax.step(h, unconstrained.hourly["reference_load"], where="mid", color="black", ls=":", label="Reference")
    ax.step(h, unconstrained.hourly["load"], where="mid", lw=1.8, label="Unconstrained Q2(c)")
    ax.step(h, constrained.hourly["load"], where="mid", lw=1.8, label="Q3 minimum-energy")
    ax.set(xlabel="Hour", ylabel="Load [kWh/h]", xticks=np.arange(0, 24, 2))
    ax.grid(alpha=0.2)
    ax2 = ax.twinx()
    ax2.step(h, constrained.hourly["import_price"], where="mid", color="C3", alpha=0.55, label="Import price")
    ax2.set_ylabel("Import price [DKK/kWh]", color="C3")
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, ncol=2, fontsize=8, loc="upper left")
    save_figure(fig, "q3_base_comparison.png")


def run_q3f(base: InputData) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Sweep the minimum energy and quadratic-disutility coefficient one at a time."""
    emin_values = [0.0, 20.0, 30.0, 32.34, 40.0, 55.0, 80.0, 120.0, 140.0]
    emin_rows = []
    for value in emin_values:
        data = replace(base, min_daily_energy_kWh=value)
        result = solve_case(data, f"emin_{value:g}", enforce_min_energy=True)
        row = result.metrics()
        row["Emin_kWh"] = value
        emin_rows.append(row)
    emin_table = pd.DataFrame(emin_rows)
    emin_table.to_csv(RESULTS / "q3f_emin_sensitivity.csv", index=False)

    cq_values = [0.10, 0.25, 0.50, 1.00, 2.00, 5.00]
    cq_rows = []
    for value in cq_values:
        data = replace(base, quadratic_disutility=value)
        result = solve_case(data, f"cq_{value:g}", enforce_min_energy=True)
        row = result.metrics()
        row["cQ_DKK_per_kWh2"] = value
        cq_rows.append(row)
    cq_table = pd.DataFrame(cq_rows)
    cq_table.to_csv(RESULTS / "q3f_cq_sensitivity.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    axes[0].plot(emin_table["Emin_kWh"], emin_table["total_cost_DKK"], "o-", label="Total cost")
    axes[0].set(xlabel="$E^{min}$ [kWh]", ylabel="Total cost [DKK]")
    axes[0].grid(alpha=0.25)
    ax0b = axes[0].twinx()
    ax0b.plot(emin_table["Emin_kWh"], emin_table["energy_dual_DKK_per_kWh"], "s--", color="C3", label="Energy dual")
    ax0b.set_ylabel("Energy dual [DKK/kWh]", color="C3")

    axes[1].semilogx(cq_table["cQ_DKK_per_kWh2"], cq_table["above_reference_kWh"], "o-", label="Above reference")
    axes[1].semilogx(cq_table["cQ_DKK_per_kWh2"], cq_table["absolute_deviation_kWh"], "s--", label="Absolute deviation")
    axes[1].set(xlabel="$c^Q$ [DKK/kWh$^2$]", ylabel="Deviation [kWh]")
    axes[1].grid(alpha=0.25)
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    save_figure(fig, "q3f_sensitivity.png")
    return emin_table, cq_table


def plot_battery_comparison(no_battery: Q3Results, battery: Q3Results) -> None:
    """Show the load, battery operation, state of charge, and grid exchange."""
    h = battery.hourly.index
    fig, axes = plt.subplots(3, 1, figsize=(9.5, 8.0), sharex=True)
    axes[0].step(h, battery.hourly["reference_load"], where="mid", color="black", ls=":", label="Reference")
    axes[0].step(h, no_battery.hourly["load"], where="mid", label="Without battery")
    axes[0].step(h, battery.hourly["load"], where="mid", label="With battery")
    axes[0].set_ylabel("Load [kWh/h]")
    axes[0].legend(ncol=3, fontsize=8)

    axes[1].bar(h - 0.18, battery.hourly["charge"], width=0.36, label="Charge")
    axes[1].bar(h + 0.18, -battery.hourly["discharge"], width=0.36, label="Discharge")
    ax_soc = axes[1].twinx()
    ax_soc.plot(h, battery.hourly["soc"], "k.-", label="State of charge")
    axes[1].set_ylabel("Power [kW]")
    ax_soc.set_ylabel("SoC [kWh]")
    lines, labels = axes[1].get_legend_handles_labels()
    lines2, labels2 = ax_soc.get_legend_handles_labels()
    axes[1].legend(lines + lines2, labels + labels2, ncol=3, fontsize=8, loc="upper left")

    axes[2].step(h, no_battery.hourly["import"] - no_battery.hourly["export"], where="mid", label="Net import without battery")
    axes[2].step(h, battery.hourly["import"] - battery.hourly["export"], where="mid", label="Net import with battery")
    axes[2].axhline(0.0, color="black", lw=0.7)
    axes[2].set(xlabel="Hour", ylabel="Net import [kWh/h]", xticks=np.arange(0, 24, 2))
    axes[2].legend(fontsize=8)
    for ax in axes:
        ax.grid(alpha=0.2)
    fig.tight_layout()
    save_figure(fig, "q3g_battery_comparison.png")


def run_q3g_sensitivity(base_battery: InputData) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Sweep price variability and battery capacity and calculate storage value."""
    spread_values = [0.0, 0.5, 1.0, 1.5, 2.0]
    spread_rows = []
    for factor in spread_values:
        data = scale_prices(base_battery, factor=factor, keep_mean=True)
        no_battery = solve_case(data, f"spread_{factor:g}_no_battery", enforce_min_energy=True)
        battery = solve_case(data, f"spread_{factor:g}_battery", enforce_min_energy=True, with_battery=True)
        spread_rows.append(
            {
                "price_spread_factor": factor,
                "price_range_DKK_per_kWh": float(data.energy_price.max() - data.energy_price.min()),
                "cost_without_battery_DKK": no_battery.total_cost,
                "cost_with_battery_DKK": battery.total_cost,
                "battery_value_DKK": no_battery.total_cost - battery.total_cost,
                "battery_cycles_equivalent": float(battery.hourly["discharge"].sum() / data.battery_capacity_kWh),
            }
        )
    spread_table = pd.DataFrame(spread_rows)
    spread_table.to_csv(RESULTS / "q3g_price_spread_sensitivity.csv", index=False)

    capacity_values = [0.0, 2.0, 4.0, 6.0, 8.0, 12.0]
    no_battery_base = solve_case(base_battery, "capacity_reference_no_battery", enforce_min_energy=True)
    capacity_rows = []
    base_ratio = base_battery.battery_initial_soc_kWh / base_battery.battery_capacity_kWh
    for capacity in capacity_values:
        data = replace(
            base_battery,
            battery_capacity_kWh=capacity,
            battery_initial_soc_kWh=base_ratio * capacity,
        )
        battery = solve_case(data, f"capacity_{capacity:g}", enforce_min_energy=True, with_battery=True)
        capacity_rows.append(
            {
                "battery_capacity_kWh": capacity,
                "max_charge_power_kW": data.battery_max_charge_kW,
                "max_discharge_power_kW": data.battery_max_discharge_kW,
                "cost_with_battery_DKK": battery.total_cost,
                "battery_value_DKK": no_battery_base.total_cost - battery.total_cost,
                "charged_energy_kWh": float(battery.hourly["charge"].sum()),
                "discharged_energy_kWh": float(battery.hourly["discharge"].sum()),
            }
        )
    capacity_table = pd.DataFrame(capacity_rows)
    capacity_table.to_csv(RESULTS / "q3g_capacity_sensitivity.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.6))
    axes[0].plot(spread_table["price_spread_factor"], spread_table["battery_value_DKK"], "o-")
    axes[0].set(xlabel="Price-spread factor", ylabel="Battery value [DKK/day]")
    axes[0].grid(alpha=0.25)
    axes[1].plot(capacity_table["battery_capacity_kWh"], capacity_table["battery_value_DKK"], "o-", color="C2")
    axes[1].set(xlabel="Battery capacity [kWh]", ylabel="Battery value [DKK/day]")
    axes[1].grid(alpha=0.25)
    fig.tight_layout()
    save_figure(fig, "q3g_battery_value_sensitivity.png")
    return spread_table, capacity_table


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    REPORT_FIGURES.mkdir(parents=True, exist_ok=True)

    base = load_question("Q3")
    unconstrained = solve_case(base, "q2c_unconstrained", enforce_min_energy=False)
    constrained = solve_case(base, "q3_base", enforce_min_energy=True)
    pd.DataFrame([unconstrained.metrics(), constrained.metrics()]).to_csv(
        RESULTS / "q3e_base_comparison.csv", index=False
    )
    plot_base_comparison(unconstrained, constrained)
    emin_table, cq_table = run_q3f(base)

    battery_data = load_question("Q3_battery")
    no_battery = solve_case(battery_data, "q3_base_no_battery", enforce_min_energy=True)
    battery = solve_case(battery_data, "q3_base_battery", enforce_min_energy=True, with_battery=True)
    battery_value = no_battery.total_cost - battery.total_cost
    base_battery_table = pd.DataFrame([no_battery.metrics(), battery.metrics()])
    base_battery_table["battery_value_DKK"] = [0.0, battery_value]
    base_battery_table.to_csv(RESULTS / "q3g_base_comparison.csv", index=False)
    plot_battery_comparison(no_battery, battery)
    spread_table, capacity_table = run_q3g_sensitivity(battery_data)

    print("\nBase comparison")
    print(pd.DataFrame([unconstrained.metrics(), constrained.metrics()]).to_string(index=False))
    print("\nBattery comparison")
    print(base_battery_table.to_string(index=False))
    print("\nEmin sensitivity")
    print(emin_table[["Emin_kWh", "total_load_kWh", "total_cost_DKK", "energy_dual_DKK_per_kWh"]].to_string(index=False))
    print("\ncQ sensitivity")
    print(cq_table[["cQ_DKK_per_kWh2", "total_cost_DKK", "above_reference_kWh", "absolute_deviation_kWh"]].to_string(index=False))
    print("\nBattery value: price spread")
    print(spread_table.to_string(index=False))
    print("\nBattery value: capacity")
    print(capacity_table.to_string(index=False))
    print(f"\nOutputs written to {RESULTS}")
    print(f"Report figures written to {REPORT_FIGURES}")


if __name__ == "__main__":
    main()
