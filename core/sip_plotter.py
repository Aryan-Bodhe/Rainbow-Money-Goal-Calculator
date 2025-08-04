import json
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
        rows=1, cols=2,
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
        row=1, col=2
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
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(
            x=[median_val, median_val], y=[0, counts.max()],
            mode="lines",
            line=dict(color="brown", dash="dot"),
            name="Median",
            hovertemplate="Median: %{x:.2f}%<extra></extra>"
        ),
        row=1, col=2
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
    fig.update_xaxes(title_text="Rolling Returns %",  row=1, col=2)
    fig.update_yaxes(title_text="Frequency",       row=1, col=2)
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


def generate_returns_html(rolling_returns, dates=None):
    if not rolling_returns:
        return """
        <div style="display:flex;justify-content:center;align-items:center;height:100%">
            <p style="color:#666;text-align:center">
                No rolling returns data available.<br>
                Try calculating the goal again.
            </p>
        </div>
        """

    fig = build_plotly_fig(rolling_returns, dates)

    # Grab exactly the same snippet you used before
    snippet = fig.to_html(include_plotlyjs="cdn", full_html=False)

    # Inject it into the wrapper above
    html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
            html, body {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
            }}
            #graph {{
                position: relative;
                width: 100%;
                height: 100%;
                display: block;
            }}
            #graph .plotly-graph-div,
            #graph .js-plotly-plot {{
                position: absolute !important;
                top: 0 !important;
                left: 0 !important;
                width: 100% !important;
                height: 100% !important;
            }}
            </style>
        </head>
        <body>
            <div id="graph">
            {snippet}
            </div>
        </body>
        </html>
    """
    return html
