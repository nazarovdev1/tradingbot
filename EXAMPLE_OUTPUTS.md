# Forex Signal Bot - Example Outputs

This file shows example outputs from the multi-timeframe Forex signal bot for each timeframe.

## 3 Minute Scalping Example Output:
```
📊 XAU/USD Signal (3min)
💰 Price: 2845.67
📈 RSI14: 22.34
📉 EMA20: 2843.21
📉 EMA50: 2839.85
📉 EMA200: 2820.43
🕯 Pattern Detected: BULLISH_ENGULFING
📌 Trend direction: BULLISH
🎯 Final SIGNAL: BUY
🔮 Probability: 80–90%
💡 Reason: 4/4 conditions met (EMA20 > EMA50, RSI < 25, Bullish Engulfing, Price above EMA20)
```

## 15 Minute Advanced Scalping Example Output:
```
📊 XAU/USD Signal (15min)
💰 Price: 2847.23
📈 RSI14: 28.15
📉 EMA20: 2845.60
📉 EMA50: 2841.32
📉 EMA200: 2825.78
🕯 Pattern Detected: BULLISH_ENGULFING
📌 Trend direction: BULLISH
🎯 Final SIGNAL: BUY
🔮 Probability: 85–95%
💡 Reason: 5/5 conditions met (EMA50 > EMA200, EMA20 > EMA50, RSI < 30, Bullish Engulfing, Price above EMA20)
```

## 1 Hour Swing Trading Example Output:
```
📊 XAU/USD Signal (1h)
💰 Price: 2850.45
📈 RSI14: 48.21
📉 EMA20: 2848.73
📉 EMA50: 2840.65
📉 EMA200: 2815.89
🕯 Pattern Detected: BULLISH_ENGULFING
📌 Trend direction: BULLISH
🎯 Final SIGNAL: BUY
🔮 Probability: 80–90%
💡 Reason: 4/4 conditions met (EMA20 > EMA50 (crossing up), EMA50 > EMA200, RSI between 40–55, Bullish pattern)
```

## 1 Day Long-term Example Output:
```
📊 XAU/USD Signal (1day)
💰 Price: 2855.67
📈 RSI14: 38.56
📉 EMA20: 2852.43
📉 EMA50: 2845.21
📉 EMA200: 2810.87
🕯 Pattern Detected: BULLISH_ENGULFING
📌 Trend direction: BULLISH
🎯 Final SIGNAL: BUY
🔮 Probability: 85–95%
💡 Reason: 4/4 conditions met (EMA50 > EMA200, RSI < 40, Bullish Engulfing, Price above EMA50)
```

## NEUTRAL Signal Example:
```
📊 XAU/USD Signal (15min)
💰 Price: 2835.12
📈 RSI14: 45.67
📉 EMA20: 2832.89
📉 EMA50: 2837.45
📉 EMA200: 2825.10
🕯 Pattern Detected: No pattern
📌 Trend direction: NEUTRAL
🎯 Final SIGNAL: NEUTRAL
🔮 Probability: < 50%
💡 Reason: 1/5 conditions met (EMA50 < EMA200)
```

## Telegram Interface Layout:
```
[ 🟡 XAUUSD ]
[ 3min  15min ]
[  1h   1day  ]
```

Each button triggers the corresponding strategy based on the selected timeframe.