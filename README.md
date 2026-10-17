# 46750 - Assignment 1: Demand-Side Flexibility in Active Distribution Grids

Group code for **Assignment 1** of *46750 - Optimization in Modern Power Systems* (DTU).
Vlad's Question 1, Pavi's Question 2, and Samuel's Question 3 implementations are
combined here. Run commands from the repository root so that the shared `data/`
files and output paths are found correctly.

**Submitting your code.** Choose one of the two, and say in your report which one you chose:
attach your complete project code as a single `.zip` file to your submission in DTU Learn, or give
the link to your group's GitHub repository on the front page of your report. A linked repository must
be accessible to the graders (public, or private with the teaching team invited) and must not be
modified after the deadline - the last commit before the deadline is what is graded.

## 1. Setup

### 1.1 Python environment

Use one of the two options (both install the same packages).

**Option A - pip and venv**
```bash
python -m venv venv
source venv/bin/activate            # macOS / Linux
# venv\Scripts\activate.bat         # Windows cmd
# venv\Scripts\Activate.ps1         # Windows PowerShell
pip install -r requirements.txt
```

**Option B - conda**
```bash
conda env create -f environment.yaml
conda activate 46750-a1
```

### 1.2 Gurobi licence

The code uses [Gurobi](https://www.gurobi.com) through the `gurobipy` package and needs a valid
licence. If your installation does not already have one, request a free
[academic licence](https://www.gurobi.com/academia/academic-program-and-licenses/) with your DTU e-mail
and activate it with `grbgetkey <your-key>` (on the DTU network or VPN).

### 1.3 Run the assignment
```bash
python main.py --question Q1_caseA
python main.py --question Q1_caseB
python main.py --question Q2_linear
python main.py --question Q2_quadratic
python main.py --question Q3
python main.py --question Q3_battery
python run_q3.py
```
`main.py` solves a selected case and writes CSV/TXT results and PNG figures to
`results/<case>/`. `run_q3.py` additionally reproduces the Q3 comparison,
sensitivity analysis and battery figures under `results/Q3/`.
For Pavi's complete Q2 experiments, open `Assignment_01_final.ipynb` in
JupyterLab from the repository root and run its cells in order.

## 2. Repository structure

```
main.py                  Entry point for Q1, Q2 and Q3 base cases
run_q3.py                Q3 experiments and report figures
src/
  data_loader.py         load_question("Q1_caseA") -> InputData (all parameters, with units)
  model.py               Shared model/results code and Vlad's Q1 model
  model_q2.py            Q2 linear, quadratic and temporally coupled model classes
  model_q3.py            Q3 minimum-energy and battery model classes
  scenarios.py           Helpers that derive sensitivity scenarios from a base InputData
  plotting.py            Figures for inputs, optimal schedule, duals and scenario comparisons
data/
  appliance_params.json  SHARED catalogue: every PV system, flexible load and battery - see Section 4
  bus_params.json        SHARED grid connection: prices (both days) and tariffs
  params_Q1_caseA.json   One small file per case: composes a consumer from the catalogue
  params_Q1_caseB.json
  params_Q2_linear.json
  params_Q2_quadratic.json
  params_Q3.json
  params_Q3_battery.json
results/                 Generated outputs (git-ignored)
Assignment_01_final.ipynb  Question 2 experiments, tables and plots
requirements.txt, environment.yaml, LICENSE, .gitignore
```

### Question 2 models and experiments

`src/model_q2.py` contains `LinearDisutilityModel` for Q2(b),
`QuadraticDisutilityModel` for Q2(c), and `TemporallyCoupledDisutilityModel`
for the optional Q2(e). Each subclasses `FlexibleConsumerModel`, so other
scripts can use the same `build().solve()` interface. For example:

```python
from src.data_loader import load_question
from src.model_q2 import QuadraticDisutilityModel

data = load_question("Q2_quadratic")
results = QuadraticDisutilityModel(data).build().solve()
print(results)
```

Open `Assignment_01_final.ipynb` with the repository root as the working
directory to reproduce Pavi's Q2(b)--(e) experiments. The notebook imports
these model classes from `src/model_q2.py` and writes its tables and figures
under `results/Q2_linear/`, `results/Q2_quadratic/`, and `results/Q2_temporal/`.
Q2(e) is notebook-only because no dedicated input case is supplied.

## 3. How to use the code

**Run a base case or example scenarios**
```bash
python main.py --question Q1_caseA
python main.py --question Q1_caseA --scenarios
python main.py --question Q2_quadratic
python main.py --question Q3_battery
python main.py --show
```

**Use it from a notebook or your own script** (run from the repository root):
```python
from src.data_loader import load_question
from src.model import FlexibleConsumerModel_Q1
from src.plotting import plot_schedule, plot_duals
from src.scenarios import scale_prices

data = load_question("Q1_caseA")
print(data.summary())

results = FlexibleConsumerModel_Q1(data).build().solve()
print(results)                    # objective, daily totals, scalar duals
results.hourly                    # DataFrame: one row per hour with variables, prices and hourly duals
plot_schedule(results, data)

high_spread = scale_prices(data, factor=2.0, keep_mean=True)
results_hs = FlexibleConsumerModel_Q1(high_spread).build().solve()
```

`FlexibleConsumerModel` in `src/model.py` supplies common result extraction;
the runnable formulations are its question-specific subclasses. The Q3 script
uses its own `Q3Results` wrapper for additional cost and battery metrics.

**Conventions that make the primal and dual values come out for free**

* Store every variable family in `self.var[<name>]`. `solve()` returns the hourly values of each family
  as a column of `results.hourly`. gurobipy indexes names automatically - `m.addVars(T, name="p_import")`
  creates `p_import[0]` ... `p_import[23]`, and the same holds for `m.addConstrs(..., name=...)` - so
  per-hour names come for free. Families named `import`, `export`, `load`, `pv` make the standard plots
  of `src/plotting.py` work out of the box. With binary or integer variables (`vtype=GRB.BINARY`) the
  model becomes a MILP and dual values are no longer defined - `solve()` then skips them.

* Store every constraint family in `self.con[<name>]`. `solve()` returns the dual value (Gurobi attribute
  `Pi`) of every hourly constraint as a column `dual_<name>` of `results.hourly`, and of every single
  constraint in `results.duals`.
* Write the bounds you want a dual for as explicit constraints (`m.addConstr(...)`), not as variable bounds
  (`lb=`, `ub=`). Gurobi reports the sensitivity of a variable bound in the reduced cost (`RC`), not in `Pi`.
* No quadratic *constraint* is needed in this assignment: the quadratic disutility sits in the objective, and
  the duals of the (linear) constraints of a QP need nothing special. If you ever add one (`m.addQConstr(...)`),
  its dual is in the attribute `QCPi` and Gurobi only computes it when the parameter `QCPDual` is 1 -
  `model.py` sets it and reads the right attribute for you.
  Gurobi's sign convention is d(objective)/d(right-hand side): for a "<=" constraint in a minimization the value
  is non-positive; state the convention you use when you report multipliers.

## 4. Input data

All input data lives in `data/`: two **shared** files plus one small **case** file per
question. The shared files form a catalogue of every appliance used anywhere in the assignment;
each `params_<case>.json` composes the consumer of one case by picking appliances from the
catalogue by ID. All time series have 24 hourly values (hour 0 to 23).

**Units.** Every field name carries its unit. Fields ending in `_kW` are power ratings (kW);
fields ending in `_kWh_per_hour` (or `_KWh_per_hour` - same unit despite the capital K) are hourly
energy bounds (kWh consumed within one hour); fields ending in `_kWh` are energy amounts;
`_DKK_per_kWh` are prices/costs and `_DKK_per_kWh2` is the quadratic disutility coefficient.
**Capacity factors and ratios** (`hourly_profile_ratio`, `reference_load_capacity_factor`,
`initial_state_of_charge_ratio`, and the `_next_day` profiles) are **dimensionless fractions in
[0, 1] of the corresponding maximum** - multiply by it to get physical values. With 1-hour periods,
a power rating in kW and an energy amount in kWh/h are numerically interchangeable; the loader
does every conversion for you and exposes physical quantities:
`pv_available = max_power_kW x hourly_profile_ratio` (kWh/h),
`reference_load = max_load_KWh_per_hour x reference_load_capacity_factor` (kWh/h), and
`battery_initial_soc_kWh = storage_capacity_kWh x initial_state_of_charge_ratio` (kWh).

| Question in the assignment | Case | Appliances (from the catalogue) |
|---|---|---|
| Question 1 - hourly consumption decision (utility u, PV cost c_PV), case A: c_PV < u | `Q1_caseA` | `PV_01_A` + `FL_01` (a load with `consumption_utility_DKK_per_kWh`; no reference profile, no daily requirement) |
| Question 1, case B: a more expensive PV, c_PV > u | `Q1_caseB` | `PV_01_B` + `FL_01` (`PV_01_B` differs from `PV_01_A` only in `marginal_cost_DKK_per_kWh`) |
| Question 2 - linear disutility of deviating from a reference profile | `Q2_linear` | `PV_01_A` + `FL_02_L` (reference profile, `linear_disutility_DKK_per_kWh`; same hourly bounds as Question 1; no utility) |
| Question 2 - quadratic disutility | `Q2_quadratic` | `PV_01_A` + `FL_02_Q` (as `FL_02_L` with `quadratic_disutility_DKK_per_kWh2` instead) |
| Question 3 - minimum daily energy requirement | `Q3` | `PV_01_A` + `FL_03` (as `FL_02_Q` plus `min_total_energy_per_day_kWh`, the E_min of the daily requirement) |
| Question 3.(g) - the same consumer with a small battery | `Q3_battery` | `PV_01_A` + `FL_03` + `BAT_01` |

No data is shipped for the bonus question 2.(e) on purpose: choosing your own cost parameters (and
justifying them) is part of that question - start from the `Q2_quadratic` case and override in code.

`params_<case>.json` - the case file
: `consumers[]`: `consumer_id`, `connection_bus` (a `bus_id` of `bus_params.json`), `list_appliances`
  (IDs of the consumer's DERs, loads and storages in `appliance_params.json`). `hyperparameters` is
  unused in Assignment 1 (`null`).

`appliance_params.json` - the shared catalogue, one list per appliance type (`null` if none)
: **DERs**: `DER_id`, `DER_type` (`"PV"`), `max_power_kW` (peak power, kW), `marginal_cost_DKK_per_kWh` (cost of every kWh produced), `hourly_profile_ratio` (dimensionless fraction of `max_power_kW` available each hour; available energy in kWh/h = `max_power_kW` x ratio), `hourly_profile_ratio_next_day` (see *Next-day forecasts* below)
: **loads**: `load_id`, `load_type`, `max_load_KWh_per_hour` and `min_load_KWh_per_hour` (hourly consumption bounds, kWh/h), `consumption_utility_DKK_per_kWh` (value of every kWh consumed, Question 1), `linear_disutility_DKK_per_kWh` and `quadratic_disutility_DKK_per_kWh2` (Questions 2-3), `min_total_energy_per_day_kWh` (the E_min of Question 3), `reference_load_capacity_factor` (dimensionless fraction of `max_load_KWh_per_hour`; preferred consumption in kWh/h = max load x factor), `reference_hourly_profile_ratio_next_day` (see *Next-day forecasts*). Fields a load does not use are `null`. The hourly bounds are the same for every load: deviations from the reference are limited only by them.
: **storages**: `storage_id`, `storage_type` (`"battery"`), `storage_capacity_kWh`, `max_charging_power_kW`, `max_discharging_power_kW`, `charging_efficiency` and `discharging_efficiency` (fraction of the energy transferred that survives each conversion - a full round trip keeps η_ch·η_dis), `initial_state_of_charge_ratio` (fraction of `storage_capacity_kWh` in the battery at the start of the day). **No final state of charge is given on purpose**: how to treat the battery's state of charge at the end of the day (constraint or objective) is your modeling choice in Question 3.(g).
: **heat_pumps**: not used in Assignment 1 (`null`)

`bus_params.json` - grid and market conditions at the connection bus
: `bus_id`, `import_tariff_DKK_per_kWh`, `export_tariff_DKK_per_kWh`, `energy_price_DKK_per_kWh` (24 values), `energy_price_next_day_DKK_per_kWh` (see *Next-day forecasts*), `max_import_kW`, `max_export_kW` (`null` = no grid limit in Assignment 1)

**Next-day forecasts.** Three fields carry the forecast for the *following* day:
`energy_price_next_day_DKK_per_kWh` (in `bus_params.json`), `hourly_profile_ratio_next_day` (in the
DER entries) and `reference_hourly_profile_ratio_next_day` (in the load entries). They are **not
needed for the base models**: they are provided in case you want to explore the end-of-horizon
choice of Question 3.(g) with a look-ahead (for instance a rolling-horizon or a two-day experiment).
`load_question()` exposes them as `energy_price_next_day`, `pv_available_next_day` and
`reference_load_next_day`.

`load_question()` in `src/data_loader.py` shows exactly how each attribute is derived from these files.

**Modifying or adding data.** For sensitivity analyses, prefer deriving scenarios in code
(`src/scenarios.py`) over editing the JSON files - it keeps the base case intact and the experiment
reproducible. If you do add appliances or case files, follow the same structure (a new entry in the
catalogue, a new `params_<case>.json`) and document them here.

## 5. What is expected of your code

Your code is part of the submission (as a repository link or a `.zip`, see the top of this README).
The graders should be able to open it, follow this README, and reproduce every number and figure in
your report. In practice:

* keep the separation between data loading, model building, solving and plotting;
* document every function you add (a short docstring stating inputs, outputs and units is enough), and
  describe any new module or data file in this README;
* make each experiment of the report runnable with a single command (e.g. `python main.py --question ...`
  or one notebook cell), and save its outputs under `results/`;
* commit regularly and with meaningful messages - the git history is also a record of everyone's contribution.

## 6. Question 3 implementation

Question 3 is implemented in `src/model_q3.py` as subclasses of `FlexibleConsumerModel`:
`FlexibleConsumerModel_Q2Quadratic` is the unconstrained Question 2(c) benchmark,
`FlexibleConsumerModel_Q3` adds the minimum daily energy requirement, and
`FlexibleConsumerModel_Q3Battery` adds storage with a cyclic end-of-horizon state of charge.
The standard `main.py --question Q3` and `main.py --question Q3_battery` commands use these classes.
Run every Question 3 base case and sensitivity experiment with:

```bash
python run_q3.py
```

The command saves hourly schedules, summary tables, and report-ready figures under `results/Q3/`.
