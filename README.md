# 46750 - Assignment 1: Demand-Side Flexibility in Active Distribution Grids

Starter repository for **Group Assignment 1** of *46750 - Optimization in Modern Power Systems* (DTU).
It contains the input data for every question, a small and working Python code base to build on, and
the instructions below. The structure is a suggestion: adapt it to your needs, but keep it documented
(update this README) so that your code stays reproducible and easy to grade.

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

The code uses [Gurobi](https://www.gurobi.com) through the `gurobipy` package. The package ships with a
restricted licence that is large enough for this assignment (models up to 2000 variables/constraints), so
`python main.py` works out of the box. For unrestricted use, request a free
[academic licence](https://www.gurobi.com/academia/academic-program-and-licenses/) with your DTU e-mail
and activate it with `grbgetkey <your-key>` (on the DTU network or VPN).

### 1.3 Check that everything works
```bash
python main.py
```
This loads `data/question_1_caseA`, prints a summary of the input data and saves the input figure to
`results/question_1_caseA/`. Until you complete the model (see Section 3) it prints
`[skipped] The model has no constraints ...` and stops there - that is expected.

## 2. Repository structure

```
main.py                  Entry point: load data -> build model -> solve -> save results and figures
src/
  data_loader.py         load_question("question_1_caseA") -> InputData (all parameters, with units)
  model.py               FlexibleConsumerModel: build() / solve() -> Results (primal + dual values)
  scenarios.py           Helpers that derive sensitivity scenarios from a base InputData
  plotting.py            Figures for inputs, optimal schedule, duals and scenario comparisons
data/
  question_1_caseA/      One folder per question (two cases for Question 1) - see Section 4
  question_1_caseB/
  question_2/
  question_3/
results/                 Written by main.py (git-ignored)
requirements.txt, environment.yaml, LICENSE, .gitignore
```

The four modules mirror the workflow you are asked to implement and document: *data loading*,
*model building*, *solving and extracting results*, *plotting*. Keep them separate as your code grows -
for example one model class per question in `src/model.py` (or one file per question), and one function per
experiment in `main.py`.

## 3. How to use the code

**Run everything for one question**
```bash
python main.py --question question_1_caseA          # base case
python main.py --question question_1_caseA --scenarios   # + example sensitivity scenarios
python main.py --show                               # open the figures in a window
```

**Use it from a notebook or your own script** (run from the repository root):
```python
from src.data_loader import load_question
from src.model import FlexibleConsumerModel
from src.plotting import plot_schedule, plot_duals
from src.scenarios import scale_prices

data = load_question("question_1_caseA")
print(data.summary())

results = FlexibleConsumerModel(data).build().solve()
print(results)                    # objective, daily totals, scalar duals
results.hourly                    # DataFrame: one row per hour with variables, prices and hourly duals
plot_schedule(results, data)

high_spread = scale_prices(data, factor=2.0, keep_mean=True)
results_hs = FlexibleConsumerModel(high_spread).build().solve()
```

**What you need to implement.** `FlexibleConsumerModel.build()` in `src/model.py` declares the decision
variables but leaves the objective and constraints as `TODO`, with the gurobipy pattern shown in comments.
Complete it with your formulation from Question 1 (utility and PV cost are in `data.consumption_utility` and `data.pv_marginal_cost`), then extend or subclass it for the following questions.
Everything downstream (solving, extraction of primal and dual values, saving, plotting) already works.

**Two conventions that make the dual variables come out for free**

* Store every constraint family in `self.con[<name>]`. `solve()` returns the dual value (Gurobi attribute
  `Pi`) of every hourly constraint as a column `dual_<name>` of `results.hourly`, and of every single
  constraint in `results.duals`.
* Write the bounds you want a dual for as explicit constraints (`m.addConstr(...)`), not as variable bounds
  (`lb=`, `ub=`). Gurobi reports the sensitivity of a variable bound in the reduced cost (`RC`), not in `Pi`.
* A quadratic constraint (`m.addQConstr(...)`, Question 3.(c)) has its dual in the attribute `QCPi`, and Gurobi
  only computes it when the parameter `QCPDual` is 1 - `model.py` sets it and reads the right attribute for you.
  Gurobi's sign convention is d(objective)/d(right-hand side): for a "<=" constraint in a minimization the value
  is non-positive; state the convention you use when you report multipliers.

## 4. Input data

Each `data/question_xx/` folder contains the same five JSON files. All time series have 24 hourly values
(hour 0 to 23), all ratios are dimensionless fractions of the corresponding maximum, and every field name
carries its unit.

| Question in the assignment | Data folder | What differs |
|---|---|---|
| Question 1 - hourly consumption decision (utility u, PV cost c_PV), case A: c_PV < u | `question_1_caseA` | `consumption_utility_DKK_per_kWh`, PV `marginal_cost_DKK_per_kWh` = 0.3; no reference profile, no daily requirement |
| Question 1, case B: a more expensive PV | `question_1_caseB` | as case A with PV `marginal_cost_DKK_per_kWh` = 0.9 |
| Question 2 - separable disutility of deviating from a reference profile (linear and quadratic) | `question_2` | `reference_hourly_profile_ratio`, `max_hourly_deviation_kWh`, `linear_disutility_DKK_per_kWh`, `quadratic_disutility_DKK_per_kWh2`; no utility |
| Question 3 - intertemporal constraints (daily comfort budgets; minimum daily energy in the bonus question) | `question_3` | utility and PV cost of case A, reference profile and `max_hourly_deviation_kWh`, `max_daily_deviation_kWh` (the budget ε), `min_total_energy_per_day_kWh` (bonus question only) |

`consumer_params.json` - list of consumers
: `consumer_id`, `connection_bus`, `list_appliances` (IDs of the consumer's DERs, loads and storages)

`appliance_params.json` - technical characteristics, one list per appliance type (`null` if none)
: **DER**: `DER_id`, `DER_type` (`"PV"`), `max_power_kW`, `marginal_cost_DKK_per_kWh` (cost of every kWh produced), `min_power_ratio`, `max_ramp_rate_up_ratio`, `max_ramp_rate_down_ratio`
: **load**: `load_id`, `load_type`, `max_load_kWh_per_hour`, `min_load_ratio` (minimum hourly load as a fraction of the maximum), `max_ramp_rate_up_ratio`, `max_ramp_rate_down_ratio`, `min_on_time_h`, `min_off_time_h`
: **storage**, **heat_pump**: not used in Assignment 1 (`null`)

`usage_preferences.json` - the consumer's flexibility preferences
: `load_preferences[]`: `load_id`, `consumption_utility_DKK_per_kWh` (value of every kWh consumed), `min_total_energy_per_day_kWh`, `max_total_energy_per_day_kWh`, `reference_hourly_profile_ratio` (preferred consumption each hour as a fraction of `max_load_kWh_per_hour`), `max_hourly_deviation_kWh`, `max_daily_deviation_kWh` (the budget ε of Question 3; in kWh for the linear discomfort, kWh² for the quadratic one), `linear_disutility_DKK_per_kWh`, `quadratic_disutility_DKK_per_kWh2`. Fields that do not apply to a question are `null`.
: `storage_preferences`, `grid_preferences`, `DER_preferences`, `heat_pump_preferences`: unused in Assignment 1 (`null`)

`DER_production.json` - availability profiles
: `consumer_id`, `DER_id`, `DER_type`, `hourly_profile_ratio` (available production as a fraction of `max_power_kW`)

`bus_params.json` - grid and market conditions at the connection bus
: `bus_id`, `import_tariff_DKK_per_kWh`, `export_tariff_DKK_per_kWh`, `energy_price_DKK_per_kWh` (24 values), `max_import_kW`, `max_export_kW` (large, i.e. not binding in Assignment 1)

The ramp-rate and minimum on/off-time fields are not needed in Assignment 1 and can be ignored.
`load_question()` in `src/data_loader.py` shows exactly how each attribute is derived from these files.

**Modifying or adding data.** For sensitivity analyses, prefer deriving scenarios in code
(`src/scenarios.py`) over editing the JSON files - it keeps the base case intact and the experiment
reproducible. If you do add data folders or files, follow the same structure and document them here.

## 5. What is expected of your code

Your repository is part of the submission. The graders should be able to clone it, follow this README,
and reproduce every number and figure in your report. In practice:

* keep the separation between data loading, model building, solving and plotting;
* document every function you add (a short docstring stating inputs, outputs and units is enough), and
  describe any new module or data file in this README;
* make each experiment of the report runnable with a single command (e.g. `python main.py --question ...`
  or one notebook cell), and save its outputs under `results/`;
* commit regularly and with meaningful messages - the git history is also a record of everyone's contribution.
