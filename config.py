import os

NUM_SIMULATIONS = 10000
TARGET_PROB_OF_SUCCESS = 0.95
USER_RISK_PROFILES = ['conservative', 'balanced', 'aggressive']

FOREX_RATES_DIR = os.path.join(os.getcwd(), 'data/final/forex/')

# Ensure that the asset names here match with those in the data paths
CONSERVATIVE_PORTFOLIO = {
    "smallcap": 0.05,
    "midcap": 0.05,
    "s&p_500": 0.20,
    "debt": 0.4,
    "gold": 0.3
}

BALANCED_PORTFOLIO = {
    "smallcap": 0.10,
    "midcap": 0.15,
    "s&p_500": 0.30,
    "debt": 0.30,
    "gold": 0.15
}

AGGRESSIVE_PORTFOLIO = {
    "smallcap": 0.15,
    "midcap": 0.25,
    "s&p_500": 0.35,
    "debt": 0.15,
    "gold": 0.10
}

# Ensure that the asset names here match with those in the portfolios
INDEX_MONTHLY_DATA_PATH = {
    "smallcap": os.path.join(os.getcwd(), "data/final/navs/smallcap.feather"),
    "midcap":   os.path.join(os.getcwd(), "data/final/navs/midcap.feather"),
    "s&p_500":  os.path.join(os.getcwd(), "data/final/navs/s&p500.feather"),
    "debt":     os.path.join(os.getcwd(), "data/final/navs/debt.feather"),
    "gold":     os.path.join(os.getcwd(), "data/final/navs/gold.feather")
}