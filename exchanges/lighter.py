import asyncio
import aiohttp
from datetime import datetime, timezone
from typing import List, Dict
from .base import BaseExchange
from models import FundingData

class LighterExchange(BaseExchange):
    def __init__(self):
        # Using the mainnet endpoint found during research
        super().__init__("Lighter", "https://mainnet.zklighter.elliot.ai/api/v1")
        
        # Mapping for common symbols
        self.symbol_map = {
            "BTC-PERP": "BTC"
        }

    async def get_funding_rates(self, symbols: List[str]) -> List[FundingData]:
        results = []
        async with aiohttp.ClientSession() as session:
            try:
                # The research indicated a /funding-rates endpoint
                response_data = await self._fetch_json(session, "/funding-rates")
                
                if isinstance(response_data, dict) and 'funding_rates' in response_data:
                    data = response_data['funding_rates']
                elif isinstance(response_data, list):
                    data = response_data
                else:
                    data = []
                
                # Assume data is a list of funding rate objects
                # Field: market_id, exchange, symbol, rate
                now = datetime.now(timezone.utc)
                
                # Create a map for efficient lookup
                market_data = {item['symbol']: item for item in data if isinstance(item, dict)}
                
                for requested_symbol in symbols:
                    internal_symbol = self.symbol_map.get(requested_symbol, requested_symbol)
                    
                    if internal_symbol in market_data:
                        item = market_data[internal_symbol]
                        
                        results.append(FundingData(
                            exchange=self.name,
                            symbol=requested_symbol,
                            funding_rate=float(item['rate']) / 8,
                            funding_time=now,
                            timestamp=now,
                            price=None,
                            raw_response=item
                        ))
            except Exception as e:
                print(f"Error fetching from Lighter: {e}")
                
        return results
