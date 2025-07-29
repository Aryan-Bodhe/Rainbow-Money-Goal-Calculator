from pydantic import BaseModel
from typing import Optional

class AssetSummary(BaseModel):
    name: str
    weight: float
    expected_return: float
    sip_amount: float
