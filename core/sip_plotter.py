# # SIP_Plotter.py

# import os
# from typing import List
# import numpy as np
# import matplotlib.pyplot as plt
# import seaborn as sns
# import matplotlib.dates as mdates
# import pandas as pd

# import matplotlib.pyplot as plt
# from matplotlib.ticker import (
#     MultipleLocator,
#     FixedLocator,
#     FuncFormatter
# )

# class SipPlotter:
#     """
#     A class to visualize SIP portfolio performance (multi-asset) using matplotlib.
#     """

#     def __init__(self):
#         pass


#     def plot_rolling_returns(self, rolling_returns, dates=None, bins=20, kde_bw=0.7):
#         """
#         Plots side-by-side:
#         1) Distribution of rolling returns (histogram + KDE) with mode & median
#         2) Trendline of rolling returns over time or index
        
#         Parameters
#         ----------
#         rolling_returns : list, ndarray, or pd.Series
#             Sequence of numeric rolling-return values.
#         dates : list of datetime, pd.DatetimeIndex, or None
#             Matching dates for each return. If None, uses integer index [0,1,2...].
#         bins : int
#             Number of bins for the histogram.
#         kde_bw : float
#             Bandwidth adjustment for the KDE curve (smaller → less smooth).
#         """
#         # Convert to NumPy array
#         rr = np.asarray(rolling_returns)
#         n = rr.shape[0]
        
#         # Compute mode via the highest-count bin
#         counts, edges = np.histogram(rr, bins=bins)
#         mode_idx = np.argmax(counts)
#         mode_val = (edges[mode_idx] + edges[mode_idx+1]) / 2
#         median_val = np.median(rr)
        
#         # Prepare x-axis for trendline
#         if dates is not None:
#             x = pd.to_datetime(dates)
#             use_dates = True
#         else:
#             x = np.arange(n)
#             use_dates = False
        
#         # Aesthetic theme
#         sns.set_theme(style="whitegrid", font_scale=1.1)
        
#         # Figure & axes
#         fig, (ax_dist, ax_trend) = plt.subplots(
#             1, 2, figsize=(14,5), 
#             gridspec_kw={"width_ratios":[1,1.2]}
#         )
        
#         # 1) Histogram + KDE
#         plt.figure(figsize=(12,10))
#         sns.histplot(rr, bins=bins, alpha=0.6, edgecolor="black", ax=ax_dist)
#         sns.kdeplot(rr, bw_adjust=kde_bw, ax=ax_dist, color="navy", linewidth=2)
#         ax_dist.axvline(mode_val, color="purple", linestyle="-.", label="Mode")
#         ax_dist.axvline(median_val, color="brown",  linestyle=":",  label="Median")
#         ax_dist.set_title("Distribution of Rolling Returns", pad=15)
#         ax_dist.set_xlabel("Rolling Return")
#         ax_dist.set_ylabel("Frequency / Density")
#         ax_dist.legend()
#         ax_dist.tick_params(axis="x", rotation=0)
        
#         # 2) Trendline
#         ax_trend.plot(x, rr, marker="o", linewidth=2, markersize=4)
#         if use_dates:
#             ax_trend.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
#         ax_trend.tick_params(axis="x", rotation=0)
#         ax_trend.set_title("Rolling Returns Over Time", pad=15)
#         ax_trend.set_xlabel("Date" if use_dates else "Index")
#         ax_trend.set_ylabel("Rolling Return")
#         ax_trend.grid(True, linestyle="--", alpha=0.5)
        
#         # Super-title and layout
#         fig.suptitle("Rolling Returns: Distribution and Trend", fontsize=16, y=1.02)
#         fig.tight_layout()
#         plt.savefig('freq_dist_chart.png', dpi=400)
#         plt.show()

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

app = FastAPI()

def build_plotly_fig(rolling_returns, dates=None, bins=20, kde_bw=0.7):
    """
    Returns a Plotly Figure with:
      • Left: Histogram + KDE (mode & median)
      • Right: Trendline (Mon DD labels or index)
      • Responsive layout settings
    """
    rr = np.asarray(rolling_returns)
    # compute mode & median
    counts, edges = np.histogram(rr, bins=bins)
    mode_idx   = np.argmax(counts)
    mode_val   = (edges[mode_idx] + edges[mode_idx+1]) / 2
    median_val = np.median(rr)

    # x‑axis values
    if dates is not None:
        x_vals = pd.to_datetime(dates)
        x_title = "Date"
    else:
        x_vals = list(range(len(rr)))
        x_title = "Index"

    # Subplot figure
    fig = make_subplots(
        rows=2, cols=1,
        # column_widths=[0.6, 0.4],
        subplot_titles=("Rolling Returns Over Time", "Distribution of Rolling Returns")
    )

    # Histogram
    fig.add_trace(
        go.Histogram(
            x=rr,
            xbins=dict(
                start=edges[0],
                end=edges[-1],
                size=edges[1] - edges[0]
            ),
            nbinsx=bins,
            opacity=0.6,
            marker_line_color="black",
            name="Histogram",
            marker_line_width=1,      
            hovertemplate="Range: %{x:.2f}%, Count: %{y}<extra></extra>"
        ),
        row=2, col=1
    )

    # Mode & Median
    fig.add_trace(
        go.Scatter(
            x=[mode_val, mode_val], y=[0, counts.max()],
            mode="lines",
            line=dict(color="purple", dash="dashdot"),
            name="Mode",
            hovertemplate="Mode: %{x:.2f}%<extra></extra>"
        ),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=[median_val, median_val], y=[0, counts.max()],
            mode="lines",
            line=dict(color="brown", dash="dot"),
            name="Median",
            hovertemplate="Median: %{x:.2f}%<extra></extra>"
        ),
        row=2, col=1
    )

    #---------------------------
    # Second Plot
    fig.add_trace(
        go.Scatter(
            x=x_vals, y=rr,
            mode="lines",
            marker=dict(size=6),
            line=dict(width=2, color='green'),
            name="Rolling Return",
            fill='tozeroy',  # Fills down to the x-axis
            fillcolor='rgba(0, 100, 0, 0.3)',  # Light green shadow
        ),
        row=1, col=1
    )

    # Layout & formatting
    fig.update_xaxes(title_text=x_title, row=1, col=1)
    fig.update_yaxes(title_text="Rolling Returns %",  row=1, col=1)
    fig.update_xaxes(title_text="Rolling Returns %",  row=2, col=1)
    fig.update_yaxes(title_text="Frequency",       row=2, col=1)
    fig.update_layout(xaxis=dict(type='date'))
    fig.update_layout(
        legend=dict(
            x=0.02,         # x position (0 to 1, from left to right)
            y=0.98,         # y position (0 to 1, from bottom to top)
            bgcolor='rgba(255,255,255,0.5)',  # Optional: semi-transparent background
            bordercolor='black',
            borderwidth=1,
            font=dict(size=12),
        )
    )
    fig.update_layout(
        hovermode="x unified",
        autosize=True,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    return fig

@app.post("/rolling-returns-spec")
async def rolling_returns_spec(payload: dict):
    """
    Request JSON: { "returns": [..], "dates": [..] }  # dates optional
    Response JSON: Plotly figure spec (data + layout)
    """
    returns = payload.get("returns")
    if returns is None:
        raise HTTPException(400, "Missing 'returns' array")
    dates = payload.get("dates", None)
    fig = build_plotly_fig(returns, dates)
    # Return the full figure spec as JSON
    return JSONResponse(status_code=200, content=fig.to_dict())

