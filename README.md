# Forex Signal Telegram Bot - Multi-Timeframe Edition

This is an advanced Forex Signal Telegram Bot that supports multiple timeframes and uses various technical indicators to generate trading signals for XAU/USD (Gold).

python -m uvicorn smc_server:app --host 0.0.0.0 --port 8000

## Features
- **Multi-timeframe support**: 3min, 15min, 1h, and 1day timeframes
- **Technical indicators**: RSI(14), EMA20, EMA50, EMA200
- **Candlestick pattern detection**: Bullish and Bearish Engulfing patterns
- **Timeframe-specific strategies**: Each timeframe uses a tailored trading strategy
- **Probability calculation**: Signals come with probability estimates
- **Formatted output**: Professional signal format for Telegram

## Setup
1. Install dependencies: `npm install`
2. Create a `.env` file with:
   ```
   BOT_TOKEN=your_telegram_bot_token
   TWELVEDATA_KEY=your_twelvedata_api_key  # or your preferred API
   PORT=3000  # Optional, defaults to 3000
   ```
3. Start the bot: `npm start`

## Timeframe Strategies

### 3 Minute Scalping Strategy
- Uses extremely fast conditions
- EMA20 > EMA50 for bullish momentum
- RSI < 25 for BUY zone, RSI > 75 for SELL zone
- Requires engulfing candle pattern
- Price must be above EMA20 for BUY, below for SELL
- Probability: 80-90% (4/4 conditions), 60-75% (3/4 conditions), else NEUTRAL

### 15 Minute Advanced Scalping Strategy
- BUY: EMA50 > EMA200, EMA20 > EMA50, RSI < 30, Bullish engulfing, Price above EMA20
- SELL: EMA50 < EMA200, EMA20 < EMA50, RSI > 70, Bearish engulfing, Price below EMA20
- Probability: 85-95% (5/5 conditions), 70-85% (4/5 conditions), 50-70% (3/5 conditions), else NEUTRAL

### 1 Hour Swing Trading Strategy
- BUY: EMA20 crossing above EMA50, EMA50 > EMA200, RSI 40-55, Bullish pattern
- SELL: EMA20 crossing below EMA50, EMA50 < EMA200, RSI 45-60, Bearish pattern
- Probability: 80-90% (4/4 conditions), 60-75% (3/4 conditions), else NEUTRAL

### 1 Day Long-term Strategy
- BUY: EMA50 > EMA200 (macro uptrend), RSI < 40, Bullish engulfing, Price above EMA50
- SELL: EMA50 < EMA200, RSI > 60, Bearish engulfing, Price below EMA50
- Probability: 85-95% (4/4 conditions), 60-80% (3/4 conditions), else NEUTRAL

## Usage
- Start the bot with `/start` command
- Select XAUUSD symbol using the inline keyboard
- Choose from available timeframes: 3min, 15min, 1h, or 1day
- The bot will analyze the market based on the selected timeframe and provide a detailed signal

## Signal Output Format
```
📊 XAU/USD Signal (timeframe)
💰 Price: [price]
📈 RSI14: [rsi_value]
📉 EMA20: [ema20_value]
📉 EMA50: [ema50_value]
📉 EMA200: [ema200_value]
🕯 Pattern Detected: [pattern_type]
📌 Trend direction: [trend]
🎯 Final SIGNAL: [BUY/SELL/NEUTRAL]
🔮 Probability: [probability_percentage]
💡 Reason: [conditions_met]/[total_conditions] conditions met ([reason_list])
```

## Implementation Details
- Modular strategy functions for each timeframe
- Dispatcher function to apply correct strategy based on timeframe
- Candle pattern detector for engulfing patterns
- Probability calculator for each strategy
- Message formatter for consistent Telegram output
