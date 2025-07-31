# SIP_Goal_Based.py
from typing import Literal

from models.goal_request import AssetAllocation
from config import (
    AGGRESSIVE_PORTFOLIO,
    BALANCED_PORTFOLIO,
    CONSERVATIVE_PORTFOLIO,
    USER_RISK_PROFILES
)

from core.exceptions import (
    InvalidGoalAmountError, 
    InvalidLumpsumAmountError, 
    InvalidRiskProfileError, 
    InvalidTimeHorizonError, 
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
        lumpsum: float,
        risk_profile: Literal['conservative', 'balanced', 'aggressive', 'custom'],
        allocation: AssetAllocation
    ) -> None:
        """
        Directly sets parameters for testing (bypasses console input).
        """
        if goal <= 0:
            raise InvalidGoalAmountError(goal)
        if time_horizon <= 0:
            raise InvalidTimeHorizonError(time_horizon)
        if lumpsum < 0 or lumpsum > goal:
            raise InvalidLumpsumAmountError(lumpsum)

        if risk_profile not in USER_RISK_PROFILES:
            raise InvalidRiskProfileError(risk_profile, USER_RISK_PROFILES)

        self.goal_amount = goal
        self.time_horizon = time_horizon
        self.lumpsum_amount = lumpsum
        self.risk_profile = risk_profile

        if risk_profile == 'conservative':
            self.asset_weights = CONSERVATIVE_PORTFOLIO
        elif risk_profile == 'balanced':
            self.asset_weights = BALANCED_PORTFOLIO
        elif risk_profile == 'aggressive':
            self.asset_weights = AGGRESSIVE_PORTFOLIO
        elif risk_profile == 'custom':
            if allocation is None:
                raise ValueError('Custom Profile without allocation.')
            allocs = {name: weight for name, weight in allocation.model_dump().items() if weight != 0}
            self.asset_weights = allocs
        