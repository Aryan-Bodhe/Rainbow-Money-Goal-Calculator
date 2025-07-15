from pydantic import BaseModel
from typing import Literal

class GoalRequest(BaseModel):
    goal_amount: float = None
    time_horizon: int = None
    lumpsum_amount: float = None
    risk_profile: Literal['conservative', 'balanced', 'aggressive'] = None
