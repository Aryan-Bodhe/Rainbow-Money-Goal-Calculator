from pydantic import BaseModel
from typing import Union, List
from .asset_summary import AssetSummary
from typing import Optional

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

    months: Optional[List[int]] = None
    cumulative_investment: Optional[List[float]] = None
    cumulative_returns: Optional[List[float]] = None
    rolling_returns: Optional[List[float]] = None
    dates: Optional[List[str]] = None