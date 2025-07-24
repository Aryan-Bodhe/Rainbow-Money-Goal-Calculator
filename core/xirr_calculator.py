from __future__ import annotations

import pandas as pd
import pyxirr
from typing import List, Literal
from colorama import Fore
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

from config import ENABLE_XIRR_DUMP
from core.exceptions import (
    HistoricalDataTooLowError,
    NeitherDataNorPathProvidedError,
    XirrComputationFailedError,
    InvalidReturnCalculationModeError
)


class XirrCalculator:
    """
    Computes rolling XIRR (Extended Internal Rate of Return) values
    from SIP investments using historical NAV data.
    """

    def __init__(self):
        pass

    def _compute_rolling_window_xirrs(
        self,
        df: pd.DataFrame,
        time_horizon: int,
        sip_amount: float = 1000
    ) -> List[float]:
        """
        Compute XIRRs for all rolling SIP windows of specified time_horizon.

        Args:
            df: DataFrame containing ['Date', 'NAV_INR'] columns.
            time_horizon: Duration in years for each SIP window.
            sip_amount: Monthly SIP amount in INR.

        Returns:
            List of XIRR values (annualized returns in %).
        """
        months = time_horizon * 12
        xirrs: List[float] = []
        end_dates: List = []

        for start in range(len(df) - months):
            window = df.iloc[start : start + months + 1]
            if len(window) < months + 1:
                continue

            # SIP investments
            dates = list(window['Date'][:months])
            amounts = [-sip_amount] * months

            # Units purchased each month
            start_prices = window['NAV_INR'].iloc[:months].values
            end_price = window['NAV_INR'].iloc[months]
            units = [sip_amount / p for p in start_prices]

            total_units = sum(units)
            maturity_value = total_units * end_price

            # Add final redemption
            dates.append(window['Date'].iloc[months])
            amounts.append(maturity_value)

            try:
                xirr_val = pyxirr.xirr(dict(zip(dates, amounts))) * 100
                xirrs.append(xirr_val)
                end_dates.append(window['Date'].iloc[months])
            except Exception as e:
                raise XirrComputationFailedError(e)

        return xirrs, end_dates

    def compute_rolling_xirr(
        self,
        time_horizon: int,
        feather_path: str | None = None,
        df: pd.DataFrame | None = None,
        mode: Literal["mean", "median", "optimistic", "pessimistic"] = "median"
    ) -> tuple[float, list, list]:
        """
        Estimate return using rolling SIP XIRR approach over historical data.

        Args:
            time_horizon: Duration (in years) for each SIP window.
            feather_path: Optional path to Feather file with NAV data.
            df: Optional pre-loaded DataFrame with ['Date', 'NAV_INR'].
            mode: Statistic to compute from XIRR values ('median', 'mean', 'pessimistic', 'optimistic').

        Returns:
            Annualized return (% CAGR) as float.

        Raises:
            NeitherDataNorPathProvidedError: If both df and feather_path are missing.
            HistoricalDataTooLowError: If data is insufficient for computation.
            InvalidReturnCalculationModeError: If mode is not recognized.
            XirrComputationFailedError: If pyxirr fails to compute any return.
        """
        if df is None:
            if feather_path is None:
                raise NeitherDataNorPathProvidedError()
            df = pd.read_feather(feather_path)

        # Ensure sorted and clean data
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date').reset_index(drop=True)

        # Compute rolling XIRRs
        xirrs, end_dates = self._compute_rolling_window_xirrs(df, time_horizon)
        if not xirrs:
            raise HistoricalDataTooLowError('', '', '')


        # Return appropriate statistic
        series = pd.Series(xirrs)
        if mode == "median":
            return round(series.median(), 2), xirrs, end_dates
        elif mode == "mean":
            return round(series.mean(), 2), xirrs, end_dates
        elif mode == "pessimistic":
            return round(series.quantile(0.25), 2), xirrs, end_dates
        elif mode == "optimistic":
            return round(series.quantile(0.75), 2), xirrs, end_dates
        else:
            raise InvalidReturnCalculationModeError(
                mode, ("median", "mean", "pessimistic", "optimistic")
            )
