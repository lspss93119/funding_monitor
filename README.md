# Funding Rate Monitor & Arbitrage Scanner

[English](README.md) | [繁體中文](README_zh.md)

A real-time dashboard designed to monitor funding rates across decentralized exchanges (Lighter, StandX) and identify high-yield arbitrage opportunities.

## 🚀 Features

- **Real-time Monitoring**: Fetches live funding rates every 30 seconds.
- **Spread Analysis**: Automatically calculates the spread and annualized APY between exchanges.
- **Visual Dashboard**:
  - **Live Charts**: Tracks funding rate trends and spread divergence.
  - **Heatmap**: Visualizes historical spread intensity by day and hour.
  - **Opportunity Alerts**: Highlights spreads > 10% APR with visual and audio cues.
- **Local Data Persistence**: Stores historical data locally in SQLite for privacy and speed.
- **Profit Calculator**: Built-in calculator to estimate daily/weekly returns based on principal amount.

## 🛠️ Supported Exchanges

- **Lighter** (Orderbook DEX)
- **StandX** (Perpetual DEX)

## 📦 Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/lspss93119/funding_monitor.git
    cd funding_monitor
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Monitor**
    ```bash
    python3 main.py
    ```

4.  **Access Dashboard**
    Open your browser and navigate to:
    `http://localhost:8080`

## ⚙️ Configuration

You can adjust settings in `config.yaml`:
- **Symbols**: Add or remove trading pairs (e.g., `BTC-PERP`).
- **Polling Interval**: Set how often to fetch data (default: 30s).

## 📊 Project Structure

- `main.py`: Entry point for the application.
- `monitor.py`: Core logic for fetching and processing data.
- `storage.py`: SQLite database management.
- `templates/dashboard.html`: The frontend user interface.
- `exchanges/`: Exchange-specific API integrations.

## 📝 License

This project is for personal use and educational purposes.
