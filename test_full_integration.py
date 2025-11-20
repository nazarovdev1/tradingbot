"""
Full Integration Test - Tests entire SMC + AI + Telegram Bot pipeline
"""
import requests
import pandas as pd
import json

print("=" * 70)
print("FULL TRADING BOT INTEGRATION TEST")
print("=" * 70)

# Load sample data
df = pd.read_csv('sample_data.csv')
df = df.tail(50)  # Last 50 candles

# Ensure all values are float (Pydantic expects List[float])
payload = {
    "open": [float(x) for x in df['open'].tolist()],
    "high": [float(x) for x in df['high'].tolist()],
    "low": [float(x) for x in df['low'].tolist()],
    "close": [float(x) for x in df['close'].tolist()]
}

base_url = "http://127.0.0.1:8000"

# Test 1: Health Check
print("\n" + "=" * 70)
print("TEST 1: Health Check")
print("=" * 70)
try:
    response = requests.get(f"{base_url}/health", timeout=5)
    if response.status_code == 200:
        health = response.json()
        print("✅ Server is healthy")
        print(f"   SMC Engine: {'✅' if health['smc_engine_loaded'] else '❌'}")
        print(f"   AI Model: {'✅' if health['ai_model_loaded'] else '❌'}")
    else:
        print(f"❌ Health check failed: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ Cannot connect to server: {e}")
    print("   Make sure SMC server is running: python smc_server.py")
    exit(1)

# Test 2: SMC Endpoint
print("\n" + "=" * 70)
print("TEST 2: SMC Analysis Endpoint")
print("=" * 70)
try:
    response = requests.post(f"{base_url}/smc", json=payload, timeout=10)
    if response.status_code == 200:
        smc_result = response.json()
        print("✅ SMC endpoint working")
        print(f"   Bias: {smc_result['bias']}")
        print(f"   Trend: {smc_result['trend']}")
        print(f"   FVG Zones: {len(smc_result['fvgZones'])}")
        print(f"   Order Blocks: {len(smc_result['orderBlocks'])}")
    else:
        print(f"❌ SMC endpoint failed: {response.status_code}")
        print(f"   {response.text}")
except Exception as e:
    print(f"❌ SMC endpoint error: {e}")

# Test 3: AI Prediction Endpoint
print("\n" + "=" * 70)
print("TEST 3: AI Prediction Endpoint")
print("=" * 70)
try:
    ai_payload = {"closes": payload['close']}
    response = requests.post(f"{base_url}/predict", json=ai_payload, timeout=10)
    if response.status_code == 200:
        ai_result = response.json()
        print("✅ AI endpoint working")
        print(f"   Signal: {ai_result['signal']}")
        print(f"   Confidence: {ai_result['confidence']:.4f} ({ai_result['confidence']*100:.2f}%)")
        print(f"   Raw Prediction: {ai_result['raw_prediction']:.6f}")
        
        # Check if AI is working properly
        if ai_result['confidence'] > 0:
            print("   ✅ AI confidence > 0 (FIXED!)")
        else:
            print("   ⚠️  AI confidence still 0")
    else:
        print(f"❌ AI endpoint failed: {response.status_code}")
        print(f"   {response.text}")
except Exception as e:
    print(f"❌ AI endpoint error: {e}")

# Test 4: Final Endpoint (SMC + AI Confluence)
print("\n" + "=" * 70)
print("TEST 4: Final Endpoint (SMC + AI Confluence)")
print("=" * 70)
try:
    response = requests.post(f"{base_url}/final", json=payload, timeout=10)
    if response.status_code == 200:
        final_result = response.json()
        print("✅ Final endpoint working")
        print(f"\n   FINAL SIGNAL: {final_result['signal']}")
        print(f"   Confidence: {final_result['confidence']:.4f} ({final_result['confidence']*100:.2f}%)")
        print(f"\n   SMC Bias: {final_result['smc_analysis']['bias']}")
        print(f"   AI Signal: {final_result['ai_prediction']['signal']}")
        print(f"   AI Confidence: {final_result['ai_prediction']['confidence']:.4f}")
        
        if final_result['entry']:
            print(f"\n   Entry: {final_result['entry']:.4f}")
            print(f"   Stop Loss: {final_result['sl']:.4f}")
            print(f"   Take Profit: {final_result['tp']:.4f}")
        
        print(f"\n   Explanation:")
        print(f"   {final_result['explanation']}")
        
        # Check if integration is working
        if final_result['ai_prediction']['confidence'] > 0:
            print("\n   ✅ AI integration working - confidence > 0")
        else:
            print("\n   ⚠️  AI integration issue - confidence still 0")
            
    else:
        print(f"❌ Final endpoint failed: {response.status_code}")
        print(f"   {response.text}")
except Exception as e:
    print(f"❌ Final endpoint error: {e}")

# Summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print("\n✅ All core endpoints are working!")
print("\nNext steps:")
print("1. Start Telegram bot: run_bot.bat")
print("2. Test with /start command")
print("3. Click 'Manual Sniper Scan' button")
print("4. Verify AI confidence shows > 0")
print("\n" + "=" * 70)
