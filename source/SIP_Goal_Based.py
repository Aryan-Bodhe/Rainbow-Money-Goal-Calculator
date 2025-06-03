# SIP_Goal_Based.py
from typing import Literal

from config import (
    AGGRESSIVE_PORTFOLIO,
    BALANCED_PORTFOLIO,
    CONSERVATIVE_PORTFOLIO,
    USER_RISK_PROFILES
)

from source.Exceptions import (
    InvalidGoalAmountError, 
    InvalidLumpsumAmountError, 
    InvalidRiskProfileError, 
    InvalidTimeHorizonError, 
    TimeHorizonNotIntegerError
)

class SipGoalBased:
    """
    Collects and validates user inputs for a goal-based SIP.
    Responsible only for:
      - goal_amount (₹)
      - time_horizon (years)
      - lumpsum_amount (₹)
      - risk_profile ('conservative', 'balanced', 'aggressive')
      - computing asset_weights based on risk_profile
    """

    def __init__(self):
        self.goal_amount: float = 0.0
        self.time_horizon: int = 0
        self.lumpsum_amount: float = 0.0
        self.risk_profile: str | None = None
        self.asset_weights: dict[str, float] = {}


    def set_testing_data(
        self,
        goal: float,
        time_horizon: int,
        lumpsum: float = 0.0,
        risk_profile: Literal['conservative', 'balanced', 'aggressive'] = 'conservative'
    ) -> None:
        """
        Directly sets parameters for testing (bypasses console input).
        """
        if goal <= 0:
            # raise ValueError("[ERROR] Goal must be > 0.")
            raise InvalidGoalAmountError(goal)
        if time_horizon <= 0:
            # raise ValueError("[ERROR] Time horizon must be > 0.")
            raise InvalidTimeHorizonError(time_horizon)
        if lumpsum < 0 or lumpsum > goal:
            # raise ValueError("[ERROR] Lumpsum must be ≥ 0 and ≤ goal.")
            raise InvalidLumpsumAmountError(lumpsum)

        if risk_profile not in USER_RISK_PROFILES:
            # raise ValueError("[ERROR] Invalid risk profile.")
            raise InvalidRiskProfileError(risk_profile, USER_RISK_PROFILES)

        self.goal_amount = goal
        self.time_horizon = time_horizon
        self.lumpsum_amount = lumpsum
        self.risk_profile = risk_profile

        if risk_profile == 'conservative':
            self.asset_weights = CONSERVATIVE_PORTFOLIO
        elif risk_profile == 'balanced':
            self.asset_weights = BALANCED_PORTFOLIO
        else:
            self.asset_weights = AGGRESSIVE_PORTFOLIO
        

    def input_sip_data(self) -> None:
        """
        Prompts the user for goal, horizon, lumpsum, and allocates weights by risk profile.
        Raises ValueError on invalid inputs.
        """
        # Validate Goal Amount
        goal = float(input("Enter the goal amount (₹): "))
        if goal <= 0:
            # raise ValueError("[ERROR] Goal Amount must be greater than 0.")
            raise InvalidGoalAmountError(goal)

        # Validate Time Horizon
        th = float(input("Enter the investment duration (years): "))
        if th <= 0 or int(th) != th:
            # raise ValueError("[ERROR] Time horizon must be a positive integer.")
            raise TimeHorizonNotIntegerError(th)
        th_int = int(th)

        # Validate Lumpsum Amount
        lump = float(input("Enter lumpsum investment amount (₹): "))
        if lump < 0 or lump > goal:
            # raise ValueError("[ERROR] Lumpsum must be ≥ 0 and ≤ goal amount.")
            raise InvalidLumpsumAmountError(lump, goal)

        # Select Risk Profile
        rp = input("Enter risk profile ('conservative','balanced','aggressive'): ").lower()
        
        if rp not in USER_RISK_PROFILES:
            # raise ValueError("[ERROR] Invalid risk profile.")
            raise InvalidRiskProfileError(rp, USER_RISK_PROFILES)

        # Set attributes
        self.goal_amount = goal
        self.time_horizon = th_int
        self.lumpsum_amount = lump
        self.risk_profile = rp

        # Determine asset_weights based on rp
        if rp == 'conservative':
            self.asset_weights = CONSERVATIVE_PORTFOLIO
        elif rp == 'balanced':
            self.asset_weights = BALANCED_PORTFOLIO
        else:  
            self.asset_weights = AGGRESSIVE_PORTFOLIO


    def display_sip_data(self) -> None:
        """
        Prints the user’s inputs and resulting asset weights.
        """
        print("\n----------------------------------------------------")
        print("SIP Inputs & Asset Weights:")
        print(f"Target Goal Amount   : ₹{self.goal_amount:,.2f}")
        print(f"Investment Duration  : {self.time_horizon} years")
        print(f"Lumpsum Amount       : ₹{self.lumpsum_amount:,.2f}")
        print(f"Risk Profile         : {self.risk_profile.capitalize()}")
        print("Asset Allocation (%):")
        for asset, wt in self.asset_weights.items():
            print(f"  • {asset.capitalize():<10} : {wt*100:.2f}%")
        print("----------------------------------------------------\n")
