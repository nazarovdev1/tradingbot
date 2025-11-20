# SMC + AI Backtesting System

A complete backtesting framework that integrates Smart Money Concepts (SMC), AI predictions, and risk management into a Backtrader-based system.

## Overview

This system combines multiple sophisticated trading elements:
- Smart Money Concepts (BOS, CHOCH, FVG, Order Blocks, Liquidity Sweeps)
- AI predictions using LSTM models
- Comprehensive risk management
- Professional backtesting metrics

## Directory Structure

```
├── smc_engine/           # SMC analysis modules
│   ├── smc.py           # Main SMC analyzer
│   ├── structure.py     # Swing, BOS, CHOCH detection
│   ├── fvg.py          # Fair Value Gap detection
│   ├── orderblock.py   # Order Block detection
│   └── liquidity.py    # Liquidity analysis
├── ai_engine/           # AI model integration
│   ├── model_loader.py # Model loading and prediction
│   └── predict.py      # Prediction interface
├── strategy/            # Trading strategies
│   └── hybrid_smc_ai_strategy.py # Main strategy implementation
├── backtest/            # Backtesting components
│   ├── run_backtest.py # Main runner
│   ├── data_loader.py  # Data loading utilities
│   ├── metrics.py      # Performance metrics
│   └── plot.py         # Visualization tools
├── models/              # Trained AI models (optional)
├── sample_data/         # Example data files (optional)
├── requirements.txt     # Python dependencies
└── instructions.md      # This file
```

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure you have a trained AI model at `models/model.h5` (optional - system works without it)

## Data Format

The system expects CSV data with the following columns:
- `datetime`: Date and time (parseable by pandas)
- `open`: Opening price
- `high`: Highest price
- `low`: Lowest price
- `close`: Closing price
- `volume`: Trading volume

Example:
```csv
datetime,open,high,low,close,volume
2023-01-01 00:00:00,100.0,101.5,99.5,101.0,1000
2023-01-01 00:15:00,101.0,102.0,100.5,101.8,1200
...
```

## Usage

Run the backtest with default parameters:
```bash
python backtest/run_backtest.py --data /path/to/your/data.csv
```

### Optional Parameters

- `--output-dir`: Directory for output files (default: ./backtest_results)
- `--initial-cash`: Starting capital (default: 10000.0)
- `--commission`: Trading commission rate (default: 0.001 = 0.1%)
- `--risk-per-trade`: Risk per trade as % of capital (default: 0.02 = 2%)
- `--max-risk`: Maximum risk score allowed (default: 40)
- `--atr-period`: ATR indicator period (default: 14)
- `--ema200-period`: EMA 200 period (default: 200)
- `--ema50-period`: EMA 50 period (default: 50)
- `--rsi-period`: RSI period (default: 14)
- `--risk-reward`: Risk/reward ratio (default: 2.0)
- `--printlog`: Enable detailed logging

Example with custom parameters:
```bash
python backtest/run_backtest.py \
  --data sample_data/xauusd_15m.csv \
  --output-dir results \
  --initial-cash 50000 \
  --risk-per-trade 0.01 \
  --max-risk 30 \
  --risk-reward 3.0
```

## Features

### SMC Analysis
- Swing High/Low detection
- BOS (Break of Structure) and CHOCH (Change of Character)
- FVG (Fair Value Gap) detection
- Order Block identification
- Liquidity sweep detection
- Market phase classification

### AI Integration
- LSTM model loading and prediction
- Confidence-based signal filtering
- Automatic fallback for missing models

### Risk Management
- Position sizing based on risk percentage
- Dynamic stop loss based on SMC levels
- Take profit at risk/reward ratio
- Comprehensive risk scoring

### Performance Metrics
- Total return and annualized return
- Sharpe ratio
- Maximum drawdown
- Win rate and profit factor
- Expectancy and trade distribution
- Equity curve visualization
- Trade analysis charts

## Strategy Logic

The Hybrid SMC + AI Strategy follows these rules:

1. **Signal Generation**:
   - SMC engine provides bias based on current market structure
   - AI model provides direction prediction with confidence score
   - Risk engine validates if conditions are favorable

2. **Signal Combination**:
   - If SMC and AI agree: proceed with trade
   - If conflicting: SMC takes priority over AI
   - If both neutral: no trade

3. **Position Management**:
   - Position size based on risk % of account
   - Stop loss set at recent swing levels (SMC-based)
   - Take profit at 1:2 or better risk/reward ratio

## Output Files

The system generates several output files:

- `backtest_results_{data_name}.csv`: Summary metrics
- `backtest_results_{data_name}_trades.csv`: Individual trade details
- `backtest_results_{data_name}.json`: Complete results in JSON format
- `equity_curve_{data_name}.png`: Equity curve chart
- `trade_analysis_{data_name}.png`: Detailed trade analysis

## Customization

To modify strategy behavior, adjust the parameters:
- Risk management settings control position sizing
- Technical indicator periods can be tuned for different timeframes
- Confidence thresholds for AI signals
- Risk/reward ratios

## Troubleshooting

- If you get "Model not found" errors, the system will use random predictions as fallback
- Ensure your data has no missing values in OHLCV columns
- For best results, use at least 6 months of data
- Check that datetime column is in a parseable format