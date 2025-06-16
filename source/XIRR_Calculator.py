# XIRR_Calculator.py

from __future__ import annotations
import pandas as pd
import pyxirr
from typing import List, Literal
from colorama import Fore
from config import ENABLE_XIRR_DUMP

from source.Exceptions import (
    HistoricalDataTooLowError, 
    NeitherDataNorPathProvidedError, 
    XirrComputationFailedError, 
    InvalidReturnCalculationModeError
)

class XirrCalculator:
    def __init__(self):
        pass

    def _compute_rolling_window_xirrs(
        self, df: pd.DataFrame, time_horizon: int, sip_amount: float = 1000
    ) -> List[float]:
        """
        Compute XIRRs for rolling SIP windows using historical data.
        """
        months = time_horizon * 12
        xirrs: List[float] = []

        for start in range(len(df) - months):
            window = df.iloc[start : start + months + 1]
            if len(window) < months + 1:
                continue

            dates = list(window['Date'][:months])
            amounts = [-sip_amount] * months

            start_prices = window['NAV_INR'].iloc[:months].values
            end_price = window['NAV_INR'].iloc[months]

            units = [sip_amount / p for p in start_prices]
            total_units = sum(units)
            maturity_value = total_units * end_price

            dates.append(window['Date'].iloc[months])
            amounts.append(maturity_value)

            try:
                xirr_val = pyxirr.xirr(dict(zip(dates, amounts))) * 100
                xirrs.append(xirr_val)
            except Exception as e:
                raise XirrComputationFailedError(e)
        
        return xirrs

    def compute_rolling_xirr(
        self,
        time_horizon: int,
        feather_path: str | None = None,
        df: pd.DataFrame | None = None,
        mode: Literal["mean", "median", "optimistic", "pessimistic"] = "median"
    ) -> float:
        """
        :param time_horizon: Investment horizon in years.
        :param feather_path: If provided, reads this Feather file into df.
        :param df: If provided, uses this DataFrame directly (skips reading from file).
        :param mode: 'median', 'mean', 'pessimistic', or 'optimistic'.
        :return: Estimated return rate (% CAGR).
        """
        if df is None:
            if feather_path is None:
                # raise ValueError("[ERROR] Must supply either `df` or `feather_path`.")
                raise NeitherDataNorPathProvidedError()
            df = pd.read_feather(feather_path)

        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date').reset_index(drop=True)

        xirrs = self._compute_rolling_window_xirrs(df, time_horizon)
        if not xirrs:
            # raise ValueError(Fore.YELLOW + "[WARNING] Not enough data to compute returns." + Fore.RESET)
            raise HistoricalDataTooLowError('', '', '')
        
        if ENABLE_XIRR_DUMP:
            print(xirrs)

        series = pd.Series(xirrs)
        if mode == "median":
            return round(series.median(), 2)
        elif mode == "mean":
            return round(series.mean(), 2)
        elif mode == "pessimistic":
            return round(series.quantile(0.25), 2)
        elif mode == "optimistic":
            return round(series.quantile(0.75), 2)
        else:
            raise InvalidReturnCalculationModeError(mode, ("median", "mean", "pessimistic", "optimistic"))
            
