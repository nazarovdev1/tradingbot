"""
Debug SMC server to see what data is being received
"""
import requests
import json

# Simulate what Telegram bot sends
payload = {
    "open": [1800.0 + i*0.5 for i in range(50)],
    "high": [1801.0 + i*0.5 for i in range(50)],
    "low": [1799.0 + i*0.5 for i in range(50)],
    "close": [1800.5 + i*0.5 for i in range(50)]
}

print("Testing SMC endpoint with valid data...")
print(f"Sending {len(payload['close'])} candles")

try:
    response = requests.post(
        "http://127.0.0.1:8000/smc",
        json=payload,
        timeout=10
    )
    
    print(f"\nStatus: {response.status_code}")
    if response.status_code == 200:
        print("✅ SUCCESS - SMC endpoint working!")
        result = response.json()
        print(f"Bias: {result['bias']}")
    else:
        print(f"❌ FAILED - Status {response.status_code}")
        print(f"Response: {response.text}")
        with open("debug_error.txt", "w") as f:
            f.write(response.text)
except Exception as e:
    print(f"❌ ERROR: {e}")
    with open("debug_error.txt", "w") as f:
        f.write(str(e))
