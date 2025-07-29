from pydantic import BaseModel
from typing import Union, List
from .asset_summary import AssetSummary

class PortfolioSummary(BaseModel):
    goal_amount: float
    time_horizon: int
    lumpsum_amount: float
    total_monthly_sip: Union[float, str]
    risk_profile: str
    portfolio_growth: float
    asset_summaries: List[AssetSummary]
    rolling_xirr: float
    goal_achievement_probability: float
    suggested_sip: Union[float, str]