import pandas as pd
from smc_engine import SMCEngine

df = pd.read_csv('sample_data.csv')
engine = SMCEngine()
result = engine.analyze_market_structure(df)

print("=" * 60)
print("SMC QUICK TEST RESULTS")
print("=" * 60)
print(f"Bias: {result['bias']}")
print(f"Trend: {result['trend']}")
print(f"FVG Zones: {len(result['fvgZones'])}")
print(f"Order Blocks: {len(result['orderBlocks'])}")
print(f"Entry: {result['entry']}")
print(f"SL: {result['sl']}")
print(f"TP: {result['tp']}")
print(f"BOS Bullish: {result['bos']['bullish']}")
print(f"BOS Bearish: {result['bos']['bearish']}")
print(f"CHOCH Bullish: {result['choch']['bullish']}")
print(f"CHOCH Bearish: {result['choch']['bearish']}")
print("=" * 60)
