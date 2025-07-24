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
    # "smallcap": 0.0,
    "largecap": 1,
    # "s&p_500":0.1,
    # "midcap": 0.0,
    # "debt": 0.7,
    # "gold": 0.7
}

BALANCED_PORTFOLIO = {
    # "smallcap": 0.0,
    "largecap": 0.30,
    "s&p_500": 0.20,
    # "midcap": 0.15,
    # "debt": 0.30,
    "gold": 0.5
}

AGGRESSIVE_PORTFOLIO = {
    # "smallcap": 0.0,
    "largecap": 0.4,
    "s&p_500": 0.3,
    # "midcap": 0.20,
    # "debt": 0.10,
    "gold": 0.30
}

# Ensure that the asset names here exist in the portfolios
ASSET_NAV_DATA_PATH = {
    # "smallcap": os.path.join(os.getcwd(), "data/final/navs/smallcap.feather"),
    # "midcap":   os.path.join(os.getcwd(), "data/final/navs/midcap.feather"),
    # "largecap": os.path.join(os.getcwd(), "data/final/navs/largecap.feather"),
    # "s&p_500":  os.path.join(os.getcwd(), "data/final/navs/s&p500.feather"),
    # "debt":     os.path.join(os.getcwd(), "data/final/navs/debt.feather"),
    # "gold":     os.path.join(os.getcwd(), "data/final/navs/gold.feather")
    # "smallcap": os.path.join(os.getcwd(), "data/newfinal/"),
    # "midcap":   os.path.join(os.getcwd(), "data/final_syn/midcap.feather"),
    "largecap": os.path.join(os.getcwd(), "data/newfinal/monthly_nav/largecap.feather"),
    "s&p_500":  os.path.join(os.getcwd(), "data/newfinal/monthly_nav/sp500.feather"),
    # "debt":     os.path.join(os.getcwd(), "data/final_syn/debt.feather"),
    "gold":     os.path.join(os.getcwd(), "data/newfinal/monthly_nav/gold.feather")
}