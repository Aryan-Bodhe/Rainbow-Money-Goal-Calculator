# core/Portfolio.py

from datetime import datetime
from typing import List, Dict, Literal

import pandas as pd
import numpy as np

from core.asset import Asset
from core.xirr_calculator import XirrCalculator
from models.asset import AssetSummary
from models.portfolio import PortfolioSummary

class Portfolio:
    """
    Represents a multi-asset SIP portfolio:
      - goal_amount (₹), time_horizon (years), lumpsum_amount (₹)
      - list of Asset instances (weights sum to 1)
      - computes per-asset SIPs, per-asset XIRRs
      - computes portfolio XIRR via rolling historical NAV
      - simulates month-by-month growth
      - estimates probability of reaching goal via Monte Carlo
      - suggests SIP to hit a target probability
    """

    def __init__(
        self,
        goal_amount: float,
        time_horizon: int,
        lumpsum_amount: float,
        assets: List[Asset],
        start_date: datetime,
        risk_profile: Literal['conservative', 'balanced', 'aggressive']
    ):
        # Core parameters
        self.goal_amount = goal_amount
        self.time_horizon = time_horizon  # in years
        self.lumpsum_amount = lumpsum_amount
        self.assets = assets              # List[Asset]
        self.start_date = start_date
        self.total_months = time_horizon * 12
        self.risk_profile = risk_profile

        # Computation results
        self.asset_returns: Dict[str, float] = {}
        self.asset_sips: Dict[str, float] = {}
        self.asset_xirrs: Dict[str, float] = {}
        self.total_monthly_sip: float = 0.0
        self.monthly_rate: float = 0.0
        self.cumulative_investment: List[float] = []
        self.cumulative_returns: List[float] = []
        self.portfolio_xirr: float = 0.0
        self.portfolio_forecasted_xirr: float = 0.0

        # Probability-related
        self._composite_nav_df: pd.DataFrame | None = None
        self.goal_achievement_probability: float = 0.0
        self.suggested_sip: float = 0.0

    def check_weights(self) -> None:
        """
        Validates that the sum of asset weights equals 1 (within FP tolerance).
        """
        total = sum(asset.weight for asset in self.assets)
        if int(total + 1e-8) != 1:
            raise ValueError("Portfolio asset weights do not sum to 1.")

    def convert_assets_to_inr(self) -> None:
        """
        Converts each Asset's NAV history to INR.
        """
        for asset in self.assets:
            asset.convert_navs_to_inr()

    def compute_asset_xirr(self, mode: Literal["mean", "median", "optimistic", "pessimistic"] = "median") -> None:
        """
        Computes rolling-window XIRR for each asset.
        Stores in self.asset_returns.
        """
        for asset in self.assets:
            rate = asset.compute_rolling_xirr(self.time_horizon, mode=mode)
            self.asset_returns[asset.name] = rate

    def compute_per_asset_sips(self) -> None:
        """
        Calculates SIP per asset based on weighted average return.
        Updates self.asset_sips and total_monthly_sip.
        """
        avg_return = sum(a.expected_return_rate * a.weight for a in self.assets)
        self.monthly_rate = (avg_return / 100) / 12

        for asset in self.assets:
            sip = asset.compute_monthly_sip_for_asset(
                total_FV=self.goal_amount,
                lumpsum_amount=self.lumpsum_amount,
                total_months=self.total_months,
                monthly_rate=self.monthly_rate
            )
            self.asset_sips[asset.name] = sip

        self.total_monthly_sip = round(sum(self.asset_sips.values()), 2)

    def build_portfolio_nav(self) -> pd.DataFrame:
        """
        Builds composite NAV by weighted sum of each asset's NAV_INR series.
        Returns DataFrame ['Date', 'NAV_INR'].
        """
        if self._composite_nav_df is None:
            self.prepare_composite_nav()

        weights = {a.name: a.weight for a in self.assets}
        missing = set(weights) - set(self._composite_nav_df.columns)
        if missing:
            raise ValueError(f"Missing NAV columns for assets: {missing}")

        weighted = self._composite_nav_df.mul(pd.Series(weights), axis=1)
        nav_series = weighted.sum(axis=1)

        return pd.DataFrame({
            "Date": nav_series.index,
            "NAV_INR": nav_series.values
        }).reset_index(drop=True)

    def compute_portfolio_rolling_xirr(self, mode: Literal["mean", "median", "optimistic", "pessimistic"] = "median") -> float:
        """
        Computes portfolio-level rolling XIRR from historical composite NAV.
        """
        hist_nav = self.build_portfolio_nav()
        self.portfolio_xirr = XirrCalculator().compute_rolling_xirr(self.time_horizon, df=hist_nav, mode=mode)
        return self.portfolio_xirr

    def simulate_growth(self) -> None:
        """
        Simulates month-by-month portfolio growth at `self.monthly_rate` and SIP.
        Populates self.cumulative_investment and cumulative_returns.
        """
        M, r, s, L = self.total_months, self.monthly_rate, self.total_monthly_sip, self.lumpsum_amount
        months = list(range(M + 1))
        inv_list, val_list = [], []

        for m in months:
            # Investment to date
            inv = (L + s * max(0, m - 1)) if L > 0 else s * m
            inv_list.append(inv)

            # Portfolio value to date
            if L > 0:
                lump_growth = L * (1 + r) ** m
                sip_growth = s * (((1 + r) ** m - 1) / r) * (1 + r) if m > 0 else 0
                val = lump_growth + sip_growth
            else:
                val = s * (((1 + r) ** m - 1) / r) * (1 + r) if m > 0 else 0

            val_list.append(val)

        self.cumulative_investment = inv_list
        self.cumulative_returns = [max(0, val - inv) for val, inv in zip(val_list, inv_list)]

    def get_portfolio_summary(self) -> PortfolioSummary:
        """
        Aggregates all computed metrics into a PortfolioSummary model.
        """
        asset_summaries = [
            AssetSummary(
                name=a.name,
                weight=a.weight,
                expected_return=self.asset_returns.get(a.name, 0.0),
                sip_amount=self.asset_sips.get(a.name, 0.0),
                xirr=self.asset_returns.get(a.name, 0.0)
            )
            for a in self.assets
        ]

        growth = (
            (self.cumulative_returns[-1] / self.cumulative_investment[-1] * 100)
            if self.cumulative_investment and self.cumulative_investment[-1] != 0
            else 0
        )

        return PortfolioSummary(
            goal_amount=self.goal_amount,
            time_horizon=self.time_horizon,
            lumpsum_amount=self.lumpsum_amount,
            total_monthly_sip=(
                round(self.total_monthly_sip, 2)
                if self.total_monthly_sip > 0
                else "SIP not required. Lumpsum enough to reach Goal."
            ),
            risk_profile=self.risk_profile.capitalize(),
            portfolio_growth=round(growth, 2),
            asset_summaries=asset_summaries,
            rolling_xirr=round(self.portfolio_xirr, 2),
            goal_achievement_probability=round(self.goal_achievement_probability * 100, 2),
            suggested_sip=(
                round(self.suggested_sip, 2)
                if self.suggested_sip > 1000
                else "No additional SIP required."
            )
        )

    def prepare_composite_nav(self) -> None:
        """
        Aligns each Asset's NAV_INR history by date and fills gaps,
        storing in self._composite_nav_df.
        """
        dfs = []
        for asset in self.assets:
            df = asset._df[['Date', 'NAV_INR']].copy()
            df.set_index('Date', inplace=True)
            df.rename(columns={'NAV_INR': asset.name}, inplace=True)
            dfs.append(df)

        combined = pd.concat(dfs, axis=1).sort_index().ffill().bfill()
        self._composite_nav_df = combined

    def probability_of_reaching_goal(
        self,
        monthly_sip: float,
        lumpsum: float = 0.0,
        num_simulations: int = 10_000
    ) -> float:
        """
        Monte Carlo simulation to estimate probability of reaching goal_amount.
        """
        if self._composite_nav_df is None:
            self.prepare_composite_nav()

        log_returns = np.log(self._composite_nav_df / self._composite_nav_df.shift(1)).dropna()
        mu = log_returns.mean().values
        cov = log_returns.cov().values

        weights = np.array([a.weight for a in self.assets])
        months = self.total_months
        lumpsum_alloc = weights * lumpsum
        sip_alloc = weights * monthly_sip

        # Initialize values for each simulation
        values = np.zeros((num_simulations, len(self.assets)))
        L = np.linalg.cholesky(cov)

        for m in range(months):
            values += (lumpsum_alloc + sip_alloc) if m == 0 else sip_alloc
            z = np.random.randn(num_simulations, len(self.assets))
            returns = z @ L.T + mu
            values *= np.exp(returns)

        portfolio_vals = values.sum(axis=1)
        prob = float((portfolio_vals >= self.goal_amount).mean())
        self.goal_achievement_probability = prob
        return prob

    def suggest_sip_for_probability(
        self,
        target_prob: float = 0.95,
        lumpsum: float = 0.0,
        num_simulations: int = 10_000
    ) -> float:
        """
        Uses bisection search to find SIP that achieves target probability.
        """
        low, high = 0.0, self.goal_amount
        for _ in range(20):
            mid = (low + high) / 2
            p = self.probability_of_reaching_goal(mid, lumpsum, num_simulations)
            if p < target_prob:
                low = mid
            else:
                high = mid
        self.suggested_sip = round(high, 2)
        return self.suggested_sip
