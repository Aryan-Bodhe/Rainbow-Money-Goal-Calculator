"""
Configuration module for investment portfolio simulations.

This module centralizes:
- Simulation parameters (Monte Carlo settings, target probabilities, etc.)
- Supported user risk profiles and time horizons
- Logging settings and file retention
- Paths to financial data sources
- Predefined portfolio allocations
- Fallback asset return rates

Simulation Parameters
---------------------
NUM_SIMULATIONS : int
    Number of Monte Carlo simulations to run for each scenario.
TARGET_PROB_OF_SUCCESS : float
    Desired probability of achieving the investment target (e.g., 0.90 = 90%).
USER_RISK_PROFILES : list of str
    Supported investment risk profiles. Also used for selecting predefined
    asset allocation mixes.
SIMULATION_TIME_HORIZONS : list of int
    Time horizons (in years) over which simulations are conducted.

Logging Parameters
------------------
LOGGING_DIR : str
    Directory where log files will be stored.
LOGGING_LIMIT_DAYS : int
    Number of days to retain rotated log files.
CREATE_HISTOGRAM : bool
    Whether to generate a histogram of simulated returns.
HISTOGRAM_PATH : str
    File path to save the histogram image.

Data Paths
----------
FOREX_RATES_DIR : str
    Directory containing monthly foreign exchange rate data.
ASSET_NAV_DATA_PATH : dict
    Maps asset names to their corresponding `.feather` NAV data file paths.

Portfolio Definitions
----------------------
CONSERVATIVE_PORTFOLIO : dict
    Asset allocation for conservative investors.
BALANCED_PORTFOLIO : dict
    Asset allocation for balanced investors.
AGGRESSIVE_PORTFOLIO : dict
    Asset allocation for aggressive investors.

Fallback Data
-------------
ASSET_RETURN_RATES : dict
    Default annual return rates for assets if no historical NAV data is found.

Notes
-----
- Ensure all assets referenced in portfolios exist in the NAV data paths.
- Asset weights should sum to 1.0 for each portfolio definition.
"""

import os

# ---------------- Simulation Parameters ----------------

NUM_SIMULATIONS = 5000
"""int: Number of Monte Carlo simulations to run for each investment scenario."""

TARGET_PROB_OF_SUCCESS = 0.90
"""float: Desired probability of achieving the investment target (e.g., 0.90 = 90%)."""

USER_RISK_PROFILES = ['conservative', 'balanced', 'aggressive', 'custom']
"""list[str]: Supported investment risk profiles.
   These determine the asset allocation strategy for simulations."""

SIMULATION_TIME_HORIZONS = [1, 3, 5, 10]
"""list[int]: Investment time horizons in years to run simulations for."""

# ---------------- Logging Parameters ----------------

LOGGING_DIR = "logs/"
"""str: Directory where log files will be stored."""

LOGGING_LIMIT_DAYS = 10
"""int: Number of days to retain rotated log files before deletion."""

CREATE_HISTOGRAM = False
"""bool: Whether to generate a histogram of simulated returns."""

HISTOGRAM_PATH = 'temp/returns_histogram.png'
"""str: File path where the generated returns histogram will be saved."""

# ---------------- Data Paths ----------------

FOREX_RATES_DIR = os.path.join(os.getcwd(), 'data/newfinal/monthly_forex/')
"""str: Directory containing monthly foreign exchange rate data files."""

ASSET_NAV_DATA_PATH = {
    "largecap": os.path.join(os.getcwd(), "data/newfinal/monthly_nav/largecap.feather"),
    "sp_500":   os.path.join(os.getcwd(), "data/newfinal/monthly_nav/sp500.feather"),
    "gold":     os.path.join(os.getcwd(), "data/newfinal/monthly_nav/gold.feather"),
}
"""dict[str, str]: Maps asset identifiers to paths for their monthly NAV `.feather` files."""

# ---------------- Portfolio Definitions ----------------

CONSERVATIVE_PORTFOLIO = {
    "largecap": 0.2,
    "fixed_deposit": 0.6,
    "gold": 0.2
}
"""dict[str, float]: Asset allocation for conservative investors.
   Prioritizes stability and fixed income over high returns."""

BALANCED_PORTFOLIO = {
    "largecap": 0.30,
    "sp_500": 0.20,
    "gold": 0.3,
    "fixed_deposit": 0.2
}
"""dict[str, float]: Asset allocation for balanced investors.
   Seeks a middle ground between growth and risk."""

AGGRESSIVE_PORTFOLIO = {
    "largecap": 0.4,
    "sp_500": 0.3,
    "gold": 0.30
}
"""dict[str, float]: Asset allocation for aggressive investors.
   Focuses on high-growth equities and tolerates higher volatility."""

# ---------------- Fallback Data ----------------

ASSET_RETURN_RATES = {
    "fixed_deposit": 7
}
"""dict[str, float]: Default annual return rates (in %) for assets if no NAV data is found."""
