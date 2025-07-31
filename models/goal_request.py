from pydantic import BaseModel
from typing import Literal, Optional

class AssetAllocation(BaseModel):
    largecap: Optional[float] = 0.0
    gold: Optional[float] = 0.0
    sp500: Optional[float] = 0.0
    fixed_deposit: Optional[float] = 0.0

class GoalRequest(BaseModel):
    goal_amount: float = None
    time_horizon: int = None
    lumpsum_amount: float = None
    risk_profile: Literal['conservative', 'balanced', 'aggressive', 'custom'] = None
    asset_allocation: AssetAllocation
