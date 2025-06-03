INDEX_MONTHLY_DATA_PATH = {
    "smallcap": "data/final/smallcap.feather",
    "midcap": "data/final/midcap.feather",
    "largecap": "data/final/largecap.feather",
    "debt":    "data/final/debt.feather",
    "gold":    "data/final/gold.feather"
}

NUM_SIMULATIONS = 10000
TARGET_PROB_OF_SUCCESS = 0.95

CONSERVATIVE_PORTFOLIO = {
    "smallcap": 0.05,
    "midcap": 0.05,
    "largecap": 0.20,
    "debt": 0.4,
    "gold": 0.3
}

BALANCED_PORTFOLIO = {
    "smallcap": 0.10,
    "midcap": 0.15,
    "largecap": 0.30,
    "debt": 0.30,
    "gold": 0.15
}

AGGRESSIVE_PORTFOLIO = {
    "smallcap": 0.15,
    "midcap": 0.25,
    "largecap": 0.35,
    "debt": 0.15,
    "gold": 0.10
}

USER_RISK_PROFILES = ['conservative', 'balanced', 'aggressive']