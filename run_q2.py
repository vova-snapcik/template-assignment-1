"""Reproduce Pavi's Question 2 experiments with ``python run_q2.py``.

The original notebook is the source of the experiments. Its code cells use
regular Python, so running them in order avoids a Jupyter runtime dependency
and keeps this command synchronized with the notebook.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "Assignment_01_final.ipynb"


def _display(*values: object) -> None:
    """Show notebook tables in a terminal without requiring IPython."""
    for value in values:
        print(value)


def run_notebook() -> None:
    """Execute all Q2 notebook code cells and save their figures and tables."""
    with NOTEBOOK.open(encoding="utf-8") as file:
        notebook = json.load(file)
    if notebook.get("nbformat") != 4:
        raise ValueError(f"Unsupported notebook format: {NOTEBOOK}")

    namespace: dict[str, object] = {
        "__name__": "__main__",
        "__file__": str(NOTEBOOK),
        "display": _display,
    }
    previous_directory = Path.cwd()
    executed = 0
    try:
        os.chdir(ROOT)
        for number, cell in enumerate(notebook["cells"], start=1):
            if cell.get("cell_type") != "code":
                continue
            source = cell.get("source", [])
            code = "".join(source) if isinstance(source, list) else source
            if not code.strip():
                continue
            try:
                exec(compile(code, f"{NOTEBOOK.name}:cell-{number}", "exec"), namespace)
            except Exception as error:
                raise RuntimeError(f"Question 2 notebook failed in cell {number}") from error
            executed += 1

        # These comparison tables were previously displayed but not saved.
        for variable, relative_path in (
            ("comparison_df", "results/Q2_quadratic/Q2_b_c_model_comparison.csv"),
            ("comparison_price", "results/Q2_temporal/Q2_e_price_scenarios.csv"),
        ):
            table = namespace.get(variable)
            if table is None:
                raise RuntimeError(f"Question 2 notebook did not create {variable}")
            destination = ROOT / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            table.to_csv(destination, index=False)
    finally:
        plt.close("all")
        os.chdir(previous_directory)

    print(f"Completed {executed} Question 2 code cells. Outputs: {ROOT / 'results'}")


if __name__ == "__main__":
    run_notebook()
