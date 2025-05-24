from source.SIP_Calculator import SipCalculator
from source.SIP_Plotter import SipPlotter
from source.SIP_Goal_Based import SipGoalBased
from source.SIP_Return_Forecaster import SIPReturnForecaster
from colorama import Fore, init
from config import INDEX_MONTHLY_DATA_PATH


def run_sip_analysis():
    """
    Main driver function to run SIP goal-based analysis:
    - Takes user input for SIP configuration.
    - Computes SIP amount and XIRR.
    - Displays the SIP summary.
    - Plots investment vs returns over time.
    """
    # Initialize color formatting for terminal output
    init(autoreset=True)

    # Initialize core components
    sip_calc = SipCalculator()
    sip_plotter = SipPlotter()
    sip_plan = SipGoalBased()

    # Step 1: Input SIP details from the user
    try:
        sip_plan.input_sip_data()
    except ValueError as e:
        print(Fore.RED + str(e))
        return  # Exit on invalid input

    # Step 2: Compute required monthly SIP amount
    try:
        sip_plan.monthly_sip = sip_calc.compute_monthly_sip(sip_plan)
    except ValueError as e:
        print(Fore.RED + str(e))
        return

    # Step 3: Compute XIRR for the cashflows
    try:
        sip_plan.xirr_value = sip_calc.compute_xirr(sip_plan)
    except ValueError as e:
        print(Fore.RED + str(e))
        return

    # Step 4: Display SIP summary and plot results
    sip_plan.display_sip_data()
    sip_plotter.plot_returns(sip_plan)

def run_sip_testing():
    # Initialize color formatting for terminal output
    init(autoreset=True)

    # Initialize core components
    sip_calc = SipCalculator()
    sip_plotter = SipPlotter()
    sip_plan = SipGoalBased()
    forecaster = SIPReturnForecaster(INDEX_MONTHLY_DATA_PATH)

    goal = 10000000
    times = [1,3,5,10]
    

    for time in times:
        try:
            sip_plan.set_testing_data(goal=goal, time_horizon=time)
        except ValueError as e:
            print(Fore.RED + str(e))
            return  # Exit on invalid input
        
        sip_plan.return_rate = forecaster.get_expected_sip_return(time_horizon=sip_plan.time_horizon, mode='mean')

        # Step 2: Compute required monthly SIP amount
        try:
            sip_plan.monthly_sip = sip_calc.compute_monthly_sip(sip_plan)
        except ValueError as e:
            print(Fore.RED + str(e))
            return

        # Step 3: Compute XIRR for the cashflows
        try:
            sip_plan.xirr_value = sip_calc.compute_xirr(sip_plan)
        except ValueError as e:
            print(Fore.RED + str(e))
            return
        
        _, investment, total_value = forecaster.simulate_portfolio_returns(sip_plan=sip_plan)
        returns = [tv - inv for tv, inv in zip(total_value, investment)]
        returns = [ret if ret > 1e-6 else 0 for ret in returns]
        sip_plan.cumulative_investment = investment
        sip_plan.cumulative_returns = returns

        # print("Investments")
        # print(sip_plan.cumulative_investment)
        # print("Returns")
        # print(sip_plan.cumulative_returns)

        # Step 4: Display SIP summary and plot results
        sip_plan.display_sip_data()
        sip_plotter.plot_returns(sip_plan)    


if __name__ == '__main__':
    run_sip_testing()
