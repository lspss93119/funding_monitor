import aiosqlite
import logging

from datetime import datetime
from typing import List, Dict, Any
from models import FundingData

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self, db_path: str = "funding_data.db"):
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS funding_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exchange TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    funding_rate REAL,
                    price REAL,
                    timestamp INTEGER
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_symbol_timestamp 
                ON funding_history (symbol, timestamp)
            """)
            await db.commit()
            logger.info(f"Database initialized at {self.db_path}")

    async def save_rate(self, data: FundingData):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Deduplication: Check if exactly the same data point exists
                async with db.execute(
                    "SELECT 1 FROM funding_history WHERE exchange = ? AND symbol = ? AND timestamp = ?",
                    (data.exchange, data.symbol, int(data.timestamp.timestamp()))
                ) as cursor:
                    if await cursor.fetchone():
                        return

                await db.execute(
                    """
                    INSERT INTO funding_history (exchange, symbol, funding_rate, price, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        data.exchange,
                        data.symbol,
                        data.funding_rate,
                        data.price,
                        int(data.timestamp.timestamp())
                    )
                )
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to save data: {e}")

    async def get_history(self, symbol: str, limit: int = 200) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT exchange, funding_rate, price, timestamp
                FROM funding_history
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (symbol, limit * 2) 
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_24h_stats(self, symbol: str) -> Dict[str, float]:
        import time
        cutoff = int(time.time() - 86400)
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT 
                    ABS(l.funding_rate - s.funding_rate) as spread
                FROM (
                    SELECT timestamp / 60 as bucket, AVG(funding_rate) as funding_rate
                    FROM funding_history
                    WHERE symbol = ? AND exchange = 'Lighter' AND timestamp > ?
                    GROUP BY bucket
                ) l
                JOIN (
                    SELECT timestamp / 60 as bucket, AVG(funding_rate) as funding_rate
                    FROM funding_history
                    WHERE symbol = ? AND exchange = 'StandX' AND timestamp > ?
                    GROUP BY bucket
                ) s ON l.bucket = s.bucket
                """,
                (symbol, cutoff, symbol, cutoff)
            ) as cursor:
                rows = await cursor.fetchall()
        
        if not rows:
            return {"max_spread_apr": 0, "avg_spread_apr": 0}

        spreads = [r['spread'] for r in rows]
        max_spread = max(spreads)
        avg_spread = sum(spreads) / len(spreads)
        
        return {
            "max_spread_apr": max_spread * 24 * 365 * 100,
            "avg_spread_apr": avg_spread * 24 * 365 * 100
        }

    async def get_heatmap_stats(self, symbol: str) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                WITH aggregated AS (
                    SELECT 
                        exchange,
                        timestamp / 60 as bucket,
                        AVG(funding_rate) as funding_rate
                    FROM funding_history
                    WHERE symbol = ?
                      -- Filter STRICTLY for top of the hour (00 min, 00 sec range)
                      -- Polling is every 30s (:00, :30). 
                      -- We want to exclude :30, so window must be < 30s.
                      AND (timestamp % 3600) < 25
                    GROUP BY exchange, bucket
                )
                SELECT 
                    strftime('%w', datetime(r1.bucket * 60, 'unixepoch')) as weekday,
                    strftime('%H', datetime(r1.bucket * 60, 'unixepoch')) as hour,
                    AVG(ABS(r1.funding_rate - r2.funding_rate) * 24 * 365 * 100) as avg_spread_apr,
                    COUNT(*) as data_points
                FROM aggregated r1
                JOIN aggregated r2 ON r1.bucket = r2.bucket
                WHERE r1.exchange = 'Lighter' 
                  AND r2.exchange = 'StandX'
                GROUP BY weekday, hour
                ORDER BY weekday, hour
                """,
                (symbol,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
