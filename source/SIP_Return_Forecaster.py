from __future__ import annotations
import pandas as pd
import pyxirr
from typing import List, Tuple
from colorama import Fore
from typing import Literal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from source.SIP_Goal_Based import SipGoalBased as SGP


class SIPReturnForecaster:
    def __init__(self, feather_path: str):
        """
        Initialize with monthly index data from a .feather file.
        :param feather_path: Path to the Feather file with 'Date' and 'Closing Price' columns.
        """
        self.df = pd.read_feather(feather_path)
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        self.df = self.df.sort_values('Date').reset_index(drop=True)


    def fixed_window_sip_xirr(self, years: int, sip_amount: float = 10_000) -> float:
        months = years * 12
        df = self.df.set_index("Date")
        window = df.iloc[-(months+1):]  # last N years + final NAV
        sip_navs = window["Closing Price"].iloc[:-1].values
        redemption_nav = window["Closing Price"].iloc[-1]

        # Align to 1st of month (or next trading day)
        sip_dates = pd.date_range(end=window.index[-1], periods=months, freq="MS")
        actual = [d if d in df.index else d + pd.Timedelta(days=1) for d in sip_dates]

        units = sip_amount / df.loc[actual, "Closing Price"].values
        final_value = units.sum() * redemption_nav
        cashflows = [-sip_amount]*months + [final_value]
        dates = actual + [window.index[-1]]

        return round(pyxirr.xirr(dict(zip(dates, cashflows)))*100, 2)


    def simulate_portfolio_returns(
        self, sip_plan: SGP
    ) -> Tuple[List[int], List[float], List[float]]:
        """
        Simulate portfolio values and investment over time.

        Args:
            sip_plan (SGP): SIP parameters including amount, rate, and duration.

        Returns:
            Tuple: (months, investment values, portfolio values)
        """
        M = sip_plan.time_horizon * 12  # Total months
        r = sip_plan.return_rate / 100 / 12  # Monthly return rate
        s = sip_plan.monthly_sip
        L = sip_plan.lumpsum_amount

        total_months = M + 1  # Include final redemption month
        months = list(range(total_months))

        investment = []
        total_value = []

        for m in months:
            # Cumulative investment till the start of month m
            if L > 0:
                inv = L + s * max(0, m - 1)  # lumpsum at start, SIP starts from month 1
            else:
                inv = s * m
            investment.append(inv)

            # Future value calculation for lumpsum + SIP (annuity-due formula)
            if L > 0:
                lumpsum_growth = L * (1 + r) ** m
                sip_growth = (
                    s * (((1 + r) ** m - 1) / r) * (1 + r)
                    if m > 0
                    else 0
                )
                val = lumpsum_growth + sip_growth
            else:
                val = (
                    s * (((1 + r) ** m - 1) / r) * (1 + r)
                    if m > 0
                    else 0
                )

            total_value.append(val)

        return months, investment, total_value



    def _compute_rolling_sip_xirrs(self, time_horizon: int, sip_amount: float = 1000) -> List[float]:
        """
        Compute XIRRs for rolling SIP windows.
        :param time_horizon: Investment horizon in time_horizon.
        :param sip_amount: SIP amount per month (default: ₹1000).
        :return: List of XIRRs (in %).
        """
        months = time_horizon * 12
        xirrs = []

        for start in range(len(self.df) - months):
            window = self.df.iloc[start:start + months + 1]
            if len(window) < months + 1:
                continue

            dates = list(window['Date'][:months])
            amounts = [-sip_amount] * months

            start_prices = window['Closing Price'].iloc[:months].values
            end_price = window['Closing Price'].iloc[months]

            units = [sip_amount / p for p in start_prices]
            total_units = sum(units)
            maturity_value = total_units * end_price

            dates.append(window['Date'].iloc[months])
            amounts.append(maturity_value)

            try:
                xirr = pyxirr.xirr(dict(zip(dates, amounts))) * 100
                xirrs.append(xirr)
            except Exception:
                continue
        # print("\nXIRRS:")
        # print(xirrs)
        return xirrs
    


    def get_expected_sip_return(
            self,
            time_horizon: int,
            mode: Literal["mean", "median", "optimistic", "pessimistic"] = "mean"
        ) -> float:
        """
        Get the expected return rate based on rolling SIP simulations.
        :param time_horizon: Time horizon (in years).
        :param method: 'median', 'mean', 'pessimistic', or 'optimistic'.
        :return: Estimated return rate (% CAGR).
        """
        xirrs = self._compute_rolling_sip_xirrs(time_horizon)
        if not xirrs:
            raise ValueError(Fore.YELLOW + "[WARNING] Not enough data to compute rolling returns." + Fore.RESET)

        series = pd.Series(xirrs)
        if mode == "median":
            return round(series.median(), 2)
        elif mode == "mean":
            return round(series.mean(), 2)
            # return series.iloc[-1]
        elif mode == "pessimistic":
            return round(series.quantile(0.25), 2)
        elif mode == "optimistic":
            return round(series.quantile(0.75), 2)
        else:
            raise ValueError(Fore.RED + f"[ERROR] Unknown mode '{mode}'. Choose from median, mean, pessimistic, optimistic." + Fore.RESET)
