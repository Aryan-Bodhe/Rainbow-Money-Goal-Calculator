import os

NUM_SIMULATIONS = 5000
TARGET_PROB_OF_SUCCESS = 0.90
USER_RISK_PROFILES = ['conservative', 'balanced', 'aggressive']     # ['conservative', 'balanced', 'aggressive']
SIMULATION_TIME_HORIZONS = [1,3,5,10]   # [1,3,5,10]
LOGGING_DIR = "logs/"
LOGGING_LIMIT_DAYS = 10
CREATE_HISTOGRAM = False

HISTOGRAM_PATH = 'temp/returns_histogram.png'
FOREX_RATES_DIR = os.path.join(os.getcwd(), 'data/newfinal/monthly_forex/')

# Ensure that the asset names exist in the data paths
CONSERVATIVE_PORTFOLIO = {
    "largecap": 0.2,
    "fixed_deposit": 0.6,
    "gold": 0.2
}

BALANCED_PORTFOLIO = {
    "largecap": 0.30,
    "s&p_500": 0.20,
    "gold": 0.3,
    "fixed_deposit": 0.2
}

AGGRESSIVE_PORTFOLIO = {
    "largecap": 0.4,
    "s&p_500": 0.3,
    "gold": 0.30
}

# Used if data file for asset not found
ASSET_RETURN_RATES = {
    "fixed_deposit": 7
}

# Ensure that the asset names here exist in the portfolios
ASSET_NAV_DATA_PATH = {
    "largecap": os.path.join(os.getcwd(), "data/newfinal/monthly_nav/largecap.feather"),
    "s&p_500":  os.path.join(os.getcwd(), "data/newfinal/monthly_nav/sp500.feather"),
    "gold":     os.path.join(os.getcwd(), "data/newfinal/monthly_nav/gold.feather"),
}