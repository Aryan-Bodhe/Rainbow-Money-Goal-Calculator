
import os
from datetime import datetime
from typing import Literal

from config import ASSET_NAV_DATA_PATH, CREATE_HISTOGRAM, NUM_SIMULATIONS, TARGET_PROB_OF_SUCCESS
from core.asset import Asset
from core.exceptions import DataFileNotFoundError
from core.portfolio import Portfolio
from core.sip_goal_based import SipGoalBased
from core.sip_plotter import SipPlotter
from models.portfolio import PortfolioSummary
from utils.logger import get_logger


def run_analysis(
    goal_amount: float,
    time_horizon: int,
    lumpsum: float,
    risk_profile: Literal['conservative','balanced','aggressive']
) -> PortfolioSummary:
    """
    Orchestrates the entire pipeline for SIP goal analysis:
    1. Initializes SIP plan
    2. Loads asset data
    3. Builds and processes portfolio
    4. Runs simulations and computes probability
    5. Returns final portfolio summary
    """
    logger = get_logger()
    logger.info("Starting run_analysis")

    # 1) Build SIP plan
    try:
        sip_plan = SipGoalBased()
        sip_plan.set_testing_data(
            goal=goal_amount,
            time_horizon=time_horizon,
            lumpsum=lumpsum,
            risk_profile=risk_profile
        )
        logger.info("SIP plan initialized")
    except Exception:
        logger.exception("Failed to initialize SIP plan")
        raise

    # 2) Load assets
    try:
        assets = []
        for name, weight in sip_plan.asset_weights.items():
            if weight == 0:
                continue
            path = ASSET_NAV_DATA_PATH.get(name)
            if not path or not os.path.exists(path):
                msg = f"No data file for asset '{name}': {path}"
                logger.error(msg)
                raise DataFileNotFoundError(name, path)
            assets.append(Asset(name=name, feather_path=path, weight=weight, is_sip_start_of_month=True))
        logger.info("Assets loaded")
    except Exception:
        logger.exception("Asset loading failed")
        raise

    # 3) Build portfolio
    try:
        portfolio = Portfolio(
            goal_amount=sip_plan.goal_amount,
            time_horizon=sip_plan.time_horizon,
            lumpsum_amount=sip_plan.lumpsum_amount,
            assets=assets,
            start_date=datetime.today(),
            risk_profile=sip_plan.risk_profile
        )
        portfolio.check_weights()
        portfolio.convert_assets_to_inr()
        logger.info("Portfolio constructed")
    except Exception:
        logger.exception("Portfolio construction failed")
        raise

    # 4) Compute XIRR & allocations
    try:
        portfolio.compute_asset_xirr(mode='median')
        portfolio.compute_per_asset_sips()
        portfolio.compute_portfolio_rolling_xirr(mode='median')
        logger.info("Computed XIRRs and allocations")
    except Exception:
        logger.exception("XIRR/allocation computation failed")
        raise

    # 5) Simulate growth
    try:
        portfolio.simulate_growth()
        logger.info("Simulated portfolio growth")
    except Exception:
        logger.exception("Growth simulation failed")
        raise

    # 6) Plot histogram (optional)
    if CREATE_HISTOGRAM:
        try:
            SipPlotter().plot_returns(portfolio)
            logger.info("Plotted returns histogram")
        except Exception:
            logger.exception("Histogram plotting failed")
            # non-fatal: continue

    # 7) Probability & SIP suggestion
    try:
        prob = portfolio.probability_of_reaching_goal(
            monthly_sip=portfolio.total_monthly_sip,
            num_simulations=NUM_SIMULATIONS,
            lumpsum=portfolio.lumpsum_amount
        )
        suggested = portfolio.suggest_sip_for_probability(
            target_prob=TARGET_PROB_OF_SUCCESS,
            num_simulations=NUM_SIMULATIONS,
            lumpsum=portfolio.lumpsum_amount
        )
        logger.info(f"Computed Goal Achievement Probability and Suggested SIP.")
    except Exception:
        logger.exception("Probability/SIP suggestion failed")
        raise

    # 8) Summarize and return
    try:
        summary = portfolio.get_portfolio_summary()
        logger.info("Portfolio summary generated")
        return summary
    except Exception:
        logger.exception("Final summary generation failed")
        raise