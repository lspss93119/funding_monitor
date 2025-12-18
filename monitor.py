import asyncio
import logging

from aiohttp import web
from typing import List, Dict
from datetime import datetime
from dataclasses import asdict
from exchanges.base import BaseExchange
from models import FundingData
from storage import StorageManager

# Set up logging for console output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FundingMonitor:
    def __init__(self, exchanges: List[BaseExchange], config: Dict):
        self.exchanges = exchanges
        self.config = config
        self.symbols = config.get('symbols', ['BTC-PERP', 'ETH-PERP'])
        self.interval = config.get('polling_interval', 30)
        self.thresholds = config.get('thresholds', {})
        self.storage = StorageManager()
        
        # Store latest funding rates: {symbol: {exchange_name: FundingData}}
        self.latest_data: Dict[str, Dict[str, FundingData]] = {s: {} for s in self.symbols}

    async def handle_index(self, request):
        return web.FileResponse('./templates/dashboard.html')

    async def handle_data(self, request):
        # Convert data to JSON-serializable format
        serializable_data = {}
        for symbol, exchange_map in self.latest_data.items():
            serializable_data[symbol] = {}
            for exchange, data in exchange_map.items():
                data_dict = asdict(data)
                # Convert datetime objects to ISO strings
                data_dict['funding_time'] = data.funding_time.isoformat() if data.funding_time else None
                data_dict['timestamp'] = data.timestamp.isoformat()
                serializable_data[symbol][exchange] = data_dict
            
            # Inject stats from DB
            try:
                 stats = await self.storage.get_24h_stats(symbol)
                 serializable_data[symbol]['stats'] = stats
            except Exception as e:
                 logger.error(f"Error fetching stats for {symbol}: {e}")
                 serializable_data[symbol]['stats'] = {"max_spread_apr": 0, "avg_spread_apr": 0}
        
        return web.json_response(serializable_data)

    async def handle_history(self, request):
        symbol = request.query.get('symbol', 'BTC-PERP')
        try:
            limit = int(request.query.get('limit', 100))
        except ValueError:
            limit = 100
            
        data = await self.storage.get_history(symbol, limit)
        return web.json_response(data)

    async def handle_heatmap(self, request):
        symbol = request.query.get('symbol', 'BTC-PERP')
        try:
             stats = await self.storage.get_heatmap_stats(symbol)
             return web.json_response(stats)
        except Exception as e:
             logger.error(f"Error fetching heatmap stats: {e}")
             return web.json_response([], status=500)

    async def run(self):
        # Initialize DB
        await self.storage.init_db()

        # Setup Web Server
        app = web.Application()
        app.router.add_get('/', self.handle_index)
        app.router.add_get('/api/data', self.handle_data)
        app.router.add_get('/api/history', self.handle_history)
        app.router.add_get('/api/heatmap', self.handle_heatmap)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()
        
        logger.info(f"Starting Filter Monitor (Interval: {self.interval}s, Symbols: {self.symbols})")
        logger.info("Dashboard running at http://localhost:8080")
        
        try:
            while True:
                tasks = [ex.get_funding_rates(self.symbols) for ex in self.exchanges]
                results = await asyncio.gather(*tasks)
                
                for exchange_results in results:
                    for data in exchange_results:
                        await self._process_data(data)
                
                self._check_comparisons()
                await asyncio.sleep(self.interval)
        finally:
            await runner.cleanup()

    async def _process_data(self, data: FundingData):
        prev_data = self.latest_data[data.symbol].get(data.exchange)
        
        # 0. Save to DB (Local History)
        await self.storage.save_rate(data)
        
        # 1. Update latest data
        self.latest_data[data.symbol][data.exchange] = data
        
        # 2. Check Absolute Threshold
        threshold = self.thresholds.get('absolute', 0.001) # Default 0.1%
        if abs(data.funding_rate) >= threshold:
            logger.warning(
                f"[{data.exchange}] {data.symbol} Funding Rate High: {data.funding_rate:+.6%} "
                f"(Threshold: {threshold:+.4%})"
            )
            
        # 3. Check Direction Flip
        if prev_data:
            if (prev_data.funding_rate > 0 and data.funding_rate < 0) or \
               (prev_data.funding_rate < 0 and data.funding_rate > 0):
                logger.warning(
                    f"[{data.exchange}] {data.symbol} Funding Flip: "
                    f"{prev_data.funding_rate:+.6%} -> {data.funding_rate:+.6%}"
                )
        
        # Periodic Info Log
        logger.info(f"Parsed: {data}")

    def _check_comparisons(self):
        diff_threshold = self.thresholds.get('difference', 0.0005) # Default 0.05%
        
        for symbol, exchange_map in self.latest_data.items():
            if len(exchange_map) >= 2:
                # Compare pairs (currently Lighter vs StandX)
                ex_names = list(exchange_map.keys())
                for i in range(len(ex_names)):
                    for j in range(i + 1, len(ex_names)):
                        ex1, ex2 = ex_names[i], ex_names[j]
                        rate1 = exchange_map[ex1].funding_rate
                        rate2 = exchange_map[ex2].funding_rate
                        diff = abs(rate1 - rate2)
                        
                        if diff >= diff_threshold:
                            logger.warning(
                                f"[{symbol}] Significant Spread: {ex1}({rate1:+.6%}) vs "
                                f"{ex2}({rate2:+.6%}) | Diff: {diff:+.6%}"
                            )
