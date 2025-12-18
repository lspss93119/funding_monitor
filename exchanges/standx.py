import asyncio
import aiohttp
from datetime import datetime, timezone
from typing import List, Dict
from .base import BaseExchange
from models import FundingData

class StandXExchange(BaseExchange):
    def __init__(self):
        # Base URL confirmed as perps.standx.com
        super().__init__("StandX", "https://perps.standx.com")
        
        # Mapping for common symbols. 
        # API docs example shows 'BTC-USD', assuming this corresponds to the perp contract.
        self.symbol_map = {
            "BTC-PERP": "BTC-USD"
        }

    async def get_funding_rates(self, symbols: List[str]) -> List[FundingData]:
        results = []
        async with aiohttp.ClientSession() as session:
            tasks = []
            for requested_symbol in symbols:
                internal_symbol = self.symbol_map.get(requested_symbol, requested_symbol)
                tasks.append(self._fetch_symbol_rate(session, requested_symbol, internal_symbol))
            
            # Execute all requests concurrently
            fetched_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for res in fetched_results:
                if isinstance(res, FundingData):
                    results.append(res)
                elif isinstance(res, Exception):
                    print(f"Error fetching specific symbol from StandX: {res}")
        return results

    async def _fetch_symbol_rate(self, session: aiohttp.ClientSession, requested_symbol: str, internal_symbol: str) -> FundingData:
        # 1. Fetch funding rate (likely hourly)
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        start_ms = now_ms - (24 * 60 * 60 * 1000)
        params = {"symbol": internal_symbol, "start_time": start_ms, "end_time": now_ms}
        
        funding_task = self._fetch_json(session, "/api/query_funding_rates", params=params)
        price_task = self._fetch_json(session, "/api/query_symbol_price", params={"symbol": internal_symbol})
        
        funding_data, price_data = await asyncio.gather(funding_task, price_task, return_exceptions=True)
        
        # Process funding
        item = {}
        if isinstance(funding_data, list) and len(funding_data) > 0:
            try: item = max(funding_data, key=lambda x: x.get('time', ''))
            except: item = funding_data[-1]
        elif isinstance(funding_data, dict):
            item = funding_data

        # Process price
        mark_price = None
        if isinstance(price_data, dict):
            mark_price = float(price_data.get('mark_price') or price_data.get('last_price', 0))

        current_time = datetime.now(timezone.utc)
        return FundingData(
            exchange=self.name,
            symbol=requested_symbol,
            funding_rate=float(item.get('funding_rate', 0)),
            funding_time=current_time,
            timestamp=current_time,
            price=mark_price,
            raw_response={"funding": item, "price": price_data}
        )
