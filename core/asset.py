import pandas as pd
from datetime import datetime
import pyxirr

from core.xirr_calculator import XirrCalculator
from core.currency_converter import CurrencyConverter
from core.exceptions import (
    InvalidStartDateError,
    LumpsumEnoughToReachGoalError, 
    InvalidTimeHorizonError, 
    InvalidReturnRateError, 
    XirrComputationFailedError
)

class Asset:
    """
    Represents a single asset (e.g., smallcap, debt, gold) with:
      - name (e.g. "smallcap")
      - weight (fraction of the total portfolio)
      - path to its historical NAV (feather) file
      - methods to compute expected return, per-asset SIP, and per-asset XIRR
    """

    def __init__(
        self,
        name: str,
        feather_path: str,
        weight: float,
        is_sip_start_of_month: bool = False
    ):
        """
        :param name: Asset name (e.g., "smallcap").
        :param feather_path: Path to that asset's historical price (Feather format).
        :param weight: Fraction of total portfolio allocated to this asset (must sum to 1).
        :param is_sip_start_of_month: If True, SIP is at month-start; otherwise month-end.
        """
        self.name = name
        self.feather_path = feather_path
        self.weight = weight
        self.is_sip_start_of_month = is_sip_start_of_month

        self.expected_return_rate: float = 0.0   # % annual, from rolling‐window XIRR
        self.asset_sip_amount: float = 0.0       # ₹ SIP per month for this asset
        self.asset_xirr: float = 0.0             # XIRR % computed for this asset
        self._df: pd.DataFrame | None = None     # loaded historical DataFrame

    def convert_navs_to_inr(self) -> None:
        """
        Converts the NAV of the historical data to INR using date-matched conversion rates.
        """
        curr_conv = CurrencyConverter()
        if self._df is None:
            self.load_history()

        # Assumes date-aligned FX rates exist for all NAV dates
        self._df = curr_conv.convert_to_inr(nav_data=self._df)

    def load_history(self) -> None:
        """
        Reads the Feather file into self._df, normalizes dates to midnight, and sorts.
        Expects the Feather file to contain a 'Date' column.
        """
        df = pd.read_feather(self.feather_path)
        df['Date'] = pd.to_datetime(df['Date']).dt.normalize()
        df = df.sort_values('Date').reset_index(drop=True)
        self._df = df

    def compute_rolling_xirr(
        self,
        time_horizon: int,
        mode: str = "median"
    ) -> float:
        """
        Uses SIPReturnForecaster to compute rolling-window SIP XIRR (median/mean/etc.)
        on this asset's history. Stores result in self.expected_return_rate.

        :param time_horizon: Number of years for the rolling XIRR window.
        :param mode: Aggregation mode over rolling windows ('median', 'mean', etc.)
        :return: Estimated annual return rate (%)
        """
        if self._df is None:
            self.load_history()

        xirr_calc = XirrCalculator()

        expected, _, _ = xirr_calc.compute_rolling_xirr(
            time_horizon=time_horizon,
            df=self._df,
            mode=mode
        )
        self.expected_return_rate = expected
        return expected

    def compute_monthly_sip_for_asset(
        self,
        total_FV: float,
        lumpsum_amount: float,
        total_months: int,
        monthly_rate: float
    ) -> float:
        """
        Applies ordinary annuity SIP formula for this asset:
            sip = ((FV - L*(1+r)^n) / (((1+r)^n - 1)/r)) * weight

        :param total_FV: The overall portfolio goal (₹).
        :param lumpsum_amount: The overall lumpsum (₹).
        :param total_months: Time horizon in months (years * 12).
        :param monthly_rate: Monthly rate of return as decimal (annual / 12 / 100).
        :return: ₹ per-month SIP for this asset (rounded).
        """
        numerator = total_FV - lumpsum_amount * (1 + monthly_rate) ** total_months
        denominator = ((1 + monthly_rate) ** total_months - 1) / monthly_rate
        sip_amt = (numerator / denominator) * self.weight

        # SIP should not be negative. If it is, default to 0.
        self.asset_sip_amount = max(0, round(sip_amt, 2))
        return self.asset_sip_amount

    def compute_forecasted_asset_xirr(
        self,
        goal_amt: float,
        lumpsum_amt: float = 0.0,
        start_date: datetime = None,
        total_months: int = 0,
    ) -> float:
        """
        Builds a forward-looking cashflow dictionary using expected_return_rate
        (no future price lookup), then computes XIRR using pyxirr.

        :param goal_amt: Target amount to reach (₹).
        :param lumpsum_amt: Lumpsum investment at start (₹). Default is 0.
        :param start_date: Start date of investment.
        :param total_months: Investment duration in months.
        :return: Asset XIRR (%) rounded to 2 decimal places.
        """
        if self.expected_return_rate <= 0:
            raise InvalidReturnRateError(self.expected_return_rate)

        if start_date is None:
            raise InvalidStartDateError(start_date)

        if total_months <= 0:
            raise InvalidTimeHorizonError(total_months / 12)

        r_annual = self.expected_return_rate / 100
        r_monthly = r_annual / 12
        N = total_months

        sip_amt = self.asset_sip_amount

        # Compute final value from both lumpsum and SIP growth
        lumpsum_growth = lumpsum_amt * (1 + r_monthly) ** N
        sip_growth = 0

        if lumpsum_growth > goal_amt:
            self.asset_xirr = 0.0
            raise LumpsumEnoughToReachGoalError(lumpsum_amt, goal_amt)

        if r_monthly != 0:
            sip_growth = sip_amt * (((1 + r_monthly) ** N - 1) / r_monthly) * (1 + r_monthly)
        else:
            sip_growth = sip_amt * N  # No interest case

        final_value = lumpsum_growth + sip_growth

        # Build date-wise cashflow dictionary
        cf_dict: dict[datetime, float] = {}
        t0 = pd.Timestamp(start_date.date())

        cf_dict[t0] = -round(lumpsum_amt + sip_amt, 2)  # Initial outflow

        for m in range(1, N):
            sip_date = t0 + pd.DateOffset(months=m)
            cf_dict[sip_date] = -round(sip_amt, 2)

        redemption_date = t0 + pd.DateOffset(months=N)
        cf_dict[redemption_date] = round(final_value, 2)  # Final inflow

        try:
            rate = pyxirr.xirr(cf_dict) * 100
        except Exception as e:
            raise XirrComputationFailedError(e)

        self.asset_xirr = round(rate, 2)
        return self.asset_xirr
