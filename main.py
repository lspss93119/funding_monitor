import asyncio
import yaml
import os
from exchanges.lighter import LighterExchange
from exchanges.standx import StandXExchange
from monitor import FundingMonitor

async def main():
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Initialize exchanges
    exchanges = [
        LighterExchange(),
        StandXExchange()
    ]

    # Initialize monitor
    monitor = FundingMonitor(exchanges, config)

    # Run monitor
    try:
        await monitor.run()
    except KeyboardInterrupt:
        print("\nMonitor stopped by user.")
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
