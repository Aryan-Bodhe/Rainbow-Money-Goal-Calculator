# SIP_Plotter.py

import os
from typing import List

import matplotlib.pyplot as plt
from matplotlib.ticker import (
    MultipleLocator,
    FixedLocator,
    FuncFormatter
)

from source.Portfolio import Portfolio

class SipPlotter:
    """
    A class to visualize SIP portfolio performance (multi-asset) using matplotlib.
    """

    def __init__(self):
        pass

    def plot_returns(self, portfolio: Portfolio) -> None:
        """
        Generate and save a stacked bar chart of total invested vs returns over time,
        with y-axis dynamically scaled into thousands/lakhs, and showing 'cr' when
        100 lakhs is reached. Axis titles and ticks have been enlarged for clarity.
        """
        investment    = portfolio.cumulative_investment
        returns       = portfolio.cumulative_returns
        total_months  = portfolio.time_horizon * 12 + 1
        months        = list(range(total_months))
        goal_amount   = portfolio.goal_amount

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
            ax.set_xticklabels(xtick_labels, color='lightgray', fontsize=14)

        plt.tight_layout(pad=2.0)
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
        Internal helper to render a stacked bar chart on a dark background,
        automatically scaling the y-axis into thousands or lakhs depending on the data.
        - If max_total < 1e5: scale_factor = 1e3  (thousands)
        - If max_total >= 1e5: scale_factor = 1e5 (lakhs)
        Within lakhs, whenever a tick = 100 (i.e. 100 lakhs = 1 cr), we label “1 cr.”
        Axis titles and ticks have been enlarged for better readability.
        """
        # Step 1: Find maximum total value (investment + returns or goal):
        total_series = [inv + ret for inv, ret in zip(investment, returns)]
        max_total    = max(total_series + [goal_amount])

        # Step 2: Decide on scale factor and unit label:
        if max_total >= 1e5:
            # Use lakhs as base unit
            scale_factor = 1e5
            unit_label   = " (in lakhs)"
        elif max_total >= 1e3:
            # Use thousands as base unit
            scale_factor = 1e3
            unit_label   = " (in thousands)"
        else:
            # No scaling needed
            scale_factor = 1.0
            unit_label   = ""

        # Step 3: Scale the data
        scaled_investment = [val / scale_factor for val in investment]
        scaled_returns    = [val / scale_factor for val in returns]
        scaled_goal       = goal_amount / scale_factor

        # Step 4: Create figure + axes, with a slightly smaller size to enlarge fonts
        fig = plt.figure(figsize=(20, 12), facecolor='black')
        ax  = fig.add_subplot(111)
        ax.set_facecolor('#1e1e1e')  # very dark grey

        # Step 5: Plot stacked bars + goal line with neon colors
        ax.bar(
            months,
            scaled_investment,
            label='Invested Amount',
            color="#00B5C9",  # neon cyan
            zorder=3
        )
        ax.bar(
            months,
            scaled_returns,
            bottom=scaled_investment,
            label='Returns (Gain)',
            color="#FFAE00",  # neon yellow
            zorder=4
        )
        ax.axhline(
            y=scaled_goal,
            color='#00FF92',  # neon green
            linestyle='--',
            label='Goal Amount',
            zorder=5
        )

        # Step 6: If goal achieved, draw neon magenta vertical line
        if maturity_month != -1:
            ax.axvline(
                x=maturity_month,
                color='#FF00E1',  # neon magenta
                linestyle='--',
                linewidth=2,
                label=(
                    fr'Goal Achievement in '
                    rf'($\mathbf{{{maturity_month//12}\ yr,\ {maturity_month%12}\ months}}$)'
                ),
                zorder=5
            )

        # Step 7: Style spines and ticks, enlarging tick labels
        for spine in ax.spines.values():
            spine.set_color('gray')
        ax.tick_params(axis='x', colors='lightgray', labelsize=12)
        ax.tick_params(axis='y', colors='lightgray', labelsize=12)

        # Step 8: X/Y labels and title (larger font sizes)
        ax.set_xlabel('Month', color='lightgray', fontsize=16)
        ax.set_ylabel('Total Investment Value' + unit_label, color='lightgray', fontsize=16)
        ax.set_title('SIP Investment vs Returns Over Time', color='lightgray', fontsize=18)

        # Step 9: Grid lines
        ax.grid(color="#3d3d3d", zorder=0)

        # Step 10: X‐limits and X‐ticks (every 6 months)
        ax.set_xlim(left=-1 if left_padding else 0)
        ax.xaxis.set_major_locator(MultipleLocator(6))

        # Step 11: Y‐tick spacing
        if scaled_goal < 10:
            interval = scaled_goal / 10
        else:
            interval = max(int(scaled_goal / 10), 1)
        ax.yaxis.set_major_locator(MultipleLocator(interval))

        # Step 12: Ensure the y-axis starts at zero, so no negative ticks
        ax.set_ylim(bottom=0)

        # Step 13: Custom y‐axis formatter
        def y_formatter(x, _pos):
            """
            - If scale_factor == 1e5 (lakhs):
              • If x ≥ 100 (i.e. 100 lakhs = ₹1 cr), label as “X.Y cr” or “N cr” if integer.
              • If 0 < x < 100 and x is integer, label as integer (meaning lakhs).
              • If 0 < x < 100 and x is fractional, label with one decimal (e.g. 1.5).
            - If scale_factor == 1e3 (thousands):
              • Show the raw rupee amount with commas (e.g. x=50 → “50,000”).
            - If scale_factor == 1.0:
              • Show integer or one decimal if needed.
            """
            ix = float(x)
            if ix < 0:
                return ""  # avoid labeling negative
            if ix == 0:
                return "0"

            # Case A: using lakhs
            if scale_factor == 1e5:
                if ix >= 100:
                    crores_val = ix / 100
                    # If exactly whole crore:
                    if abs(crores_val - round(crores_val)) < 1e-6:
                        return f"{int(round(crores_val))} Cr"
                    else:
                        return f"{crores_val:.1f} Cr"
                # Below 100 lakhs:
                if abs(ix - round(ix)) < 1e-6:
                    return f"{int(round(ix))} L"
                return f"{ix:.1f}"

            # Case B: using thousands
            elif scale_factor == 1e3:
                actual_value = int(round(ix * 1000))
                return f"{actual_value:,} Th"

            # Case C: no scaling
            else:
                if abs(ix - round(ix)) < 1e-6:
                    return f"{int(round(ix))}"
                return f"{ix:.1f}"

        ax.yaxis.set_major_formatter(FuncFormatter(y_formatter))

        # Step 14: Bold the tick corresponding to the goal value
        ticks = ax.get_yticks()
        # Filter out any negative ticks
        nonneg_ticks = [t for t in ticks if t >= 0]
        formatted_labels = [y_formatter(t, None) for t in nonneg_ticks]

        ax.set_yticks(nonneg_ticks)
        ax.set_yticklabels(
            formatted_labels,
            color='lightgray',
            fontsize=14
        )

        for text in ax.get_yticklabels():
            if text.get_text() == y_formatter(scaled_goal, None):
                text.set_fontweight('bold')

        # Step 15: Legend styling
        legend = ax.legend(fontsize=10)
        frame = legend.get_frame()
        frame.set_facecolor('none')
        frame.set_edgecolor('gray')
        for text in legend.get_texts():
            text.set_color('lightgray')
            text.set_fontsize(14)

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
