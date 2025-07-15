# source/Portfolio.py

from datetime import datetime
from collections import defaultdict
from typing import List, Dict
import pandas as pd
import pyxirr
from typing import Literal
import numpy as np

from source.Asset import Asset
from source.XIRR_Calculator import XirrCalculator
from models.asset import AssetSummary
from models.portfolio import PortfolioSummary
from source.Exceptions import (
    InvalidSipAmountError, 
    LumpsumEnoughToReachGoalError, 
    XirrComputationFailedError
) 

class Portfolio:
    """
    Represents a multi-asset SIP portfolio:
      - goal_amount (₹), time_horizon (years), lumpsum_amount (₹)
      - list of Asset instances (each with weight & expected_return_rate)
      - computes per-asset SIPs, per-asset XIRRs
      - computes portfolio XIRR (forward-looking) by aggregating cashflows
      - simulates month-by-month growth for plotting
      - estimates probability of reaching goal via Monte Carlo on composite NAV
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
        self.goal_amount = goal_amount
        self.time_horizon = time_horizon  # in years
        self.lumpsum_amount = lumpsum_amount
        self.assets = assets              # List[Asset], weights must sum to 1
        self.start_date = start_date      # datetime
        self.total_months = time_horizon * 12
        self.risk_profile = risk_profile

        # Populated by methods below:
        self.asset_returns: Dict[str, float] = {}    # {asset_name: expected_return%}
        self.asset_sips: Dict[str, float] = {}       # {asset_name: ₹ SIP/month}
        self.asset_xirrs: Dict[str, float] = {}      # {asset_name: forward‐looking XIRR%}
        self.total_monthly_sip: float = 0.0
        self.monthly_rate: float = 0.0               # weighted‐avg monthly decimal rate
        self.cumulative_investment: List[float] = []
        self.cumulative_returns: List[float] = []
        self.portfolio_xirr: float = 0.0
        self.portfolio_forecasted_xirr: float = 0.0

        # For probability methods:
        self._composite_nav_df: pd.DataFrame | None = None
        self.goal_achievement_probability = 0.0
        self.suggested_sip = 0.0


    def check_weights(self) -> None: 
        weight_sum = 0
        for asset in self.assets:
            weight_sum += asset.weight

        weight_sum = int(weight_sum + 1e-8) # add a correction factor for floating point precision error

        if weight_sum != 1:
            print(weight_sum)
            raise ValueError('Portfolio asset weights do not sum to 1.')


    def convert_assets_to_inr(self) -> None:
        """
        For each Asset, convert its nav values from whichever currency to INR.
        """
        for asset in self.assets:
            asset.convert_navs_to_inr()


    def compute_asset_xirr(self, mode: Literal["mean", "median", "optimistic", "pessimistic"] = "median") -> None:
        """
        For each Asset, call compute_expected_return(time_horizon, mode)
        and store in self.asset_returns.
        """
        for asset in self.assets:
            rate = asset.compute_rolling_xirr(
                time_horizon=self.time_horizon,
                mode=mode
            )
            self.asset_returns[asset.name] = rate



    def compute_per_asset_sips(self) -> None:
        """
        1. Weighted‐avg annual return = sum(asset.expected_return_rate * asset.weight)
        2. monthly_rate = (avg_annual_return/100) / 12
        3. For each asset, call compute_monthly_sip_for_asset(...) to get ₹ SIP
        4. total_monthly_sip = sum(self.asset_sips.values())
        """
        avg_annual_return = sum(
            asset.expected_return_rate * asset.weight for asset in self.assets
        )
        self.monthly_rate = (avg_annual_return / 100) / 12

        for asset in self.assets:
            sip_amt = asset.compute_monthly_sip_for_asset(
                total_FV=self.goal_amount,
                lumpsum_amount=self.lumpsum_amount,
                total_months=self.total_months,
                monthly_rate=self.monthly_rate
            )
            self.asset_sips[asset.name] = sip_amt

        self.total_monthly_sip = round(sum(self.asset_sips.values()), 2)


    def build_portfolio_nav(self) -> pd.DataFrame:
        """
        Constructs a single portfolio NAV time series by taking a weighted sum
        of each asset’s NAV_INR series in self._composite_nav_df.

        Returns:
            pd.DataFrame with columns ['Date', 'NAV_INR'], where each NAV_INR value
            is sum(asset_NAV_INR * asset.weight) for that date.

        Raises:
            ValueError: if any asset.name is missing from self._composite_nav_df columns.
        """
        # 1) Ensure composite NAV is prepared
        if self._composite_nav_df is None:
            # raise ValueError("Composite NAV not prepared. Call prepare_composite_nav() first.")
            self.prepare_composite_nav()

        # 2) Build a dict of {asset_name: weight}
        weights = {asset.name: asset.weight for asset in self.assets}

        # 3) Check that every asset name appears as a column in _composite_nav_df
        missing = set(weights.keys()) - set(self._composite_nav_df.columns)
        if missing:
            raise ValueError(f"Missing NAV columns for assets: {missing}")

        # 4) Multiply each column by its weight, then sum across columns to get portfolio NAV
        #    (self._composite_nav_df columns are asset names, each column = NAV_INR time series)
        w_series = pd.Series(weights)
        portfolio_nav_series = self._composite_nav_df.mul(w_series, axis=1).sum(axis=1)

        # 5) Return a DataFrame with ['Date', 'NAV_INR']
        portfolio_df = pd.DataFrame({
            "Date": portfolio_nav_series.index,
            "NAV_INR": portfolio_nav_series.values
        }).reset_index(drop=True)

        return portfolio_df
    

    def compute_portfolio_rolling_xirr(self, mode: Literal["mean", "median", "optimistic", "pessimistic"] = "median") -> None:
        portfolio_historical_value = self.build_portfolio_nav()
        xirr_calc = XirrCalculator()
        self.portfolio_xirr = xirr_calc.compute_rolling_xirr(self.time_horizon, df=portfolio_historical_value, mode=mode)
        return self.portfolio_xirr
    

    def simulate_growth(self) -> None:
        """
        Simulates month‐by‐month growth at the average monthly rate (self.monthly_rate)
        and total SIP (self.total_monthly_sip). Fills self.cumulative_investment
        and self.cumulative_returns. Returns (months, investment, total_value).
        """
        M = self.total_months
        r = self.monthly_rate
        s = self.total_monthly_sip
        L = self.lumpsum_amount

        total_months = M + 1
        months = list(range(total_months))
        investment: list[float] = []
        total_value: list[float] = []

        for m in months:
            if L > 0:
                inv = L + s * max(0, m - 1)
            else:
                inv = s * m
            investment.append(inv)

            if L > 0:
                lumpsum_growth = L * (1 + r) ** m
                sip_growth = (s * (((1 + r) ** m - 1) / r) * (1 + r)) if m > 0 else 0
                val = lumpsum_growth + sip_growth
            else:
                val = (s * (((1 + r) ** m - 1) / r) * (1 + r)) if m > 0 else 0

            total_value.append(val)

        self.cumulative_investment = investment
        self.cumulative_returns = [
            (tv - inv) if (tv - inv) > 1e-6 else 0
            for tv, inv in zip(total_value, investment)
        ]

    
    def get_portfolio_summary(self) -> PortfolioSummary:
        asset_summaries = []

        for asset in self.assets:
            asset_summaries.append(
                AssetSummary(
                    name=asset.name,
                    weight=asset.weight,
                    expected_return=self.asset_returns.get(asset.name, 0.0),
                    sip_amount=self.asset_sips.get(asset.name, 0.0),
                    xirr=self.asset_returns.get(asset.name)
                )
            )

        if self.cumulative_returns and self.cumulative_investment and self.cumulative_investment[-1] != 0:
            growth = self.cumulative_returns[-1] / self.cumulative_investment[-1] * 100

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
            goal_achievement_probability=round(self.goal_achievement_probability*100, 2),
            suggested_sip=(
                round(self.suggested_sip, 2)
                if self.suggested_sip > 1000
                else "No additional SIP required."
            )
        )


    def display_summary(self) -> None:
        """
        Prints a full portfolio summary:
          - goal, horizon, lumpsum, total SIP
          - per-asset weight, expected return, SIP, XIRR
          - overall portfolio XIRR
        """
        print("\n----------- PORTFOLIO SUMMARY -----------")
        print(f"Goal Amount       : ₹{self.goal_amount:,.2f}")
        print(f"Time Horizon      : {self.time_horizon} years")
        print(f"Lumpsum Amount    : ₹{self.lumpsum_amount:,.2f}")
        print(f"Total Monthly SIP : {('₹'+str(round(self.total_monthly_sip, 2)) if self.total_monthly_sip > 0 else "SIP not required. Lumpsum enough to reach Goal.")}")
        print(f"Risk Profile      : {self.risk_profile.capitalize()}")
        print(f"Portfolio Growth  : {self.cumulative_returns[-1]/self.cumulative_investment[-1]*100:.2f}%\n")

        print("Asset Allocation & Expected Returns:")
        for asset in self.assets:
            w = asset.weight
            er = self.asset_returns.get(asset.name, 0.0)
            sip_amt = self.asset_sips.get(asset.name, 0.0)
            print(f"  • {asset.name.capitalize():<10} "
                  f"weight={w:.2f}, exp_return={er:.2f}%, SIP=₹{sip_amt:.2f}")

        print("\nAsset-Level XIRRs:")
        for name, xr in self.asset_xirrs.items():
            print(f"  • {name.capitalize():<10} XIRR = {xr:.2f}%")

        print(f"\nPortfolio Forecasted XIRR : {self.portfolio_forecasted_xirr:.2f}%.")
        print(f"Portfolio Rolling XIRR : {self.portfolio_xirr:0.2f}%.")
        print(f"Probability of reaching ₹{self.goal_amount:,.0f} in {self.time_horizon} years: {self.goal_achievement_probability*100:.2f}%")
        print(f"Suggested total monthly SIP for 95% probability: ₹{self.suggested_sip:,.2f}")
        print("------------------------------------------\n")



    # ── Probability / Suggested SIP Methods ─────────────────────────────────

    def prepare_composite_nav(self) -> None:
        """
        Prepare self._composite_nav_df with monthly NAVs for all assets aligned by date.
        Assumes each Asset has a DataFrame attribute 'nav_df' with 'Date' and 'NAV'.
        """
        nav_dfs = []
        for asset in self.assets:
            df = asset._df[['Date', 'NAV_INR']].copy()
            df.set_index('Date', inplace=True)
            df.rename(columns={'NAV_INR': asset.name}, inplace=True)
            nav_dfs.append(df)

        combined = pd.concat(nav_dfs, axis=1).sort_index().ffill().bfill()
        self._composite_nav_df = combined
        # combined.to_csv('temp/combined.csv')
        

    def probability_of_reaching_goal(
        self,
        monthly_sip: float,
        lumpsum: float = 0.0,
        num_simulations: int = 10_000
    ) -> float:
        """
        Monte Carlo probability of hitting self.goal_amount in `total_months` months,
        given:
        - lumpsum  invested alongside the first SIP at the start of Month 1
        - monthly_sip invested at the start of each Month 1…Month N
        - redemption at the end of Month N (i.e. after N return steps)
        """
        if self._composite_nav_df is None:
            self.prepare_composite_nav()

        n_assets = len(self.assets)

        # 1) Compute historical monthly log‐returns for each asset
        log_returns = np.log(self._composite_nav_df / self._composite_nav_df.shift(1)).dropna()
        mu  = log_returns.mean().values      # shape: (n_assets,)
        # mu = np.full(n_assets, np.log(1 + self.portfolio_xirr) / 12)
        cov = log_returns.cov().values        # shape: (n_assets, n_assets)

        weights = np.array([asset.weight for asset in self.assets])  # (n_assets,)
        months  = self.total_months

        # 2) How much lumpsum goes into each asset at Month 1?
        lumpsum_per_asset = weights * lumpsum      # (n_assets,)

        # 3) How much SIP goes into each asset each month?
        sip_per_asset = weights * monthly_sip      # (n_assets,)

        # 4) Initialize simulated “values” to zero (no money invested before Month 1)
        #    shape: (num_simulations, n_assets)
        values = np.zeros((num_simulations, n_assets))

        # 5) Precompute Cholesky for correlated random draws
        L = np.linalg.cholesky(cov)

        # 6) Loop through each month 1…N (index m=0…months-1)
        for m in range(months):
            if m == 0:
                # Month 1: invest lumpsum + SIP together
                values += (lumpsum_per_asset + sip_per_asset)  # broadcast to each simulation
            else:
                # Months 2…N: invest only the SIP
                values += sip_per_asset

            # Draw correlated monthly log‐returns for all sims
            rand_normals = np.random.randn(num_simulations, n_assets)
            correlated_returns = rand_normals @ L.T + mu  # (num_simulations, n_assets)

            # Apply growth for this month
            values = values * np.exp(correlated_returns)

        # 7) After N months of returns, sum across assets → final portfolio values
        portfolio_values = values.sum(axis=1)  # (num_simulations,)

        # 8) Probability of hitting or exceeding goal_amount
        prob = float(np.mean(portfolio_values >= self.goal_amount))
        self.goal_achievement_probability = prob
        return prob


    def suggest_sip_for_probability(
        self,
        target_prob: float = 0.95,
        lumpsum: float = 0.0,
        num_simulations: int = 10_000
    ) -> float:
        """
        Binary‐search the monthly SIP such that P(final_portfolio ≥ goal_amount) ≈ target_prob,
        given a lumpsum invested alongside the first SIP in Month 1.
        """
        low, high = 0.0, self.goal_amount  # assume SIP ≤ goal is an adequate upper bound

        for _ in range(20):
            mid = (low + high) / 2
            prob = self.probability_of_reaching_goal(
                monthly_sip=mid,
                lumpsum=lumpsum,
                num_simulations=num_simulations
            )
            if prob < target_prob:
                low = mid
            else:
                high = mid
        sugg_sip = round(high, 2)
        self.suggested_sip = sugg_sip
        return sugg_sip
    


    # ── Forecasted Return Rate Methods ─────────────────────────────────

    def compute_forecasted_asset_xirrs(self) -> None:
        """
        For each Asset:
          - lumpsum_cf = –(self.lumpsum_amount * asset.weight)
          - call asset.compute_asset_xirr(lumpsum_cf, self.start_date, self.total_months)
          - store in self.asset_xirrs[asset.name]
        """
        for asset in self.assets:
            lumpsum_cf = (self.lumpsum_amount * asset.weight)
            try:
                xirr_pct = asset.compute_forecasted_asset_xirr(
                    goal_amt=self.goal_amount,
                    lumpsum_amt=lumpsum_cf,
                    start_date=self.start_date,
                    total_months=self.total_months
                )
                self.asset_xirrs[asset.name] = xirr_pct
            except LumpsumEnoughToReachGoalError:
                print("Lumpsum is good")
                return


    def compute_forecasted_portfolio_xirr(self) -> float:
        """
        Aggregates forward‐looking cashflows (lumpsum + SIPs + redemption) for each asset:
          - lumpsum at t0
          - SIP each month for N months
          - redemption at month N using each asset’s expected_return_rate
        Calls pyxirr.xirr(...) on the combined cashflow dict and returns XIRR%.
        """
        combined_cfs: dict[datetime, float] = defaultdict(float)
        N = self.total_months
        t0 = pd.Timestamp(self.start_date.date())

        for asset in self.assets:
            # print(asset.name)
            # 1) Optional Lumpsum Outflow
            lumpsum_cf = 0.0
            sip_amt = asset.asset_sip_amount

            if sip_amt < 0:
                # raise ValueError(f"[ERROR] asset_sip_amount for '{asset.name}' is not set.")
                raise InvalidSipAmountError(sip_amt)

            # if self.lumpsum_amount > 0:
            lumpsum_cf = (self.lumpsum_amount * asset.weight)
            combined_cfs[t0] += -(lumpsum_cf + sip_amt)

            # 2) SIP Outflows (Always happens if asset_sip_amount > 0)
            # for m in range(1, N + 1):
            for m in range(1, N):
                sip_date = t0 + pd.DateOffset(months=m)
                combined_cfs[sip_date] += -sip_amt

            # 3) Redemption Inflow
            r_monthly = (asset.expected_return_rate / 100) / 12

            # Handle case where lumpsum_cf = 0
            lumpsum_growth = (lumpsum_cf) * (1 + r_monthly) ** N 

            # SIP future value (assumes SIPs occur at start of month, i.e. annuity due)
            sip_growth = 0
            if r_monthly != 0:
                sip_growth = sip_amt * (((1 + r_monthly) ** N - 1) / r_monthly) * (1 + r_monthly)
            elif r_monthly == 0:
                sip_growth = sip_amt * N  # No interest case

            # print(lumpsum_growth)
            # print(sip_growth)
            
            final_value = lumpsum_growth + sip_growth
            redemption_date = t0 + pd.DateOffset(months=N)
            combined_cfs[redemption_date] += final_value

        # Clean cashflows: remove zero-amount dates
        cf_dict = {date: round(amount, 2) for date, amount in combined_cfs.items() if abs(amount) > 1e-8}

        # Must have at least one negative and one positive cashflow
        # if not any(v < 0 for v in cf_dict.values()) or not any(v > 0 for v in cf_dict.values()):
        #     # raise ValueError("[ERROR] Cashflows must include at least one inflow and one outflow to compute XIRR.")
        #     raise XirrComputationFailedError("")

        try:
            rate = pyxirr.xirr(cf_dict) * 100
        except Exception as e:
            # raise ValueError(f"[ERROR] Cannot compute portfolio XIRR: {e}")
            raise XirrComputationFailedError(e)

        self.portfolio_forecasted_xirr = round(rate, 2)
        # print('portfolio-level')
        # print(cf_dict, len(cf_dict))

        return self.portfolio_forecasted_xirr

