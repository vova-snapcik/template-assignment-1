"""Reusable Question 2 consumer models extracted from Pavi's notebook.

The notebook contains the experiments; these classes keep the optimization
formulations importable by the rest of the group project.
"""
from __future__ import annotations

import gurobipy as gp
from gurobipy import GRB

from .model import FlexibleConsumerModel


class LinearDisutilityModel(FlexibleConsumerModel):
    """Question 2(b): linear absolute-deviation disutility."""

    def __init__(self, data, cL=None, name="Q2_linear", verbose=False):

        super().__init__(
            data,
            name=name,
            verbose=verbose
        )

        if cL is None:
            cL = data.linear_disutility

        self.cL = float(cL)

        if self.cL <= 0:
            raise ValueError("cL must be positive.")

        if data.reference_load is None:
            raise ValueError(
                "Reference load is required for Q2(b)."
            )

    def build(self):

        d = self.data
        m = self.m
        T = self.T

        # ----------------------------------------------------
        # Decision variables
        # ----------------------------------------------------

        L = m.addVars(
            T,
            lb=-GRB.INFINITY,
            vtype=GRB.CONTINUOUS,
            name="load"
        )

        PV = m.addVars(
            T,
            lb=-GRB.INFINITY,
            vtype=GRB.CONTINUOUS,
            name="pv"
        )

        P_imp = m.addVars(
            T,
            lb=-GRB.INFINITY,
            vtype=GRB.CONTINUOUS,
            name="import"
        )

        P_exp = m.addVars(
            T,
            lb=-GRB.INFINITY,
            vtype=GRB.CONTINUOUS,
            name="export"
        )

        x = m.addVars(
            T,
            lb=0,
            vtype=GRB.CONTINUOUS,
            name="deviation"
        )

        # Store variables so the repository can retrieve them
        self.var["load"] = L
        self.var["pv"] = PV
        self.var["import"] = P_imp
        self.var["export"] = P_exp
        self.var["deviation"] = x

        # ----------------------------------------------------
        # Effective prices
        # ----------------------------------------------------

        p_imp = (
            d.energy_price
            + d.import_tariff
        )

        p_exp = (
            d.energy_price
            - d.export_tariff
        )

        # ----------------------------------------------------
        # Objective
        #
        # max sum [
        #   -cL*x
        #   -cPV*PV
        #   -p_imp*P_imp
        #   +p_exp*P_exp
        # ]
        # ----------------------------------------------------

        m.setObjective(
            gp.quicksum(
                -self.cL * x[t]
                - d.pv_marginal_cost * PV[t]
                - p_imp[t] * P_imp[t]
                + p_exp[t] * P_exp[t]
                for t in T
            ),
            GRB.MAXIMIZE
        )

        # ----------------------------------------------------
        # (2b-2) Energy balance
        # ----------------------------------------------------

        self.con["balance"] = m.addConstrs(
            PV[t]
            - L[t]
            - P_exp[t]
            + P_imp[t]
            == 0
            for t in T
        )

        # ----------------------------------------------------
        # (2b-3) Load bounds
        # ----------------------------------------------------

        self.con["load_min"] = m.addConstrs(
            L[t] >= d.load_min_kWh
            for t in T
        )

        self.con["load_max"] = m.addConstrs(
            L[t] <= d.load_max_kWh
            for t in T
        )

        # ----------------------------------------------------
        # (2b-4) PV bounds
        # ----------------------------------------------------

        self.con["pv_min"] = m.addConstrs(
            PV[t] >= 0
            for t in T
        )

        self.con["pv_max"] = m.addConstrs(
            PV[t] <= d.pv_available[t]
            for t in T
        )

        # ----------------------------------------------------
        # (2b-5) Import >= 0
        # ----------------------------------------------------

        self.con["import_min"] = m.addConstrs(
            P_imp[t] >= 0
            for t in T
        )

        # ----------------------------------------------------
        # (2b-6) Export >= 0
        # ----------------------------------------------------

        self.con["export_min"] = m.addConstrs(
            P_exp[t] >= 0
            for t in T
        )

        # ----------------------------------------------------
        # (2b-7)
        #
        # x >= L - L_ref
        # ----------------------------------------------------

        self.con["dev_pos"] = m.addConstrs(
            x[t]
            >= L[t] - d.reference_load[t]
            for t in T
        )

        # ----------------------------------------------------
        # (2b-8)
        #
        # x >= L_ref - L
        # ----------------------------------------------------

        self.con["dev_neg"] = m.addConstrs(
            x[t]
            >= d.reference_load[t] - L[t]
            for t in T
        )

        # ----------------------------------------------------
        # (2b-9)
        #
        # x >= 0
        # ----------------------------------------------------

        self.con["deviation_nonnegative"] = m.addConstrs(
            x[t] >= 0
            for t in T
        )

        m.update()

        return self


class QuadraticDisutilityModel(FlexibleConsumerModel):
    """
    Q2(c): Flexible consumer with quadratic disutility.

    Energy quantities are in kWh.
    Energy prices and PV marginal cost are in DKK/kWh.
    The quadratic disutility coefficient cQ is in DKK/kWh^2.
    """

    def __init__(
        self,
        data,
        cQ=None,
        name="Q2_quadratic",
        verbose=False
    ):
        super().__init__(
            data,
            name=name,
            verbose=verbose
        )

        if cQ is None:
            cQ = data.quadratic_disutility

        self.cQ = float(cQ)

        if self.cQ <= 0:
            raise ValueError(
                "cQ must be positive."
            )

        if data.reference_load is None:
            raise ValueError(
                "Reference load is required for Q2(c)."
            )

    def build(self):
        d = self.data
        m = self.m
        T = self.T

        # -------------------------------------------------
        # Decision variables
        # -------------------------------------------------

        L = m.addVars(
            T,
            lb=-GRB.INFINITY,
            vtype=GRB.CONTINUOUS,
            name="load"
        )

        PV = m.addVars(
            T,
            lb=-GRB.INFINITY,
            vtype=GRB.CONTINUOUS,
            name="pv"
        )

        P_imp = m.addVars(
            T,
            lb=-GRB.INFINITY,
            vtype=GRB.CONTINUOUS,
            name="import"
        )

        P_exp = m.addVars(
            T,
            lb=-GRB.INFINITY,
            vtype=GRB.CONTINUOUS,
            name="export"
        )

        self.var["load"] = L
        self.var["pv"] = PV
        self.var["import"] = P_imp
        self.var["export"] = P_exp

        # -------------------------------------------------
        # Effective import/export prices
        # -------------------------------------------------

        p_imp = (
            d.energy_price
            + d.import_tariff
        )

        p_exp = (
            d.energy_price
            - d.export_tariff
        )

        # -------------------------------------------------
        # Objective
        # -------------------------------------------------

        objective = gp.quicksum(
            -self.cQ
            * (
                L[t]
                - d.reference_load[t]
            ) ** 2

            - d.pv_marginal_cost * PV[t]

            - p_imp[t] * P_imp[t]

            + p_exp[t] * P_exp[t]

            for t in T
        )

        m.setObjective(
            objective,
            GRB.MAXIMIZE
        )

        # -------------------------------------------------
        # Constraints
        # -------------------------------------------------

        # Energy balance
        self.con["balance"] = m.addConstrs(
            PV[t]
            - L[t]
            - P_exp[t]
            + P_imp[t]
            == 0
            for t in T
        )

        # Load bounds
        self.con["load_min"] = m.addConstrs(
            L[t] >= d.load_min_kWh
            for t in T
        )

        self.con["load_max"] = m.addConstrs(
            L[t] <= d.load_max_kWh
            for t in T
        )

        # PV bounds
        self.con["pv_min"] = m.addConstrs(
            PV[t] >= 0
            for t in T
        )

        self.con["pv_max"] = m.addConstrs(
            PV[t] <= d.pv_available[t]
            for t in T
        )

        # Grid import/export bounds
        self.con["import_min"] = m.addConstrs(
            P_imp[t] >= 0
            for t in T
        )

        self.con["export_min"] = m.addConstrs(
            P_exp[t] >= 0
            for t in T
        )

        m.update()

        return self


class TemporallyCoupledDisutilityModel(FlexibleConsumerModel):
    """
    Q2(e): Flexible consumer with temporally coupled quadratic disutility.

    Disutility:
        cQ * sum_t (L_t - L_ref_t)^2
        + gamma * sum_{t=2}^{24}
          ((L_t - L_ref_t) + (L_{t-1} - L_ref_{t-1}))^2

    Units:
        cQ    : DKK/kWh^2
        gamma : DKK/kWh^2
        load  : kWh
    """

    def __init__(
        self,
        data,
        cQ=None,
        gamma=0.25,
        name="Q2_temporal",
        verbose=False
    ):
        super().__init__(data, name=name, verbose=verbose)

        # Use the Q2(c) quadratic coefficient by default
        if cQ is None:
            cQ = data.quadratic_disutility

        self.cQ = float(cQ)
        self.gamma = float(gamma)

        if self.cQ <= 0:
            raise ValueError("cQ must be positive.")

        if self.gamma < 0:
            raise ValueError("gamma must be non-negative.")

        if data.reference_load is None:
            raise ValueError(
                "Reference load is required for the temporally "
                "coupled disutility model."
            )

    def build(self):
        d = self.data
        m = self.m
        T = self.T

        # ---------------------------------------------------------
        # Decision variables
        # ---------------------------------------------------------

        L = m.addVars(
            T,
            lb=-GRB.INFINITY,
            vtype=GRB.CONTINUOUS,
            name="load"
        )

        PV = m.addVars(
            T,
            lb=-GRB.INFINITY,
            vtype=GRB.CONTINUOUS,
            name="pv"
        )

        P_imp = m.addVars(
            T,
            lb=-GRB.INFINITY,
            vtype=GRB.CONTINUOUS,
            name="import"
        )

        P_exp = m.addVars(
            T,
            lb=-GRB.INFINITY,
            vtype=GRB.CONTINUOUS,
            name="export"
        )

        # Store variables so that results.hourly contains them
        self.var["load"] = L
        self.var["pv"] = PV
        self.var["import"] = P_imp
        self.var["export"] = P_exp

        # ---------------------------------------------------------
        # Effective import/export prices
        # ---------------------------------------------------------

        p_imp = d.energy_price + d.import_tariff
        p_exp = d.energy_price - d.export_tariff

        # ---------------------------------------------------------
        # Deviations from reference
        # ---------------------------------------------------------

        deviation = {
            t: L[t] - d.reference_load[t]
            for t in T
        }

        # ---------------------------------------------------------
        # Objective
        #
        # Maximize negative total cost:
        #
        #   procurement cost
        # + separable quadratic disutility
        # + temporal coupling disutility
        # ---------------------------------------------------------

        separable_disutility = gp.quicksum(
            self.cQ * deviation[t] ** 2
            for t in T
        )

        temporal_disutility = gp.quicksum(
            self.gamma
            * (deviation[t] + deviation[t - 1]) ** 2
            for t in T
            if t > 0
        )

        procurement_cost = gp.quicksum(
            d.pv_marginal_cost * PV[t]
            + p_imp[t] * P_imp[t]
            - p_exp[t] * P_exp[t]
            for t in T
        )

        m.setObjective(
            -procurement_cost
            -separable_disutility
            -temporal_disutility,
            GRB.MAXIMIZE
        )

        # ---------------------------------------------------------
        # Energy balance
        # ---------------------------------------------------------

        self.con["balance"] = m.addConstrs(
            PV[t]
            - L[t]
            - P_exp[t]
            + P_imp[t]
            == 0
            for t in T
        )

        # ---------------------------------------------------------
        # Load bounds
        # ---------------------------------------------------------

        self.con["load_min"] = m.addConstrs(
            L[t] >= d.load_min_kWh
            for t in T
        )

        self.con["load_max"] = m.addConstrs(
            L[t] <= d.load_max_kWh
            for t in T
        )

        # ---------------------------------------------------------
        # PV bounds
        # ---------------------------------------------------------

        self.con["pv_min"] = m.addConstrs(
            PV[t] >= 0
            for t in T
        )

        self.con["pv_max"] = m.addConstrs(
            PV[t] <= d.pv_available[t]
            for t in T
        )

        # ---------------------------------------------------------
        # Grid import/export bounds
        # ---------------------------------------------------------

        self.con["import_min"] = m.addConstrs(
            P_imp[t] >= 0
            for t in T
        )

        self.con["export_min"] = m.addConstrs(
            P_exp[t] >= 0
            for t in T
        )

        m.update()

        return self

