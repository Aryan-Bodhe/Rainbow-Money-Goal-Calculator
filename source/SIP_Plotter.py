# SIP_Plotter.py

import os
from typing import List
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FixedLocator

from source.Portfolio import Portfolio

class SipPlotter:
    """
    A class to visualize SIP portfolio performance (multi-asset) using matplotlib.
    """

    def __init__(self):
        pass

    def plot_returns(self, portfolio: Portfolio) -> None:
        """
        Generate and save a stacked bar chart of total invested vs returns over time.

        Args:
            portfolio (Portfolio): A Portfolio instance with simulated data.
        """
        investment = portfolio.cumulative_investment
        returns = portfolio.cumulative_returns
        total_months = portfolio.time_horizon * 12 + 1
        months = list(range(total_months))
        goal_amount = portfolio.goal_amount

        maturity_month = self._find_goal_achievement_month(
            investment, returns, goal_amount, months
        )

        padding = (portfolio.lumpsum_amount != 0)

        self._plot_stacked_returns_chart(
            months, investment, returns, goal_amount, maturity_month, padding
        )

        if maturity_month != -1:
            ax = plt.gca()
            xticks = ax.get_xticks()
            xticks_int = [int(round(t)) for t in xticks]
            xtick_labels = [
                f"$\\bf{{{t}}}$" if t == maturity_month else str(t)
                for t in xticks_int
            ]
            ax.xaxis.set_major_locator(FixedLocator(xticks))
            ax.set_xticklabels(xtick_labels)

        plt.tight_layout()
        os.makedirs('./temp', exist_ok=True)
        plt.savefig('./temp/returns_histogram.png', dpi=400)
        plt.close()

    def _plot_stacked_returns_chart(
        self,
        months: List[int],
        investment: List[float],
        returns: List[float],
        goal_amount: float,
        maturity_month: int,
        left_padding: bool
    ) -> None:
        """
        Internal helper to render a stacked bar chart.
        """
        plt.figure(figsize=(20, 12))
        plt.bar(months, investment, label='Invested Amount', color='skyblue', zorder=3)
        plt.bar(months, returns, bottom=investment, label='Returns (Gain)', color='orange', zorder=4)
        plt.axhline(y=goal_amount, color='green', linestyle='--', label='Goal Amount', zorder=5)

        if maturity_month != -1:
            plt.axvline(
                x=maturity_month,
                color='green',
                linestyle='--',
                linewidth=2,
                label=(
                    fr'Goal Achievement in '
                    rf'($\mathbf{{{maturity_month//12}\ yr,\ {maturity_month%12}\ months}}$)'
                ),
                zorder=5
            )

        plt.xlabel('Month')
        plt.ylabel('Total Investment Value')
        plt.title('SIP Investment vs Returns Over Time')
        plt.grid(True, zorder=0)
        plt.xlim(left=-1 if left_padding else 0)
        plt.gca().xaxis.set_major_locator(MultipleLocator(6))

        y_interval = max(int(goal_amount / 10), 1)
        plt.gca().yaxis.set_major_locator(MultipleLocator(y_interval))

        plt.legend()

    def _find_goal_achievement_month(
        self,
        investment: List[float],
        returns: List[float],
        goal_amount: float,
        months: List[int]
    ) -> int:
        """
        Find the first month where (investment + returns) ≥ goal_amount.
        """
        total_values = [inv + ret for inv, ret in zip(investment, returns)]
        for idx, val in enumerate(total_values):
            if val >= goal_amount:
                return months[idx]
        return -1
