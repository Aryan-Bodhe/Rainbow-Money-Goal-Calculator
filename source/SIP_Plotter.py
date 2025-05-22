import os
from typing import Tuple, List
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FixedLocator
from source.SIP_Goal_Based import SipGoalBased as SGP

class SipPlotter:
    """
    A class to visualize SIP (Systematic Investment Plan) portfolio performance
    and identify goal achievement using matplotlib.
    """

    def __init__(self):
        pass

    def plot_returns(self, sip_plan: SGP) -> None:
        """
        Generate and save a bar chart of investment and returns over time.

        Args:
            sip_plan (SGP): An instance of SipGoalBased containing SIP details.
        """
        months, investment, total_value = self._simulate_portfolio_returns(sip_plan)
        
        # Compute returns = total_value - invested amount
        # Clamp any near-zero negative returns (likely due to float precision) to 0
        returns = [tv - inv for tv, inv in zip(total_value, investment)]
        returns = [ret if ret > 1e-6 else 0 for ret in returns]

        # Determine the month where the goal is achieved
        maturity_month = self._find_goal_achievement_month(
            investment, returns, sip_plan.goal_amount, months
        )

        # Padding needed for graph aesthetics if there's a lumpsum
        padding = sip_plan.lumpsum_amount != 0

        # Create the plot
        self._plot_stacked_returns_chart(
            months, investment, returns, sip_plan.goal_amount, maturity_month, padding
        )

        # Bold the maturity month label on the x-axis
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

        # Save plot in a temp directory
        os.makedirs('./temp', exist_ok=True)
        plt.savefig('./temp/returns_histogram.png', dpi=400)
        plt.close()

    def _plot_stacked_returns_chart(
        self, months: List[int], investment: List[float],
        returns: List[float], goal_amount: float,
        maturity_month: int, left_padding: bool
    ) -> None:
        """
        Internal helper to render a stacked bar chart of investments and returns.

        Args:
            months (List[int]): X-axis time in months.
            investment (List[float]): Monthly invested values.
            returns (List[float]): Monthly returns.
            goal_amount (float): Target goal value.
            maturity_month (int): Month when the goal is achieved, -1 if not achieved.
            left_padding (bool): Whether to allow -1 as x-axis min (for lumpsum start).
        """
        plt.figure(figsize=(20, 12))
        plt.bar(months, investment, label='Invested Amount', color='skyblue', zorder=3)
        plt.bar(months, returns, bottom=investment, label='Returns (Gain)', color='orange', zorder=4)
        plt.axhline(y=goal_amount, color='green', linestyle='--', label='Goal Amount', zorder=5)

        # Draw vertical line on goal achievement month
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

        # Set x-axis range
        plt.xlim(left=-1 if left_padding else 0)

        # Set x-axis ticks every 6 months
        plt.gca().xaxis.set_major_locator(MultipleLocator(6))

        # Set y-axis ticks dynamically based on goal
        y_interval = max(int(goal_amount / 10), 1)
        plt.gca().yaxis.set_major_locator(MultipleLocator(y_interval))

        plt.legend()

    def _simulate_portfolio_returns(
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

    def _find_goal_achievement_month(
        self, investment: List[float], returns: List[float],
        goal_amount: float, months: List[int]
    ) -> int:
        """
        Find the first month where investment value meets or exceeds the goal.

        Args:
            investment (List[float]): Invested amounts.
            returns (List[float]): Returns.
            goal_amount (float): Goal target.
            months (List[int]): Corresponding month numbers.

        Returns:
            int: Month index of goal achievement, or -1 if never achieved.
        """
        total_values = [inv + ret for inv, ret in zip(investment, returns)]
        for idx, val in enumerate(total_values):
            if val >= goal_amount:
                return months[idx]
        return -1
