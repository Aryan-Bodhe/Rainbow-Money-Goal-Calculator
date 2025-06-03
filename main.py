# main.py
import sys
from datetime import datetime
import os
from typing import Literal

from source.SIP_Goal_Based import SipGoalBased
from source.Asset import Asset
from source.Portfolio import Portfolio
from source.SIP_Plotter import SipPlotter
from config import *
from source.Exceptions import DataFileNotFoundError

test_id = 1
ENABLE_LOGGING = True


def run_test(
        goal_amount: float = 10_000_000,
        time_horizon: int = 10,
        lumpsum: float = 0.0,
        risk_profile: Literal['conservative', 'balanced', 'aggressive'] = 'conservative'
    ):
    
    if ENABLE_LOGGING:
        testname = f'logs/testing_g{str(goal_amount)}_t{str(time_horizon)}_l{str(lumpsum)}_{str(risk_profile)}'
        sys.stdout = open(testname+'.txt', 'w')

    # 1) Collect or set SIP inputs
    sip_plan = SipGoalBased()

    # If you want interactive input, uncomment:
    # sip_plan.input_sip_data()

    # For testing purposes:
    sip_plan.set_testing_data(
        goal=goal_amount,        
        time_horizon=time_horizon, 
        lumpsum=lumpsum,         
        risk_profile=risk_profile  
    )
    # sip_plan.display_sip_data()

    # 2) Build Asset instances from sip_plan.asset_weights
    assets = []
    for name, weight in sip_plan.asset_weights.items():
        feather_path = INDEX_MONTHLY_DATA_PATH.get(name)
        if not feather_path or not os.path.exists(feather_path):
            # raise FileNotFoundError(f"No Feather file found for asset '{name}': {feather_path}")
            raise DataFileNotFoundError(name, feather_path)

        assets.append(
            Asset(
                name=name,
                feather_path=feather_path,
                weight=weight,
                is_sip_start_of_month=True
            )
        )

    # 3) Create the Portfolio
    portfolio = Portfolio(
        goal_amount=sip_plan.goal_amount,
        time_horizon=sip_plan.time_horizon,
        lumpsum_amount=sip_plan.lumpsum_amount,
        assets=assets,
        start_date=datetime.today(),
        risk_profile=sip_plan.risk_profile
    )

    # 4) Compute per-asset expected returns (rolling SIP XIRR)
    portfolio.compute_asset_expected_returns(mode="median")

    # 5) Compute per-asset SIP allocations & total SIP
    portfolio.compute_per_asset_sips()
    # print(f"Total Monthly SIP across all assets: ₹{portfolio.total_monthly_sip:,.2f}")

    # 6) Compute each asset’s forward‐looking XIRR
    portfolio.compute_asset_xirrs()

    # 7) Compute portfolio‐level forward‐looking XIRR
    portfolio.compute_portfolio_xirr()
    # print(f"Portfolio XIRR (combined): {overall_xirr:.2f}%")

    # 8) Simulate month‐by‐month growth (investment vs returns)
    portfolio.simulate_growth()
    # print(f'Portfolio Growth : {(total_value[-1]/investment[-1] - 1)*100:0.2f}%.')

    # 9) Display summary 
    portfolio.display_summary()

    # 10) Create returns plot and save
    # plotter = SipPlotter()
    # plotter.plot_returns(portfolio)
    # print("Plot saved to './temp/returns_histogram.png'\n")

    # # 11) Estimate probability of reaching the goal with current SIP
    prob = portfolio.probability_of_reaching_goal(
        monthly_sip=portfolio.total_monthly_sip, 
        num_simulations=10_000, 
        lumpsum=portfolio.lumpsum_amount
    )

    # # 12) Suggest a new SIP for 95% probability
    suggested_sip = portfolio.suggest_sip_for_probability(
        target_prob=TARGET_PROB_OF_SUCCESS,
        num_simulations=NUM_SIMULATIONS,
        lumpsum=portfolio.lumpsum_amount
    )

    print(f"Probability of reaching ₹{portfolio.goal_amount:,.0f} in {portfolio.time_horizon} years: {prob*100:.2f}%")
    print(f"Suggested total monthly SIP for 95% probability: ₹{suggested_sip:,.2f}")

    if ENABLE_LOGGING:
        sys.stdout = sys.__stdout__
        global test_id
        print(f'Test {test_id} complete : {testname}')
        test_id += 1


def main():
    # default test
    # goal = 1cr, time = 10, lumpsum = 0, risk = conservative
    # run_test()

    # -------------- Single Parameter Testing ---------------- #

    # # goal-amount testing
    run_test(goal_amount=1_000_000)
    run_test(goal_amount=2_500_000)
    run_test(goal_amount=5_000_000)

    # # time-horizon testing
    run_test(time_horizon=1)
    run_test(time_horizon=3)
    run_test(time_horizon=5)
    
    # # risk-profile testing
    run_test(risk_profile='conservative')
    run_test(risk_profile='balanced')
    run_test(risk_profile='aggressive')

    # # lumpsum-amount testing
    run_test(lumpsum=1_000_000)
    run_test(lumpsum=2_500_000)
    run_test(lumpsum=5_000_000)


    # --------------- Two Parameter Testing ----------------- #


    # --------------- Three Parameter Testing --------------- #



if __name__ == "__main__":
    main()
