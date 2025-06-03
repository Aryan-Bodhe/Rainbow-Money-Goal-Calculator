# source/Asset.py

import pandas as pd
from datetime import datetime
import pyxirr

from source.SIP_Return_Forecaster import SIPReturnForecaster
from source.Exceptions import (
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
        :param feather_path: Path to that asset’s historical price (Feather format).
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


    def load_history(self) -> None:
        """
        Reads the Feather file into self._df, normalizes dates to midnight, and sorts.
        """
        df = pd.read_feather(self.feather_path)
        df['Date'] = pd.to_datetime(df['Date']).dt.normalize()
        df = df.sort_values('Date').reset_index(drop=True)
        self._df = df


    def compute_expected_return(
        self,
        time_horizon: int,
        mode: str = "median"
    ) -> float:
        """
        Uses SIPReturnForecaster to compute rolling‐window SIP XIRR (median/mean/etc.)
        on this asset’s history. Stores result in self.expected_return_rate.
        """
        if self._df is None:
            self.load_history()

        forecaster = SIPReturnForecaster()

        expected = forecaster.get_expected_sip_return_rate(
            time_horizon=time_horizon,
            feather_path=self.feather_path,
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
        Applies your exact SIP formula for this asset:
            sip = ((FV - L*(1+r)^n) / (((1+r)^n - 1)/r)) * weight

        :param total_FV: The overall portfolio goal (₹).
        :param lumpsum_amount: The overall lumpsum (₹).
        :param total_months: time_horizon * 12.
        :param monthly_rate: annual_expected/12/100 (decimal).
        :return: ₹ per-month SIP for this asset (rounded).
        """
        numerator = total_FV - lumpsum_amount * (1 + monthly_rate) ** total_months
        denominator = ((1 + monthly_rate) ** total_months - 1) / monthly_rate
        sip_amt = (numerator / denominator) * self.weight

        # if sip_amt < 0:
        #     self.asset_sip_amount = 0
        #     raise LumpsumEnoughToReachGoalError(lumpsum_amount, goal_amount=goal_amt)
        
        self.asset_sip_amount = max(0, round(sip_amt, 2)) # default to zero if sip < 0 => no sip needed
        return self.asset_sip_amount


    def compute_asset_xirr(
        self,
        goal_amt: float,
        lumpsum_amt: float = 0.0,   # default optional parameter
        start_date: datetime = None,
        total_months: int = 0,
    ) -> float:
        """
        Builds a forward-looking cashflow dictionary using expected_return_rate (no future price lookup),
        then calls pyxirr.xirr(...) to get XIRR%. Stores result in self.asset_xirr.

        :param lumpsum_amt: -(L * weight) at t0. Optional, default 0 (no lumpsum).
        :param start_date:       date of lumpsum (datetime).
        :param total_months:     time_horizon * 12.
        :return:                 XIRR % for this asset (rounded).
        """
        if self.expected_return_rate <= 0:
            # raise ValueError(f"[ERROR] expected_return_rate for '{self.name}' is not set.")
            raise InvalidReturnRateError(self.expected_return_rate)

        if start_date is None:
            # raise ValueError(f"[ERROR] start_date must be provided.")
            raise InvalidStartDateError(start_date)

        if total_months <= 0:
            # raise ValueError(f"[ERROR] total_months must be greater than 0.")
            InvalidTimeHorizonError(total_months / 12)

        r_annual = self.expected_return_rate / 100
        r_monthly = r_annual / 12
        N = total_months

        sip_amt = self.asset_sip_amount

        # Compute final value using closed‐form lump + SIP formula:
        lumpsum_growth = (lumpsum_amt) * (1 + r_monthly) ** N
        sip_growth = 0

        if lumpsum_growth > goal_amt:
            self.asset_xirr = 0.0
            raise LumpsumEnoughToReachGoalError(lumpsum_amt, goal_amt)

        if r_monthly != 0:
            sip_growth = sip_amt * (((1 + r_monthly) ** N - 1) / r_monthly) * (1 + r_monthly)
        elif r_monthly == 0:
            sip_growth = sip_amt * N  # No interest case

        final_value = lumpsum_growth + sip_growth
        # print(lumpsum_growth)
        # print(sip_growth)

        # Build cashflow dict with date keys at exact months:
        cf_dict: dict[datetime, float] = {}
        t0 = pd.Timestamp(start_date.date())

        # print("First month: ", round(lumpsum_amt + sip_amt, 2))

        # Add lumpsum_amt only if non-zero:
        # if lumpsum_amt != 0:
        cf_dict[t0] = -round(lumpsum_amt + sip_amt, 2) # negative at t0

        for m in range(1, N):
            sip_date = t0 + pd.DateOffset(months=m)
            cf_dict[sip_date] = -round(sip_amt, 2)

        redemption_date = t0 + pd.DateOffset(months=N)
        cf_dict[redemption_date] = round(final_value, 2)  # positive
        # print(cf_dict, len(cf_dict))


        try:
            rate = pyxirr.xirr(cf_dict) * 100
        except Exception as e:
            # raise ValueError(f"[ERROR] Cannot compute XIRR for '{self.name}': {e}")
            raise XirrComputationFailedError(e)

        self.asset_xirr = round(rate, 2)

        return self.asset_xirr
