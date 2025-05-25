from source.SIP_Return_Forecaster import SIPReturnForecaster as SRF
from colorama import Fore
from config import INDEX_MONTHLY_DATA_PATH

class SipGoalBased:
    """
    A class to store and manage the parameters of a goal-based SIP (Systematic Investment Plan).

    Attributes:
        goal_amount (float): The target corpus the investor aims to accumulate.
        time_horizon (int): Investment duration in years.
        return_rate (float): Expected annual return (CAGR) in percentage.
        lumpsum_amount (float): Initial lumpsum amount invested.
        monthly_sip (float): Monthly SIP investment required to reach the goal.
        xirr_value (float): Effective annualized return (XIRR) based on all cashflows.
    """

    def __init__(self):
        """
        Initializes the SIP parameters with default values (0).
        """
        self.goal_amount = 0
        self.time_horizon = 0
        self.return_rate = 0
        self.lumpsum_amount = 0
        self.monthly_sip = 0
        self.xirr_value = 0
        self.cumulative_investment = []
        self.cumulative_returns = []

    def input_sip_data(self) -> None:
        """
        Collects SIP-related inputs from the user via the console.

        Raises:
            ValueError: If any input is invalid, such as non-positive goal/return/time,
                        non-integer time, negative or excessive lumpsum, or if the
                        lumpsum alone is sufficient to meet the goal.
        """

        # Validate Goal Amount
        goal_amount = float(input("Enter the goal amount (in rupees): "))
        if goal_amount <= 0:
            raise ValueError("[ERROR] Goal Amount must be greater than 0.")
        
        # DEPRECATED
        # Validate Return Rate
        # rate = float(input("Enter the expected CAGR rate (in percentage): "))
        # if rate <= 0:
        #     raise ValueError("[ERROR] Rate must be greater than 0")
        

        # Validate Time Horizon
        time_horizon = float(input("Enter the investment duration (in years): "))
        if time_horizon <= 0:
            raise ValueError("[ERROR] Time horizon must be greater than 0.")
        if int(time_horizon) != time_horizon:
            raise ValueError("[ERROR] Time duration must be integral.")
        time_horizon = int(time_horizon)
        

        # Validate Lumpsum Amount
        lumpsum = float(input("Enter lumpsum investment amount (in rupees): "))
        if lumpsum < 0:
            raise ValueError("[ERROR] Lumpsum amount must be greater than or equal to 0.")
        if lumpsum > goal_amount:
            raise ValueError("[ERROR] Lumpsum amount cannot exceed goal amount.")
        

        # Get expected return rate
        expected_rate = 8 # fallback
        forecaster = None
        try:
            forecaster = SRF(INDEX_MONTHLY_DATA_PATH)
        except FileNotFoundError as e:
            print(Fore.RED + "[ERROR] Specified file not found." + Fore.RESET)

        try:
            expected_rate = forecaster.get_expected_sip_return(time_horizon=time_horizon)
        except ValueError as e:
            expected_rate = float(input("Enter the expected CAGR rate (in percentage): "))
            if expected_rate <= 0:
                raise ValueError("[ERROR] Rate must be greater than 0")
            print(e)
        # except Exception as e:
            # print(Fore.RED + str(e) + Fore.RESET)
            # Validate Inputted Return Rate
        finally:
            del forecaster

        
        # Check if future value of lumpsum alone meets or exceeds the goal
        future_lumpsum = lumpsum * (1 + expected_rate / 100) ** time_horizon
        if future_lumpsum >= goal_amount:
            raise ValueError("[ERROR] Investment of Lumpsum alone meets the goal. No SIP needed.")


        # Set valid user inputs to class attributes
        self.goal_amount = goal_amount
        self.return_rate = expected_rate
        self.time_horizon = time_horizon
        self.lumpsum_amount = lumpsum


    def set_testing_data(self, goal, time_horizon,  lumpsum=0):
        self.goal_amount = goal
        self.time_horizon = time_horizon
        self.lumpsum_amount = lumpsum

    def display_sip_data(self) -> None:
        """
        Displays a summary of the SIP plan including inputs and calculated outputs.
        """
        forecaster = SRF(INDEX_MONTHLY_DATA_PATH)
        print("\n----------------------------------------------------")
        print("SIP Details:")
        print(f"Target Goal Amount : {self.goal_amount}.")
        print(f"Investment Duration : {self.time_horizon} years.")
        # print(f"Expected SIP Return Rate (XIRR) : {self.return_rate :.2f}%.")
        print(f"Lumpsum Amount Invested : {self.lumpsum_amount}.")        
        # print(f"XIRR : {self.xirr_value:.2f}%")
        print(f"\nMonthly SIP amount : {self.monthly_sip:.2f}")
        print(f"Total SIP Amount : {self.monthly_sip * self.time_horizon * 12:.2f}")
        print(f"Total Investment Amount : {self.lumpsum_amount + self.monthly_sip * self.time_horizon * 12:.2f}")
        print(f"Portfolio Returns (Ratio of total_returns to total_investment) : {self.cumulative_returns[-1]/(self.cumulative_investment[-1] + 1e6)*100 : .2f}%")
        print()
        print(f"Portfolio XIRR (Worst Case) : {forecaster.get_expected_sip_return(time_horizon=self.time_horizon, mode="pessimistic")}%")
        print(f"Portfolio XIRR (Median)  : {forecaster.get_expected_sip_return(time_horizon=self.time_horizon, mode="median")}%")
        print(f"Portfolio XIRR (Best Case) : {forecaster.get_expected_sip_return(time_horizon=self.time_horizon, mode="optimistic")}%")
        # print("----------------------------------------------------\n")
        
        del forecaster
