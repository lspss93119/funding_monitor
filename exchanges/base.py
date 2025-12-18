from abc import ABC, abstractmethod
from typing import List, Dict
import aiohttp
from models import FundingData

class BaseExchange(ABC):
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url

    @abstractmethod
    async def get_funding_rates(self, symbols: List[str]) -> List[FundingData]:
        """Fetch current funding rates for specific symbols."""
        pass

    async def _fetch_json(self, session: aiohttp.ClientSession, endpoint: str, params: Dict = None) -> Dict:
        url = f"{self.base_url}{endpoint}"
        headers = {"User-Agent": "Mozilla/5.0"}
        async with session.get(url, params=params, headers=headers, timeout=20) as response:
            response.raise_for_status()
            return await response.json(content_type=None)
