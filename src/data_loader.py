"""Load the input data of one question folder (``data/question_xx/``) into a single object.

Usage
-----
>>> from src.data_loader import load_question
>>> data = load_question("question_1_caseA")
>>> data.energy_price          # numpy array of 24 hourly prices, DKK/kWh
>>> data.pv_available          # numpy array of 24 hourly PV availability, kWh/h
>>> data.summary()             # human-readable overview

The loader reads the five JSON files described in the README, checks that they are
consistent (24 hourly values, ratios within [0, 1], appliance IDs that exist) and exposes
the quantities needed by the optimisation models as attributes with explicit units.
The raw dictionaries are kept in ``data.raw`` in case you need a field that is not
exposed as an attribute.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

# Repository root = parent of the ``src`` folder. Works whatever the current working directory.
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"

REQUIRED_FILES = (
    "consumer_params.json",
    "appliance_params.json",
    "usage_preferences.json",
    "DER_production.json",
    "bus_params.json",
)


@dataclass
class InputData:
    """All parameters of one consumer for one question, with units in the attribute names."""

    question: str
    consumer_id: str
    hours: np.ndarray                     # 0 .. 23

    # Grid / market conditions (from bus_params.json)
    energy_price: np.ndarray              # DKK/kWh, one value per hour
    import_tariff: float                  # DKK/kWh charged on every kWh imported
    export_tariff: float                  # DKK/kWh charged on every kWh exported
    max_import_kW: float                  # not binding in Assignment 1 (very large)
    max_export_kW: float                  # not binding in Assignment 1 (very large)

    # PV system (from appliance_params.json + DER_production.json)
    pv_max_kW: float
    pv_profile: np.ndarray                # ratio of pv_max_kW available each hour, in [0, 1]
    pv_available: np.ndarray              # kWh/h = pv_max_kW * pv_profile
    pv_marginal_cost: float               # DKK per kWh of PV actually produced (0 if not given)

    # Flexible load (from appliance_params.json + usage_preferences.json)
    load_max_kWh: float                   # maximum hourly consumption, kWh/h
    load_min_kWh: float                   # minimum hourly consumption, kWh/h
    consumption_utility: float | None     # DKK per kWh consumed (value of consumption; None if not given)
    min_daily_energy_kWh: float | None    # minimum energy to consume over the day (None if not required)
    max_daily_energy_kWh: float | None
    reference_load: np.ndarray | None     # preferred hourly consumption, kWh/h (None if not given)
    max_hourly_deviation_kWh: float | None
    max_daily_deviation_kWh: float | None  # the epsilon of the epsilon-constraint model
    linear_disutility: float | None       # DKK per kWh of absolute deviation from reference_load
    quadratic_disutility: float | None    # DKK per kWh^2 of deviation from reference_load

    # Everything that was read, unprocessed
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    # ------------------------------------------------------------------ helpers
    @property
    def n_hours(self) -> int:
        return len(self.hours)

    def summary(self) -> str:
        """Compact textual overview of the dataset."""
        lines = [
            f"Question folder      : {self.question}",
            f"Consumer             : {self.consumer_id}",
            f"Energy price         : mean {self.energy_price.mean():.2f}, min {self.energy_price.min():.2f}, "
            f"max {self.energy_price.max():.2f} DKK/kWh",
            f"Import/export tariff : {self.import_tariff:.2f} / {self.export_tariff:.2f} DKK/kWh",
            f"PV                   : {self.pv_max_kW:.1f} kW peak, {self.pv_available.sum():.1f} kWh available/day, marginal cost {self.pv_marginal_cost:.2f} DKK/kWh",
            f"Load bounds          : {self.load_min_kWh:.1f} - {self.load_max_kWh:.1f} kWh/h",
            f"Consumption utility  : {self.consumption_utility}",
            f"Min daily energy     : {self.min_daily_energy_kWh}",
            f"Reference profile    : {'yes (%.1f kWh/day)' % self.reference_load.sum() if self.reference_load is not None else 'no'}",
            f"Max hourly deviation : {self.max_hourly_deviation_kWh}",
            f"Max daily deviation  : {self.max_daily_deviation_kWh}",
            f"Disutility lin/quad  : {self.linear_disutility} / {self.quadratic_disutility}",
            f"Storage              : {'yes' if self.raw['appliance_params'].get('storage') else 'no'}",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------- loading
def _read_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _first_with(items: list[dict], key: str, value: str, what: str) -> dict:
    """Return the first dict in ``items`` whose ``key`` equals ``value``."""
    for item in items:
        if item.get(key) == value:
            return item
    raise KeyError(f"No {what} with {key} == {value!r}")


def _as_array(values, name: str, n_hours: int = 24) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.shape != (n_hours,):
        raise ValueError(f"{name} must have {n_hours} hourly values, got shape {arr.shape}")
    return arr


def load_question(question: str, data_dir: Path | str = DATA_DIR, consumer_index: int = 0) -> InputData:
    """Read ``data/<question>/`` and return an :class:`InputData` for one consumer.

    Parameters
    ----------
    question : str
        Name of the folder under ``data/``, e.g. ``"question_1_caseA"``.
    data_dir : Path, optional
        Root data directory (defaults to ``<repo>/data``).
    consumer_index : int, optional
        Which consumer to load if the files describe several (Assignment 1 has one).
    """
    folder = Path(data_dir) / question
    if not folder.is_dir():
        available = sorted(p.name for p in Path(data_dir).iterdir() if p.is_dir())
        raise FileNotFoundError(f"Unknown question folder {folder}. Available: {available}")

    raw = {name.removesuffix(".json"): _read_json(folder / name) for name in REQUIRED_FILES}

    consumer = raw["consumer_params"][consumer_index]
    cid = consumer["consumer_id"]
    appliance_ids = list(consumer["list_appliances"])

    # --- bus / market
    bus = _first_with(raw["bus_params"], "bus_id", consumer["connection_bus"], "bus")
    price = _as_array(bus["energy_price_DKK_per_kWh"], "energy_price_DKK_per_kWh")
    if (price < 0).any():
        raise ValueError("Energy prices are assumed non-negative in Assignment 1")

    # --- PV (the consumer's DER of type PV)
    ders = raw["appliance_params"].get("DER") or []
    pv = next(d for d in ders if d["DER_id"] in appliance_ids and d["DER_type"] == "PV")
    production = _first_with(raw["DER_production"], "DER_id", pv["DER_id"], "DER production profile")
    pv_profile = _as_array(production["hourly_profile_ratio"], "PV hourly_profile_ratio")
    if (pv_profile < 0).any() or (pv_profile > 1).any():
        raise ValueError("PV hourly_profile_ratio must lie in [0, 1]")

    # --- flexible load and its usage preferences
    loads = raw["appliance_params"].get("load") or []
    load = next(l for l in loads if l["load_id"] in appliance_ids)
    prefs = _first_with(raw["usage_preferences"], "consumer_id", cid, "usage preference")
    load_pref = _first_with(prefs["load_preferences"], "load_id", load["load_id"], "load preference")

    load_max = float(load["max_load_kWh_per_hour"])
    ref_ratio = load_pref.get("reference_hourly_profile_ratio")
    reference_load = None if ref_ratio is None else load_max * _as_array(ref_ratio, "reference_hourly_profile_ratio")

    def opt_float(key: str) -> float | None:
        v = load_pref.get(key)
        return None if v is None else float(v)

    return InputData(
        question=question,
        consumer_id=cid,
        hours=np.arange(len(price)),
        energy_price=price,
        import_tariff=float(bus["import_tariff_DKK_per_kWh"]),
        export_tariff=float(bus["export_tariff_DKK_per_kWh"]),
        max_import_kW=float(bus["max_import_kW"]),
        max_export_kW=float(bus["max_export_kW"]),
        pv_max_kW=float(pv["max_power_kW"]),
        pv_profile=pv_profile,
        pv_available=float(pv["max_power_kW"]) * pv_profile,
        pv_marginal_cost=float(pv.get("marginal_cost_DKK_per_kWh") or 0.0),
        load_max_kWh=load_max,
        load_min_kWh=load_max * float(load.get("min_load_ratio", 0.0)),
        consumption_utility=opt_float("consumption_utility_DKK_per_kWh"),
        min_daily_energy_kWh=opt_float("min_total_energy_per_day_kWh"),
        max_daily_energy_kWh=opt_float("max_total_energy_per_day_kWh"),
        reference_load=reference_load,
        max_hourly_deviation_kWh=opt_float("max_hourly_deviation_kWh"),
        max_daily_deviation_kWh=opt_float("max_daily_deviation_kWh"),
        linear_disutility=opt_float("linear_disutility_DKK_per_kWh"),
        quadratic_disutility=opt_float("quadratic_disutility_DKK_per_kWh2"),
        raw=raw,
    )


def list_questions(data_dir: Path | str = DATA_DIR) -> list[str]:
    """Names of all question folders available under ``data/``."""
    return sorted(p.name for p in Path(data_dir).iterdir() if p.is_dir())


if __name__ == "__main__":  # quick manual check:  python -m src.data_loader
    for q in list_questions():
        print(load_question(q).summary(), end="\n\n")
