from source.SIP_Calculator import SipCalculator
from source.SIP_Plotter import SipPlotter
from source.SIP_Goal_Based import SipGoalBased
from colorama import Fore, init


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


if __name__ == '__main__':
    run_sip_analysis()
