# main.py
import os
from datetime import datetime
from typing import Literal
from fastapi import FastAPI, HTTPException
import json

from logger import get_logger
from source.SIP_Goal_Based import SipGoalBased
from source.Asset import Asset
from source.Portfolio import Portfolio
from source.SIP_Plotter import SipPlotter
from config import *
from source.Exceptions import DataFileNotFoundError
from models.goal_request import GoalRequest
from models.portfolio import PortfolioSummary

import time as tm
import tracemalloc

app = FastAPI()

@app.post("/calculate-goal")
def calculate_goal(req: GoalRequest):
    logger = get_logger()
    logger.info('---------- New Request Received ----------')
    try:
        start = tm.time()
        tracemalloc.start()
        result = run_analysis(
            goal_amount=req.goal_amount,
            time_horizon=req.time_horizon,
            lumpsum=req.lumpsum_amount,
            risk_profile=req.risk_profile
        ).model_dump_json()
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        end = tm.time()
        
        logger.info(f"Total Test Runtime: {end - start : 0.3f} s.")
        logger.info(f"Peak memory usage: {peak / 10**6:.3f} MB")
        logger.info('Goal Calculation Completed Successfully.')
        logger.info('------------------------------------------')
        return result
    except DataFileNotFoundError as e:
        logger.exception("Unexpected error during goal calculation.")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error during goal calculation.")
        raise HTTPException(status_code=500, detail="Internal error")
    
def main():
    os.system('clear')
    
    # tracemalloc.start()

    result = calculate_goal(
        GoalRequest(
            goal_amount=1_000_000,
            time_horizon=5,
            lumpsum_amount=750_000,
            risk_profile='balanced'
        )
    )

    # with open('temp.json', 'w') as f:
    #     json.dump(json.loads(result), f, indent=2)

def run_analysis(
    goal_amount: float,
    time_horizon: int,
    lumpsum: float,
    risk_profile: Literal['conservative','balanced','aggressive']
) -> PortfolioSummary:
    
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



# def main():
#     os.system('clear')
    
#     # tracemalloc.start()

#     output = calculate_goal(
#         GoalRequest(
#             goal_amount=1_000_000,
#             time_horizon=5,
#             lumpsum_amount=0,
#             risk_profile='balanced'
#         )
#     )
    
    # for time in [10]:
    #     for risk in USER_RISK_PROFILES:

    #         start = tm.time()
    #         calculate_goal(time_horizon=time, risk_profile=risk)
    #         end = tm.time()
          
    #         current, peak = tracemalloc.get_traced_memory()
    #         print(f"Total Test Runtime: {end - start : 0.3f} s.")
    #         print(f"Peak memory usage: {peak / 10**6:.3f} MB")
    #         # print(f"Current memory usage: {current / 10**6:.3f} MB")
           
    #         print('\n------------------------------------------\n')
    #         # exit(0)
        

    # tracemalloc.stop()

    

    # -------------- Single Parameter Testing ---------------- #

    # # goal-amount testing
    # run_test(goal_amount=1_000_000)
    # run_test(goal_amount=2_500_000)
    # run_test(goal_amount=5_000_000)

    # # time-horizon testing
    # run_test(time_horizon=1)
    # run_test(time_horizon=3)
    # run_test(time_horizon=5)
    
    # # risk-profile testing
    # run_test(risk_profile='conservative')
    # run_test(risk_profile='balanced')
    # run_test(risk_profile='aggressive')

    # # lumpsum-amount testing
    # run_test(lumpsum=1_000_000)
    # run_test(lumpsum=2_500_000)
    # run_test(lumpsum=5_000_000)
    # --------------- Two Parameter Testing ----------------- #


    # --------------- Three Parameter Testing --------------- #



if __name__ == "__main__":
    main()
