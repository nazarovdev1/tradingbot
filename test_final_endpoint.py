"""
Quick test of /final endpoint to see SMC + AI integration
"""
import requests
import json

# Sample OHLC data (50 candles)
import pandas as pd
df = pd.read_csv('sample_data.csv')

# Take last 50 candles
df = df.tail(50)

payload = {
    "open": df['open'].tolist(),
    "high": df['high'].tolist(),
    "low": df['low'].tolist(),
    "close": df['close'].tolist()
}

print("=" * 60)
print("TESTING /final ENDPOINT (SMC + AI)")
print("=" * 60)
print(f"Sending {len(payload['close'])} candles")

url = "http://127.0.0.1:8000/final"

try:
    response = requests.post(url, json=payload, timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ SUCCESS!")
        print(f"\nFinal Signal: {result['signal']}")
        print(f"Confidence: {result['confidence']:.4f} ({result['confidence']*100:.2f}%)")
        print(f"\nSMC Analysis:")
        print(f"  Bias: {result['smc_analysis']['bias']}")
        print(f"  Entry: {result['smc_analysis']['entry']}")
        print(f"  SL: {result['smc_analysis']['sl']}")
        print(f"  TP: {result['smc_analysis']['tp']}")
        print(f"\nAI Prediction:")
        print(f"  Signal: {result['ai_prediction']['signal']}")
        print(f"  Confidence: {result['ai_prediction']['confidence']:.4f}")
        print(f"  Raw: {result['ai_prediction']['raw_prediction']:.6f}")
        print(f"\nExplanation:")
        print(f"  {result['explanation']}")
    else:
        print(f"\n❌ FAILED: Status code {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("\n" + "=" * 60)
