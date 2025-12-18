from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class FundingData:
    exchange: str
    symbol: str
    funding_rate: float
    funding_time: datetime
    timestamp: datetime
    price: Optional[float] = None
    raw_response: Optional[dict] = None

    def __repr__(self):
        return (f"[{self.exchange}] {self.symbol}: {self.funding_rate:+.6%}"
                f" (Time: {self.funding_time})")
