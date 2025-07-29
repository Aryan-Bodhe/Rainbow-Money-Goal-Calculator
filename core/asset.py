import pandas as pd

from core.xirr_calculator import XirrCalculator
from core.currency_converter import CurrencyConverter

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
        is_sip_start_of_month: bool = True,
        return_rate: float = None
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

        self.expected_return_rate: float = return_rate   # % annual, from rolling‐window XIRR
        self.asset_sip_amount: float = 0.0       # ₹ SIP per month for this asset
        self.asset_xirr: float = 0.0             # XIRR % computed for this asset
        self._df: pd.DataFrame | None = None     # loaded historical DataFrame
        self.data_available = False if return_rate else True

    def convert_navs_to_inr(self) -> None:
        """
        Converts the NAV of the historical data to INR using date-matched conversion rates.
        """
        if not self.data_available:
            return
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
        if not self.data_available:
            return
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
        if not self.data_available:
            return self.expected_return_rate
        
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
